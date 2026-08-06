# Task 11 : Tiêu chí đánh giá và lựa chọn mô hình phân cụm

## 1. Xác định các thuật toán phân cụm

### 1.1. Mục tiêu

Mục tiêu của bước này là thống nhất các thuật toán phân cụm sẽ được sử dụng trong dự án Customer Segmentation và xác định vai trò của từng thuật toán trong quá trình thực nghiệm. Việc lựa chọn trước các thuật toán giúp toàn bộ nhóm triển khai theo cùng một định hướng, đảm bảo các kết quả thu được có thể so sánh một cách công bằng và nhất quán.

---

### 1.2. Danh sách thuật toán sử dụng

Dự án sử dụng ba thuật toán phân cụm sau:

| Thuật toán | Vai trò |
|------------|----------|
| K-Means | Mô hình phân cụm cơ sở (Baseline Model) |
| Gaussian Mixture Model (GMM) | Mô hình phân cụm xác suất |
| HDBSCAN | Mô hình phân cụm theo mật độ |

---

### 1.3. Mô tả từng thuật toán

#### 1.3.1. K-Means

K-Means được lựa chọn làm mô hình cơ sở của dự án nhờ khả năng triển khai đơn giản, tốc độ huấn luyện nhanh và dễ diễn giải kết quả. Thuật toán hoạt động bằng cách chia dữ liệu thành *K* cụm sao cho tổng khoảng cách từ mỗi điểm dữ liệu đến tâm cụm là nhỏ nhất.

Trong dự án này, K-Means đóng vai trò là mô hình tham chiếu để so sánh với các thuật toán còn lại. Đây cũng là thuật toán được sử dụng phổ biến trong các bài toán Customer Segmentation.

##### Ưu điểm

- Dễ cài đặt và triển khai.
- Thời gian huấn luyện nhanh.
- Kết quả dễ giải thích.
- Phù hợp với dữ liệu đã được chuẩn hóa.

##### Hạn chế

- Phải xác định trước số cụm.
- Nhạy cảm với Outlier.
- Giả định các cụm có dạng hình cầu.
- Không xử lý tốt dữ liệu có mật độ phức tạp.

##### Trường hợp áp dụng phù hợp

K-Means phù hợp khi dữ liệu đã được chuẩn hóa và các cụm có hình dạng tương đối rõ ràng.

---

#### 1.3.2. Gaussian Mixture Model (GMM)

Gaussian Mixture Model là thuật toán phân cụm dựa trên mô hình xác suất. Thay vì gán cứng mỗi khách hàng vào một cụm, GMM ước lượng xác suất một khách hàng thuộc về từng cụm thông qua mô hình hỗn hợp Gaussian.

Điều này giúp GMM mô hình hóa linh hoạt hơn các phân phối dữ liệu có hình dạng elip hoặc chồng lấn.

##### Ưu điểm

- Phân cụm mềm (Soft Clustering).
- Mô hình hóa được các cụm có hình dạng khác nhau.
- Linh hoạt hơn K-Means.
- Có thể biểu diễn mức độ chắc chắn của việc phân cụm.

##### Hạn chế

- Thời gian huấn luyện dài hơn K-Means.
- Cần xác định trước số cụm.
- Có thể hội tụ vào nghiệm cục bộ.
- Nhạy cảm với khởi tạo ban đầu.

##### Trường hợp áp dụng phù hợp

GMM phù hợp khi dữ liệu có sự chồng lấn giữa các cụm hoặc không tuân theo dạng hình cầu.

---

#### 1.3.3. HDBSCAN

HDBSCAN là thuật toán phân cụm dựa trên mật độ. Khác với K-Means và GMM, HDBSCAN không yêu cầu xác định trước số lượng cụm mà tự động phát hiện các cụm dựa trên mật độ phân bố của dữ liệu.

Thuật toán cũng có khả năng nhận diện các điểm nhiễu (Noise) và xử lý tốt các cụm có hình dạng phức tạp.

##### Ưu điểm

- Không cần xác định trước số cụm.
- Tự động phát hiện điểm nhiễu.
- Xử lý tốt các cụm có mật độ khác nhau.
- Ít bị ảnh hưởng bởi Outlier.

##### Hạn chế

- Thời gian tính toán cao hơn.
- Có nhiều siêu tham số cần điều chỉnh.
- Khó diễn giải hơn K-Means.
- Kết quả phụ thuộc vào mật độ dữ liệu.

