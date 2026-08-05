from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COMPARISON_PATH = PROJECT_ROOT / "outputs" / "tables" / "model_comparison.csv"
DEFAULT_STABILITY_PATH = PROJECT_ROOT / "data" / "processed" / "stability_results.csv"
DEFAULT_SEPARATION_PATH = PROJECT_ROOT / "outputs" / "results" / "cluster_separation.csv"
DEFAULT_PROFILES_PATH = PROJECT_ROOT / "data" / "processed" / "cluster_profiles.csv"

MODEL_COLUMN = "model"

COMPARISON_REQUIRED_COLUMNS = [
    MODEL_COLUMN,
    "n_clusters",
    "n_noise",
    "silhouette",
    "davies_bouldin",
    "calinski_harabasz",
    "mean_ari",
    "customer_coverage",
    "revenue_coverage",
    "score_quality",
    "score_stability",
    "score_interpretability",
    "score_overall",
]
STABILITY_REQUIRED_COLUMNS = [
    MODEL_COLUMN,
    "mean_ari",
    "std_ari",
    "min_ari",
    "max_ari",
    "stability",
]
SEPARATION_REQUIRED_COLUMNS = [
    MODEL_COLUMN,
    "delta_recency",
    "delta_frequency",
    "delta_monetary",
    "delta_mean",
    "delta_min",
]
PROFILE_REQUIRED_COLUMNS = [
    MODEL_COLUMN,
    "cluster",
    "segment",
    "n_customers",
    "share",
    "revenue_share",
    "strategy",
]

QUALITY_METRICS = {
    "silhouette": "Silhouette",
    "davies_bouldin": "Davies-Bouldin",
    "calinski_harabasz": "Calinski-Harabasz",
}
INTERPRETABILITY_METRICS = {
    "score_interpretability": "Interpretability Score",
    "customer_coverage": "Customer Coverage",
    "revenue_coverage": "Revenue Coverage",
}
RADAR_METRICS = [
    ("Quality", "score_quality"),
    ("Stability", "score_stability"),
    ("Interpretability", "score_interpretability"),
    ("Overall", "score_overall"),
]


class EvaluationDataError(ValueError):
    """Raised when Task 12 evaluation outputs cannot be displayed safely."""


@dataclass(frozen=True)
class EvaluationOutputs:
    comparison: pd.DataFrame
    stability: pd.DataFrame
    separation: pd.DataFrame
    profiles: pd.DataFrame


def load_evaluation_outputs(
    comparison_path: Path | str = DEFAULT_COMPARISON_PATH,
    stability_path: Path | str = DEFAULT_STABILITY_PATH,
    separation_path: Path | str = DEFAULT_SEPARATION_PATH,
    profiles_path: Path | str = DEFAULT_PROFILES_PATH,
) -> EvaluationOutputs:
    comparison = _validate_comparison_frame(
        _read_required_csv(Path(comparison_path), "Task 12 model comparison"),
        Path(comparison_path),
    )
    stability = _validate_stability_frame(
        _read_required_csv(Path(stability_path), "Task 12 stability metrics"),
        Path(stability_path),
    )
    separation = _validate_separation_frame(
        _read_required_csv(Path(separation_path), "Task 12 cluster separation"),
        Path(separation_path),
    )
    profiles = _validate_profiles_frame(
        _read_required_csv(Path(profiles_path), "Task 12 business profiles"),
        Path(profiles_path),
    )
    return EvaluationOutputs(
        comparison=comparison,
        stability=stability,
        separation=separation,
        profiles=profiles,
    )


def build_evaluation_table(comparison: pd.DataFrame) -> pd.DataFrame:
    columns = [
        MODEL_COLUMN,
        "n_clusters",
        "n_noise",
        "silhouette",
        "davies_bouldin",
        "calinski_harabasz",
        "mean_ari",
        "score_quality",
        "score_stability",
        "score_interpretability",
        "score_overall",
    ]
    return comparison[columns].sort_values("score_overall", ascending=False)


def filter_by_model(df: pd.DataFrame, query: str) -> pd.DataFrame:
    query = query.strip()
    if not query:
        return df
    models = df[MODEL_COLUMN].astype(str).str.casefold()
    return df[models.str.contains(query.casefold(), regex=False, na=False)]


