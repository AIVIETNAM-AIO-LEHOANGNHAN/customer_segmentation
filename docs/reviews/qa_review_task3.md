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

## 4. Lỗi biên phát hiện ở vòng soi sâu (29/07/2026)

Sau khi checklist Nhóm C đã qua hết, QA soi tiếp các tình huống dữ liệu bất thường mà người dùng thật dễ tạo ra. Tất cả đều đã được viết thành test và tái hiện được.

### 🔴 T3-02 (Nghiêm trọng) — Đổi tên cột có thể tạo hai cột trùng tên, làm vỡ ứng dụng

`apply_column_mapping()` chỉ gọi `df.rename()`, không kiểm tra tên đích có trùng cột đã có sẵn không. `validate_mapping()` cũng không bắt được.

Kịch bản rất dễ gặp — file của khách có cả `UnitPrice` (giá niêm yết) lẫn `Price` (giá thực trả):

```python
df["UnitPrice"] = df["Price"] * 1.2
m = build_default_mapping(list(df.columns))   # tự động chọn UnitPrice
m["UnitPrice"] = "Price"                      # người dùng sửa tay sang giá thực trả
validate_mapping(m, list(df.columns)).is_valid   # -> True, KHÔNG cảnh báo
list(apply_column_mapping(df, m).columns)
# -> [..., 'UnitPrice', ..., 'UnitPrice']  HAI CỘT CÙNG TÊN
```

Từ đó `df["UnitPrice"]` trả về DataFrame chứ không phải Series, và người dùng nhận thông báo vô nghĩa:

> `Cannot process file: arg must be a list, tuple, 1-d array, or Series`

**Đề xuất:** chỉ giữ các cột được ánh xạ rồi kiểm tra trùng tên — xử lý luôn cả T3-06.

```python
result = df[list(rename_dict.keys())].rename(columns=rename_dict)
duplicated = result.columns[result.columns.duplicated()].unique().tolist()
if duplicated:
    raise ValueError(f"Ánh xạ tạo ra cột trùng tên: {', '.join(duplicated)}.")
```

### 🟠 T3-03 (Trung bình) — Fallback `latin1` nuốt lỗi bảng mã

`CSV_ENCODINGS` thử `utf-8-sig → utf-8 → latin1`. Vấn đề ở bước cuối: **`latin1` giải mã được mọi chuỗi byte nên không bao giờ raise**. File UTF-16 (Excel bản cũ, phần mềm kế toán hay xuất) được đọc thành cột rác mà không có lỗi nào:

```
read_uploaded_columns(buf, 'utf16.csv')
-> ['ÿþI', 'Unnamed: 1', 'Unnamed: 2', ...]
```

Người dùng thấy danh sách cột toàn ký tự lạ, mọi ô mapping đều trống, không có gì giải thích.

**Đề xuất:** thêm `utf-16` và `cp1258` vào danh sách thử trước `latin1`, và kiểm tra kết quả đọc có hợp lý không (tên cột phần lớn là chữ/số, không đầy `Unnamed:`) trước khi chấp nhận.

### 🟠 T3-04 (Trung bình) — Hai cột chuẩn hoá trùng key, một cột bị bỏ âm thầm

`normalized_source` là dict comprehension nên khi hai cột chuẩn hoá về cùng khoá, cột sau đè cột trước:

```python
df = df.rename(columns={"Customer ID": "customer_id"})
df["Customer-ID"] = 999                      # cột rác thêm sau
build_default_mapping(list(df.columns))["CustomerID"]
# -> 'Customer-ID'   chọn nhầm cột rác, validate vẫn báo hợp lệ
```

Toàn bộ mã khách hàng bị lấy sai. Kết quả phân cụm vẫn ra một bảng đẹp nhưng gán sai khách — loại lỗi nguy hiểm nhất vì không có dấu hiệu phát hiện.

**Đề xuất:** ghi nhận khoá nhập nhằng thay vì ghi đè, để trống ô mapping và yêu cầu người dùng chọn tay.

### 🟠 T3-05 (Trung bình) — Excel gộp mọi sheet không kiểm cấu trúc

Hai sheet lệch cột → `pd.concat` sinh cột mới và điền `NaN`, không cảnh báo. Sheet phụ không phải dữ liệu (`Ghi chú`, `Hướng dẫn`) cũng bị trộn vào dữ liệu giao dịch:

```
sheet 'Y2010' (có Country, Price) + sheet 'Y2011' (thiếu Country, tên cột UnitPrice)
-> shape (10, 9), sinh thêm cột UnitPrice và 10 ô NaN, không cảnh báo

file có sheet phụ 'Ghi chu'
-> shape (6, 9), thêm 1 dòng rác + 1 cột rác vào dữ liệu giao dịch
```

