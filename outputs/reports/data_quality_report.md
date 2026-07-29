# BÁO CÁO CHẤT LƯỢNG DỮ LIỆU — CUỐI GIAI ĐOẠN 1

| | |
|---|---|
| **Task** | KAN-12 — Task 5: Kiểm thử dữ liệu đầu vào và báo cáo chất lượng dữ liệu |
| **Epic** | KAN-4 — Giai đoạn 1: Khám phá, Làm sạch & Chuẩn hóa dữ liệu |
| **Vai trò** | QA/QC |
| **Người thực hiện** | Tam Tran |
| **Vòng 1** | 27/07/2026 — Task 2 `b52a0b3` |
| **Vòng 2** | **29/07/2026** — Task 2 `5cfc434` · Task 3 `510245c` · Task 4 `3d4248e` |
| **Căn cứ đối chiếu** | `docs/T01_data_specification.md` mục 1.3, 2, 3 (BR-01 → BR-08) |

---

## 1. Tóm tắt cho Leader

**Giai đoạn 1 đã tiến bộ rõ rệt, nhưng vẫn chưa đóng được.**

Vòng 1 phát hiện 12 vấn đề. Data đã sửa 5 vấn đề nặng nhất và QA xác nhận bằng test tự động. Task 3 và Task 4 hoàn thành, cả hai đều đạt chất lượng tốt:

- **Task 3 (Pipeline)** — **6/6 hạng mục checklist Nhóm C đều ĐẠT**, kể cả hạng mục C3 mà QA đã cảnh báo sớm là cái bẫy tốn kém nhất của giai đoạn này.
- **Task 4 (Model)** — **QA kiểm chứng độc lập 40 con số, cả 40 đều tái lập chính xác.**

Nhưng vòng 2 phát hiện **6 vấn đề mới**, trong đó 3 vấn đề mức Nghiêm trọng — và cả 3 đều là **lỗi ở mối nối giữa các vai trò**, không phải lỗi bên trong công việc của ai.

| Mức độ | Mã | Số lượng | Yêu cầu |
|---|---|---|---|
| 🔴 **Nghiêm trọng** | QA-07, QA-13, QA-16, QA-17 | 4 | Phải xử lý trước khi sang Giai đoạn 2 |
| 🟠 **Trung bình** | QA-01*, QA-08, QA-09*, QA-14, QA-15, QA-18 | 6 | Xử lý trong Giai đoạn 2 |
| 🟡 **Nhẹ** | QA-06*, QA-10, QA-11, QA-12 | 4 | Cải thiện sau |
| ✅ **Đã sửa & xác nhận** | QA-02, QA-03, QA-04, QA-05 | 4 | — |

<sup>*Sửa một phần.</sup>

**Kết quả kiểm thử tự động vòng 2:** 29 tiêu chí — **26 ĐẠT / 3 KHÔNG ĐẠT** *(vòng 1: 16/23)*.
Bộ test: **43 passed, 4 xfailed**. Chi tiết: [`qa_test_results.md`](qa_test_results.md).

### Một câu cho Leader

> Ba lỗi Nghiêm trọng mới **không nằm trong code của bất kỳ ai** — chúng nằm ở chỗ các vai trò gặp nhau: Data sửa code nhưng chưa sinh lại file kết quả (QA-13), nên Model phân tích trên dữ liệu cũ (QA-17); và Pipeline code theo tài liệu trong khi tài liệu lệch với dữ liệu thật (QA-16, gốc là QA-08 chưa được chốt từ vòng 1). Đây là dấu hiệu nhóm cần **một điểm chốt schema và một quy ước "ai sinh lại artifact khi nào"**, chứ không phải dấu hiệu ai đó làm ẩu.

---

## 2. Những gì đã được sửa và QA đã xác nhận

Bộ test dùng `@pytest.mark.xfail(strict=True)`. Khi chạy lại trên commit `5cfc434`, **6 test chuyển sang XPASS** — pytest tự phát hiện "lỗi này đã hết" mà QA không cần đọc lại code.

