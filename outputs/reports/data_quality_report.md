# BÁO CÁO CHẤT LƯỢNG DỮ LIỆU — CUỐI GIAI ĐOẠN 1

| | |
|---|---|
| **Task** | KAN-12 — Task 5: Kiểm thử dữ liệu đầu vào và báo cáo chất lượng dữ liệu |
| **Epic** | KAN-4 — Giai đoạn 1: Khám phá, Làm sạch & Chuẩn hóa dữ liệu |
| **Vai trò** | QA/QC |
| **Người thực hiện** | Tam Tran |
| **Ngày** | 27/07/2026 |
| **Đối tượng kiểm thử** | `src/data/cleaning.py` (Task 2) @ `b52a0b3` — nhánh `task2-data-cleaning` |
| **Căn cứ đối chiếu** | `docs/T01_data_specification.md` mục 1.3, 2, 3 (BR-01 → BR-08) |

---

## 1. Tóm tắt cho Leader

Module làm sạch của Task 2 **giữ đúng nguyên tắc cốt lõi "gắn cờ, không xoá vội"** trên cả 4 trường hợp đặc thù nhạy cảm nhất của Online Retail II. Đây là điều đáng ghi nhận — đây chính là chỗ dễ sai nhất và Data đã làm đúng:

- `Customer ID` null → **giữ dòng**, gắn cờ `HasCustomerID = False` ✅
- Hóa đơn hủy (`C…`) → **giữ dòng**, gắn cờ `IsCancelled = True` ✅
- Mã dịch vụ (`POST`, `DOT`…) → **giữ dòng**, gắn cờ `IsServiceCode = True` ✅
- `Price = 0` → **giữ dòng**, gắn cờ `PriceAnomaly = True` ✅

Toàn bộ 536.642 dòng sau xử lý tái lập được 100% khi QA chạy lại (mục 4).

**Tuy nhiên, chưa thể đóng Giai đoạn 1.** Phát hiện **12 vấn đề**, trong đó **4 vấn đề mức Nghiêm trọng phải xử lý trước khi sang Giai đoạn 2** — cả 4 đều làm hỏng dữ liệu đầu vào của bước tính RFM chứ không phải lỗi hiển thị.

| Mức độ | Mã | Số lượng | Yêu cầu |
|---|---|---|---|
| 🔴 **Nghiêm trọng** | QA-02, QA-03, QA-04, QA-07 | 4 | Phải fix trước khi sang Giai đoạn 2 |
| 🟠 **Trung bình** | QA-01, QA-05, QA-08, QA-09 | 4 | Fix trong Giai đoạn 2, cần ghi nhận ngay |
| 🟡 **Nhẹ** | QA-06, QA-10, QA-11, QA-12 | 4 | Cải thiện sau |

**Kết quả kiểm thử tự động:** 23 tiêu chí — **16 ĐẠT / 7 KHÔNG ĐẠT**. Chi tiết: [`qa_test_results.md`](qa_test_results.md).

**Hạng mục chưa thực thi được:** toàn bộ Nhóm C (UI upload & mapping — Task 3) vì Task 3 chưa có mã nguồn. Xem mục 6.

---

## 2. Phạm vi đã kiểm thử

| Bước (theo KAN-12) | Trạng thái |
|---|---|
| Bước 1 — Đọc đặc tả, chốt "đáp án đúng" | ✅ Hoàn thành |
| Bước 2 — Xây checklist 2 nhóm | ✅ Hoàn thành — [`docs/qa_checklist_data.md`](../../docs/qa_checklist_data.md) |
| Bước 3 — Chuẩn bị 7 file test lỗi cố ý | ✅ Hoàn thành — `data/test_samples/` |
| Bước 4 — Chạy toàn bộ luồng với từng file test | ⚠️ Chạy được phần **làm sạch**; phần **upload → mapping** bị chặn (Task 3 chưa có) |
| Bước 5 — Test riêng UI mapping | ⛔ **Chưa thực thi được** — xem mục 6 |
| Bước 6 — Đối chiếu số liệu với Task 2 | ✅ Hoàn thành — mục 4 |
| Bước 7 — Viết báo cáo, phân loại theo mức ưu tiên | ✅ Tài liệu này |

