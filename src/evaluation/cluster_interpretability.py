import os
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.stability import fit_on_sample, load_best_configs  # noqa: E402
from models.clustering import FEATURE_COLUMNS, NOISE_LABEL  # noqa: E402

MODEL_ORDER = ("K-Means", "GMM", "HDBSCAN")

# Ngưỡng z-score dùng để gán nhãn nghiệp vụ cho cụm. Recency đã chuẩn hóa nên
# giá trị càng lớn nghĩa là lần mua gần nhất càng xa, tức càng xấu.
RECENCY_HIGH = 0.5
VALUE_HIGH = 0.5

NOISE_SEGMENT = "Chưa phân khúc (nhiễu)"

SEGMENT_STRATEGY = {
    "Khách hàng giá trị cao": "Giữ chân: ưu đãi riêng, chăm sóc chủ động, ưu tiên nguồn lực",
    "Khách hàng phổ thông": "Tăng giá trị: gợi ý mua kèm, chương trình tích điểm để nâng tần suất",
    "Khách hàng đã rời bỏ": "Kích hoạt lại: chiến dịch win-back, hoặc loại khỏi danh sách tiếp thị",
    "Khách hàng giá trị cao có nguy cơ rời bỏ": "Cảnh báo sớm: liên hệ trực tiếp trước khi mất hẳn",
    NOISE_SEGMENT: "Không áp dụng được chính sách: cần xử lý riêng ngoài quy trình phân khúc",
}

# Tên rút gọn dùng trên biểu đồ, nơi không đủ chỗ cho tên phân khúc đầy đủ.
SEGMENT_SHORT = {
    "Khách hàng giá trị cao": "Giá trị cao",
    "Khách hàng phổ thông": "Phổ thông",
    "Khách hàng đã rời bỏ": "Đã rời bỏ",
    "Khách hàng giá trị cao có nguy cơ rời bỏ": "Giá trị cao, nguy cơ rời bỏ",
    NOISE_SEGMENT: "Nhiễu",
}

# Bảng màu phân loại đã được kiểm định về độ tách biệt cho người mù màu.
# Màu gắn với phân khúc nghiệp vụ chứ không gắn với số hiệu cụm: số hiệu cụm do
# thuật toán sinh ra tùy tiện, nên nếu tô theo số hiệu thì cùng một màu sẽ mang
# ý nghĩa khác nhau ở ba biểu đồ và không so sánh được. Chỉ ba màu đầu được dùng
# cho các phân khúc xuất hiện trong dữ liệu này, vì biểu đồ PCA là dạng so sánh
# mọi cặp màu với nhau. Nhiễu dùng màu xám trung tính vì đó không phải phân khúc.
SEGMENT_COLORS = {
    "Khách hàng giá trị cao": "#2a78d6",
    "Khách hàng phổ thông": "#eb6834",
    "Khách hàng đã rời bỏ": "#1baf7a",
    "Khách hàng giá trị cao có nguy cơ rời bỏ": "#eda100",
    NOISE_SEGMENT: "#8a8880",
}

# Thứ tự hiển thị phân khúc trên chú giải, dùng chung cho cả ba mô hình.
SEGMENT_ORDER = tuple(SEGMENT_COLORS)

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID_COLOR = "#dcdbd6"


def fit_best_models(X, configs):
    """Huấn luyện lại cấu hình tốt nhất của từng thuật toán trên toàn bộ dữ liệu."""
    labels_by_model = {}

    for model_name in MODEL_ORDER:
        result = fit_on_sample(model_name, X, configs[model_name])
        labels_by_model[model_name] = result["labels"]
        print(f"  {model_name:<8}: {result['n_clusters']} cụm"
              f"{', ' + str(result['n_noise']) + ' điểm nhiễu' if 'n_noise' in result else ''}")

    return labels_by_model


def build_labeled_customers(rfm_raw, labels_by_model):
    """
    Ghép giá trị RFM gốc với nhãn cụm của cả ba mô hình vào một bảng duy nhất.
    Đây là dữ liệu đầu vào cho toàn bộ các bước phân tích phía sau.
    """
    labeled = rfm_raw[["CustomerID", *FEATURE_COLUMNS]].copy()

    for model_name, labels in labels_by_model.items():
        labeled[f"{model_name}_Cluster"] = labels

    return labeled


def cluster_z_means(X, labels):
    """Giá trị trung bình của từng đặc trưng đã chuẩn hóa, theo từng cụm."""
    return (
        pd.DataFrame(X, columns=list(FEATURE_COLUMNS))
        .groupby(labels)
        .mean()
        .rename_axis("cluster")
    )


