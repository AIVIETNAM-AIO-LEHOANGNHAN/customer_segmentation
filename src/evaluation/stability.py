import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.clustering import (  # noqa: E402
    NOISE_LABEL,
    load_scaled_rfm,
    train_gmm,
    train_hdbscan,
    train_kmeans,
)

N_ITERATIONS = 50
SAMPLE_SIZE = 0.8
RANDOM_STATE = 42

# Nhãn đánh dấu điểm không nằm trong tập lấy mẫu của một lần lặp.
NOT_SAMPLED = -2

# Ngưỡng diễn giải độ ổn định: (Mean ARI tối thiểu, Std ARI tối đa, mức độ).
# Std ARI được đưa vào ngưỡng vì một mô hình có Mean ARI cao nhưng biến động
# lớn giữa các lần chạy không thể coi là ổn định như mô hình biến động thấp.
STABILITY_LEVELS = (
    (0.90, 0.03, "Rất ổn định"),
    (0.75, 0.10, "Ổn định"),
    (0.50, float("inf"), "Trung bình"),
)


def _parse_param_value(value):
    """Chuyển một giá trị tham số dạng chuỗi về đúng kiểu dữ liệu Python."""
    value = value.strip()

    if value == "None":
        return None
    if value.lstrip("-").isdigit():
        return int(value)

    return value


def load_best_configs(filepath, metric="silhouette"):
    """
    Đọc kết quả thực nghiệm của Task 12 và lấy cấu hình tốt nhất của từng
    thuật toán theo `metric`. Trả về dict {tên mô hình: dict tham số}.
    """
    results = pd.read_csv(filepath)
    best = results.loc[results.groupby("model")[metric].idxmax()]

    configs = {}
    for _, row in best.iterrows():
        params = dict(
            item.split("=", 1) for item in str(row["params"]).split(",")
        )
        configs[row["model"]] = {
            key.strip(): _parse_param_value(value) for key, value in params.items()
        }

    print(f"Loaded best configurations from {filepath} (metric: {metric})")
    for model, params in configs.items():
        print(f"  {model:<8}: {params}")

    return configs


def generate_samples(n_rows, n_iterations=N_ITERATIONS, sample_size=SAMPLE_SIZE,
                     random_state=RANDOM_STATE):
    """
    Sinh `n_iterations` tập chỉ số con, mỗi tập lấy ngẫu nhiên không hoàn lại
    `sample_size` phần dữ liệu gốc. Trả về danh sách các mảng chỉ số.
    """
    rng = np.random.default_rng(random_state)
    n_sample = int(round(n_rows * sample_size))

    return [
        np.sort(rng.choice(n_rows, size=n_sample, replace=False))
        for _ in range(n_iterations)
    ]


def fit_on_sample(model_name, X_sample, config):
    """
    Huấn luyện lại một thuật toán trên tập dữ liệu con và trả về nhãn cụm
    kèm các thông tin cần ghi lại của riêng thuật toán đó.
    """
    if model_name == "K-Means":
        result = train_kmeans(X_sample, config["n_clusters"])
        labels = result["labels"]
        extra = {"inertia": result["inertia"]}

    elif model_name == "GMM":
        result = train_gmm(X_sample, config["n_components"], config["covariance_type"])
        labels = result["labels"]
        proba = result["model"].predict_proba(X_sample).max(axis=1)
        extra = {
            "log_likelihood": result["log_likelihood"],
            "mean_max_proba": float(proba.mean()),
            "low_confidence_ratio": float((proba < 0.8).mean()),
        }

    elif model_name == "HDBSCAN":
        result = train_hdbscan(X_sample, config["min_cluster_size"], config["min_samples"])
        labels = result["labels"]
        extra = {
            "n_noise": result["n_noise"],
            "noise_ratio": result["n_noise"] / len(X_sample),
        }

    else:
        raise ValueError(f"Unknown model: {model_name}")

    return {
        "labels": labels,
        "n_clusters": len(set(labels) - {NOISE_LABEL}),
        "train_time": result["train_time"],
        **extra,
    }


def run_resampling(X, configs, n_iterations=N_ITERATIONS, sample_size=SAMPLE_SIZE,
                   random_state=RANDOM_STATE):
    """
    Huấn luyện lại từng thuật toán trên `n_iterations` tập dữ liệu con.

    Trả về (label_matrices, iterations):
      - label_matrices: dict {mô hình: ma trận (n_iterations, n_rows)}, ô nào
        không thuộc tập mẫu của lần lặp mang giá trị NOT_SAMPLED.
      - iterations: DataFrame ghi lại kết quả của từng lần lặp.
    """
    samples = generate_samples(len(X), n_iterations, sample_size, random_state)

    label_matrices = {
        model: np.full((n_iterations, len(X)), NOT_SAMPLED, dtype=int)
        for model in configs
    }
    rows = []

    for model_name, config in configs.items():
        for iteration, indices in enumerate(samples):
            result = fit_on_sample(model_name, X[indices], config)

            label_matrices[model_name][iteration, indices] = result["labels"]
            rows.append({
                "model": model_name,
                "iteration": iteration,
                "n_sample": len(indices),
                **{key: value for key, value in result.items() if key != "labels"},
            })

        print(f"  {model_name:<8}: trained on {n_iterations} resampled datasets")

    return label_matrices, pd.DataFrame(rows)


