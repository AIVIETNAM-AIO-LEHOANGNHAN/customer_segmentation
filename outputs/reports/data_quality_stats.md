# BÁO CÁO PHÂN TÍCH THỐNG KÊ DỮ LIỆU ĐÃ LÀM SẠCH


## 1. Tổng quan dữ liệu đầu vào

| Chỉ số | Giá trị |
|---|---|
| Số dòng | **536,642** |
| Số cột | 12 (8 cột gốc + 4 cột cờ từ Task 2) |
| Khoảng thời gian | 2010-12-01 → 2011-12-09 |
| Số StockCode | 4,070 |
| Tổng `TotalPrice` (chưa lọc) | **£9,726,024.95** |

### Mức độ phổ biến của từng cờ

| Cờ | Số dòng | % số dòng | Tổng `TotalPrice` | % tổng `TotalPrice` |
|---|---:|---:|---:|---:|
| `IsCancelled = True` | 9,251 | 1.72% | −£893,979.73 | −9.19% |
| `IsServiceCode = True` | 2,730 | 0.51% | +£195,336.86 | 2.01% |
| `PriceAnomaly = True` | 2,512 | 0.47% | −£22,124.12 | −0.23% |
| `HasCustomerID = True` *(cờ giữ lại)* | 401,605 | 74.84% | £8,278,537.42 | 85.12% |

> **Lưu ý:** `HasCustomerID` là cờ *tích cực* (True = giữ). Ba cờ còn lại là cờ *cảnh báo*.

---

## 2. Thống kê mô tả — so sánh nhóm hủy đơn / không hủy

### 2.1 Bảng `describe()` theo `IsCancelled`

| Chỉ số | | `IsCancelled = False` | `IsCancelled = True` |
|---|---|---:|---:|
| **Quantity** | count | 527,391 | 9,251 |
| | mean | 10.31 | **−29.79** |
| | std | 160.37 | 1,148.00 |
| | min | −9,600 | −80,995 |
| | 25% / 50% / 75% | 1 / 3 / 11 | −6 / −2 / **−1** |
| | max | 80,995 | **−1** |
| **Price** | mean | 3.86 | 48.57 |
| | median | 2.08 | 2.95 |
| | max | 13,541.33 | 38,970.00 |
| **TotalPrice** | mean | **+20.14** | **−96.64** |
| | median | 9.90 | −8.50 |
| | min / max | −11,062.06 / 168,469.60 | −168,469.60 / −0.12 |
| | **sum** | **£10,620,004.68** | **−£893,979.73** |

### 2.2 ✅ Giả thuyết được xác nhận 100%

| | `Quantity < 0` | `Quantity > 0` |
|---|---:|---:|
| `IsCancelled = False` | 1,336 | 526,055 |
| `IsCancelled = True` | **9,251** | **0** |

**Toàn bộ 9,251 dòng hủy đơn đều có `Quantity` âm — không có một ngoại lệ nào** (max = −1).

### 2.3 Tác động nếu KHÔNG loại đơn hủy

```
Doanh thu nhóm KHÔNG hủy : £10,620,004.68
Giá trị nhóm HỦY         : −£893,979.73   (≈ 8.42% doanh thu nhóm không hủy)
Nếu cộng dồn cả 2 nhóm   : £9,726,024.95  ← Monetary bị GIẢM ẢO
```

Hệ quả nghiêm trọng hơn con số tổng: khách hàng **hay trả hàng** sẽ bị trừ Monetary hai lần
(một lần không được cộng doanh thu, một lần bị trừ giá trị hủy) → bị đẩy nhầm vào cụm
"khách giá trị thấp / sắp rời bỏ", trong khi thực tế họ có thể là khách mua nhiều.

### 2.4 🔍 Phát hiện thêm — 1,336 dòng `Quantity < 0` nhưng `IsCancelled = False`

| Đặc điểm | Giá trị |
|---|---|
| Số dòng | 1,336 |
| Tổng `TotalPrice` | £0.00 |
| Có `Price = 0` | **1,336 / 1,336 (100%)** |
| Có `Customer ID` | **0 / 1,336 (0%)** |
| Description phổ biến | `NaN`, `check`, `?`, `damages`, `damaged`, `found`, `adjustment` |

