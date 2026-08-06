# BÁO CÁO SO SÁNH CÁC MÔ HÌNH PHÂN CỤM


## 1. Tóm tắt kết quả

Bài toán Customer Segmentation của dự án không có nhãn tham chiếu, do đó việc lựa chọn thuật toán phân cụm phải dựa trên thực nghiệm thay vì dựa trên giả định. Báo cáo này trình bày kết quả huấn luyện ba thuật toán K-Means, Gaussian Mixture Model và HDBSCAN trên cùng bộ dữ liệu RFM đã chuẩn hóa, cùng một hệ chỉ số đánh giá nội tại và cùng `random_state = 42`.

Tổng cộng 60 cấu hình đã được huấn luyện và đánh giá: 9 cấu hình K-Means, 36 cấu hình GMM và 15 cấu hình HDBSCAN. Kết quả cho thấy K-Means với `n_clusters = 3` đạt Silhouette 0,4143, DBI 0,8293 và CHI 4.389,6. Cấu hình GMM tốt nhất (`n_components = 3`, `covariance_type = spherical`) đạt Silhouette 0,4144 và DBI 0,8167, tức là gần như trùng với K-Means, trong khi cấu hình HDBSCAN tốt nhất chỉ đạt Silhouette 0,2028 và phải loại 854 khách hàng (19,8%) ra khỏi phép đánh giá vì bị gán nhãn nhiễu.

Mô hình được chọn là **K-Means với 3 cụm**. Mục 6 trình bày căn cứ của lựa chọn này và đặc điểm nghiệp vụ của ba cụm thu được.

---

## 2. Thiết lập 

### 2.1. Dữ liệu đầu vào

Bộ dữ liệu `rfm_scaled.csv` được tạo từ Epic 2 sau các bước tính RFM, biến đổi logarithm và chuẩn hóa bằng StandardScaler. Kiểm tra đầu vào cho kết quả như sau.

| Hạng mục kiểm tra | Kết quả |
|---|---|
| Số lượng khách hàng | 4.324 |
| Số lượng đặc trưng dùng để phân cụm | 3 (`Recency`, `Frequency`, `Monetary`) |
| Giá trị thiếu | 0 trên cả ba đặc trưng |
| Kiểu dữ liệu | `float64` trên cả ba đặc trưng |
| Trung bình / độ lệch chuẩn | xấp xỉ 0 và 1 trên cả ba đặc trưng, đúng với kết quả của StandardScaler |

Cột `CustomerID` được giữ lại để gắn nhãn cụm ở bước đầu ra nhưng không tham gia vào quá trình huấn luyện.

### 2.2. Không gian tham số


| Thuật toán | Tham số | Giá trị thử nghiệm | Số cấu hình |
|---|---|---|---|
| K-Means | `n_clusters` | 2 đến 10 | 9 |
| K-Means | `init`, `n_init`, `max_iter`, `random_state` | `k-means++`, `auto`, 300, 42 | cố định |
| GMM | `n_components` | 2 đến 10 | 36 |
| GMM | `covariance_type` | `full`, `tied`, `diag`, `spherical` | |
| GMM | `max_iter`, `random_state` | 300, 42 | cố định |
| HDBSCAN | `min_cluster_size` | 5, 10, 20, 30, 50 | 15 |
| HDBSCAN | `min_samples` | `None`, 5, 10 | |
| HDBSCAN | `metric`, `cluster_selection_method` | `euclidean`, `eom` | cố định |

### 2.3. Chỉ số đánh giá

Cả ba thuật toán được đánh giá bằng cùng ba chỉ số: Silhouette Score (càng lớn càng tốt), Davies-Bouldin Index (càng nhỏ càng tốt) và Calinski-Harabasz Index (càng lớn càng tốt).