def make_quality_chart(comparison: pd.DataFrame) -> alt.FacetChart:
    long = comparison.melt(
        id_vars=[MODEL_COLUMN],
        value_vars=list(QUALITY_METRICS),
        var_name="Metric",
        value_name="Value",
    )
    long["Metric"] = long["Metric"].map(QUALITY_METRICS)
    model_order = comparison.sort_values("score_quality", ascending=False)[
        MODEL_COLUMN
    ].tolist()
    return (
        alt.Chart(long)
        .mark_bar(opacity=0.86)
        .encode(
            x=alt.X(f"{MODEL_COLUMN}:N", sort=model_order, title="Model"),
            y=alt.Y("Value:Q", title="Value"),
            color=alt.Color(f"{MODEL_COLUMN}:N", title="Model"),
            column=alt.Column("Metric:N", title=None),
            tooltip=[
                alt.Tooltip(f"{MODEL_COLUMN}:N", title="Model"),
                alt.Tooltip("Metric:N", title="Metric"),
                alt.Tooltip("Value:Q", title="Value", format=",.4f"),
            ],
        )
        .properties(height=280)
        .resolve_scale(y="independent")
    )


def make_stability_chart(stability: pd.DataFrame) -> alt.LayerChart:
    model_order = stability.sort_values("mean_ari", ascending=False)[
        MODEL_COLUMN
    ].tolist()
    base = alt.Chart(stability).encode(
        x=alt.X(f"{MODEL_COLUMN}:N", sort=model_order, title="Model"),
        tooltip=[
            alt.Tooltip(f"{MODEL_COLUMN}:N", title="Model"),
            alt.Tooltip("mean_ari:Q", title="Mean ARI", format=".4f"),
            alt.Tooltip("std_ari:Q", title="Std ARI", format=".4f"),
            alt.Tooltip("min_ari:Q", title="Min ARI", format=".4f"),
            alt.Tooltip("max_ari:Q", title="Max ARI", format=".4f"),
            alt.Tooltip("stability:N", title="Stability"),
        ],
    )
    bars = base.mark_bar(color="#0f766e", opacity=0.82).encode(
        y=alt.Y("mean_ari:Q", title="Adjusted Rand Index", scale=alt.Scale(domain=[0, 1]))
    )
    ranges = base.mark_rule(color="#111827").encode(
        y=alt.Y("min_ari:Q"),
        y2=alt.Y2("max_ari:Q"),
    )
    return (bars + ranges).properties(height=320)


def make_interpretability_chart(comparison: pd.DataFrame) -> alt.FacetChart:
    long = comparison.melt(
        id_vars=[MODEL_COLUMN],
        value_vars=list(INTERPRETABILITY_METRICS),
        var_name="Metric",
        value_name="Value",
    )
    long["Metric"] = long["Metric"].map(INTERPRETABILITY_METRICS)
    return (
        alt.Chart(long)
        .mark_bar(opacity=0.86, color="#7c3aed")
        .encode(
            x=alt.X(f"{MODEL_COLUMN}:N", title="Model"),
            y=alt.Y("Value:Q", title="Score", scale=alt.Scale(domain=[0, 1])),
            column=alt.Column("Metric:N", title=None),
            tooltip=[
                alt.Tooltip(f"{MODEL_COLUMN}:N", title="Model"),
                alt.Tooltip("Metric:N", title="Metric"),
                alt.Tooltip("Value:Q", title="Value", format=".2%"),
            ],
        )
        .properties(height=280)
    )


def build_radar_frame(comparison: pd.DataFrame) -> pd.DataFrame:
    rows = []
    metric_count = len(RADAR_METRICS)
    for _, row in comparison.iterrows():
        first_metric = None
        for order, (metric_label, column) in enumerate(RADAR_METRICS):
            value = float(row[column])
            angle = (2 * pi * order / metric_count) - (pi / 2)
            metric_row = {
                MODEL_COLUMN: row[MODEL_COLUMN],
                "Metric": metric_label,
                "Value": value,
                "Order": order,
                "X": cos(angle) * value,
                "Y": sin(angle) * value,
            }
            if first_metric is None:
                first_metric = metric_row
            rows.append(metric_row)
        if first_metric is not None:
            closed = first_metric.copy()
            closed["Order"] = metric_count
            rows.append(closed)
    return pd.DataFrame(rows)


