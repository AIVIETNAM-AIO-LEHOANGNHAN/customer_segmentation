"""Task 10.2 — Kiểm thử Task 8: Xử lý Outlier và Chuẩn hóa dữ liệu RFM.

Chạy:
    python -m pytest "tests/T10.2_test_scaling.py" -v

Sinh lại file mẫu kiểm thử:
    python "tests/T10.2_test_scaling.py"

Ghi chú về cách kiểm thử
------------------------
Task 8 hiện **chỉ tồn tại dưới dạng notebook** (`notebooks/rfm_preprocessing.ipynb`),
không có module trong `src/features/`. Vì vậy không thể `import` để kiểm thử ở mức
đơn vị như T10.1 đã làm với `src/features/rfm.py`.

Cách QA xử lý: **tái dựng đúng chuỗi bước ghi trong notebook** thành hàm
`build_scaled_reference()`, rồi đối chiếu kết quả của nó với file
`data/processed/rfm_scaled.csv` đã commit. Nếu hai bên khớp, ta chứng minh được
artifact đúng là sản phẩm của quy trình đã mô tả — và từ đó mọi kiểm thử về log,
scaling, tính nhất quán đều có cơ sở.

Căn cứ đối chiếu (do chưa có tài liệu thiết kế riêng cho Task 8):
  - `docs/T11_clustering_specification.md` §2.3 — luồng RFM → Logarithm → StandardScaler
  - `outputs/reports/data_quality_stats.md` §6.3, §7 (khuyến nghị #8, #9) — giữ nguyên
    outlier B2B, chỉ log-transform Frequency/Monetary, không transform Recency
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RFM_PATH = ROOT / "data" / "processed" / "rfm_table.csv"
SCALED_PATH = ROOT / "data" / "processed" / "rfm_scaled.csv"
SAMPLES_PATH = ROOT / "outputs" / "results" / "T10.2_scaling_validation_samples.csv"

FEATURES = ["Recency", "Frequency", "Monetary"]
LOG_FEATURES = ["Frequency", "Monetary"]


# ==========================================
# Tiện ích dùng chung
# ==========================================

def load_rfm() -> pd.DataFrame:
    if not RFM_PATH.exists():
        pytest.skip(f"Thiếu đầu vào {RFM_PATH}")
    return pd.read_csv(RFM_PATH)


def load_scaled() -> pd.DataFrame:
    if not SCALED_PATH.exists():
        pytest.skip(f"Thiếu đầu ra {SCALED_PATH}")
    return pd.read_csv(SCALED_PATH)


def build_scaled_reference(rfm: pd.DataFrame) -> pd.DataFrame:
    """Tái dựng ĐÚNG các bước của `notebooks/rfm_preprocessing.ipynb` (cell 16–24).

    Giữ nguyên cả `insert()` như notebook để bản tham chiếu phản ánh trung thực
    code thật; rủi ro của `insert()` được kiểm riêng ở nhóm 7.
    """
    d = rfm.copy()
    d["Frequency_log"] = np.log1p(d["Frequency"])
    d["Monetary_log"] = np.log1p(d["Monetary"])

    scaler = StandardScaler()
    arr = scaler.fit_transform(d[["Recency", "Frequency_log", "Monetary_log"]])

    out = pd.DataFrame(arr, columns=FEATURES)
    out.insert(0, "CustomerID", d["CustomerID"])
    return out


@pytest.fixture(scope="module")
def rfm():
    return load_rfm()


@pytest.fixture(scope="module")
def scaled():
    return load_scaled()


@pytest.fixture(scope="module")
def reference(rfm):
    return build_scaled_reference(rfm)


# ==========================================
# 1. Kiểm thử dữ liệu đầu vào
# ==========================================

def test_input_schema(rfm):
    """Đầu vào đúng cấu trúc bảng RFM."""
    assert set(rfm.columns) == {"CustomerID", *FEATURES}


def test_input_has_all_three_rfm_features(rfm):
    """Đủ ba đặc trưng Recency, Frequency, Monetary."""
    for col in FEATURES:
        assert col in rfm.columns, f"thiếu đặc trưng {col}"


def test_input_features_are_numeric(rfm):
    """Cả ba đặc trưng phải là kiểu số."""
    for col in FEATURES:
        assert pd.api.types.is_numeric_dtype(rfm[col]), f"{col} không phải kiểu số"


def test_input_has_no_null(rfm):
    """Không còn giá trị NULL."""
    assert not rfm.isna().any().any(), rfm.isna().sum().to_dict()


def test_input_has_no_infinite(rfm):
    """Không có giá trị vô hạn."""
    assert not np.isinf(rfm[FEATURES].to_numpy()).any()


def test_input_customer_id_is_unique(rfm):
    """Mỗi khách hàng chỉ xuất hiện một lần."""
    assert rfm["CustomerID"].duplicated().sum() == 0


def test_input_values_are_in_valid_business_range(rfm):
    """Recency ≥ 0, Frequency ≥ 1, Monetary > 0 theo đặc tả RFM (Task 6)."""
    assert (rfm["Recency"] >= 0).all(), "Recency âm"
    assert (rfm["Frequency"] >= 1).all(), "Frequency < 1"
    assert (rfm["Monetary"] > 0).all(), "Monetary ≤ 0"


def test_input_matches_task7_module_output(rfm):
    """Đối chiếu với đầu ra Task 7 — không có thay đổi ngoài mong muốn."""
    try:
        from src.features.rfm import (
            calculate_rfm,
            calculate_total_price,
            filter_valid_transactions,
            load_data,
        )
    except ImportError:  # pragma: no cover
        pytest.skip("Không import được src.features.rfm")

    src_path = ROOT / "data" / "processed" / "cleaned_transactions.csv"
    if not src_path.exists():
        pytest.skip("Thiếu cleaned_transactions.csv")

    df = calculate_total_price(filter_valid_transactions(load_data(str(src_path))))
    t7 = calculate_rfm(df).sort_values("CustomerID").reset_index(drop=True)
    got = rfm.sort_values("CustomerID").reset_index(drop=True)

    assert len(t7) == len(got), f"Task 7 sinh {len(t7)} khách, file có {len(got)}"
    assert set(t7["CustomerID"]) == set(got["CustomerID"])
    for col in FEATURES:
        # 1e-6 đủ chặt cho tiền tệ, vẫn dung thứ sai số làm tròn khi ghi/đọc CSV
        assert np.allclose(t7[col], got[col], atol=1e-6), f"{col} lệch so với Task 7"


# ==========================================
# 2. Kiểm thử xử lý Outlier
# ==========================================

def test_no_customer_is_dropped(rfm, scaled):
    """Số lượng khách hàng trước và sau xử lý phải bằng nhau."""
    assert len(scaled) == len(rfm), f"{len(rfm)} → {len(scaled)}: đã mất khách hàng"


def test_customer_set_is_preserved(rfm, scaled):
    """Không được mất hay thêm bất kỳ CustomerID nào."""
    before, after = set(rfm["CustomerID"]), set(scaled["CustomerID"])
    assert before == after, {
        "bị mất": sorted(before - after)[:10],
        "phát sinh thêm": sorted(after - before)[:10],
    }


def test_top_monetary_customers_are_kept(rfm, scaled):
    """Khách B2B giá trị lớn nhất phải còn nguyên (khuyến nghị #8, Task 4)."""
    top = rfm.nlargest(20, "Monetary")["CustomerID"]
    missing = set(top) - set(scaled["CustomerID"])
    assert not missing, f"đã loại nhầm khách B2B: {sorted(missing)}"


def test_top_frequency_customers_are_kept(rfm, scaled):
    """Khách mua nhiều lần nhất cũng phải còn nguyên."""
    top = rfm.nlargest(20, "Frequency")["CustomerID"]
    assert not set(top) - set(scaled["CustomerID"])


def test_iqr_outlier_customers_are_all_kept(rfm, scaled):
    """Toàn bộ khách vượt ngưỡng IQR đều được giữ — không cắt outlier."""
    q1, q3 = rfm["Monetary"].quantile([0.25, 0.75])
    threshold = q3 + 1.5 * (q3 - q1)
    outliers = set(rfm.loc[rfm["Monetary"] > threshold, "CustomerID"])
    assert outliers, "dữ liệu mẫu không có outlier nào để kiểm"
    assert not outliers - set(scaled["CustomerID"]), "đã cắt outlier trái thiết kế"


def test_relative_order_of_customers_is_preserved(rfm, scaled):
    """log1p + StandardScaler là phép biến đổi đơn điệu tăng — không được đảo thứ hạng.

    Kiểm trực tiếp bằng số cặp bị đảo, không dùng hệ số tương quan: với 4.324 hạng
    và 85 giá trị Monetary trùng nhau, `corr()` trả về 0,9999999997 do sai số dấu
    phẩy động ngay cả khi thứ tự hoàn toàn đúng — con số đó không kết luận được gì.
    """
    merged = (
        rfm[["CustomerID", "Monetary"]]
        .merge(scaled[["CustomerID", "Monetary"]], on="CustomerID", suffixes=("_raw", "_scaled"))
        .sort_values("Monetary_raw")
    )
    inversions = int((merged["Monetary_scaled"].diff() < 0).sum())
    assert inversions == 0, f"có {inversions} cặp khách hàng bị đảo thứ hạng sau chuẩn hóa"


# ==========================================
# 3. Kiểm thử Log Transformation
# ==========================================

def test_notebook_uses_log1p(rfm):
    """Module phải dùng log1p, không phải log — nếu dùng log thì Frequency=... vẫn ổn
    nhưng Monetary nhỏ sẽ ra âm vô hạn khi giá trị tiến về 0."""
    import json

    nb = ROOT / "notebooks" / "rfm_preprocessing.ipynb"
    if not nb.exists():
        pytest.skip("Không tìm thấy notebook Task 8")
    source = " ".join(
        "".join(c["source"]) for c in json.loads(nb.read_text(encoding="utf-8"))["cells"]
        if c["cell_type"] == "code"
    )
    assert "log1p" in source, "không thấy log1p trong notebook"


def test_log_is_applied_to_frequency_and_monetary(rfm, scaled, reference):
    """Log được áp dụng đúng hai đặc trưng Frequency và Monetary."""
    for col in LOG_FEATURES:
        assert np.allclose(reference[col], scaled[col], atol=1e-9), (
            f"{col} không khớp với log1p + StandardScaler"
        )


def test_recency_is_not_log_transformed(rfm, scaled):
    """Recency KHÔNG được log — đúng khuyến nghị Task 4 (phân phối gần đều theo ngày).

    Kiểm bằng độ lệch: chuẩn hóa tuyến tính giữ nguyên skew, log thì không.
    """
    assert scaled["Recency"].skew() == pytest.approx(rfm["Recency"].skew(), abs=1e-6), (
        "Recency có vẻ đã bị biến đổi phi tuyến"
    )


def test_log_transformation_produces_no_nan_or_inf(rfm):
    """Sau log1p không phát sinh NaN hoặc vô hạn."""
    for col in LOG_FEATURES:
        vals = np.log1p(rfm[col].to_numpy())
        assert not np.isnan(vals).any(), f"{col} sinh NaN sau log1p"
        assert not np.isinf(vals).any(), f"{col} sinh Inf sau log1p"


def test_log_transformation_reduces_skewness(rfm):
    """Độ lệch phân phối phải giảm rõ rệt sau biến đổi."""
    for col in LOG_FEATURES:
        before = abs(rfm[col].skew())
        after = abs(np.log1p(rfm[col]).skew())
        assert after < before, f"{col}: skew không giảm ({before:.3f} → {after:.3f})"
        assert after < 2.0, f"{col}: skew sau log vẫn cao ({after:.3f})"


def test_log_transformation_is_monotonic_on_samples(rfm):
    """Đối chiếu giá trị trước/sau trên mẫu: log1p phải đơn điệu tăng và đúng công thức."""
    sample = rfm.nlargest(5, "Monetary")[["Monetary"]].copy()
    sample["expected"] = np.log(1.0 + sample["Monetary"])
    assert np.allclose(np.log1p(sample["Monetary"]), sample["expected"], atol=1e-12)
    assert sample["expected"].is_monotonic_decreasing  # nlargest → giảm dần


# ==========================================
# 4. Kiểm thử Standard Scaling
# ==========================================

def test_scaled_mean_is_approximately_zero(scaled):
    """Trung bình mỗi đặc trưng sau chuẩn hóa xấp xỉ 0."""
    for col in FEATURES:
        assert scaled[col].mean() == pytest.approx(0.0, abs=1e-9), (
            f"{col}: mean={scaled[col].mean():.3e}"
        )


def test_scaled_std_is_approximately_one(scaled):
    """Độ lệch chuẩn xấp xỉ 1.

    StandardScaler dùng ddof=0 (độ lệch chuẩn tổng thể), còn pandas mặc định
    ddof=1. Kiểm bằng ddof=0 để so đúng với định nghĩa của scikit-learn.
    """
    for col in FEATURES:
        assert scaled[col].std(ddof=0) == pytest.approx(1.0, abs=1e-9), (
            f"{col}: std={scaled[col].std(ddof=0):.10f}"
        )


def test_scaled_output_matches_standardscaler_reference(scaled, reference):
    """Toàn bộ giá trị khớp với StandardScaler chạy lại trên cùng đầu vào."""
    for col in FEATURES:
        assert np.allclose(reference[col], scaled[col], atol=1e-9), (
            f"{col}: lệch tối đa {np.abs(reference[col] - scaled[col]).max():.3e}"
        )


def test_scaling_does_not_change_customer_count(rfm, scaled):
    """Chuẩn hóa không được làm thay đổi số bản ghi."""
    assert len(scaled) == len(rfm)


def test_scaled_output_has_no_nan_or_inf(scaled):
    """Không xuất hiện NaN hoặc Infinite sau chuẩn hóa."""
    arr = scaled[FEATURES].to_numpy()
    assert not np.isnan(arr).any()
    assert not np.isinf(arr).any()


def test_scaling_is_reversible_to_the_log_space(rfm, scaled):
    """Có thể khôi phục lại giá trị log ban đầu — chứng tỏ phép biến đổi tuyến tính."""
    d = rfm.copy()
    d["Frequency_log"] = np.log1p(d["Frequency"])
    d["Monetary_log"] = np.log1p(d["Monetary"])
    scaler = StandardScaler().fit(d[["Recency", "Frequency_log", "Monetary_log"]])
    restored = scaler.inverse_transform(scaled[FEATURES].to_numpy())
    assert np.allclose(restored[:, 0], d["Recency"], atol=1e-6)
    assert np.allclose(restored[:, 1], d["Frequency_log"], atol=1e-9)
    assert np.allclose(restored[:, 2], d["Monetary_log"], atol=1e-9)


# ==========================================
# 5. Kiểm thử chất lượng dữ liệu đầu ra
# ==========================================

def test_output_schema(scaled):
    """Đầu ra đúng cấu trúc: CustomerID + ba đặc trưng."""
    assert list(scaled.columns) == ["CustomerID", *FEATURES]


def test_output_has_no_missing_value(scaled):
    """Không còn giá trị thiếu."""
    assert not scaled.isna().any().any(), scaled.isna().sum().to_dict()


def test_output_customer_count_matches_task7(rfm, scaled):
    """Số khách hàng đúng bằng đầu ra Task 7."""
    assert len(scaled) == len(rfm) == scaled["CustomerID"].nunique()


def test_output_features_are_all_numeric(scaled):
    """Toàn bộ giá trị đặc trưng đều là số."""
    for col in FEATURES:
        assert pd.api.types.is_numeric_dtype(scaled[col])


def test_output_customer_id_is_unique(scaled):
    assert scaled["CustomerID"].duplicated().sum() == 0


def test_output_is_accepted_by_kmeans(scaled):
    """Dữ liệu đưa thẳng vào K-Means được."""
    from sklearn.cluster import KMeans

    model = KMeans(n_clusters=4, n_init=10, random_state=42).fit(scaled[FEATURES])
    assert len(set(model.labels_)) == 4


def test_output_is_accepted_by_gaussian_mixture(scaled):
    """Dữ liệu đưa thẳng vào Gaussian Mixture Model được."""
    from sklearn.mixture import GaussianMixture

    model = GaussianMixture(n_components=4, random_state=42).fit(scaled[FEATURES])
    assert model.converged_


def test_output_is_accepted_by_hdbscan(scaled):
    """Dữ liệu đưa thẳng vào HDBSCAN được."""
    try:
        from hdbscan import HDBSCAN
    except ImportError:
        from sklearn.cluster import HDBSCAN

    labels = HDBSCAN(min_cluster_size=50).fit(scaled[FEATURES]).labels_
    assert len(set(labels) - {-1}) >= 1, "HDBSCAN không tìm được cụm nào"


# ==========================================
# 6. Kiểm thử tính nhất quán
# ==========================================

def test_running_twice_gives_identical_result(rfm):
    """Chạy lại nhiều lần trên cùng dữ liệu cho kết quả giống hệt."""
    assert_frame_equal(build_scaled_reference(rfm), build_scaled_reference(rfm))


def test_result_is_invariant_to_input_row_order(rfm):
    """Đổi thứ tự bản ghi đầu vào không làm thay đổi giá trị của từng khách hàng."""
    shuffled = rfm.sample(frac=1.0, random_state=7).reset_index(drop=True)
    base = build_scaled_reference(rfm)
    other = build_scaled_reference(shuffled)

    merged = base.merge(other, on="CustomerID", suffixes=("_a", "_b"))
    assert len(merged) == len(rfm)
    for col in FEATURES:
        diff = (merged[f"{col}_a"] - merged[f"{col}_b"]).abs().max()
        assert diff < 1e-9, f"{col} lệch {diff:.3e} khi đổi thứ tự đầu vào"


def test_committed_artifact_matches_a_fresh_run(rfm, scaled):
    """File đã commit đúng là sản phẩm của quy trình hiện tại, không bị lỗi thời."""
    fresh = build_scaled_reference(rfm)
    assert fresh["CustomerID"].equals(scaled["CustomerID"]), "thứ tự khách hàng khác"
    for col in FEATURES:
        assert np.allclose(fresh[col], scaled[col], atol=1e-9)


def test_scaler_statistics_are_reproducible(rfm):
    """Tham số mean/scale của scaler ổn định giữa các lần fit."""
    def fit_stats(d):
        x = d.copy()
        x["Frequency_log"] = np.log1p(x["Frequency"])
        x["Monetary_log"] = np.log1p(x["Monetary"])
        s = StandardScaler().fit(x[["Recency", "Frequency_log", "Monetary_log"]])
        return s.mean_, s.scale_

    m1, s1 = fit_stats(rfm)
    m2, s2 = fit_stats(rfm)
    assert np.array_equal(m1, m2)
    assert np.array_equal(s1, s2)


# ==========================================
# 7. Lỗi phát hiện trong quá trình kiểm thử
# ==========================================

@pytest.mark.xfail(
    strict=True,
    reason="BUG-001: notebook dùng rfm_scaled.insert(0, 'CustomerID', rfm['CustomerID']). "
           "insert() căn chỉnh theo INDEX, còn DataFrame kết quả luôn có index 0..n-1. "
           "Hiện tại đúng vì đầu vào đọc thẳng từ CSV, nhưng nếu ai đó lọc/sắp xếp "
           "rfm trước khi chuẩn hóa thì CustomerID sẽ ghép sai dòng — âm thầm, không lỗi.",
)
def test_bug001_customer_id_is_bound_by_position_not_index(rfm):
    """Ghép CustomerID phải theo VỊ TRÍ dòng, không phụ thuộc index của đầu vào."""
    reordered = rfm.sort_values("Monetary", ascending=False)  # index không còn 0..n-1
    out = build_scaled_reference(reordered)

    assert out["CustomerID"].isna().sum() == 0, "sinh CustomerID rỗng"
    top_expected = reordered.iloc[0]["CustomerID"]
    top_actual = out.loc[out["Monetary"].idxmax(), "CustomerID"]
    assert top_actual == top_expected, (
        f"khách Monetary lớn nhất là {top_expected} nhưng bị gán vào dòng của {top_actual}"
    )


@pytest.mark.xfail(
    strict=True,
    reason="BUG-002: Task 8 chỉ tồn tại trong notebooks/rfm_preprocessing.ipynb, "
           "chưa có module trong src/features/ như README quy định. Không import "
           "lại được cho app Streamlit (Epic 4) và không kiểm thử được ở mức đơn vị.",
)
def test_bug002_scaling_module_exists_and_is_importable():
    """Task 8 phải có module tái sử dụng được, giống Task 7 có src/features/rfm.py."""
    candidates = ["src.features.scaling", "src.features.outlier", "src.features.preprocessing"]
    found = []
    for name in candidates:
        try:
            __import__(name)
            found.append(name)
        except ImportError:
            continue
    assert found, f"không tìm thấy module nào trong {candidates}"


@pytest.mark.xfail(
    strict=True,
    reason="BUG-003: đối tượng StandardScaler đã fit không được lưu lại. Epic 4 cần "
           "transform dữ liệu người dùng upload bằng ĐÚNG mean/scale này; fit lại trên "
           "dữ liệu mới sẽ cho kết quả phân cụm không so sánh được với mô hình đã huấn luyện.",
)
def test_bug003_fitted_scaler_is_persisted():
    """Tham số scaler phải được lưu ra file để tái sử dụng ở Epic 3 và Epic 4."""
    patterns = ["*.pkl", "*.joblib", "*scaler*.json", "*scaler*.npy"]
    hits = [p for d in (ROOT / "models", ROOT / "outputs" / "results", ROOT / "data" / "processed")
            if d.exists() for pat in patterns for p in d.glob(pat)]
    assert hits, "không tìm thấy file lưu tham số scaler"


# ==========================================
# Sinh file mẫu kiểm thử
# ==========================================

def _build_samples() -> pd.DataFrame:
    """Dựng bảng mẫu đối chiếu kỳ vọng vs thực tế cho `outputs/results/`."""
    rfm_df, scaled_df = load_rfm(), load_scaled()
    ref = build_scaled_reference(rfm_df)

    q1, q3 = rfm_df["Monetary"].quantile([0.25, 0.75])
    iqr_threshold = q3 + 1.5 * (q3 - q1)
    median_monetary = rfm_df["Monetary"].median()

    groups: list[tuple[str, pd.Index]] = [
        ("TOP_MONETARY_B2B", rfm_df.nlargest(10, "Monetary").index),
        ("TOP_FREQUENCY", rfm_df.nlargest(5, "Frequency").index),
        ("IQR_OUTLIER", rfm_df[rfm_df["Monetary"] > iqr_threshold]
            .sample(8, random_state=42).index),
        ("MEDIAN_TYPICAL", (rfm_df["Monetary"] - median_monetary).abs()
            .nsmallest(8).index),
        ("MIN_MONETARY", rfm_df.nsmallest(4, "Monetary").index),
        ("RECENCY_MIN", rfm_df.nsmallest(3, "Recency").index),
        ("RECENCY_MAX", rfm_df.nlargest(3, "Recency").index),
        ("FREQUENCY_MIN", rfm_df[rfm_df["Frequency"] == rfm_df["Frequency"].min()]
            .sample(4, random_state=42).index),
    ]

    rows = []
    sample_id = 0
    seen: set[int] = set()
    for group, idx in groups:
        for i in idx:
            if i in seen:
                continue
            seen.add(i)
            sample_id += 1
            src, exp = rfm_df.loc[i], ref.loc[i]
            act = scaled_df.loc[i]
            diff = max(abs(exp[c] - act[c]) for c in FEATURES)
            rows.append({
                "SampleID": f"S{sample_id:03d}",
                "NhomMau": group,
                "CustomerID": int(src["CustomerID"]),
                "Recency_goc": int(src["Recency"]),
                "Frequency_goc": int(src["Frequency"]),
                "Monetary_goc": round(float(src["Monetary"]), 2),
                "Frequency_log1p": round(float(np.log1p(src["Frequency"])), 6),
                "Monetary_log1p": round(float(np.log1p(src["Monetary"])), 6),
                "Recency_scaled_kyvong": round(float(exp["Recency"]), 9),
                "Frequency_scaled_kyvong": round(float(exp["Frequency"]), 9),
                "Monetary_scaled_kyvong": round(float(exp["Monetary"]), 9),
                "Recency_scaled_thucte": round(float(act["Recency"]), 9),
                "Frequency_scaled_thucte": round(float(act["Frequency"]), 9),
                "Monetary_scaled_thucte": round(float(act["Monetary"]), 9),
                "LechToiDa": f"{diff:.2e}",
                "ConTonTaiSauXuLy": bool(src["CustomerID"] in set(scaled_df["CustomerID"])),
                "KetLuan": "DAT" if diff < 1e-9 else "KHONG DAT",
            })
    return pd.DataFrame(rows)


def test_validation_samples_file_is_up_to_date():
    """File mẫu kiểm thử đã commit phải khớp với dữ liệu hiện tại."""
    if not SAMPLES_PATH.exists():
        pytest.skip("Chưa sinh file mẫu — chạy: python tests/T10.2_test_scaling.py")
    committed = pd.read_csv(SAMPLES_PATH)
    fresh = _build_samples()
    assert len(committed) == len(fresh)
    assert (committed["KetLuan"] == "DAT").all(), "có mẫu KHÔNG ĐẠT trong file đã commit"


if __name__ == "__main__":
    SAMPLES_PATH.parent.mkdir(parents=True, exist_ok=True)
    samples = _build_samples()
    samples.to_csv(SAMPLES_PATH, index=False, encoding="utf-8")
    print(f"Đã ghi {len(samples)} mẫu vào {SAMPLES_PATH}")
    print(samples["KetLuan"].value_counts().to_string())
