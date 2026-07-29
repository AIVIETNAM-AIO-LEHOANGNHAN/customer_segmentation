# QA REVIEW — TASK 2 (Data): Module làm sạch dữ liệu

| | |
|---|---|
| **Người review** | Tam Tran (QA/QC) |
| **Ngày** | 29/07/2026 — vòng 2 |
| **Nhánh** | `task2-data-cleaning` |
| **Commit review** | `5cfc434` *fix(qa): resolve data quality issues QA-01 to QA-05* |
| **Đối chiếu** | `docs/T01_data_specification.md` mục 1.3, 2, 3 |
| **Cách tái lập** | `python -m pytest tests/ -v` và `python scripts/run_qa_scenarios.py` (nhánh `feature/task5-qa-data-quality`) |

---

## 1. Kết luận nhanh

**Cảm ơn Data — 5/5 lỗi đã nhận đều được sửa đúng và QA xác nhận bằng test tự động.**

Bộ test dùng `@pytest.mark.xfail(strict=True)`, nên khi chạy lại trên commit `5cfc434`, 6 test đã chuyển sang **XPASS** — tức pytest tự phát hiện "lỗi này đã hết". Đây là bằng chứng máy móc, không phải QA đọc code rồi kết luận bằng mắt.

| Mã | Nội dung | Vòng 1 | Vòng 2 |
|---|---|---|---|
| QA-01 | Sót mã dịch vụ `D`, `S`, `AMAZONFEE`, biến thể `m` | ❌ | ✅ **Đã sửa** *(còn sót `B`, `gift_*` — mục 3)* |
| QA-02 | `Quantity` không ép kiểu số | ❌ | ✅ **Đã sửa** |
| QA-03 | Dòng `InvoiceDate` lỗi bị xoá không gắn cờ | ❌ | ✅ **Đã sửa** |
| QA-04 | `Customer ID` thành `17850.0` | ❌ | ✅ **Đã sửa** |
| QA-05 | Thiếu cột `TotalPrice` | ❌ | ✅ **Đã sửa** |

Nhưng **chưa thể đóng Task 2**: có **1 lỗi mới mức Nghiêm trọng** (QA-13) và 2 hạng mục còn dở. Chi tiết bên dưới.

---

## 2. 🔴 QA-13 (MỚI, Nghiêm trọng) — `cleaned_transactions.csv` chưa được sinh lại

**Đây là việc quan trọng nhất cần làm ngay.**

Code đã sửa, nhưng file kết quả `data/processed/cleaned_transactions.csv` trong repo **vẫn là bản sinh ra trước khi sửa**:

| Kiểm tra | File đang commit | Chạy lại code hiện tại |
|---|---|---|
| Số cột | **12** | **14** |
| Có cột `TotalPrice` | ❌ thiếu | ✅ có |
| Có cột `HasInvalidDate` | ❌ thiếu | ✅ có |
| Mẫu `Customer ID` | **`17850.0`** *(lỗi QA-04 cũ)* | `17850` |
| `IsServiceCode` | **2.730 dòng** | **2.904 dòng** |

Nghĩa là: **QA-04 và QA-05 đã sửa trong code nhưng vẫn còn nguyên trong dữ liệu mà cả nhóm đang dùng.**

### Vì sao nghiêm trọng

Đây không phải vấn đề lý thuyết — nó **đã gây hậu quả thật**:

> **Task 4 (Model) đã chạy toàn bộ phân tích EDA trên chính file cũ này.** Báo cáo `outputs/reports/data_quality_stats.md` lấy `IsServiceCode = 2.730` và kết luận mã dịch vụ đóng góp **+£195.336,86**. Chạy lại trên code đã sửa, con số này là **−£34.916,96** — **đổi cả dấu**, lệch £230.253,82.

Task 4 không sai; họ dùng đúng dữ liệu có trong repo tại thời điểm đó. Nhưng kết luận của họ ở mục 3 giờ phải viết lại.

### Cần làm

```bash
python src/data/cleaning.py
```

Rồi commit lại file kết quả và **báo cho Model biết để chạy lại EDA**.

> 💡 **Đề xuất kèm theo:** thêm `data/processed/` vào `.gitignore` (lỗi QA-10 vòng 1 — file này nặng 60 MB). Dữ liệu sinh lại được bằng một lệnh thì không nên nằm trong Git; mỗi lần chạy lại tạo một diff 536.000 dòng, review PR gần như không thể. Nếu nhóm muốn giữ để tiện chia sẻ, tối thiểu hãy ghi ngày sinh + commit hash vào `data/processed/README.md` để người dùng biết file có còn tươi không.

---

## 3. 🟠 QA-01 (còn lại, Trung bình) — vẫn sót `B` và nhóm `gift_0001_*`

Phần đã sửa rất tốt: thêm `D`, `S`, `AMAZONFEE` và dùng `.str.upper()` nên biến thể chữ thường `m` (Manual) đã bắt được. QA có test riêng xác nhận `.str.upper()` **không** gắn cờ nhầm mã sản phẩm thật (`85123A`, `DCGSSGIRL`, `DCGSSBOY`, `PADS`) — không có regression.

Còn sót:

| StockCode | Description | Số dòng | `TotalPrice` ròng | Đã gắn cờ |
|---|---|---:|---:|---|
| `B` | Adjust bad debt | 3 | **−£11.062,06** | ❌ |
| `gift_0001_*` | Dotcomgiftshop Gift Voucher | 34 | +£685,81 | ❌ |
| | **Tổng** | **37** | **−£10.376,25** | |

