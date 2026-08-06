# BÁO CÁO ĐÁNH GIÁ ĐỘ ỔN ĐỊNH CỦA CÁC MÔ HÌNH PHÂN CỤM


## 1. Tóm tắt kết quả

Báo cáo `clustering_comparison.md` của Task 12 đã chọn được cấu hình tốt nhất của ba thuật toán dựa trên chất lượng phân cụm đo trên một lần chạy duy nhất. Mục 8 của báo cáo đó ghi nhận một hạn chế còn để ngỏ: độ ổn định mới chỉ được kiểm tra qua `random_state`, chưa kiểm tra khi tập dữ liệu thay đổi. Báo cáo này giải quyết đúng hạn chế đó.

Phương pháp là lấy mẫu ngẫu nhiên 80% số khách hàng, lặp lại 50 lần, huấn luyện lại cả ba mô hình trên từng tập mẫu, rồi đo Adjusted Rand Index giữa mọi cặp trong 50 lần lặp, tức 1.225 cặp cho mỗi thuật toán.

Kết quả: K-Means đạt Mean ARI 0,9751 với Std ARI 0,0136, GMM `spherical` đạt 0,9747 với Std 0,0143, HDBSCAN đạt 0,9543 với Std 0,0506. Hai mô hình đầu ngang nhau và đều rất ổn định. HDBSCAN có Mean ARI thấp hơn và biến động cao gấp gần bốn lần, nhưng nguyên nhân không nằm ở lõi cụm: sau khi loại các điểm nhiễu, Mean ARI của HDBSCAN đạt 0,9953. Toàn bộ phần biến động lớn của HDBSCAN đến từ một lần lặp duy nhất trong 50 lần, ở đó thuật toán tách ra 4 cụm thay vì 3 và đẩy tỷ lệ nhiễu lên 32,3%.

Kết luận thực tiễn: quyết định chọn K-Means với 3 cụm ở Task 12 vẫn giữ nguyên, và nay có thêm căn cứ về độ ổn định trước biến động dữ liệu chứ không chỉ trước `random_state`.

---

## 2. Thiết lập thực nghiệm

### 2.1. Dữ liệu đầu vào

Thực nghiệm dùng lại đúng bộ dữ liệu của Task 12: `data/processed/rfm_scaled.csv`, gồm 4.324 khách hàng và ba đặc trưng `Recency`, `Frequency`, `Monetary` đã qua biến đổi logarithm và StandardScaler. Không có giá trị thiếu, cả ba đặc trưng đều `float64`. Cột `CustomerID` không tham gia huấn luyện.

### 2.2. Cấu hình tối ưu lấy từ Task 12

Cấu hình không được nhập tay mà đọc trực tiếp từ `outputs/results/clustering_experiments.csv`, lấy dòng có Silhouette cao nhất của mỗi thuật toán. 

| Thuật toán | Cấu hình sử dụng | Silhouette tại Task 12 |
|---|---|---|
| K-Means | `n_clusters = 3` | 0,4143 |
| GMM | `n_components = 3`, `covariance_type = spherical` | 0,4144 |
| HDBSCAN | `min_cluster_size = 50`, `min_samples = None` | 0,2028 |

### 2.3. Quy trình lấy mẫu lại

| Tham số | Giá trị |
|---|---|
| Số lần lặp (`n_iterations`) | 50 |
| Tỷ lệ dữ liệu mỗi lần (`sample_size`) | 80% |
| Kích thước mỗi tập mẫu | 3.459 / 4.324 khách hàng |
| Cách lấy mẫu | Ngẫu nhiên không hoàn lại |
| Tỷ lệ trùng nhau trung bình giữa hai tập mẫu bất kỳ | 80,0% |
| `random_state` sinh mẫu | 42 |

Ba thuật toán dùng chung đúng 50 tập mẫu đó. Nếu mỗi thuật toán được cấp một bộ mẫu riêng thì chênh lệch ARI giữa các thuật toán sẽ lẫn cả phần biến động do tập mẫu khác nhau, làm phép so sánh mất ý nghĩa.

