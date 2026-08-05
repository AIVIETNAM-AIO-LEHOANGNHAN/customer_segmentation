import os
import time

import pandas as pd
from sklearn.cluster import HDBSCAN, KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture

FEATURE_COLUMNS = ("Recency", "Frequency", "Monetary")
RANDOM_STATE = 42
MAX_ITER = 300
NOISE_LABEL = -1


def load_scaled_rfm(filepath):
    """
    Đọc bộ RFM đã chuẩn hóa từ Epic 2 và in các thông tin kiểm tra đầu vào.
    Trả về (df, X) với X là ma trận đặc trưng dùng cho phân cụm.
    """
    df = pd.read_csv(filepath)

    missing = [col for col in FEATURE_COLUMNS if col not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {', '.join(missing)}")

    print(f"Loaded {filepath}")
    print(f"  Customers: {len(df)}")
    print(f"  Features : {list(FEATURE_COLUMNS)}")
    print(f"  Missing  : {df[list(FEATURE_COLUMNS)].isna().sum().to_dict()}")
    print(f"  Dtypes   : {df[list(FEATURE_COLUMNS)].dtypes.to_dict()}")

    return df, df[list(FEATURE_COLUMNS)].values


def train_kmeans(X, n_clusters):
    """Huấn luyện K-Means, trả về nhãn cụm, inertia và thời gian huấn luyện."""
    model = KMeans(
        n_clusters=n_clusters,
        init="k-means++",
        n_init="auto",
        max_iter=MAX_ITER,
        random_state=RANDOM_STATE,
    )

    start = time.perf_counter()
    labels = model.fit_predict(X)
    train_time = time.perf_counter() - start

    return {
        "model": model,
        "labels": labels,
        "inertia": model.inertia_,
        "train_time": train_time,
    }


def train_gmm(X, n_components, covariance_type="full"):
    """Huấn luyện GMM, trả về nhãn cụm, log-likelihood và thời gian huấn luyện."""
    model = GaussianMixture(
        n_components=n_components,
        covariance_type=covariance_type,
        max_iter=MAX_ITER,
        random_state=RANDOM_STATE,
    )

    start = time.perf_counter()
    labels = model.fit_predict(X)
    train_time = time.perf_counter() - start

    return {
        "model": model,
        "labels": labels,
        "log_likelihood": model.score(X) * len(X),
        "train_time": train_time,
    }


def train_hdbscan(X, min_cluster_size, min_samples=None):
    """
    Huấn luyện HDBSCAN, trả về nhãn cụm, số cụm phát hiện được,
    số điểm nhiễu và thời gian huấn luyện.
    """
    model = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
        cluster_selection_method="eom",
    )

    start = time.perf_counter()
    labels = model.fit_predict(X)
    train_time = time.perf_counter() - start

    return {
        "model": model,
        "labels": labels,
        "n_clusters": len(set(labels) - {NOISE_LABEL}),
        "n_noise": int((labels == NOISE_LABEL).sum()),
        "train_time": train_time,
    }


def evaluate_model(X, labels, drop_noise=False):
    """
    Tính Silhouette Score, Davies-Bouldin Index và Calinski-Harabasz Index.
    Với HDBSCAN, đặt drop_noise=True để loại các điểm nhiễu trước khi tính.
    Trả về các chỉ số bằng None nếu số cụm hợp lệ nhỏ hơn 2.
    """
    if drop_noise:
        mask = labels != NOISE_LABEL
        X, labels = X[mask], labels[mask]

    if len(set(labels)) < 2:
        return {"silhouette": None, "davies_bouldin": None, "calinski_harabasz": None}

    return {
        "silhouette": silhouette_score(X, labels),
        "davies_bouldin": davies_bouldin_score(X, labels),
        "calinski_harabasz": calinski_harabasz_score(X, labels),
    }


def compare_models(X, k_values=range(2, 11), covariance_types=("full", "tied", "diag", "spherical"),
                   min_cluster_sizes=(5, 10, 20, 30, 50), min_samples_values=(None, 5, 10)):
    """
    Huấn luyện toàn bộ không gian tham số của ba thuật toán và tổng hợp
    kết quả đánh giá vào một DataFrame duy nhất để so sánh.
    """
    rows = []

    for k in k_values:
        result = train_kmeans(X, k)
        rows.append({
            "model": "K-Means",
            "params": f"n_clusters={k}",
            "n_clusters": k,
            "n_noise": 0,
            "inertia": result["inertia"],
            "train_time": result["train_time"],
            **evaluate_model(X, result["labels"]),
        })

    for covariance_type in covariance_types:
        for k in k_values:
            result = train_gmm(X, k, covariance_type)
            rows.append({
                "model": "GMM",
                "params": f"n_components={k}, covariance_type={covariance_type}",
                "n_clusters": len(set(result["labels"])),
                "n_noise": 0,
                "log_likelihood": result["log_likelihood"],
                "train_time": result["train_time"],
                **evaluate_model(X, result["labels"]),
            })

    for min_cluster_size in min_cluster_sizes:
        for min_samples in min_samples_values:
            result = train_hdbscan(X, min_cluster_size, min_samples)
            rows.append({
                "model": "HDBSCAN",
                "params": f"min_cluster_size={min_cluster_size}, min_samples={min_samples}",
                "n_clusters": result["n_clusters"],
                "n_noise": result["n_noise"],
                "train_time": result["train_time"],
                **evaluate_model(X, result["labels"], drop_noise=True),
            })

    return pd.DataFrame(rows)


def save_cluster_result(customer_ids, labels, output_path):
    """Lưu bảng CustomerID - Cluster của mô hình được chọn."""
    result = pd.DataFrame({"CustomerID": customer_ids, "Cluster": labels})

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result.to_csv(output_path, index=False)
    print(f"Saved {len(result)} cluster labels to {output_path}")

    return result


if __name__ == "__main__":
    df, X = load_scaled_rfm("data/processed/rfm_scaled.csv")

    results = compare_models(X)
    results.to_csv("outputs/results/clustering_experiments.csv", index=False)

    # K-Means là mô hình được chọn (xem outputs/reports/clustering_comparison.md):
    # Silhouette ngang GMM tốt nhất nhưng CHI cao hơn, kết quả tất định và dễ diễn giải.
    kmeans_results = results[results["model"] == "K-Means"]
    best = kmeans_results.sort_values("silhouette", ascending=False).iloc[0]
    print(f"\nSelected configuration: {best['model']} ({best['params']}), "
          f"silhouette={best['silhouette']:.4f}")

    best_labels = train_kmeans(X, int(best["n_clusters"]))["labels"]
    save_cluster_result(df["CustomerID"], best_labels, "data/processed/customer_clusters.csv")
