"""Kiểm thử UI Upload & Ánh xạ cột (Task 3) — Nhóm C của KAN-12 (QA/QC).

Chạy:  pytest tests/test_upload_mapping.py -v

Các test này kiểm phần **logic** của `src/app/column_mapper.py` và mối nối của nó
với module làm sạch — tức đúng chuỗi mà `src/app/Home.py` chạy khi người dùng bấm
"Apply mapping and clean data":

    read_uploaded_dataframe -> build_default_mapping -> validate_mapping
                            -> apply_column_mapping -> clean_pipeline

Không dựng Streamlit server: phần `st.*` chỉ là lớp hiển thị, còn toàn bộ quyết
định nghiệp vụ (cột nào bắt buộc, khi nào chặn xử lý) đều nằm trong
`column_mapper.py`. Kiểm ở đây vừa nhanh vừa chạy được trong CI.

Hạng mục C1→C6 tương ứng checklist Nhóm C trong `docs/qa_checklist_data.md`.
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

column_mapper = pytest.importorskip(
    "src.app.column_mapper",
    reason="Task 3 (src/app/column_mapper.py) chưa có trên nhánh này",
)

from src.data.cleaning import clean_pipeline  # noqa: E402

apply_column_mapping = column_mapper.apply_column_mapping
build_default_mapping = column_mapper.build_default_mapping
normalize_column_name = column_mapper.normalize_column_name
validate_mapping = column_mapper.validate_mapping
ensure_supported_file = column_mapper.ensure_supported_file
UnsupportedFileTypeError = column_mapper.UnsupportedFileTypeError
NO_COLUMN_OPTION = column_mapper.NO_COLUMN_OPTION
REQUIRED_COLUMNS = column_mapper.REQUIRED_COLUMNS

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "test_samples")
ENCODING = "latin1"


def load_sample(name: str) -> pd.DataFrame:
    path = os.path.join(SAMPLE_DIR, name)
    if not os.path.exists(path):
        pytest.skip(f"Thiếu file test {name}. Chạy: python scripts/generate_test_samples.py")
    return pd.read_csv(path, encoding=ENCODING)


def auto_map(df: pd.DataFrame):
    columns = list(df.columns)
    return build_default_mapping(columns), columns


# ---------------------------------------------------------------------------
# C1 — Mapping tự động với tên cột gốc Online Retail II
# ---------------------------------------------------------------------------


def test_c1_auto_mapping_matches_all_eight_columns():
    """C1: file gốc -> tự động khớp đủ 8/8 cột, không cần thao tác tay."""
    mapping, columns = auto_map(load_sample("base_sample.csv"))
    assert all(mapping.values()), f"còn cột chưa khớp: {[k for k, v in mapping.items() if not v]}"
    assert validate_mapping(mapping, columns).is_valid


def test_c1_auto_mapping_handles_customer_id_with_space():
    """'Customer ID' (có dấu cách) phải khớp được với cột chuẩn CustomerID."""
    mapping, _ = auto_map(load_sample("base_sample.csv"))
    assert mapping["CustomerID"] == "Customer ID"
    assert mapping["UnitPrice"] == "Price"
    assert mapping["InvoiceNo"] == "Invoice"


def test_c1_normalisation_ignores_case_space_and_separators():
    """Chuẩn hoá tên cột bỏ qua hoa/thường, dấu cách, gạch dưới, gạch ngang."""
    assert normalize_column_name("Customer ID") == normalize_column_name("customer_id")
    assert normalize_column_name("Customer-ID") == normalize_column_name("CUSTOMERID")
    assert normalize_column_name("Unit Price") == normalize_column_name("unitprice")


# ---------------------------------------------------------------------------
# C2 — Mapping thủ công với file đổi tên cột
# ---------------------------------------------------------------------------


def test_c2_renamed_columns_are_not_auto_mapped():
    """File đổi tên cột thì mapping tự động phải để trống, không đoán bừa."""
    df = load_sample("base_sample.csv").rename(
        columns={"Invoice": "Ma_don_hang", "Quantity": "So_luong", "Price": "Don_gia"}
    )
    mapping, columns = auto_map(df)
    assert mapping["InvoiceNo"] is None
    assert not validate_mapping(mapping, columns).is_valid


def test_c2_manual_mapping_is_accepted_and_applied():
    """C2: map tay các cột đã đổi tên -> hợp lệ và rename đúng."""
    df = load_sample("base_sample.csv").rename(
        columns={
            "Invoice": "Ma_don_hang", "StockCode": "Ma_SP", "Quantity": "So_luong",
            "InvoiceDate": "Ngay_HD", "Price": "Don_gia", "Customer ID": "Ma_KH",
        }
    )
    manual = {
        "InvoiceNo": "Ma_don_hang", "StockCode": "Ma_SP", "Description": "Description",
        "Quantity": "So_luong", "InvoiceDate": "Ngay_HD", "UnitPrice": "Don_gia",
        "CustomerID": "Ma_KH", "Country": "Country",
    }
    assert validate_mapping(manual, list(df.columns)).is_valid
    mapped = apply_column_mapping(df, manual)
    assert {"InvoiceNo", "Quantity", "UnitPrice", "CustomerID"} <= set(mapped.columns)


def test_c2_mapping_one_source_to_two_targets_is_rejected():
    """Không được map cùng một cột nguồn cho hai cột chuẩn."""
    df = load_sample("base_sample.csv")
    bad = build_default_mapping(list(df.columns))
    bad["Description"] = bad["StockCode"]
    result = validate_mapping(bad, list(df.columns))
    assert not result.is_valid
    assert result.duplicate_sources


def test_c2_mapping_to_nonexistent_column_is_rejected():
    """Map tới cột không tồn tại trong file -> phải báo lỗi."""
    df = load_sample("base_sample.csv")
    bad = build_default_mapping(list(df.columns))
    bad["Country"] = "Khong_Ton_Tai"
    result = validate_mapping(bad, list(df.columns))
    assert not result.is_valid
    assert result.unknown_sources


# ---------------------------------------------------------------------------
# C3 — Điểm rủi ro nhất: CustomerID null KHÔNG được chặn upload (BR-03)
# ---------------------------------------------------------------------------


def test_c3_null_customerid_does_not_block_upload():
    """C3: file có 25% CustomerID null vẫn phải qua được bước validate.

    Đây là lỗi tốn kém nhất của Giai đoạn 1 nếu mắc phải: schema mục 2 ghi
    Customer ID là "Có (đối với RFM)", rất dễ bị hiện thực nhầm thành ràng buộc
    NOT NULL, và sẽ chặn mất 25,16% dataset (135.037 dòng) ngay từ cửa.
    """
    df = load_sample("test_missing_customerid.csv")
    mapping, columns = auto_map(df)
    result = validate_mapping(mapping, columns)
    assert result.is_valid, f"upload bị chặn sai: {result.messages()}"


def test_c3_null_customerid_survives_the_whole_flow():
    """Cả 300 dòng phải đi hết luồng mapping -> làm sạch, không mất dòng nào."""
    df = load_sample("test_missing_customerid.csv")
    mapping, _ = auto_map(df)
    cleaned = clean_pipeline(apply_column_mapping(df, mapping))
    assert len(cleaned) == 300
    assert int((~cleaned["HasCustomerID"]).sum()) == 75


# ---------------------------------------------------------------------------
# C4 — Thiếu cột bắt buộc phải chặn, báo lỗi rõ
# ---------------------------------------------------------------------------


def test_c4_missing_required_column_blocks_upload():
    """C4: thiếu InvoiceDate -> validate fail, nêu đúng tên cột."""
    df = load_sample("test_missing_column.csv")
    mapping, columns = auto_map(df)
    result = validate_mapping(mapping, columns)
    assert not result.is_valid
    assert "InvoiceDate" in result.missing_required
    assert any("InvoiceDate" in m for m in result.messages())


def test_c4_apply_mapping_refuses_invalid_mapping():
    """apply_column_mapping phải tự chặn, không phụ thuộc UI kiểm trước."""
    df = load_sample("test_missing_column.csv")
    mapping, _ = auto_map(df)
    with pytest.raises(ValueError, match="InvoiceDate"):
        apply_column_mapping(df, mapping)


def test_c4_unmapped_option_counts_as_missing():
    """Chọn '-- Not mapped --' cho cột bắt buộc cũng phải bị chặn."""
    df = load_sample("base_sample.csv")
    mapping, columns = auto_map(df)
    mapping["Quantity"] = NO_COLUMN_OPTION
    result = validate_mapping(mapping, columns)
    assert not result.is_valid
    assert "Quantity" in result.missing_required


# ---------------------------------------------------------------------------
# C5 — Cột tùy chọn được phép thiếu
# ---------------------------------------------------------------------------


def test_c5_optional_columns_may_be_absent():
    """C5: thiếu Description và Country vẫn cho đi tiếp (schema mục 1.4)."""
    df = load_sample("base_sample.csv").drop(columns=["Description", "Country"])
    mapping, columns = auto_map(df)
    assert validate_mapping(mapping, columns).is_valid


def test_c5_optional_columns_are_not_in_required_list():
    assert "Description" not in REQUIRED_COLUMNS
    assert "Country" not in REQUIRED_COLUMNS


# ---------------------------------------------------------------------------
# C6 — File hỏng không được làm sập app
# ---------------------------------------------------------------------------


def test_c6_wrong_dtype_file_does_not_crash_the_flow():
    """C6: file lẫn text trong Quantity vẫn chạy hết luồng, không raise."""
    df = load_sample("test_wrong_dtype.csv")
    mapping, _ = auto_map(df)
    cleaned = clean_pipeline(apply_column_mapping(df, mapping))
    assert len(cleaned) == 300
    assert pd.api.types.is_numeric_dtype(cleaned["Quantity"])


def test_c6_unsupported_file_type_is_rejected_clearly():
    """Đuôi file lạ phải bị từ chối bằng lỗi có thông điệp rõ ràng."""
    with pytest.raises(UnsupportedFileTypeError, match="csv|xlsx"):
        ensure_supported_file("du_lieu.txt")


def test_c6_extension_check_is_case_insensitive():
    ensure_supported_file("DATA.CSV")
    ensure_supported_file("DATA.XLSX")


# ---------------------------------------------------------------------------
# C7 — Tích hợp: mapping -> làm sạch (đúng luồng Home.py)
# ---------------------------------------------------------------------------


def test_c7_mapped_dataframe_is_accepted_by_clean_pipeline():
    """Mối nối Task 3 -> Task 2 phải chạy được đầu-cuối."""
    df = load_sample("base_sample.csv")
    mapping, _ = auto_map(df)
    cleaned = clean_pipeline(apply_column_mapping(df, mapping))
    assert len(cleaned) == 300
    for col in ("IsCancelled", "HasCustomerID", "IsServiceCode", "TotalPrice"):
        assert col in cleaned.columns


# ---------------------------------------------------------------------------
# C8 — Lỗi biên phát hiện ở vòng soi sâu (29/07/2026)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason="T3-02: apply_column_mapping chỉ gọi df.rename() mà không kiểm tra "
           "tên đích có trùng cột sẵn có không. File vừa có 'UnitPrice' vừa có "
           "'Price', người dùng map UnitPrice<-Price -> hai cột cùng tên "
           "'UnitPrice' -> clean_pipeline vỡ với thông báo vô nghĩa.",
)
def test_c8_rename_must_not_create_duplicate_columns():
    df = load_sample("base_sample.csv")
    df["UnitPrice"] = df["Price"] * 1.2
    mapping = build_default_mapping(list(df.columns))
    mapping["UnitPrice"] = "Price"
    assert validate_mapping(mapping, list(df.columns)).is_valid
    mapped = apply_column_mapping(df, mapping)
    cols = list(mapped.columns)
    dup = sorted({c for c in cols if cols.count(c) > 1})
    assert not dup, f"cột bị trùng sau khi rename: {dup}"


@pytest.mark.xfail(
    strict=True,
    reason="T3-04: normalized_source là dict comprehension nên hai cột khác "
           "nhau cùng chuẩn hoá về một key ('customer_id' và 'Customer-ID' "
           "-> 'customerid') sẽ đè nhau, cột sau thắng, không cảnh báo.",
)
def test_c8_ambiguous_source_columns_are_reported():
    df = load_sample("base_sample.csv").rename(columns={"Customer ID": "customer_id"})
    df["Customer-ID"] = 999
    mapping = build_default_mapping(list(df.columns))
    result = validate_mapping(mapping, list(df.columns))
    assert not result.is_valid, (
        f"hai cột cùng chuẩn hoá về 'customerid' nhưng vẫn hợp lệ; "
        f"đã chọn {mapping['CustomerID']!r}"
    )


@pytest.mark.xfail(
    strict=True,
    reason="T3-03: _read_csv thử utf-8-sig -> utf-8 -> latin1. latin1 giải mã "
           "được MỌI chuỗi byte nên không bao giờ raise; file UTF-16 bị đọc "
           "thành cột rác 'ÿþI', 'Unnamed: 1'... mà không báo lỗi.",
)
def test_c8_undecodable_file_raises_instead_of_producing_garbage():
    import io as _io

    df = pd.DataFrame({
        "Invoice": ["536365"], "StockCode": ["85123A"], "Description": ["Nến thơm"],
        "Quantity": [6], "InvoiceDate": ["12/1/10 8:26"], "Price": [2.55],
        "Customer ID": [17850], "Country": ["Việt Nam"],
    })
    buf = _io.BytesIO()
    df.to_csv(buf, index=False, encoding="utf-16")
    buf.seek(0)
    columns = column_mapper.read_uploaded_columns(buf, "utf16.csv")
    assert "Invoice" in columns, f"đọc sai mà không báo lỗi, cột nhận được: {columns[:3]}"


@pytest.mark.xfail(
    strict=True,
    reason="T3-06: apply_column_mapping giữ lại cả cột không được map, nên "
           "cột rác đi thẳng vào dữ liệu sạch. Cột trùng tên với cột phái "
           "sinh (IsCancelled...) thì bị ghi đè âm thầm.",
)
def test_c8_unmapped_columns_are_dropped():
    df = load_sample("base_sample.csv")
    df["Ghi_chu_noi_bo"] = "rác"
    mapping = build_default_mapping(list(df.columns))
    mapped = apply_column_mapping(df, mapping)
    assert "Ghi_chu_noi_bo" not in mapped.columns


@pytest.mark.xfail(
    strict=True,
    reason="T3-07: file chỉ có header (0 dòng dữ liệu) đi hết luồng và UI báo "
           "'Processed 0 rows' như một lần chạy thành công.",
)
def test_c8_empty_file_is_rejected():
    import io as _io

    buf = _io.BytesIO(b"Invoice,StockCode,Quantity,InvoiceDate,Price,Customer ID\n")
    df = column_mapper.read_uploaded_dataframe(buf, "empty.csv")
    mapping = build_default_mapping(list(df.columns))
    result = validate_mapping(mapping, list(df.columns))
    assert not result.is_valid, "file 0 dòng vẫn được coi là hợp lệ"


@pytest.mark.xfail(
    strict=True,
    reason="QA-16: luồng batch (python src/data/cleaning.py) xuất cột "
           "Invoice/Price/'Customer ID', còn luồng UI xuất "
           "InvoiceNo/UnitPrice/CustomerID — hai schema khác nhau cùng ghi ra "
           "cleaned_transactions.csv. Epic 2 không biết sẽ nhận schema nào.",
)
def test_c7_batch_and_ui_paths_produce_the_same_schema():
    """Hai đường chạy phải cho ra cùng một bộ tên cột."""
    df = load_sample("base_sample.csv")
    mapping, _ = auto_map(df)
    batch = clean_pipeline(df.copy())
    via_ui = clean_pipeline(apply_column_mapping(df.copy(), mapping))
    assert set(batch.columns) == set(via_ui.columns), (
        f"chỉ có ở batch: {sorted(set(batch.columns) - set(via_ui.columns))} | "
        f"chỉ có ở UI: {sorted(set(via_ui.columns) - set(batch.columns))}"
    )