Riêng HDBSCAN, các điểm mang nhãn nhiễu (`label = -1`) được loại bỏ trước khi tính ba chỉ số. Lý do là nhãn nhiễu không phải một cụm, nếu giữ lại thì tập điểm rời rạc này bị tính như một cụm và làm sai lệch cả ba chỉ số. Cần lưu ý rằng cách xử lý này khiến chỉ số của HDBSCAN được tính trên một tập con dễ hơn, nên khi so sánh phải xem xét kèm tỷ lệ nhiễu.

### 2.4. Công cụ

Notebook sử dụng `scikit-learn` 1.6.1 để huấn luyện các mô hình.

---

## 3. Kết quả huấn luyện K-Means

Bảng dưới trình bày toàn bộ 9 cấu hình K-Means.

| n_clusters | Inertia | Silhouette | DBI | CHI | Thời gian (s) |
|---|---|---|---|---|---|
| 2 | 6839,6 | 0,4063 | 0,9144 | 3875,2 | 0,020 |
| **3** | **4278,8** | **0,4143** | **0,8293** | **4389,6** | **0,004** |
| 4 | 3212,4 | 0,3796 | 0,8579 | 4375,1 | 0,004 |
| 5 | 2735,2 | 0,3440 | 0,9383 | 4041,2 | 0,003 |
| 6 | 2365,5 | 0,3323 | 0,9721 | 3872,4 | 0,005 |
| 7 | 2141,9 | 0,3306 | 0,9317 | 3638,2 | 0,004 |
| 8 | 1930,6 | 0,3050 | 0,9899 | 3526,2 | 0,006 |
| 9 | 1826,8 | 0,2968 | 1,0625 | 3290,7 | 0,006 |
| 10 | 1701,6 | 0,2929 | 1,0583 | 3174,8 | 0,007 |

Ba chỉ số đánh giá cùng chỉ về một cấu hình. Với `n_clusters = 3`, K-Means đạt Silhouette cao nhất (0,4143), DBI thấp nhất (0,8293) và CHI cao nhất (4.389,6). Sự đồng thuận của ba chỉ số độc lập là căn cứ mạnh hơn nhiều so với việc chỉ dựa vào một chỉ số.

Inertia giảm đơn điệu khi số cụm tăng, đúng như bản chất của chỉ số này, nên không thể dùng inertia để chọn số cụm. Mức giảm mạnh nhất nằm ở đoạn từ k = 2 sang k = 3 (giảm 2.560,9) và từ k = 3 sang k = 4 (giảm 1.066,4), tức là điểm gãy của đường Elbow cũng nằm tại k = 3. Kết quả này thống nhất với ba chỉ số đánh giá.

Thời gian huấn luyện của toàn bộ 9 cấu hình đều dưới 0,02 giây.

---

## 4. Kết quả huấn luyện GMM

Bảng dưới trình bày toàn bộ 36 cấu hình GMM, nhóm theo `covariance_type`.