**Đề xuất:** so tập cột giữa các sheet, lệch thì báo lỗi nêu rõ sheet nào; hoặc cho người dùng chọn sheet cần nạp.

### 🟡 T3-06 (Nhẹ) — Cột không được ánh xạ vẫn lọt vào dữ liệu sạch

`df.rename()` giữ nguyên mọi cột không map, nên cột rác đi thẳng ra file kết quả. Nguy hiểm hơn: cột trùng tên với cột phái sinh của Task 2 (`IsCancelled`, `TotalPrice`...) bị ghi đè âm thầm. Sửa T3-02 theo đề xuất trên là lỗi này tự hết.

### 🟡 T3-07 (Nhẹ) — File chỉ có header vẫn báo thành công

File CSV 0 dòng dữ liệu đi hết luồng, giao diện hiện `Processed 0 rows.` màu xanh như một lần chạy thành công. Nên chặn ngay sau `read_uploaded_dataframe()`:

```python
if raw_df.empty:
    st.error("File không có dòng dữ liệu nào. Vui lòng kiểm tra lại.")
    return
```

### 🟡 T3-09 (Nhẹ) — Caption viết tay dễ lệch khỏi hằng số

`st.caption` ở `Home.py` liệt kê cột bắt buộc/tùy chọn bằng chuỗi viết tay trong khi `REQUIRED_COLUMNS` và `OPTIONAL_COLUMNS` đã có sẵn. Nếu sửa T3-01 mà quên sửa chuỗi này, giao diện sẽ hướng dẫn tên cột cũ.

### Ghi chú thêm

- **Đọc file hai lần vào RAM** — `read_uploaded_columns()` rồi `read_uploaded_dataframe()`. Với file 1 triệu dòng nên cân nhắc `st.cache_data`.
- **`requirements.txt`** — cảm ơn Pipeline đã thêm 3 dòng đầu tiên (vòng 1 file rỗng hoàn toàn), và đã nhớ `openpyxl` cho phần đọc Excel. Còn thiếu `pytest` và thư viện Epic 3 (`scikit-learn`, `hdbscan`, `plotly`).

---

## 5. Việc cần làm

| # | Việc | Lỗi | Mức | Chặn Giai đoạn 2? |
|---|---|---|---|---|
| 1 | **Chờ Leader chốt bộ tên cột chuẩn**, rồi sửa `STANDARD_COLUMNS` | QA-16 / T3-01 | 🔴 Nghiêm trọng | **Có** |
| 2 | Chỉ giữ cột được ánh xạ + chặn trùng tên cột | T3-02, T3-06 | 🔴 Nghiêm trọng | **Có** |
| 3 | Kiểm cấu trúc các sheet Excel trước khi gộp | T3-05 | 🟠 Trung bình | Không |
| 4 | Bổ sung `utf-16`/`cp1258` + kiểm tra kết quả đọc | T3-03 | 🟠 Trung bình | Không |
| 5 | Phát hiện tên cột nhập nhằng sau chuẩn hoá | T3-04 | 🟠 Trung bình | Không |
| 6 | Thống nhất với Data quyền sở hữu `cleaning.py` | QA-15 / T3-08 | 🟠 Trung bình | Không |
| 7 | Chặn file 0 dòng | T3-07 | 🟡 Nhẹ | Không |
| 8 | Dựng caption từ hằng số | T3-09 | 🟡 Nhẹ | Không |
| 9 | Bổ sung `pytest` + thư viện Epic 3 vào `requirements.txt` | QA-09 | 🟡 Nhẹ | Không |

Chạy lại kiểm thử Nhóm C bất cứ lúc nào:

```bash
python -m pytest tests/test_upload_mapping.py -v
```

Hiện tại: **18 PASSED, 6 XFAIL**. `XFAIL` = lỗi đã ghi nhận, chưa sửa. Khi bạn sửa xong, test chuyển thành `XPASS` và pytest báo fail để nhắc gỡ marker `@pytest.mark.xfail` — rồi báo QA cập nhật báo cáo.

> 📄 **Bản đầy đủ dạng Word** (14 trang, có ảnh chụp lỗi, code tái hiện và code sửa cho từng lỗi): `BAO_CAO_LOI_TASK3_Upload_Mapping.docx` — QA gửi kèm trong Jira KAN-12.

---

*Báo cáo đầy đủ: `outputs/reports/data_quality_report.md` trên nhánh `feature/task5-qa-data-quality` (KAN-12).*
