import os
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.cluster_interpretability import (  # noqa: E402
    GRID_COLOR,
    MODEL_ORDER,
    NOISE_SEGMENT,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    _style_axes,
)

# Mỗi chỉ số gồm: hướng tối ưu ("max" hoặc "min") và nhóm tiêu chí mà nó thuộc về.
METRICS = {
    "silhouette": ("max", "quality"),
    "davies_bouldin": ("min", "quality"),
    "calinski_harabasz": ("max", "quality"),
    "mean_ari": ("max", "stability"),
    "std_ari": ("min", "stability"),
    "delta_mean": ("max", "interpretability"),
    "n_noise": ("min", "interpretability"),
    "revenue_coverage": ("max", "interpretability"),
}

GROUPS = ("quality", "stability", "interpretability")

GROUP_LABELS = {
    "quality": "Chất lượng phân cụm",
    "stability": "Độ ổn định",
    "interpretability": "Khả năng diễn giải",
    "overall": "Điểm tổng hợp",
}

MODEL_COLORS = {"K-Means": "#2a78d6", "GMM": "#eb6834", "HDBSCAN": "#1baf7a"}


def collect_results(experiments_path, stability_path, separation_path, profiles_path):
    """
    Thu thập kết quả đánh giá của ba task trước vào một bảng duy nhất:
    chất lượng phân cụm (Task 12), độ ổn định (Task 13), khả năng diễn giải và
    ý nghĩa nghiệp vụ (Task 14).
    """
    experiments = pd.read_csv(experiments_path)
    best = (
        experiments.loc[experiments.groupby("model")["silhouette"].idxmax()]
        .set_index("model")[["params", "n_clusters", "n_noise",
                             "silhouette", "davies_bouldin", "calinski_harabasz"]]
    )

    stability = pd.read_csv(stability_path).set_index("model")[["mean_ari", "std_ari", "stability"]]
    separation = pd.read_csv(separation_path).set_index("model")[["delta_mean", "delta_min"]]

    profiles = pd.read_csv(profiles_path)
    named = profiles[profiles["segment"] != NOISE_SEGMENT]
    business = named.groupby("model").agg(
        n_segments=("segment", "nunique"),
        customer_coverage=("share", "sum"),
        revenue_coverage=("revenue_share", "sum"),
    )

    results = best.join([stability, separation, business]).loc[list(MODEL_ORDER)]

    return results.rename_axis("model").reset_index()


def normalize_scores(results, metrics=METRICS):
    """
    Chuẩn hóa Min-Max từng chỉ số về thang [0, 1] theo hướng "càng lớn càng tốt".
    Các chỉ số cần tối thiểu được đảo chiều trước khi chuẩn hóa.
    Khi ba mô hình có cùng giá trị, cả ba cùng nhận điểm 1.
    """
    normalized = results[["model"]].copy()

    for column, (direction, _) in metrics.items():
        values = results[column].astype(float)
        values = -values if direction == "min" else values
        span = values.max() - values.min()

        normalized[f"norm_{column}"] = 1.0 if span == 0 else (values - values.min()) / span

    return normalized


def composite_scores(normalized, metrics=METRICS, groups=GROUPS):
    """
    Gộp các chỉ số đã chuẩn hóa thành ba điểm nhóm và một điểm tổng hợp.
    Trong mỗi nhóm các chỉ số có trọng số bằng nhau, và ba nhóm cũng có trọng số
    bằng nhau ở điểm tổng hợp, vì không có căn cứ khách quan để ưu tiên nhóm nào.
    """
    scores = normalized[["model"]].copy()

    for group in groups:
        columns = [f"norm_{name}" for name, (_, g) in metrics.items() if g == group]
        scores[f"score_{group}"] = normalized[columns].mean(axis=1)

    scores["score_overall"] = scores[[f"score_{group}" for group in groups]].mean(axis=1)

    return scores


def build_comparison_table(results, metrics=METRICS, groups=GROUPS):
    """Ghép giá trị gốc, giá trị đã chuẩn hóa và điểm tổng hợp vào một bảng."""
    normalized = normalize_scores(results, metrics)
    scores = composite_scores(normalized, metrics, groups)

    table = results.merge(normalized, on="model").merge(scores, on="model")

    return table.sort_values("score_overall", ascending=False)


def weight_sensitivity(scores, groups=GROUPS, step=0.1):
    """
    Kiểm tra xem thứ hạng có phụ thuộc vào cách chọn trọng số hay không, bằng cách
    quét toàn bộ các bộ trọng số là bội của `step` và cộng lại bằng 1.
    Trả về số lần mỗi mô hình đứng đầu.
    """
    columns = [f"score_{group}" for group in groups]
    matrix = scores.set_index("model")[columns]

    steps = np.arange(0, 1 + step / 2, step)
    winners = []

    for weight_quality in steps:
        for weight_stability in steps:
            weight_interpretability = 1 - weight_quality - weight_stability
            if weight_interpretability < -step / 2:
                continue

            weights = np.array([weight_quality, weight_stability, max(weight_interpretability, 0)])
            winners.append((matrix.values @ weights).argmax())

    counts = pd.Series(winners).value_counts().sort_index()

    return pd.DataFrame({
        "model": matrix.index[counts.index],
        "n_weightings_won": counts.values,
        "share_of_weightings": counts.values / len(winners),
    }).sort_values("n_weightings_won", ascending=False)