| Mã | Nội dung | Bằng chứng đã sửa |
|---|---|---|
| **QA-02** | `Quantity` không ép kiểu số | `to_numeric(errors='coerce')`; `test_wrong_dtype.csv` giữ đủ 300 dòng, dtype `float64` |
| **QA-03** | `InvoiceDate` lỗi bị xoá không cờ | Thêm `flag_invalid_date()` → cột `HasInvalidDate`; 5 dòng ngày sai được giữ + gắn cờ |
| **QA-04** | `Customer ID` thành `17850.0` | 0/225 mã còn đuôi `.0`; `nunique` không đổi (không gộp nhầm khách) |
| **QA-05** | Thiếu cột `TotalPrice` | Thêm `calc_total_price()`; đủ 4 cột phái sinh theo schema mục 1.3 |
| **QA-01** | Sót mã dịch vụ | Thêm `D`, `S`, `AMAZONFEE` + `.str.upper()` → `m` bắt được; 12/12 dòng mẫu |

QA cũng bổ sung **regression test** cho rủi ro của bản sửa: `.str.upper()` **không** gắn cờ nhầm mã sản phẩm thật (`85123A`, `DCGSSGIRL`, `DCGSSBOY`, `PADS`), và việc sửa định dạng `Customer ID` **không** gộp hai khách hàng làm một.

---

## 3. Bảng đối chiếu kết quả test (kỳ vọng vs thực tế)

Sinh tự động bằng `python scripts/run_qa_scenarios.py` — 29 tiêu chí, 26 ĐẠT / 3 KHÔNG ĐẠT.
Bảng đầy đủ: [`qa_test_results.md`](qa_test_results.md). Ba tiêu chí KHÔNG ĐẠT:

| File / đối tượng | Tiêu chí | Kỳ vọng | Thực tế | Mã lỗi |
|---|---|---|---|---|
| `test_wrong_dtype.csv` | Dòng `Quantity` ép kiểu hỏng được gắn cờ | có cột cờ riêng | 0 cột cờ | **QA-14** |
| `base_sample.csv` | Luồng batch và luồng UI cho cùng schema | cùng bộ tên cột | lệch 3 cột | **QA-16** |
| `data/processed/cleaned_transactions.csv` | File sinh lại sau khi sửa module | có `TotalPrice` + `HasInvalidDate` | 12 cột, thiếu cả hai | **QA-13** |

---

## 4. Kết quả kiểm thử Task 3 — UI Upload & Mapping *(lần đầu chạy được)*

Vòng 1 phải bỏ trống toàn bộ Nhóm C vì Task 3 chưa có mã nguồn. Vòng 2 đã chạy đủ, bằng `tests/test_upload_mapping.py`.

| # | Hạng mục | Kết quả |
|---|---|---|
| C1 | Mapping tự động khớp 8 cột file gốc | ✅ **8/8** |
| C2 | Mapping thủ công với file đổi tên cột | ✅ |
| **C3** | **File nhiều `Customer ID` null vẫn được chấp nhận** | ✅ **ĐẠT** |
| C4 | Thiếu cột bắt buộc → chặn, báo lỗi rõ | ✅ |
| C5 | Thiếu cột tùy chọn vẫn cho đi tiếp | ✅ |
| C6 | File sai kiểu dữ liệu không làm sập app | ✅ |
| C7–C10 | Chống map trùng, map sai, chuẩn hoá tên cột, chặn đuôi file lạ | ✅ |
| C11 | Luồng batch và UI cho cùng schema | ❌ **QA-16** |

**Về C3:** ở vòng 1 QA cảnh báo rằng schema mục 2 ghi `Customer ID` là *"Có (đối với RFM)"* rất dễ bị hiện thực nhầm thành ràng buộc `NOT NULL`, sẽ chặn mất 135.037 dòng ngay từ cửa. **Pipeline đã làm đúng** — `validate_mapping()` chỉ kiểm cột có được *ánh xạ* hay không, không đụng tới giá trị. QA đã chạy trọn luồng với file 25% null: qua validate, giữ đủ 300 dòng, gắn cờ đúng 75.