Một điểm cần nói rõ: `random_state` của cả ba mô hình được giữ nguyên bằng 42 trong suốt 50 lần lặp. Vì vậy nguồn biến động duy nhất trong thực nghiệm này là dữ liệu, không phải khởi tạo mô hình. Đây là điều kiện cần để trả lời câu hỏi "thuật toán nào nhạy cảm với sự thay đổi của dữ liệu". 

### 2.4. Cách tính Adjusted Rand Index

ARI đòi hỏi hai kết quả phân cụm được đo trên cùng một tập điểm, trong khi hai tập mẫu 80% chỉ trùng nhau khoảng 80%. Vì vậy với mỗi cặp lần lặp, ARI chỉ được tính trên phần khách hàng xuất hiện ở cả hai tập mẫu, trung bình khoảng 2.767 khách hàng cho mỗi cặp. Với 50 lần lặp, mỗi thuật toán có 1.225 giá trị ARI, từ đó tính Mean ARI và Std ARI.

Riêng HDBSCAN, nhãn nhiễu `-1` được giữ nguyên khi tính ARI ở bảng chính. Cách này coi tập điểm nhiễu như một nhóm riêng, nên nếu HDBSCAN gán nhiễu cho những khách hàng khác nhau giữa các lần chạy thì ARI sẽ giảm — đúng với điều cần đo, vì trong bài toán phân khúc thì việc một khách hàng lúc thì thuộc cụm, lúc thì bị loại ra ngoài cũng là một dạng bất ổn định. Mục 4.3 tính thêm ARI sau khi loại các điểm nhiễu để tách riêng hai nguồn biến động.

Ngoài ARI theo cặp, báo cáo còn ghi lại ARI đối chiếu: so sánh kết quả của từng lần lặp với kết quả huấn luyện trên toàn bộ 4.324 khách hàng, đo trên phần dữ liệu được lấy mẫu của lần lặp đó. Chỉ số này cho biết mô hình huấn luyện trên 80% dữ liệu có tái tạo lại được phân cụm gốc hay không.

### 2.5. Công cụ

`scikit-learn` 1.6.1 cho ba mô hình và `adjusted_rand_score`, `numpy` cho việc sinh mẫu. Toàn bộ thực nghiệm chạy dưới 10 giây.

---

## 3. Kết quả huấn luyện lại từng thuật toán

### 3.1. K-Means

| Hạng mục | Trung bình | Std | Nhỏ nhất | Lớn nhất |
|---|---|---|---|---|
| Số cụm tạo thành | 3,00 | 0,00 | 3 | 3 |
| Inertia | 3.420,6 | 46,5 | 3.336,5 | 3.520,1 |
| Thời gian huấn luyện (s) | 0,0029 | 0,0007 | 0,0013 | 0,0042 |

Cả 50 lần lặp đều cho đúng 3 cụm. Inertia dao động trong biên độ hẹp, khoảng 1,4% quanh giá trị trung bình, và mức dao động này chủ yếu phản ánh việc mỗi tập mẫu có 3.459 điểm khác nhau chứ không phải cấu trúc cụm thay đổi.

### 3.2. GMM

| Hạng mục | Trung bình | Std | Nhỏ nhất | Lớn nhất |
|---|---|---|---|---|
| Số cụm tạo thành | 3,00 | 0,00 | 3 | 3 |
| Log-likelihood | -12.203,1 | 60,7 | -12.343,4 | -12.105,8 |
| Xác suất trung bình của cụm được gán | 0,9280 | 0,0014 | 0,9250 | 0,9316 |
| Tỷ lệ khách hàng có xác suất cao nhất < 0,8 | 14,3% | 0,4% | 13,3% | 14,9% |

Cả 50 lần lặp đều cho 3 cụm. Xác suất thuộc cụm là thông tin mà K-Means không có, và ở đây nó cho thấy GMM gán cụm với độ chắc chắn cao: trung bình 0,9280, tức phần lớn khách hàng thuộc hẳn về một cụm. Khoảng 14,3% khách hàng có xác suất cao nhất dưới 0,8, đây là nhóm nằm ở vùng giao giữa hai cụm. Tỷ lệ này gần như không đổi qua 50 lần lặp (Std 0,4%), nghĩa là vùng giao giữa các cụm là đặc điểm ổn định của dữ liệu chứ không phải hiện tượng ngẫu nhiên của một lần chạy.