| n_components | covariance_type | Log-likelihood | Silhouette | DBI | CHI | Thời gian (s) |
|---|---|---|---|---|---|---|
| 2 | full | -13064,3 | 0,3031 | 1,2001 | 2165,3 | 0,011 |
| 3 | full | -12509,5 | 0,1894 | 1,5899 | 1892,4 | 0,014 |
| 4 | full | -4326,2 | 0,0831 | 2,0640 | 1441,3 | 0,028 |
| 5 | full | -129,2 | 0,0744 | 1,9830 | 1319,8 | 0,026 |
| 6 | full | 11,4 | 0,0356 | 2,2202 | 1198,8 | 0,025 |
| 7 | full | 419,1 | 0,1200 | 1,8925 | 1565,4 | 0,039 |
| 8 | full | 451,2 | 0,0609 | 2,0580 | 1292,0 | 0,054 |
| 9 | full | 532,7 | 0,0985 | 3,0482 | 1352,7 | 0,058 |
| 10 | full | 4491,0 | -0,0012 | 2,3369 | 866,0 | 0,053 |
| 2 | tied | -15131,6 | 0,3757 | 0,7972 | 2126,1 | 0,011 |
| 3 | tied | -13904,0 | 0,3779 | 0,8248 | 3487,5 | 0,012 |
| 4 | tied | -13719,7 | 0,3610 | 0,8441 | 3666,8 | 0,025 |
| 5 | tied | -13690,0 | 0,3288 | 0,9111 | 3661,2 | 0,015 |
| 6 | tied | -13233,8 | 0,3016 | 1,0318 | 3323,6 | 0,017 |
| 7 | tied | -12997,3 | 0,2602 | 1,2718 | 2602,0 | 0,035 |
| 8 | tied | -13079,5 | 0,2614 | 1,0706 | 2840,9 | 0,028 |
| 9 | tied | -12953,4 | 0,2508 | 1,1466 | 2394,1 | 0,050 |
| 10 | tied | -12850,0 | 0,1951 | 1,4612 | 2087,9 | 0,035 |
| 2 | diag | -14821,9 | 0,3926 | 0,9417 | 3693,0 | 0,005 |
| 3 | diag | -5739,1 | 0,2367 | 1,3404 | 2477,8 | 0,015 |
| 4 | diag | -13207,3 | 0,3233 | 0,9183 | 3641,7 | 0,010 |
| 5 | diag | -616,3 | 0,1695 | 1,7269 | 1721,2 | 0,018 |
| 6 | diag | -334,2 | 0,1321 | 1,5169 | 1534,5 | 0,016 |
| 7 | diag | 41,1 | 0,2319 | 1,3430 | 2254,7 | 0,018 |
| 8 | diag | -4047,2 | 0,2054 | 1,2278 | 2396,0 | 0,021 |
| 9 | diag | 297,4 | 0,1649 | 1,6623 | 1777,9 | 0,038 |
| 10 | diag | 4325,9 | 0,0358 | 1,9034 | 984,3 | 0,046 |
| 2 | spherical | -16742,5 | 0,4054 | 0,8823 | 3771,3 | 0,005 |
| **3** | **spherical** | **-15259,9** | **0,4144** | **0,8167** | **4364,7** | **0,006** |
| 4 | spherical | -14345,5 | 0,3809 | 0,8372 | 4291,7 | 0,007 |
| 5 | spherical | -13884,8 | 0,3341 | 0,8886 | 3788,9 | 0,010 |
| 6 | spherical | -13663,7 | 0,3151 | 1,0364 | 3407,1 | 0,015 |
| 7 | spherical | -13554,5 | 0,3263 | 0,9362 | 3504,8 | 0,011 |
| 8 | spherical | -13321,5 | 0,3006 | 0,9693 | 3354,3 | 0,011 |
| 9 | spherical | -13261,1 | 0,2971 | 1,0704 | 3130,3 | 0,015 |
| 10 | spherical | -13217,6 | 0,2942 | 1,0926 | 3027,4 | 0,015 |

Kết quả của GMM phụ thuộc mạnh vào `covariance_type`. Hai dạng `spherical` và `tied` cho chất lượng phân cụm tốt (Silhouette cao nhất lần lượt là 0,4144 và 0,3779), trong khi hai dạng `full` và `diag` cho kết quả kém hơn hẳn (Silhouette cao nhất chỉ 0,3031 và 0,3926, và giảm nhanh khi số thành phần tăng). Cấu hình `full` với 10 thành phần thậm chí cho Silhouette âm (-0,0012), nghĩa là nhiều điểm dữ liệu nằm gần cụm khác hơn cụm được gán.

