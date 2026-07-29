# QA REVIEW — TASK 3 (Pipeline): UI Upload & Ánh xạ cột

| | |
|---|---|
| **Người review** | Tam Tran (QA/QC) |
| **Ngày** | 29/07/2026 |
| **Nhánh** | `task-3-upload-mapping` |
| **Commit review** | `510245c` *Implement upload column mapping UI* |
| **Đối chiếu** | `docs/T01_data_specification.md` mục 1.4 (Quy định Data Mapping) + BR-03 |
| **Bộ test** | `tests/test_upload_mapping.py` (18 test, nhánh `feature/task5-qa-data-quality`) |

---

## 1. Kết luận nhanh

**Toàn bộ 6 hạng mục checklist Nhóm C đều ĐẠT.** Đây là lần đầu Nhóm C chạy được — vòng 1 phải bỏ trống vì chưa có mã nguồn.

| # | Hạng mục | Kết quả |
|---|---|---|
| C1 | Mapping tự động khớp đúng cả 8 cột với file gốc | ✅ **8/8** |
| C2 | Mapping thủ công với file đã đổi tên cột | ✅ ĐẠT |
| C3 | **Upload file nhiều `CustomerID` null vẫn được chấp nhận** | ✅ **ĐẠT** |
| C4 | Thiếu cột bắt buộc → chặn, báo lỗi rõ | ✅ ĐẠT |
| C5 | Thiếu cột tùy chọn vẫn cho đi tiếp | ✅ ĐẠT |
| C6 | File sai kiểu dữ liệu không làm sập app | ✅ ĐẠT |

### 👏 Ghi nhận riêng cho C3

Ở vòng 1, QA đã gửi cảnh báo sớm: schema mục 2 ghi `Customer ID` là *"Có (đối với RFM)"*, rất dễ bị hiện thực nhầm thành ràng buộc `NOT NULL` ở bước validate, và sẽ **chặn mất 25,16% dataset (135.037 dòng)** ngay từ cửa.

**Pipeline đã làm đúng.** `validate_mapping()` chỉ kiểm tra cột bắt buộc có **được ánh xạ** hay không, hoàn toàn không đụng tới giá trị bên trong. QA đã chạy `test_missing_customerid.csv` (75/300 dòng null) qua trọn luồng: validate cho qua, làm sạch giữ đủ 300 dòng, gắn cờ đúng 75. Đây là cái bẫy tốn kém nhất của Giai đoạn 1 và nó đã được tránh.

### Điểm cộng ngoài yêu cầu

- `normalize_column_name()` bỏ qua hoa/thường, dấu cách, `_`, `-` → `customer_id`, `Customer-ID`, `CUSTOMERID` đều khớp. Tốt hơn mức đề bài yêu cầu.
- Bắt được cả hai lỗi mapping mà đề bài không nêu: map một cột nguồn cho hai cột chuẩn, và map tới cột không tồn tại.
- `apply_column_mapping()` tự gọi `validate_mapping()` thay vì tin UI đã kiểm — đúng nguyên tắc không tin tầng trên.
- Đọc CSV thử lần lượt `utf-8-sig → utf-8 → latin1`; file Excel nhiều sheet được gộp lại. Với Online Retail II (2 sheet) đây là xử lý đúng.
- `docs/T03_upload_mapping_test_notes.md` — có tài liệu tự kiểm thử, rất đáng khuyến khích.

---

## 2. 🔴 QA-16 (MỚI, Nghiêm trọng) — Hai luồng chạy cho ra hai schema khác nhau

**Đây là vấn đề duy nhất cần xử lý gấp.**

Hệ thống hiện có hai đường sinh ra dữ liệu sạch, và chúng cho **bộ tên cột khác nhau**:

| | Luồng batch<br>`python src/data/cleaning.py` | Luồng UI<br>upload → mapping → clean |
|---|---|---|
| Mã hóa đơn | `Invoice` | **`InvoiceNo`** |
| Đơn giá | `Price` | **`UnitPrice`** |
| Mã khách | `Customer ID` | **`CustomerID`** |
| Tên file xuất | `cleaned_transactions.csv` | `cleaned_transactions.csv` |

Nguyên nhân: `STANDARD_COLUMNS` trong `column_mapper.py` dùng bộ tên của **Online Retail I** (`InvoiceNo`/`UnitPrice`/`CustomerID`), trong khi dữ liệu thật và module làm sạch dùng `Invoice`/`Price`/`Customer ID`.

### Vì sao nghiêm trọng

Epic 2 (Model) sẽ viết `rfm.groupby("Customer ID")`. Code đó **chạy được với file batch, hỏng với file tải từ UI** — và ngược lại. Cùng một tên file, hai cấu trúc. Lỗi sẽ xuất hiện dưới dạng `KeyError` ngẫu nhiên tùy người dùng lấy file từ đâu, rất tốn thời gian truy vết.

Hàm `_first_existing_column()` mà Pipeline thêm vào `cleaning.py` khiến **module làm sạch** chịu được cả hai tên — nhưng nó không giải quyết được việc **file xuất ra** vẫn mang hai schema. Mọi module hạ nguồn (RFM, phân cụm, dashboard, export CSV) sẽ phải lặp lại đúng thủ thuật đó ở từng chỗ.