### 3.3. HDBSCAN

| Hạng mục | Trung bình | Std | Nhỏ nhất | Lớn nhất |
|---|---|---|---|---|
| Số cụm phát hiện được | 3,02 | 0,14 | 3 | 4 |
| Số điểm nhiễu | 839,7 | 43,7 | 797 | 1.117 |
| Tỷ lệ nhiễu | 24,3% | 1,3% | 23,0% | 32,3% |

Số cụm phát hiện được là 3 ở 49 lần lặp và 4 ở 1 lần lặp (lần lặp số 12). Đây là khác biệt quan trọng nhất so với hai thuật toán còn lại: K-Means và GMM được ấn định trước số cụm nên không bao giờ đổi, còn HDBSCAN tự suy ra số cụm từ dữ liệu nên số cụm là một đại lượng có thể thay đổi.

Tỷ lệ nhiễu tăng từ 19,8% khi huấn luyện trên toàn bộ 4.324 khách hàng lên trung bình 24,3% khi chỉ dùng 80% dữ liệu. Mức tăng gần 4,5 điểm phần trăm này là hệ quả trực tiếp của cách HDBSCAN hoạt động: thuật toán đánh giá mật độ cục bộ, mà bỏ đi 20% số điểm thì mật độ tại mọi vùng đều giảm, nên nhiều điểm ở vùng biên rơi xuống dưới ngưỡng và bị xếp vào nhiễu. Điều này cho thấy kết quả của HDBSCAN không chỉ nhạy với việc dữ liệu thay đổi mà còn nhạy với lượng dữ liệu có sẵn.

Lần lặp số 12 là trường hợp cực đoan của cùng hiện tượng đó: tỷ lệ nhiễu lên 32,3% và một cụm bị tách đôi thành 4 cụm.

---

## 4. Kết quả đánh giá bằng Adjusted Rand Index

### 4.1. Bảng so sánh chính

| Model | Mean ARI | Std ARI | Stability |
|---|---|---|---|
| **K-Means** | **0,9751** | **0,0136** | **Rất ổn định** |
| GMM | 0,9747 | 0,0143 | Rất ổn định |
| HDBSCAN | 0,9543 | 0,0506 | Ổn định |

Mức độ ổn định được xếp theo cả hai chỉ số: mức `Rất ổn định` yêu cầu Mean ARI từ 0,90 trở lên **và** Std ARI không quá 0,03; mức `Ổn định` yêu cầu Mean ARI từ 0,75 và Std ARI không quá 0,10. Std ARI được đưa vào ngưỡng vì một mô hình có Mean ARI cao nhưng biến động lớn giữa các lần chạy không đáng tin bằng mô hình biến động thấp — nếu chỉ xét Mean ARI thì cả ba thuật toán đều rơi vào cùng một mức và bảng mất khả năng phân biệt.

### 4.2. Phân phối chi tiết của ARI

| Model | Số cặp | Mean | Std | Nhỏ nhất | Phân vị 25% | Trung vị | Phân vị 75% | Lớn nhất |
|---|---|---|---|---|---|---|---|---|
| K-Means | 1.225 | 0,9751 | 0,0136 | 0,9293 | 0,9660 | 0,9773 | 0,9856 | 0,9989 |
| GMM | 1.225 | 0,9747 | 0,0143 | 0,9206 | 0,9656 | 0,9771 | 0,9858 | 1,0000 |
| HDBSCAN | 1.225 | 0,9543 | 0,0506 | 0,6894 | 0,9602 | 0,9649 | 0,9688 | 0,9811 |

