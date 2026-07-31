import pandas as pd

DATA_PATH = "data/processed/cleaned_transactions.csv"

df = pd.read_csv(DATA_PATH, parse_dates=["InvoiceDate"])


# ==========================================
# 1. Kiểm tra dữ liệu đầu vào đúng schema
# ==========================================
def test_schema():

    expected_columns = [
        "Invoice",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "Price",
        "Customer ID",
        "Country",
        "IsCancelled",
        "HasCustomerID",
        "IsServiceCode",
        "PriceAnomaly",
        "TotalPrice",
    ]

    assert set(df.columns) == set(expected_columns)


# ==========================================
# 2. Kiểm tra các cột bắt buộc tồn tại
# ==========================================
def test_required_columns():

    required_columns = [
        "Invoice",
        "StockCode",
        "Quantity",
        "InvoiceDate",
        "Price",
        "Customer ID"
    ]

    for col in required_columns:
        assert col in df.columns


# ==========================================
# 3. Kiểm tra kiểu dữ liệu
# ==========================================
def test_data_types():

    assert pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"])
    assert pd.api.types.is_numeric_dtype(df["Quantity"])
    assert pd.api.types.is_numeric_dtype(df["Price"])
    assert pd.api.types.is_numeric_dtype(df["TotalPrice"])
    assert pd.api.types.is_bool_dtype(df["IsCancelled"])
    assert pd.api.types.is_bool_dtype(df["HasCustomerID"])
    assert pd.api.types.is_bool_dtype(df["IsServiceCode"])
    assert pd.api.types.is_bool_dtype(df["PriceAnomaly"])


# ==========================================
# 4. Kiểm tra dữ liệu đã làm sạch theo Business Rules
# ==========================================
def test_business_rules():

    # Không còn duplicate
    assert df.duplicated().sum() == 0

    # InvoiceDate hợp lệ
    assert df["InvoiceDate"].isna().sum() == 0

    # Cờ IsCancelled đúng
    expected_cancel = df["Invoice"].astype(str).str.startswith("C")
    assert (expected_cancel == df["IsCancelled"]).all()

    # Cờ HasCustomerID đúng
    expected_customer = df["Customer ID"].notna()
    assert (expected_customer == df["HasCustomerID"]).all()

    # Cờ PriceAnomaly đúng
    expected_price = df["Price"] <= 0
    assert (expected_price == df["PriceAnomaly"]).all()