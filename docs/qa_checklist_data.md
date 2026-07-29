# CHECKLIST KIỂM THỬ DỮ LIỆU ĐẦU VÀO

**Task:** KAN-12 — Task 5, Giai đoạn 1
**Vai trò:** QA/QC
**Phạm vi:** Module làm sạch (Task 2) + UI upload/mapping (Task 3) + đối chiếu EDA (Task 4)
**Căn cứ đối chiếu:** `docs/T01_data_specification.md` — mục 1.3 (cột phái sinh), mục 2 (schema), mục 3 (Business Rules BR-01 → BR-08)

| Vòng | Ngày | Commit được kiểm | Kết quả |
|---|---|---|---|
| 1 | 27/07/2026 | Task 2 `b52a0b3` | 23 tiêu chí — 16 ĐẠT / 7 KHÔNG ĐẠT |
| **2** | **29/07/2026** | Task 2 `5cfc434` · Task 3 `510245c` · Task 4 `3d4248e` | **29 tiêu chí — 26 ĐẠT / 3 KHÔNG ĐẠT** |

---

## Nguyên tắc nền

> **"Gắn cờ, không xoá vội".**
> Với bộ **Online Retail II**, các dòng "trông như lỗi" — thiếu `Customer ID`, hóa đơn hủy, mã dịch vụ, giá bằng 0 — phần lớn là **dữ liệu nghiệp vụ hợp lệ**. Chúng chỉ bị loại ở bước tính RFM (Epic 2), **không bị loại ở bước làm sạch**.
> Chỉ có **đúng một** trường hợp được phép xoá dòng ở bước làm sạch: bản ghi trùng lặp hoàn toàn (BR-06).

---

## Cách chạy bộ kiểm thử

```bash
python scripts/generate_test_samples.py
```

```bash
python scripts/run_qa_scenarios.py
```

```bash
python -m pytest tests/ -v
```

---

## NHÓM A — Lỗi kỹ thuật chung

| # | Hạng mục kiểm tra | Kỳ vọng | Căn cứ | Vòng 1 | Vòng 2 |
|---|---|---|---|---|---|
| A1 | Bản ghi trùng lặp hoàn toàn | Chỉ giữ 1 bản ghi | BR-06 | ✅ | ✅ |
| A2 | Không xoá nhầm dòng chỉ giống một phần | Giữ nguyên số dòng | BR-06 | ✅ | ✅ |
| A3 | `InvoiceDate` sai định dạng được gắn cờ | Gắn cờ **rồi mới** loại | BR-07 | ❌ QA-03 | ✅ **Đã sửa** |
| A4 | `InvoiceDate` sau xử lý là `datetime` | `datetime64[ns]` | Schema mục 2 | ✅ | ✅ |
| A5 | `Quantity` sau xử lý là kiểu số | numeric | Schema mục 2 | ❌ QA-02 | ✅ **Đã sửa** |
| A6 | `Price` sau xử lý là kiểu số | `float64` | Schema mục 2 | ✅ | ✅ |
| A7 | Thiếu cột bắt buộc thì chặn xử lý | Dừng, không xử lý tiếp | Mục 1.4 | ✅ | ✅ |
| A8 | Thông báo lỗi thiếu cột đủ rõ | Nêu rõ tên cột thiếu | Mục 1.4 | ⚠️ QA-06 | ✅ *(còn `KeyError` — QA-06 mở)* |
| A9 | Không crash khi gặp dữ liệu sai kiểu | Có kiểm soát | — | ✅ | ✅ |
| A10 | Đủ 4 cột phái sinh theo schema | `TotalPrice`, `IsCancelled`, `HasCustomerID`, `IsServiceCode` | Mục 1.3 | ❌ QA-05 | ✅ **Đã sửa** |
| A11 | Dòng `Quantity` ép kiểu hỏng được **giữ lại** | 0 dòng bị xoá | BR-07 (suy rộng) | — | ✅ |
| A12 | Dòng `Quantity` ép kiểu hỏng được **gắn cờ** | Có cột cờ riêng | Đối xứng với A3 | — | ❌ **QA-14** |

---

## NHÓM B — Đặc thù Online Retail II *(quan trọng nhất, dễ sai nhất)*