→ Đây là **bút toán điều chỉnh kho** (hàng hỏng, kiểm kê), **không phải giao dịch**.
Chúng có `TotalPrice = 0` nên không ảnh hưởng Monetary, nhưng **sẽ thổi phồng Frequency**
nếu đếm theo số dòng/số hóa đơn. Nhóm này trùng hoàn toàn với `PriceAnomaly`.

![Phân phối Quantity theo nhóm hủy đơn](../figures/quantity_cancelled_vs_valid.png)

---

## 3. Ảnh hưởng của mã dịch vụ (`IsServiceCode`) lên Monetary

### 3.1 Tỷ trọng toàn cục — nhỏ

| | Số dòng | % số dòng | Tổng `TotalPrice` | % tổng |
|---|---:|---:|---:|---:|
| `IsServiceCode = False` | 533,912 | 99.49% | £9,530,688.09 | 97.99% |
| `IsServiceCode = True` | 2,730 | 0.51% | £195,336.86 | **2.01%** |



### 3.2 Chi tiết từng mã — đóng góp **hai chiều**, cực đoan

| StockCode | Mô tả | Số dòng | Đóng góp ròng | Max | Min | Số dòng hủy |
|---|---|---:|---:|---:|---:|---:|
| `DOT` | DOTCOM POSTAGE | 710 | **+£206,245.48** | 4,505.17 | −3.29 | 1 |
| `POST` | POSTAGE | 1,257 | +£66,248.64 | 8,142.75 | −8,142.75 | 126 |
| `C2` | CARRIAGE | 144 | +£6,986.00 | 150.00 | −50.00 | 2 |
| `BANK CHARGES` | Bank Charges | 37 | −£7,175.64 | 15.00 | −1,050.15 | 25 |
| `CRUK` | CRUK Commission | 16 | −£7,933.43 | −1.60 | −1,100.44 | 16 |
| `M` | Manual | 566 | **−£69,034.19** | 4,287.63 | **−38,970.00** | 244 |


**Các dòng bất thường lớn nhất:**

| Invoice | Mã | Quantity | Price | TotalPrice | Country |
|---|---|---:|---:|---:|---|
| `C556445` | `M` (Manual) | −1 | 38,970.00 | **−£38,970.00** | United Kingdom |
| `C573079` | `M` (Manual) | −2 | 4,161.06 | −£8,322.12 | France |
| `551697` | `POST` | 1 | 8,142.75 | +£8,142.75 | United Kingdom |
| `562955` | `DOT` | 1 | 4,505.17 | +£4,505.17 | United Kingdom |

### 3.3 ⚠️ Ở cấp khách hàng, ảnh hưởng KHÔNG hề nhỏ

| Chỉ số | Giá trị |
|---|---|
| Số khách có Monetary bị mã dịch vụ tác động | **542 / 4,339 (12.5%)** |
| Mức thổi phồng trung vị (trong nhóm bị tác động) | **9.47%** |
| Số khách bị thổi phồng **> 10%** Monetary | **257** |
| Số khách bị thổi phồng **> 50%** Monetary | **17** |

**Ví dụ cực đoan:**

| Customer ID | Monetary có mã dịch vụ | Monetary không có | % thổi phồng |
|---|---:|---:|---:|
| 15581 | £3,675.77 | £717.43 | **+412.35%** |
| 15935 | £416.86 | £108.04 | +285.84% |
| 12536 | £12,601.83 | £4,279.71 | +194.46% |
| 12744 | £21,279.29 | £9,120.39 | +133.32% |

> **Kết luận:** tỷ trọng toàn cục 2% **không** phải lý do để giữ lại. Ở cấp khách hàng —
> đúng cấp mà K-Means làm việc — mã dịch vụ đủ sức đẩy hàng trăm khách sang nhầm cụm RFM.
> **→ LOẠI khỏi toàn bộ RFM.**

### 3.4 🚨 Lỗ hổng trong danh sách mã dịch vụ của Task 2

Kiểm tra ngược các `StockCode` không theo pattern 5 chữ số nhưng **chưa** được gắn `IsServiceCode`:

| StockCode | Mô tả | Số dòng | Đóng góp ròng |
|---|---|---:|---:|
| `AMAZONFEE` | AMAZON FEE | 34 | **−£221,520.50** |
| `B` | Adjust bad debt | 3 | −£11,062.06 |
| `D` | Discount | 77 | −£5,696.22 |
| `S` | SAMPLES | 62 | −£3,039.65 |
| | **Tổng** | **176** | **−£241,318.43** |

