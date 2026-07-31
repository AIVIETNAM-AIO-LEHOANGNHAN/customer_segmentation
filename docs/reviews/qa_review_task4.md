# QA REVIEW — TASK 4 (Model): Phân tích thống kê dữ liệu sạch

| | |
|---|---|
| **Người review** | Tam Tran (QA/QC) |
| **Ngày** | 29/07/2026 |
| **Nhánh** | `task4-eda` |
| **Commit review** | `3d4248e` *eda + report* |
| **Tài liệu review** | `outputs/reports/data_quality_stats.md`, `outputs/results/outliers_detected.csv` |

---

## 1. Kết luận nhanh

**QA đã kiểm chứng độc lập 40 con số trong báo cáo — cả 40 đều tái lập chính xác.**

QA không đọc lại notebook rồi gật đầu; QA viết script riêng, tự nạp `cleaned_transactions.csv`, tự tính lại từ đầu và so từng giá trị với báo cáo. Không có con số nào lệch.

| Nhóm chỉ số | Số mục kiểm | Kết quả |
|---|---:|---|
| Tổng quan + tỷ lệ từng cờ | 11 | ✅ khớp tuyệt đối |
| Giả thuyết hủy đơn ↔ `Quantity` âm | 6 | ✅ khớp tuyệt đối |
| Mã phi-sản-phẩm chưa gắn cờ (mục 3.4) | 8 | ✅ khớp tuyệt đối |
| Tập hợp lệ + outlier IQR | 8 | ✅ khớp tuyệt đối |
| Skewness + Monetary cấp khách hàng | 7 | ✅ khớp tuyệt đối |

Riêng vài giá trị lệch ở chữ số thập phân thứ hai (`skew Monetary` 19,57 vs 19,58; `Monetary` trung vị £662,56 vs £662,57) là do làm tròn, không phải sai lệch.

### Ghi nhận riêng

**Mục 3.4 của báo cáo trùng khớp với lỗi QA-01 mà QA phát hiện độc lập ở vòng 1.** Hai vai trò, hai phương pháp — QA dựng file test lỗi cố ý, Model quét ngược `StockCode` không theo pattern 5 chữ số — cùng chỉ ra `AMAZONFEE`, `B`, `D`, `S`. Model còn định lượng được tác động tiền tệ mà QA không có: `AMAZONFEE` ròng **−£221.520,50**, một mình lớn hơn mọi mã đang được gắn cờ. Đây là phần bổ sung giá trị thật.

Ba lập luận dưới đây QA đánh giá là **chắc và nên giữ nguyên** trong báo cáo cuối:

1. **Không loại outlier** — 7,83% số dòng chiếm 50,77% doanh thu, và bằng chứng B2B rất thuyết phục (Netherlands vượt trội 9,28×, khách `14646` có 1.680 dòng outlier, 87,26% có `Customer ID`). Lập luận "lỗi nhập liệu không lặp lại có hệ thống" là đúng trọng tâm.
2. **Cặp mua–hủy** (`581483`/`C581484`, `541431`/`C541433`) — phát hiện sắc. Chỉ loại dòng `C` mà giữ dòng gốc sẽ đẩy khách `16446` lên top Monetary với +£168.470 dù thực tế không mua gì. QA xác nhận cả hai cặp tồn tại đúng như mô tả.
3. **`Frequency` phải đếm `Invoice.nunique()`, không đếm số dòng** — trung vị 12 dòng/hóa đơn, đếm nhầm sẽ thổi phồng ~12 lần.

---

## 2. 🔴 QA-17 (Nghiêm trọng) — Phân tích chạy trên bản dữ liệu đã lỗi thời

**Vấn đề không nằm ở cách làm của Model, mà ở dữ liệu đầu vào.**

Báo cáo được tính trên `data/processed/cleaned_transactions.csv` **bản cũ** — sinh ra *trước* khi Data sửa lỗi ở commit `5cfc434`. File đó có 12 cột, `Customer ID` còn dạng `17850.0`, chưa có `TotalPrice` lẫn `HasInvalidDate`.

Data đã sửa code nhưng **chưa chạy lại pipeline để sinh file mới** (QA đã ghi việc này thành lỗi QA-13 trong `docs/reviews/qa_review_task2.md`). Model dùng đúng dữ liệu có trong repo tại thời điểm đó — **không ai làm sai quy trình cả**, nhưng kết quả cần được làm mới.

### Con số thay đổi sau khi Data sinh lại file

| Chỉ số | Báo cáo hiện tại | Sau khi sinh lại | Ghi chú |
|---|---:|---:|---|
| Số cột | 12 | **14** | thêm `TotalPrice`, `HasInvalidDate` |
| `IsServiceCode` số dòng | 2.730 | **2.904** | +174 dòng (`D`, `S`, `AMAZONFEE`, `m`) |
| **`IsServiceCode` đóng góp `TotalPrice`** | **+£195.336,86** | **−£34.916,96** | ⚠️ **đổi dấu**, lệch £230.253,82 |
| Tập hợp lệ | 525.075 dòng | 525.070 dòng | −5 dòng |
| Outlier trên | 41.124 dòng | 41.122 dòng | −2 dòng |
| Outlier % doanh thu hợp lệ | 50,77% | 50,71% | gần như không đổi |
| `skew TotalPrice` (tập hợp lệ) | 506,27 | 509,65 | gần như không đổi |

### Phần nào phải viết lại, phần nào giữ nguyên

**Cần cập nhật:**

