from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from src.visualization.rfm_dashboard import (
    FEATURE_COLUMNS,
    ID_COLUMN,
    filter_by_customer_id,
    paginate_dataframe,
    sort_rfm_table,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CLUSTER_RESULTS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "customer_clusters_all_models.csv"
)
DEFAULT_CLUSTER_PROFILES_PATH = (
    PROJECT_ROOT / "data" / "processed" / "cluster_profiles.csv"
)

CLUSTER_COLUMN = "Cluster"
REQUIRED_RESULT_COLUMNS = [ID_COLUMN, *FEATURE_COLUMNS]
PROFILE_COLUMNS = [
    "model",
    "cluster",
    "segment",
    "n_customers",
    "share",
    "revenue_share",
    "strategy",
]


@dataclass(frozen=True)
class AlgorithmConfig:
    label: str
    model_name: str
    cluster_column: str
    download_filename: str
    has_noise: bool = False


ALGORITHMS: dict[str, AlgorithmConfig] = {
    "K-Means": AlgorithmConfig(
        label="K-Means",
        model_name="K-Means",
        cluster_column="K-Means_Cluster",
        download_filename="customer_clusters_kmeans.csv",
    ),
    "Gaussian Mixture Model (GMM)": AlgorithmConfig(
        label="Gaussian Mixture Model (GMM)",
        model_name="GMM",
        cluster_column="GMM_Cluster",
        download_filename="customer_clusters_gmm.csv",
    ),
    "HDBSCAN": AlgorithmConfig(
        label="HDBSCAN",
        model_name="HDBSCAN",
        cluster_column="HDBSCAN_Cluster",
        download_filename="customer_clusters_hdbscan.csv",
        has_noise=True,
    ),
}


class ClusteringDataError(ValueError):
    """Raised when Task 12 clustering outputs cannot be displayed safely."""


@dataclass(frozen=True)
class ClusteringOutputs:
    results: pd.DataFrame
    profiles: pd.DataFrame | None = None


def load_clustering_outputs(
    results_path: Path | str = DEFAULT_CLUSTER_RESULTS_PATH,
    profiles_path: Path | str = DEFAULT_CLUSTER_PROFILES_PATH,
) -> ClusteringOutputs:
    results_source = _read_required_csv(Path(results_path), "Task 12 clustering results")
    results = _validate_results_frame(results_source, Path(results_path))

    profiles = None
    profile_path = Path(profiles_path)
    if profile_path.exists():
        profile_source = _read_required_csv(profile_path, "Task 12 cluster profiles")
        profiles = _validate_profiles_frame(profile_source, profile_path)

    return ClusteringOutputs(results=results, profiles=profiles)


def build_algorithm_frame(outputs: ClusteringOutputs, algorithm_label: str) -> pd.DataFrame:
    config = _get_algorithm_config(algorithm_label)
    selected = outputs.results[
        [ID_COLUMN, *FEATURE_COLUMNS, config.cluster_column]
    ].copy()
    selected = selected.rename(columns={config.cluster_column: CLUSTER_COLUMN})
    return selected


def build_cluster_summary(df: pd.DataFrame, algorithm_label: str) -> pd.DataFrame:
    config = _get_algorithm_config(algorithm_label)
    total = len(df)
    if total == 0:
        raise ClusteringDataError("No clustering rows are available.")

    counts = (
        df[CLUSTER_COLUMN]
        .value_counts()
        .rename_axis(CLUSTER_COLUMN)
        .reset_index(name="Customers")
        .sort_values(CLUSTER_COLUMN, kind="mergesort")
    )
    counts["Share"] = counts["Customers"] / total
    counts["ClusterLabel"] = counts[CLUSTER_COLUMN].apply(
        lambda value: format_cluster_label(value, config.has_noise)
    )
    return counts[[CLUSTER_COLUMN, "ClusterLabel", "Customers", "Share"]]


def count_clusters(summary: pd.DataFrame, algorithm_label: str) -> int:
    config = _get_algorithm_config(algorithm_label)
    clusters = summary[CLUSTER_COLUMN]
    if config.has_noise:
        clusters = clusters[clusters != -1]
    return int(clusters.nunique())


def count_noise(summary: pd.DataFrame, algorithm_label: str) -> int:
    config = _get_algorithm_config(algorithm_label)
    if not config.has_noise:
        return 0
    noise_rows = summary.loc[summary[CLUSTER_COLUMN] == -1, "Customers"]
    if noise_rows.empty:
        return 0
    return int(noise_rows.iloc[0])


def build_cluster_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cluster, group in df.groupby(CLUSTER_COLUMN, sort=True):
        row: dict[str, float | int] = {
            CLUSTER_COLUMN: int(cluster),
            "Customers": int(len(group)),
        }
        for feature in FEATURE_COLUMNS:
            values = group[feature]
            row[f"{feature}_Mean"] = float(values.mean())
            row[f"{feature}_Median"] = float(values.median())
            row[f"{feature}_Std"] = float(values.std())
            row[f"{feature}_Min"] = float(values.min())
            row[f"{feature}_Max"] = float(values.max())
        rows.append(row)
    return pd.DataFrame(rows)