### Đề xuất

Chốt **một** bộ tên chuẩn cho toàn hệ thống — QA đề nghị lấy theo dữ liệu thật (`Invoice`, `Price`, `Customer ID`), vì đó là thứ không sửa được:

```python
STANDARD_COLUMNS = [
    "Invoice", "StockCode", "Description", "Quantity",
    "InvoiceDate", "Price", "Customer ID", "Country",
]
```

`DEFAULT_COLUMN_ALIASES` giữ nguyên cả hai tên làm alias để người dùng upload file kiểu nào cũng khớp — phần đó Pipeline đã làm đúng rồi, chỉ cần đổi **đích** của phép ánh xạ.

> Đây là biểu hiện của lỗi **QA-08** vòng 1 (tài liệu dùng `InvoiceNo`/`UnitPrice`/`CustomerID`, dữ liệu thật dùng `Invoice`/`Price`/`Customer ID`) mà Leader chưa chốt. Pipeline code theo tài liệu là hợp lý — nhưng tài liệu đang sai so với dữ liệu. **Cần Leader quyết trước, Pipeline sửa sau**, kẻo sửa xong lại phải đổi lần nữa.

---

## 3. 🟠 QA-15 (MỚI, Trung bình) — Task 3 sửa file thuộc sở hữu của Task 2

Commit `510245c` sửa **74 dòng trong `src/data/cleaning.py`** — deliverable của Task 2 (Data).

Về kỹ thuật, bản sửa tốt: `_first_existing_column()` gọn, có thông điệp lỗi rõ, và còn tiện tay bổ sung ép kiểu cho `Price` (Data mới chỉ làm cho `Quantity`).

Về quy trình thì có rủi ro:

- QA đã thử merge cả `task-3-upload-mapping` và `task4-eda` vào `develop` — **hiện không xung đột**, vì Task 3 nhánh ra từ `develop` sau khi bản sửa của Data đã vào. Không cần lo ngay.
- Nhưng sau khi merge, bản `cleaning.py` trên `develop` là **bản của Pipeline**, không phải bản Data đang thấy trên nhánh của họ. Lần tới Data sửa tiếp file này, khả năng cao sẽ xung đột.

**Đề nghị:** báo Data biết (QA đã ghi việc này trong `docs/reviews/qa_review_task2.md`) và thống nhất ai sở hữu `cleaning.py`. Nếu Pipeline cần module chịu được nhiều tên cột, cách sạch hơn là đặt lớp chuẩn hoá ở `src/app/` và giữ `cleaning.py` chỉ nhận đúng một schema.

---

## 4. 🟡 Ghi chú nhỏ — không chặn

**N1. `Description` bị ép thành cột bắt buộc trên thực tế.**
`REQUIRED_COLUMNS` khai báo đúng (`Description` là tùy chọn) và QA đã xác nhận C5 ĐẠT. Nhưng `caption` ở `Home.py` liệt kê required/optional bằng chuỗi viết tay, dễ lệch khỏi hằng số khi ai đó sửa. Nên dựng caption từ chính `REQUIRED_COLUMNS`/`OPTIONAL_COLUMNS`.

**N2. Excel nhiều sheet gộp bằng `pd.concat` không kiểm cấu trúc.**
Nếu hai sheet có tập cột khác nhau, `concat` sẽ tạo cột `NaN` lặng lẽ thay vì báo lỗi. Với Online Retail II (2 sheet cùng cấu trúc) thì không sao, nhưng nên cảnh báo khi tập cột giữa các sheet không khớp.

**N3. Thiếu giới hạn kích thước file.**
File 1 triệu dòng đọc thẳng vào RAM hai lần (`read_uploaded_columns` rồi `read_uploaded_dataframe`). Nên cân nhắc `st.cache_data` hoặc cảnh báo khi file quá lớn.

**N4. `requirements.txt`** — cảm ơn Pipeline đã thêm 3 dòng đầu tiên (lỗi QA-09 vòng 1 là file rỗng hoàn toàn). Vẫn còn thiếu `pytest` và các thư viện của Epic 3 (`scikit-learn`, `hdbscan`, `plotly`).

---

## 5. Việc cần làm

| # | Việc | Mức | Chặn Giai đoạn 2? |
|---|---|---|---|
| 1 | **Chờ Leader chốt bộ tên cột chuẩn**, rồi sửa `STANDARD_COLUMNS` để hai luồng cùng schema (QA-16) | 🔴 Nghiêm trọng | **Có** |
| 2 | Thống nhất với Data quyền sở hữu `src/data/cleaning.py` (QA-15) | 🟠 Trung bình | Không |
| 3 | Dựng caption required/optional từ hằng số thay vì viết tay | 🟡 Nhẹ | Không |
| 4 | Cảnh báo khi các sheet Excel lệch cấu trúc | 🟡 Nhẹ | Không |
| 5 | Bổ sung `pytest` và thư viện Epic 3 vào `requirements.txt` | 🟡 Nhẹ | Không |

Chạy lại kiểm thử Nhóm C bất cứ lúc nào:

```bash
python -m pytest tests/test_upload_mapping.py -v
```

---

*Báo cáo đầy đủ: `outputs/reports/data_quality_report.md` trên nhánh `feature/task5-qa-data-quality` (KAN-12).*