---

## 5. Đối chiếu số liệu Task 4 — QA kiểm chứng độc lập

QA không đọc lại notebook rồi gật đầu. QA viết script riêng, tự nạp `cleaned_transactions.csv`, tính lại từ đầu và so từng con số với báo cáo `outputs/reports/data_quality_stats.md`.

| Nhóm chỉ số | Số mục kiểm | Kết quả |
|---|---:|---|
| Tổng quan + tỷ lệ từng cờ | 11 | ✅ khớp tuyệt đối |
| Giả thuyết hủy đơn ↔ `Quantity` âm | 6 | ✅ khớp tuyệt đối |
| Mã phi-sản-phẩm chưa gắn cờ (mục 3.4) | 8 | ✅ khớp tuyệt đối |
| Tập hợp lệ + outlier IQR | 8 | ✅ khớp tuyệt đối |
| Skewness + Monetary cấp khách hàng | 7 | ✅ khớp tuyệt đối |
| | **40** | **40/40 tái lập được** |

Đáng chú ý: **mục 3.4 của Task 4 trùng khớp với lỗi QA-01 mà QA phát hiện độc lập ở vòng 1.** Hai vai trò, hai phương pháp khác nhau (QA dựng file test lỗi cố ý; Model quét ngược `StockCode` không theo pattern 5 chữ số), cùng chỉ ra `AMAZONFEE`, `B`, `D`, `S`. Model còn định lượng được tác động tiền tệ mà QA không có.

---

## 6. Vấn đề mới phát hiện ở vòng 2

### 🔴 QA-13 (Nghiêm trọng) — `cleaned_transactions.csv` chưa được sinh lại

**Vai trò xử lý: Data.**

Code đã sửa nhưng file kết quả trong repo vẫn là bản sinh ra *trước* khi sửa:

| Kiểm tra | File đang commit | Chạy lại code hiện tại |
|---|---|---|
| Số cột | **12** | **14** |
| Có `TotalPrice` | ❌ thiếu | ✅ |
| Có `HasInvalidDate` | ❌ thiếu | ✅ |
| Mẫu `Customer ID` | **`17850.0`** | `17850` |
| `IsServiceCode` | **2.730 dòng** | **2.904 dòng** |

Nghĩa là **QA-04 và QA-05 đã sửa trong code nhưng vẫn còn nguyên trong dữ liệu mà cả nhóm đang dùng.** Đây không phải vấn đề lý thuyết — nó đã trực tiếp gây ra QA-17 bên dưới.

**Cần làm:** chạy `python src/data/cleaning.py`, commit file mới, báo Model chạy lại EDA.

---

### 🔴 QA-16 (Nghiêm trọng) — Hai luồng chạy cho ra hai schema khác nhau

**Vai trò xử lý: Pipeline + Leader.**

| | Luồng batch<br>`python src/data/cleaning.py` | Luồng UI<br>upload → mapping → clean |
|---|---|---|
| Mã hóa đơn | `Invoice` | **`InvoiceNo`** |
| Đơn giá | `Price` | **`UnitPrice`** |
| Mã khách | `Customer ID` | **`CustomerID`** |
| Tên file xuất | `cleaned_transactions.csv` | `cleaned_transactions.csv` |

Nguyên nhân: `STANDARD_COLUMNS` trong `column_mapper.py` dùng bộ tên của **Online Retail I** — đúng theo tài liệu, nhưng tài liệu đang lệch với dữ liệu thật. **Đây chính là hậu quả của QA-08 vòng 1 chưa được chốt.**

**Vì sao nghiêm trọng.** Epic 2 sẽ viết `rfm.groupby("Customer ID")`. Code đó chạy được với file batch, hỏng với file tải từ UI — cùng một tên file, hai cấu trúc. Lỗi sẽ xuất hiện dưới dạng `KeyError` ngẫu nhiên tùy người dùng lấy file từ đâu.

