from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from pathlib import Path
from typing import Mapping

import altair as alt
import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RFM_TABLE_PATH = PROJECT_ROOT / "data" / "processed" / "rfm_table.csv"
DEFAULT_RFM_SCALED_PATH = PROJECT_ROOT / "data" / "processed" / "rfm_scaled.csv"

ID_COLUMN = "CustomerID"
FEATURE_COLUMNS = ["Recency", "Frequency", "Monetary"]
REQUIRED_COLUMNS = [ID_COLUMN, *FEATURE_COLUMNS]

LOG_COLUMN_CANDIDATES = {
    "Recency": ("Recency_log", "LogRecency", "RecencyLog", "log_Recency"),
    "Frequency": ("Frequency_log", "LogFrequency", "FrequencyLog", "log_Frequency"),
    "Monetary": ("Monetary_log", "LogMonetary", "MonetaryLog", "log_Monetary"),
}

RAW_LABEL = "RFM original"
LOG_LABEL = "RFM after log-transform"
SCALED_LABEL = "RFM after StandardScaler"


class DashboardDataError(ValueError):
    """Raised when Task 7/8 outputs cannot be displayed safely."""


@dataclass(frozen=True)
class RfmOutputs:
    raw: pd.DataFrame
    scaled: pd.DataFrame
    log_transformed: pd.DataFrame | None = None


@dataclass(frozen=True)
class PaginationResult:
    dataframe: pd.DataFrame
    page_number: int
    total_pages: int
    start_row: int
    end_row: int


def load_rfm_outputs(
    rfm_table_path: Path | str = DEFAULT_RFM_TABLE_PATH,
    rfm_scaled_path: Path | str = DEFAULT_RFM_SCALED_PATH,
) -> RfmOutputs:
    raw_path = Path(rfm_table_path)
    scaled_path = Path(rfm_scaled_path)

    raw_source = _read_required_csv(raw_path, "Task 7 RFM table")
    scaled_source = _read_required_csv(scaled_path, "Task 8 scaled RFM data")

    raw = _validate_rfm_frame(raw_source, raw_path)
    scaled = _validate_rfm_frame(scaled_source, scaled_path)
    log_transformed = _extract_log_transform_frame(raw_source, scaled_source)

    return RfmOutputs(raw=raw, scaled=scaled, log_transformed=log_transformed)


def build_dataset_options(outputs: RfmOutputs) -> dict[str, pd.DataFrame]:
    options = {RAW_LABEL: outputs.raw}
    if outputs.log_transformed is not None:
        options[LOG_LABEL] = outputs.log_transformed
    options[SCALED_LABEL] = outputs.scaled
    return options


def build_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    stats = df[FEATURE_COLUMNS].describe(percentiles=[0.25, 0.5, 0.75])
    stats = stats.reindex(["count", "mean", "50%", "std", "min", "25%", "75%", "max"])
    return stats.rename(
        index={
            "count": "Count",
            "mean": "Mean",
            "50%": "Median (Q2)",
            "std": "Standard Deviation",
            "min": "Minimum",
            "25%": "Q1",
            "75%": "Q3",
            "max": "Maximum",
        }
    )


def filter_by_customer_id(df: pd.DataFrame, query: str) -> pd.DataFrame:
    query = query.strip()
    if not query:
        return df
    customer_id = df[ID_COLUMN].astype(str).str.casefold()
    return df[customer_id.str.contains(query.casefold(), regex=False, na=False)]


def sort_rfm_table(df: pd.DataFrame, sort_column: str, ascending: bool) -> pd.DataFrame:
    if sort_column not in df.columns:
        return df
    if sort_column == ID_COLUMN:
        numeric_sort_column = "_customer_id_numeric_sort"
        text_sort_column = "_customer_id_text_sort"
        sortable = df.assign(
            **{
                numeric_sort_column: pd.to_numeric(df[ID_COLUMN], errors="coerce"),
                text_sort_column: df[ID_COLUMN].astype(str),
            }
        )
        return (
            sortable.sort_values(
                [numeric_sort_column, text_sort_column],
                ascending=[ascending, ascending],
                kind="mergesort",
                na_position="last",
            )
            .drop(columns=[numeric_sort_column, text_sort_column])
        )
    return df.sort_values(sort_column, ascending=ascending, kind="mergesort")