def plot_score_comparison(table, output_path):
    """
    Biểu đồ so sánh ba mô hình: hàng trên là điểm đã chuẩn hóa theo ba nhóm tiêu
    chí và điểm tổng hợp, hàng dưới là ba chỉ số gốc tiêu biểu trên thang đo thật.
    Hàng dưới là cần thiết vì chuẩn hóa Min-Max trên ba mô hình luôn đẩy mô hình
    kém nhất về 0, dễ bị đọc nhầm thành "không có giá trị nào".
    """
    table = table.set_index("model").loc[list(MODEL_ORDER)]

    figure = plt.figure(figsize=(14, 8), facecolor=SURFACE)
    grid = figure.add_gridspec(2, 3, height_ratios=[1.25, 1], hspace=0.42, wspace=0.28)

    top = figure.add_subplot(grid[0, :])
    columns = [f"score_{group}" for group in GROUPS] + ["score_overall"]
    labels = [GROUP_LABELS[group] for group in GROUPS] + [GROUP_LABELS["overall"]]
    positions = np.arange(len(columns))
    width = 0.8 / len(MODEL_ORDER)

    for index, model_name in enumerate(MODEL_ORDER):
        offset = (index - (len(MODEL_ORDER) - 1) / 2) * width
        values = table.loc[model_name, columns].values.astype(float)
        bars = top.bar(positions + offset, values, width * 0.92, label=model_name,
                       color=MODEL_COLORS[model_name], linewidth=0)

        for bar, value in zip(bars, values):
            top.annotate(f"{value:.3f}", (bar.get_x() + bar.get_width() / 2, value),
                         xytext=(0, 3), textcoords="offset points",
                         ha="center", fontsize=8, color=TEXT_SECONDARY)

    top.set_xticks(positions, labels)
    top.set_ylim(0, 1.12)
    top.set_ylabel("Điểm sau chuẩn hóa Min-Max", fontsize=9.5, color=TEXT_SECONDARY)
    top.set_title("Điểm đã chuẩn hóa theo ba nhóm tiêu chí — 1 là tốt nhất trong ba mô hình",
                  fontsize=11, color=TEXT_PRIMARY, pad=34)
    top.legend(frameon=False, fontsize=9.5, labelcolor=TEXT_SECONDARY, ncols=3,
               loc="lower left", bbox_to_anchor=(0, 1.005))
    _style_axes(top)

    raw_metrics = (
        ("silhouette", "Silhouette Score", "{:.4f}"),
        ("mean_ari", "Mean ARI (độ ổn định)", "{:.4f}"),
        ("delta_mean", "Δ trung bình (mức phân biệt)", "{:.3f}"),
    )

    for column, (metric, title, fmt) in enumerate(raw_metrics):
        ax = figure.add_subplot(grid[1, column])
        values = table[metric].values.astype(float)
        bars = ax.bar(np.arange(len(MODEL_ORDER)), values, 0.62,
                      color=[MODEL_COLORS[name] for name in MODEL_ORDER], linewidth=0)

        for bar, value in zip(bars, values):
            ax.annotate(fmt.format(value), (bar.get_x() + bar.get_width() / 2, value),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", fontsize=8.5, color=TEXT_SECONDARY)

        ax.set_xticks(np.arange(len(MODEL_ORDER)), list(MODEL_ORDER))
        ax.set_ylim(0, values.max() * 1.22)
        ax.set_title(title, fontsize=10, color=TEXT_PRIMARY, pad=8)
        _style_axes(ax)

    figure.suptitle("So sánh ba thuật toán phân cụm trên toàn bộ tiêu chí đánh giá",
                    fontsize=13, color=TEXT_PRIMARY, y=0.98)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    figure.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    plt.close(figure)
    print(f"Saved figure to {output_path}")

    return output_path


def save_table(table, output_path):
    """Lưu bảng so sánh tổng hợp phục vụ viết báo cáo."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    table.to_csv(output_path, index=False)
    print(f"Saved comparison table for {len(table)} models to {output_path}")

    return table


if __name__ == "__main__":
    results = collect_results(
        "outputs/results/clustering_experiments.csv",
        "data/processed/stability_results.csv",
        "outputs/results/cluster_separation.csv",
        "data/processed/cluster_profiles.csv",
    )

    table = build_comparison_table(results)
    save_table(table, "outputs/tables/model_comparison.csv")

    plot_score_comparison(table, "outputs/figures/model_score_comparison.png")

    print("\nGiá trị gốc:")
    print(results[["model", "n_clusters", "n_noise", "silhouette", "davies_bouldin",
                   "calinski_harabasz", "mean_ari", "std_ari", "delta_mean",
                   "n_segments", "customer_coverage", "revenue_coverage"]].round(4).to_string(index=False))

    print("\nĐiểm tổng hợp:")
    print(table[["model", "score_quality", "score_stability", "score_interpretability",
                 "score_overall"]].round(4).to_string(index=False))

    print("\nĐộ nhạy của thứ hạng theo trọng số:")
    print(weight_sensitivity(table).round(3).to_string(index=False))
