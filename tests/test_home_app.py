"""Kiểm thử giao diện Streamlit `src/app/Home.py` (Task 3) — KAN-12 (QA/QC).

Chạy:  pytest tests/test_home_app.py -v

Vì sao có file này
------------------
`tests/test_upload_mapping.py` kiểm phần logic trong `column_mapper.py` bằng cách
**mô phỏng lại** chuỗi lệnh mà `Home.py` chạy. Mô phỏng không phải là chạy thật:
mọi thứ nằm riêng trong `Home.py` — thứ tự gọi hàm, điều kiện bật/tắt nút,
nhánh `try/except`, tham số truyền cho widget — đều không được kiểm.

File này chạy **chính `Home.py`** bằng `streamlit.testing.v1.AppTest`: nạp app,
gán file vào ô upload, bấm nút, rồi đọc kết quả hiện ra trên giao diện — đúng
những gì người dùng thật làm, không cần mở trình duyệt.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

AppTest = pytest.importorskip(
    "streamlit.testing.v1", reason="Cần streamlit >= 1.28 để chạy AppTest"
).AppTest

pytest.importorskip("src.app.column_mapper", reason="Task 3 chưa có trên nhánh này")

APP = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "app", "Home.py"))
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "test_samples")
CSV_MIME = "text/csv"


def read_sample(name: str) -> bytes:
    path = os.path.join(SAMPLE_DIR, name)
    if not os.path.exists(path):
        pytest.skip(f"Thiếu file test {name}. Chạy: python scripts/generate_test_samples.py")
    with open(path, "rb") as fh:
        return fh.read()


def run_app(upload: str | None = None, timeout: int = 120):
    """Nạp app; nếu có `upload` thì gán file vào ô upload rồi chạy lại."""
    at = AppTest.from_file(APP, default_timeout=timeout)
    at.run()
    if upload is not None:
        at.file_uploader[0].set_value((upload, read_sample(upload), CSV_MIME))
        at.run()
    return at


def click_process(at):
    """Bấm nút 'Apply mapping and clean data'."""
    at.button[0].click().run()
    return at


def texts(elements) -> list[str]:
    return [e.value for e in elements]


# ---------------------------------------------------------------------------
# Khởi động
# ---------------------------------------------------------------------------


def test_app_starts_without_error():
    at = run_app()
    assert not at.exception, f"app lỗi ngay khi khởi động: {texts(at.exception)}"
    assert at.title[0].value == "Upload & Column Mapping"


def test_app_prompts_for_a_file_before_anything_else():
    at = run_app()
    assert any("Upload a CSV or XLSX file" in m for m in texts(at.info))
    assert not at.button, "chưa upload gì mà đã có nút xử lý"


# ---------------------------------------------------------------------------
# Luồng chính
# ---------------------------------------------------------------------------


def test_uploading_valid_file_shows_valid_mapping():
    at = run_app("base_sample.csv")
    assert not at.exception, texts(at.exception)
    assert any("Mapping is valid" in s for s in texts(at.success))
    assert not at.error, f"không được có lỗi nào: {texts(at.error)}"


def test_selectboxes_are_rendered_for_all_eight_standard_columns():
    at = run_app("base_sample.csv")
    assert len(at.selectbox) == 8, f"phải có 8 ô chọn, đang có {len(at.selectbox)}"


def test_auto_mapping_preselects_the_right_source_columns():
    at = run_app("base_sample.csv")
    chosen = [sb.value for sb in at.selectbox]
    assert "Invoice" in chosen
    assert "Price" in chosen
    assert "Customer ID" in chosen
    assert "-- Not mapped --" not in chosen, "còn cột chưa được khớp tự động"


def test_process_button_is_enabled_when_mapping_is_valid():
    at = run_app("base_sample.csv")
    assert at.button, "không tìm thấy nút xử lý"
    assert not at.button[0].disabled


def test_full_flow_processes_the_file_and_reports_row_count():
    """Bấm nút và đi hết luồng upload -> mapping -> làm sạch."""
    at = click_process(run_app("base_sample.csv"))
    assert not at.exception, texts(at.exception)
    assert not at.error, f"luồng đầy đủ báo lỗi: {texts(at.error)}"
    assert any("300" in s for s in texts(at.success)), texts(at.success)


def test_previews_are_rendered_after_processing():
    """Sau khi xử lý phải hiện 3 bảng: cột nguồn, dữ liệu đã map, dữ liệu đã sạch.

    `AppTest` không bóc tách được `st.download_button` thành accessor riêng, nên
    QA kiểm bằng các bảng preview — chúng nằm sau nút tải về trong `Home.py`,
    có nghĩa là luồng đã chạy tới cuối.
    """
    at = click_process(run_app("base_sample.csv"))
    assert len(at.dataframe) == 3, f"phải có 3 bảng, đang có {len(at.dataframe)}"
    assert any("Cleaning log" in e.label for e in at.expander), "thiếu mục Cleaning log"


# ---------------------------------------------------------------------------
# C3 qua giao diện thật — điểm rủi ro nhất của Giai đoạn 1
# ---------------------------------------------------------------------------


def test_c3_file_with_null_customerid_is_accepted_by_the_real_ui():
    """25% Customer ID trống vẫn phải qua được, kiểm trên chính giao diện."""
    at = run_app("test_missing_customerid.csv")
    assert any("Mapping is valid" in s for s in texts(at.success)), texts(at.error)
    assert not at.button[0].disabled, "nút xử lý bị khoá vì Customer ID trống"


def test_c3_file_with_null_customerid_completes_the_whole_flow():
    at = click_process(run_app("test_missing_customerid.csv"))
    assert not at.error, texts(at.error)
    assert any("300" in s for s in texts(at.success)), (
        f"phải giữ đủ 300 dòng: {texts(at.success)}"
    )


# ---------------------------------------------------------------------------
# File hỏng
# ---------------------------------------------------------------------------


def test_missing_required_column_blocks_the_button():
    at = run_app("test_missing_column.csv")
    assert any("InvoiceDate" in s for s in texts(at.error)), texts(at.error)
    assert at.button[0].disabled, "thiếu cột bắt buộc mà nút xử lý vẫn bấm được"


def test_wrong_dtype_file_does_not_crash_the_app():
    at = click_process(run_app("test_wrong_dtype.csv"))
    assert not at.exception, f"app sập: {texts(at.exception)}"


def test_cancelled_invoice_file_completes():
    at = click_process(run_app("test_cancelled_invoice.csv"))
    assert not at.error, texts(at.error)
    assert any("320" in s for s in texts(at.success)), texts(at.success)


# ---------------------------------------------------------------------------
# Lỗi phát hiện khi chạy app thật
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason="T3-10: Home.py dùng use_container_width, đã bị Streamlit đánh dấu "
           "deprecated với hạn gỡ bỏ 2025-12-31 — hạn này ĐÃ QUA. Mỗi lần "
           "render bảng, terminal in ra cảnh báo. Cần đổi sang width='stretch'.",
)
def test_t3_10_no_deprecated_streamlit_parameters():
    """Không được dùng tham số widget đã hết hạn hỗ trợ."""
    with open(APP, encoding="utf-8") as fh:
        source = fh.read()
    assert "use_container_width" not in source, (
        "use_container_width đã hết hạn 2025-12-31, thay bằng width='stretch'"
    )


@pytest.mark.xfail(
    strict=True,
    reason="T3-07: file chỉ có dòng tiêu đề đi hết luồng và báo "
           "'Processed 0 rows' như một lần chạy thành công.",
)
def test_t3_07_empty_file_is_rejected_by_the_ui(tmp_path):
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    header_only = b"Invoice,StockCode,Quantity,InvoiceDate,Price,Customer ID\n"
    at.file_uploader[0].set_value(("empty.csv", header_only, CSV_MIME))
    at.run()
    if at.button and not at.button[0].disabled:
        at.button[0].click().run()
    assert at.error, "file 0 dòng phải bị từ chối, không được báo thành công"