def pairwise_ari(label_matrix, ignore_noise=False):
    """
    Tính ARI giữa mọi cặp lần lặp, chỉ trên các điểm xuất hiện ở cả hai tập mẫu.
    Đặt ignore_noise=True để loại thêm các điểm bị gán nhãn nhiễu.
    Trả về mảng ARI của tất cả các cặp.
    """
    scores = []

    for i in range(len(label_matrix)):
        for j in range(i + 1, len(label_matrix)):
            first, second = label_matrix[i], label_matrix[j]
            mask = (first != NOT_SAMPLED) & (second != NOT_SAMPLED)

            if ignore_noise:
                mask &= (first != NOISE_LABEL) & (second != NOISE_LABEL)

            if mask.sum() < 2:
                continue

            scores.append(adjusted_rand_score(first[mask], second[mask]))

    return np.array(scores)


def reference_ari(X, label_matrix, model_name, config):
    """
    Tính ARI giữa kết quả của từng lần lặp và kết quả huấn luyện trên toàn bộ
    dữ liệu, đo trên phần dữ liệu được lấy mẫu của lần lặp đó.
    """
    reference = fit_on_sample(model_name, X, config)["labels"]

    scores = []
    for labels in label_matrix:
        mask = labels != NOT_SAMPLED
        scores.append(adjusted_rand_score(reference[mask], labels[mask]))

    return np.array(scores)


def classify_stability(mean_ari, std_ari):
    """Diễn giải cặp (Mean ARI, Std ARI) thành mức độ ổn định."""
    for min_mean, max_std, level in STABILITY_LEVELS:
        if mean_ari >= min_mean and std_ari <= max_std:
            return level

    return "Không ổn định"


def summarize_stability(X, configs, label_matrices, iterations):
    """
    Tổng hợp Mean ARI, Std ARI và mức độ ổn định của từng thuật toán thành
    một bảng so sánh duy nhất.
    """
    rows = []

    for model_name, config in configs.items():
        scores = pairwise_ari(label_matrices[model_name])
        reference = reference_ari(X, label_matrices[model_name], model_name, config)
        detail = iterations[iterations["model"] == model_name]

        row = {
            "model": model_name,
            "params": ", ".join(f"{key}={value}" for key, value in config.items()),
            "n_iterations": len(label_matrices[model_name]),
            "n_pairs": len(scores),
            "mean_ari": scores.mean(),
            "std_ari": scores.std(ddof=1),
            "min_ari": scores.min(),
            "max_ari": scores.max(),
            "mean_reference_ari": reference.mean(),
            "std_reference_ari": reference.std(ddof=1),
            "mean_n_clusters": detail["n_clusters"].mean(),
            "min_n_clusters": detail["n_clusters"].min(),
            "max_n_clusters": detail["n_clusters"].max(),
            "mean_train_time": detail["train_time"].mean(),
            "stability": classify_stability(scores.mean(), scores.std(ddof=1)),
        }

        if model_name == "HDBSCAN":
            clean = pairwise_ari(label_matrices[model_name], ignore_noise=True)
            row["mean_ari_no_noise"] = clean.mean()
            row["std_ari_no_noise"] = clean.std(ddof=1)
            row["mean_noise_ratio"] = detail["noise_ratio"].mean()

        rows.append(row)

    return pd.DataFrame(rows).sort_values("mean_ari", ascending=False)


def save_results(summary, output_path):
    """Lưu bảng tổng hợp độ ổn định."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    summary.to_csv(output_path, index=False)
    print(f"Saved stability summary for {len(summary)} models to {output_path}")

    return summary


if __name__ == "__main__":
    df, X = load_scaled_rfm("data/processed/rfm_scaled.csv")

    configs = load_best_configs("outputs/results/clustering_experiments.csv")

    print(f"\nResampling: {N_ITERATIONS} iterations, sample size {SAMPLE_SIZE:.0%}")
    label_matrices, iterations = run_resampling(X, configs)

    iterations.to_csv("outputs/results/stability_iterations.csv", index=False)

    summary = summarize_stability(X, configs, label_matrices, iterations)
    save_results(summary, "data/processed/stability_results.csv")

    print("\n" + summary[["model", "mean_ari", "std_ari", "stability"]].to_string(index=False))
