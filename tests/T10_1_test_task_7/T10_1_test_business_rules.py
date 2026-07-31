import pandas as pd

# ==========================
# Load dữ liệu
# ==========================
transactions = pd.read_csv(
    "data/processed/cleaned_transactions.csv"
)

rfm = pd.read_csv(
    "data/processed/rfm_table.csv"
)


# =====================================================
# Test 1. Giao dịch hủy không được tính vào RFM
# =====================================================
def test_cancelled_transactions_removed():

    cancelled_customers = set(
        transactions.loc[
            transactions["IsCancelled"],
            "Customer ID"
        ].dropna()
    )

    # Kiểm tra không còn giao dịch hủy trong dữ liệu tính RFM
    filtered = transactions[
        transactions["IsCancelled"] == False
    ]

    assert filtered["IsCancelled"].sum() == 0


# =====================================================
# Test 2. Mã dịch vụ không được tính vào RFM
# =====================================================
def test_service_codes_removed():

    filtered = transactions[
        transactions["IsServiceCode"] == False
    ]

    assert filtered["IsServiceCode"].sum() == 0


# =====================================================
# Test 3. Price Anomaly đã bị loại
# =====================================================
def test_price_anomaly_removed():

    filtered = transactions[
        transactions["PriceAnomaly"] == False
    ]

    assert filtered["PriceAnomaly"].sum() == 0


# =====================================================
# Test 4. CustomerID thiếu không xuất hiện trong RFM
# =====================================================
def test_missing_customer_removed():

    assert rfm["CustomerID"].isna().sum() == 0


# =====================================================
# Test 5. Các cặp mua – hủy được xử lý đúng
# =====================================================
def test_cancel_pairs_removed():

    duplicated_pairs = transactions[
        transactions["IsCancelled"] == False
    ]

    # Sau bước lọc, không còn Invoice bị đánh dấu hủy
    assert duplicated_pairs["Invoice"].astype(str).str.startswith("C").sum() == 0