##### Trường hợp áp dụng phù hợp

HDBSCAN phù hợp khi dữ liệu có phân bố không đồng đều hoặc tồn tại nhiều điểm ngoại lệ.

---

## 2. Xây dựng quy trình huấn luyện và đánh giá mô hình

### 2.1. Mục tiêu

Mục tiêu của bước này là xây dựng một quy trình huấn luyện và đánh giá thống nhất cho tất cả các thuật toán phân cụm trong dự án. Toàn bộ mô hình sẽ được triển khai trên cùng một bộ dữ liệu đầu vào, áp dụng cùng quy trình tiền xử lý và được đánh giá bằng cùng hệ thống chỉ số nhằm đảm bảo kết quả có thể so sánh trực tiếp.

---

### 2.2 Quy trình tổng quát

Toàn bộ quá trình huấn luyện và đánh giá được thực hiện theo quy trình sau:

```text
RFM Scaled
      │
      ▼
Huấn luyện mô hình
      │
      ▼
Sinh nhãn Cluster
      │
      ▼
Đánh giá chất lượng phân cụm
      │
      ▼
So sánh giữa các thuật toán
      │
      ▼
Lựa chọn mô hình tối ưu
```

---

### 2.3. Mô tả từng giai đoạn

#### Giai đoạn 1. Chuẩn bị dữ liệu đầu vào

Tất cả các thuật toán đều sử dụng cùng một bộ dữ liệu đầu vào là `rfm_scaled.csv`, được tạo từ Epic 2 sau khi hoàn thành các bước tính toán RFM, biến đổi Logarithm và chuẩn hóa bằng StandardScaler.

Việc sử dụng chung một bộ dữ liệu giúp đảm bảo các thuật toán được đánh giá trên cùng điều kiện.

---

#### Giai đoạn 2. Huấn luyện mô hình

Mỗi thuật toán sẽ được huấn luyện độc lập với bộ siêu tham số đã được quy định trong tài liệu đặc tả.

Trong quá trình này, mô hình sẽ học cấu trúc dữ liệu và gán mỗi khách hàng vào một cụm tương ứng.

---

#### Giai đoạn 3. Sinh nhãn phân cụm

Sau khi huấn luyện, mô hình sẽ sinh ra nhãn (Cluster Label) cho từng khách hàng.

Kết quả đầu ra bao gồm: `CustomerID` va `Cluster Label`

Đây là cơ sở để phân tích đặc điểm từng nhóm khách hàng ở các bước tiếp theo.

---

#### Giai đoạn 4. Đánh giá chất lượng mô hình

Các mô hình sau khi huấn luyện sẽ được đánh giá bằng cùng một bộ chỉ số nội tại (Internal Validation Metrics).

Việc đánh giá tập trung vào:

- Mức độ tách biệt giữa các cụm.
- Mức độ đồng nhất trong từng cụm.
- Chất lượng tổng thể của kết quả phân cụm.

Tất cả các thuật toán đều sử dụng cùng hệ thống chỉ số để đảm bảo khả năng so sánh.

---

#### Giai đoạn 5. So sánh các mô hình

Kết quả đánh giá của từng thuật toán sẽ được tổng hợp vào cùng một bảng so sánh.

Các tiêu chí được sử dụng bao gồm:

- Chất lượng phân cụm.
- Độ ổn định của mô hình.
- Khả năng diễn giải kết quả.
- Ý nghĩa nghiệp vụ của các cụm khách hàng.

---

#### Giai đoạn 6. Lựa chọn mô hình tối ưu

Mô hình cuối cùng không được lựa chọn chỉ dựa trên một chỉ số duy nhất mà phải xem xét đồng thời nhiều tiêu chí đánh giá.

Mô hình được chọn cần đáp ứng các yêu cầu:

- Chất lượng phân cụm tốt.
- Kết quả ổn định.
- Dễ giải thích.
- Phù hợp với mục tiêu Customer Segmentation của dự án.

---

## 3. Xác định phạm vi tìm kiếm siêu tham số (Hyperparameter Search Space)

### 3.1. Mục tiêu

Mục tiêu của bước này là xây dựng phạm vi tìm kiếm siêu tham số (Hyperparameter Search Space) cho từng thuật toán phân cụm nhằm đảm bảo quá trình huấn luyện được thực hiện một cách khách quan, nhất quán và có thể tái lập.