| # | Hạng mục kiểm tra | Kỳ vọng | Căn cứ | Vòng 1 | Vòng 2 |
|---|---|---|---|---|---|
| B1 | Dòng `Customer ID` null **còn tồn tại** | Không xoá dòng nào | BR-03 | ✅ | ✅ |
| B2 | Dòng `Customer ID` null gắn cờ `HasCustomerID = False` | Đúng 75/300 dòng | BR-03 | ✅ | ✅ |
| B3 | `Customer ID` giữ đúng định dạng mã | `17850`, không phải `17850.0` | Mục 1.2 | ❌ QA-04 | ✅ **Đã sửa** |
| B4 | Sửa định dạng không gộp nhầm hai khách làm một | `nunique` không đổi | Mục 1.2 | — | ✅ |
| B5 | Dòng `Invoice` bắt đầu bằng `C` **không bị xoá** | Giữ nguyên | BR-01 | ✅ | ✅ |
| B6 | Hóa đơn hủy gắn cờ `IsCancelled = True` | Đúng 20 dòng | BR-01 | ✅ | ✅ |
| B7 | `Quantity` âm được giữ lại | Giữ nguyên 20 dòng | BR-02 | ✅ | ✅ |
| B8 | Hóa đơn thường không bị gắn cờ nhầm | 0 dòng | BR-01 | ✅ | ✅ |
| B9 | Dòng mã dịch vụ **không bị xoá** | Giữ nguyên | BR-05 | ✅ | ✅ |
| B10 | Gắn cờ `IsServiceCode` đầy đủ | 12/12 dòng mẫu | BR-05 | ❌ QA-01 | ✅ **Đã sửa** |
| B11 | So khớp mã dịch vụ không phân biệt hoa/thường | `m` bắt được như `M` | BR-05 | ❌ QA-01 | ✅ **Đã sửa** |
| B12 | **Không** gắn cờ nhầm mã sản phẩm thật | `85123A`, `DCGSSGIRL`, `PADS` → False | BR-05 | — | ✅ *(regression của `.str.upper()`)* |
| B13 | Không sót mã phi-sản-phẩm nào trên dữ liệu thật | `B`, `gift_*` phải gắn cờ | BR-05 | ❌ QA-01 | ❌ **QA-01 còn lại** |
| B14 | Dòng `Price = 0` **không bị xoá**, chỉ gắn cờ | Giữ nguyên 300 dòng | BR-04 | ✅ | ✅ |
| B15 | Dòng `Price = 0` được đánh dấu | Đúng 15 dòng | BR-04 | ✅ | ✅ |
| B16 | `Price` âm cũng được đánh dấu | Đánh dấu | BR-04 | ✅ | ✅ |
| B17 | Dòng thiếu `Description` được giữ nguyên | Không xoá | BR-08 | ✅ | ✅ |

---

## NHÓM C — UI Upload & Mapping *(Task 3)*

> Vòng 1: ⛔ chưa thực thi được (chưa có mã nguồn).
> **Vòng 2: đã chạy đầy đủ** trên `task-3-upload-mapping` @ `510245c`. Bộ test: `tests/test_upload_mapping.py`.

| # | Hạng mục kiểm tra | Kỳ vọng | Căn cứ | Kết quả |
|---|---|---|---|---|
| C1 | Upload file gốc → mapping tự động khớp 8 cột | 8/8 | Mục 1.4 | ✅ **8/8** |
| C2 | Upload file đổi tên cột → mapping thủ công hoạt động | Map tay được | Mục 1.4 | ✅ |
| C3 | **File nhiều `Customer ID` null vẫn được chấp nhận** | **Không chặn ở validate** | BR-03 | ✅ **ĐẠT** |
| C4 | Thiếu cột bắt buộc → chặn, báo lỗi rõ | Chặn + nêu tên cột | Mục 1.4 | ✅ |
| C5 | Thiếu cột tùy chọn vẫn cho đi tiếp | Cho phép tiếp tục | Mục 1.4 | ✅ |
| C6 | File sai kiểu dữ liệu không làm sập app | Có kiểm soát | — | ✅ |
| C7 | Map 1 cột nguồn cho 2 cột chuẩn → bị từ chối | Báo lỗi | Mục 1.4 | ✅ |
| C8 | Map tới cột không tồn tại → bị từ chối | Báo lỗi | Mục 1.4 | ✅ |
| C9 | Chuẩn hoá tên cột bỏ qua hoa/thường, `_`, `-` | Khớp được | — | ✅ |
| C10 | Đuôi file lạ bị từ chối rõ ràng | `UnsupportedFileTypeError` | — | ✅ |
| C11 | **Luồng batch và luồng UI cho cùng schema** | Cùng bộ tên cột | Mục 1.4 | ❌ **QA-16** |

---

## NHÓM D — Đối chiếu số liệu liên vai trò

