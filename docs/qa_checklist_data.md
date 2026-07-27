# CHECKLIST KIỂM THỬ DỮ LIỆU ĐẦU VÀO

**Task:** KAN-12 — Task 5, Giai đoạn 1
**Vai trò:** QA/QC
**Phạm vi:** Module làm sạch (Task 2, `src/data/cleaning.py`) + UI upload/mapping (Task 3)
**Căn cứ đối chiếu:** `docs/T01_data_specification.md` — mục 1.3 (cột phái sinh), mục 2 (schema), mục 3 (Business Rules BR-01 → BR-08)

---

## Nguyên tắc nền

> **"Gắn cờ, không xoá vội".**
> Với bộ **Online Retail II**, các dòng "trông như lỗi" — thiếu `Customer ID`, hóa đơn hủy, mã dịch vụ, giá bằng 0 — phần lớn là **dữ liệu nghiệp vụ hợp lệ**. Chúng chỉ bị loại ở bước tính RFM (Epic 2), **không bị loại ở bước làm sạch**.
> Vì vậy tiêu chí kiểm thử quan trọng nhất của giai đoạn này không phải "hệ thống có chạy không", mà là **"hệ thống có xoá nhầm cái gì không"**.

Chỉ có **đúng một** trường hợp được phép xoá dòng ở bước làm sạch: bản ghi trùng lặp hoàn toàn (BR-06).

---

## Cách chạy bộ kiểm thử

```bash
python scripts/generate_test_samples.py    # sinh lại 7 file test trong data/test_samples/
```

```bash
python scripts/run_qa_scenarios.py         # chạy 7 kịch bản, ghi outputs/reports/qa_test_results.md
```

```bash
python -m pytest tests/ -v                 # bộ test tự động (xfail = lỗi đã ghi nhận, chưa sửa)
```

---

## NHÓM A — Lỗi kỹ thuật chung

| # | Hạng mục kiểm tra | Kỳ vọng | Căn cứ | Cách kiểm | Kết quả |
|---|---|---|---|---|---|
| A1 | Bản ghi trùng lặp hoàn toàn | Chỉ giữ lại 1 bản ghi | BR-06 | `test_duplicate.csv` (350 → 300 dòng) | ✅ ĐẠT |
| A2 | Không xoá nhầm dòng chỉ giống nhau một phần | Giữ nguyên số dòng | BR-06 | `base_sample.csv` | ✅ ĐẠT |
| A3 | `InvoiceDate` sai định dạng được convert hoặc gắn cờ | Convert được thì convert; không convert được thì **gắn cờ rồi mới loại** | BR-07 | `test_wrong_dtype.csv` (5 dòng `"not-a-date"`) | ❌ **QA-03** — xoá thẳng, không cờ |
| A4 | `InvoiceDate` sau xử lý là kiểu `datetime` | `datetime64[ns]` | Schema mục 2 | `base_sample.csv` | ✅ ĐẠT |
| A5 | `Quantity` sau xử lý là kiểu số | numeric | Schema mục 2 | `test_wrong_dtype.csv` (10 dòng `"abc"`) | ❌ **QA-02** — giữ dtype `object` |
| A6 | `Price` sau xử lý là kiểu số | `float64` | Schema mục 2 | `base_sample.csv` | ✅ ĐẠT |
| A7 | Thiếu cột bắt buộc thì chặn xử lý | Dừng, không xử lý tiếp | Schema mục 1.4 | `test_missing_column.csv` (xoá `InvoiceDate`) | ✅ ĐẠT |
| A8 | Thông báo lỗi thiếu cột đủ rõ cho người dùng | Nêu rõ tên cột thiếu, dạng lỗi nghiệp vụ | Schema mục 1.4 | `test_missing_column.csv` | ⚠️ **QA-06** — `KeyError` thô |
| A9 | Không crash khi gặp dữ liệu sai kiểu | Xử lý xong hoặc báo lỗi có kiểm soát | — | `test_wrong_dtype.csv` | ✅ ĐẠT |
| A10 | Đủ các cột phái sinh theo schema | 4 cột: `TotalPrice`, `IsCancelled`, `HasCustomerID`, `IsServiceCode` | Mục 1.3 | `base_sample.csv` | ❌ **QA-05** — thiếu `TotalPrice` |

---

## NHÓM B — Đặc thù Online Retail II *(quan trọng nhất, dễ sai nhất)*