Toàn bộ các mô hình trong dự án phải sử dụng đúng phạm vi tham số được quy định trong tài liệu này.

---

### 3.2. Nguyên tắc lựa chọn phạm vi tham số

Việc xây dựng không gian tìm kiếm tham số tuân theo các nguyên tắc sau:

- Phạm vi tham số phải đủ rộng để mô hình tìm được nghiệm tối ưu.
- Không sử dụng phạm vi quá lớn gây tăng thời gian huấn luyện không cần thiết.
- Các thuật toán phải được đánh giá trên cùng bộ dữ liệu đầu vào.
- Tất cả các lần huấn luyện phải sử dụng cùng `random_state` để đảm bảo khả năng tái lập kết quả.

---

### 3.3. Không gian tìm kiếm của K-Means

Các siêu tham số cần đánh giá gồm:

| Tham số | Giá trị đề xuất |
|----------|-----------------|
| n_clusters | 2 → 10 |
| init | k-means++ |
| n_init | auto |
| max_iter | 300 |
| random_state | 42 |

Trong đó, `n_clusters` là tham số quan trọng nhất và sẽ được thay đổi trong quá trình thực nghiệm nhằm tìm số lượng cụm phù hợp nhất.

---

### 3.4. Không gian tìm kiếm của Gaussian Mixture Model (GMM)

Các siêu tham số cần đánh giá gồm:

| Tham số | Giá trị đề xuất |
|----------|-----------------|
| n_components | 2 → 10 |
| covariance_type | full, tied, diag, spherical |
| max_iter | 300 |
| random_state | 42 |

Việc đánh giá nhiều dạng ma trận hiệp phương sai (Covariance Type) giúp GMM có thể mô hình hóa các cụm với hình dạng và mức độ phân tán khác nhau.

---

### 3.5. Không gian tìm kiếm của HDBSCAN

Các siêu tham số cần đánh giá gồm:

| Tham số | Giá trị đề xuất |
|----------|-----------------|
| min_cluster_size | 5, 10, 20, 30, 50 |
| min_samples | None, 5, 10 |
| cluster_selection_method | eom |
| metric | euclidean |

Do HDBSCAN không yêu cầu xác định trước số cụm, việc điều chỉnh `min_cluster_size` và `min_samples` sẽ ảnh hưởng trực tiếp đến số lượng cụm được phát hiện và khả năng nhận diện các điểm nhiễu.

---

### 3.6. Quy định khi thực nghiệm

Để đảm bảo tính công bằng giữa các mô hình, toàn bộ quá trình thực nghiệm cần tuân thủ các quy định sau:

- Mỗi thuật toán được huấn luyện trên cùng bộ dữ liệu `rfm_scaled.csv`.
- Chỉ thay đổi các siêu tham số đã được quy định.
- Không thay đổi dữ liệu đầu vào trong quá trình tìm kiếm tham số.
- Kết quả của từng lần chạy phải được lưu lại để phục vụ so sánh và đánh giá.

---

## 4. Xây dựng bộ chỉ số đánh giá mô hình phân cụm

### 4.1. Mục tiêu

Mục tiêu của bước này là xây dựng bộ chỉ số đánh giá thống nhất nhằm đo lường chất lượng của các mô hình phân cụm. Do bài toán Customer Segmentation không có nhãn (Ground Truth), việc đánh giá sẽ dựa trên các chỉ số đánh giá nội tại (Internal Validation Metrics), phản ánh mức độ tách biệt giữa các cụm và sự tương đồng của các điểm dữ liệu trong cùng một cụm

---

### 4.2. Nguyên tắc đánh giá

Việc đánh giá mô hình tuân theo các nguyên tắc sau:

- Tất cả các thuật toán sử dụng cùng bộ dữ liệu đầu vào.
- Áp dụng cùng hệ thống chỉ số đánh giá.
- Không ưu tiên bất kỳ thuật toán nào trước khi có kết quả thực nghiệm.
- Việc lựa chọn mô hình phải dựa trên nhiều chỉ số thay vì một chỉ số duy nhất.

---

### 4.3. Bộ chỉ số đánh giá

Dự án sử dụng ba chỉ số đánh giá nội tại phổ biến trong bài toán phân cụm.

