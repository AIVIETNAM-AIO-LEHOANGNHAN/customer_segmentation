"""Chạy 7 kịch bản lỗi cố ý qua module làm sạch (Task 2) và ghi lại kết quả thực tế.

Chạy:  python scripts/run_qa_scenarios.py

Script này hiện thực **Bước 4** của KAN-12: nạp từng file trong
`data/test_samples/`, đẩy qua `src.data.cleaning.clean_pipeline`, rồi đối chiếu
kết quả thực tế với kỳ vọng lấy từ Business Rules trong
`docs/T01_data_specification.md`.

Đầu ra: bảng đối chiếu in ra console + ghi vào
`outputs/reports/qa_test_results.md` để đính kèm báo cáo chất lượng dữ liệu.
"""

from __future__ import annotations

import os
import sys
import traceback
from contextlib import redirect_stdout
from io import StringIO

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.cleaning import clean_pipeline  # noqa: E402

SAMPLE_DIR = os.path.join("data", "test_samples")
REPORT_PATH = os.path.join("outputs", "reports", "qa_test_results.md")
ENCODING = "latin1"

PASS, FAIL = "ĐẠT", "KHÔNG ĐẠT"


def run_pipeline(path: str):
    """Chạy pipeline, nuốt log của module. Trả về (df | None, log, exception | None)."""
    df = pd.read_csv(path, encoding=ENCODING)
    buf = StringIO()
    try:
        with redirect_stdout(buf):
            return clean_pipeline(df), buf.getvalue(), None
    except Exception as exc:  # noqa: BLE001 - QA cần bắt mọi lỗi để phân loại
        return None, buf.getvalue(), exc


# --- Các hàm kiểm tra: mỗi hàm trả về list[(tiêu chí, kỳ vọng, thực tế, kết luận)] ---


def check_missing_customerid(out, exc):
    if out is None:
        return [("Pipeline chạy được", "không crash", f"crash: {type(exc).__name__}", FAIL)]
    kept = len(out)
    flagged = int((~out["HasCustomerID"]).sum())
    # Khi có null, pandas đọc Customer ID thành float64; astype(str) sinh ra '17850.0'.
    # Đây chính là tình huống của dataset gốc (25% null) nên phải kiểm ở kịch bản này.
    ids = out["Customer ID"].dropna().astype(str)
    corrupted = int(ids.str.endswith(".0").sum())
    return [
        ("Dòng Customer ID null còn tồn tại", "300 dòng", f"{kept} dòng", PASS if kept == 300 else FAIL),
        ("HasCustomerID = False được gắn cờ", "75 dòng", f"{flagged} dòng", PASS if flagged == 75 else FAIL),
        ("Customer ID giữ đúng định dạng mã (vd 17850)", "0 mã bị lệch",
         f"{corrupted}/{len(ids)} mã thành dạng '{ids.iloc[0] if len(ids) else ''}'",
         PASS if corrupted == 0 else FAIL),
    ]


def check_cancelled_invoice(out, exc):
    if out is None:
        return [("Pipeline chạy được", "không crash", f"crash: {type(exc).__name__}", FAIL)]
    kept = len(out)
    flagged = int(out["IsCancelled"].sum())
    neg_kept = int((out["Quantity"] < 0).sum())
    return [
        ("Hóa đơn hủy không bị xoá", "320 dòng", f"{kept} dòng", PASS if kept == 320 else FAIL),
        ("IsCancelled = True được gắn cờ", "20 dòng", f"{flagged} dòng", PASS if flagged == 20 else FAIL),
        ("Quantity âm được giữ lại (BR-02)", "20 dòng", f"{neg_kept} dòng", PASS if neg_kept == 20 else FAIL),
    ]


def check_service_code(out, exc):
    if out is None:
        return [("Pipeline chạy được", "không crash", f"crash: {type(exc).__name__}", FAIL)]
    kept = len(out)
    flagged = int(out["IsServiceCode"].sum())
    missed = sorted(
        out.loc[~out["IsServiceCode"] & out["Invoice"].astype(str).str.startswith("9"), "StockCode"]
        .astype(str)
        .unique()
    )
    return [
        ("Dòng mã dịch vụ không bị xoá", "312 dòng", f"{kept} dòng", PASS if kept == 312 else FAIL),
        ("IsServiceCode = True được gắn cờ", "12 dòng", f"{flagged} dòng", PASS if flagged == 12 else FAIL),
        ("Không sót mã dịch vụ nào", "sót 0 mã", f"sót {len(missed)} mã: {', '.join(missed) or '—'}",
         PASS if not missed else FAIL),
    ]


def check_zero_price(out, exc):
    if out is None:
        return [("Pipeline chạy được", "không crash", f"crash: {type(exc).__name__}", FAIL)]
    kept = len(out)
    flagged = int(out["PriceAnomaly"].sum())
    return [
        ("Dòng Price = 0 không bị xoá", "300 dòng", f"{kept} dòng", PASS if kept == 300 else FAIL),
        ("Được gắn cờ giá bất thường", "15 dòng", f"{flagged} dòng", PASS if flagged == 15 else FAIL),
    ]


def check_missing_column(out, exc):
    if out is not None:
        return [("Chặn xử lý khi thiếu cột bắt buộc", "báo lỗi & dừng",
                 f"vẫn xử lý xong, trả về {len(out)} dòng", FAIL)]
    friendly = isinstance(exc, (ValueError, KeyError)) and "InvoiceDate" in str(exc)
    return [
        ("Chặn xử lý khi thiếu cột bắt buộc", "báo lỗi & dừng",
         f"dừng bằng {type(exc).__name__}", PASS),
        ("Thông báo lỗi rõ ràng cho người dùng", "nêu rõ cột nào thiếu",
         f"{type(exc).__name__}: {str(exc)[:60]}", PASS if friendly else FAIL),
    ]