Hàm `_first_existing_column()` mà Pipeline thêm vào giúp *module làm sạch* chịu được cả hai tên, nhưng **file xuất ra vẫn mang hai schema** — mọi module hạ nguồn sẽ phải lặp lại đúng thủ thuật đó.

**Cần làm:** Leader chốt một bộ tên chuẩn (QA đề nghị lấy theo dữ liệu thật: `Invoice`, `Price`, `Customer ID`), Pipeline sửa `STANDARD_COLUMNS` cho khớp. Giữ nguyên `DEFAULT_COLUMN_ALIASES` để người dùng upload kiểu nào cũng khớp.

---

### 🔴 QA-17 (Nghiêm trọng) — EDA Task 4 chạy trên dữ liệu lỗi thời

**Vai trò xử lý: Model (sau khi Data xong QA-13).**

Báo cáo Task 4 được tính trên bản `cleaned_transactions.csv` cũ. Model dùng đúng dữ liệu có trong repo tại thời điểm đó — **không ai làm sai quy trình** — nhưng kết quả cần làm mới.

| Chỉ số | Báo cáo hiện tại | Sau khi sinh lại | Ghi chú |
|---|---:|---:|---|
| `IsServiceCode` số dòng | 2.730 | **2.904** | +174 dòng |
| **`IsServiceCode` đóng góp `TotalPrice`** | **+£195.336,86** | **−£34.916,96** | ⚠️ **đổi dấu**, lệch £230.253,82 |
| Tập hợp lệ | 525.075 | 525.070 | −5 dòng |
| Outlier trên | 41.124 | 41.122 | −2 dòng |
| Outlier % doanh thu | 50,77% | 50,71% | gần như không đổi |

**Phải viết lại:** mục 1 (bảng tổng quan), mục 3.1 và 3.2 (đổi nhiều nhất — kết luận về đóng góp của mã dịch vụ đổi dấu), mục 3.4 (`AMAZONFEE`, `D`, `S` đã được sửa; chỉ còn `B` và `gift_*`), mục 8 (bảng kiểm chứng bộ lọc).

**Giữ nguyên, không ảnh hưởng:** mục 2 (hủy đơn ↔ `Quantity` âm), mục 5 (outlier/B2B — lệch 2 dòng trên 41.124), mục 6 (skewness, log-transform), mục 10 (đề xuất công thức RFM).

---

### 🟠 QA-14 (Trung bình) — `Quantity` ép kiểu hỏng không có cờ

**Vai trò xử lý: Data.**

Cách xử lý hai loại lỗi giống hệt nhau đang bất đối xứng:

| Trường hợp | Ép kiểu | Giữ dòng | Có cờ |
|---|---|---|---|
| `InvoiceDate` không parse được | `to_datetime(errors='coerce')` | ✅ | ✅ `HasInvalidDate` |
| `Quantity` không parse được | `to_numeric(errors='coerce')` | ✅ | ❌ **không có** |

10 dòng `Quantity = "abc"` được giữ lại (đúng) nhưng lặng lẽ thành `NaN`, không cột nào ghi nhận. Xuống Epic 2, `groupby().sum()` bỏ qua `NaN` không báo gì — Monetary thiếu một phần mà không ai biết.

**Cần làm:** thêm `flag_invalid_quantity()` đối xứng với `flag_invalid_date()`.

---

### 🟠 QA-15 (Trung bình) — Task 3 sửa file thuộc sở hữu Task 2

**Vai trò xử lý: Pipeline + Data.**

Commit `510245c` sửa 74 dòng trong `src/data/cleaning.py` — deliverable của Task 2.

Về kỹ thuật bản sửa tốt (`_first_existing_column()` gọn, thông điệp lỗi rõ, còn tiện tay bổ sung ép kiểu cho `Price` mà Data chưa làm). Về quy trình thì có rủi ro: sau khi merge, bản `cleaning.py` trên `develop` là bản của Pipeline, không phải bản Data đang thấy. Lần tới Data sửa tiếp file này, khả năng cao sẽ xung đột.

