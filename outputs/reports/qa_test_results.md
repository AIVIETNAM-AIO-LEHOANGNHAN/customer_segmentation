# Bảng đối chiếu kết quả kiểm thử — Kỳ vọng vs Thực tế

> Sinh tự động bởi `scripts/run_qa_scenarios.py`. Không sửa tay.
> Kỳ vọng lấy từ Business Rules mục 3, `docs/T01_data_specification.md`.

**Tổng: 23 tiêu chí — ĐẠT 16 / KHÔNG ĐẠT 7**

| File test | Business Rule | Tiêu chí kiểm tra | Kỳ vọng | Thực tế | Kết luận |
|---|---|---|---|---|---|
| `base_sample.csv` | Schema mục 1.3 — Dữ liệu sạch | Không mất dòng nào trên dữ liệu sạch | 300 dòng | 300 dòng | ✅ ĐẠT |
| `base_sample.csv` | Schema mục 1.3 — Dữ liệu sạch | Đủ 4 cột phái sinh theo schema mục 1.3 | 4 cột | 3 cột: IsCancelled, HasCustomerID, IsServiceCode | ❌ KHÔNG ĐẠT |
| `base_sample.csv` | Schema mục 1.3 — Dữ liệu sạch | Có cột TotalPrice (Quantity × Price) | có | thiếu | ❌ KHÔNG ĐẠT |
| `base_sample.csv` | Schema mục 1.3 — Dữ liệu sạch | InvoiceDate là datetime | datetime64 | datetime64[ns] | ✅ ĐẠT |
| `base_sample.csv` | Schema mục 1.3 — Dữ liệu sạch | Price là numeric | float | float64 | ✅ ĐẠT |
| `test_missing_customerid.csv` | BR-03 — CustomerID null | Dòng Customer ID null còn tồn tại | 300 dòng | 300 dòng | ✅ ĐẠT |
| `test_missing_customerid.csv` | BR-03 — CustomerID null | HasCustomerID = False được gắn cờ | 75 dòng | 75 dòng | ✅ ĐẠT |
| `test_missing_customerid.csv` | BR-03 — CustomerID null | Customer ID giữ đúng định dạng mã (vd 17850) | 0 mã bị lệch | 225/225 mã thành dạng '17850.0' | ❌ KHÔNG ĐẠT |
| `test_cancelled_invoice.csv` | BR-01/BR-02 — Hóa đơn hủy | Hóa đơn hủy không bị xoá | 320 dòng | 320 dòng | ✅ ĐẠT |
| `test_cancelled_invoice.csv` | BR-01/BR-02 — Hóa đơn hủy | IsCancelled = True được gắn cờ | 20 dòng | 20 dòng | ✅ ĐẠT |
| `test_cancelled_invoice.csv` | BR-01/BR-02 — Hóa đơn hủy | Quantity âm được giữ lại (BR-02) | 20 dòng | 20 dòng | ✅ ĐẠT |
| `test_service_code.csv` | BR-05 — Mã dịch vụ | Dòng mã dịch vụ không bị xoá | 312 dòng | 312 dòng | ✅ ĐẠT |
| `test_service_code.csv` | BR-05 — Mã dịch vụ | IsServiceCode = True được gắn cờ | 12 dòng | 8 dòng | ❌ KHÔNG ĐẠT |
| `test_service_code.csv` | BR-05 — Mã dịch vụ | Không sót mã dịch vụ nào | sót 0 mã | sót 4 mã: AMAZONFEE, D, S, m | ❌ KHÔNG ĐẠT |
| `test_zero_price.csv` | BR-04 — Giá bằng 0 | Dòng Price = 0 không bị xoá | 300 dòng | 300 dòng | ✅ ĐẠT |
| `test_zero_price.csv` | BR-04 — Giá bằng 0 | Được gắn cờ giá bất thường | 15 dòng | 15 dòng | ✅ ĐẠT |
| `test_missing_column.csv` | Thiếu cột bắt buộc | Chặn xử lý khi thiếu cột bắt buộc | báo lỗi & dừng | dừng bằng KeyError | ✅ ĐẠT |
| `test_missing_column.csv` | Thiếu cột bắt buộc | Thông báo lỗi rõ ràng cho người dùng | nêu rõ cột nào thiếu | KeyError: 'InvoiceDate' | ✅ ĐẠT |
| `test_wrong_dtype.csv` | BR-07 — Sai kiểu dữ liệu | Không crash khi gặp sai kiểu dữ liệu | không crash | không crash | ✅ ĐẠT |
| `test_wrong_dtype.csv` | BR-07 — Sai kiểu dữ liệu | Quantity sau xử lý là kiểu số | numeric | object | ❌ KHÔNG ĐẠT |
| `test_wrong_dtype.csv` | BR-07 — Sai kiểu dữ liệu | InvoiceDate sau xử lý là datetime | datetime64 | datetime64[ns] | ✅ ĐẠT |
| `test_wrong_dtype.csv` | BR-07 — Sai kiểu dữ liệu | Dòng ngày sai được gắn cờ, không xoá âm thầm | 0 dòng bị xoá không cờ | 5 dòng bị xoá, không có cột cờ | ❌ KHÔNG ĐẠT |
| `test_duplicate.csv` | BR-06 — Bản ghi trùng lặp | Duplicate bị loại, chỉ giữ 1 bản ghi | 300 dòng | 300 dòng | ✅ ĐẠT |