| # | Hạng mục kiểm tra | Kỳ vọng | Căn cứ | Cách kiểm | Kết quả |
|---|---|---|---|---|---|
| B1 | Dòng `Customer ID` null **còn tồn tại** trong `data/processed/` | Không xoá dòng nào | BR-03 | `test_missing_customerid.csv` (75/300 dòng null) | ✅ ĐẠT |
| B2 | Dòng `Customer ID` null được gắn cờ `HasCustomerID = False` | Đúng 75 dòng | BR-03 | `test_missing_customerid.csv` | ✅ ĐẠT |
| B3 | `Customer ID` giữ đúng định dạng mã | `17850`, không phải `17850.0` | Mục 1.2 | `test_missing_customerid.csv` | ❌ **QA-04** — 100% mã bị lệch |
| B4 | Dòng `Invoice` bắt đầu bằng `C` **không bị xoá** | Giữ nguyên | BR-01 | `test_cancelled_invoice.csv` (20 dòng) | ✅ ĐẠT |
| B5 | Dòng hóa đơn hủy được gắn cờ `IsCancelled = True` | Đúng 20 dòng | BR-01 | `test_cancelled_invoice.csv` | ✅ ĐẠT |
| B6 | `Quantity` âm được giữ lại, không coi là lỗi | Giữ nguyên 20 dòng | BR-02 | `test_cancelled_invoice.csv` | ✅ ĐẠT |
| B7 | Hóa đơn thường không bị gắn cờ nhầm `IsCancelled` | 0 dòng | BR-01 | `base_sample.csv` | ✅ ĐẠT |
| B8 | Dòng mã dịch vụ **không bị xoá** | Giữ nguyên | BR-05 | `test_service_code.csv` (12 dòng) | ✅ ĐẠT |
| B9 | Mã dịch vụ được gắn cờ `IsServiceCode = True` **đầy đủ, không sót** | 12/12 dòng | BR-05 | `test_service_code.csv` | ❌ **QA-01** — sót 4 mã |
| B10 | So khớp mã dịch vụ không phân biệt hoa/thường | `m` cũng phải bắt được như `M` | BR-05 | `test_service_code.csv` | ❌ **QA-01** — sót `m` |
| B11 | Dòng `Price = 0` **không bị xoá**, chỉ gắn cờ | Giữ nguyên 300 dòng | BR-04 | `test_zero_price.csv` (15 dòng) | ✅ ĐẠT |
| B12 | Dòng `Price = 0` được đánh dấu | Đúng 15 dòng | BR-04 | `test_zero_price.csv` | ✅ ĐẠT |
| B13 | `Price` âm cũng được đánh dấu | Đánh dấu | BR-04 (mở rộng) | unit test `flag_price_anomaly` | ✅ ĐẠT |
| B14 | Dòng thiếu `Description` được giữ nguyên | Không xoá | BR-08 | Dữ liệu gốc: 1.454 dòng null | ✅ ĐẠT |

---

## NHÓM C — UI Upload & Mapping *(Task 3)*

> ⛔ **Chưa thực thi được.** Tính đến 27/07/2026, Task 3 chưa có mã nguồn trên bất kỳ nhánh nào của repo (`main`, `develop`, `task2-data-cleaning` đều không có `src/app/`). Checklist dưới đây đã soạn sẵn và file test đã chuẩn bị xong, sẽ chạy ngay khi Pipeline bàn giao.

| # | Hạng mục kiểm tra | Kỳ vọng | Căn cứ | File test |
|---|---|---|---|---|
| C1 | Upload file gốc Online Retail II | Mapping tự động khớp đúng cả 8 cột | Mục 1.4 | `data/raw/online_retail_II.csv` |
| C2 | Upload file đã đổi tên cột (`Ma_don_hang` thay `Invoice`...) | Mapping thủ công hoạt động | Mục 1.4 | *(cần bổ sung khi có UI)* |
| C3 | **Upload file có nhiều `Customer ID` null vẫn được chấp nhận** | **Không chặn ở bước validate** | BR-03 | `test_missing_customerid.csv` |
| C4 | Thiếu cột bắt buộc thì chặn upload, báo lỗi rõ | Chặn + nêu tên cột thiếu | Mục 1.4 | `test_missing_column.csv` |
| C5 | Thiếu cột tùy chọn (`Description`, `Country`) vẫn cho đi tiếp | Cho phép tiếp tục | Mục 1.4 | *(cần bổ sung khi có UI)* |
| C6 | File sai kiểu dữ liệu không làm sập app | Báo lỗi có kiểm soát | — | `test_wrong_dtype.csv` |

