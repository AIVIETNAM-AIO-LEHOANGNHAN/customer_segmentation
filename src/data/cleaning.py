import pandas as pd
pd.options.mode.chained_assignment = None
import logging

INVOICE_COLUMNS = ("InvoiceNo", "Invoice")
PRICE_COLUMNS = ("UnitPrice", "Price")
CUSTOMER_COLUMNS = ("CustomerID", "Customer ID")
QUANTITY_COLUMNS = ("Quantity",)
INVOICE_DATE_COLUMNS = ("InvoiceDate",)
STOCK_CODE_COLUMNS = ("StockCode",)


def _first_existing_column(df, candidates, required=True):
    for column in candidates:
        if column in df.columns:
            return column
    if required:
        expected = ", ".join(candidates)
        raise KeyError(f"Missing required column. Expected one of: {expected}")
    return None


def remove_duplicates(df):
    initial_len = len(df)
    df = df.drop_duplicates()
    final_len = len(df)
    print(f"[remove_duplicates] Removed {initial_len - final_len} duplicate rows.")
    return df

def fix_dtypes(df):
    print("[fix_dtypes] Fixing data types...")
    # InvoiceDate to datetime
    invoice_date_col = _first_existing_column(df, INVOICE_DATE_COLUMNS)
    df[invoice_date_col] = pd.to_datetime(df[invoice_date_col], errors='coerce')
    
    # Quantity to numeric (QA-02)
    quantity_col = _first_existing_column(df, QUANTITY_COLUMNS, required=False)
    if quantity_col:
        df[quantity_col] = pd.to_numeric(df[quantity_col], errors='coerce')

    price_col = _first_existing_column(df, PRICE_COLUMNS, required=False)
    if price_col:
        df[price_col] = pd.to_numeric(df[price_col], errors='coerce')
    
    # Customer ID to string (keeping nan as missing) (QA-04)
    customer_col = _first_existing_column(df, CUSTOMER_COLUMNS, required=False)
    if customer_col:
        df[customer_col] = df[customer_col].astype(str).str.replace(r'\.0$', '', regex=True)
        df[customer_col] = df[customer_col].replace(['nan', 'None', '<NA>'], pd.NA)
    
    return df

def flag_invalid_date(df):
    # (QA-03) Flag invalid dates instead of dropping them
    invoice_date_col = _first_existing_column(df, INVOICE_DATE_COLUMNS, required=False)
    if invoice_date_col:
        df['HasInvalidDate'] = df[invoice_date_col].isna()
        print(f"[flag_invalid_date] Flagged {df['HasInvalidDate'].sum()} rows with invalid InvoiceDate.")
    return df

def flag_cancelled(df):
    invoice_col = _first_existing_column(df, INVOICE_COLUMNS)
    df['IsCancelled'] = df[invoice_col].astype(str).str.startswith('C')
    print(f"[flag_cancelled] Flagged {df['IsCancelled'].sum()} cancelled invoices.")
    return df

def flag_missing_customer(df):
    customer_col = _first_existing_column(df, CUSTOMER_COLUMNS)
    df['HasCustomerID'] = df[customer_col].notna()
    print(f"[flag_missing_customer] Flagged {(~df['HasCustomerID']).sum()} rows missing Customer ID.")
    return df

def flag_special_stockcode(df):
    special_codes = ['POST', 'DOT', 'M', 'BANK CHARGES', 'C2', 'ADJUST', 'CRUK', 'D', 'S', 'AMAZONFEE']
    stock_code_col = _first_existing_column(df, STOCK_CODE_COLUMNS)
    df['IsServiceCode'] = df[stock_code_col].astype(str).str.upper().isin(special_codes)
    print(f"[flag_special_stockcode] Flagged {df['IsServiceCode'].sum()} rows with special StockCodes.")
    return df

def flag_price_anomaly(df):
    price_col = _first_existing_column(df, PRICE_COLUMNS)
    df['PriceAnomaly'] = df[price_col] <= 0
    print(f"[flag_price_anomaly] Flagged {df['PriceAnomaly'].sum()} rows with Price <= 0.")
    return df

def calc_total_price(df):
    quantity_col = _first_existing_column(df, QUANTITY_COLUMNS, required=False)
    price_col = _first_existing_column(df, PRICE_COLUMNS, required=False)
    if quantity_col and price_col:
        df['TotalPrice'] = df[quantity_col] * df[price_col]
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