Log-likelihood và chất lượng phân cụm đi ngược chiều nhau ở nhóm `full` và `diag`. Log-likelihood của nhóm `full` tăng từ -13.064,3 lên 4.491,0 khi số thành phần tăng từ 2 lên 10, trong khi Silhouette giảm từ 0,3031 xuống -0,0012. Nguyên nhân là ma trận hiệp phương sai đầy đủ cho phép một số thành phần co lại quanh một nhóm điểm rất nhỏ, làm mật độ tại đó tăng vọt và đẩy log-likelihood lên, nhưng các thành phần này không tương ứng với cụm khách hàng có ý nghĩa. Vì vậy log-likelihood không được dùng làm tiêu chí chọn mô hình trong báo cáo này, nó chỉ được ghi lại theo yêu cầu của quy trình thực nghiệm.

Cấu hình GMM tốt nhất là `n_components = 3` với `covariance_type = spherical`. Đây cũng là cấu hình mà giả định của GMM trở nên gần với giả định của K-Means, và kết quả phân cụm của hai mô hình trùng nhau ở mức Adjusted Rand Index 0,9306.

---

## 5. Kết quả huấn luyện HDBSCAN

Bảng dưới trình bày toàn bộ 15 cấu hình HDBSCAN. Ba chỉ số đánh giá được tính sau khi loại các điểm nhiễu.

| min_cluster_size | min_samples | Số cụm | Điểm nhiễu | Tỷ lệ nhiễu | Silhouette | DBI | CHI | Thời gian (s) |
|---|---|---|---|---|---|---|---|---|
| 5 | None | 32 | 522 | 12,1% | -0,0386 | 1,3866 | 174,0 | 0,052 |
| 5 | 5 | 32 | 522 | 12,1% | -0,0386 | 1,3866 | 174,0 | 0,042 |
| 5 | 10 | 9 | 694 | 16,0% | -0,0285 | 1,9946 | 640,2 | 0,041 |
| 10 | None | 9 | 694 | 16,0% | -0,0285 | 1,9946 | 640,2 | 0,042 |
| 10 | 5 | 15 | 518 | 12,0% | 0,0272 | 2,0997 | 362,4 | 0,039 |
| 10 | 10 | 9 | 694 | 16,0% | -0,0285 | 1,9946 | 640,2 | 0,041 |
| 20 | None | 6 | 893 | 20,7% | 0,0571 | 1,7528 | 970,2 | 0,043 |
| 20 | 5 | 10 | 484 | 11,2% | 0,0245 | 2,5140 | 577,6 | 0,044 |
| 20 | 10 | 8 | 651 | 15,1% | 0,0361 | 2,1509 | 718,3 | 0,042 |
| 30 | None | 5 | 1033 | 23,9% | 0,0874 | 1,5379 | 1239,1 | 0,046 |
| 30 | 5 | 10 | 484 | 11,2% | 0,0245 | 2,5140 | 577,6 | 0,039 |
| 30 | 10 | 8 | 651 | 15,1% | 0,0361 | 2,1509 | 718,3 | 0,040 |
| **50** | **None** | **3** | **854** | **19,8%** | **0,2028** | **1,1956** | **2404,6** | **0,052** |
| 50 | 5 | 9 | 432 | 10,0% | 0,0247 | 2,3789 | 711,5 | 0,039 |
| 50 | 10 | 8 | 651 | 15,1% | 0,0361 | 2,1509 | 718,3 | 0,049 |

Số cụm mà HDBSCAN phát hiện thay đổi rất mạnh theo tham số, từ 3 cụm đến 32 cụm. Xu hướng chung là `min_cluster_size` càng lớn thì số cụm càng giảm và chất lượng phân cụm càng tăng. Cấu hình tốt nhất là `min_cluster_size = 50` với `min_samples = None`, cho 3 cụm và Silhouette 0,2028.

Ngay cả cấu hình tốt nhất này vẫn kém hơn K-Means và GMM một khoảng lớn: Silhouette 0,2028 so với 0,4143, và CHI 2.404,6 so với 4.389,6. Khoảng cách còn lớn hơn thực tế nếu tính đến việc chỉ số của HDBSCAN được tính trên 3.470 khách hàng sau khi loại 854 khách hàng bị gán nhãn nhiễu, trong khi chỉ số của K-Means được tính trên toàn bộ 4.324 khách hàng.