> QA đã thử merge cả `task-3-upload-mapping` và `task4-eda` vào `develop` — **hiện không xung đột**, `cleaning.py` không bị mất. Không cần xử lý gấp, nhưng cần thống nhất quyền sở hữu.

---

### 🟠 QA-18 (Trung bình) — Nhánh `task4-eda` không có `cleaning.py`

**Vai trò xử lý: Model.**

Nhánh tạo ra từ `a367feb` — commit revert Task 2 trên `main` — nên không có `src/data/cleaning.py`. Model không thể tự chạy lại pipeline trên nhánh của mình, chỉ dùng được file commit sẵn (đúng file đã lỗi thời ở QA-17).

> QA ban đầu lo commit revert sẽ kéo theo xoá `cleaning.py` khi merge vào `develop`. **Đã thử nghiệm: không xảy ra, merge sạch.** Không có rủi ro merge; chỉ cần merge `develop` vào nhánh này để Model tự sinh được dữ liệu tươi.

---

## 7. Vấn đề còn mở từ vòng 1

| Mã | Nội dung | Mức | Trạng thái |
|---|---|---|---|
| **QA-07** | Dataset chỉ có 541.910 dòng (12/2010→12/2011), thiếu nửa năm 2009-2010 của Online Retail II. README ghi "khoảng 1 triệu giao dịch" | 🔴 Nghiêm trọng | **Chưa xử lý** — cần Leader + Data chốt trước khi Epic 2 tính RFM |
| **QA-08** | Tài liệu dùng `InvoiceNo`/`UnitPrice`/`CustomerID`, dữ liệu thật dùng `Invoice`/`Price`/`Customer ID` | 🟠 Trung bình | **Chưa chốt — đã gây ra QA-16** |
| QA-01 | Còn sót `B` (3 dòng, ròng −£11.062,06) và `gift_0001_*` (34 dòng) | 🟠 Trung bình | Sửa một phần |
| QA-09 | `requirements.txt` | 🟠 Trung bình | Task 3 thêm 3 dòng; còn thiếu `pytest`, thư viện Epic 3 |
| QA-06 | Lỗi thiếu cột vẫn là `KeyError` | 🟡 Nhẹ | Thông điệp đã tốt hơn nhờ Task 3 |
| QA-10 | File 60 MB `cleaned_transactions.csv` bị commit | 🟡 Nhẹ | Chưa xử lý |
| QA-11 | Hóa đơn tiền tố `A` chưa có quy tắc | 🟡 Nhẹ | Chưa xử lý |
| QA-12 | Chất lượng mã nguồn module làm sạch | 🟡 Nhẹ | Chưa xử lý |

---

## 8. Kiến nghị

### Chặn cửa Giai đoạn 2

| # | Việc | Vai trò | Phụ thuộc |
|---|---|---|---|
| 1 | Chạy lại `python src/data/cleaning.py`, commit file mới (QA-13) | Data | — |
| 2 | Chạy lại notebook EDA, cập nhật mục 1/3.1/3.2/3.4/8 (QA-17) | Model | Sau việc 1 |
| 3 | **Chốt bộ tên cột chuẩn cho toàn hệ thống** (QA-08) | Leader | — |
| 4 | Sửa `STANDARD_COLUMNS` để hai luồng cùng schema (QA-16) | Pipeline | Sau việc 3 |
| 5 | Chốt phạm vi dataset — 1 năm hay 2 năm (QA-07) | Leader + Data | — |
| 6 | Chạy lại `pytest tests/`, QA xác nhận | QA/QC | Sau 1–5 |

> **Việc 1 → 2 là chuỗi phụ thuộc.** Model không thể bắt đầu trước khi Data sinh lại file. Đề nghị Leader xếp thứ tự này khi giao việc.

### Song song, không chặn cửa