`AMAZONFEE` một mình có ảnh hưởng ròng lớn hơn **mọi** mã đang được gắn cờ, và hiện đang được
tính vào Monetary. Các mã `gift_0001_*`, `DCGS*` là sản phẩm/voucher thật — **giữ lại**.

**👉 Đề xuất hành động:** bổ sung `AMAZONFEE`, `B`, `D`, `S` vào hằng số `SERVICE_CODES` của module
làm sạch (Task 2), chạy lại pipeline, rồi mới tính RFM.

---

## 4. Phân phối trên tập giao dịch hợp lệ

**Định nghĩa tập hợp lệ (loại tạm để phân phối không bị nhiễu):**
`valid = df[(~df.IsCancelled) & (~df.IsServiceCode)]` → **525,075 dòng (97.84%)**

| Chỉ số `TotalPrice` | Giá trị |
|---|---:|
| mean | 19.52 |
| std | 271.23 |
| min | −11,062.06 |
| 25% / 50% / 75% | 3.75 / 9.90 / 17.70 |
| max | **168,469.60** |

Trong tập hợp lệ vẫn còn **2,496 dòng `TotalPrice = 0`** và **2 dòng `TotalPrice < 0`**
(`A563186`, `A563187` — *Adjust bad debt*, `Price = −11,062.06`). Hai dòng này được loại khi
vẽ log-transform (vì `log1p` không nhận giá trị âm).


**Đọc biểu đồ:**
- **Histogram thang gốc:** toàn bộ dữ liệu dồn vào một cột sát 0; phải dùng trục y thang log
  mới nhìn thấy đuôi phải kéo dài tới £168k.
- **Boxplot thang gốc:** hộp bị nén thành một vạch — không đọc được gì. Đây là dấu hiệu kinh điển
  của phân phối lệch phải cực mạnh.
- **Sau `log1p`:** phân phối trở thành hình chuông rõ ràng, đỉnh quanh `log1p ≈ 2–3` (tương đương £6–£19).

---

## 5. Outlier theo IQR — hành vi thật hay bất thường?

### 5.1 Ngưỡng IQR

```
Q1 = £3.75 | Q3 = £17.70 | IQR = £13.95
Ngưỡng trên = Q3 + 1.5 × IQR = £38.63
Ngưỡng dưới = Q1 − 1.5 × IQR = −£17.18
```

| | Số dòng | % tập hợp lệ | % doanh thu hợp lệ |
|---|---:|---:|---:|
| **Outlier trên** | **41,124** | **7.83%** | **50.77%** |
| Outlier dưới | 2 | 0.00% | — |

> 🚩 **7.83% số dòng chiếm 50.77% doanh thu.** Loại chúng đi = xóa mất **một nửa doanh thu**
> và toàn bộ nhóm khách hàng giá trị cao — chính là nhóm mà bài toán phân khúc cần tìm nhất.

### 5.2 Chân dung outlier — bằng chứng đây là B2B thật

| Chỉ số | Nhóm outlier | Toàn tập hợp lệ |
|---|---:|---:|
| Số dòng | 41,124 | 525,075 |
| `Quantity` trung vị | **24** | 4 |
| `Price` trung vị | 2.55 | 2.08 |
| % có `Customer ID` | **87.26%** | 74.50% |
| % ngoài United Kingdom | **18.77%** | 8.32% |
| Số khách hàng duy nhất | 2,835 | 4,335 |

**Phân bố quốc gia — outlier lệch mạnh ra khỏi thị trường UK:**

| Country | % trong outlier | % trong tập hợp lệ | Tỷ lệ vượt trội |
|---|---:|---:|---:|
| United Kingdom | 81.23% | 91.68% | 0.89× |
| **Netherlands** | 4.11% | 0.44% | **9.28×** |
| **Japan** | 0.52% | 0.06% | **8.51×** |
| **Australia** | 1.70% | 0.23% | **7.53×** |
| Sweden | 0.45% | 0.08% | 5.56× |
| Norway | 0.59% | 0.20% | 2.97× |
| EIRE | 2.95% | 1.48% | 2.00× |


**Dấu hiệu quyết định — outlier lặp lại có hệ thống ở cùng vài khách hàng:**

| Customer ID | Số dòng outlier |
|---|---:|
| 14646 (Netherlands) | **1,680** |
| 17511 | 670 |
| 12415 | 618 |
| 14911 | 596 |
| 14156 | 549 |

