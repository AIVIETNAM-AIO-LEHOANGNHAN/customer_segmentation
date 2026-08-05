from __future__ import annotations

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.visualization.rfm_dashboard import (  # noqa: E402
    DashboardDataError,
    LOG_LABEL,
    RAW_LABEL,
    SCALED_LABEL,
    build_boxplot_summary,
    build_dataset_options,
    build_descriptive_stats,
    filter_by_customer_id,
    load_rfm_outputs,
    make_boxplot,
    paginate_dataframe,
    sort_rfm_table,
)


def raw_rfm() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CustomerID": ["12347.0", "12348.0", "12349.0"],
            "Recency": [2, 75, 18],
            "Frequency": [7, 4, 1],
            "Monetary": [4310.0, 1437.24, 1457.55],
        }
    )


def scaled_rfm() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CustomerID": ["12347.0", "12348.0", "12349.0"],
            "Recency": [-0.90, -0.17, -0.74],
            "Frequency": [1.08, 0.39, -0.95],
            "Monetary": [1.44, 0.56, 0.57],
        }
    )


def write_outputs(tmp_path, raw=None, scaled=None):
    raw_path = tmp_path / "rfm_table.csv"
    scaled_path = tmp_path / "rfm_scaled.csv"
    (raw if raw is not None else raw_rfm()).to_csv(raw_path, index=False)
    (scaled if scaled is not None else scaled_rfm()).to_csv(scaled_path, index=False)
    return raw_path, scaled_path


def test_load_rfm_outputs_reads_task7_and_task8_files(tmp_path):
    raw_path, scaled_path = write_outputs(tmp_path)

    outputs = load_rfm_outputs(raw_path, scaled_path)

    assert len(outputs.raw) == 3
    assert len(outputs.scaled) == 3
    assert list(outputs.raw.columns) == ["CustomerID", "Recency", "Frequency", "Monetary"]


def test_load_rfm_outputs_reports_missing_file(tmp_path):
    raw_path = tmp_path / "rfm_table.csv"
    raw_rfm().to_csv(raw_path, index=False)

    with pytest.raises(DashboardDataError, match="rfm_scaled.csv"):
        load_rfm_outputs(raw_path, tmp_path / "rfm_scaled.csv")


def test_load_rfm_outputs_reports_missing_required_columns(tmp_path):
    raw_path, scaled_path = write_outputs(
        tmp_path,
        scaled=scaled_rfm().drop(columns=["Monetary"]),
    )

    with pytest.raises(DashboardDataError, match="Monetary"):
        load_rfm_outputs(raw_path, scaled_path)


def test_load_rfm_outputs_reports_empty_files(tmp_path):
    raw_path, scaled_path = write_outputs(
        tmp_path,
        raw=pd.DataFrame(columns=["CustomerID", "Recency", "Frequency", "Monetary"]),
    )

    with pytest.raises(DashboardDataError, match="empty"):
        load_rfm_outputs(raw_path, scaled_path)


def test_dataset_options_include_log_view_when_task8_exports_log_columns(tmp_path):
    raw = raw_rfm()
    raw["Frequency_log"] = [2.08, 1.60, 0.69]
    raw["Monetary_log"] = [8.37, 7.27, 7.28]
    raw_path, scaled_path = write_outputs(tmp_path, raw=raw)

    outputs = load_rfm_outputs(raw_path, scaled_path)
    options = build_dataset_options(outputs)

    assert list(options) == [RAW_LABEL, LOG_LABEL, SCALED_LABEL]
    assert options[LOG_LABEL]["Frequency"].tolist() == [2.08, 1.60, 0.69]
    assert options[LOG_LABEL]["Recency"].tolist() == [2, 75, 18]


def test_dataset_options_skip_log_view_when_log_columns_do_not_exist(tmp_path):
    raw_path, scaled_path = write_outputs(tmp_path)

    outputs = load_rfm_outputs(raw_path, scaled_path)

    assert list(build_dataset_options(outputs)) == [RAW_LABEL, SCALED_LABEL]


def test_table_search_sort_and_pagination_work_together():
    df = raw_rfm()

    filtered = filter_by_customer_id(df, "1234")
    sorted_df = sort_rfm_table(filtered, "Monetary", ascending=False)
    page = paginate_dataframe(sorted_df, page_size=2, page_number=1)

    assert len(filtered) == 3
    assert page.total_pages == 2
    assert page.start_row == 1
    assert page.end_row == 2
    assert page.dataframe.iloc[0]["CustomerID"] == "12347.0"


def test_sort_customer_id_uses_numeric_order_for_mixed_length_ids():
    df = pd.DataFrame(
        {
            "CustomerID": ["9999", "12347", "12348", "555"],
            "Recency": [1, 2, 3, 4],
            "Frequency": [1, 2, 3, 4],
            "Monetary": [10.0, 20.0, 30.0, 40.0],
        }
    )

    sorted_df = sort_rfm_table(df, "CustomerID", ascending=True)

    assert sorted_df["CustomerID"].tolist() == ["555", "9999", "12347", "12348"]
    assert df["CustomerID"].tolist() == ["9999", "12347", "12348", "555"]


def test_descriptive_stats_include_required_summary_rows():
    stats = build_descriptive_stats(raw_rfm())

    assert "Mean" in stats.index
    assert "Median (Q2)" in stats.index
    assert "Standard Deviation" in stats.index
    assert "Q1" in stats.index
    assert "Q3" in stats.index


def test_boxplot_summary_and_chart_export_are_compact():
    summary = build_boxplot_summary(raw_rfm())
    spec = make_boxplot(raw_rfm()).to_dict()

    assert summary["Feature"].tolist() == ["Recency", "Frequency", "Monetary"]
    assert len(summary) == 3
    assert "vconcat" in spec
    assert len(spec["vconcat"]) == 3
    assert spec["resolve"]["scale"]["x"] == "independent"