def assign_segment(recency_z, frequency_z, monetary_z, cluster=None):
    """
    Gán nhãn nghiệp vụ cho một cụm dựa trên z-score trung bình của cụm đó.
    `value_z` gộp Frequency và Monetary thành một trục giá trị khách hàng.
    """
    if cluster == NOISE_LABEL:
        return NOISE_SEGMENT

    value_z = (frequency_z + monetary_z) / 2

    if recency_z >= RECENCY_HIGH and value_z >= VALUE_HIGH:
        return "Khách hàng giá trị cao có nguy cơ rời bỏ"
    if recency_z >= RECENCY_HIGH:
        return "Khách hàng đã rời bỏ"
    if value_z >= VALUE_HIGH:
        return "Khách hàng giá trị cao"

    return "Khách hàng phổ thông"


def build_cluster_profiles(labeled, X, labels_by_model):
    """
    Xây dựng hồ sơ của từng cụm: thống kê mô tả RFM trên thang giá trị gốc,
    quy mô cụm, đóng góp doanh thu, z-score trung bình và nhãn nghiệp vụ.
    Trả về một DataFrame gộp kết quả của cả ba mô hình.
    """
    total_revenue = labeled["Monetary"].sum()
    rows = []

    for model_name, labels in labels_by_model.items():
        z_means = cluster_z_means(X, labels)
        grouped = labeled.groupby(labels)

        for cluster, group in grouped:
            z = z_means.loc[cluster]
            revenue = group["Monetary"].sum()

            row = {
                "model": model_name,
                "cluster": cluster,
                "segment": assign_segment(*z[list(FEATURE_COLUMNS)], cluster=cluster),
                "n_customers": len(group),
                "share": len(group) / len(labeled),
                "revenue": revenue,
                "revenue_share": revenue / total_revenue,
            }

            for feature in FEATURE_COLUMNS:
                row[f"{feature.lower()}_mean"] = group[feature].mean()
                row[f"{feature.lower()}_median"] = group[feature].median()
                row[f"{feature.lower()}_std"] = group[feature].std(ddof=1)
                row[f"{feature.lower()}_z"] = z[feature]

            row["strategy"] = SEGMENT_STRATEGY[row["segment"]]
            rows.append(row)

    return pd.DataFrame(rows)


def separation_scores(X, labels):
    """
    Mức độ phân biệt của từng đặc trưng:
        delta_j = (max_k mean_kj - min_k mean_kj) / sigma_j
    với sigma_j là độ lệch chuẩn của toàn bộ dữ liệu. Các điểm nhiễu không
    tham gia vì nhiễu không phải một cụm.
    """
    mask = labels != NOISE_LABEL
    z_means = cluster_z_means(X[mask], labels[mask])
    sigma = pd.DataFrame(X, columns=list(FEATURE_COLUMNS)).std(ddof=0)

    return (z_means.max() - z_means.min()) / sigma


def build_separation_table(X, labels_by_model):
    """Bảng mức độ phân biệt của cả ba mô hình, kèm giá trị trung bình và nhỏ nhất."""
    rows = []

    for model_name, labels in labels_by_model.items():
        delta = separation_scores(X, labels)
        rows.append({
            "model": model_name,
            **{f"delta_{feature.lower()}": delta[feature] for feature in FEATURE_COLUMNS},
            "delta_mean": delta.mean(),
            "delta_min": delta.min(),
        })

    return pd.DataFrame(rows)


def cluster_segments(X, labels):
    """Nhãn nghiệp vụ của từng cụm, suy ra từ z-score trung bình của cụm đó."""
    z_means = cluster_z_means(X, labels)

    return {
        cluster: assign_segment(*z[list(FEATURE_COLUMNS)], cluster=cluster)
        for cluster, z in z_means.iterrows()
    }


def _cluster_style(X, labels):
    """
    Trả về danh sách (nhãn cụm, tên hiển thị, màu) theo thứ tự phân khúc dùng
    chung cho cả ba mô hình, để chú giải của ba biểu đồ đọc được như nhau.
    """
    segments = cluster_segments(X, labels)
    ordered = sorted(segments, key=lambda cluster: SEGMENT_ORDER.index(segments[cluster]))

    return [
        (cluster,
         f"C{cluster} · {SEGMENT_SHORT[segments[cluster]]}" if cluster != NOISE_LABEL
         else SEGMENT_SHORT[NOISE_SEGMENT],
         SEGMENT_COLORS[segments[cluster]])
        for cluster in ordered
    ]