| Chỉ số | Ý nghĩa | Giá trị mong muốn |
|---------|----------|------------------|
| Silhouette Score | Đánh giá mức độ tách biệt giữa các cụm | Càng lớn càng tốt |
| Davies–Bouldin Index (DBI) | Đánh giá mức độ chồng lấn giữa các cụm | Càng nhỏ càng tốt |
| Calinski–Harabasz Index (CHI) | Đánh giá độ phân tách và độ cô đặc của cụm | Càng lớn càng tốt |

Ba chỉ số này sẽ được tính cho tất cả các mô hình nhằm đảm bảo khả năng so sánh công bằng.

---

### 4.4 Ý nghĩa của từng chỉ số

#### 4.1.1. Silhouette Score

Silhouette Score đo lường mức độ tương đồng của một điểm dữ liệu với các điểm trong cùng cụm so với các cụm khác.

Giá trị của chỉ số nằm trong khoảng từ -1 đến 1.

- Giá trị gần 1 cho thấy các cụm được phân tách rõ ràng.
- Giá trị gần 0 cho thấy các cụm có sự chồng lấn.
- Giá trị âm cho thấy nhiều điểm dữ liệu có thể đã được gán sai cụm.

Trong dự án, mô hình có Silhouette Score cao hơn sẽ được ưu tiên.

---

#### 4.2.2. Davies–Bouldin Index (DBI)

Davies–Bouldin Index đánh giá mức độ tương đồng giữa các cụm dựa trên khoảng cách giữa tâm cụm và độ phân tán bên trong từng cụm.

Giá trị càng nhỏ cho thấy các cụm càng tách biệt và đồng nhất.

Mô hình có DBI thấp hơn được xem là có chất lượng phân cụm tốt hơn.

---

#### 4.3.3. Calinski–Harabasz Index (CHI)

Calinski–Harabasz Index đánh giá tỷ lệ giữa độ phân tán giữa các cụm và độ phân tán trong từng cụm.

Giá trị càng lớn chứng tỏ các cụm càng rõ ràng và dữ liệu trong cùng cụm càng đồng nhất.

Đây là chỉ số thường được sử dụng để đánh giá chất lượng tổng thể của mô hình phân cụm.

---

## 5. Thiết kế quy trình lựa chọn mô hình tối ưu

### 5.1. Mục tiêu

Mục tiêu của bước này là xây dựng quy trình lựa chọn mô hình phân cụm tối ưu sau khi hoàn thành quá trình huấn luyện và đánh giá. Thay vì lựa chọn mô hình dựa trên một chỉ số duy nhất, dự án áp dụng phương pháp đánh giá tổng hợp nhằm xem xét đồng thời chất lượng phân cụm, tính ổn định của mô hình và khả năng diễn giải kết quả.

Quy trình này giúp đảm bảo mô hình cuối cùng không chỉ đạt hiệu quả về mặt kỹ thuật mà còn tạo ra các cụm khách hàng có ý nghĩa đối với bài toán Customer Segmentation.

---

### 5.2. Nguyên tắc lựa chọn

Việc lựa chọn mô hình phải tuân thủ các nguyên tắc sau:

- Không lựa chọn mô hình dựa trên một chỉ số duy nhất.
- So sánh tất cả các mô hình trên cùng bộ dữ liệu đầu vào.
- Kết quả phải có khả năng tái lập.
- Các cụm tạo ra phải có ý nghĩa nghiệp vụ.
- Mô hình được chọn phải phù hợp với mục tiêu phân khúc khách hàng của dự án.

---

### 5.3. Tiêu chí đánh giá

Mỗi mô hình sẽ được đánh giá theo các nhóm tiêu chí sau.

| Nhóm tiêu chí | Nội dung đánh giá |
|---------------|-------------------|
| Chất lượng phân cụm | Silhouette Score, Davies–Bouldin Index, Calinski–Harabasz Index |
| Độ ổn định | Kết quả giữa nhiều lần chạy có nhất quán hay không |
| Khả năng diễn giải | Các cụm có dễ phân tích và mô tả đặc điểm hay không |
| Ý nghĩa nghiệp vụ | Các cụm có phản ánh đúng hành vi khách hàng hay không |

---

### 5.4. Quy trình lựa chọn

Việc lựa chọn mô hình được thực hiện theo trình tự sau:

