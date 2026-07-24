# DATA SPECIFICATION REPORT

## 1. Data Dictionary

### 1.1. Mục đích

Data Dictionary mô tả ý nghĩa nghiệp vụ của từng trường dữ liệu trong bộ dữ liệu **Online Retail II** và quy định cách ánh xạ (Data Mapping) giữa dữ liệu người dùng tải lên với cấu trúc chuẩn của hệ thống.

Phần này giúp tất cả thành viên trong nhóm thống nhất cách hiểu về dữ liệu và là căn cứ để:

- **Data** thực hiện tiền xử lý dữ liệu.
- **Pipeline** xây dựng chức năng Upload và Mapping cột.
- **Model** xây dựng đặc trưng RFM.
- **QA/QC** kiểm thử tính hợp lệ của dữ liệu đầu vào.

---

### 1.2 Data Dictionary

| Cột chuẩn | Kiểu dữ liệu | Ý nghĩa nghiệp vụ | Ví dụ | Sử dụng trong |
|-----------|-------------|-------------------|--------|---------------|
| **Invoice** | String | Mã định danh của hóa đơn. Nếu bắt đầu bằng ký tự **C** thì đây là hóa đơn hủy. | 536365 | Data Cleaning |
| **StockCode** | String | Mã định danh sản phẩm hoặc dịch vụ. Một số mã đặc biệt (POST, DOT, M, BANK CHARGES...) không đại diện cho sản phẩm. | 85123A | Data Cleaning |
| **Description** | String | Tên sản phẩm. Chỉ dùng để hiển thị và phân tích mô tả sản phẩm. | WHITE HANGING HEART T-LIGHT HOLDER | Dashboard |
| **Quantity** | Integer | Số lượng sản phẩm trong một dòng giao dịch. Giá trị âm thường xuất hiện ở hóa đơn hủy. | 6 | RFM |
| **InvoiceDate** | Datetime | Thời điểm phát sinh giao dịch. Dùng để tính Recency. | 2010-12-01 08:26 | RFM |
| **Price** | Float | Đơn giá của một sản phẩm. | 2.55 | Monetary |
| **Customer ID** | String | Mã định danh khách hàng. Là khóa để gom các giao dịch theo khách hàng khi xây dựng RFM. | 17850 | RFM |
| **Country** | String | Quốc gia của khách hàng. Chủ yếu dùng để thống kê và trực quan hóa. | United Kingdom | Dashboard |

---

### 1.3. Các cột phái sinh sau tiền xử lý

Sau khi tiền xử lý, hệ thống sẽ tạo thêm các cột sau.

| Cột | Kiểu dữ liệu | Công thức | Mục đích |
|------|-------------|-----------|----------|
| **TotalPrice** | Float | Quantity × UnitPrice | Tính Monetary |
| **IsCancelled** | Boolean | InvoiceNo bắt đầu bằng "C" | Đánh dấu hóa đơn hủy |
| **HasCustomerID** | Boolean | CustomerID khác null | Kiểm tra đủ điều kiện tính RFM |
| **IsServiceCode** | Boolean | StockCode thuộc danh sách mã dịch vụ | Loại khỏi Frequency và Monetary |

---

### 1.4. Quy định Data Mapping cho Pipeline

Ứng dụng không yêu cầu người dùng phải sử dụng đúng tên cột của Online Retail II.

Thay vào đó, người dùng sẽ ánh xạ (Mapping) các cột trong file dữ liệu sang cấu trúc chuẩn của hệ thống.

#### Các cột bắt buộc

| Cột chuẩn | Mục đích |
|-----------|----------|----------|
| Invoice | Xác định hóa đơn và hóa đơn hủy |
| StockCode | Xác định sản phẩm |
| Quantity | Tính Frequency và Monetary |
| InvoiceDate | Tính Recency |
| Price | Tính Monetary |
| CustomerID | Gom giao dịch theo khách hàng |

Nếu thiếu bất kỳ cột nào ở trên, hệ thống sẽ không cho phép tiếp tục xử lý.

#### Các cột tùy chọn

| Cột chuẩn | Mục đích |
|-----------|----------|
| Description | Hiển thị tên sản phẩm |
| Country | Phân tích theo quốc gia |

Nếu thiếu hai cột này, hệ thống vẫn có thể thực hiện phân khúc khách hàng.

---

## 2. Schema dữ liệu đầu vào

Bảng dưới đây mô tả cấu trúc chuẩn của bộ dữ liệu **Online Retail II** được sử dụng trong dự án.

| Cột | Kiểu dữ liệu | Bắt buộc  | Ràng buộc |
|------|-------------|----------|-------|-----------|
| Invoice | String | Có | Không được để trống |
| StockCode | String | Có | Không được để trống |
| Description | String | Không | Có thể thiếu |
| Quantity | Integer | Có | Có thể âm đối với hóa đơn hủy |
| InvoiceDate | Datetime | Có | Phải chuyển đổi được sang kiểu Datetime |
| Price | Float | Có | Giá trị ≥ 0 |
| Customer ID | String | Có (đối với RFM) | Có thể thiếu trong dữ liệu gốc |
| Country | String | Không | Có thể thiếu |

