"""Kiểm thử module làm sạch dữ liệu (Task 2) theo Business Rules — KAN-12 (QA/QC).

Chạy:  pytest tests/ -v

Quy ước quan trọng
------------------
Mỗi test dưới đây khẳng định **hành vi đúng theo đặc tả**
(`docs/T01_data_specification.md`), không phải hành vi hiện tại của code.

Những test ứng với lỗi đã phát hiện được đánh dấu:

    @pytest.mark.xfail(strict=True, reason="QA-xx: ...")

`strict=True` có nghĩa: khi Data sửa xong lỗi, test sẽ chuyển sang XPASS và
**pytest báo fail** — buộc người sửa phải quay lại gỡ marker. Nhờ vậy bộ test
luôn xanh khi chưa sửa, và tự động nhắc khi đã sửa; không có test đỏ kinh niên
để mọi người tập làm ngơ.

Bảng đối chiếu kỳ vọng/thực tế đầy đủ: `outputs/reports/qa_test_results.md`.
Danh sách lỗi và mức ưu tiên: `outputs/reports/data_quality_report.md`.
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
    assert pd.api.types.is_numeric_dtype(out["Price"])


@pytest.mark.xfail(
    strict=True,
    reason="QA-02: fix_dtypes() không ép kiểu Quantity. Text 'abc' lọt qua, "
           "cột giữ dtype object và sẽ vỡ ở bước tính Monetary (Epic 2).",
)
def test_quantity_is_numeric_after_cleaning():
    """Nhóm A: Quantity phải là numeric kể cả khi file đầu vào lẫn text."""
    out = clean_pipeline(load_sample("test_wrong_dtype.csv"))
    assert pd.api.types.is_numeric_dtype(out["Quantity"])


@pytest.mark.xfail(
    strict=True,
    reason="QA-03: fix_dtypes() dropna() thẳng các dòng InvoiceDate lỗi, "
           "không gắn cờ. BR-07 yêu cầu 'đánh dấu lỗi' trước khi loại.",
)
def test_invalid_invoicedate_is_flagged_not_silently_dropped():
    """BR-07: ngày không parse được phải được *đánh dấu*, không biến mất âm thầm."""
    df = load_sample("test_wrong_dtype.csv")
    out = clean_pipeline(df.copy())
    flag_cols = [c for c in out.columns if "date" in c.lower() and out[c].dtype == bool]
    assert len(out) == len(df) and flag_cols, (
        f"{len(df) - len(out)} dòng bị xoá mà không có cột cờ nào ghi nhận"
    )


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


@pytest.mark.xfail(
    strict=True,
    reason="QA-04: fix_dtypes() dùng astype(str) trên cột float64 nên "
           "17850 -> '17850.0'. Sai định dạng khoá khách hàng theo schema mục 1.2.",
)
def test_customerid_format_is_preserved():
    """Customer ID phải giữ nguyên dạng mã (17850), không thành '17850.0'."""
    out = clean_pipeline(load_sample("test_missing_customerid.csv"))
    ids = out["Customer ID"].dropna().astype(str)
    assert not ids.str.endswith(".0").any(), f"ví dụ mã bị lệch: {ids.iloc[0]}"


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


@pytest.mark.xfail(
    strict=True,
    reason="QA-01: danh sách special_codes thiếu D, S, AMAZONFEE và không "
           "xử lý biến thể chữ thường 'm'. 4/12 dòng dịch vụ không được gắn cờ.",
)
def test_all_service_codes_are_flagged():
    """BR-05: đủ 12/12 dòng mã dịch vụ được gắn cờ, không sót mã nào."""
    out = clean_pipeline(load_sample("test_service_code.csv"))
    assert int(out["IsServiceCode"].sum()) == 12


@pytest.mark.xfail(
    strict=True,
    reason="QA-01: so khớp phân biệt hoa/thường nên StockCode 'm' (Manual) "
           "bị bỏ sót — mã này có thật trong dataset gốc.",
)
def test_service_code_matching_is_case_insensitive(base):
    df = base.head(3).copy()
    df["StockCode"] = ["POST", "m", "bank charges"]
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
    reason="QA-06: chưa có src/data/validation.py. Lỗi thiếu cột nổi lên dưới "
           "dạng KeyError thô, chưa phải thông báo nghiệp vụ cho người dùng.",
)
def test_missing_required_column_raises_business_error():
    """Thông báo lỗi phải nêu rõ cột nào thiếu, dạng ValueError nghiệp vụ."""
    with pytest.raises(ValueError, match="InvoiceDate"):
        clean_pipeline(load_sample("test_missing_column.csv"))


@pytest.mark.xfail(
    strict=True,
    reason="QA-05: clean_pipeline chưa sinh cột TotalPrice = Quantity × Price "
           "như schema mục 1.3 quy định. Epic 2 cần cột này để tính Monetary.",
)
def test_totalprice_column_is_created(base):
    """Schema mục 1.3: TotalPrice = Quantity × Price."""
    out = clean_pipeline(base.copy())
    assert "TotalPrice" in out.columns
    expected = out["Quantity"] * out["Price"]
    assert out["TotalPrice"].round(4).equals(expected.round(4))


def test_all_derived_flag_columns_exist(base):
    """Ba cột cờ boolean bắt buộc phải có mặt sau khi làm sạch."""
    out = clean_pipeline(base.copy())
    for col in ("IsCancelled", "HasCustomerID", "IsServiceCode"):
        assert col in out.columns, f"thiếu cột phái sinh {col}"
        assert out[col].dtype == bool, f"{col} phải là kiểu bool, đang là {out[col].dtype}"


def test_clean_data_passes_through_untouched(base):
    """Dữ liệu vốn đã sạch thì không được mất dòng nào."""
    out = clean_pipeline(base.copy())
    assert len(out) == len(base)
