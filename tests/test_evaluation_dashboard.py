from __future__ import annotations

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.visualization.evaluation_dashboard import (  # noqa: E402
    EvaluationDataError,
    build_evaluation_table,
    build_radar_frame,
    filter_by_model,
    load_evaluation_outputs,
    make_interpretability_chart,
    make_overall_score_chart,
    make_quality_chart,
    make_radar_chart,
    make_separation_chart,
    make_stability_chart,
)


def comparison_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "model": ["K-Means", "GMM", "HDBSCAN"],
            "n_clusters": [3, 3, 3],
            "n_noise": [0, 0, 854],
            "silhouette": [0.4143, 0.4144, 0.2028],
            "davies_bouldin": [0.8292, 0.8166, 1.1955],
            "calinski_harabasz": [4389.58, 4364.69, 2404.56],
            "mean_ari": [0.9751, 0.9747, 0.9543],
            "customer_coverage": [1.0, 1.0, 0.8024],
            "revenue_coverage": [1.0, 1.0, 0.4596],
            "score_quality": [0.9887, 0.9958, 0.0],
            "score_stability": [1.0, 0.9812, 0.0],
            "score_interpretability": [0.9762, 1.0, 0.0],
            "score_overall": [0.9883, 0.9923, 0.0],
        }
    )


def stability_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "model": ["K-Means", "GMM", "HDBSCAN"],
            "mean_ari": [0.9751, 0.9747, 0.9543],
            "std_ari": [0.0136, 0.0143, 0.0506],
            "min_ari": [0.9292, 0.9206, 0.6893],
            "max_ari": [0.9989, 1.0, 0.9811],
            "stability": ["Very stable", "Very stable", "Stable"],
        }
    )


def separation_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "model": ["K-Means", "GMM", "HDBSCAN"],
            "delta_recency": [2.24, 2.29, 1.25],
            "delta_frequency": [1.95, 1.98, 1.70],
            "delta_monetary": [1.88, 1.93, 1.48],
            "delta_mean": [2.02, 2.07, 1.48],
            "delta_min": [1.88, 1.93, 1.25],
        }
    )


def profiles_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "model": ["K-Means", "GMM", "HDBSCAN"],
            "cluster": [0, 0, -1],
            "segment": ["Low", "Low", "Noise"],
            "n_customers": [990, 923, 854],
            "share": [0.22, 0.21, 0.19],
            "revenue_share": [0.04, 0.04, 0.54],
            "strategy": ["Recover", "Recover", "Handle separately"],
        }
    )


def write_evaluation_outputs(tmp_path, comparison=None, stability=None, separation=None, profiles=None):
    comparison_path = tmp_path / "model_comparison.csv"
    stability_path = tmp_path / "stability_results.csv"
    separation_path = tmp_path / "cluster_separation.csv"
    profiles_path = tmp_path / "cluster_profiles.csv"
    (comparison if comparison is not None else comparison_frame()).to_csv(comparison_path, index=False)
    (stability if stability is not None else stability_frame()).to_csv(stability_path, index=False)
    (separation if separation is not None else separation_frame()).to_csv(separation_path, index=False)
    (profiles if profiles is not None else profiles_frame()).to_csv(profiles_path, index=False)
    return comparison_path, stability_path, separation_path, profiles_path


def test_load_evaluation_outputs_validates_all_task12_files(tmp_path):
    paths = write_evaluation_outputs(tmp_path)

    outputs = load_evaluation_outputs(*paths)

    assert len(outputs.comparison) == 3
    assert len(outputs.stability) == 3
    assert len(outputs.separation) == 3
    assert len(outputs.profiles) == 3


def test_load_evaluation_outputs_reports_missing_required_column(tmp_path):
    broken = comparison_frame().drop(columns=["score_overall"])
    paths = write_evaluation_outputs(tmp_path, comparison=broken)

    with pytest.raises(EvaluationDataError, match="score_overall"):
        load_evaluation_outputs(*paths)


def test_evaluation_table_is_sorted_by_overall_score_and_searchable():
    table = build_evaluation_table(comparison_frame())
    filtered = filter_by_model(table, "gmm")

    assert table.iloc[0]["model"] == "GMM"
    assert filtered["model"].tolist() == ["GMM"]


def test_radar_frame_closes_each_model_polygon():
    radar = build_radar_frame(comparison_frame())

    assert len(radar) == 15
    for model, group in radar.groupby("model"):
        assert group.iloc[0]["Metric"] == group.iloc[-1]["Metric"], model
        assert group.iloc[-1]["Order"] == 4


def test_evaluation_charts_export_to_altair_specs():
    comparison = comparison_frame()
    stability = stability_frame()
    separation = separation_frame()

    make_quality_chart(comparison).to_dict()
    make_stability_chart(stability).to_dict()
    make_interpretability_chart(comparison).to_dict()
    make_radar_chart(comparison).to_dict()
    make_overall_score_chart(comparison).to_dict()
    make_separation_chart(separation).to_dict()