**Môi trường:** Python 3.13.14, pandas 2.3.0, numpy 2.3.1, pytest 9.1.1, Windows 10.

---

## 3. Bảng đối chiếu kết quả test (kỳ vọng vs thực tế)

Sinh tự động bằng `python scripts/run_qa_scenarios.py`.

| File test | Business Rule | Tiêu chí | Kỳ vọng | Thực tế | Kết luận |
|---|---|---|---|---|---|
| `base_sample.csv` | Schema 1.3 | Không mất dòng trên dữ liệu sạch | 300 dòng | 300 dòng | ✅ |
| `base_sample.csv` | Schema 1.3 | Đủ 4 cột phái sinh | 4 cột | 3 cột | ❌ QA-05 |
| `base_sample.csv` | Schema 1.3 | Có cột `TotalPrice` | có | thiếu | ❌ QA-05 |
| `base_sample.csv` | Schema 2 | `InvoiceDate` là datetime | `datetime64` | `datetime64[ns]` | ✅ |
| `base_sample.csv` | Schema 2 | `Price` là numeric | float | `float64` | ✅ |
| `test_missing_customerid.csv` | BR-03 | Dòng `Customer ID` null còn tồn tại | 300 dòng | 300 dòng | ✅ |
| `test_missing_customerid.csv` | BR-03 | `HasCustomerID = False` được gắn cờ | 75 dòng | 75 dòng | ✅ |
| `test_missing_customerid.csv` | Mục 1.2 | `Customer ID` giữ đúng định dạng | 0 mã lệch | **225/225 mã thành `17850.0`** | ❌ QA-04 |
| `test_cancelled_invoice.csv` | BR-01 | Hóa đơn hủy không bị xoá | 320 dòng | 320 dòng | ✅ |
| `test_cancelled_invoice.csv` | BR-01 | `IsCancelled = True` được gắn cờ | 20 dòng | 20 dòng | ✅ |
| `test_cancelled_invoice.csv` | BR-02 | `Quantity` âm được giữ lại | 20 dòng | 20 dòng | ✅ |
| `test_service_code.csv` | BR-05 | Dòng mã dịch vụ không bị xoá | 312 dòng | 312 dòng | ✅ |
| `test_service_code.csv` | BR-05 | Gắn cờ `IsServiceCode` đầy đủ | 12 dòng | **8 dòng** | ❌ QA-01 |
| `test_service_code.csv` | BR-05 | Không sót mã nào | sót 0 | **sót 4: `AMAZONFEE`, `D`, `S`, `m`** | ❌ QA-01 |
| `test_zero_price.csv` | BR-04 | Dòng `Price = 0` không bị xoá | 300 dòng | 300 dòng | ✅ |
| `test_zero_price.csv` | BR-04 | Được gắn cờ giá bất thường | 15 dòng | 15 dòng | ✅ |
| `test_missing_column.csv` | Mục 1.4 | Chặn xử lý khi thiếu cột bắt buộc | báo lỗi & dừng | dừng bằng `KeyError` | ✅ |
| `test_missing_column.csv` | Mục 1.4 | Thông báo lỗi rõ ràng | nêu rõ cột thiếu | `KeyError: 'InvoiceDate'` | ⚠️ QA-06 |
| `test_wrong_dtype.csv` | — | Không crash khi sai kiểu | không crash | không crash | ✅ |
| `test_wrong_dtype.csv` | Schema 2 | `Quantity` sau xử lý là kiểu số | numeric | **`object`** | ❌ QA-02 |
| `test_wrong_dtype.csv` | Schema 2 | `InvoiceDate` sau xử lý là datetime | `datetime64` | `datetime64[ns]` | ✅ |
| `test_wrong_dtype.csv` | BR-07 | Ngày sai được gắn cờ, không xoá âm thầm | 0 dòng xoá không cờ | **5 dòng bị xoá, không cờ** | ❌ QA-03 |
| `test_duplicate.csv` | BR-06 | Duplicate bị loại, giữ 1 bản ghi | 300 dòng | 300 dòng | ✅ |