| # | Việc | Vai trò |
|---|---|---|
| 7 | Bổ sung `B` và tiền tố `gift_` vào `special_codes` (QA-01) | Data |
| 8 | Thêm cờ `HasInvalidQuantity` (QA-14) | Data |
| 9 | Thống nhất quyền sở hữu `src/data/cleaning.py` (QA-15) | Data + Pipeline |
| 10 | Merge `develop` vào `task4-eda` (QA-18) | Model |
| 11 | Bổ sung `pytest` + thư viện Epic 3 vào `requirements.txt` (QA-09) | Leader |
| 12 | Thêm `data/processed/`, `outputs/results/` vào `.gitignore` (QA-10) | Data |

### Quy trình — hai đề nghị cho Giai đoạn 2

**1. Quy ước "sinh lại artifact".** QA-13 và QA-17 là cùng một gốc: không ai biết file trong `data/processed/` có còn khớp với code hay không. Đề nghị hoặc bỏ file này khỏi Git (sinh lại khi cần), hoặc bắt buộc ghi commit hash + thời điểm sinh vào `data/processed/README.md`. Notebook và script nên in nguồn dữ liệu ở cell đầu.

**2. Thêm `pytest tests/` vào tiêu chí review PR.** Bộ test hiện có 43 test chạy trong ~1 giây, phủ cả module làm sạch lẫn UI mapping. Các lỗi đã ghi nhận dùng `xfail(strict=True)` nên bộ test luôn xanh khi chưa sửa, và **tự báo fail khi lỗi được sửa** để buộc gỡ marker — không lỗi nào bị sửa âm thầm mà QA không biết.

---

## 9. Kết luận

Nguyên tắc **"gắn cờ, không xoá vội"** tiếp tục được tuân thủ đúng, và 4 lỗi ép kiểu/định dạng nặng nhất của vòng 1 đã được Data xử lý gọn. Task 3 vượt qua toàn bộ checklist Nhóm C, kể cả cái bẫy `Customer ID` null. Task 4 cho ra một phân tích mà QA kiểm chứng được từng con số. Chất lượng công việc của từng vai trò là tốt.

Vấn đề còn lại nằm ở **mối nối giữa các vai trò**: một artifact chưa được làm mới đã khiến cả một báo cáo EDA phải viết lại, và một dòng tài liệu chưa được chốt đã sinh ra hai schema song song trong cùng một hệ thống. Cả hai đều rẻ để sửa bây giờ và đắt nếu để sang Epic 2.

**Khuyến nghị:** ⛔ **chưa đóng Giai đoạn 1.** Xử lý xong 6 việc chặn cửa ở mục 8 — trong đó việc 1 và 3 nên làm ngay vì các việc khác phụ thuộc vào chúng — sau đó QA chạy lại toàn bộ và cập nhật báo cáo này.

---

## Phụ lục — Tài liệu liên quan

| Tài liệu | Đường dẫn |
|---|---|
| Checklist kiểm thử (Nhóm A/B/C/D) | [`docs/qa_checklist_data.md`](../../docs/qa_checklist_data.md) |
| Review gửi Data (Task 2) | [`docs/reviews/qa_review_task2.md`](../../docs/reviews/qa_review_task2.md) |
| Review gửi Pipeline (Task 3) | [`docs/reviews/qa_review_task3.md`](../../docs/reviews/qa_review_task3.md) |
| Review gửi Model (Task 4) | [`docs/reviews/qa_review_task4.md`](../../docs/reviews/qa_review_task4.md) |
| Bảng đối chiếu tự động | [`outputs/reports/qa_test_results.md`](qa_test_results.md) |
| Bộ 7 file test lỗi cố ý + base sample | `data/test_samples/` |
| Script sinh file test | `scripts/generate_test_samples.py` |
| Script chạy kịch bản kiểm thử | `scripts/run_qa_scenarios.py` |
| Bộ test module làm sạch | `tests/test_cleaning.py` |
| Bộ test UI upload & mapping | `tests/test_upload_mapping.py` |
| Đặc tả gốc (đáp án đối chiếu) | [`docs/T01_data_specification.md`](../../docs/T01_data_specification.md) |