> ⚠️ **Lưu ý cho Pipeline khi làm C3:** đây là lỗi rất dễ mắc. Schema mục 2 ghi `Customer ID` là *"Có (đối với RFM)"* — dòng chữ này dễ bị đọc nhầm thành ràng buộc `NOT NULL` ở bước validate upload. Đúng phải là: **`Customer ID` bắt buộc phải được *mapping*, nhưng giá trị trong cột được phép null** (25% dữ liệu gốc là null). Chặn upload ở đây sẽ loại bỏ 1/4 dataset.

---

## NHÓM D — Đối chiếu số liệu với Task 2

| # | Hạng mục kiểm tra | Kỳ vọng | Kết quả |
|---|---|---|---|
| D1 | Số dòng trước/sau xử lý khớp với output của Data | Khớp | ✅ ĐẠT — 541.910 → 536.642 |
| D2 | Tỷ lệ `IsCancelled` khớp | Khớp | ✅ ĐẠT — 9.251 (1,72%) |
| D3 | Tỷ lệ `HasCustomerID = False` khớp | Khớp | ✅ ĐẠT — 135.037 (25,16%) |
| D4 | Tỷ lệ `IsServiceCode` khớp | Khớp | ✅ ĐẠT — 2.730 (0,51%) |
| D5 | Chạy lại pipeline cho kết quả tái lập được | Khớp 100% | ✅ ĐẠT |
| D6 | Quy mô dataset khớp mô tả dự án | ~1 triệu giao dịch (README) | ❌ **QA-07** — chỉ có 541.910 |

---

## Bảng tra cứu lỗi

| Mã | Mô tả ngắn | Mức | Chi tiết |
|---|---|---|---|
| QA-01 | Sót mã dịch vụ `D`, `S`, `AMAZONFEE`, `m` | Trung bình | [Báo cáo](../outputs/reports/data_quality_report.md) |
| QA-02 | `Quantity` không được ép kiểu số | Nghiêm trọng | nt |
| QA-03 | `InvoiceDate` lỗi bị xoá không gắn cờ | Nghiêm trọng | nt |
| QA-04 | `Customer ID` bị đổi thành `17850.0` | Nghiêm trọng | nt |
| QA-05 | Thiếu cột `TotalPrice` | Trung bình | nt |
| QA-06 | Lỗi thiếu cột trả về `KeyError` thô | Nhẹ | nt |
| QA-07 | Dataset chỉ có 1/2 dữ liệu Online Retail II | Nghiêm trọng | nt |
| QA-08 | Tên cột trong tài liệu lệch với dữ liệu thật | Trung bình | nt |
| QA-09 | `requirements.txt` rỗng | Trung bình | nt |
| QA-10 | File 60 MB `cleaned_transactions.csv` bị commit | Nhẹ | nt |
| QA-11 | Hóa đơn `A` (Adjust bad debt) chưa có quy tắc xử lý | Nhẹ | nt |
| QA-12 | Chất lượng mã nguồn module làm sạch (tắt warning toàn cục, `print` thay `logging`) | Nhẹ | nt |

---

## Bộ file test

| File | Nội dung chỉnh sửa | Số dòng |
|---|---|---|
| `base_sample.csv` | Dữ liệu nền, sạch tuyệt đối với mọi Business Rule | 300 |
| `test_missing_customerid.csv` | Xoá `Customer ID` ở 75 dòng (25%) | 300 |
| `test_cancelled_invoice.csv` | Thêm 20 dòng `Invoice` = `C…` kèm `Quantity` âm | 320 |
| `test_service_code.csv` | Chèn 12 dòng mã dịch vụ (`POST`, `DOT`, `M`, `m`, `BANK CHARGES`, `D`, `S`, `AMAZONFEE`) | 312 |
| `test_zero_price.csv` | Đặt `Price = 0` cho 15 dòng | 300 |
| `test_missing_column.csv` | Xoá hẳn cột `InvoiceDate` | 300 (7 cột) |
| `test_wrong_dtype.csv` | 10 dòng `Quantity = "abc"`, 5 dòng `InvoiceDate = "not-a-date"` | 300 |
| `test_duplicate.csv` | Nhân đôi 50 dòng | 350 |

Tất cả sinh lại được bằng `python scripts/generate_test_samples.py` (deterministic — cùng input cho ra cùng output).