---

## 4. Đối chiếu số liệu với báo cáo của Data (Bước 6)

QA nạp lại `data/raw/online_retail_II.csv`, chạy lại `clean_pipeline()` và so với file `data/processed/cleaned_transactions.csv` mà Data đã commit.

| Chỉ số | Data commit | QA chạy lại | Chênh lệch |
|---|---|---|---|
| Số dòng thô ban đầu | 541.910 | 541.910 | — |
| Số dòng sau làm sạch | 536.642 | 536.642 | **Khớp** |
| Số dòng bị loại (duplicate) | 5.268 | 5.268 | **Khớp** |
| Số cột | 12 | 12 | **Khớp** |
| `IsCancelled = True` | 9.251 (1,72%) | 9.251 | **Khớp** |
| `HasCustomerID = False` | 135.037 (25,16%) | 135.037 | **Khớp** |
| `IsServiceCode = True` | 2.730 (0,51%) | 2.730 | **Khớp** |
| `PriceAnomaly = True` | 2.512 (0,47%) | 2.512 | **Khớp** |

**Kết luận:** không có chênh lệch bất thường. Pipeline **tái lập được hoàn toàn** — chạy lại trên máy khác cho ra đúng cùng con số. Tỷ lệ `HasCustomerID = False` là **25,16%**, khớp với con số ~25% nêu trong mô tả task.

Lưu ý: các con số này khớp *về mặt số lượng*, nhưng **không có nghĩa là đúng về mặt nghiệp vụ** — QA-01 (sót mã dịch vụ) khiến con số 2.730 bị **thiếu khoảng 212 dòng** so với đúng đặc tả (xem QA-01).

---

## 5. Danh sách vấn đề theo mức ưu tiên

### 🔴 Mức NGHIÊM TRỌNG — phải fix trước khi sang Giai đoạn 2

---

#### QA-04 — `Customer ID` bị đổi định dạng thành `17850.0`

| | |
|---|---|
| **Vị trí** | `src/data/cleaning.py:24` — `df['Customer ID'] = df['Customer ID'].astype(str)` |
| **Ảnh hưởng** | **401.605 dòng (100% số dòng có Customer ID)** trong `data/processed/cleaned_transactions.csv` đã commit |

**Hiện tượng.** Vì dataset gốc có 25% giá trị null, pandas đọc `Customer ID` lên thành `float64`. Gọi `astype(str)` trên cột float sinh ra chuỗi `'17850.0'` thay vì `'17850'`.

Kiểm chứng trực tiếp trên file Data đã commit:

```
Customer ID mẫu trong cleaned_transactions.csv: ['17850.0', '17850.0', '17850.0']
```

**Vì sao nghiêm trọng.** `Customer ID` là **khoá gom nhóm của toàn bộ RFM** (Epic 2). Schema mục 1.2 quy định kiểu `String`, ví dụ `17850`. Hậu quả:
- Mọi kết quả phân cụm xuất ra sẽ mang mã khách hàng sai định dạng, không đối chiếu ngược được với hệ thống nguồn của doanh nghiệp.
- Không join được với bất kỳ nguồn dữ liệu khách hàng nào khác.
- Bước xuất CSV ở Epic 4 sẽ giao cho người dùng cuối một cột mã hỏng.

**Đề xuất fix:**

```python
df['Customer ID'] = df['Customer ID'].astype('Int64').astype(str).replace('<NA>', pd.NA)
```

---

#### QA-03 — Dòng `InvoiceDate` lỗi bị xoá thẳng, không gắn cờ

| | |
|---|---|
| **Vị trí** | `src/data/cleaning.py:18-21` — `df = df.dropna(subset=['InvoiceDate'])` |
| **Bằng chứng** | `test_wrong_dtype.csv`: 5 dòng ngày sai → biến mất, không có cột cờ nào ghi nhận |

