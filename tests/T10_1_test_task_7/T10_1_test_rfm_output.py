import pandas as pd

# ==========================
# Load dữ liệu RFM
# ==========================

RFM_PATH = "data/processed/rfm_table.csv"

rfm = pd.read_csv(RFM_PATH)


# ======================================================
# Test 1 - Mỗi khách hàng chỉ xuất hiện một lần
# ======================================================

def test_customer_unique():

    assert rfm["CustomerID"].is_unique, \
        "Có CustomerID xuất hiện nhiều hơn một lần."


# ======================================================
# Test 2 - Không còn giá trị thiếu
# ======================================================

def test_no_missing_values():

    assert rfm.isnull().sum().sum() == 0, \
        "RFM còn tồn tại giá trị NULL."


# ======================================================
# Test 3 - Recency >= 0
# ======================================================

def test_recency_positive():

    assert (rfm["Recency"] >= 0).all(), \
        "Có Recency âm."


# ======================================================
# Test 4 - Frequency > 0
# ======================================================

def test_frequency_positive():

    assert (rfm["Frequency"] > 0).all(), \
        "Có Frequency <= 0."


# ======================================================
# Test 5 - Monetary > 0
# ======================================================

def test_monetary_positive():

    assert (rfm["Monetary"] > 0).all(), \
        "Có Monetary <= 0."


# ======================================================
# Test 6 - Số lượng khách hàng đúng kỳ vọng
# ======================================================

EXPECTED_CUSTOMERS = 4333

def test_number_of_customers():

    assert len(rfm) == EXPECTED_CUSTOMERS, \
        f"Số khách hàng không đúng. Kỳ vọng {EXPECTED_CUSTOMERS}, thực tế {len(rfm)}."