`B` đáng chú ý hơn cả: chỉ 3 dòng nhưng ròng −£11.062,06, và **Task 4 độc lập cũng phát hiện đúng mã này** (mục 3.4 báo cáo của họ). Hai vai trò khác nhau, hai phương pháp khác nhau, cùng chỉ ra một chỗ — nên xử lý.

**Đề xuất:**

```python
special_codes = [
    'POST', 'DOT', 'M', 'BANK CHARGES', 'C2', 'ADJUST', 'CRUK',
    'D', 'S', 'AMAZONFEE', 'B',            # bổ sung
]
code = df[stock_code_col].astype(str).str.upper()
df['IsServiceCode'] = code.isin(special_codes) | code.str.startswith('GIFT_')
```

Ghi chú nhỏ: `'ADJUST'` có trong danh sách nhưng **không tồn tại dòng nào** trong dataset (0 dòng). Giữ cũng được, nhưng nên có comment kẻo người sau tưởng đã kiểm chứng.

---

## 4. 🟠 QA-14 (MỚI, Trung bình) — `Quantity` ép kiểu hỏng không có cờ

Cách xử lý hai loại lỗi giống hệt nhau đang **bất đối xứng**:

| Trường hợp | Ép kiểu | Giữ dòng | Có cờ |
|---|---|---|---|
| `InvoiceDate` không parse được | `to_datetime(errors='coerce')` | ✅ | ✅ `HasInvalidDate` |
| `Quantity` không parse được | `to_numeric(errors='coerce')` | ✅ | ❌ **không có** |

Kiểm chứng trên `test_wrong_dtype.csv`: 10 dòng `Quantity = "abc"` được giữ lại (đúng), nhưng lặng lẽ thành `NaN` và **không cột nào ghi nhận**. Xuống Epic 2, `groupby().sum()` sẽ bỏ qua `NaN` mà không báo gì — Monetary của khách đó thiếu một phần, không ai biết.

Chính lý do QA đề nghị gắn cờ cho `InvoiceDate` ở QA-03 cũng áp dụng nguyên vẹn ở đây.

**Đề xuất:** thêm `flag_invalid_quantity()` đối xứng với `flag_invalid_date()`, sinh cột `HasInvalidQuantity`.

> Trên dữ liệu gốc hiện tại, cả `HasInvalidDate` lẫn số dòng `Quantity` NaN đều bằng **0** — nên lỗi này chưa gây thiệt hại. Nó chỉ phát tác khi người dùng upload file thật của họ, đúng kịch bản mà hệ thống được xây để phục vụ.

---

## 5. 🟡 QA-06 (còn mở, Nhẹ) — vẫn là `KeyError`, chưa phải lỗi nghiệp vụ

Thông điệp lỗi đã tốt hơn nhiều nhờ Task 3 (`Missing required column. Expected one of: InvoiceDate`), nhưng vẫn `raise KeyError`. Repo vẫn chưa có `src/data/validation.py` như README mô tả.

Không gấp — UI của Task 3 đã chặn trước ở tầng mapping nên người dùng hiếm khi chạm tới. Ghi nhận để làm gọn ở Giai đoạn 2.

---

## 6. ⚠️ Cần biết: Task 3 đã sửa file `src/data/cleaning.py` của Task 2

Commit `510245c` trên nhánh `task-3-upload-mapping` **đã viết lại 74 dòng trong `src/data/cleaning.py`** để module chấp nhận cả hai bộ tên cột (`Invoice` lẫn `InvoiceNo`, `Price` lẫn `UnitPrice`...) thông qua hàm mới `_first_existing_column()`.

QA đã thử merge — **hiện tại không xung đột**, vì Task 3 nhánh ra từ `develop` sau khi bản sửa của Data đã vào. Nhưng:

- Lần tới Data sửa tiếp `cleaning.py` trên nhánh này, khả năng cao sẽ **xung đột** với bản của Task 3.
- Sau khi merge, bản `cleaning.py` trên `develop` sẽ là **bản của Task 3**, không phải bản Data đang thấy ở đây.

**Đề nghị:** Data và Pipeline thống nhất ai sở hữu file này trước khi ai đó sửa tiếp. Xem thêm QA-16 trong `docs/reviews/qa_review_task3.md` — gốc rễ là lỗi QA-08 (tên cột trong tài liệu lệch với dữ liệu thật) vẫn chưa được Leader chốt.

---

## 7. Việc cần làm

| # | Việc | Mức | Chặn Giai đoạn 2? |
|---|---|---|---|
| 1 | Chạy lại `python src/data/cleaning.py`, commit file mới, **báo Model chạy lại EDA** | 🔴 Nghiêm trọng | **Có** |
| 2 | Bổ sung `B` và tiền tố `gift_` vào `special_codes` | 🟠 Trung bình | Không |
| 3 | Thêm cờ `HasInvalidQuantity` đối xứng với `HasInvalidDate` | 🟠 Trung bình | Không |
| 4 | Thêm `data/processed/` vào `.gitignore` | 🟡 Nhẹ | Không |
| 5 | Thống nhất với Pipeline về quyền sở hữu `cleaning.py` | 🟠 Trung bình | Không |

Sau khi làm xong mục 1–3, chạy:

```bash
python -m pytest tests/ -v
```

Các test `xfail` tương ứng sẽ chuyển thành **XPASS** và pytest báo fail — đó là tín hiệu đúng, nghĩa là lỗi đã hết. Khi đó gỡ marker `@pytest.mark.xfail` khỏi test và báo QA để cập nhật báo cáo.

---

*Báo cáo đầy đủ: `outputs/reports/data_quality_report.md` trên nhánh `feature/task5-qa-data-quality` (KAN-12).*