Phân phối của HDBSCAN có hình dạng khác hẳn hai thuật toán còn lại. Khoảng tứ phân vị của nó rất hẹp (0,9602 đến 0,9688), hẹp hơn cả K-Means và GMM, nhưng giá trị nhỏ nhất lại tụt xuống 0,6894. Nguyên nhân là 49 cặp có ARI dưới 0,80, và cả 49 cặp này đều là các cặp liên quan đến lần lặp số 12, tức đúng lần lặp cho 4 cụm ở mục 3.3. Nếu loại lần lặp đó ra, HDBSCAN đạt Mean ARI 0,9646 với Std chỉ 0,0063, thấp nhất trong ba thuật toán.

Cách đọc đúng của con số này không phải "HDBSCAN thực ra ổn định nhất", mà là: HDBSCAN dao động rất ít trong điều kiện bình thường nhưng có rủi ro đuôi, tức thỉnh thoảng cho ra một kết quả khác hẳn. Với tần suất quan sát được là 1 trên 50 lần, rủi ro này không thể bỏ qua khi mô hình được dùng để chia phân khúc khách hàng định kỳ. K-Means và GMM không có cặp nào dưới 0,90.

### 4.3. ARI của HDBSCAN sau khi loại điểm nhiễu

| Cách tính | Mean ARI | Std ARI |
|---|---|---|
| Giữ nhãn nhiễu (bảng chính) | 0,9543 | 0,0506 |
| Loại các điểm nhiễu | 0,9953 | 0,0231 |

Chênh lệch 0,0410 giữa hai cách tính chỉ ra chính xác nguồn gốc bất ổn định của HDBSCAN. Với những khách hàng được gán vào cụm ở cả hai lần chạy, kết quả gần như trùng khớp hoàn toàn (0,9953). Toàn bộ phần ARI bị mất nằm ở ranh giới giữa cụm và nhiễu, tức ở việc khách hàng nào bị loại ra ngoài. Nói cách khác, lõi ba cụm mà HDBSCAN tìm được là cấu trúc thật và ổn định, còn tập khoảng 24% khách hàng bị gán nhãn nhiễu thì thay đổi đáng kể giữa các lần chạy.

### 4.4. ARI đối chiếu với kết quả trên toàn bộ dữ liệu

| Model | Mean ARI đối chiếu | Std | Nhỏ nhất |
|---|---|---|---|
| GMM | 0,9814 | 0,0096 | 0,9581 |
| K-Means | 0,9811 | 0,0094 | 0,9599 |
| HDBSCAN | 0,8918 | 0,0365 | 0,6424 |

Chỉ số này xác nhận lại kết luận của bảng chính từ một góc khác. K-Means và GMM huấn luyện trên 80% dữ liệu vẫn tái tạo lại phân cụm gốc ở mức 0,98, còn HDBSCAN chỉ đạt 0,8918. Khoảng cách của HDBSCAN ở đây (0,8918 so với 0,9543 khi so từng cặp với nhau) là hệ quả của việc tỷ lệ nhiễu tăng từ 19,8% lên 24,3% đã nêu ở mục 3.3: các lần lặp giống nhau nhiều hơn là giống với mô hình gốc, vì chúng cùng chịu chung tác động của việc mất 20% dữ liệu.

---

## 5. Phân tích kết quả

### 5.1. Thuật toán nào tạo ra các nhóm khách hàng nhất quán khi dữ liệu thay đổi nhỏ?

K-Means và GMM `spherical`, ngang nhau. Chênh lệch Mean ARI giữa hai mô hình là 0,0004, trong khi Std ARI của mỗi mô hình khoảng 0,014, tức chênh lệch nhỏ hơn 3% độ lệch chuẩn. So sánh theo từng cặp lần lặp cho cùng kết luận: K-Means cho ARI cao hơn GMM ở 610 trên 1.225 cặp, tức 49,8%, gần đúng bằng tỷ lệ của một phép chọn ngẫu nhiên. Không có cơ sở để nói mô hình nào ổn định hơn mô hình nào.

Kết quả này chothấy: hai mô hình có ARI 0,9306 với nhau trên toàn bộ dữ liệu, tức chúng chia tập khách hàng theo cách gần như giống hệt nhau, nên rất khó có chuyện chúng phản ứng khác nhau trước cùng một biến động dữ liệu.

