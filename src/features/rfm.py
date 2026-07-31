import pandas as pd
import numpy as np
import os

CUSTOMER_COLUMNS = ("CustomerID", "Customer ID")
INVOICE_DATE_COLUMNS = ("InvoiceDate",)

def _first_existing_column(df, candidates, required=True):
    for column in candidates:
        if column in df.columns:
            return column
    if required:
        expected = ", ".join(candidates)
        raise KeyError(f"Missing required column. Expected one of: {expected}")
    return None

def load_data(filepath):
    print(f"Loading data from {filepath}...")
    df = pd.read_csv(filepath)
    invoice_date_col = _first_existing_column(df, INVOICE_DATE_COLUMNS)
    df[invoice_date_col] = pd.to_datetime(df[invoice_date_col], errors='coerce')
    return df

def remove_buy_cancel_pairs(df):
    """
    Xác định và loại bỏ các bản gốc của hóa đơn hủy (cặp mua-hủy hoàn toàn).
    Giả định: Dòng hủy có IsCancelled=True, Quantity < 0.
    """
    customer_col = _first_existing_column(df, CUSTOMER_COLUMNS)
    invoice_date_col = _first_existing_column(df, INVOICE_DATE_COLUMNS)
    
    # 1. Tìm các dòng hủy hợp lệ để xét
    cancelled = df[(df['IsCancelled'] == True) & (df['HasCustomerID'] == True) & (df['Quantity'] < 0)].copy()
    cancelled['AbsQuantity'] = cancelled['Quantity'].abs()
    
    # 2. Tìm các dòng mua hợp lệ
    valid_purchases = df[(df['IsCancelled'] == False) & (df['HasCustomerID'] == True) & (df['Quantity'] > 0)].copy()
    
    # Reset index để giữ lại index gốc nhằm xóa sau này
    cancelled = cancelled.reset_index()
    valid_purchases = valid_purchases.reset_index()
    
    # Merge based on Customer, StockCode, and Quantity
    merged = pd.merge(
        cancelled[['index', customer_col, 'StockCode', 'AbsQuantity', invoice_date_col]],
        valid_purchases[['index', customer_col, 'StockCode', 'Quantity', invoice_date_col]],
        left_on=[customer_col, 'StockCode', 'AbsQuantity'],
        right_on=[customer_col, 'StockCode', 'Quantity'],
        suffixes=('_cancel', '_buy')
    )
    
    # Filter where buy date is <= cancel date
    merged = merged[merged[f'{invoice_date_col}_buy'] <= merged[f'{invoice_date_col}_cancel']]
    
    # Sort and group to get the closest buy to the cancel date
    merged = merged.sort_values(f'{invoice_date_col}_buy', ascending=False)
    merged = merged.drop_duplicates(subset=['index_cancel'], keep='first')
    
    # Lấy các index cần xóa (cả hủy và mua)
    indices_to_drop = set(cancelled['index']) | set(merged['index_buy'])
    
    print(f"[remove_buy_cancel_pairs] Removed {len(indices_to_drop)} rows (buy-cancel pairs).")
    return df.drop(index=list(indices_to_drop))

def filter_valid_transactions(df):
    """
    Áp dụng các Business Rules để lọc tập dữ liệu sẵn sàng tính RFM.
    """
    print(f"Start filtering. Initial rows: {len(df)}")
    
    # 1. Loại cặp mua - hủy
    df = remove_buy_cancel_pairs(df)
    
    # 2. Loại theo các cờ
    valid_mask = (
        (df['IsCancelled'] == False) &
        (df['HasCustomerID'] == True) &
        (df['IsServiceCode'] == False) &
        (df['PriceAnomaly'] == False)
    )
    df = df[valid_mask]
    
    print(f"Finished filtering. Valid rows remaining: {len(df)}")
    return df

def calculate_total_price(df):
    if 'TotalPrice' not in df.columns:
        df['TotalPrice'] = df['Quantity'] * df['Price']
    return df

def calculate_rfm(df, snapshot_date='2011-12-10'):
    customer_col = _first_existing_column(df, CUSTOMER_COLUMNS)
    invoice_date_col = _first_existing_column(df, INVOICE_DATE_COLUMNS)
    
    snapshot = pd.to_datetime(snapshot_date)
    
    print("Calculating R, F, M...")
    rfm = df.groupby(customer_col).agg(
        Recency=(invoice_date_col, lambda dates: (snapshot - dates.max()).days),
        Frequency=('Invoice', 'nunique'),
        Monetary=('TotalPrice', 'sum')
    ).reset_index()
    
    # Đổi tên cột customer về CustomerID cho chuẩn đầu ra
    rfm.rename(columns={customer_col: 'CustomerID'}, inplace=True)
    
    return rfm

def build_rfm_table(input_path, output_path):
    df = load_data(input_path)
    df = filter_valid_transactions(df)
    df = calculate_total_price(df)
    rfm_table = calculate_rfm(df)
    
    print(f"Saving RFM table with {len(rfm_table)} customers to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    rfm_table.to_csv(output_path, index=False)
    return rfm_table

if __name__ == '__main__':
    input_file = 'data/processed/cleaned_transactions.csv'
    output_file = 'data/processed/rfm_table.csv'
    build_rfm_table(input_file, output_file)