**Hiện tượng.** `to_datetime(errors='coerce')` biến ngày không parse được thành `NaT`, rồi `dropna()` xoá luôn các dòng đó.

**Vì sao nghiêm trọng.** BR-07 quy định *"**Đánh dấu lỗi** và loại khỏi tập dữ liệu phân tích nếu không thể khắc phục"* — hai vế: **đánh dấu trước, loại sau**, và chỉ loại ở **tập phân tích**, không phải ở `data/processed/`. Code hiện tại bỏ hẳn vế đánh dấu và xoá ngay ở bước làm sạch. Đây đúng là kiểu vi phạm nguyên tắc "gắn cờ, không xoá vội" mà task này được lập ra để chặn.

Trên dữ liệu gốc hiện tại con số là **0 dòng** (mọi ngày đều parse được), nên lỗi này *chưa gây thiệt hại*. Nhưng hệ thống được thiết kế để **người dùng upload file bất kỳ** — với file thật của doanh nghiệp, dữ liệu sẽ âm thầm bốc hơi mà không ai biết bao nhiêu dòng đã mất.

**Đề xuất fix:** thêm cột `HasValidDate`, giữ nguyên dòng ở `data/processed/`, chỉ lọc ở bước tính RFM.

---

#### QA-07 — Dataset chỉ chứa một nửa Online Retail II

| | |
|---|---|
| **Vị trí** | `data/raw/online_retail_II.csv` |
| **Bằng chứng** | 541.910 dòng, khoảng thời gian **01/12/2010 → 09/12/2011** |

**Hiện tượng.** Bộ **Online Retail II** đầy đủ gồm 2 sheet — *Year 2009-2010* và *Year 2010-2011* — tổng khoảng **1.067.371 dòng**, trải từ 01/12/2009. File trong repo chỉ có sheet 2010-2011, tức **thiếu khoảng 525.000 giao dịch của năm đầu**. Đây thực chất là bộ *Online Retail* (bản I) chứ không phải *Online Retail II*.

**Vì sao nghiêm trọng.** README dự án ghi *"Khoảng 1 triệu giao dịch"* và *"Dữ liệu giao dịch trong nhiều năm"* — cả hai đều không đúng với file hiện có. Hậu quả:
- Recency, Frequency, Monetary tính trên 12 tháng thay vì 24 tháng → chân dung khách hàng lệch, khách mua năm 2009-2010 bị mất hoàn toàn.
- Báo cáo so sánh 3 thuật toán ở Epic 4 sẽ mô tả sai quy mô dữ liệu.

**Đề xuất:** Leader và Data xác nhận — hoặc bổ sung sheet 2009-2010 vào `data/raw/`, hoặc sửa README và tài liệu cho khớp phạm vi dữ liệu thực tế. **Cần chốt trước khi Epic 2 bắt đầu tính RFM**, vì đổi phạm vi dữ liệu sau đó đồng nghĩa làm lại toàn bộ.

---

#### QA-02 — `Quantity` không được ép kiểu số

| | |
|---|---|
| **Vị trí** | `src/data/cleaning.py:12-28` — `fix_dtypes()` chỉ xử lý `InvoiceDate` và `Customer ID` |
| **Bằng chứng** | `test_wrong_dtype.csv`: 10 dòng `Quantity = "abc"` đi qua trọn vẹn, cột giữ dtype `object` |

**Hiện tượng.** Không có bước `to_numeric` cho `Quantity` (và cũng không cho `Price`). Với file gốc, pandas tự suy ra `int64` nên không lộ vấn đề — nhưng chỉ cần **một** ô chứa text là **cả cột** rơi về `object`, và khi đó *mọi* giá trị trong cột đều thành chuỗi, kể cả các dòng hợp lệ:

```
Quantity dtype: object
sample values: ['abc', '6', '8']      <- '6' và '8' vốn là số, giờ là chuỗi
```

**Vì sao nghiêm trọng.** QA đã chạy thử 4 phép toán mà Epic 2 chắc chắn dùng, trên đúng cột `Quantity` sau khi qua `clean_pipeline()`:

