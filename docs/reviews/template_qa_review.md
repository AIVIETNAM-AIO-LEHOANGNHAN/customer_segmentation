# Báo cáo kiểm thử QA/QC

> **Mục đích:** Báo cáo kết quả kiểm thử sau khi hoàn thành một Task, giúp Leader nhanh chóng đánh giá chất lượng sản phẩm, mức độ đáp ứng yêu cầu và đưa ra quyết định nghiệm thu hoặc yêu cầu chỉnh sửa.

---

## 1. Thông tin chung

| Thuộc tính | Nội dung |
|------------|----------|
| Epic | |
| Task | |
| Ngày kiểm thử | |

---

## 2. Tóm tắt kết quả kiểm thử

### 2.1. Kết quả tổng quan

| Chỉ số | Kết quả |
|---------|----------|
| Tổng số tiêu chí kiểm thử | |
| Đạt | |
| Không đạt | |
| Tỷ lệ đạt | |
| Critical Bugs | |
| Major Bugs | |
| Minor Bugs | |

---

### 2.2. Nhận xét nhanh

> Tóm tắt ngắn gọn chất lượng của Task sau kiểm thử (khoảng 3–5 dòng). Nêu rõ mức độ hoàn thành, số lượng lỗi quan trọng (nếu có) và đánh giá tổng quan để Leader nắm được tình trạng hiện tại mà không cần đọc toàn bộ báo cáo.

---

### 3. Kết quả theo từng nhóm kiểm thử

| Nhóm kiểm thử | Kết quả | Nhận xét |
|---------------|----------|-----------|
| Kiểm thử dữ liệu đầu vào | ✅ / ❌ | |
| Kiểm thử chức năng chính | ✅ / ❌ | |
| Kiểm thử Business Rules | ✅ / ❌ | |
| Kiểm thử dữ liệu đầu ra | ✅ / ❌ | |
| Kiểm thử tính nhất quán | ✅ / ❌ | |
| Kiểm thử hiệu năng | ✅ / ❌ | |

---

### 4. Danh sách lỗi phát hiện

| ID | Mức độ | Mô tả lỗi | Trạng thái |
|----|---------|-----------|------------|
| BUG-001 | Critical / Major / Minor | | Open / Fixed |
| BUG-002 | Critical / Major / Minor | | Open / Fixed |

> Nếu không phát hiện lỗi, ghi rõ: **Không phát hiện lỗi.**

> Minh chứng lỗi : Kết quả code pytest hoặc kết quả review thủ công rõ ràng

---

### 5. Đánh giá chất lượng

| Tiêu chí | Kết quả |
|-----------|----------|
| Đúng yêu cầu nghiệp vụ | ✅ / ❌ |
| Đúng Business Rules | ✅ / ❌ |
| Dữ liệu đầu ra hợp lệ | ✅ / ❌ |
| Đủ điều kiện cho Task tiếp theo | ✅ / ❌ |

---

### 6. Kết luận

#### 6.1. Đánh giá

> Tóm tắt ngắn gọn kết quả kiểm thử, nêu rõ Task đã đáp ứng yêu cầu hay chưa và các vấn đề còn tồn tại (nếu có).

#### 6.2. Kiến nghị

- ✅ Nghiệm thu và chuyển sang Task tiếp theo.
- ⚠️ Cần chỉnh sửa trước khi nghiệm thu.
- ❌ Chưa đủ điều kiện chuyển sang giai đoạn tiếp theo.

---