def build_profile_table(
    profiles: pd.DataFrame | None,
    algorithm_label: str,
) -> pd.DataFrame | None:
    if profiles is None:
        return None
    config = _get_algorithm_config(algorithm_label)
    profile = profiles.loc[profiles["model"] == config.model_name].copy()
    if profile.empty:
        return None
    profile = profile.rename(
        columns={
            "cluster": CLUSTER_COLUMN,
            "segment": "Segment",
            "n_customers": "Customers",
            "share": "Share",
            "revenue_share": "RevenueShare",
            "strategy": "Strategy",
        }
    )
    return profile[
        [CLUSTER_COLUMN, "Segment", "Customers", "Share", "RevenueShare", "Strategy"]
    ].sort_values(CLUSTER_COLUMN, kind="mergesort")


def build_pca_projection(df: pd.DataFrame, algorithm_label: str) -> pd.DataFrame:
    config = _get_algorithm_config(algorithm_label)
    valid = df.dropna(subset=[*FEATURE_COLUMNS, CLUSTER_COLUMN]).copy()
    if len(valid) < 2:
        raise ClusteringDataError("At least 2 rows are required to build the PCA plot.")

    scaled = StandardScaler().fit_transform(valid[FEATURE_COLUMNS])
    components = PCA(n_components=2).fit_transform(scaled)

    projection = valid[[ID_COLUMN, CLUSTER_COLUMN, *FEATURE_COLUMNS]].copy()
    projection["PC1"] = components[:, 0]
    projection["PC2"] = components[:, 1]
    projection["ClusterLabel"] = projection[CLUSTER_COLUMN].apply(
        lambda value: format_cluster_label(value, config.has_noise)
    )
    return projection


def format_cluster_label(cluster: int | float, has_noise: bool) -> str:
    cluster_id = int(cluster)
    if has_noise and cluster_id == -1:
        return "Noise"
    return f"Cluster {cluster_id}"


def make_pca_scatter(projection: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(projection)
        .mark_circle(size=54, opacity=0.72)
        .encode(
            x=alt.X("PC1:Q", title="PCA component 1"),
            y=alt.Y("PC2:Q", title="PCA component 2"),
            color=alt.Color("ClusterLabel:N", title="Cluster"),
            tooltip=[
                alt.Tooltip(f"{ID_COLUMN}:N", title="CustomerID"),
                alt.Tooltip("ClusterLabel:N", title="Cluster"),
                alt.Tooltip("Recency:Q", title="Recency", format=",.2f"),
                alt.Tooltip("Frequency:Q", title="Frequency", format=",.2f"),
                alt.Tooltip("Monetary:Q", title="Monetary", format=",.2f"),
            ],
        )
        .properties(height=430)
    )


def make_cluster_distribution_chart(summary: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(summary)
        .mark_bar(color="#2563eb", opacity=0.86)
        .encode(
            x=alt.X(
                "ClusterLabel:N",
                sort=summary["ClusterLabel"].tolist(),
                title="Cluster",
            ),
            y=alt.Y("Customers:Q", title="Customers"),
            tooltip=[
                alt.Tooltip("ClusterLabel:N", title="Cluster"),
                alt.Tooltip("Customers:Q", title="Customers", format=","),
                alt.Tooltip("Share:Q", title="Share", format=".1%"),
            ],
        )
        .properties(height=320)
    )


def render_dashboard() -> None:
    st.title("Clustering Results Dashboard")
    st.caption("Review Task 12 clustering outputs without retraining any model.")

    try:
        outputs = load_clustering_outputs()
    except ClusteringDataError as error:
        st.error(str(error))
        st.warning(
            "Run Task 12 to create data/processed/customer_clusters_all_models.csv "
            "before opening this dashboard."
        )
        return

    algorithm_label = st.selectbox("Algorithm", list(ALGORITHMS), index=0)
    selected_df = build_algorithm_frame(outputs, algorithm_label)
    summary = build_cluster_summary(selected_df, algorithm_label)
    cluster_count = count_clusters(summary, algorithm_label)
    if cluster_count == 0:
        st.error("No valid cluster was found for the selected algorithm.")
        return

    noise_count = count_noise(summary, algorithm_label)
    metric_columns = st.columns(4 if ALGORITHMS[algorithm_label].has_noise else 3)
    metric_columns[0].metric("Total Customers", f"{len(selected_df):,}")
    metric_columns[1].metric("Clusters", f"{cluster_count:,}")
    metric_columns[2].metric("Largest Cluster", f"{summary['Customers'].max():,}")
    if ALGORITHMS[algorithm_label].has_noise:
        metric_columns[3].metric(
            "Noise",
            f"{noise_count:,}",
            f"{noise_count / len(selected_df):.1%}",
        )

    table_tab, stats_tab, pca_tab, distribution_tab, profile_tab, download_tab = st.tabs(
        [
            "Customers",
            "Cluster Stats",
            "PCA Scatter",
            "Distribution",
            "Profiles",
            "Downloads",
        ]
    )

    with table_tab:
        _render_cluster_table(selected_df, algorithm_label)

    with stats_tab:
        st.dataframe(build_cluster_descriptive_stats(selected_df), width="stretch")

    with pca_tab:
        try:
            projection = build_pca_projection(selected_df, algorithm_label)
        except ClusteringDataError as error:
            st.error(str(error))
        else:
            st.altair_chart(make_pca_scatter(projection), width="stretch")

    with distribution_tab:
        st.dataframe(summary, hide_index=True, width="stretch")
        st.altair_chart(make_cluster_distribution_chart(summary), width="stretch")

    with profile_tab:
        profile = build_profile_table(outputs.profiles, algorithm_label)
        if profile is None:
            st.info("Cluster profile data is not available for this algorithm.")
        else:
            st.dataframe(profile, hide_index=True, width="stretch")

    with download_tab:
        _render_download(selected_df, algorithm_label)