## 3. Business Rules

### 3.1. Mục đích

Business Rules quy định cách xử lý các trường hợp đặc biệt trong bộ dữ liệu **Online Retail II**. Đây là bộ quy tắc thống nhất cho toàn bộ dự án, giúp các thành viên xử lý dữ liệu theo cùng một tiêu chuẩn và đảm bảo tính nhất quán trong toàn bộ pipeline.

Các quy tắc dưới đây được áp dụng xuyên suốt từ giai đoạn tiền xử lý dữ liệu đến xây dựng đặc trưng RFM và phân cụm khách hàng.

---

#### BR-01. Hóa đơn hủy (Cancelled Invoice)

| Thuộc tính | Nội dung |
|------------|----------|
| Điều kiện | `Invoice` bắt đầu bằng ký tự **"C"** |
| Hành động | Tạo cột `IsCancelled = True`, **không xóa** khỏi dữ liệu gốc |
| Xử lý ở bước RFM | Loại khỏi quá trình tính Frequency và Monetary |
| Lý do | Đây là giao dịch hoàn trả hoặc hủy đơn, không phản ánh hành vi mua hàng thực tế của khách hàng. Tuy nhiên vẫn cần giữ trong dữ liệu gốc để phục vụ kiểm tra và phân tích. |

---

#### BR-02. Quantity âm

| Thuộc tính | Nội dung |
|------------|----------|
| Điều kiện | `Quantity < 0` |
| Hành động | Giữ nguyên bản ghi, đánh dấu để kiểm tra cùng `IsCancelled` |
| Xử lý ở bước RFM | Chỉ loại nếu là giao dịch hủy |
| Lý do | Phần lớn Quantity âm xuất hiện trong các hóa đơn hủy. Không xem đây là lỗi dữ liệu nếu phù hợp với nghiệp vụ. |

---

#### BR-03. CustomerID bị thiếu

| Thuộc tính | Nội dung |
|------------|----------|
| Điều kiện | `CustomerID` là giá trị null |
| Hành động | Tạo cột `HasCustomerID = False`, không xóa khỏi dữ liệu gốc |
| Xử lý ở bước RFM | Loại khỏi tập dữ liệu dùng để tính RFM |
| Lý do | Không thể xác định khách hàng nên không thể tính Recency, Frequency và Monetary. Tuy nhiên vẫn có thể sử dụng các bản ghi này cho các phân tích khác như doanh thu theo quốc gia. |

---

#### BR-04. Giá bằng 0

| Thuộc tính | Nội dung |
|------------|----------|
| Điều kiện | `UnitPrice = 0` |
| Hành động | Giữ nguyên và đánh dấu |
| Xử lý ở bước RFM | Đánh giá trước khi tính Monetary |
| Lý do | Có thể là hàng khuyến mãi, quà tặng hoặc điều chỉnh kế toán. Không nên loại bỏ ngay khi chưa phân tích nguyên nhân. |

---

#### BR-05. StockCode đặc biệt

| Thuộc tính | Nội dung |
|------------|----------|
| Điều kiện | `StockCode` thuộc các mã như `POST`, `DOT`, `M`, `BANK CHARGES`, `CRUK`,... |
| Hành động | Tạo cột `IsServiceCode = True` |
| Xử lý ở bước RFM | Không sử dụng để tính Frequency và Monetary |
| Lý do | Đây là các mã dịch vụ, phí vận chuyển hoặc điều chỉnh kế toán, không đại diện cho hành vi mua sản phẩm của khách hàng. |

---

#### BR-06. Bản ghi trùng lặp

| Thuộc tính | Nội dung |
|------------|----------|
| Điều kiện | Hai bản ghi giống nhau trên tất cả các cột |
| Hành động | Giữ lại một bản ghi, loại bỏ các bản ghi còn lại |
| Xử lý | Thực hiện trong giai đoạn Data Cleaning |
| Lý do | Đây là lỗi kỹ thuật, không mang ý nghĩa nghiệp vụ. |

---

#### BR-07. InvoiceDate không hợp lệ

| Thuộc tính | Nội dung |
|------------|----------|
| Điều kiện | Không thể chuyển sang kiểu `Datetime` |
| Hành động | Đánh dấu lỗi và loại khỏi tập dữ liệu phân tích nếu không thể khắc phục |
| Lý do | Không thể tính Recency nếu thiếu hoặc sai thời gian giao dịch. |

---

#### BR-08. Giá trị thiếu ở Description

| Thuộc tính | Nội dung |
|------------|----------|
| Điều kiện | `Description` là null |
| Hành động | Giữ nguyên |
| Lý do | Description không được sử dụng trong tính toán RFM và phân cụm. |

---

### 3.2. Nguyên tắc sử dụng Business Rules
- Không tự ý thay đổi Business Rules trong quá trình triển khai.
- Mọi thay đổi phải được Leader xem xét và cập nhật vào tài liệu trước khi áp dụng.
- Data, Model, Pipeline và QA/QC phải sử dụng cùng một phiên bản Business Rules để đảm bảo tính nhất quán của toàn bộ hệ thống.