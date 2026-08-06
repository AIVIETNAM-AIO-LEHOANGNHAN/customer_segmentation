import pandas as pd
from pandas.testing import assert_frame_equal

import sys
from pathlib import Path

### project root
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.features.rfm import (
    load_data,
    filter_valid_transactions,
    calculate_total_price,
    calculate_rfm,
)

DATA_PATH = "data/processed/cleaned_transactions.csv"

### Chạy module nhiều lần với cùng dữ liệu đầu vào.

def build_rfm():
    """Chạy toàn bộ pipeline tạo RFM"""
    df = load_data(DATA_PATH)
    df = filter_valid_transactions(df)
    df = calculate_total_price(df)

    rfm = calculate_rfm(df)

    # Sắp xếp để so sánh
    rfm = rfm.sort_values("CustomerID").reset_index(drop=True)
    return rfm

### So sánh kết quả giữa các lần chạy.

def test_rfm_consistency_same_input():
    """
    Chạy nhiều lần với cùng dữ liệu.
    Kết quả phải giống hệt nhau.
    """
    rfm1 = build_rfm()
    rfm2 = build_rfm()

    assert_frame_equal(rfm1, rfm2)

### Đảm bảo kết quả luôn giống nhau.

def test_rfm_consistency_shuffle_input():
    """
    Thay đổi thứ tự dữ liệu đầu vào.
    Kết quả RFM không được thay đổi.
    """

    df = load_data(DATA_PATH)

    # Shuffle dữ liệu
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    df = filter_valid_transactions(df)
    df = calculate_total_price(df)

    rfm_shuffle = (
        calculate_rfm(df)
        .sort_values("CustomerID")
        .reset_index(drop=True)
    )

    rfm_original = build_rfm()

    assert_frame_equal(rfm_original, rfm_shuffle)