def _style_axes(ax):
    """Trục và lưới lùi về sau, để phần dữ liệu nổi lên trước."""
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    ax.set_axisbelow(True)

    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID_COLOR)

    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)


def plot_rfm_bars(X, labels_by_model, output_path):
    """
    Bar chart so sánh giá trị RFM trung bình giữa các cụm.
    Ba đặc trưng dùng chung một trục z-score nên so sánh được trực tiếp với nhau,
    không cần trục thứ hai.
    """
    figure, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True, facecolor=SURFACE)

    for ax, model_name in zip(axes, MODEL_ORDER):
        labels = labels_by_model[model_name]
        z_means = cluster_z_means(X, labels)
        styles = _cluster_style(X, labels)

        positions = np.arange(len(FEATURE_COLUMNS))
        width = 0.8 / len(styles)

        for index, (cluster, name, color) in enumerate(styles):
            offset = (index - (len(styles) - 1) / 2) * width
            values = z_means.loc[cluster, list(FEATURE_COLUMNS)].values
            bars = ax.bar(positions + offset, values, width * 0.92, label=name,
                          color=color, linewidth=0)

            for bar, value in zip(bars, values):
                ax.annotate(f"{value:.2f}", (bar.get_x() + bar.get_width() / 2, value),
                            xytext=(0, 3 if value >= 0 else -11), textcoords="offset points",
                            ha="center", fontsize=7.5, color=TEXT_SECONDARY)

        ax.axhline(0, color=TEXT_SECONDARY, linewidth=0.8)
        ax.set_xticks(positions, list(FEATURE_COLUMNS))
        ax.set_title(model_name, fontsize=11, color=TEXT_PRIMARY, pad=10)
        ax.legend(frameon=False, fontsize=8.5, labelcolor=TEXT_SECONDARY, ncols=2)
        _style_axes(ax)

    axes[0].set_ylabel("Giá trị trung bình (z-score)", fontsize=9.5, color=TEXT_SECONDARY)
    figure.suptitle("Giá trị RFM trung bình của từng cụm — Recency càng cao càng lâu chưa mua",
                    fontsize=12.5, color=TEXT_PRIMARY, y=1.0)
    figure.tight_layout()

    return _save_figure(figure, output_path)


def plot_radar(X, labels_by_model, output_path):
    """
    Radar chart biểu diễn hồ sơ cụm. Recency được đảo chiều để cả ba trục cùng
    hướng "xa tâm là tốt hơn", nên diện tích đa giác đọc được như mức độ giá trị
    của phân khúc. Ba đặc trưng dùng chung một thang chuẩn hóa từ z-score của
    toàn bộ chín cụm nên ba biểu đồ so sánh được với nhau.
    """
    all_z = pd.concat([cluster_z_means(X, labels) for labels in labels_by_model.values()])
    signed = all_z.copy()
    signed["Recency"] = -signed["Recency"]
    lower, upper = signed.min().min(), signed.max().max()

    angles = np.linspace(0, 2 * np.pi, len(FEATURE_COLUMNS), endpoint=False).tolist()
    angles += angles[:1]
    axis_labels = ["Recency\n(đảo chiều)", "Frequency", "Monetary"]

    figure, axes = plt.subplots(1, 3, figsize=(15, 5.4), facecolor=SURFACE,
                                subplot_kw={"projection": "polar"})

    for ax, model_name in zip(axes, MODEL_ORDER):
        labels = labels_by_model[model_name]
        z_means = cluster_z_means(X, labels)

        for cluster, name, color in _cluster_style(X, labels):
            z = z_means.loc[cluster, list(FEATURE_COLUMNS)].copy()
            z["Recency"] = -z["Recency"]
            values = ((z - lower) / (upper - lower)).tolist()
            values += values[:1]

            is_noise = cluster == NOISE_LABEL
            ax.plot(angles, values, color=color, linewidth=2, label=name,
                    linestyle="--" if is_noise else "-")
            ax.fill(angles, values, color=color, alpha=0.10)

        ax.set_facecolor(SURFACE)
        ax.set_xticks(angles[:-1], axis_labels, fontsize=9, color=TEXT_SECONDARY)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.25, 0.50, 0.75], ["", "", ""])
        ax.tick_params(colors=TEXT_SECONDARY)
        ax.grid(color=GRID_COLOR, linewidth=0.8)
        ax.spines["polar"].set_color(GRID_COLOR)
        ax.set_title(model_name, fontsize=11, color=TEXT_PRIMARY, pad=22)
        ax.legend(frameon=False, fontsize=8.5, labelcolor=TEXT_SECONDARY,
                  loc="upper right", bbox_to_anchor=(1.22, 1.14))

    figure.suptitle("Hồ sơ cụm trên ba trục RFM — xa tâm là phân khúc có giá trị hơn",
                    fontsize=12.5, color=TEXT_PRIMARY, y=1.0)
    figure.tight_layout()

    return _save_figure(figure, output_path)


