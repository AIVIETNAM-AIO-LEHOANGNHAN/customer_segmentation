from __future__ import annotations

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.visualization.clustering_dashboard import (  # noqa: E402
    CLUSTER_COLUMN,
    ClusteringDataError,
    build_algorithm_frame,
    build_cluster_descriptive_stats,
    build_cluster_summary,
    build_pca_projection,
    build_profile_table,
    count_clusters,
    count_noise,
    load_clustering_outputs,
    make_cluster_distribution_chart,
    make_pca_scatter,
)


def cluster_results() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CustomerID": ["9999", "12347", "12348", "555"],
            "Recency": [12, 2, 75, 310],
            "Frequency": [2, 7, 4, 1],
            "Monetary": [90.0, 4310.0, 1437.24, 294.4],
            "K-Means_Cluster": [0, 2, 2, 0],
            "GMM_Cluster": [1, 2, 2, 0],
            "HDBSCAN_Cluster": [-1, 1, 1, 0],
        }
    )


def cluster_profiles() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "model": ["K-Means", "K-Means", "GMM", "HDBSCAN"],
            "cluster": [0, 2, 1, -1],
            "segment": ["Low", "High", "Mixed", "Noise"],
            "n_customers": [2, 2, 1, 1],
            "share": [0.5, 0.5, 0.25, 0.25],
            "revenue_share": [0.1, 0.9, 0.2, 0.3],
            "strategy": ["Recover", "Retain", "Review", "Handle separately"],
        }
    )


def write_cluster_outputs(tmp_path, results=None, profiles=None):
    results_path = tmp_path / "customer_clusters_all_models.csv"
    profiles_path = tmp_path / "cluster_profiles.csv"
    (results if results is not None else cluster_results()).to_csv(results_path, index=False)
    (profiles if profiles is not None else cluster_profiles()).to_csv(profiles_path, index=False)
    return results_path, profiles_path


def test_load_clustering_outputs_validates_task12_files(tmp_path):
    results_path, profiles_path = write_cluster_outputs(tmp_path)

    outputs = load_clustering_outputs(results_path, profiles_path)

    assert len(outputs.results) == 4
    assert outputs.results["CustomerID"].dtype == object
    assert outputs.profiles is not None
    assert len(outputs.profiles) == 4


def test_load_clustering_outputs_reports_missing_required_cluster_column(tmp_path):
    broken = cluster_results().drop(columns=["GMM_Cluster"])
    results_path, profiles_path = write_cluster_outputs(tmp_path, results=broken)

    with pytest.raises(ClusteringDataError, match="GMM_Cluster"):
        load_clustering_outputs(results_path, profiles_path)


def test_build_algorithm_frame_uses_selected_cluster_column(tmp_path):
    results_path, profiles_path = write_cluster_outputs(tmp_path)
    outputs = load_clustering_outputs(results_path, profiles_path)

    gmm = build_algorithm_frame(outputs, "Gaussian Mixture Model (GMM)")

    assert list(gmm.columns) == ["CustomerID", "Recency", "Frequency", "Monetary", CLUSTER_COLUMN]
    assert gmm[CLUSTER_COLUMN].tolist() == [1, 2, 2, 0]


def test_hdbscan_summary_counts_clusters_and_noise(tmp_path):
    results_path, profiles_path = write_cluster_outputs(tmp_path)
    outputs = load_clustering_outputs(results_path, profiles_path)
    hdbscan = build_algorithm_frame(outputs, "HDBSCAN")

    summary = build_cluster_summary(hdbscan, "HDBSCAN")

    assert count_clusters(summary, "HDBSCAN") == 2
    assert count_noise(summary, "HDBSCAN") == 1
    assert "Noise" in summary["ClusterLabel"].tolist()


def test_cluster_stats_profile_and_charts_export(tmp_path):
    results_path, profiles_path = write_cluster_outputs(tmp_path)
    outputs = load_clustering_outputs(results_path, profiles_path)
    kmeans = build_algorithm_frame(outputs, "K-Means")

    stats = build_cluster_descriptive_stats(kmeans)
    profile = build_profile_table(outputs.profiles, "K-Means")
    projection = build_pca_projection(kmeans, "K-Means")
    summary = build_cluster_summary(kmeans, "K-Means")

    assert set(stats[CLUSTER_COLUMN]) == {0, 2}
    assert profile is not None
    assert profile["Segment"].tolist() == ["Low", "High"]
    assert {"PC1", "PC2", "ClusterLabel"}.issubset(projection.columns)
    make_pca_scatter(projection).to_dict()
    make_cluster_distribution_chart(summary).to_dict()