def make_radar_chart(comparison: pd.DataFrame) -> alt.LayerChart:
    radar = build_radar_frame(comparison)
    labels = []
    for order, (metric_label, _) in enumerate(RADAR_METRICS):
        angle = (2 * pi * order / len(RADAR_METRICS)) - (pi / 2)
        labels.append(
            {
                "Metric": metric_label,
                "X": cos(angle) * 1.08,
                "Y": sin(angle) * 1.08,
            }
        )
    label_df = pd.DataFrame(labels)

    polygons = (
        alt.Chart(radar)
        .mark_line(point=True, strokeWidth=2)
        .encode(
            x=alt.X("X:Q", axis=None, scale=alt.Scale(domain=[-1.15, 1.15])),
            y=alt.Y("Y:Q", axis=None, scale=alt.Scale(domain=[-1.15, 1.15])),
            color=alt.Color(f"{MODEL_COLUMN}:N", title="Model"),
            detail=f"{MODEL_COLUMN}:N",
            order="Order:Q",
            tooltip=[
                alt.Tooltip(f"{MODEL_COLUMN}:N", title="Model"),
                alt.Tooltip("Metric:N", title="Metric"),
                alt.Tooltip("Value:Q", title="Score", format=".2%"),
            ],
        )
    )
    axis_labels = (
        alt.Chart(label_df)
        .mark_text(size=12, color="#111827")
        .encode(
            x=alt.X("X:Q", axis=None, scale=alt.Scale(domain=[-1.15, 1.15])),
            y=alt.Y("Y:Q", axis=None, scale=alt.Scale(domain=[-1.15, 1.15])),
            text="Metric:N",
        )
    )
    return (polygons + axis_labels).properties(height=420)


def make_overall_score_chart(comparison: pd.DataFrame) -> alt.Chart:
    ordered = comparison.sort_values("score_overall", ascending=False)
    return (
        alt.Chart(ordered)
        .mark_bar(color="#2563eb", opacity=0.86)
        .encode(
            x=alt.X(f"{MODEL_COLUMN}:N", sort=ordered[MODEL_COLUMN].tolist(), title="Model"),
            y=alt.Y("score_overall:Q", title="Overall Score", scale=alt.Scale(domain=[0, 1])),
            tooltip=[
                alt.Tooltip(f"{MODEL_COLUMN}:N", title="Model"),
                alt.Tooltip("score_overall:Q", title="Overall", format=".2%"),
            ],
        )
        .properties(height=300)
    )


def make_separation_chart(separation: pd.DataFrame) -> alt.FacetChart:
    labels = {
        "delta_recency": "Recency Separation",
        "delta_frequency": "Frequency Separation",
        "delta_monetary": "Monetary Separation",
        "delta_mean": "Mean Separation",
    }
    long = separation.melt(
        id_vars=[MODEL_COLUMN],
        value_vars=list(labels),
        var_name="Metric",
        value_name="Value",
    )
    long["Metric"] = long["Metric"].map(labels)
    return (
        alt.Chart(long)
        .mark_bar(color="#0f766e", opacity=0.82)
        .encode(
            x=alt.X(f"{MODEL_COLUMN}:N", title="Model"),
            y=alt.Y("Value:Q", title="Separation"),
            column=alt.Column("Metric:N", title=None),
            tooltip=[
                alt.Tooltip(f"{MODEL_COLUMN}:N", title="Model"),
                alt.Tooltip("Metric:N", title="Metric"),
                alt.Tooltip("Value:Q", title="Value", format=",.3f"),
            ],
        )
        .properties(height=260)
        .resolve_scale(y="independent")
    )


def render_dashboard() -> None:
    st.title("Clustering Evaluation Dashboard")
    st.caption("Compare Task 12 clustering quality, stability, and business meaning.")

    try:
        outputs = load_evaluation_outputs()
    except EvaluationDataError as error:
        st.error(str(error))
        st.warning(
            "Run Task 12 evaluation to create outputs/tables/model_comparison.csv "
            "and the related stability/profile outputs before opening this dashboard."
        )
        return

    comparison = outputs.comparison
    best = comparison.sort_values("score_overall", ascending=False).iloc[0]
    metrics = st.columns(4)
    metrics[0].metric("Models", f"{len(comparison):,}")
    metrics[1].metric("Best Overall", str(best[MODEL_COLUMN]))
    metrics[2].metric("Best Score", f"{best['score_overall']:.1%}")
    metrics[3].metric("Best Silhouette", f"{comparison['silhouette'].max():.4f}")

    table_tab, quality_tab, stability_tab, meaning_tab, radar_tab, download_tab = st.tabs(
        [
            "Evaluation Table",
            "Quality",
            "Stability",
            "Business Meaning",
            "Overall Compare",
            "Downloads",
        ]
    )

    with table_tab:
        _render_evaluation_table(build_evaluation_table(comparison))

    with quality_tab:
        st.altair_chart(make_quality_chart(comparison), width="stretch")
        st.altair_chart(make_separation_chart(outputs.separation), width="stretch")

    with stability_tab:
        st.dataframe(outputs.stability, hide_index=True, width="stretch")
        st.altair_chart(make_stability_chart(outputs.stability), width="stretch")

    with meaning_tab:
        st.altair_chart(make_interpretability_chart(comparison), width="stretch")
        st.dataframe(outputs.profiles, hide_index=True, width="stretch")

    with radar_tab:
        st.altair_chart(make_radar_chart(comparison), width="stretch")
        st.altair_chart(make_overall_score_chart(comparison), width="stretch")

    with download_tab:
        _render_downloads(outputs)