- **Mục 1** — bảng tổng quan: số cột 12 → 14; `IsServiceCode` 2.730 → 2.904.
- **Mục 3.1 và 3.2** — đây là chỗ đổi nhiều nhất. Câu *"`IsServiceCode` đóng góp +£195.336,86, chiếm 2,01% tổng"* trở thành **−£34.916,96**. Bảng chi tiết từng mã ở 3.2 cần thêm dòng cho `D`, `S`, `AMAZONFEE`.
- **Mục 3.4** — phần lớn đã được Data xử lý: `AMAZONFEE`, `D`, `S` nay đã gắn cờ. **Chỉ còn `B` (3 dòng, ròng −£11.062,06)** và nhóm `gift_0001_*` (34 dòng, ròng +£685,81) là chưa. Khuyến nghị số 4 ở mục 7 nên thu hẹp lại tương ứng.
- **Mục 8** — bảng kiểm chứng bộ lọc: dòng *"− `IsServiceCode` + 4 mã bổ sung"* giờ chỉ còn 1 mã bổ sung.

**Giữ nguyên, không bị ảnh hưởng:**

- Toàn bộ mục 2 (hủy đơn ↔ `Quantity` âm) — con số không đổi.
- Mục 5 (outlier / B2B) — lệch 2 dòng trên 41.124, kết luận không suy chuyển.
- Mục 6 (skewness, log-transform) — lệch ở chữ số thứ ba, kết luận không suy chuyển.
- Mục 10 (đề xuất công thức RFM) — vẫn đúng.

> **Đề nghị trình tự:** chờ Data chạy `python src/data/cleaning.py` và commit file mới (việc số 1 trong review Task 2), rồi Model chạy lại notebook. Ngoài mục 3, các mục khác gần như chỉ cần đổi vài con số.

---

## 3. 🟠 QA-18 (Trung bình) — Nhánh `task4-eda` không tự chạy lại được

Nhánh này được tạo ra từ `a367feb` — commit **revert Task 2** trên `main`. Hệ quả: nhánh **không có `src/data/cleaning.py`**.

Nghĩa là trên chính nhánh của mình, Model không thể chạy lại pipeline để sinh dữ liệu đầu vào cho notebook; chỉ có thể dùng file `cleaned_transactions.csv` được commit sẵn — đúng là file đã lỗi thời ở QA-17.

**Tin tốt:** QA đã thử merge `task4-eda` vào `develop` (cả một mình lẫn kèm `task-3-upload-mapping`) — **merge sạch, `src/data/cleaning.py` không bị xoá**. Ban đầu QA lo commit revert sẽ kéo theo xoá file khi merge, nhưng thử nghiệm cho thấy không xảy ra, vì `develop` nhận `cleaning.py` qua một commit khác nhánh với commit bị revert. **Không cần xử lý gì về mặt merge.**

**Đề nghị:** rebase `task4-eda` lên `develop` (hoặc merge `develop` vào nhánh này) trước khi chạy lại notebook, để Model có `cleaning.py` và tự sinh được dữ liệu tươi mà không phải chờ file commit sẵn.

---

## 4. 🟡 Ghi chú nhỏ — không chặn

**N1. Notebook nên ghi nguồn dữ liệu.**
Đề nghị in ra commit hash hoặc thời điểm sinh file `cleaned_transactions.csv` ở cell đầu. Nếu có thói quen này, chênh lệch ở QA-17 đã lộ ra ngay khi chạy.

**N2. Báo cáo tự tính `TotalPrice`.**
File cũ chưa có cột này nên notebook tự nhân `Quantity × Price` — hợp lý. Sau khi Data sinh lại file, cột `TotalPrice` đã có sẵn; nên dùng cột đó thay vì tính lại, tránh hai định nghĩa lệch nhau về sau.

**N3. Biểu đồ được tham chiếu nhưng chưa có trong repo.**
Báo cáo trỏ tới `outputs/figures/quantity_cancelled_vs_valid.png` (mục 2.4) và nhắc tới biểu đồ ở mục 4, nhưng thư mục `outputs/figures/` chưa được commit. Người đọc báo cáo trên GitHub sẽ thấy ảnh vỡ.

**N4. `outliers_detected.csv` (41.124 dòng × 21 cột) được commit.**
Cùng nhóm vấn đề với QA-10/QA-13: đây là dữ liệu sinh lại được. Khi Model chạy lại notebook, file này sẽ tạo một diff lớn. Cân nhắc đưa `outputs/results/` vào `.gitignore`.

---

## 5. Việc cần làm

| # | Việc | Mức | Chặn Giai đoạn 2? |
|---|---|---|---|
| 1 | Chờ Data sinh lại `cleaned_transactions.csv`, **chạy lại notebook**, cập nhật mục 1, 3.1, 3.2, 3.4, 8 (QA-17) | 🔴 Nghiêm trọng | **Có** |
| 2 | Merge `develop` vào `task4-eda` để nhánh có `cleaning.py` (QA-18) | 🟠 Trung bình | Không |
| 3 | Commit `outputs/figures/` hoặc bỏ tham chiếu ảnh trong báo cáo | 🟡 Nhẹ | Không |
| 4 | In nguồn/thời điểm dữ liệu ở đầu notebook | 🟡 Nhẹ | Không |
| 5 | Dùng cột `TotalPrice` có sẵn thay vì tự tính lại | 🟡 Nhẹ | Không |

---

*Một lần nữa: chất lượng phân tích ở đây rất tốt — 40/40 con số tái lập được, và mục 3.4 phát hiện đúng một lỗi mà QA cũng tìm ra bằng đường khác. Vấn đề duy nhất là dữ liệu đầu vào đã lỗi thời, và đó không phải lỗi của Model.*

*Báo cáo đầy đủ: `outputs/reports/data_quality_report.md` trên nhánh `feature/task5-qa-data-quality` (KAN-12).*
