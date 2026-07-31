# Ghi chú kiểm thử Task 3: Upload file và mapping cột

Ngày kiểm thử: 2026-07-27
Branch: develop

## Phạm vi

Đã triển khai và kiểm thử chức năng upload file CSV/XLSX và mapping cột.
Schema chuẩn theo Task 3 sử dụng tên cột của Online Retail II:

- Cột bắt buộc: InvoiceNo, StockCode, Quantity, InvoiceDate, UnitPrice, CustomerID
- Cột tùy chọn: Description, Country

Lưu ý quan trọng: Bước upload/mapping chỉ kiểm tra cột CustomerID đã được mapping hay chưa.
Không chặn upload nếu giá trị CustomerID bị null, vì đây là đặc điểm bình thường của dataset gốc.

## Kịch bản 1: File gốc Online Retail II

Dữ liệu đầu vào:

- File XLSX mẫu có 2 sheet.
- Các cột: InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country.
- Có 1 dòng bị thiếu giá trị CustomerID.

Kết quả mong đợi:

- Đọc header để lấy danh sách cột trước khi đọc toàn bộ dữ liệu.
- Tự động mapping đủ 8 cột khi tên cột trùng schema chuẩn.
- Đọc và gộp dữ liệu từ nhiều sheet.
- Không chặn xử lý chỉ vì CustomerID có giá trị null.
- Sau khi mapping hợp lệ, dữ liệu được truyền vào cleaning pipeline.

Kết quả thực tế:

- Đạt.
- Mapping mặc định hợp lệ.
- 2 sheet được gộp thành 3 dòng trong bộ test.
- Cleaning pipeline tạo cột HasCustomerID và đánh dấu 1 dòng thiếu CustomerID.

Kiểm tra bổ sung với tên cột kiểu UCI:

- Đã kiểm tra thêm file XLSX 2 sheet với tên cột Invoice, Price, Customer ID.
- Mapping mặc định nhận đúng Invoice -> InvoiceNo, Price -> UnitPrice, Customer ID -> CustomerID.
- Dữ liệu từ 2 sheet được gộp thành công.

## Kịch bản 2: File có tên cột khác

Dữ liệu đầu vào:

- File CSV mẫu.
- Cột nguồn: bill_id, sku, product_name, qty, sold_at, price_each, buyer_id, ship_country.
- Người dùng mapping thủ công các cột nguồn sang 8 cột chuẩn.

Kết quả mong đợi:

- Mapping mặc định không bắt buộc phải khớp với các tên cột tùy biến.
- Người dùng có thể chọn mapping thủ công bằng dropdown.
- Mapping hợp lệ khi đã chọn đủ 6 cột bắt buộc.
- Các cột được rename sang schema chuẩn.
- Dữ liệu sau mapping được truyền vào cleaning pipeline.

Kết quả thực tế:

- Đạt.
- Mapping thủ công hợp lệ.
- DataFrame sau mapping có đủ các cột chuẩn.
- Cleaning pipeline tính TotalPrice đúng.

## Kịch bản 3: File thiếu cột bắt buộc

Dữ liệu đầu vào:

- File CSV mẫu có các cột InvoiceNo, StockCode, Quantity, InvoiceDate, CustomerID.
- Thiếu cột UnitPrice.

Kết quả mong đợi:

- Validate thất bại.
- Không cho bấm nút xử lý tiếp.
- Thông báo lỗi phải nêu rõ cột bắt buộc còn thiếu.

Kết quả thực tế:

- Đạt.
- Validate thất bại với missing_required = ["UnitPrice"].
- UI hiển thị thông báo: Missing required mapping: UnitPrice.

## File dùng để test nhanh

Có thể test nhanh bằng file có sẵn trong repo:

- data/processed/cleaned_transactions.csv

File này dùng một số tên cột theo schema cũ của module cleaning:

- Invoice thay cho InvoiceNo
- Price thay cho UnitPrice
- Customer ID thay cho CustomerID

Mapper đã hỗ trợ các alias trên, nên khi upload file này UI vẫn tự động mapping được các cột bắt buộc.
File cũng có sẵn một số cột sau cleaning như IsCancelled, HasCustomerID, IsServiceCode, PriceAnomaly; các cột dư này không ảnh hưởng đến bước mapping.

## Lệnh kiểm tra đã chạy

```powershell
python -m py_compile src\app\column_mapper.py src\app\Home.py src\data\cleaning.py
```

Ngoài ra đã chạy script Python nội tuyến để mô phỏng 3 kịch bản trên và kiểm tra mapping/cleaning bằng assertion.
