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
    
    # Tập hợp index cần bị loại (cả dòng hủy và dòng mua gốc)
    indices_to_drop = set()
    
    # 1. Tìm các dòng hủy hợp lệ để xét
    cancelled = df[(df['IsCancelled'] == True) & (df['HasCustomerID'] == True) & (df['Quantity'] < 0)]
    
    # Đánh dấu xóa sẵn các dòng hủy
    indices_to_drop.update(cancelled.index)
    
    # Tối ưu hóa việc tìm kiếm: Nhóm các giao dịch hợp lệ theo Customer và StockCode
    valid_purchases = df[(df['IsCancelled'] == False) & (df['HasCustomerID'] == True) & (df['Quantity'] > 0)]
    
    for idx, row in cancelled.iterrows():
        customer = row[customer_col]
        stock = row['StockCode']
        qty = abs(row['Quantity'])
        date = row[invoice_date_col]
        
        # Lọc nhanh
        candidates = valid_purchases[
            (valid_purchases[customer_col] == customer) &
            (valid_purchases['StockCode'] == stock) &
            (valid_purchases['Quantity'] == qty) &
            (valid_purchases[invoice_date_col] <= date)
        ]
        
        # Sắp xếp theo ngày giảm dần (tìm dòng gốc gần nhất)
        candidates = candidates.sort_values(by=invoice_date_col, ascending=False)
        
        for cand_idx in candidates.index:
            if cand_idx not in indices_to_drop:
                indices_to_drop.add(cand_idx)
                break
                
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