Tỷ lệ nhiễu là hạn chế nghiêm trọng nhất của HDBSCAN đối với bài toán này. Với mọi cấu hình đã thử, thuật toán để lại từ 10,0% đến 23,9% khách hàng không thuộc cụm nào. Trong bài toán Customer Segmentation, mỗi khách hàng đều cần một phân khúc để bộ phận kinh doanh có thể áp dụng chính sách tương ứng, nên việc bỏ trống khoảng một phần năm tập khách hàng là chi phí khó chấp nhận.

Nguyên nhân nằm ở cấu trúc dữ liệu. Dữ liệu RFM sau khi biến đổi logarithm và chuẩn hóa tạo thành một khối liên tục, mật độ giảm dần đều từ tâm ra biên, không có các vùng mật độ cao tách biệt bởi các vùng mật độ thấp. Đây chính là dạng cấu trúc mà thuật toán phân cụm theo mật độ không phát huy được ưu thế.

---

## 6. So sánh tổng hợp và lựa chọn mô hình

### 6.1. Bảng so sánh

Bảng dưới tổng hợp cấu hình tốt nhất của mỗi thuật toán, chọn theo Silhouette Score.

| Model | Cấu hình tốt nhất | Cluster | Silhouette | DBI | CHI | Điểm nhiễu | Thời gian (s) |
|---|---|---|---|---|---|---|---|
| **K-Means** | `n_clusters = 3` | 3 | 0,4143 | 0,8293 | **4389,6** | 0 | 0,004 |
| GMM | `n_components = 3`, `spherical` | 3 | **0,4144** | **0,8167** | 4364,7 | 0 | 0,006 |
| HDBSCAN | `min_cluster_size = 50`, `min_samples = None` | 3 | 0,2028 | 1,1956 | 2404,6 | 854 | 0,052 |

Cả ba thuật toán đều hội tụ về 3 cụm dù xuất phát từ ba nguyên lý khác nhau. K-Means dựa trên khoảng cách tới tâm cụm, GMM dựa trên mô hình xác suất, HDBSCAN dựa trên mật độ. Việc ba phương pháp độc lập cùng cho 3 cụm là bằng chứng cho thấy cấu trúc 3 phân khúc là đặc điểm thực của dữ liệu chứ không phải sản phẩm của một thuật toán cụ thể.

### 6.2. Kiểm tra độ ổn định

Theo yêu cầu tại mục 5.3 của tài liệu đặc tả, độ ổn định được kiểm tra bằng cách huấn luyện lại mỗi mô hình với 5 giá trị `random_state` khác nhau (0, 1, 7, 2024, 12345) và đo Adjusted Rand Index giữa kết quả thu được với kết quả của `random_state = 42`.

| Mô hình | ARI thấp nhất | ARI cao nhất | Nhận xét |
|---|---|---|---|
| K-Means, k = 3 | 0,9894 | 0,9987 | Ổn định |
| GMM, 3 thành phần, `spherical` | 0,9955 | 0,9993 | Ổn định |
| GMM, 6 thành phần, `full` | 0,8153 | 0,9911 | Không ổn định |

Hai cấu hình tốt nhất đều ổn định. Kết quả này cũng cho thấy tính ổn định của GMM phụ thuộc vào cấu hình: dạng `full` với nhiều thành phần cho ARI thấp tới 0,8153, phù hợp với hiện tượng một số thành phần co lại quanh nhóm điểm nhỏ đã trình bày ở mục 4.

### 6.3. Ưu điểm và hạn chế quan sát được từ thực nghiệm

