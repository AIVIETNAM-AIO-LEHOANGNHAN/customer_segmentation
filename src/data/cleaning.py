import pandas as pd
pd.options.mode.chained_assignment = None
import logging

def remove_duplicates(df):
    initial_len = len(df)
    df = df.drop_duplicates()
    final_len = len(df)
    print(f"[remove_duplicates] Removed {initial_len - final_len} duplicate rows.")
    return df

def fix_dtypes(df):
    print("[fix_dtypes] Fixing data types...")
    # InvoiceDate to datetime
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
    
    # Quantity to numeric (QA-02)
    if 'Quantity' in df.columns:
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    
    # Customer ID to string (keeping nan as missing) (QA-04)
    if 'Customer ID' in df.columns:
        df['Customer ID'] = df['Customer ID'].astype(str).str.replace(r'\.0$', '', regex=True)
        df['Customer ID'] = df['Customer ID'].replace('nan', pd.NA)
    
    return df

def flag_invalid_date(df):
    # (QA-03) Flag invalid dates instead of dropping them
    if 'InvoiceDate' in df.columns:
        df['HasInvalidDate'] = df['InvoiceDate'].isna()
        print(f"[flag_invalid_date] Flagged {df['HasInvalidDate'].sum()} rows with invalid InvoiceDate.")
    return df

def flag_cancelled(df):
    df['IsCancelled'] = df['Invoice'].astype(str).str.startswith('C')
    print(f"[flag_cancelled] Flagged {df['IsCancelled'].sum()} cancelled invoices.")
    return df

def flag_missing_customer(df):
    df['HasCustomerID'] = df['Customer ID'].notna()
    print(f"[flag_missing_customer] Flagged {(~df['HasCustomerID']).sum()} rows missing Customer ID.")
    return df

def flag_special_stockcode(df):
    special_codes = ['POST', 'DOT', 'M', 'BANK CHARGES', 'C2', 'ADJUST', 'CRUK', 'D', 'S', 'AMAZONFEE']
    df['IsServiceCode'] = df['StockCode'].astype(str).str.upper().isin(special_codes)
    print(f"[flag_special_stockcode] Flagged {df['IsServiceCode'].sum()} rows with special StockCodes.")
    return df

def flag_price_anomaly(df):
    df['PriceAnomaly'] = df['Price'] <= 0
    print(f"[flag_price_anomaly] Flagged {df['PriceAnomaly'].sum()} rows with Price <= 0.")
    return df

def calc_total_price(df):
    if 'Quantity' in df.columns and 'Price' in df.columns:
        df['TotalPrice'] = df['Quantity'] * df['Price']
    return df

def clean_pipeline(df):
    print(f"--- Starting cleaning pipeline. Initial shape: {df.shape} ---")
    df = remove_duplicates(df)
    df = fix_dtypes(df)
    df = flag_invalid_date(df)
    df = flag_cancelled(df)
    df = flag_missing_customer(df)
    df = flag_special_stockcode(df)
    df = flag_price_anomaly(df)
    df = calc_total_price(df)
    print(f"--- Finished cleaning pipeline. Final shape: {df.shape} ---")
    return df

if __name__ == '__main__':
    import os
    input_path = 'data/raw/online_retail_II.csv'
    output_path = 'data/processed/cleaned_transactions.csv'
    
    print(f"Loading data from {input_path}")
    df = pd.read_csv(input_path, encoding='latin1')
    
    df_cleaned = clean_pipeline(df)
    
    print(f"Saving cleaned data to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_cleaned.to_csv(output_path, index=False)
    print("Cleaning complete. Data saved successfully.")