def check_wrong_dtype(out, exc):
    if out is None:
        return [("Không crash khi gặp sai kiểu dữ liệu", "không crash",
                 f"crash: {type(exc).__name__}: {str(exc)[:50]}", FAIL)]
    qty_numeric = pd.api.types.is_numeric_dtype(out["Quantity"])
    date_dt = pd.api.types.is_datetime64_any_dtype(out["InvoiceDate"])
    lost = 300 - len(out)
    return [
        ("Không crash khi gặp sai kiểu dữ liệu", "không crash", "không crash", PASS),
        ("Quantity sau xử lý là kiểu số", "numeric", str(out["Quantity"].dtype),
         PASS if qty_numeric else FAIL),
        ("InvoiceDate sau xử lý là datetime", "datetime64", str(out["InvoiceDate"].dtype),
         PASS if date_dt else FAIL),
        ("Dòng ngày sai được gắn cờ, không xoá âm thầm", "0 dòng bị xoá không cờ",
         f"{lost} dòng bị xoá, không có cột cờ", PASS if lost == 0 else FAIL),
    ]


def check_duplicate(out, exc):
    if out is None:
        return [("Pipeline chạy được", "không crash", f"crash: {type(exc).__name__}", FAIL)]
    kept = len(out)
    return [
        ("Duplicate bị loại, chỉ giữ 1 bản ghi", "300 dòng", f"{kept} dòng",
         PASS if kept == 300 else FAIL),
    ]


def check_schema_conformance(out, exc):
    """Chạy trên base_sample.csv (dữ liệu hoàn toàn sạch) để soi riêng phần
    tuân thủ schema mục 1.3 — không lẫn với nhiễu của các kịch bản lỗi."""
    if out is None:
        return [("Pipeline chạy được trên dữ liệu sạch", "không crash",
                 f"crash: {type(exc).__name__}", FAIL)]

    has_total = "TotalPrice" in out.columns
    derived = [c for c in ("TotalPrice", "IsCancelled", "HasCustomerID", "IsServiceCode")
               if c in out.columns]
    return [
        ("Không mất dòng nào trên dữ liệu sạch", "300 dòng", f"{len(out)} dòng",
         PASS if len(out) == 300 else FAIL),
        ("Đủ 4 cột phái sinh theo schema mục 1.3", "4 cột", f"{len(derived)} cột: {', '.join(derived)}",
         PASS if len(derived) == 4 else FAIL),
        ("Có cột TotalPrice (Quantity × Price)", "có", "có" if has_total else "thiếu",
         PASS if has_total else FAIL),
        ("InvoiceDate là datetime", "datetime64", str(out["InvoiceDate"].dtype),
         PASS if pd.api.types.is_datetime64_any_dtype(out["InvoiceDate"]) else FAIL),
        ("Price là numeric", "float", str(out["Price"].dtype),
         PASS if pd.api.types.is_numeric_dtype(out["Price"]) else FAIL),
    ]


SCENARIOS = [
    ("base_sample.csv", "Schema mục 1.3 — Dữ liệu sạch", check_schema_conformance),
    ("test_missing_customerid.csv", "BR-03 — CustomerID null", check_missing_customerid),
    ("test_cancelled_invoice.csv", "BR-01/BR-02 — Hóa đơn hủy", check_cancelled_invoice),
    ("test_service_code.csv", "BR-05 — Mã dịch vụ", check_service_code),
    ("test_zero_price.csv", "BR-04 — Giá bằng 0", check_zero_price),
    ("test_missing_column.csv", "Thiếu cột bắt buộc", check_missing_column),
    ("test_wrong_dtype.csv", "BR-07 — Sai kiểu dữ liệu", check_wrong_dtype),
    ("test_duplicate.csv", "BR-06 — Bản ghi trùng lặp", check_duplicate),
]


def main() -> int:
    rows = []
    for filename, rule, checker in SCENARIOS:
        path = os.path.join(SAMPLE_DIR, filename)
        out, _log, exc = run_pipeline(path)
        for criterion, expected, actual, verdict in checker(out, exc):
            rows.append((filename, rule, criterion, expected, actual, verdict))

    total = len(rows)
    failed = sum(1 for r in rows if r[5] == FAIL)

    lines = [
        "# Bảng đối chiếu kết quả kiểm thử — Kỳ vọng vs Thực tế",
        "",
        "> Sinh tự động bởi `scripts/run_qa_scenarios.py`. Không sửa tay.",
        "> Kỳ vọng lấy từ Business Rules mục 3, `docs/T01_data_specification.md`.",
        "",
        f"**Tổng: {total} tiêu chí — ĐẠT {total - failed} / KHÔNG ĐẠT {failed}**",
        "",
        "| File test | Business Rule | Tiêu chí kiểm tra | Kỳ vọng | Thực tế | Kết luận |",
        "|---|---|---|---|---|---|",
    ]
    for filename, rule, criterion, expected, actual, verdict in rows:
        mark = "✅ ĐẠT" if verdict == PASS else "❌ KHÔNG ĐẠT"
        lines.append(f"| `{filename}` | {rule} | {criterion} | {expected} | {actual} | {mark} |")
    lines.append("")

    report = "\n".join(lines)
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write(report)

    print(report)
    print(f"Đã ghi bảng đối chiếu vào {REPORT_PATH}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