| Phép toán ở Epic 2 | Kết quả thực tế |
|---|---|
| `Quantity × Price` (Monetary) | 💥 `TypeError: can't multiply sequence by non-int of type 'float'` |
| `Quantity < 0` (lọc hóa đơn hủy) | 💥 `TypeError: '<' not supported between 'str' and 'int'` |
| `Quantity.sum()` | ⚠️ **Không báo lỗi**, trả về `'abc686666663333266866323344324241212abc…'` |
| `groupby('Customer ID')['Quantity'].sum()` | ⚠️ **Không báo lỗi**, trả về `'68126463244222424'` cho từng khách hàng |

Hai dòng đầu chỉ gây crash — khó chịu nhưng *lộ ra ngay*. **Hai dòng cuối mới là vấn đề thật:** `groupby(...).sum()` chính là phép toán trung tâm của Frequency và Monetary, và ở dtype `object` nó **nối chuỗi thay vì cộng số, không phát sinh bất kỳ exception nào**. Kết quả RFM sẽ là những con số vô nghĩa dài hàng chục chữ số, chảy thẳng vào bước phân cụm mà không có gì cảnh báo.

**Đề xuất fix:** trong `fix_dtypes()`, thêm ép kiểu cho `Quantity` và `Price` bằng `pd.to_numeric(..., errors='coerce')`, gắn cờ dòng ép hỏng thay vì xoá.

> *Ghi chú phân loại:* theo rubric của KAN-12 thì "Nghiêm trọng" định nghĩa là xoá nhầm dữ liệu. QA-02 không xoá dữ liệu nhưng **làm hỏng dữ liệu một cách âm thầm ở bước kế tiếp**, hậu quả tương đương hoặc nặng hơn (sai mà không ai biết), nên QA xếp mức Nghiêm trọng. Đề nghị Leader xác nhận.

---

### 🟠 Mức TRUNG BÌNH — ghi nhận ngay, fix trong Giai đoạn 2

---

#### QA-01 — Sót mã dịch vụ: `D`, `S`, `AMAZONFEE`, và biến thể chữ thường `m`

| | |
|---|---|
| **Vị trí** | `src/data/cleaning.py:41` — `special_codes = ['POST','DOT','M','BANK CHARGES','C2','ADJUST','CRUK']` |
| **Bằng chứng** | `test_service_code.csv`: chỉ 8/12 dòng được gắn cờ |

**Hiện tượng.** Quét toàn bộ dữ liệu gốc, các `StockCode` mang ngữ nghĩa dịch vụ nhưng **không** có trong danh sách:

| StockCode | Description | Số dòng trong dữ liệu gốc |
|---|---|---|
| `D` | Discount | 77 |
| `S` | SAMPLES | 63 |
| `AMAZONFEE` | AMAZON FEE | 34 |
| `gift_0001_*` | Dotcomgiftshop Gift Voucher | 34 |
| `B` | Adjust bad debt | 3 |
| `m` | Manual *(chữ thường của `M` đã có trong list)* | 1 |
| | **Tổng bỏ sót** | **≈ 212 dòng** |

Ngoài ra `'ADJUST'` có trong danh sách nhưng **không tồn tại** trong dữ liệu (0 dòng) — có vẻ chép từ tài liệu khác.

**Ảnh hưởng.** 212 dòng phí dịch vụ/chiết khấu sẽ bị tính nhầm thành **giao dịch mua hàng thật** ở Frequency và Monetary. Riêng `AMAZONFEE` và `D` có giá trị tiền lớn nên đủ sức đẩy lệch Monetary của một vài khách hàng. Con số `IsServiceCode = 2.730` ở mục 4 vì vậy **thiếu khoảng 212** so với đúng đặc tả.

**Đề xuất fix:** bổ sung `D`, `S`, `AMAZONFEE`, `B`, tiền tố `gift_`; so khớp **không phân biệt hoa/thường** (`.str.upper()`); bỏ `ADJUST` hoặc giữ lại kèm ghi chú.

---

#### QA-05 — Thiếu cột `TotalPrice`

**Vị trí:** `src/data/cleaning.py:51-60` — `clean_pipeline()`