Lỗi nhập liệu **không lặp lại có hệ thống** như vậy. Một khách hàng phát sinh 1,680 giao dịch
giá trị lớn trong 12 tháng là **nhà bán buôn / B2B thật**.

Trong file `outliers_detected.csv`, **31,689 / 41,124 dòng (77.1%)** thỏa ít nhất một trong ba dấu hiệu B2B:

| Dấu hiệu | Số dòng |
|---|---:|
| Mua sỉ (`Quantity ≥ 50`) | 11,229 |
| Ngoài United Kingdom | 7,721 |
| Khách có ≥ 10 dòng outlier | 29,474 |

### 5.3 🚨 Chỉ có 2 trường hợp THẬT SỰ bất thường — và chúng cần xử lý riêng

| Invoice | StockCode | Quantity | TotalPrice | Customer ID | Hóa đơn hủy đối ứng |
|---|---|---:|---:|---|---|
| `581483` | 23843 | 80,995 | **£168,469.60** | 16446 | `C581484` (−80,995) |
| `541431` | 23166 | 74,215 | **£77,183.60** | 12346 | `C541433` (−74,215) |

Cả hai đều là **đơn đặt rồi hủy toàn bộ ngay sau đó**. Đây là lý do quan trọng:

> ⚠️ Quy tắc "loại `IsCancelled`" **một mình là chưa đủ**. Nếu chỉ loại dòng `C` mà giữ dòng gốc,
> Monetary của khách `16446` bị thổi phồng **+£168,470** và khách `12346` **+£77,184** —
> hai khách này sẽ nhảy thẳng lên top Monetary dù thực tế **không mua gì cả**.
> **→ Phải loại cả cặp mua–hủy.**

Ngoài ra, 2 dòng outlier `AMAZONFEE` (£13,541.33) và `B / Adjust bad debt` (£11,062.06)
cũng lọt vào danh sách — thêm bằng chứng cho lỗ hổng ở **mục 3.4**.



### 5.4 Kết luận về outlier

> ❌ **KHÔNG loại outlier** khỏi RFM — đây là hành vi mua sắm thật của nhóm khách giá trị nhất.
> ✅ Thay vào đó: **log-transform Monetary** trước khi đưa vào K-Means (xem mục 6).
> ⚠️ Ngoại lệ duy nhất: 2 cặp mua–hủy ở mục 5.3 và các mã phi-sản-phẩm ở mục 3.4.

---

## 6. Skewness và ảnh hưởng tới bước chuẩn hóa

### 6.1 Mức độ lệch — cực kỳ mạnh, đúng như dự đoán với Online Retail II

| Biến | Skew (gốc) | Skew (sau `log1p`) | Kurtosis (gốc) |
|---|---:|---:|---:|
| `TotalPrice` (cấp dòng, tập hợp lệ) | **506.27** | **0.54** | 296,667.83 |
| `Quantity` (cấp dòng) | 431.59 | 1.02 | 209,762.05 |
| `Price` (cấp dòng) | 61.42 | 0.71 | 131,190.14 |
| **`Monetary` (cấp khách hàng)** | **19.57** | **0.40** | — |
| **`Frequency` (cấp khách hàng)** | **11.95** | **1.21** | — |

**Phân phối Monetary theo khách hàng (4,334 khách):**

| | Giá trị |
|---|---:|
| mean | £2,015.97 |
| **median** | **£662.56** |
| std | £8,903.67 |
| 25% / 75% | £304.24 / £1,631.62 |
| **max** | **£279,138.02** |

Trung bình cao gấp **3× trung vị**, max gấp **421× trung vị** — dấu hiệu điển hình của
đuôi phải do khách B2B.


### 6.2 ⚠️ Lưu ý phương pháp quan trọng

Trên **toàn bộ dữ liệu** (chưa loại đơn hủy), skew `TotalPrice` **đảo dấu thành −0.96** vì dòng hủy
−£168,469 kéo ngược đuôi trái. Đây là bằng chứng độc lập cho việc **phải loại `IsCancelled`
trước khi đánh giá bất kỳ chỉ số phân phối nào** — nếu không, skewness hoàn toàn vô nghĩa.

### 6.3 Hệ quả trực tiếp cho K-Means

K-Means dùng khoảng cách Euclid, nên nhạy tuyệt đối với thang đo:

