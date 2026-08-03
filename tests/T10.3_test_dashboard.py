"""Task 10.3 — Kiểm thử Task 9: Giao diện hiển thị bảng RFM và biểu đồ phân phối.

Chạy:
    python -m pytest "tests/T10.3_test_dashboard.py" -v

Sinh lại file mẫu kiểm thử:
    python "tests/T10.3_test_dashboard.py"

Phạm vi
-------
Đề bài Task 10.3 quy định "Viết code Pytest" chỉ cho **Nhóm 3 — Kiểm thử tính
chính xác của dữ liệu hiển thị**; 5 nhóm còn lại ghi "Review thủ công". Trong
thực tế `src/visualization/rfm_dashboard.py` tách logic thành các hàm thuần
(`sort_rfm_table`, `filter_by_customer_id`, `paginate_dataframe`,
`build_descriptive_stats`, `make_histogram`, `make_boxplot`), nên phần lớn
review thủ công vẫn kiểm chứng được bằng Pytest — kể cả sắp xếp, tìm kiếm,
phân trang và trường hợp đặc biệt. QA tận dụng điều đó để giảm phần thuần
thị giác (bố cục, màu sắc) xuống review thủ công thật sự, ghi trong
`outputs/reports/T10.3_dashboard_validation_report.md`.

Ngoài kiểm ở mức hàm, QA còn chạy **chính `src/app/Home.py`** bằng
`streamlit.testing.v1.AppTest` — chọn trang "RFM Dashboard", thao tác tìm
kiếm/sắp xếp/phân trang trên giao diện thật — để xác nhận các hàm thuần được
nối đúng vào UI, không chỉ đúng khi gọi độc lập.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.visualization.rfm_dashboard import (  # noqa: E402
    FEATURE_COLUMNS,
    ID_COLUMN,
    REQUIRED_COLUMNS,
    DashboardDataError,
    build_dataset_options,
    build_descriptive_stats,
    filter_by_customer_id,
    load_rfm_outputs,
    make_boxplot,
    make_histogram,
    paginate_dataframe,
    sort_rfm_table,
)

RFM_PATH = ROOT / "data" / "processed" / "rfm_table.csv"
SCALED_PATH = ROOT / "data" / "processed" / "rfm_scaled.csv"
SAMPLES_PATH = ROOT / "outputs" / "results" / "T10.3_dashboard_validation_samples.csv"

RANDOM_SEED = 42
SAMPLE_SIZE = 20


def _require_real_data() -> None:
    if not RFM_PATH.exists() or not SCALED_PATH.exists():
        pytest.skip("Thiếu data/processed/rfm_table.csv hoặc rfm_scaled.csv")


@pytest.fixture(scope="module")
def outputs():
    _require_real_data()
    return load_rfm_outputs()


@pytest.fixture(scope="module")
def raw(outputs):
    return outputs.raw


@pytest.fixture(scope="module")
def scaled(outputs):
    return outputs.scaled


@pytest.fixture(scope="module")
def source_raw():
    """Đọc thẳng file nguồn, KHÔNG qua dashboard, để đối chiếu độc lập."""
    _require_real_data()
    df = pd.read_csv(RFM_PATH)
    df[ID_COLUMN] = df[ID_COLUMN].astype(str)
    return df


@pytest.fixture(scope="module")
def source_scaled():
    _require_real_data()
    df = pd.read_csv(SCALED_PATH)
    df[ID_COLUMN] = df[ID_COLUMN].astype(str)
    return df


# ===========================================================================
# NHÓM 1 — Giao diện bảng RFM (phần kiểm được bằng hàm thuần)
# ===========================================================================


def test_group1_table_has_all_required_columns(raw):
    """Bảng RFM hiển thị đầy đủ các cột theo đặc tả Task 6."""
    assert list(raw.columns) == REQUIRED_COLUMNS


def test_group1_column_names_match_design_spec(raw):
    """Tên cột đúng CustomerID, Recency, Frequency, Monetary — không dấu cách,
    không khác biệt hoa/thường so với docs/T06_rfm_specification.md §5."""
    assert list(raw.columns) == ["CustomerID", "Recency", "Frequency", "Monetary"]


def test_group1_data_types_match_design_spec(raw):
    """CustomerID: String, Recency/Frequency: Integer, Monetary: Float (T06 §5)."""
    assert raw[ID_COLUMN].dtype == object, "CustomerID phải là string"
    assert pd.api.types.is_integer_dtype(raw["Recency"])
    assert pd.api.types.is_integer_dtype(raw["Frequency"])
    assert pd.api.types.is_float_dtype(raw["Monetary"])


def test_group1_row_count_matches_source_file(raw, source_raw):
    """Số bản ghi hiển thị đúng bằng số dòng trong rfm_table.csv (Task 7)."""
    assert len(raw) == len(source_raw)


def test_group1_no_row_is_dropped_or_duplicated_on_load(raw, source_raw):
    """Nạp qua dashboard không được làm mất hay nhân đôi khách hàng nào."""
    assert set(raw[ID_COLUMN]) == set(source_raw[ID_COLUMN])
    assert raw[ID_COLUMN].duplicated().sum() == 0


# ===========================================================================
# NHÓM 2 — Biểu đồ phân phối
# ===========================================================================


def test_group2_histogram_can_be_built_for_all_three_features(raw):
    """Vẽ được histogram cho cả Recency, Frequency, Monetary."""
    for feature in FEATURE_COLUMNS:
        chart = make_histogram(raw, feature)
        assert chart is not None


def test_group2_histogram_axis_titles_are_present(raw):
    """Tiêu đề trục X là tên đặc trưng, trục Y là số khách hàng."""
    for feature in FEATURE_COLUMNS:
        spec = make_histogram(raw, feature).to_dict()
        assert spec["encoding"]["x"]["title"] == feature
        assert spec["encoding"]["y"]["title"] == "Customers"


def test_group2_histogram_rejects_unknown_feature(raw):
    """Không cho vẽ histogram cho cột không thuộc RFM."""
    with pytest.raises(ValueError, match="Unknown RFM feature"):
        make_histogram(raw, "CustomerID")


def test_group2_boxplot_can_be_built(raw):
    chart = make_boxplot(raw)
    assert chart is not None


def test_group2_scaled_view_is_available_as_the_normalized_chart(scaled):
    """'Kiểm tra biểu đồ sau chuẩn hóa (nếu có)': view StandardScaler luôn có sẵn."""
    for feature in FEATURE_COLUMNS:
        assert make_histogram(scaled, feature) is not None


def test_group2_scaled_distribution_mean_and_std_match_task8_output(scaled):
    """Hình dạng biểu đồ 'sau chuẩn hóa' phải khớp kết quả Task 8: mean≈0, std≈1."""
    for feature in FEATURE_COLUMNS:
        assert scaled[feature].mean() == pytest.approx(0.0, abs=1e-6)
        assert scaled[feature].std(ddof=0) == pytest.approx(1.0, abs=1e-6)


@pytest.mark.xfail(
    strict=True,
    reason="BUG-002: Task 8 (notebooks/rfm_preprocessing.ipynb) không xuất cột "
           "Frequency_log/Monetary_log ra rfm_table.csv hay rfm_scaled.csv (ghi "
           "nhận từ T10.2). Do đó Dataset view của dashboard chỉ có 2 lựa chọn "
           "(RFM original, RFM after StandardScaler), thiếu hẳn view 'sau "
           "log-transform' mà mục 2 của đề bài Task 10.3 liệt kê riêng.",
)
def test_group2_log_transform_view_is_available(outputs):
    """'Kiểm tra biểu đồ sau chuẩn hóa (nếu có)' — bao gồm cả view log-transform."""
    options = build_dataset_options(outputs)
    assert any("log" in label.lower() for label in options), (
        f"không có view log-transform, chỉ có: {list(options)}"
    )


# ===========================================================================
# NHÓM 3 — Tính chính xác của dữ liệu hiển thị (yêu cầu bắt buộc viết Pytest)
# ===========================================================================


def test_group3_random_sample_matches_source_exactly(raw, source_raw):
    """Đối chiếu ngẫu nhiên N CustomerID: R, F, M trên 'giao diện' khớp tuyệt
    đối với file nguồn rfm_table.csv."""
    sample_ids = source_raw[ID_COLUMN].sample(SAMPLE_SIZE, random_state=RANDOM_SEED)
    for customer_id in sample_ids:
        shown = raw.loc[raw[ID_COLUMN] == customer_id, FEATURE_COLUMNS].iloc[0]
        truth = source_raw.loc[source_raw[ID_COLUMN] == customer_id, FEATURE_COLUMNS].iloc[0]
        for col in FEATURE_COLUMNS:
            assert shown[col] == truth[col], f"{customer_id}.{col}: {shown[col]} != {truth[col]}"


def test_group3_random_sample_matches_source_on_scaled_view(scaled, source_scaled):
    """Tương tự nhưng trên view 'RFM after StandardScaler'."""
    sample_ids = source_scaled[ID_COLUMN].sample(SAMPLE_SIZE, random_state=RANDOM_SEED)
    for customer_id in sample_ids:
        shown = scaled.loc[scaled[ID_COLUMN] == customer_id, FEATURE_COLUMNS].iloc[0]
        truth = source_scaled.loc[source_scaled[ID_COLUMN] == customer_id, FEATURE_COLUMNS].iloc[0]
        for col in FEATURE_COLUMNS:
            assert shown[col] == pytest.approx(truth[col], abs=1e-9), (
                f"{customer_id}.{col}: {shown[col]} != {truth[col]}"
            )


def test_group3_customer_count_matches_source(raw, scaled, source_raw, source_scaled):
    """Số lượng khách hàng đúng ở cả hai view."""
    assert len(raw) == len(source_raw)
    assert len(scaled) == len(source_scaled)


def test_group3_descriptive_statistics_match_source(raw, source_raw):
    """Giá trị thống kê (mean, median, std, min, max) khớp file nguồn."""
    stats = build_descriptive_stats(raw)
    for col in FEATURE_COLUMNS:
        assert stats.loc["Mean", col] == pytest.approx(source_raw[col].mean(), rel=1e-9)
        assert stats.loc["Median (Q2)", col] == pytest.approx(source_raw[col].median(), rel=1e-9)
        assert stats.loc["Minimum", col] == source_raw[col].min()
        assert stats.loc["Maximum", col] == source_raw[col].max()


def test_group3_total_customers_metric_matches_both_files(raw, scaled):
    """Chỉ số 'Total Customers'/'Scaled Rows' trên đầu trang phải đúng bằng
    độ dài hai DataFrame — đúng công thức Home.py dùng để tính metric."""
    assert len(raw) == len(scaled) == 4324, (
        "Nếu con số này thay đổi, Task 7/8 đã sinh lại dữ liệu — cần đồng bộ "
        "lại file mẫu kiểm thử T10.3_dashboard_validation_samples.csv"
    )


# ===========================================================================
# NHÓM 4 — Chức năng tương tác (đề bài ghi "Review thủ công", QA phủ thêm Pytest)
# ===========================================================================


def test_group4_sort_by_monetary_descending_matches_source_ranking(raw, source_raw):
    """Sắp xếp Monetary giảm dần trên bảng phải khớp thứ hạng thật của dữ liệu."""
    sorted_df = sort_rfm_table(raw, "Monetary", ascending=False)
    expected_top10 = source_raw.nlargest(10, "Monetary")[ID_COLUMN].tolist()
    assert sorted_df.head(10)[ID_COLUMN].tolist() == expected_top10


def test_group4_sort_does_not_mutate_the_underlying_dataframe(raw):
    """Sắp xếp không được làm thay đổi dữ liệu gốc (đúng yêu cầu đề bài)."""
    before = raw.copy(deep=True)
    sort_rfm_table(raw, "Monetary", ascending=False)
    pd.testing.assert_frame_equal(raw, before)


def test_group4_search_returns_only_matching_customers(raw):
    """Tìm kiếm theo CustomerID chỉ trả về đúng các khách hàng chứa chuỗi tìm."""
    result = filter_by_customer_id(raw, "12347")
    assert len(result) >= 1
    assert all("12347" in cid for cid in result[ID_COLUMN])


def test_group4_search_is_case_insensitive_and_whitespace_tolerant(raw):
    real_id = raw[ID_COLUMN].iloc[0]
    padded = f"  {real_id.upper()}  "
    result = filter_by_customer_id(raw, padded)
    assert real_id in result[ID_COLUMN].tolist()


def test_group4_search_does_not_mutate_the_underlying_dataframe(raw):
    before = raw.copy(deep=True)
    filter_by_customer_id(raw, "12347")
    pd.testing.assert_frame_equal(raw, before)


def test_group4_empty_search_returns_the_full_table(raw):
    """Ô tìm kiếm để trống thì hiển thị toàn bộ bảng, không lọc gì."""
    result = filter_by_customer_id(raw, "")
    assert len(result) == len(raw)


def test_group4_search_with_no_match_returns_empty_without_error(raw):
    """Tìm mã không tồn tại: trả về 0 dòng, không raise lỗi."""
    result = filter_by_customer_id(raw, "no_such_customer_id_xyz")
    assert len(result) == 0


@pytest.mark.parametrize("special_query", ["(", "[", ".*", "\\", "^$+?"])
def test_group4_search_handles_regex_special_characters_safely(raw, special_query):
    """Ký tự đặc biệt của regex không được làm crash tìm kiếm (khớp literal)."""
    result = filter_by_customer_id(raw, special_query)
    assert isinstance(result, pd.DataFrame)


def test_group4_pagination_pages_do_not_overlap(raw):
    """Hai trang liên tiếp không chứa khách hàng trùng nhau."""
    page1 = paginate_dataframe(raw, page_size=25, page_number=1)
    page2 = paginate_dataframe(raw, page_size=25, page_number=2)
    overlap = set(page1.dataframe[ID_COLUMN]) & set(page2.dataframe[ID_COLUMN])
    assert not overlap


def test_group4_pagination_covers_every_row_exactly_once(raw):
    """Duyệt hết tất cả các trang phải khớp đúng 100% dữ liệu, không thiếu không thừa."""
    page_size = 100
    first = paginate_dataframe(raw, page_size=page_size, page_number=1)
    seen_ids: list[str] = []
    for page_number in range(1, first.total_pages + 1):
        page = paginate_dataframe(raw, page_size=page_size, page_number=page_number)
        seen_ids.extend(page.dataframe[ID_COLUMN].tolist())
    assert len(seen_ids) == len(raw)
    assert set(seen_ids) == set(raw[ID_COLUMN])
    assert len(seen_ids) == len(set(seen_ids)), "có khách hàng bị lặp giữa các trang"


def test_group4_pagination_clamps_out_of_range_page_number(raw):
    """Yêu cầu trang vượt quá tổng số trang phải được kẹp về trang cuối, không lỗi."""
    page = paginate_dataframe(raw, page_size=25, page_number=99999)
    assert page.page_number == page.total_pages


def test_group4_sort_and_filter_compose_correctly(raw):
    """Kết hợp tìm kiếm rồi sắp xếp phải cho kết quả nhất quán."""
    filtered = filter_by_customer_id(raw, "1")
    sorted_and_filtered = sort_rfm_table(filtered, "Monetary", ascending=False)
    assert len(sorted_and_filtered) == len(filtered)
    assert sorted_and_filtered["Monetary"].is_monotonic_decreasing


@pytest.mark.xfail(
    strict=True,
    reason="BUG-007: sort_rfm_table dùng df.sort_values(sort_column, ...) trực "
           "tiếp. CustomerID được lưu dưới dạng CHUỖI (đúng T06), nên sắp xếp "
           "theo CustomerID là sắp xếp TỪ ĐIỂN, không phải sắp xếp SỐ. Dữ liệu "
           "hiện tại của Online Retail II toàn CustomerID 5 chữ số nên chưa lộ "
           "ra, nhưng chỉ cần một khách hàng mã số khác độ dài là sai ngay.",
)
def test_group4_sort_by_customer_id_is_numeric_not_lexicographic():
    """Sắp xếp theo CustomerID phải theo giá trị SỐ, không theo ký tự."""
    mixed = pd.DataFrame({
        ID_COLUMN: ["9999", "12347", "12348", "555"],
        "Recency": [1, 2, 3, 4],
        "Frequency": [1, 2, 3, 4],
        "Monetary": [10.0, 20.0, 30.0, 40.0],
    })
    ascending = sort_rfm_table(mixed, ID_COLUMN, ascending=True)
    assert ascending[ID_COLUMN].tolist() == ["555", "9999", "12347", "12348"], (
        f"kỳ vọng sắp theo số 555 < 9999 < 12347 < 12348, thực tế: "
        f"{ascending[ID_COLUMN].tolist()} (đây là thứ tự CHUỖI)"
    )


# ===========================================================================
# NHÓM 5 — Trường hợp đặc biệt
# ===========================================================================


def _make_temp_files(tmp_path, df: pd.DataFrame):
    raw_path = tmp_path / "rfm_table.csv"
    scaled_path = tmp_path / "rfm_scaled.csv"
    df.to_csv(raw_path, index=False)
    df.to_csv(scaled_path, index=False)
    return raw_path, scaled_path


def test_group5_single_customer_dataset_loads_without_error(tmp_path):
    """Dữ liệu chỉ có 1 khách hàng: nạp được, không crash."""
    df = pd.DataFrame({
        ID_COLUMN: ["12347"], "Recency": [2], "Frequency": [7], "Monetary": [4310.0],
    })
    raw_path, scaled_path = _make_temp_files(tmp_path, df)
    outputs = load_rfm_outputs(raw_path, scaled_path)
    assert len(outputs.raw) == 1


def test_group5_single_customer_statistics_show_nan_std_not_error(tmp_path):
    """Độ lệch chuẩn của 1 điểm dữ liệu phải là NaN có kiểm soát, không phải lỗi."""
    df = pd.DataFrame({
        ID_COLUMN: ["12347"], "Recency": [2], "Frequency": [7], "Monetary": [4310.0],
    })
    raw_path, scaled_path = _make_temp_files(tmp_path, df)
    outputs = load_rfm_outputs(raw_path, scaled_path)
    stats = build_descriptive_stats(outputs.raw)
    assert stats.loc["Standard Deviation"].isna().all()
    assert stats.loc["Mean", "Monetary"] == 4310.0


def test_group5_single_customer_chart_functions_do_not_raise(tmp_path):
    """Vẽ biểu đồ với 1 điểm dữ liệu không được ném lỗi."""
    df = pd.DataFrame({
        ID_COLUMN: ["12347"], "Recency": [2], "Frequency": [7], "Monetary": [4310.0],
    })
    raw_path, scaled_path = _make_temp_files(tmp_path, df)
    outputs = load_rfm_outputs(raw_path, scaled_path)
    for feature in FEATURE_COLUMNS:
        assert make_histogram(outputs.raw, feature) is not None
    assert make_boxplot(outputs.raw) is not None


def test_group5_empty_dataset_raises_controlled_error(tmp_path):
    """Dữ liệu rỗng phải báo DashboardDataError có kiểm soát, không phải traceback thô."""
    df = pd.DataFrame(columns=[ID_COLUMN, *FEATURE_COLUMNS])
    raw_path, scaled_path = _make_temp_files(tmp_path, df)
    with pytest.raises(DashboardDataError, match="empty"):
        load_rfm_outputs(raw_path, scaled_path)


def test_group5_missing_scaled_file_raises_controlled_error(tmp_path):
    """Mở dashboard khi Task 8 chưa chạy xong (thiếu rfm_scaled.csv) phải báo lỗi rõ."""
    df = pd.DataFrame({
        ID_COLUMN: ["12347"], "Recency": [2], "Frequency": [7], "Monetary": [4310.0],
    })
    raw_path = tmp_path / "rfm_table.csv"
    df.to_csv(raw_path, index=False)
    missing_scaled_path = tmp_path / "rfm_scaled.csv"

    with pytest.raises(DashboardDataError, match="rfm_scaled.csv"):
        load_rfm_outputs(raw_path, missing_scaled_path)


def test_group5_missing_required_column_raises_controlled_error(tmp_path):
    """Thiếu cột bắt buộc (vd Monetary) phải báo lỗi rõ ràng, không KeyError thô."""
    df = pd.DataFrame({ID_COLUMN: ["12347"], "Recency": [2], "Frequency": [7]})
    raw_path, scaled_path = _make_temp_files(tmp_path, df)
    with pytest.raises(DashboardDataError, match="Monetary"):
        load_rfm_outputs(raw_path, scaled_path)


def test_group5_large_dataset_loads_within_reasonable_time(tmp_path):
    """Dữ liệu lớn (108.100 dòng, gấp 25 lần dữ liệu thật) vẫn nạp và xử lý được."""
    import time

    real = pd.read_csv(RFM_PATH) if RFM_PATH.exists() else pd.DataFrame({
        ID_COLUMN: range(4324), "Recency": [10] * 4324,
        "Frequency": [2] * 4324, "Monetary": [100.0] * 4324,
    })
    big = pd.concat(
        [real.assign(**{ID_COLUMN: real[ID_COLUMN].astype(float) + i * 100_000})
         for i in range(25)],
        ignore_index=True,
    )
    raw_path, scaled_path = _make_temp_files(tmp_path, big)

    start = time.perf_counter()
    outputs = load_rfm_outputs(raw_path, scaled_path)
    build_descriptive_stats(outputs.raw)
    paginate_dataframe(sort_rfm_table(outputs.raw, "Monetary", False), 25, 1)
    elapsed = time.perf_counter() - start

    assert len(outputs.raw) == len(big)
    assert elapsed < 5.0, f"quá chậm với dữ liệu lớn: {elapsed:.2f}s"


@pytest.mark.xfail(
    strict=True,
    reason="BUG-008: make_boxplot() gọi df.melt() rồi vẽ 3 đặc trưng trên "
           "boxplot; với 4.324 khách (12.972 dòng sau melt), Altair.to_dict() "
           "vượt giới hạn mặc định 5.000 dòng và ném MaxRowsError. Streamlit tự "
           "render qua Arrow nên UI thật KHÔNG vỡ, nhưng bất kỳ chỗ nào khác gọi "
           "make_boxplot(df).to_dict()/.save() trực tiếp trên dữ liệu lớn (xuất "
           "ảnh tĩnh, notebook, script) sẽ crash ngay lập tức.",
)
def test_group5_boxplot_spec_is_exportable_for_large_dataset(raw):
    """Chart phải xuất được ra dict/JSON ngay cả với dữ liệu đầy đủ 4.324 khách."""
    make_boxplot(raw).to_dict()


# ===========================================================================
# NHÓM 6 — Tính ổn định
# ===========================================================================


def test_group6_reloading_the_same_files_gives_identical_result():
    """Mở lại giao diện nhiều lần với cùng dữ liệu phải cho kết quả giống hệt."""
    _require_real_data()
    first = load_rfm_outputs()
    second = load_rfm_outputs()
    pd.testing.assert_frame_equal(first.raw, second.raw)
    pd.testing.assert_frame_equal(first.scaled, second.scaled)


def test_group6_reloading_five_times_is_consistent():
    """Tải lại dữ liệu 5 lần liên tiếp, số khách hàng luôn nhất quán."""
    _require_real_data()
    counts = {len(load_rfm_outputs().raw) for _ in range(5)}
    assert len(counts) == 1, f"số khách hàng đổi qua các lần tải lại: {counts}"


def test_group6_sort_search_paginate_are_pure_and_repeatable(raw):
    """Gọi lại cùng thao tác tương tác nhiều lần phải cho cùng kết quả."""
    def run_once():
        filtered = filter_by_customer_id(raw, "1")
        sorted_df = sort_rfm_table(filtered, "Monetary", ascending=False)
        return paginate_dataframe(sorted_df, page_size=25, page_number=1).dataframe

    first, second = run_once(), run_once()
    pd.testing.assert_frame_equal(
        first.reset_index(drop=True), second.reset_index(drop=True)
    )


# ===========================================================================
# Tích hợp — chạy chính src/app/Home.py bằng AppTest (không chỉ mô phỏng)
# ===========================================================================

AppTest = pytest.importorskip(
    "streamlit.testing.v1", reason="Cần streamlit >= 1.28 để chạy AppTest"
).AppTest

HOME_APP = ROOT / "src" / "app" / "Home.py"


def _open_dashboard():
    at = AppTest.from_file(str(HOME_APP), default_timeout=90)
    at.run()
    at.radio[0].set_value("RFM Dashboard").run()
    return at


def test_ui_dashboard_page_opens_without_exception():
    _require_real_data()
    at = _open_dashboard()
    assert not at.exception, [e.value for e in at.exception]
    assert at.title[0].value == "RFM Feature Dashboard"


def test_ui_metrics_match_customer_count():
    _require_real_data()
    at = _open_dashboard()
    total = int(at.metric[0].value.replace(",", ""))
    scaled_rows = int(at.metric[1].value.replace(",", ""))
    assert total == scaled_rows == 4324


def test_ui_search_on_real_widgets_matches_source_file(source_raw):
    at = _open_dashboard()
    tab = at.tabs[0]
    sample_id = source_raw[ID_COLUMN].iloc[100]
    tab.text_input[0].set_value(sample_id).run()
    shown = at.tabs[0].dataframe[0].value
    assert len(shown) == 1
    assert shown.iloc[0][ID_COLUMN] == sample_id
    expected = source_raw.loc[source_raw[ID_COLUMN] == sample_id, FEATURE_COLUMNS].iloc[0]
    for col in FEATURE_COLUMNS:
        assert shown.iloc[0][col] == expected[col]


def test_ui_sort_on_real_widgets_matches_top_monetary_customers(source_raw):
    at = _open_dashboard()
    tab = at.tabs[0]
    tab.selectbox[0].set_value("Monetary").run()
    tab = at.tabs[0]
    tab.toggle[0].set_value(False).run()
    shown = at.tabs[0].dataframe[0].value
    expected_top5 = source_raw.nlargest(5, "Monetary")[ID_COLUMN].tolist()
    assert shown[ID_COLUMN].head(5).tolist() == expected_top5


def test_ui_pagination_pages_do_not_repeat_customers():
    at = _open_dashboard()
    tab = at.tabs[0]
    page1_ids = set(at.tabs[0].dataframe[0].value[ID_COLUMN])
    tab.number_input[0].set_value(2).run()
    page2_ids = set(at.tabs[0].dataframe[0].value[ID_COLUMN])
    assert not (page1_ids & page2_ids)


def test_ui_switching_dataset_view_updates_the_table():
    at = _open_dashboard()
    before = at.tabs[0].dataframe[0].value
    before_first_monetary = before.iloc[0]["Monetary"]
    at.radio[0].set_value("RFM after StandardScaler").run()
    after = at.tabs[0].dataframe[0].value
    after_first_monetary = after.iloc[0]["Monetary"]
    assert before_first_monetary != pytest.approx(after_first_monetary, abs=1.0)


def test_ui_reopening_five_times_shows_identical_metric():
    """'Mở lại giao diện nhiều lần' — kiểm thật qua AppTest, không chỉ ở tầng hàm."""
    values = set()
    for _ in range(5):
        at = _open_dashboard()
        values.add(at.metric[0].value)
    assert len(values) == 1, f"Total Customers đổi qua các lần mở: {values}"


def test_ui_empty_search_then_search_resets_page_to_one():
    """Đang ở trang giữa mà lọc còn ít dữ liệu thì phải tự về trang 1, không lỗi."""
    at = _open_dashboard()
    tab = at.tabs[0]
    tab.number_input[0].set_value(5).run()
    at.tabs[0].text_input[0].set_value("12347").run()
    assert not at.exception
    assert at.tabs[0].number_input[0].value == 1


# ===========================================================================
# Sinh file mẫu kiểm thử
# ===========================================================================


def _build_samples() -> pd.DataFrame:
    _require_real_data()
    outputs = load_rfm_outputs()
    raw_df, scaled_df = outputs.raw, outputs.scaled
    src_raw = pd.read_csv(RFM_PATH)
    src_raw[ID_COLUMN] = src_raw[ID_COLUMN].astype(str)

    groups: list[tuple[str, pd.Series]] = [
        ("RANDOM", src_raw[ID_COLUMN].sample(10, random_state=RANDOM_SEED)),
        ("TOP_MONETARY", src_raw.nlargest(5, "Monetary")[ID_COLUMN]),
        ("MIN_MONETARY", src_raw.nsmallest(3, "Monetary")[ID_COLUMN]),
        ("TOP_FREQUENCY", src_raw.nlargest(3, "Frequency")[ID_COLUMN]),
        ("RECENCY_MIN", src_raw.nsmallest(2, "Recency")[ID_COLUMN]),
        ("RECENCY_MAX", src_raw.nlargest(2, "Recency")[ID_COLUMN]),
    ]

    rows = []
    seen: set[str] = set()
    sample_id = 0
    for group_name, ids in groups:
        for customer_id in ids:
            if customer_id in seen:
                continue
            seen.add(customer_id)
            sample_id += 1

            shown_raw = raw_df.loc[raw_df[ID_COLUMN] == customer_id, FEATURE_COLUMNS].iloc[0]
            truth_raw = src_raw.loc[src_raw[ID_COLUMN] == customer_id, FEATURE_COLUMNS].iloc[0]
            shown_scaled = scaled_df.loc[scaled_df[ID_COLUMN] == customer_id, FEATURE_COLUMNS].iloc[0]

            match_raw = all(shown_raw[c] == truth_raw[c] for c in FEATURE_COLUMNS)
            search_hits = len(filter_by_customer_id(raw_df, str(customer_id)))

            rows.append({
                "SampleID": f"S{sample_id:03d}",
                "NhomMau": group_name,
                "CustomerID": customer_id,
                "Recency_GiaoDien": int(shown_raw["Recency"]),
                "Recency_Nguon": int(truth_raw["Recency"]),
                "Frequency_GiaoDien": int(shown_raw["Frequency"]),
                "Frequency_Nguon": int(truth_raw["Frequency"]),
                "Monetary_GiaoDien": round(float(shown_raw["Monetary"]), 2),
                "Monetary_Nguon": round(float(truth_raw["Monetary"]), 2),
                "Monetary_ScaledGiaoDien": round(float(shown_scaled["Monetary"]), 9),
                "TimKiem_SoKetQua": search_hits,
                "KhopVoiNguon": bool(match_raw),
                "KetLuan": "DAT" if match_raw and search_hits >= 1 else "KHONG DAT",
            })

    return pd.DataFrame(rows)


def test_validation_samples_file_is_up_to_date():
    """File mẫu kiểm thử đã commit phải khớp dữ liệu hiện tại."""
    if not SAMPLES_PATH.exists():
        pytest.skip("Chưa sinh file mẫu — chạy: python tests/T10.3_test_dashboard.py")
    committed = pd.read_csv(SAMPLES_PATH)
    fresh = _build_samples()
    assert len(committed) == len(fresh)
    assert (committed["KetLuan"] == "DAT").all(), "có mẫu KHÔNG ĐẠT trong file đã commit"


if __name__ == "__main__":
    SAMPLES_PATH.parent.mkdir(parents=True, exist_ok=True)
    samples = _build_samples()
    samples.to_csv(SAMPLES_PATH, index=False, encoding="utf-8")
    print(f"Đã ghi {len(samples)} mẫu vào {SAMPLES_PATH}")
    print(samples["KetLuan"].value_counts().to_string())