Schema mục 1.3 quy định 4 cột phái sinh sau tiền xử lý. Pipeline sinh ra 3 (`IsCancelled`, `HasCustomerID`, `IsServiceCode`) cộng thêm `PriceAnomaly` (ngoài schema, chấp nhận được vì phục vụ BR-04), nhưng **thiếu `TotalPrice = Quantity × Price`**. Epic 2 cần cột này để tính Monetary.

**Đề xuất:** hoặc Data bổ sung vào `clean_pipeline()`, hoặc Leader cập nhật schema chuyển `TotalPrice` sang trách nhiệm của Epic 2. Cần chốt để Model không phải đoán.

---

#### QA-08 — Tên cột trong tài liệu lệch với dữ liệu thật

Tài liệu và dữ liệu đang dùng hai bộ tên khác nhau:

| Tài liệu (README, mô tả task, schema mục 1.3 & 1.4) | Dữ liệu thật + `cleaning.py` |
|---|---|
| `InvoiceNo` | `Invoice` |
| `UnitPrice` | `Price` |
| `CustomerID` | `Customer ID` *(có dấu cách)* |

Bảng schema mục 2 dùng tên đúng (`Invoice`, `Price`, `Customer ID`), nhưng mục 1.3 và 1.4 trong **cùng một tài liệu** lại dùng tên cũ của bộ Online Retail I.

**Ảnh hưởng.** Pipeline (Task 3) xây dictionary mapping dựa trên tài liệu sẽ sinh ra key sai và mapping tự động trượt toàn bộ. Rủi ro cao vì Task 3 chưa code — sửa tài liệu bây giờ là rẻ nhất.

**Đề xuất:** Leader thống nhất một bộ tên duy nhất trong `docs/T01_data_specification.md`, ưu tiên tên khớp dữ liệu thật.

---

#### QA-09 — `requirements.txt` rỗng

File tồn tại nhưng **0 byte**. Không ai dựng lại được môi trường, và không có ràng buộc phiên bản `pandas` — trong khi `pandas` 2.x đã đổi hành vi `to_datetime` và xử lý nullable dtype so với 1.x, đúng những chỗ mà QA-02/QA-04 đụng tới.

**Đề xuất:** ghi tối thiểu `pandas`, `numpy`, `scikit-learn`, `streamlit`, `plotly`, `matplotlib`, `pytest`, kèm ràng buộc phiên bản tối thiểu.

---

### 🟡 Mức NHẸ — cải thiện sau

---

#### QA-06 — Lỗi thiếu cột bắt buộc trả về `KeyError` thô

`clean_pipeline()` dừng đúng khi thiếu `InvoiceDate` (hành vi mong muốn), nhưng bằng `KeyError: 'InvoiceDate'` phát sinh từ tầng pandas, không phải lỗi nghiệp vụ có kiểm soát. Nếu Streamlit hiển thị thẳng, người dùng cuối sẽ thấy traceback.

Repo cũng **chưa có `src/data/validation.py`** dù README có liệt kê. Đề xuất: bổ sung `validate_schema(df)` kiểm tra đủ 6 cột bắt buộc trước khi làm sạch, `raise ValueError("Thiếu cột bắt buộc: InvoiceDate")`.

---

#### QA-10 — File `cleaned_transactions.csv` 60 MB bị commit vào Git

`.gitignore` đã loại `data/raw/*.csv` nhưng `data/processed/cleaned_transactions.csv` (60,5 MB) vẫn nằm trong lịch sử nhánh `task2-data-cleaning`. Đây là dữ liệu **sinh lại được** bằng một lệnh. Mỗi lần chạy lại pipeline sẽ tạo một diff khổng lồ, làm review PR gần như không thể.

**Đề xuất:** thêm `data/processed/` vào `.gitignore`. *(Chưa tự sửa vì file thuộc phạm vi Task 2.)*

---

#### QA-11 — Hóa đơn tiền tố `A` chưa có quy tắc xử lý