def paginate_dataframe(
    df: pd.DataFrame,
    page_size: int,
    page_number: int,
) -> PaginationResult:
    if page_size < 1:
        raise ValueError("page_size must be greater than 0")

    total_pages = max(1, ceil(len(df) / page_size))
    safe_page = min(max(page_number, 1), total_pages)
    start = (safe_page - 1) * page_size
    end = min(start + page_size, len(df))

    return PaginationResult(
        dataframe=df.iloc[start:end],
        page_number=safe_page,
        total_pages=total_pages,
        start_row=0 if df.empty else start + 1,
        end_row=end,
    )


def make_histogram(df: pd.DataFrame, feature: str) -> alt.Chart:
    if feature not in FEATURE_COLUMNS:
        raise ValueError(f"Unknown RFM feature: {feature}")

    return (
        alt.Chart(df)
        .mark_bar(opacity=0.85, color="#2563eb")
        .encode(
            x=alt.X(
                f"{feature}:Q",
                bin=alt.Bin(maxbins=40),
                title=feature,
            ),
            y=alt.Y("count():Q", title="Customers"),
            tooltip=[
                alt.Tooltip(f"{feature}:Q", bin=True, title=feature),
                alt.Tooltip("count():Q", title="Customers"),
            ],
        )
        .properties(height=260)
    )


def build_boxplot_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature in FEATURE_COLUMNS:
        values = pd.to_numeric(df[feature], errors="coerce").dropna()
        quantiles = values.quantile([0.0, 0.25, 0.5, 0.75, 1.0])
        rows.append(
            {
                "Feature": feature,
                "Minimum": quantiles.loc[0.0],
                "Q1": quantiles.loc[0.25],
                "Median": quantiles.loc[0.5],
                "Q3": quantiles.loc[0.75],
                "Maximum": quantiles.loc[1.0],
            }
        )
    return pd.DataFrame(rows)


def make_boxplot(df: pd.DataFrame) -> alt.VConcatChart:
    summary = build_boxplot_summary(df)
    charts = []

    for feature in FEATURE_COLUMNS:
        feature_summary = summary[summary["Feature"] == feature]
        base = alt.Chart(feature_summary).encode(
            y=alt.Y(
                "Feature:N",
                title=None,
                axis=alt.Axis(labels=False, ticks=False, domain=False),
            ),
            tooltip=[
                alt.Tooltip("Feature:N", title="Feature"),
                alt.Tooltip("Minimum:Q", title="Minimum", format=",.2f"),
                alt.Tooltip("Q1:Q", title="Q1", format=",.2f"),
                alt.Tooltip("Median:Q", title="Median", format=",.2f"),
                alt.Tooltip("Q3:Q", title="Q3", format=",.2f"),
                alt.Tooltip("Maximum:Q", title="Maximum", format=",.2f"),
            ],
        )
        whisker = base.mark_rule(color="#64748b").encode(
            x=alt.X("Minimum:Q", title="Value"),
            x2=alt.X2("Maximum:Q"),
        )
        box = base.mark_bar(size=28, color="#0f766e", opacity=0.72).encode(
            x=alt.X("Q1:Q", title="Value"),
            x2=alt.X2("Q3:Q"),
        )
        median = base.mark_tick(color="#111827", size=34, thickness=2).encode(
            x=alt.X("Median:Q", title="Value")
        )
        charts.append((whisker + box + median).properties(height=82, title=feature))

    return alt.vconcat(*charts, spacing=12).resolve_scale(x="independent")


def render_dashboard() -> None:
    st.title("RFM Feature Dashboard")
    st.caption(
        "Review Task 7 and Task 8 outputs before moving to model training."
    )

    try:
        outputs = load_rfm_outputs()
    except DashboardDataError as error:
        st.error(str(error))
        st.warning(
            "Run Task 7 to create data/processed/rfm_table.csv and Task 8 to "
            "create data/processed/rfm_scaled.csv before opening this dashboard."
        )
        return

    dataset_options = build_dataset_options(outputs)
    metric_left, metric_right = st.columns(2)
    with metric_left:
        st.metric("Total Customers", f"{len(outputs.raw):,}")
    with metric_right:
        st.metric("Scaled Rows", f"{len(outputs.scaled):,}")

    selected_label = st.radio(
        "Dataset view",
        list(dataset_options.keys()),
        horizontal=True,
        index=0,
    )
    selected_df = dataset_options[selected_label]

    if LOG_LABEL not in dataset_options:
        st.info(
            "Log-transform view is not available because Task 8 did not export "
            "log columns. The dashboard still compares original and scaled data."
        )

    table_tab, stats_tab, histogram_tab, boxplot_tab, download_tab = st.tabs(
        ["RFM Table", "Statistics", "Histograms", "Boxplot", "Downloads"]
    )

    with table_tab:
        _render_rfm_table(selected_df, selected_label)

    with stats_tab:
        st.dataframe(
            build_descriptive_stats(selected_df),
            width="stretch",
        )

    with histogram_tab:
        _render_histograms(selected_df)

    with boxplot_tab:
        st.altair_chart(make_boxplot(selected_df), width="stretch")

    with download_tab:
        _render_downloads(outputs)