Về mặt nghiệp vụ, Mean ARI 0,975 nghĩa là khi thay đổi 20% danh sách khách hàng đầu vào, ba phân khúc thu được vẫn gần như y nguyên. Phân khúc được tạo ra là đặc điểm của dữ liệu chứ không phải sản phẩm của một lần chạy may mắn, nên các chính sách kinh doanh xây trên ba phân khúc này không phải điều chỉnh lại mỗi khi dữ liệu được cập nhật.

### 5.2. Thuật toán nào nhạy cảm với sự thay đổi của dữ liệu?

HDBSCAN, và biểu hiện của độ nhạy này gồm ba mặt.

Thứ nhất, số cụm không cố định. Một trong 50 lần lặp cho 4 cụm thay vì 3. Với K-Means và GMM, số cụm là tham số đầu vào nên không thể thay đổi; với HDBSCAN, số cụm là kết quả đầu ra nên nó thừa hưởng toàn bộ độ biến động của dữ liệu. Trong vận hành, điều này có nghĩa là số phân khúc có thể tự đổi giữa hai kỳ chạy mà không ai chủ động yêu cầu.

Thứ hai, tỷ lệ nhiễu tăng theo lượng dữ liệu bị bớt đi, từ 19,8% trên toàn bộ dữ liệu lên trung bình 24,3% trên các tập mẫu 80%. Đây là dạng nhạy cảm đáng lo hơn cả vì nó có hướng rõ ràng chứ không phải dao động ngẫu nhiên: dữ liệu càng ít thì càng nhiều khách hàng không được phân khúc.

Thứ ba, biến động tập trung ở đuôi phân phối. HDBSCAN cho kết quả rất ổn định trong 49 trên 50 lần lặp nhưng hỏng hẳn ở 1 lần. Dạng bất ổn định này khó phát hiện hơn dạng dao động đều, vì một lần kiểm tra thông thường có xác suất cao rơi vào các lần chạy bình thường và cho cảm giác mô hình đáng tin.

Cần ghi nhận mặt ngược lại để đánh giá công bằng: kết quả ở mục 4.3 cho thấy lõi ba cụm của HDBSCAN là cấu trúc thật và rất ổn định (Mean ARI 0,9953). Vấn đề của HDBSCAN trong bài toán này không phải là nó tìm sai cụm, mà là nó phải quyết định ai bị loại ra ngoài, và quyết định đó không ổn định.

### 5.3. Mô hình có chất lượng phân cụm cao có đồng thời ổn định hay không?

Trong thực nghiệm này thì có, hai tiêu chí đồng thuận với nhau.

| Model | Silhouette | Mean ARI | Std ARI | Stability |
|---|---|---|---|---|
| K-Means | 0,4143 | 0,9751 | 0,0136 | Rất ổn định |
| GMM | 0,4144 | 0,9747 | 0,0143 | Rất ổn định |
| HDBSCAN | 0,2028 | 0,9543 | 0,0506 | Ổn định |

Thứ tự xếp hạng theo Silhouette trùng với thứ tự theo Mean ARI. Không xuất hiện trường hợp mà tài liệu đặc tả đã cảnh báo, tức Silhouette cao đi kèm ARI thấp.

Tuy vậy, không nên rút ra kết luận tổng quát rằng chất lượng cao luôn kéo theo ổn định. Ngay trong dự án này đã có phản ví dụ: mục 6.2 của báo cáo Task 12 ghi nhận cấu hình GMM `full` với 6 thành phần cho ARI thấp tới 0,8153 khi chỉ đổi `random_state`, trong khi cấu hình GMM `spherical` với 3 thành phần cho 0,9955. Hai cấu hình cùng một thuật toán, chênh lệch độ ổn định rất lớn. Điều làm cho hai tiêu chí đồng thuận ở đây là cả ba thuật toán đều hội tụ về cùng một cấu trúc 3 cụm — cấu trúc đó vừa tách bạch rõ (Silhouette cao) vừa bền trước biến động dữ liệu (ARI cao). Nói cách khác, sự đồng thuận này là đặc điểm của bộ dữ liệu RFM cụ thể này, không phải một quy luật chung.