def _read_required_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise EvaluationDataError(f"{label} file not found: {path}")
    try:
        df = pd.read_csv(path)
    except Exception as error:
        raise EvaluationDataError(f"Cannot read {label} file {path}: {error}") from error
    if df.empty:
        raise EvaluationDataError(f"{label} file is empty: {path}")
    return df


def _validate_comparison_frame(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    comparison = _validate_required_columns(df, path, COMPARISON_REQUIRED_COLUMNS)
    numeric_columns = [column for column in COMPARISON_REQUIRED_COLUMNS if column != MODEL_COLUMN]
    return _coerce_numeric(comparison, path, numeric_columns)


def _validate_stability_frame(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    stability = _validate_required_columns(df, path, STABILITY_REQUIRED_COLUMNS)
    numeric_columns = ["mean_ari", "std_ari", "min_ari", "max_ari"]
    return _coerce_numeric(stability, path, numeric_columns)


def _validate_separation_frame(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    separation = _validate_required_columns(df, path, SEPARATION_REQUIRED_COLUMNS)
    numeric_columns = [column for column in SEPARATION_REQUIRED_COLUMNS if column != MODEL_COLUMN]
    return _coerce_numeric(separation, path, numeric_columns)


def _validate_profiles_frame(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    profiles = _validate_required_columns(df, path, PROFILE_REQUIRED_COLUMNS)
    numeric_columns = ["cluster", "n_customers", "share", "revenue_share"]
    profiles = _coerce_numeric(profiles, path, numeric_columns)
    profiles["cluster"] = profiles["cluster"].astype(int)
    profiles["n_customers"] = profiles["n_customers"].astype(int)
    return profiles


def _validate_required_columns(
    df: pd.DataFrame,
    path: Path,
    required_columns: list[str],
) -> pd.DataFrame:
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise EvaluationDataError(
            f"{path} is missing required columns: {', '.join(missing)}"
        )
    validated = df[required_columns].copy()
    validated[MODEL_COLUMN] = validated[MODEL_COLUMN].astype(str).astype(object)
    return validated


def _coerce_numeric(
    df: pd.DataFrame,
    path: Path,
    numeric_columns: list[str],
) -> pd.DataFrame:
    validated = df.copy()
    invalid_columns = []
    for column in numeric_columns:
        validated[column] = pd.to_numeric(validated[column], errors="coerce")
        if validated[column].isna().any():
            invalid_columns.append(column)
    if invalid_columns:
        raise EvaluationDataError(
            f"{path} has invalid numeric values in: {', '.join(invalid_columns)}"
        )
    return validated


def _render_evaluation_table(df: pd.DataFrame) -> None:
    control_left, control_mid, control_right = st.columns([2, 1, 1])
    with control_left:
        query = st.text_input("Search model", placeholder="Example: K-Means")
    with control_mid:
        sort_column = st.selectbox("Sort by", list(df.columns), index=list(df.columns).index("score_overall"))
    with control_right:
        ascending = st.toggle("Ascending", value=False)

    filtered = filter_by_model(df, query)
    sorted_df = filtered.sort_values(
        sort_column,
        ascending=ascending,
        kind="mergesort",
    )
    st.caption(f"Showing {len(sorted_df):,} of {len(df):,} models")
    st.dataframe(sorted_df, hide_index=True, width="stretch")


def _render_downloads(outputs: EvaluationOutputs) -> None:
    downloads = [
        ("Download model_comparison.csv", outputs.comparison, "model_comparison.csv"),
        ("Download stability_results.csv", outputs.stability, "stability_results.csv"),
        ("Download cluster_separation.csv", outputs.separation, "cluster_separation.csv"),
        ("Download cluster_profiles.csv", outputs.profiles, "cluster_profiles.csv"),
    ]
    for label, df, filename in downloads:
        st.download_button(
            label,
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=filename,
            mime="text/csv",
        )


if __name__ == "__main__":
    render_dashboard()
