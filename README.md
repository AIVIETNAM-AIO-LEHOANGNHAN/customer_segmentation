````markdown
# 🛍️ Customer Segmentation using RFM
## Tên dự án : So sánh hiệu năng các thuật toán phân cụm trong bài toán Phân khúc Khách hàng

---

# Giới thiệu

Trong lĩnh vực bán lẻ và thương mại điện tử, doanh nghiệp liên tục thu thập lượng lớn dữ liệu giao dịch từ khách hàng. Tuy nhiên, không phải tất cả khách hàng đều có hành vi mua sắm giống nhau. Việc áp dụng cùng một chiến lược marketing cho toàn bộ khách hàng thường làm giảm hiệu quả kinh doanh và gây lãng phí nguồn lực.

Phân khúc khách hàng (Customer Segmentation) là một trong những bài toán quan trọng của khoa học dữ liệu, giúp doanh nghiệp chia khách hàng thành các nhóm có hành vi tương đồng để xây dựng các chiến lược marketing, chăm sóc khách hàng và tối ưu doanh thu.

Trong dự án này, nhóm sử dụng mô hình **RFM (Recency – Frequency – Monetary)** để biểu diễn hành vi mua sắm của khách hàng và tiến hành so sánh ba thuật toán phân cụm phổ biến:

- K-Means
- Gaussian Mixture Model (GMM)
- HDBSCAN

Dự án được xây dựng dưới dạng một **Web Application**, cho phép người dùng tải dữ liệu, thực hiện tiền xử lý, phân cụm, trực quan hóa kết quả và xuất báo cáo một cách trực quan.

---

# Mục lục

- [Giới thiệu](#giới-thiệu)
- [Giới thiệu dự án](#giới-thiệu-dự-án)
- [Mục tiêu dự án](#mục-tiêu-dự-án)
- [Bộ dữ liệu](#bộ-dữ-liệu)
- [Pipeline dự án](#pipeline-dự-án)
- [Vai trò thành viên](#vai-trò-thành-viên)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Cấu trúc mã nguồn](#cấu-trúc-mã-nguồn)
- [Cơ chế cộng tác](#cơ-chế-cộng-tác)
- [Sản phẩm đầu ra](#sản-phẩm-đầu-ra)

---

# Giới thiệu dự án

Dự án xây dựng một hệ thống hỗ trợ **Phân khúc khách hàng dựa trên dữ liệu giao dịch bán lẻ**.

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

# Mục tiêu dự án

## Mục tiêu tổng quát

Xây dựng hệ thống phân khúc khách hàng dựa trên mô hình RFM và so sánh hiệu quả của các thuật toán phân cụm nhằm hỗ trợ doanh nghiệp hiểu rõ hành vi khách hàng và đưa ra quyết định kinh doanh.

## Mục tiêu cụ thể

- Xây dựng quy trình tiền xử lý dữ liệu giao dịch.
- Biểu diễn khách hàng thông qua đặc trưng RFM.
- Triển khai ba thuật toán:
  - K-Means
  - Gaussian Mixture Model
  - HDBSCAN
- Đánh giá chất lượng phân cụm bằng nhiều chỉ số.
- Phân tích ưu điểm và hạn chế của từng thuật toán.
- Trực quan hóa kết quả phân cụm.
- Xây dựng Web App hỗ trợ phân tích tương tác.

---

# Bộ dữ liệu

## Dataset

**Online Retail II**

Đây là bộ dữ liệu giao dịch bán lẻ trực tuyến của một doanh nghiệp tại Vương quốc Anh, được công bố bởi UCI Machine Learning Repository và phổ biến trên Kaggle.

## Đặc điểm

- Khoảng 1 triệu giao dịch.
- Hơn 5.000 khách hàng.
- Dữ liệu giao dịch trong nhiều năm.
- Bao gồm nhiều quốc gia.

## Các thuộc tính chính

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

## Lý do lựa chọn

- Dữ liệu thực tế.
- Đủ lớn để đánh giá các thuật toán phân cụm.
- Có thể xây dựng đặc trưng RFM.
- Được sử dụng rộng rãi trong nghiên cứu Customer Segmentation.

---

# Pipeline dự án

Dự án được triển khai theo bốn Epic chính.

## Epic 1 — Khám phá, Làm sạch & Chuẩn hóa dữ liệu

- Upload dữ liệu.
- Kiểm tra schema.
- Data Profiling.
- Làm sạch dữ liệu.
- Chuẩn hóa dữ liệu.
- Data Quality Validation.

## Epic 2 — Biểu diễn đặc trưng RFM

- Xây dựng Recency.
- Xây dựng Frequency.
- Xây dựng Monetary.
- Xử lý Outlier.
- Chuẩn hóa dữ liệu.
- Hiển thị bảng RFM.

## Epic 3 — Phân cụm & Đánh giá mô hình

Triển khai:

- K-Means
- Gaussian Mixture Model
- HDBSCAN

Đánh giá bằng:

- Silhouette Score
- Davies-Bouldin Index
- Calinski-Harabasz Index

## Epic 4 — Phân tích, Trực quan hóa & Bàn giao

- Phân tích kết quả.
- So sánh các thuật toán.
- Diễn giải các cụm khách hàng.
- Dashboard.
- Xuất CSV.
- Kiểm thử toàn hệ thống.

---

# Vai trò thành viên

| Vai trò | Trách nhiệm |
|----------|-------------|
| **Leader** | Quản lý dự án, thiết kế pipeline, tổng hợp báo cáo, điều phối tiến độ |
| **Data** | Data Profiling, làm sạch dữ liệu, xây dựng đặc trưng RFM |
| **Model** | Triển khai K-Means, GMM, HDBSCAN và đánh giá mô hình |
| **Pipeline** | Xây dựng Web App, giao diện người dùng, dashboard, export dữ liệu |
| **QA/QC** | Kiểm thử dữ liệu, kiểm thử hệ thống và đảm bảo chất lượng |

---

# Công nghệ sử dụng

## Ngôn ngữ

- Python

## Data Processing

- Pandas
- NumPy

## Machine Learning

- Scikit-learn
- HDBSCAN

## Visualization

- Matplotlib
- Plotly

## Web Framework

- Streamlit

## Version Control

- Git
- GitHub

---

# Cấu trúc mã nguồn

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

# Cơ chế cộng tác

Nhóm sử dụng GitHub để quản lý mã nguồn theo mô hình Git Workflow.

## Quy trình

1. Tạo Issue.
2. Tạo Branch.
3. Phát triển tính năng.
4. Commit.
5. Push.
6. Pull Request.
7. Code Review.
8. Merge vào `main`.

## Quy ước Branch

```
main
develop
feature/<feature-name>
bugfix/<bug-name>
hotfix/<bug-name>
```

## Quy ước Commit

```
feat:
fix:
docs:
style:
refactor:
test:
chore:
```

Ví dụ

```
feat: implement K-Means clustering

fix: handle missing CustomerID

docs: update README

refactor: optimize RFM pipeline
```

---

# Sản phẩm đầu ra

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

# Kết quả mong đợi

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
````