Đó cũng là lý do độ ổn định cần được đo riêng chứ không suy ra từ chỉ số chất lượng.

---

## 6. Kết luận

 **K-Means với `n_clusters = 3`** giữ nguyên cấu trúc ba phân khúc khi 20% dữ liệu đầu vào thay đổi, với Mean ARI 0,9751 và không có lần chạy nào tụt xuống dưới 0,9293.

GMM `spherical` với 3 thành phần ngang bằng K-Means về độ ổn định, đúng như đã ngang bằng về chất lượng phân cụm. Lựa chọn giữa hai mô hình này vẫn dựa trên khả năng diễn giải như đã trình bày ở mục 6.4 của báo cáo Task 12. Nếu về sau dự án cần biết mức độ chắc chắn của từng khách hàng trong phân khúc, GMM là phương án thay thế đã được kiểm chứng cả về chất lượng lẫn độ ổn định, không cần đánh giá lại.

HDBSCAN không được chọn, nhưng thực nghiệm này bổ sung một cách dùng khác cho nó. Vì lõi ba cụm của HDBSCAN ổn định ở mức 0,9953 còn tập điểm nhiễu thì biến động mạnh, HDBSCAN không phù hợp để phân khúc toàn bộ khách hàng nhưng phù hợp để rà soát khách hàng có hành vi bất thường. Ngay cả với mục đích đó cũng cần lưu ý rằng danh sách khách hàng bị gán nhãn nhiễu thay đổi đáng kể giữa các lần chạy, nên không nên dùng danh sách của một lần chạy duy nhất làm căn cứ.

---

## 7. Hạn chế của thực nghiệm

Thứ nhất, thực nghiệm chỉ dùng một tỷ lệ lấy mẫu duy nhất là 80%. Mục 3.3 đã cho thấy tỷ lệ nhiễu của HDBSCAN tăng theo lượng dữ liệu bị bớt đi, nên Mean ARI của HDBSCAN nhiều khả năng phụ thuộc vào tỷ lệ lấy mẫu. Chạy thêm ở các mức 50%, 70% và 90% sẽ cho biết quan hệ này mạnh đến đâu, và cũng sẽ kiểm tra được liệu K-Means và GMM có giữ được mức 0,975 khi dữ liệu bị bớt nhiều hơn hay không.

Thứ hai, ARI chỉ đo mức độ trùng khớp của cách chia nhóm, không đo vị trí của các cụm. Hai lần chạy có thể cho ARI bằng 1 trong khi tâm cụm dịch chuyển, vì ARI chỉ quan tâm hai khách hàng có cùng cụm hay không. Với bài toán phân khúc, độ ổn định của tâm cụm cũng là thông tin cần thiết vì tâm cụm chính là cái mà bộ phận kinh doanh dùng để mô tả từng phân khúc. Thực nghiệm này chưa đo đại lượng đó.

Thứ ba, lấy mẫu ngẫu nhiên giả định các khách hàng có thể hoán đổi cho nhau, trong khi dữ liệu thực tế thay đổi theo thời gian: khách hàng mới xuất hiện, khách hàng cũ ngừng mua, và giá trị RFM của mọi khách hàng đều dịch chuyển. Một phép kiểm tra sát thực tế hơn là chia dữ liệu theo mốc thời gian và đo ARI giữa các kỳ, nhưng cách đó cần dữ liệu giao dịch trải trên nhiều kỳ nên nằm ngoài phạm vi của project.

Thứ tư, độ ổn định chỉ được đo cho cấu hình tốt nhất của mỗi thuật toán. Ví dụ GMM `full` ở mục 5.3 cho thấy các cấu hình khác của cùng một thuật toán có thể có độ ổn định rất khác, nên kết quả trong báo cáo này gắn với ba cấu hình cụ thể ở mục 2.2 chứ không phải với ba thuật toán nói chung.
