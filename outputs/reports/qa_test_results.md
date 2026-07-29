# Bảng đối chiếu kết quả kiểm thử — Kỳ vọng vs Thực tế

> Sinh tự động bởi `scripts/run_qa_scenarios.py`. Không sửa tay.
> Kỳ vọng lấy từ Business Rules mục 3, `docs/T01_data_specification.md`.

**Tổng: 29 tiêu chí — ĐẠT 26 / KHÔNG ĐẠT 3**

| File test | Business Rule | Tiêu chí kiểm tra | Kỳ vọng | Thực tế | Kết luận |
|---|---|---|---|---|---|
| `base_sample.csv` | Schema mục 1.3 — Dữ liệu sạch | Không mất dòng nào trên dữ liệu sạch | 300 dòng | 300 dòng | ✅ ĐẠT |
| `base_sample.csv` | Schema mục 1.3 — Dữ liệu sạch | Đủ 4 cột phái sinh theo schema mục 1.3 | 4 cột | 4 cột: TotalPrice, IsCancelled, HasCustomerID, IsServiceCode | ✅ ĐẠT |
| `base_sample.csv` | Schema mục 1.3 — Dữ liệu sạch | Có cột TotalPrice (Quantity × Price) | có | có | ✅ ĐẠT |
| `base_sample.csv` | Schema mục 1.3 — Dữ liệu sạch | InvoiceDate là datetime | datetime64 | datetime64[ns] | ✅ ĐẠT |
| `base_sample.csv` | Schema mục 1.3 — Dữ liệu sạch | Price là numeric | float | float64 | ✅ ĐẠT |
| `test_missing_customerid.csv` | BR-03 — CustomerID null | Dòng Customer ID null còn tồn tại | 300 dòng | 300 dòng | ✅ ĐẠT |
| `test_missing_customerid.csv` | BR-03 — CustomerID null | HasCustomerID = False được gắn cờ | 75 dòng | 75 dòng | ✅ ĐẠT |
| `test_missing_customerid.csv` | BR-03 — CustomerID null | Customer ID giữ đúng định dạng mã (vd 17850) | 0 mã bị lệch | 0/225 mã thành dạng '17850' | ✅ ĐẠT |
| `test_cancelled_invoice.csv` | BR-01/BR-02 — Hóa đơn hủy | Hóa đơn hủy không bị xoá | 320 dòng | 320 dòng | ✅ ĐẠT |
| `test_cancelled_invoice.csv` | BR-01/BR-02 — Hóa đơn hủy | IsCancelled = True được gắn cờ | 20 dòng | 20 dòng | ✅ ĐẠT |
| `test_cancelled_invoice.csv` | BR-01/BR-02 — Hóa đơn hủy | Quantity âm được giữ lại (BR-02) | 20 dòng | 20 dòng | ✅ ĐẠT |
| `test_service_code.csv` | BR-05 — Mã dịch vụ | Dòng mã dịch vụ không bị xoá | 312 dòng | 312 dòng | ✅ ĐẠT |
| `test_service_code.csv` | BR-05 — Mã dịch vụ | IsServiceCode = True được gắn cờ | 12 dòng | 12 dòng | ✅ ĐẠT |
| `test_service_code.csv` | BR-05 — Mã dịch vụ | Không sót mã dịch vụ nào | sót 0 mã | sót 0 mã: — | ✅ ĐẠT |
| `test_zero_price.csv` | BR-04 — Giá bằng 0 | Dòng Price = 0 không bị xoá | 300 dòng | 300 dòng | ✅ ĐẠT |
| `test_zero_price.csv` | BR-04 — Giá bằng 0 | Được gắn cờ giá bất thường | 15 dòng | 15 dòng | ✅ ĐẠT |
| `test_missing_column.csv` | Thiếu cột bắt buộc | Chặn xử lý khi thiếu cột bắt buộc | báo lỗi & dừng | dừng bằng KeyError | ✅ ĐẠT |
| `test_missing_column.csv` | Thiếu cột bắt buộc | Thông báo lỗi rõ ràng cho người dùng | nêu rõ cột nào thiếu | KeyError: 'Missing required column. Expected one of: InvoiceDate' | ✅ ĐẠT |
| `test_wrong_dtype.csv` | BR-07 — Sai kiểu dữ liệu | Không crash khi gặp sai kiểu dữ liệu | không crash | không crash | ✅ ĐẠT |
| `test_wrong_dtype.csv` | BR-07 — Sai kiểu dữ liệu | Quantity sau xử lý là kiểu số | numeric | float64 | ✅ ĐẠT |
| `test_wrong_dtype.csv` | BR-07 — Sai kiểu dữ liệu | InvoiceDate sau xử lý là datetime | datetime64 | datetime64[ns] | ✅ ĐẠT |
| `test_wrong_dtype.csv` | BR-07 — Sai kiểu dữ liệu | Dòng ngày sai được gắn cờ, không xoá âm thầm | 0 dòng bị xoá + có cờ | 0 dòng bị xoá, cờ HasInvalidDate: có | ✅ ĐẠT |
| `test_wrong_dtype.csv` | BR-07 — Sai kiểu dữ liệu | Dòng Quantity ép kiểu hỏng được giữ lại | 0 dòng bị xoá | 0 dòng bị xoá, 10 dòng thành NaN | ✅ ĐẠT |
| `test_wrong_dtype.csv` | BR-07 — Sai kiểu dữ liệu | Dòng Quantity ép kiểu hỏng được gắn cờ | có cột cờ riêng | 0 cột cờ (không có) | ❌ KHÔNG ĐẠT |
| `test_duplicate.csv` | BR-06 — Bản ghi trùng lặp | Duplicate bị loại, chỉ giữ 1 bản ghi | 300 dòng | 300 dòng | ✅ ĐẠT |
| `base_sample.csv` | Task 3 — Mapping tự động | Khớp đủ 8 cột chuẩn | 8/8 cột | 8/8 cột | ✅ ĐẠT |
| `test_missing_customerid.csv` | BR-03 + Task 3 | CustomerID null KHÔNG chặn upload | cho qua | cho qua | ✅ ĐẠT |
| `base_sample.csv` | Tích hợp Task 2 ↔ Task 3 | Luồng batch và luồng UI cho cùng schema | cùng bộ tên cột | lệch 3 cột — batch: Customer ID, Invoice, Price / UI: CustomerID, InvoiceNo, UnitPrice | ❌ KHÔNG ĐẠT |
| `data\processed\cleaned_transactions.csv` | Tính tươi của artifact | File processed sinh lại sau khi sửa module | có TotalPrice + HasInvalidDate | 12 cột, TotalPrice: thiếu, HasInvalidDate: thiếu | ❌ KHÔNG ĐẠT |
