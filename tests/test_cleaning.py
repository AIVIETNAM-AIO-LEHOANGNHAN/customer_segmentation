"""Kiểm thử module làm sạch dữ liệu (Task 2) theo Business Rules — KAN-12 (QA/QC).

Chạy:  pytest tests/ -v

Quy ước quan trọng
------------------
Mỗi test dưới đây khẳng định **hành vi đúng theo đặc tả**
(`docs/T01_data_specification.md`), không phải hành vi hiện tại của code.

Những test ứng với lỗi **đã phát hiện nhưng chưa sửa** được đánh dấu:

    @pytest.mark.xfail(strict=True, reason="QA-xx: ...")

`strict=True` có nghĩa: khi lỗi được sửa, test chuyển sang XPASS và **pytest báo
fail** — buộc người sửa quay lại gỡ marker. Nhờ vậy bộ test luôn xanh khi chưa
sửa, và tự động nhắc khi đã sửa.

Lịch sử
-------
Vòng 1 (27/07/2026, commit `b52a0b3`): 7 lỗi được đánh dấu xfail.
Vòng 2 (29/07/2026, commit `5cfc434` + `510245c`): QA-01→QA-05 đã được sửa và
QA xác nhận bằng XPASS. Các marker tương ứng đã gỡ, test giữ lại làm
**regression test**. Lỗi còn mở và lỗi mới phát hiện tiếp tục dùng xfail.

Bảng đối chiếu đầy đủ: `outputs/reports/qa_test_results.md`.
Danh sách lỗi + mức ưu tiên: `outputs/reports/data_quality_report.md`.
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.cleaning import (  # noqa: E402
    clean_pipeline,
    flag_cancelled,
    flag_missing_customer,
    flag_price_anomaly,
    flag_special_stockcode,
    remove_duplicates,
)

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "test_samples")
ENCODING = "latin1"


def load_sample(name: str) -> pd.DataFrame:
    path = os.path.join(SAMPLE_DIR, name)
    if not os.path.exists(path):
        pytest.skip(f"Thiếu file test {name}. Chạy: python scripts/generate_test_samples.py")
    return pd.read_csv(path, encoding=ENCODING)


@pytest.fixture(scope="module")
def base():
    return load_sample("base_sample.csv")


# ---------------------------------------------------------------------------
# Nhóm A — Lỗi kỹ thuật chung
# ---------------------------------------------------------------------------


def test_duplicate_rows_are_removed():
    """BR-06: hai bản ghi giống nhau toàn bộ -> chỉ giữ lại một."""
    out = clean_pipeline(load_sample("test_duplicate.csv"))
    assert len(out) == 300, "350 dòng (300 gốc + 50 nhân đôi) phải rút về đúng 300"


def test_remove_duplicates_keeps_distinct_rows(base):
    """Không được xoá nhầm các dòng chỉ *giống nhau một phần*."""
    out = remove_duplicates(base.copy())
    assert len(out) == len(base)


def test_invoicedate_is_datetime_after_cleaning(base):
    """Nhóm A: InvoiceDate sau xử lý phải là datetime để tính được Recency."""
    out = clean_pipeline(base.copy())
    assert pd.api.types.is_datetime64_any_dtype(out["InvoiceDate"])


def test_price_is_numeric_after_cleaning(base):
    """Nhóm A: Price phải là numeric để tính được Monetary."""
    out = clean_pipeline(base.copy())
    price_col = "Price" if "Price" in out.columns else "UnitPrice"
    assert pd.api.types.is_numeric_dtype(out[price_col])


def test_quantity_is_numeric_after_cleaning():
    """QA-02 (đã sửa 5cfc434) — regression: Quantity luôn phải là numeric."""
    out = clean_pipeline(load_sample("test_wrong_dtype.csv"))
    assert pd.api.types.is_numeric_dtype(out["Quantity"])


def test_invalid_quantity_rows_are_kept():
    """QA-02: dòng Quantity không ép được kiểu phải được GIỮ, không xoá."""
    df = load_sample("test_wrong_dtype.csv")
    out = clean_pipeline(df.copy())
    assert len(out) == len(df), "ép kiểu hỏng không được làm mất dòng"
    assert int(out["Quantity"].isna().sum()) == 10


@pytest.mark.xfail(
    strict=True,
    reason="QA-14: InvoiceDate lỗi có cờ HasInvalidDate, nhưng Quantity ép "
           "hỏng thì chỉ thành NaN lặng lẽ, không có cờ tương ứng. "
           "Bất đối xứng — cùng một loại lỗi, hai cách xử lý khác nhau.",
)
def test_invalid_quantity_is_flagged():
    """Dòng Quantity ép kiểu hỏng phải có cờ riêng, giống HasInvalidDate."""
    out = clean_pipeline(load_sample("test_wrong_dtype.csv"))
    flag_cols = [
        c for c in out.columns
        if "quantity" in c.lower() and out[c].dtype == bool
    ]
    assert flag_cols, "không có cột cờ nào ghi nhận 10 dòng Quantity hỏng"


def test_invalid_invoicedate_is_flagged_not_dropped():
    """QA-03 (đã sửa 5cfc434) — regression: ngày lỗi phải gắn cờ, không xoá."""
    df = load_sample("test_wrong_dtype.csv")
    out = clean_pipeline(df.copy())
    assert len(out) == len(df), "không được xoá dòng có InvoiceDate lỗi"
    assert "HasInvalidDate" in out.columns
    assert int(out["HasInvalidDate"].sum()) == 5


# ---------------------------------------------------------------------------
# Nhóm B — Đặc thù Online Retail II (nguyên tắc "gắn cờ, không xoá vội")
# ---------------------------------------------------------------------------


def test_null_customerid_rows_are_kept_not_deleted():
    """BR-03: dòng thiếu Customer ID phải CÒN trong dữ liệu sạch."""
    out = clean_pipeline(load_sample("test_missing_customerid.csv"))
    assert len(out) == 300, "không được xoá dòng chỉ vì thiếu Customer ID"


def test_null_customerid_rows_are_flagged():
    """BR-03: 75/300 dòng thiếu Customer ID -> HasCustomerID = False."""
    out = clean_pipeline(load_sample("test_missing_customerid.csv"))
    assert int((~out["HasCustomerID"]).sum()) == 75


def test_flag_missing_customer_marks_every_null(base):
    df = base.copy()
    df.loc[:9, "Customer ID"] = pd.NA
    out = flag_missing_customer(df)
    assert out.loc[:9, "HasCustomerID"].eq(False).all()
    assert out.loc[10:, "HasCustomerID"].all()


def test_customerid_format_is_preserved():
    """QA-04 (đã sửa 5cfc434) — regression: 17850 không được thành '17850.0'."""
    out = clean_pipeline(load_sample("test_missing_customerid.csv"))
    col = "Customer ID" if "Customer ID" in out.columns else "CustomerID"
    ids = out[col].dropna().astype(str)
    assert not ids.str.endswith(".0").any(), f"ví dụ mã bị lệch: {ids.iloc[0]}"


def test_customerid_uniqueness_is_not_changed_by_formatting(base):
    """Sửa định dạng không được vô tình gộp hai khách hàng làm một."""
    df = base.copy()
    out = clean_pipeline(df.copy())
    col = "Customer ID" if "Customer ID" in out.columns else "CustomerID"
    assert out[col].nunique() == df["Customer ID"].nunique()


def test_cancelled_invoices_are_kept_and_flagged():
    """BR-01: hóa đơn 'C' phải được gắn cờ và giữ nguyên trong dữ liệu."""
    out = clean_pipeline(load_sample("test_cancelled_invoice.csv"))
    assert len(out) == 320, "không được xoá hóa đơn hủy"
    assert int(out["IsCancelled"].sum()) == 20


def test_negative_quantity_is_kept():
    """BR-02: Quantity âm giữ nguyên bản ghi, chỉ đánh dấu cùng IsCancelled."""
    out = clean_pipeline(load_sample("test_cancelled_invoice.csv"))
    assert int((out["Quantity"] < 0).sum()) == 20


def test_flag_cancelled_does_not_touch_normal_invoices(base):
    out = flag_cancelled(base.copy())
    assert not out["IsCancelled"].any()


def test_service_code_rows_are_kept():
    """BR-05: dòng mã dịch vụ chỉ gắn cờ, không xoá."""
    out = clean_pipeline(load_sample("test_service_code.csv"))
    assert len(out) == 312


def test_all_service_codes_in_sample_are_flagged():
    """QA-01 (đã sửa 5cfc434) — regression: đủ 12/12 dòng mã dịch vụ."""
    out = clean_pipeline(load_sample("test_service_code.csv"))
    assert int(out["IsServiceCode"].sum()) == 12


def test_service_code_matching_is_case_insensitive(base):
    """QA-01 (đã sửa 5cfc434) — regression: 'm' phải bắt được như 'M'."""
    df = base.head(3).copy()
    df["StockCode"] = ["POST", "m", "bank charges"]
    out = flag_special_stockcode(df)
    assert out["IsServiceCode"].all()


def test_service_code_does_not_flag_real_products(base):
    """Không được gắn cờ nhầm mã sản phẩm thật (rủi ro của .str.upper())."""
    df = base.head(4).copy()
    df["StockCode"] = ["85123A", "DCGSSGIRL", "DCGSSBOY", "PADS"]
    out = flag_special_stockcode(df)
    assert not out["IsServiceCode"].any()


@pytest.mark.xfail(
    strict=True,
    reason="QA-01 (còn lại): StockCode 'B' (Adjust bad debt, 3 dòng, ròng "
           "-11.062,06) và nhóm 'gift_0001_*' (34 dòng) vẫn chưa vào "
           "special_codes. Task 4 độc lập phát hiện cùng vấn đề với 'B'.",
)
def test_remaining_service_codes_are_flagged(base):
    """Các mã phi-sản-phẩm còn sót sau vòng sửa 1."""
    df = base.head(2).copy()
    df["StockCode"] = ["B", "gift_0001_20"]
    out = flag_special_stockcode(df)
    assert out["IsServiceCode"].all()


def test_zero_price_rows_are_kept_and_flagged():
    """BR-04: giá bằng 0 giữ nguyên và đánh dấu, không xoá."""
    out = clean_pipeline(load_sample("test_zero_price.csv"))
    assert len(out) == 300, "không được xoá dòng chỉ vì Price = 0"
    assert int(out["PriceAnomaly"].sum()) == 15


def test_flag_price_anomaly_covers_zero_and_negative(base):
    df = base.head(3).copy()
    df["Price"] = [0.0, -5.0, 2.55]
    out = flag_price_anomaly(df)
    assert out["PriceAnomaly"].tolist() == [True, True, False]


# ---------------------------------------------------------------------------
# Tuân thủ schema mục 1.3 + xử lý file hỏng
# ---------------------------------------------------------------------------


def test_missing_required_column_blocks_processing():
    """Thiếu cột bắt buộc InvoiceDate -> phải dừng, không được xử lý tiếp."""
    with pytest.raises((KeyError, ValueError)):
        clean_pipeline(load_sample("test_missing_column.csv"))


@pytest.mark.xfail(
    strict=True,
    reason="QA-06: chưa có src/data/validation.py. Task 3 đã cải thiện thông "
           "điệp ('Missing required column. Expected one of: ...') nhưng vẫn "
           "raise KeyError, chưa phải lỗi nghiệp vụ ValueError.",
)
def test_missing_required_column_raises_business_error():
    """Thông báo lỗi phải nêu rõ cột nào thiếu, dạng ValueError nghiệp vụ."""
    with pytest.raises(ValueError, match="InvoiceDate"):
        clean_pipeline(load_sample("test_missing_column.csv"))


def test_totalprice_column_is_created(base):
    """QA-05 (đã sửa 5cfc434) — regression: TotalPrice = Quantity × Price."""
    out = clean_pipeline(base.copy())
    assert "TotalPrice" in out.columns
    price_col = "Price" if "Price" in out.columns else "UnitPrice"
    expected = out["Quantity"] * out[price_col]
    assert out["TotalPrice"].round(4).equals(expected.round(4))


def test_all_derived_columns_exist(base):
    """Schema mục 1.3: đủ 4 cột phái sinh sau khi làm sạch."""
    out = clean_pipeline(base.copy())
    for col in ("TotalPrice", "IsCancelled", "HasCustomerID", "IsServiceCode"):
        assert col in out.columns, f"thiếu cột phái sinh {col}"
    for col in ("IsCancelled", "HasCustomerID", "IsServiceCode"):
        assert out[col].dtype == bool, f"{col} phải là bool, đang là {out[col].dtype}"


def test_clean_data_passes_through_untouched(base):
    """Dữ liệu vốn đã sạch thì không được mất dòng nào."""
    out = clean_pipeline(base.copy())
    assert len(out) == len(base)