| Mô hình | Ưu điểm quan sát được | Hạn chế quan sát được |
|---|---|---|
| K-Means | CHI cao nhất trong ba mô hình (4.389,6); ba chỉ số cùng chỉ về k = 3; ARI giữa các lần chạy từ 0,9894 trở lên; thời gian huấn luyện 0,004 giây; mỗi khách hàng đều có nhãn cụm | Phải chỉ định trước số cụm; giả định cụm dạng hình cầu, phù hợp với dữ liệu này nhưng không phải giả định luôn đúng; gán cứng nên không biểu diễn được mức độ chắc chắn |
| GMM | Silhouette và DBI tốt nhất trong ba mô hình, dù chênh lệch so với K-Means rất nhỏ; cho xác suất thuộc cụm, hữu ích khi cần đánh giá mức độ chắc chắn của phân khúc | Kết quả nhạy với `covariance_type`, chênh lệch Silhouette giữa cấu hình tốt nhất và kém nhất lên tới 0,4156; log-likelihood tăng trong khi chất lượng cụm giảm nên không dùng được làm tiêu chí chọn mô hình; cấu hình `full` không ổn định giữa các lần chạy |
| HDBSCAN | Không cần chỉ định trước số cụm; tự phát hiện các điểm ngoại lệ, có thể dùng để rà soát khách hàng có hành vi bất thường | Cả ba chỉ số đều kém hơn rõ rệt; để lại 10,0% đến 23,9% khách hàng không thuộc cụm nào; số cụm dao động từ 3 đến 32 tùy tham số nên khó kiểm soát; thời gian huấn luyện cao gấp hơn 10 lần K-Means |

### 6.4. Mô hình được chọn

Mô hình được chọn là **K-Means với `n_clusters = 3`**.

Xét riêng chỉ số, K-Means và GMM `spherical` là ngang nhau. GMM nhỉnh hơn ở Silhouette (0,4144 so với 0,4143, chênh 0,0001) và ở DBI (0,8167 so với 0,8293), K-Means nhỉnh hơn ở CHI (4.389,6 so với 4.364,7). Hai mô hình cho kết quả phân cụm trùng nhau ở mức ARI 0,9306, nghĩa là chúng chia tập khách hàng gần như giống hệt nhau. Chênh lệch 0,0001 Silhouette không đủ để coi một mô hình là tốt hơn mô hình còn lại.

Vì chất lượng phân cụm ngang nhau, ba tiêu chí còn lại trong mục 5.3 của tài liệu đặc tả trở thành căn cứ quyết định.

- **Độ ổn định**: cả hai đều ổn định, K-Means không có lợi thế riêng ở tiêu chí này.
- **Khả năng diễn giải**: K-Means mô tả mỗi cụm bằng một tâm cụm trong không gian RFM, bộ phận kinh doanh đọc trực tiếp được ba con số Recency, Frequency, Monetary của tâm cụm. GMM mô tả mỗi cụm bằng một phân phối Gaussian với vector trung bình và ma trận hiệp phương sai, khó truyền đạt hơn.
- **Ý nghĩa nghiệp vụ**: cả hai cho ba phân khúc tương đương, nhưng K-Means gán cứng nên mỗi khách hàng thuộc đúng một phân khúc, phù hợp với cách bộ phận kinh doanh áp dụng chính sách.

HDBSCAN không được chọn vì hai lý do đã nêu ở mục 5: chất lượng phân cụm kém hơn trên cả ba chỉ số, và để lại 854 khách hàng không có phân khúc.

### 6.5. Đặc điểm ba cụm của mô hình được chọn

Bảng dưới trình bày đặc điểm ba cụm theo giá trị RFM gốc (chưa chuẩn hóa), lấy từ `data/processed/rfm_table.csv`.