def _read_required_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise ClusteringDataError(f"{label} file not found: {path}")
    try:
        df = pd.read_csv(path)
    except Exception as error:
        raise ClusteringDataError(f"Cannot read {label} file {path}: {error}") from error
    if df.empty:
        raise ClusteringDataError(f"{label} file is empty: {path}")
    return df


def _validate_results_frame(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    required_columns = [
        *REQUIRED_RESULT_COLUMNS,
        *(config.cluster_column for config in ALGORITHMS.values()),
    ]
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ClusteringDataError(
            f"{path} is missing required columns: {', '.join(missing)}"
        )

    validated = df[required_columns].copy()
    validated[ID_COLUMN] = validated[ID_COLUMN].astype(str).astype(object)

    invalid_numeric = []
    for column in FEATURE_COLUMNS:
        validated[column] = pd.to_numeric(validated[column], errors="coerce")
        if validated[column].isna().any():
            invalid_numeric.append(column)

    invalid_clusters = []
    for config in ALGORITHMS.values():
        labels = pd.to_numeric(validated[config.cluster_column], errors="coerce")
        if labels.isna().any():
            invalid_clusters.append(config.cluster_column)
            continue
        validated[config.cluster_column] = labels.astype(int)

    if invalid_numeric:
        raise ClusteringDataError(
            f"{path} has invalid numeric RFM values in: {', '.join(invalid_numeric)}"
        )
    if invalid_clusters:
        raise ClusteringDataError(
            f"{path} has invalid cluster labels in: {', '.join(invalid_clusters)}"
        )

    return validated


def _validate_profiles_frame(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    missing = [column for column in PROFILE_COLUMNS if column not in df.columns]
    if missing:
        raise ClusteringDataError(
            f"{path} is missing required columns: {', '.join(missing)}"
        )

    profile = df.copy()
    for column in ["cluster", "n_customers"]:
        profile[column] = pd.to_numeric(profile[column], errors="coerce")
        if profile[column].isna().any():
            raise ClusteringDataError(f"{path} has invalid numeric values in: {column}")
        profile[column] = profile[column].astype(int)

    for column in ["share", "revenue_share"]:
        profile[column] = pd.to_numeric(profile[column], errors="coerce")
        if profile[column].isna().any():
            raise ClusteringDataError(f"{path} has invalid numeric values in: {column}")

    return profile


def _get_algorithm_config(algorithm_label: str) -> AlgorithmConfig:
    if algorithm_label not in ALGORITHMS:
        raise ValueError(f"Unknown clustering algorithm: {algorithm_label}")
    return ALGORITHMS[algorithm_label]


def _render_cluster_table(df: pd.DataFrame, algorithm_label: str) -> None:
    key_prefix = algorithm_label.lower().replace(" ", "_").replace("-", "_")
    display_columns = [ID_COLUMN, *FEATURE_COLUMNS, CLUSTER_COLUMN]

    control_left, control_mid, control_right, control_page = st.columns([2, 1, 1, 1])
    with control_left:
        search = st.text_input(
            "Search CustomerID",
            placeholder="Example: 12347",
            key=f"{key_prefix}_cluster_search",
        )
    with control_mid:
        sort_column = st.selectbox(
            "Sort by",
            display_columns,
            index=0,
            key=f"{key_prefix}_cluster_sort_column",
        )
    with control_right:
        ascending = st.toggle(
            "Ascending",
            value=True,
            key=f"{key_prefix}_cluster_ascending",
        )
    with control_page:
        page_size = st.selectbox(
            "Rows/page",
            [10, 25, 50, 100],
            index=1,
            key=f"{key_prefix}_cluster_page_size",
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
        key=f"{key_prefix}_cluster_page_{len(sorted_df)}_{page_size}",
    )

    page = paginate_dataframe(sorted_df, page_size, int(page_number))
    st.caption(
        f"Showing {page.start_row:,}-{page.end_row:,} of {len(sorted_df):,} customers"
    )
    st.dataframe(page.dataframe, hide_index=True, width="stretch")


def _render_download(df: pd.DataFrame, algorithm_label: str) -> None:
    config = _get_algorithm_config(algorithm_label)
    st.download_button(
        f"Download {config.download_filename}",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=config.download_filename,
        mime="text/csv",
    )


if __name__ == "__main__":
    render_dashboard()