def _read_required_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise DashboardDataError(f"{label} file not found: {path}")
    try:
        df = pd.read_csv(path)
    except Exception as error:
        raise DashboardDataError(f"Cannot read {label} file {path}: {error}") from error
    if df.empty:
        raise DashboardDataError(f"{label} file is empty: {path}")
    return df


def _validate_rfm_frame(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise DashboardDataError(
            f"{path} is missing required columns: {', '.join(missing)}"
        )

    validated = df[REQUIRED_COLUMNS].copy()
    validated[ID_COLUMN] = validated[ID_COLUMN].astype(str).astype(object)

    non_numeric = []
    for column in FEATURE_COLUMNS:
        validated[column] = pd.to_numeric(validated[column], errors="coerce")
        if validated[column].isna().all():
            non_numeric.append(column)

    if non_numeric:
        raise DashboardDataError(
            f"{path} has non-numeric RFM columns: {', '.join(non_numeric)}"
        )

    return validated


def _extract_log_transform_frame(*frames: pd.DataFrame) -> pd.DataFrame | None:
    for frame in frames:
        log_columns = _find_log_columns(frame.columns)
        if not log_columns:
            continue

        selected_columns: list[str] = [ID_COLUMN]
        rename_map: dict[str, str] = {}
        missing = []

        for feature in FEATURE_COLUMNS:
            source_column = log_columns.get(feature, feature)
            if source_column not in frame.columns:
                missing.append(feature)
                continue
            selected_columns.append(source_column)
            rename_map[source_column] = feature

        if missing:
            continue

        log_frame = frame[selected_columns].rename(columns=rename_map)
        return _validate_rfm_frame(log_frame, Path("log-transform columns"))

    return None


def _find_log_columns(columns: pd.Index | list[str]) -> dict[str, str]:
    available = set(columns)
    matches: dict[str, str] = {}
    for feature, candidates in LOG_COLUMN_CANDIDATES.items():
        for candidate in candidates:
            if candidate in available:
                matches[feature] = candidate
                break
    return matches


def _render_rfm_table(df: pd.DataFrame, label: str) -> None:
    key_prefix = label.lower().replace(" ", "_").replace("-", "_")

    control_left, control_mid, control_right, control_page = st.columns([2, 1, 1, 1])
    with control_left:
        search = st.text_input(
            "Search CustomerID",
            placeholder="Example: 12347",
            key=f"{key_prefix}_search",
        )
    with control_mid:
        sort_column = st.selectbox(
            "Sort by",
            REQUIRED_COLUMNS,
            index=0,
            key=f"{key_prefix}_sort_column",
        )
    with control_right:
        ascending = st.toggle(
            "Ascending",
            value=True,
            key=f"{key_prefix}_ascending",
        )
    with control_page:
        page_size = st.selectbox(
            "Rows/page",
            [10, 25, 50, 100],
            index=1,
            key=f"{key_prefix}_page_size",
        )

    filtered = filter_by_customer_id(df, search)
    sorted_df = sort_rfm_table(filtered, sort_column, ascending)
    total_pages = max(1, ceil(len(sorted_df) / page_size))
    page_number = st.number_input(
        "Page",
        min_value=1,
        max_value=total_pages,
        value=1,
        step=1,
        key=f"{key_prefix}_page_{len(sorted_df)}_{page_size}",
    )

    page = paginate_dataframe(sorted_df, page_size, int(page_number))
    st.caption(
        f"Showing {page.start_row:,}-{page.end_row:,} of {len(sorted_df):,} customers"
    )
    st.dataframe(page.dataframe, hide_index=True, width="stretch")


def _render_histograms(df: pd.DataFrame) -> None:
    for feature in FEATURE_COLUMNS:
        st.subheader(feature)
        st.altair_chart(make_histogram(df, feature), width="stretch")


def _render_downloads(outputs: RfmOutputs) -> None:
    st.download_button(
        "Download rfm_table.csv",
        data=outputs.raw.to_csv(index=False).encode("utf-8"),
        file_name="rfm_table.csv",
        mime="text/csv",
    )
    st.download_button(
        "Download rfm_scaled.csv",
        data=outputs.scaled.to_csv(index=False).encode("utf-8"),
        file_name="rfm_scaled.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    render_dashboard()