- Trên thang gốc, khoảng cách giữa các khách bị chi phối hoàn toàn bởi vài khách B2B →
  kết quả điển hình là **1 cụm khổng lồ chứa >99% khách + vài cụm chỉ 1–2 khách**.
- `StandardScaler` **không** giải quyết được: nó chuẩn hóa mean/std nhưng **giữ nguyên hình dạng lệch**.
- `log1p` đưa skew Monetary từ **19.57 → 0.40** (gần chuẩn) và Frequency **11.95 → 1.21**,
  đồng thời **giữ nguyên toàn bộ 4,333 khách** — không mất dữ liệu như winsorize hay cắt outlier.

> **Thứ tự bắt buộc ở Giai đoạn 2:** `log1p(Monetary)`, `log1p(Frequency)` → **rồi mới** `StandardScaler` → K-Means.

### 6.4 So sánh nhóm thiếu `Customer ID` — khác biệt rõ rệt

| Chỉ số | Thiếu `Customer ID` | Có `Customer ID` |
|---|---:|---:|
| Số dòng | **135,037 (25.16%)** | 401,605 (74.84%) |
| Tổng `TotalPrice` | £1,447,487.53 (**14.88%**) | £8,278,537.42 (85.12%) |
| `TotalPrice` trung vị | **£4.96** | £11.70 |
| `Quantity` trung vị | **1** | 5 |
| `Price` trung vị | £3.29 | £1.95 |
| Số dòng / hóa đơn (trung vị) | **1** | **12** |
| Giá trị hóa đơn (trung vị) | **£0.00** | **£239.41** |
| Tỷ lệ `PriceAnomaly` (`Price ≤ 0`) | **1.80%** | 0.00% |
| Thiếu `Description` | 1.08% | 0.00% |

**Phân bố quốc gia — tập trung bất thường vào UK:**

| Country | Thiếu ID (%) | Có ID (%) |
|---|---:|---:|
| **United Kingdom** | **98.92%** | 88.83% |
| EIRE | 0.53% | 1.86% |
| Hong Kong | 0.21% | — |
| France | 0.05% | 2.11% |

**`StockCode` tập trung:** `DOT` (694 dòng — DOTCOM POSTAGE), rồi mới đến sản phẩm thật
(`85099B`, `21931`, `22411`…).

> **Kết luận:** nhóm thiếu `Customer ID` **chiếm 25.16% số dòng nhưng chỉ 14.88% doanh thu**,
> có cấu trúc hóa đơn hoàn toàn khác (1 dòng & £0.00/hóa đơn so với 12 dòng & £239.41),
> gần như chỉ đến từ UK, và tập trung ở mã vận chuyển `DOT`.
> Phần lớn là **bút toán lẻ, điều chỉnh kho, bán tại quầy** — không quy được về khách hàng nào.
>
> ❌ **Loại khỏi RFM** (RFM bắt buộc có khóa `Customer ID`).
> ✅ **Giữ lại cho dashboard doanh thu tổng** — 14.88% doanh thu này là thật, không được bỏ khỏi báo cáo.

---

## 7. 📋 BẢNG KHUYẾN NGHỊ CHO VIỆC TÍNH RFM

