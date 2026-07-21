# 🛍️ CUSTOMER SEGMENTATION USING RFM
## Tên dự án : **So sánh các thuật toán phân cụm trong bài toán Phân khúc Khách hàng**

---

## Dẫn nhập

Trong lĩnh vực bán lẻ và thương mại điện tử, doanh nghiệp liên tục thu thập lượng lớn dữ liệu giao dịch từ khách hàng. Tuy nhiên, không phải tất cả khách hàng đều có hành vi mua sắm giống nhau. Việc áp dụng cùng một chiến lược marketing cho toàn bộ khách hàng thường làm giảm hiệu quả kinh doanh và gây lãng phí nguồn lực.

Phân khúc khách hàng (Customer Segmentation) là một trong những bài toán quan trọng của khoa học dữ liệu, giúp doanh nghiệp chia khách hàng thành các nhóm có hành vi tương đồng để xây dựng các chiến lược marketing, chăm sóc khách hàng và tối ưu doanh thu.

Chính vì vậy, trong dự án này, nhóm sử dụng mô hình **RFM (Recency – Frequency – Monetary)** để biểu diễn hành vi mua sắm của khách hàng và tiến hành so sánh ba thuật toán phân cụm phổ biến:

- K-Means
- Gaussian Mixture Model (GMM)
- HDBSCAN

Dự án được xây dựng dưới dạng một **Web Application**, cho phép người dùng tải dữ liệu, thực hiện tiền xử lý, phân cụm, trực quan hóa kết quả và xuất báo cáo một cách trực quan.

---

## Mục lục