| # | Hạng mục kiểm tra | Kỳ vọng | Vòng 1 | Vòng 2 |
|---|---|---|---|---|
| D1 | Số dòng trước/sau xử lý khớp output của Data | Khớp | ✅ 541.910 → 536.642 | ✅ |
| D2 | Tỷ lệ `IsCancelled` khớp | Khớp | ✅ 9.251 (1,72%) | ✅ |
| D3 | Tỷ lệ `HasCustomerID = False` khớp | Khớp | ✅ 135.037 (25,16%) | ✅ |
| D4 | Tỷ lệ `IsServiceCode` khớp | Khớp | ✅ 2.730 | ✅ 2.904 *(sau fix)* |
| D5 | Chạy lại pipeline tái lập được kết quả | Khớp 100% | ✅ | ✅ |
| D6 | Quy mô dataset khớp mô tả dự án | ~1 triệu giao dịch | ❌ QA-07 | ❌ **QA-07 còn mở** |
| D7 | **`data/processed/` phản ánh code hiện tại** | File sinh lại sau khi sửa | — | ❌ **QA-13** |
| D8 | Số liệu báo cáo Task 4 tái lập được | Khớp | — | ✅ **40/40 con số** |
| D9 | Kết luận Task 4 còn đúng với dữ liệu hiện tại | Còn đúng | — | ❌ **QA-17** |

---

## Bảng tra cứu lỗi

| Mã | Mô tả ngắn | Mức | Vai trò | Trạng thái |
|---|---|---|---|---|
| QA-01 | Sót mã dịch vụ | Trung bình | Data | 🟡 Sửa một phần — còn `B`, `gift_*` |
| QA-02 | `Quantity` không ép kiểu số | Nghiêm trọng | Data | ✅ Đã sửa `5cfc434` |
| QA-03 | `InvoiceDate` lỗi bị xoá không gắn cờ | Nghiêm trọng | Data | ✅ Đã sửa `5cfc434` |
| QA-04 | `Customer ID` thành `17850.0` | Nghiêm trọng | Data | ✅ Đã sửa `5cfc434` |
| QA-05 | Thiếu cột `TotalPrice` | Trung bình | Data | ✅ Đã sửa `5cfc434` |
| QA-06 | Lỗi thiếu cột trả về `KeyError` thô | Nhẹ | Data | 🟡 Thông điệp tốt hơn, vẫn `KeyError` |
| QA-07 | Dataset chỉ có 1/2 dữ liệu Online Retail II | Nghiêm trọng | Leader + Data | 🔴 **Còn mở** |
| QA-08 | Tên cột tài liệu lệch dữ liệu thật | Trung bình | Leader | 🔴 **Còn mở — đã gây ra QA-16** |
| QA-09 | `requirements.txt` rỗng | Trung bình | Leader | 🟡 Task 3 thêm 3 dòng, còn thiếu |
| QA-10 | File 60 MB bị commit | Nhẹ | Data | 🟡 Còn mở |
| QA-11 | Hóa đơn `A` chưa có quy tắc | Nhẹ | Leader | 🟡 Còn mở |
| QA-12 | Chất lượng mã nguồn module làm sạch | Nhẹ | Data | 🟡 Còn mở |
| **QA-13** | **`cleaned_transactions.csv` chưa sinh lại sau khi sửa code** | **Nghiêm trọng** | Data | 🔴 **Mới** |
| **QA-14** | `Quantity` ép kiểu hỏng không có cờ | Trung bình | Data | 🟠 **Mới** |
| **QA-15** | Task 3 sửa file thuộc sở hữu Task 2 | Trung bình | Pipeline + Data | 🟠 **Mới** |
| **QA-16** | **Luồng batch và UI cho hai schema khác nhau** | **Nghiêm trọng** | Pipeline + Leader | 🔴 **Mới** |
| **QA-17** | **EDA Task 4 chạy trên dữ liệu lỗi thời** | **Nghiêm trọng** | Model | 🔴 **Mới** |
| **QA-18** | Nhánh `task4-eda` không có `cleaning.py` | Trung bình | Model | 🟠 **Mới** |

Review chi tiết theo từng vai trò: [`docs/reviews/`](reviews/)

---

## Bộ file test

| File | Nội dung chỉnh sửa | Số dòng |
|---|---|---|
| `base_sample.csv` | Dữ liệu nền, sạch tuyệt đối với mọi Business Rule | 300 |
| `test_missing_customerid.csv` | Xoá `Customer ID` ở 75 dòng (25%) | 300 |
| `test_cancelled_invoice.csv` | Thêm 20 dòng `Invoice` = `C…` kèm `Quantity` âm | 320 |
| `test_service_code.csv` | Chèn 12 dòng mã dịch vụ (gồm `m` chữ thường, `D`, `S`, `AMAZONFEE`) | 312 |
| `test_zero_price.csv` | Đặt `Price = 0` cho 15 dòng | 300 |
| `test_missing_column.csv` | Xoá hẳn cột `InvoiceDate` | 300 (7 cột) |
| `test_wrong_dtype.csv` | 10 dòng `Quantity = "abc"`, 5 dòng `InvoiceDate = "not-a-date"` | 300 |
| `test_duplicate.csv` | Nhân đôi 50 dòng | 350 |

Tất cả sinh lại được bằng `python scripts/generate_test_samples.py` (deterministic).