- Tổng hợp toàn bộ kết quả đánh giá của các thuật toán vào cùng một bảng.
- So sánh các chỉ số đánh giá nội tại giữa các mô hình.
- Đánh giá độ ổn định của mô hình bằng cách chạy nhiều lần với cùng dữ liệu đầu vào.
- Phân tích đặc điểm của từng cụm khách hàng thông qua các đặc trưng RFM.
- Đánh giá ý nghĩa nghiệp vụ của từng cụm và khả năng hỗ trợ ra quyết định trong bài toán Customer Segmentation.
- Lựa chọn mô hình có chất lượng tổng thể tốt nhất để sử dụng trong các bước phân tích và trực quan hóa tiếp theo/

---

## 6. Định nghĩa sản phẩm đầu ra của mô hình phân cụm

### 6.1. Mục tiêu

Mục tiêu của bước này là thống nhất các sản phẩm đầu ra sau khi hoàn thành quá trình huấn luyện và lựa chọn mô hình phân cụm. Việc chuẩn hóa đầu ra giúp các thành viên trong nhóm sử dụng chung một định dạng dữ liệu, đồng thời tạo điều kiện thuận lợi cho các bước trực quan hóa, phân tích đặc điểm cụm và xây dựng ứng dụng.

---

### 6.2. Nguyên tắc xây dựng đầu ra

Sản phẩm đầu ra phải đáp ứng các yêu cầu sau:

- Có thể tái sử dụng trong các giai đoạn tiếp theo.
- Định dạng thống nhất giữa các thuật toán.
- Dễ kiểm tra và dễ trực quan hóa.
- Hỗ trợ đầy đủ cho việc phân tích cụm khách hàng.

---

### 6.3. Danh sách sản phẩm đầu ra

Sau khi hoàn thành quá trình phân cụm, hệ thống cần tạo các sản phẩm sau.

#### Bảng kết quả phân cụm

Lưu thông tin khách hàng cùng nhãn cụm.

Ví dụ:

| CustomerID | Cluster |
|------------|---------|
| 12346 | 0 |
| 12347 | 2 |
| 12348 | 1 |

Đường dẫn lưu: `data/processed/customer_clusters.csv`

---

#### Bảng đặc trưng RFM kèm nhãn cụm

Ghép bộ đặc trưng RFM với kết quả phân cụm để phục vụ phân tích.

Ví dụ:

| CustomerID | Recency | Frequency | Monetary | Cluster |
|------------|----------|-----------|-----------|---------|
| 12346 | ... | ... | ... | 0 |

Đường dẫn lưu : `data/processed/rfm_clustered.csv`


---

#### Báo cáo đánh giá mô hình

Tổng hợp kết quả đánh giá của các thuật toán.

Nội dung gồm:

- Thuật toán.
- Số cụm.
- Bộ tham số.
- Silhouette Score.
- Davies–Bouldin Index.
- Calinski–Harabasz Index.
- Nhận xét.

Đường dẫn lưu: `outputs/reports/clustering_evaluation.md`

---

#### Hình ảnh trực quan

Các biểu đồ phục vụ đánh giá mô hình và phân tích cụm.

Bao gồm:

- PCA Scatter Plot.
- Cluster Distribution.
- Elbow Curve (nếu có).
- Silhouette Plot (nếu có).

Đường dẫn lưu: `outputs/figures/`

---

#### Mô hình đã huấn luyện

Lưu mô hình để phục vụ triển khai và tái sử dụng.

Đường dẫn: `models/`

---

### 6.4. Cấu trúc thư mục đầu ra

```text
data/
└── processed/
    ├── customer_clusters.csv
    └── rfm_clustered.csv

outputs/
├── reports/
│   └── clustering_evaluation.md
└── figures/
    ├── cluster_distribution.png
    ├── pca_clusters.png
    ├── elbow_curve.png
    └── silhouette_plot.png

models/
└── best_model.pkl
```

---

## 7. Kết luận

Sau giai đoạn này, toàn bộ kết quả của quá trình phân cụm được chuẩn hóa thành các sản phẩm đầu ra thống nhất, bao gồm dữ liệu, báo cáo, biểu đồ và mô hình đã huấn luyện. Đây sẽ là đầu vào trực tiếp cho giai đoạn phân tích đặc điểm cụm khách hàng, trực quan hóa kết quả và xây dựng ứng dụng Streamlit của dự án.