- [Dẫn nhập](#dẫn-nhâp)
- [Giới thiệu dự án](#giới-thiệu-dự-án)
- [Mục tiêu dự án](#mục-tiêu-dự-án)
- [Bộ dữ liệu](#bộ-dữ-liệu)
- [Pipeline dự án](#pipeline-dự-án)
- [Vai trò thành viên](#vai-trò-thành-viên)
- [Bảng cân bằng khối lượng công việc](#bảng-cân-bằng-khối-lượng-công-việc)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Cấu trúc mã nguồn](#cấu-trúc-mã-nguồn)
- [Cơ chế cộng tác](#cơ-chế-cộng-tác)
- [Sản phẩm đầu ra](#sản-phẩm-đầu-ra)
- [Kết quả mong đợi](#kết-quả-mong-đợi)

---

## Giới thiệu dự án

Dự án xây dựng một hệ thống hỗ trợ **phân khúc khách hàng dựa trên dữ liệu giao dịch bán lẻ**.

Người dùng có thể:

- Upload dữ liệu giao dịch.
- Làm sạch và chuẩn hóa dữ liệu.
- Xây dựng đặc trưng RFM.
- Thực hiện phân cụm bằng nhiều thuật toán.
- Điều chỉnh tham số mô hình.
- So sánh kết quả giữa các thuật toán.
- Trực quan hóa các cụm khách hàng.
- Xuất kết quả dưới dạng CSV.

Khác với các dự án chỉ sử dụng một thuật toán phân cụm, hệ thống hỗ trợ đồng thời:

- K-Means
- Gaussian Mixture Model (GMM)
- HDBSCAN

Nhờ đó, người dùng có thể đánh giá ưu điểm và hạn chế của từng thuật toán trên cùng một tập dữ liệu.

---

## Mục tiêu dự án

### Mục tiêu tổng quát

Xây dựng hệ thống phân khúc khách hàng dựa trên mô hình RFM và so sánh hiệu quả của các thuật toán phân cụm nhằm hỗ trợ doanh nghiệp hiểu rõ hành vi khách hàng và đưa ra quyết định kinh doanh.

### Mục tiêu cụ thể

- Xây dựng quy trình tiền xử lý dữ liệu giao dịch.
- Biểu diễn khách hàng thông qua đặc trưng RFM.
- Triển khai ba thuật toán: K-Means, Gaussian Mixture Model, HDBSCAN.
- Đánh giá chất lượng phân cụm bằng nhiều chỉ số.
- Phân tích ưu điểm và hạn chế của từng thuật toán.
- Trực quan hóa kết quả phân cụm.
- Xây dựng Web App hỗ trợ phân tích tương tác.

---

## Bộ dữ liệu

### Dataset

**Online Retail II**

Đây là bộ dữ liệu giao dịch bán lẻ trực tuyến của một doanh nghiệp tại Vương quốc Anh, được công bố bởi UCI Machine Learning Repository và phổ biến trên Kaggle.

### Đặc điểm

- Khoảng 1 triệu giao dịch.
- Hơn 5.000 khách hàng.
- Dữ liệu giao dịch trong nhiều năm.
- Bao gồm nhiều quốc gia.

### Các thuộc tính chính

| Thuộc tính | Mô tả |
|------------|-------|
| InvoiceNo | Mã hóa đơn |
| StockCode | Mã sản phẩm |
| Description | Tên sản phẩm |
| Quantity | Số lượng |
| InvoiceDate | Thời gian giao dịch |
| UnitPrice | Đơn giá |
| CustomerID | Mã khách hàng |
| Country | Quốc gia |

### Lý do lựa chọn

- Dữ liệu thực tế.
- Đủ lớn để đánh giá các thuật toán phân cụm.
- Có thể xây dựng đặc trưng RFM.
- Được sử dụng rộng rãi trong nghiên cứu Customer Segmentation.

---

## Pipeline dự án

Dự án được triển khai theo **bốn Epic**, bám sát đúng luồng xử lý của ứng dụng Streamlit: **Upload → Làm sạch → RFM → Phân cụm & đánh giá → Trực quan hóa & bàn giao**. Mỗi Epic có 5 task, mỗi task gán đúng 1 vai trò phụ trách — đảm bảo khối lượng công việc đồng đều giữa 5 thành viên trong suốt cả 4 Epic.

### Epic 1 — Khám phá, Làm sạch & Chuẩn hóa dữ liệu

**Vì sao cần Epic này:** Đây là nền móng của toàn bộ pipeline. Mọi bước sau (RFM, phân cụm, kết quả) đều phụ thuộc vào dữ liệu sạch — sai ngay từ đầu sẽ lan lỗi xuống toàn hệ thống ("garbage in, garbage out"), nên cần tách thành Epic riêng và xử lý kỹ ngay từ đầu.

| Task | Vai trò | Lý do |
|---|---|---|
| Định nghĩa chuẩn schema dữ liệu đầu vào & viết tài liệu định dạng file | Leader | Thống nhất "hợp đồng dữ liệu" trước khi các role khác bắt tay code, tránh mỗi người hiểu định dạng một kiểu |
| Viết hàm làm sạch dữ liệu (loại thiếu / trùng / đơn hủy) | Data | Xử lý dữ liệu thô cốt lõi, quyết định trực tiếp chất lượng RFM tính ở Epic sau |
| Xây UI upload file & ánh xạ cột linh hoạt | Pipeline | Người dùng thật có định dạng file khác nhau, cần giao diện để họ tự chọn cột thay vì hard-code tên cột |
| Phân tích thống kê sơ bộ dữ liệu sạch (phân phối, outlier) | Model | K-Means và GMM rất nhạy với outlier — cần biết đặc điểm dữ liệu trước để chuẩn bị xử lý ở Epic sau |
| Viết test case & hiển thị cảnh báo lỗi khi dữ liệu không hợp lệ | QA/QC | Upload là nơi dễ phát sinh lỗi nhất — cần chặn lỗi sớm trước khi lan xuống pipeline |

### Epic 2 — Biểu diễn đặc trưng RFM

**Vì sao cần Epic này:** RFM là "ngôn ngữ chung" mà cả 3 thuật toán đều dùng làm input. Đây là bước feature engineering có logic nghiệp vụ riêng — sai công thức ở đây thì dù thuật toán tốt đến đâu, kết quả cũng vô nghĩa. Cần tách Epic riêng để kiểm soát chặt.

| Task | Vai trò | Lý do |
|---|---|---|
| Định nghĩa công thức RFM chuẩn & mốc thời gian snapshot | Leader | Recency phụ thuộc vào "ngày tham chiếu" — cần thống nhất cách tính để không lệch kết quả giữa các lần chạy |
| Viết hàm tính Recency, Frequency, Monetary | Data | Logic tính toán lõi, biến giao dịch thô thành 3 đặc trưng dùng cho mô hình |
| Xử lý Outlier & chuẩn hóa dữ liệu (log-transform, scaling) | Model | Thuật toán dựa trên khoảng cách rất nhạy thang đo — bước này quyết định chất lượng cụm về sau |
| Xây giao diện hiển thị bảng RFM & biểu đồ phân phối | Pipeline | Người dùng cần "nhìn thấy" dữ liệu trung gian trước khi phân cụm để tin tưởng kết quả cuối |
| Kiểm thử công thức RFM trên tập dữ liệu mẫu có đáp án biết trước | QA/QC | Sai ở bước này sẽ kéo theo sai toàn bộ kết quả phân cụm — cần chốt đúng trước khi đi tiếp |

### Epic 3 — Huấn luyện & Đánh giá mô hình

**Vì sao cần Epic này:** Đây là lõi kỹ thuật, trả lời trực tiếp câu hỏi nghiên cứu của nhóm. Phức tạp nhất, cần nhiều vòng thử nghiệm và chuyên môn ML sâu, nên tách riêng để tập trung nguồn lực.

| Task | Vai trò | Lý do |
|---|---|---|
| Định nghĩa tiêu chí "một lần chạy hợp lệ" & điều phối thử nghiệm 3 thuật toán | Leader | 3 thuật toán chạy song song — cần khung thống nhất để so sánh công bằng, tránh mỗi thuật toán một chuẩn |
| Chuẩn bị & kiểm tra lại tập dữ liệu train cho từng thuật toán | Data | Input sai (NaN sau scaling, rò rỉ dữ liệu) khiến model chạy được nhưng cho kết quả vô nghĩa |
| Triển khai K-Means, Gaussian Mixture Model, HDBSCAN với tham số điều chỉnh được qua UI | Model | Nhiệm vụ kỹ thuật trung tâm — trực tiếp trả lời câu hỏi nghiên cứu "thuật toán nào cân bằng tốt nhất" |
| Xây state management (đổi tham số → chạy lại không load lại toàn app) | Pipeline | Trải nghiệm tương tác mượt là yêu cầu cốt lõi của một web app — không để người dùng chờ load lại mỗi lần đổi tham số |
| Viết & kiểm tra chỉ số đánh giá (Silhouette Score, Davies-Bouldin Index, Calinski-Harabasz Index) | QA/QC | Đây là "trọng tài" khách quan để so sánh 3 thuật toán — phải đảm bảo tính đúng của chỉ số trước khi dùng để kết luận |

### Epic 4 — Phân tích & Trực quan hóa

**Vì sao cần Epic này:** Kết quả phân cụm chỉ có giá trị khi người dùng không chuyên hiểu và dùng được. Epic này biến số liệu kỹ thuật thành thông tin dễ hiểu và đóng gói sản phẩm để bàn giao — thiếu Epic này thì 3 Epic trước chỉ là "đồ chơi nội bộ", không ai dùng được.

| Task | Vai trò | Lý do |
|---|---|---|
| Tổng hợp báo cáo so sánh 3 thuật toán & đưa khuyến nghị cuối cùng | Leader | Cần một người chịu trách nhiệm kết luận cuối cùng, thay vì để kết quả rời rạc, mỗi người hiểu một kiểu |
| Đặt tên & mô tả nghiệp vụ cho từng cụm dựa trên RFM trung bình | Data | Con số cụm 0, 1, 2 vô nghĩa với người không chuyên — cần "dịch" sang ngôn ngữ kinh doanh (VD: "khách VIP", "khách sắp rời bỏ") |
| Viết bảng so sánh định lượng 3 thuật toán kèm giải thích khi nào nên dùng cái nào | Model | Câu trả lời trực tiếp cho câu hỏi nghiên cứu — cần người hiểu sâu thuật toán để diễn giải đúng, tránh đọc sai chỉ số |
| Xây Dashboard (biểu đồ PCA 2D, bảng cluster profile) & chức năng xuất CSV | Pipeline | Đây là "bộ mặt" của sản phẩm — quyết định trải nghiệm và mức độ tin cậy của người dùng cuối |
| Kiểm thử toàn hệ thống từ upload đến xuất kết quả (UAT), thu thập phản hồi | QA/QC | Lần kiểm tra cuối cùng trước khi sản phẩm đến tay người dùng thật — phát hiện lỗi mà các Epic riêng lẻ không thấy được |

---

## Vai trò thành viên

| Vai trò | Trách nhiệm |
|----------|-------------|
| **Leader** | Quản lý dự án, thiết kế pipeline, tổng hợp báo cáo, điều phối tiến độ |
| **Data** | Data Profiling, làm sạch dữ liệu, xây dựng đặc trưng RFM |
| **Model** | Triển khai K-Means, GMM, HDBSCAN và đánh giá mô hình |
| **Pipeline** | Xây dựng Web App, giao diện người dùng, dashboard, export dữ liệu |
| **QA/QC** | Kiểm thử dữ liệu, kiểm thử hệ thống và đảm bảo chất lượng |

---

## Bảng cân bằng khối lượng công việc

Mỗi vai trò đảm nhận đúng 1 task trong mỗi Epic — đảm bảo không ai gánh nhiều hơn ai, và mọi thành viên đều tham gia xuyên suốt cả 4 giai đoạn của dự án thay vì chỉ hiểu mảnh việc riêng của mình.

| Vai trò | Epic 1 | Epic 2 | Epic 3 | Epic 4 | Tổng |
|---|---|---|---|---|---|
| Leader | 1 | 1 | 1 | 1 | 4 |
| Data | 1 | 1 | 1 | 1 | 4 |
| Model | 1 | 1 | 1 | 1 | 4 |
| Pipeline | 1 | 1 | 1 | 1 | 4 |
| QA/QC | 1 | 1 | 1 | 1 | 4 |

---

## Công nghệ sử dụng

### Ngôn ngữ
- Python

### Data Processing
- Pandas
- NumPy

### Machine Learning
- Scikit-learn
- HDBSCAN

### Visualization
- Matplotlib
- Plotly

### Web Framework
- Streamlit

### Version Control
- Git
- GitHub

---

## Cấu trúc mã nguồn

```text
Customer-Segmentation/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
│
├── notebooks/
│
├── src/
│   ├── data/
│   ├── features/
│   ├── models/
│   ├── visualization/
│   ├── utils/
│   └── app/
│
├── tests/
│
├── docs/
│
├── outputs/
│   ├── figures/
│   ├── reports/
│   └── results/
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Cơ chế cộng tác

Nhóm sử dụng GitHub để quản lý mã nguồn theo mô hình Git Workflow.

### Quy trình

1. Tạo Issue.
2. Tạo Branch.
3. Phát triển tính năng.
4. Commit.
5. Push.
6. Pull Request.
7. Code Review.
8. Merge vào `main`.

### Quy ước Branch

```
main
develop
feature/<feature-name>
bugfix/<bug-name>
hotfix/<bug-name>
```

### Quy ước Commit

```
feat:
fix:
docs:
style:
refactor:
test:
chore:
```

Ví dụ:

```
feat: implement K-Means clustering

fix: handle missing CustomerID

docs: update README

refactor: optimize RFM pipeline
```

---

## Sản phẩm đầu ra

Sau khi hoàn thành, dự án cung cấp:

- Web Application phân khúc khách hàng.
- Pipeline xử lý dữ liệu hoàn chỉnh.
- Module xây dựng đặc trưng RFM.
- Công cụ so sánh K-Means, GMM và HDBSCAN.
- Dashboard trực quan.
- Báo cáo phân tích.
- File CSV kết quả phân cụm.
- Mã nguồn mở trên GitHub.

---

## Kết quả mong đợi

- Hiểu rõ hành vi khách hàng thông qua RFM.
- So sánh toàn diện ba thuật toán phân cụm.
- Hỗ trợ lựa chọn thuật toán phù hợp cho từng bài toán Customer Segmentation.
- Xây dựng hệ thống có khả năng tái sử dụng trên các bộ dữ liệu giao dịch khác.

---

## Nhóm phát triển

**Project:** Customer Segmentation using RFM

**Dataset:** Online Retail II

**Algorithms:** K-Means • Gaussian Mixture Model • HDBSCAN

**Language:** Python

**Framework:** Streamlit

**License:** MIT