| # | Vấn đề | Quy mô | Ảnh hưởng | **Khuyến nghị** | Lý do |
|---|---|---|---|---|---|
| 1 | `IsCancelled = True` | 9,251 dòng (1.72%)<br>−£893,979.73 | 100% có `Quantity` âm; cộng dồn làm **giảm ảo** Monetary ~8.42%, đẩy nhầm khách hay trả hàng vào cụm giá trị thấp | ❌ **LOẠI** khỏi cả Monetary và Frequency | Hủy đơn là sự kiện đảo chiều, không phải hành vi mua. Nên tách thành đặc trưng phụ `CancelRate` để phân tích lòng trung thành |
| 2 | Dòng gốc của cặp mua–hủy<br>(`581483`, `541431`) | 2 cặp: 80,995 & 74,215 chiếc | Chỉ loại dòng `C` mà giữ dòng gốc → Monetary khách `16446` **+£168,470**, khách `12346` **+£77,184** | ❌ **LOẠI cả cặp**<br>(match Invoice/StockCode/Quantity đối ứng) | Giao dịch đã bị hủy toàn bộ, không phát sinh doanh thu thật |
| 3 | `IsServiceCode = True` | 2,730 dòng (0.51%)<br>+£195,336.86 | Chỉ 2.01% doanh thu toàn cục nhưng bóp méo Monetary của **542 khách**; **257 khách lệch > 10%**, cá biệt **+412%** | ❌ **LOẠI** khỏi toàn bộ RFM | `POST`/`DOT`/`M`/`BANK CHARGES`/`CRUK` là phí vận chuyển, chỉnh tay, phí ngân hàng, quyên góp — không phản ánh hành vi mua sản phẩm |
| 4 | Mã phi-sản-phẩm **chưa gắn cờ**:<br>`AMAZONFEE`, `B`, `D`, `S` | 176 dòng<br>ròng −£241,318.43 | `AMAZONFEE` một mình ròng **−£221,520** — lớn hơn mọi mã đang gắn cờ; **hiện đang được tính vào Monetary** | ⚠️ **BỔ SUNG** vào `SERVICE_CODES` (Task 2) rồi mới loại | Phí sàn Amazon, bút toán nợ xấu, chiết khấu, hàng mẫu — cùng bản chất với nhóm mã dịch vụ |
| 5 | `PriceAnomaly` (`Price ≤ 0`) | 2,512 dòng (0.47%)<br>ròng −£22,124.12 | 2,510 dòng `Price = 0` đóng góp £0 nhưng **thổi phồng Frequency**; 2 dòng `Price < 0` (*Adjust bad debt*) **giảm** Monetary £22,124 | ❌ **LOẠI** khỏi RFM (tỷ trọng không đáng kể) | Chỉ 40/2,512 dòng có `Customer ID`; Description là `check`/`damages`/`?`/`found` → bút toán điều chỉnh kho, **không phải khuyến mãi**. Lưu ý cờ này gồm cả `Price` âm |
| 6 | `Quantity < 0` nhưng `IsCancelled = False` | 1,336 dòng<br>£0 | Trùng hoàn toàn với nhóm `Price = 0`; làm sai lệch Frequency | ❌ **LOẠI** (đã nằm trong quy tắc #5) | Toàn bộ đều `Price = 0` và không có `Customer ID` — bút toán ghi giảm kho |
| 7 | `HasCustomerID = False` | 135,037 dòng (25.16%)<br>£1,447,487.53 (14.88%) | Không gom nhóm được theo khách; hành vi khác hẳn (98.92% từ UK; 1 dòng & £0.00/hóa đơn trung vị) | ❌ **LOẠI** khỏi RFM<br>✅ **GIỮ** cho dashboard doanh thu | RFM bắt buộc có khóa `Customer ID`. Nhưng 14.88% doanh thu là thật, không được bỏ khỏi báo cáo tổng |
| 8 | **Outlier `TotalPrice` cao (B2B)** | 41,124 dòng (7.83%)<br>**50.77% doanh thu** | Kéo lệch tâm cụm K-Means → 1 cụm khổng lồ + vài cụm 1–2 khách | ✅ **GIỮ — KHÔNG loại**<br>🔄 **log-transform** Monetary | **Hành vi THẬT**: 18.77% ngoài UK (nền 8.32%), Netherlands 9.28×, 87.3% có `Customer ID`, lặp lại có hệ thống (ID 14646: 1,680 dòng). Loại đi = xóa mất nhóm khách giá trị nhất |
| 9 | **Skewness cực mạnh**<br>(Monetary = 19.57) | ~4,333 khách hàng | Khoảng cách Euclid bị chi phối bởi vài khách B2B; K-Means chia cụm vô nghĩa | 🔄 `log1p(Monetary)`, `log1p(Frequency)`<br>→ **rồi mới** `StandardScaler` | log1p đưa skew Monetary **19.57 → 0.40** và Frequency **11.95 → 1.21**, giữ nguyên toàn bộ khách hàng thay vì mất dữ liệu như winsorize / cắt outlier |


---

## 8. Kiểm chứng — bộ lọc đề xuất giữ lại bao nhiêu dữ liệu?

| Bước lọc | Số dòng | % còn lại | Tổng `TotalPrice` |
|---|---:|---:|---:|
| Dữ liệu đã làm sạch (Task 2) | 536,642 | 100.00% | £9,726,024.95 |
| − `IsCancelled` | 527,391 | 98.28% | £10,620,004.68 |
| − `IsServiceCode` + 4 mã bổ sung | 525,068 | 97.84% | £10,247,907.68 |
| − cặp mua–hủy + `Price ≤ 0` + thiếu `Customer ID` | **391,151** | **72.89%** | **£8,491,574.44** |

**▶ Tập sẵn sàng tính RFM: 391,151 dòng | 4,333 khách hàng | £8,491,574.44**
`skew(Monetary) = 20.91 → sau log1p = 0.36`

Bộ lọc giữ lại **72.89% số dòng**. Đối chiếu với chuẩn đúng — doanh thu **không hủy** và
**quy được về khách hàng** là £8,887,226.89 — tập RFM giữ lại **95.55%**; phần chênh 4.45% chính là
mã dịch vụ, `Price ≤ 0` và cặp mua–hủy đã cố ý loại. Phần bị loại lớn nhất là nhóm thiếu
`Customer ID` (25.16% số dòng) — vốn dĩ không dùng được cho RFM.

> 📌 Sau khi loại các trường hợp đặc biệt, skew Monetary **tăng nhẹ** (19.57 → 20.91) vì tổng
> giảm trong khi khách B2B lớn nhất (ID 14646, £279,138) vẫn còn nguyên. Điều này **khẳng định lại**
> rằng lọc dữ liệu không thay thế được log-transform — **cả hai đều cần**.

---

## 9. Tiêu chí hoàn thành

| Tiêu chí | Trạng thái | Vị trí |
|---|---|---|
| So sánh thống kê nhóm `IsCancelled` True/False, xác nhận quan hệ với `Quantity` âm | ✅ | Mục 2 |
| Đánh giá tỷ trọng và ảnh hưởng của `IsServiceCode` lên tổng Monetary | ✅ | Mục 3 |
| Biểu đồ phân phối/boxplot trên tập hợp lệ | ✅ | Mục 4 + `outputs/figures/` |
| Xác định outlier bằng IQR, phân biệt B2B thật vs bất thường | ✅ | Mục 5 + `outliers_detected.csv` |
| Đánh giá skewness, ghi chú ảnh hưởng đến chuẩn hóa Monetary | ✅ | Mục 6 |
| Bảng khuyến nghị cụ thể (loại/giữ/transform) gửi Leader | ✅ | Mục 7 |

---

## 10. Đề xuất cho Task 1 — Giai đoạn 2 (định nghĩa công thức RFM)

RFM đề xuất như sau:

```python

# --- Bước 1: lọc về tập giao dịch mua thật ---
PAIRED_CANCELLED = {("581483", "23843"), ("541431", "23166")}

txn = df[
      (~df.IsCancelled)             # loại hóa đơn hủy
    & (~df.IsServiceCode)           # loại phí vận chuyển / chỉnh tay / phí NH
    & (~df.PriceAnomaly)            # loại Price <= 0 (gồm cả bút toán điều chỉnh kho)
    & (df.HasCustomerID)            # RFM bắt buộc có khóa Customer ID
    & (~is_paired_cancelled_order)  # loại dòng gốc của cặp mua-hủy
    & (df.TotalPrice > 0)
]

# --- Bước 2: tính RFM ---
snapshot = txn.InvoiceDate.max() + pd.Timedelta(days=1)   # 2011-12-10

rfm = txn.groupby("Customer ID").agg(
    Recency   = ("InvoiceDate", lambda s: (snapshot - s.max()).days),
    Frequency = ("Invoice",     "nunique"),   # đếm HÓA ĐƠN, không đếm dòng
    Monetary  = ("TotalPrice",  "sum"),
)

# --- Bước 3: chuẩn hóa TRƯỚC khi K-Means ---
rfm_scaled = StandardScaler().fit_transform(
    rfm.assign(
        Frequency = np.log1p(rfm.Frequency),   # skew 11.95 -> 1.21
        Monetary  = np.log1p(rfm.Monetary),    # skew 19.57 -> 0.40
    )
)
```

**Lưu ý bổ sung:**
- `Frequency` phải đếm **số hóa đơn duy nhất** (`nunique`), **không** đếm số dòng —
  vì trung vị 12 dòng/hóa đơn sẽ thổi phồng Frequency gấp ~12 lần.
- `Recency` không cần transform (phân phối gần đều theo ngày).
- Nên giữ thêm cột phụ `CancelRate` (tỷ lệ hóa đơn hủy / tổng hóa đơn) để làm giàu chân dung cụm
  ở bước diễn giải — không đưa vào K-Means.

---