def plot_pca_scatter(X, labels_by_model, output_path):
    """
    Chiếu dữ liệu RFM đã chuẩn hóa xuống hai thành phần chính và tô màu theo cụm,
    để quan sát trực tiếp mức độ tách biệt giữa các nhóm.
    """
    pca = PCA(n_components=2, random_state=42)
    coordinates = pca.fit_transform(X)
    variance = pca.explained_variance_ratio_

    figure, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharex=True, sharey=True,
                                facecolor=SURFACE)

    for ax, model_name in zip(axes, MODEL_ORDER):
        labels = labels_by_model[model_name]

        for cluster, name, color in _cluster_style(X, labels):
            mask = labels == cluster
            is_noise = cluster == NOISE_LABEL
            ax.scatter(coordinates[mask, 0], coordinates[mask, 1], s=4 if is_noise else 6,
                       color=color, alpha=0.30 if is_noise else 0.55, linewidths=0,
                       label=f"{name} ({mask.sum()})")

        ax.set_title(model_name, fontsize=11, color=TEXT_PRIMARY, pad=10)
        ax.set_xlabel(f"PC1 ({variance[0]:.1%} phương sai)", fontsize=9.5, color=TEXT_SECONDARY)
        ax.legend(frameon=False, fontsize=8.5, labelcolor=TEXT_SECONDARY,
                  markerscale=3, loc="upper left")
        _style_axes(ax)
        ax.grid(color=GRID_COLOR, linewidth=0.8)

    axes[0].set_ylabel(f"PC2 ({variance[1]:.1%} phương sai)", fontsize=9.5, color=TEXT_SECONDARY)
    figure.suptitle("Phân bố khách hàng trên hai thành phần chính, tô màu theo cụm",
                    fontsize=12.5, color=TEXT_PRIMARY, y=1.0)
    figure.tight_layout()

    return _save_figure(figure, output_path)


def _save_figure(figure, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    figure.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    plt.close(figure)
    print(f"Saved figure to {output_path}")

    return output_path


def save_profiles(profiles, output_path):
    """Lưu bảng hồ sơ cụm của cả ba mô hình."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    profiles.to_csv(output_path, index=False)
    print(f"Saved {len(profiles)} cluster profiles to {output_path}")

    return profiles


if __name__ == "__main__":
    rfm_raw = pd.read_csv("data/processed/rfm_table.csv")
    scaled = pd.read_csv("data/processed/rfm_scaled.csv")
    X = scaled[list(FEATURE_COLUMNS)].values

    if not (rfm_raw["CustomerID"].values == scaled["CustomerID"].values).all():
        raise ValueError("rfm_table.csv and rfm_scaled.csv are not aligned by CustomerID")

    configs = load_best_configs("outputs/results/clustering_experiments.csv")

    print("\nTraining best configuration of each model on the full dataset:")
    labels_by_model = fit_best_models(X, configs)

    labeled = build_labeled_customers(rfm_raw, labels_by_model)
    labeled.to_csv("data/processed/customer_clusters_all_models.csv", index=False)
    print(f"Saved {len(labeled)} labeled customers to "
          f"data/processed/customer_clusters_all_models.csv")

    profiles = build_cluster_profiles(labeled, X, labels_by_model)
    save_profiles(profiles, "data/processed/cluster_profiles.csv")

    separation = build_separation_table(X, labels_by_model)
    separation.to_csv("outputs/results/cluster_separation.csv", index=False)
    print(f"Saved separation scores to outputs/results/cluster_separation.csv")

    plot_rfm_bars(X, labels_by_model, "outputs/figures/cluster_rfm_bars.png")
    plot_radar(X, labels_by_model, "outputs/figures/cluster_radar.png")
    plot_pca_scatter(X, labels_by_model, "outputs/figures/cluster_pca.png")

    print("\n" + separation.round(3).to_string(index=False))
    print("\n" + profiles[["model", "cluster", "segment", "n_customers", "share",
                           "revenue_share"]].to_string(index=False))
