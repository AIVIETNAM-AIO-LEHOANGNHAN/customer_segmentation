# Task 6 - Định nghĩa công thức RFM chuẩn và Snapshot Date

---

## 1. Mục tiêu

- Mục tiêu của tài liệu này là xây dựng đặc tả (Specification) thống nhất cho quá trình tính toán ba đặc trưng **Recency (R), Frequency (F) và Monetary (M)** từ bộ dữ liệu Online Retail II.

- Tài liệu này đóng vai trò là tiêu chuẩn để các thành viên Data, Pipeline, Model và QA/QC cùng sử dụng trong các bước tiếp theo, đảm bảo mọi thành phần của hệ thống đều tính toán RFM theo cùng một quy tắc.

- Ngoài việc định nghĩa công thức tính RFM, tài liệu còn quy định **Snapshot Date**, các điều kiện lọc dữ liệu trước khi tính toán và các nguyên tắc xử lý những trường hợp đặc biệt nhằm đảm bảo kết quả phản ánh đúng hành vi mua hàng của khách hàng.

---

## 2. Phạm vi áp dụng

Tài liệu này áp dụng cho:

- Module xây dựng đặc trưng RFM (Task 7)
- Module chuẩn hóa dữ liệu (Task 8)
- Module phân cụm khách hàng (Task 9)
- Toàn bộ hoạt động kiểm thử của QA/QC
- Dashboard trực quan hóa kết quả

---

## 3. Dữ liệu đầu vào

- Dữ liệu đầu vào là tập giao dịch đã hoàn thành Giai đoạn 1.

- Nguồn dữ liệu: `data/processed/cleaned_transactions.csv`

---

## 4. Snapshot Date

### 4.1 Khái niệm

Snapshot Date là thời điểm tham chiếu được sử dụng để tính khoảng thời gian kể từ lần mua cuối cùng của khách hàng.

Recency luôn được tính dựa trên Snapshot Date thay vì thời điểm chạy chương trình nhằm đảm bảo kết quả có thể tái lập (Reproducible).

---

### 4.2 Giá trị sử dụng

Do bộ dữ liệu Online Retail II kết thúc vào ngày **2011-12-09**, nên Snapshot Date được quy định là ngày **2011-12-10**, tức là sau giao dịch cuối cùng đúng 1 ngày.

---

### 4.3 Lý do lựa chọn

Việc lựa chọn Snapshot Date cố định giúp:

- Kết quả RFM không thay đổi giữa các lần chạy
- Dễ kiểm thử
- Dễ tái hiện nghiên cứu
- Đảm bảo toàn bộ nhóm sử dụng cùng một mốc thời gian

---

## 5. Bộ dữ liệu hợp lệ để tính RFM

- Không phải mọi giao dịch trong tập cleaned_transactions đều được sử dụng. Sau quá trình phân tích dữ liệu, các Business Rules sau được áp dụng trước khi tính RFM.

| Điều kiện | Xử lý |
|------------|--------|
| IsCancelled = True | Loại |
| IsServiceCode = True | Loại |
| PriceAnomaly = True | Loại |
| HasCustomerID = False | Loại |
| Các cặp mua–hủy hoàn toàn | Loại |

Sau khi lọc, tập dữ liệu sẵn sàng xây dựng RFM gồm khoảng: 391,151 giao dịch và 4,333 khách hàng

---

### 5.1 Định nghĩa Recency

#### 5.1.1 Khái niệm

- Recency phản ánh khoảng thời gian kể từ lần mua hàng gần nhất của khách hàng đến Snapshot Date. Khách hàng mua càng gần Snapshot Date thì Recency càng nhỏ.

---

#### 5.1.2. Công thức

Recency = Snapshot Date − Ngày mua gần nhất (đơn vị : ngày)


---

### 5.2. Định nghĩa Frequency

#### 5.2.1. Khái niệm

- Frequency phản ánh số lần khách hàng thực hiện mua hàng. Trong dự án này Frequency được tính theo **Số lượng hóa đơn hợp lệ (Invoice) khác nhau của từng khách hàng.** Không tính số dòng giao dịch và số sản phẩm.

---

#### 5.2.2. Công thức

Frequency = COUNT(DISTINCT Invoice)

### 5.3. Định nghĩa Monetary

#### 5.3.1. Khái niệm

- Monetary phản ánh tổng giá trị chi tiêu của khách hàng. Giá trị được tính sau khi đã loại toàn bộ giao dịch không hợp lệ.

---

#### 5.3.2. Công thức

Trước tiên, ta tính: 

TotalPrice = Quantity × Price

Sau đó, ta tính 

Monetary = SUM(TotalPrice)
---


## 6. Đặc trưng đầu ra

- Sau khi tính toán, mỗi khách hàng chỉ còn đúng một bản ghi. Cấu trúc bảng RFM gồm:

| Cột | Kiểu dữ liệu | Ý nghĩa |
|------|-------------|----------|
| CustomerID | String | Mã khách hàng |
| Recency | Integer | Khoảng cách đến lần mua cuối |
| Frequency | Integer | Số hóa đơn hợp lệ |
| Monetary | Float | Tổng giá trị mua hàng |

---

# 10. Các nguyên tắc cần tuân thủ

Trong toàn bộ dự án, việc tính RFM phải tuân thủ các nguyên tắc sau : 

- Snapshot Date luôn cố định.
- Không sử dụng ngày hiện tại của hệ thống.
- Frequency chỉ đếm Invoice hợp lệ.
- Monetary chỉ cộng TotalPrice của giao dịch hợp lệ.
- Mỗi CustomerID chỉ sinh một dòng dữ liệu.
- Không được tự ý thay đổi Business Rules khi tính RFM.