| Cluster | Số khách hàng | Tỷ lệ | Recency TB (ngày) | Frequency TB | Monetary TB | Monetary trung vị | Diễn giải |
|---|---|---|---|---|---|---|---|
| 0 | 990 | 22,9% | 254,3 | 1,4 | 400,7 | 282,4 | Khách hàng đã rời bỏ. Mua rất ít lần và lần mua gần nhất cách hơn 8 tháng |
| 1 | 2024 | 46,8% | 54,0 | 2,0 | 601,3 | 501,4 | Khách hàng phổ thông. Còn hoạt động nhưng tần suất và giá trị mua đều thấp |
| 2 | 1310 | 30,3% | 29,1 | 9,8 | 5114,4 | 2498,0 | Khách hàng giá trị cao. Mua gần đây, thường xuyên và giá trị lớn |

Ba cụm tách biệt rõ trên cả ba chiều RFM và mỗi cụm ứng với một nhóm hành vi mà bộ phận kinh doanh có thể xử lý bằng chính sách riêng. Cụm 2 chiếm 30,3% số khách hàng nhưng có giá trị mua trung bình cao gấp 8,5 lần cụm 1, đây là nhóm cần được ưu tiên giữ chân. Cụm 0 là nhóm cần chiến dịch kích hoạt lại hoặc chấp nhận loại khỏi danh sách tiếp thị.

Giá trị trung vị của Monetary thấp hơn giá trị trung bình ở cả ba cụm, rõ nhất ở cụm 2 (2.498,0 so với 5.114,4). Điều này cho thấy phân phối chi tiêu trong từng cụm vẫn lệch phải, tức là bên trong cụm giá trị cao vẫn tồn tại một nhóm nhỏ khách hàng chi tiêu vượt trội.

---

## 7. Sản phẩm đầu ra

| Sản phẩm | Đường dẫn | Nội dung |
|---|---|---|
| Bảng kết quả phân cụm | `data/processed/customer_clusters.csv` | 4.324 dòng, hai cột `CustomerID` và `Cluster` từ mô hình được chọn |
| Bảng so sánh | `outputs/reports/clustering_comparison.md` | Tài liệu này |
| Kết quả từng lần chạy | `outputs/results/clustering_experiments.csv` | 60 dòng, toàn bộ cấu hình kèm chỉ số đánh giá và thời gian huấn luyện |
| Notebook | `notebooks/clustering_models.ipynb` | Quá trình thực nghiệm theo từng bước |
| Module | `src/models/clustering.py` | `train_kmeans`, `train_gmm`, `train_hdbscan`, `evaluate_model`, `compare_models`, `save_cluster_result` |

Toàn bộ kết quả trong báo cáo được tái lập bằng một lệnh:

```bash
python3 src/models/clustering.py
```

---

## 8. Hạn chế của thực nghiệm

Ba hạn chế sau cần được ghi nhận khi sử dụng kết quả này.

Thứ nhất, việc lựa chọn mô hình chỉ dựa trên chỉ số nội tại. Bài toán không có nhãn tham chiếu nên không thể đo độ chính xác thực sự của phân khúc. Ba chỉ số đã dùng đều thiên vị các cụm dạng hình cầu, đây là lợi thế mang tính hệ thống cho K-Means và GMM `spherical` so với HDBSCAN. Nhận định ở mục 5 rằng dữ liệu RFM tạo thành khối liên tục làm giảm bớt lo ngại này, nhưng không loại bỏ hoàn toàn.

Thứ hai, kết quả gắn liền với cách chuẩn hóa dữ liệu ở Epic 2. Nếu thay biến đổi logarithm hoặc thay StandardScaler bằng phương pháp khác, cấu trúc mật độ của dữ liệu sẽ thay đổi và kết luận về HDBSCAN có thể khác đi.

Thứ ba, độ ổn định mới chỉ được kiểm tra qua `random_state`. Thực nghiệm chưa kiểm tra độ ổn định khi thay đổi tập dữ liệu, chẳng hạn bằng cách lấy mẫu bootstrap hoặc chia dữ liệu theo thời gian.
