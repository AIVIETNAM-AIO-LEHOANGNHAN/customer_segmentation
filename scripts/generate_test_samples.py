"""Sinh bộ file test lỗi cố ý cho Task 5 (QA/QC) — KAN-12.

Chạy:  python scripts/generate_test_samples.py

Nguyên tắc thiết kế
-------------------
Tất cả 7 file test đều dựng trên cùng một *base sample* 300 dòng được trích
deterministic từ `data/raw/online_retail_II.csv`. Base sample được chọn sao cho
**sạch tuyệt đối** với mọi Business Rule trong `docs/T01_data_specification.md`:

    - Customer ID không null          -> HasCustomerID kỳ vọng toàn True
    - Invoice không bắt đầu bằng 'C'  -> IsCancelled  kỳ vọng toàn False
    - StockCode là mã sản phẩm 5 số   -> IsServiceCode kỳ vọng toàn False
    - Price > 0                       -> PriceAnomaly kỳ vọng toàn False
    - Không có dòng trùng lặp         -> remove_duplicates kỳ vọng giữ nguyên

Nhờ vậy mỗi file test chỉ chứa **đúng một loại lỗi được tiêm vào**, với số
lượng biết trước chính xác — kết quả thực tế lệch bao nhiêu là do module làm
sạch, không phải do nhiễu của dữ liệu nền.

File được ghi bằng encoding `latin1` để đồng nhất với cách `src/data/cleaning.py`
đọc dữ liệu gốc (`pd.read_csv(..., encoding='latin1')`).
"""

from __future__ import annotations

import os
import sys

import pandas as pd

# Console Windows mặc định là cp1252, không in được tiếng Việt có dấu.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAW_PATH = os.path.join("data", "raw", "online_retail_II.csv")
OUT_DIR = os.path.join("data", "test_samples")
ENCODING = "latin1"

BASE_ROWS = 300


def load_base_sample() -> pd.DataFrame:
    """Trích 300 dòng đầu tiên thoả mãn mọi Business Rule (không có lỗi nào)."""
    raw = pd.read_csv(RAW_PATH, encoding=ENCODING)

    invoice = raw["Invoice"].astype(str)
    stock = raw["StockCode"].astype(str)

    clean_mask = (
        raw["Customer ID"].notna()
        & ~invoice.str.startswith("C")
        & stock.str.fullmatch(r"\d{5}[A-Z]?")
        & (raw["Price"] > 0)
        & (raw["Quantity"] > 0)
        & raw["Description"].notna()
    )

    base = raw[clean_mask].drop_duplicates().head(BASE_ROWS).reset_index(drop=True)

    # Customer ID đọc lên là float64 (17850.0). Ghi ra CSV dưới dạng số nguyên
    # để file test giống hệt định dạng người dùng thật sẽ upload.
    base["Customer ID"] = base["Customer ID"].astype("Int64")

    assert len(base) == BASE_ROWS, f"chỉ trích được {len(base)}/{BASE_ROWS} dòng sạch"
    return base


def write(df: pd.DataFrame, name: str) -> None:
    path = os.path.join(OUT_DIR, name)
    df.to_csv(path, index=False, encoding=ENCODING)
    print(f"  [ok] {path:48} {len(df):4} dòng x {len(df.columns)} cột")


def make_missing_customerid(base: pd.DataFrame) -> pd.DataFrame:
    """BR-03: bỏ trống Customer ID ở 75/300 dòng (25%, đúng tỷ lệ dataset gốc)."""
    df = base.copy()
    df.loc[df.index % 4 == 0, "Customer ID"] = pd.NA
    return df


def make_cancelled_invoice(base: pd.DataFrame) -> pd.DataFrame:
    """BR-01 + BR-02: thêm 20 dòng hóa đơn hủy (Invoice bắt đầu 'C', Quantity âm)."""
    df = base.copy()
    cancelled = base.head(20).copy()
    cancelled["Invoice"] = "C" + cancelled["Invoice"].astype(str)
    cancelled["Quantity"] = -cancelled["Quantity"]
    return pd.concat([df, cancelled], ignore_index=True)


# 12 dòng mã dịch vụ. Cột 'note' chỉ để đọc hiểu, KHÔNG ghi vào file test.
SERVICE_ROWS = [
    ("POST", "POSTAGE"),
    ("POST", "POSTAGE"),
    ("DOT", "DOTCOM POSTAGE"),
    ("DOT", "DOTCOM POSTAGE"),
    ("M", "Manual"),
    ("M", "Manual"),
    ("m", "Manual"),                    # biến thể chữ thường, có thật trong dataset gốc
    ("BANK CHARGES", "Bank Charges"),
    ("BANK CHARGES", "Bank Charges"),
    ("D", "Discount"),                  # có thật trong dataset gốc, chưa có trong list của Task 2
    ("S", "SAMPLES"),                   # nt
    ("AMAZONFEE", "AMAZON FEE"),        # nt
]


def make_service_code(base: pd.DataFrame) -> pd.DataFrame:
    """BR-05: chèn 12 dòng mã dịch vụ (gồm cả các mã ít gặp và biến thể chữ thường)."""
    template = base.iloc[0]
    rows = []
    for i, (code, desc) in enumerate(SERVICE_ROWS):
        row = template.copy()
        row["Invoice"] = str(900000 + i)
        row["StockCode"] = code
        row["Description"] = desc
        row["Quantity"] = 1
        row["Price"] = 18.0
        rows.append(row)
    return pd.concat([base.copy(), pd.DataFrame(rows)], ignore_index=True)


def make_zero_price(base: pd.DataFrame) -> pd.DataFrame:
    """BR-04: đặt Price = 0 cho 15 dòng."""
    df = base.copy()
    df.loc[df.index % 20 == 0, "Price"] = 0.0
    return df


def make_missing_column(base: pd.DataFrame) -> pd.DataFrame:
    """Xoá hẳn cột bắt buộc InvoiceDate -> hệ thống phải báo lỗi rõ ràng, chặn xử lý."""
    return base.copy().drop(columns=["InvoiceDate"])


def make_wrong_dtype(base: pd.DataFrame) -> pd.DataFrame:
    """BR-07 + kiểm tra ép kiểu: text trong Quantity (10 dòng) và InvoiceDate sai (5 dòng)."""
    df = base.copy()
    df["Quantity"] = df["Quantity"].astype(object)
    df.loc[df.index % 30 == 0, "Quantity"] = "abc"          # 10 dòng
    df.loc[df.index % 60 == 5, "InvoiceDate"] = "not-a-date"  # 5 dòng
    return df


def make_duplicate(base: pd.DataFrame) -> pd.DataFrame:
    """BR-06: nhân đôi 50 dòng bất kỳ."""
    return pd.concat([base.copy(), base.head(50).copy()], ignore_index=True)


BUILDERS = {
    "test_missing_customerid.csv": make_missing_customerid,
    "test_cancelled_invoice.csv": make_cancelled_invoice,
    "test_service_code.csv": make_service_code,
    "test_zero_price.csv": make_zero_price,
    "test_missing_column.csv": make_missing_column,
    "test_wrong_dtype.csv": make_wrong_dtype,
    "test_duplicate.csv": make_duplicate,
}


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    base = load_base_sample()
    print(f"Base sample: {len(base)} dòng sạch trích từ {RAW_PATH}\n")

    write(base, "base_sample.csv")
    for name, builder in BUILDERS.items():
        write(builder(base), name)

    print(f"\nHoàn tất: {len(BUILDERS)} file test + 1 base sample tại {OUT_DIR}/")


if __name__ == "__main__":
    main()
