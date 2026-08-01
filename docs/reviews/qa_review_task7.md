# Báo cáo kiểm thử QA/QC

> **Mục đích:** Báo cáo kết quả kiểm thử Task 7 nhằm xác nhận module tính toán Recency, Frequency và Monetary hoạt động đúng theo tài liệu thiết kế (Task 6), đáp ứng đầy đủ Business Rules và sẵn sàng chuyển sang bước chuẩn hóa dữ liệu (Task 8).

---

# 1. Thông tin chung

| Thuộc tính | Nội dung |
|------------|----------|
| Epic | Epic 2 – Xây dựng đặc trưng RFM |
| Task | Task 7 – Xây dựng module tính toán RFM |
| Người kiểm thử | Leader |
| Ngày kiểm thử | 01/08/2026 |

---

# 2. Tóm tắt kết quả kiểm thử

## 2.1. Kết quả tổng quan

| Chỉ số | Kết quả |
|---------|----------|
| Tổng số nhóm kiểm thử | 5 |
| Đạt | 5 |
| Không đạt | 0 |
| Tỷ lệ đạt | 100% |
| Critical Bugs | 0 |
| Major Bugs | 0 |
| Minor Bugs | 0 |

**5 nhóm kiểm thử bao gồm:**
- Kiểm thử dữ liệu đầu vào
- Kiểm thử công thức tính RFM
- Kiểm thử business rules
- Kiểm thử dữ liệu đầu ra
- Kiểm thử tính nhất quán
---

## 2.2. Nhận xét nhanh

Module tính toán RFM hoạt động đúng theo đặc tả đã ban hành. Dữ liệu đầu vào đáp ứng đầy đủ Business Rules, công thức tính Recency, Frequency và Monetary chính xác trên các bộ dữ liệu kiểm thử. Kết quả đầu ra hợp lệ, ổn định giữa nhiều lần thực thi và đủ điều kiện sử dụng cho bước chuẩn hóa dữ liệu trong Task 8.

---

# 3. Kết quả theo từng nhóm kiểm thử

## 3.1. Kiểm thử dữ liệu đầu vào

| STT | Tiêu chí kiểm thử | Kết quả | Nhận xét |
|-----|-------------------|----------|-----------|
| 1 | Dữ liệu đầu vào đúng Data Schema | ✅ PASS | |
| 2 | Đầy đủ các cột bắt buộc | ✅ PASS | |
| 3 | Kiểu dữ liệu của các cột chính chính xác | ✅ PASS | |
| 4 | Dữ liệu đã được xử lý theo Business Rules của Giai đoạn 1 | ✅ PASS | |
| 5 | Không phát hiện dữ liệu đầu vào bất thường ảnh hưởng đến việc tính RFM | ✅ PASS | |

---

## 3.2. Kiểm thử công thức tính RFM

| STT | Tiêu chí kiểm thử | Kết quả | Nhận xét |
|-----|-------------------|----------|-----------|
| 1 | Công thức tính Recency đúng theo tài liệu thiết kế | ✅ PASS | |
| 2 | Công thức tính Frequency đúng theo tài liệu thiết kế | ✅ PASS | |
| 3 | Công thức tính Monetary đúng theo tài liệu thiết kế | ✅ PASS | |
| 4 | Kết quả tính toán khớp với phép tính thủ công trên dữ liệu mẫu | ✅ PASS | |
| 5 | Các trường hợp đặc biệt được tính đúng (1 hóa đơn, nhiều hóa đơn, nhiều dòng cùng hóa đơn...) | ✅ PASS | |

---

## 3.3. Kiểm thử Business Rules

| STT | Tiêu chí kiểm thử | Kết quả | Nhận xét |
|-----|-------------------|----------|-----------|
| 1 | Giao dịch hủy (IsCancelled) không được đưa vào RFM | ✅ PASS | |
| 2 | Các mã dịch vụ (IsServiceCode) không được tính vào RFM | ✅ PASS | |
| 3 | Các giao dịch Price Anomaly được loại bỏ đúng quy định | ✅ PASS | |
| 4 | Các bản ghi thiếu CustomerID không xuất hiện trong kết quả RFM | ✅ PASS | |
| 5 | Các cặp giao dịch mua – hủy được xử lý đúng theo Business Rules | ✅ PASS | |

---

## 3.4. Kiểm thử dữ liệu đầu ra

| STT | Tiêu chí kiểm thử | Kết quả | Nhận xét |
|-----|-------------------|----------|-----------|
| 1 | Mỗi CustomerID chỉ xuất hiện một lần | ✅ PASS | |
| 2 | Không còn giá trị thiếu (NULL) | ✅ PASS | |
| 3 | Giá trị Recency luôn ≥ 0 | ✅ PASS | |
| 4 | Giá trị Frequency luôn > 0 | ✅ PASS | |
| 5 | Giá trị Monetary luôn > 0 | ✅ PASS | |
| 6 | Số lượng khách hàng đúng với kỳ vọng | ✅ PASS | |

---

## 3.5. Kiểm thử tính nhất quán

| STT | Tiêu chí kiểm thử | Kết quả | Nhận xét |
|-----|-------------------|----------|-----------|
| 1 | Chạy module nhiều lần với cùng dữ liệu đầu vào | ✅ PASS | |
| 2 | Kết quả giữa các lần chạy hoàn toàn giống nhau | ✅ PASS | |
| 3 | Thay đổi thứ tự dữ liệu đầu vào không làm thay đổi kết quả | ✅ PASS | |
| 4 | Module hoạt động ổn định, không phát sinh lỗi khi thực thi lặp lại | ✅ PASS | |
---

# 4. Danh sách lỗi phát hiện

**Không phát hiện lỗi.**

### Minh chứng

- Toàn bộ testcase Pytest đều PASS. Chi tiết xin tái lập tại `tests/T10_1_test_task_7/`
- Kết quả đối chiếu thủ công khớp với công thức RFM.

---

# 5. Đánh giá chất lượng

| Tiêu chí | Kết quả |
|-----------|----------|
| Đúng yêu cầu nghiệp vụ | ✅ PASS |
| Đúng Business Rules | ✅ PASS |
| Dữ liệu đầu ra hợp lệ | ✅ PASS |
| Đủ điều kiện cho Task tiếp theo | ✅ PASS |

---

# 6. Kết luận

## 6.1. Đánh giá

Module tính toán RFM đáp ứng đầy đủ các yêu cầu của tài liệu thiết kế. Kết quả kiểm thử cho thấy công thức tính toán chính xác, Business Rules được áp dụng đầy đủ và dữ liệu đầu ra đảm bảo chất lượng để phục vụ các bước chuẩn hóa và phân cụm khách hàng.

Không phát hiện lỗi ở mức Critical, Major hoặc Minor trong quá trình kiểm thử.

---

## 6.2. Kiến nghị

- ✅ Nghiệm thu Task 7.
- ✅ Chuyển sang Task 8 – Chuẩn hóa dữ liệu RFM (Transformation & Scaling).