Dữ liệu gốc có 3 dòng `Invoice` bắt đầu bằng `A` (`A563185`, `A563186`, `A563187`), `StockCode = 'B'`, `Description = 'Adjust bad debt'`, giá trị ±11.062,06 — bút toán điều chỉnh kế toán, không phải giao dịch mua hàng.

Hiện `IsCancelled` chỉ bắt tiền tố `C` nên 3 dòng này lọt qua như giao dịch thường. Hai dòng có giá âm nên vô tình bị `PriceAnomaly` bắt được, còn **1 dòng giá `+11.062,06` không bị gắn cờ nào**. Rất may cả 3 đều có `Customer ID` null nên sẽ bị loại khỏi RFM ở Epic 2 — nhưng đó là **may chứ không phải thiết kế**.

**Đề xuất:** Leader bổ sung BR-09 cho tiền tố `A`, hoặc gộp `StockCode = 'B'` vào danh sách mã dịch vụ ở QA-01.

---

#### QA-12 — Chất lượng mã nguồn của module làm sạch

| Vấn đề | Vị trí |
|---|---|
| `pd.options.mode.chained_assignment = None` tắt cảnh báo toàn cục — che luôn các `SettingWithCopyWarning` thật ở module khác | `cleaning.py:2` |
| `import logging` nhưng không dùng, toàn bộ output bằng `print()` — Streamlit không bắt được để hiển thị cho người dùng | `cleaning.py:3` |
| `to_datetime` không truyền `format` → pandas cảnh báo và fallback về `dateutil`, chậm hơn nhiều trên 540k dòng | `cleaning.py:15` |

---

## 6. Hạng mục CHƯA thực thi được

### Bước 5 — Test UI upload & mapping (Task 3)

**Trạng thái: ⛔ bị chặn.**

Tính đến 27/07/2026, **Task 3 chưa có mã nguồn trên bất kỳ nhánh nào** của repo — `main`, `develop` và `task2-data-cleaning` đều không có thư mục `src/app/`. Không có UI để chạy, nên các hạng mục sau **chưa được kiểm chứng**:

- C1 — mapping tự động khớp đúng 8 cột với file gốc
- C2 — mapping thủ công với file đã đổi tên cột
- **C3 — upload file có nhiều `Customer ID` null vẫn được chấp nhận** ⚠️
- C4 — chặn upload khi thiếu cột bắt buộc, báo lỗi rõ ràng
- C5 — thiếu cột tùy chọn vẫn cho đi tiếp
- C6 — file sai kiểu dữ liệu không làm sập app

**Đã chuẩn bị sẵn:** checklist Nhóm C trong `docs/qa_checklist_data.md` và các file test tương ứng (`test_missing_customerid.csv`, `test_missing_column.csv`, `test_wrong_dtype.csv`). QA chạy được ngay trong ngày Pipeline bàn giao.

**Cảnh báo sớm gửi Pipeline (hạng mục C3).** Schema mục 2 ghi `Customer ID` là *"Có (đối với RFM)"*. Dòng chữ này rất dễ bị đọc thành ràng buộc `NOT NULL` ở bước validate upload. Đúng phải là: **cột `Customer ID` bắt buộc phải được *mapping*, nhưng giá trị bên trong được phép null.** Nếu Pipeline áp nhầm ràng buộc "không null", **25,16% dataset (135.037 dòng) sẽ bị chặn ngay từ cửa** — và vì lỗi nằm ở tầng validate, sẽ không có log nào của module làm sạch ghi nhận. Đây là lỗi tốn kém nhất trong Giai đoạn 1 nếu phát hiện muộn.

### Nguồn số liệu đối chiếu ở Bước 6

KAN-12 yêu cầu đối chiếu với *"số liệu Data đã báo cáo ở Bước 3 của Task 2"*. Trong repo **không có báo cáo văn bản nào của Task 2** (chỉ có `notebooks/eda_raw_data.ipynb` và file CSV đã xử lý). QA đã đối chiếu bằng nguồn thay thế mạnh hơn: **chạy lại pipeline và so từng chỉ số với file `cleaned_transactions.csv` mà Data đã commit** (mục 4). Kết quả khớp 100%.

Đề nghị Data bổ sung báo cáo định lượng của Bước 3 Task 2 để QA đối chiếu con số **do Data tự công bố**, thay vì con số QA tự tính lại.

---

## 7. Kiến nghị

### Chặn cửa Giai đoạn 2 cho tới khi xong

| # | Việc | Người chịu trách nhiệm |
|---|---|---|
| 1 | Fix QA-04 — khôi phục định dạng `Customer ID` | Data |
| 2 | Fix QA-02 — ép kiểu `Quantity` / `Price` | Data |
| 3 | Fix QA-03 — gắn cờ thay vì xoá dòng ngày lỗi | Data |
| 4 | Chốt QA-07 — phạm vi dataset (1 năm hay 2 năm) | Leader + Data |
| 5 | Chạy lại `pytest tests/` — 3 xfail tương ứng phải chuyển XPASS | Data → QA verify |

### Song song, không chặn cửa

| # | Việc | Người chịu trách nhiệm |
|---|---|---|
| 6 | Fix QA-01 — bổ sung mã dịch vụ, so khớp không phân biệt hoa/thường | Data |
| 7 | Chốt QA-05 — `TotalPrice` thuộc Epic 1 hay Epic 2 | Leader |
| 8 | Fix QA-08 — thống nhất tên cột trong tài liệu | Leader |
| 9 | Fix QA-09 — điền `requirements.txt` | Leader |
| 10 | **Đọc cảnh báo C3 ở mục 6 trước khi code validate upload** | Pipeline |

### Quy trình

- Bộ test tại `tests/test_cleaning.py` dùng `@pytest.mark.xfail(strict=True)` cho từng lỗi đã ghi nhận. **Khi lỗi được sửa, pytest sẽ báo fail** (XPASS) để buộc gỡ marker — nhờ vậy không có test đỏ kinh niên, và không lỗi nào bị sửa âm thầm mà QA không biết.
- Đề nghị thêm `pytest tests/` vào tiêu chí review PR của Giai đoạn 2.

---

## 8. Kết luận

Nguyên tắc **"gắn cờ, không xoá vội"** — trọng tâm cần bảo vệ của Giai đoạn 1 — **được tuân thủ đúng trên cả 4 trường hợp đặc thù của Online Retail II**. Không có dòng nào bị xoá nhầm vì `Customer ID` null, vì là hóa đơn hủy, vì là mã dịch vụ, hay vì giá bằng 0. Đây là kết quả tốt và là phần khó nhất của task.

Các vấn đề còn lại tập trung ở **tầng ép kiểu và định dạng dữ liệu** (QA-02, QA-03, QA-04) — chưa gây thiệt hại trên dữ liệu gốc hiện tại, nhưng sẽ làm hỏng đầu vào của RFM ngay khi Epic 2 bắt đầu, và sẽ gây mất dữ liệu âm thầm khi người dùng thật upload file của họ. Cả ba đều fix được trong phạm vi hẹp.

**Khuyến nghị:** ⛔ **chưa đóng Giai đoạn 1.** Xử lý xong 5 hạng mục chặn cửa ở mục 7, QA chạy lại toàn bộ bộ test và cập nhật báo cáo này.

---

## Phụ lục — Tài liệu liên quan

| Tài liệu | Đường dẫn |
|---|---|
| Checklist kiểm thử (Nhóm A/B/C/D) | [`docs/qa_checklist_data.md`](../../docs/qa_checklist_data.md) |
| Bảng đối chiếu tự động | [`outputs/reports/qa_test_results.md`](qa_test_results.md) |
| Bộ 7 file test lỗi cố ý + base sample | `data/test_samples/` |
| Script sinh file test | `scripts/generate_test_samples.py` |
| Script chạy kịch bản kiểm thử | `scripts/run_qa_scenarios.py` |
| Bộ test tự động | `tests/test_cleaning.py` |
| Đặc tả gốc (đáp án đối chiếu) | [`docs/T01_data_specification.md`](../../docs/T01_data_specification.md) |
