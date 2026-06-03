# 📊 BÁO CÁO TỐI ƯU HÓA MÔ HÌNH HỌC MÁY (MODEL IMPROVEMENT REPORT)

**Ngày cập nhật:** 2026-06-03
**Tác giả:** Model Optimization Team
**Mục đích:** Ghi nhận quá trình phân tích và khắc phục vấn đề Overfitting của mô hình cũ, từ đó nâng cấp lên mô hình Random Forest hiện tại.

---

## 🔍 1. VẤN ĐỀ CỦA MÔ HÌNH CŨ (Decision Tree)

Mô hình ban đầu sử dụng thuật toán Decision Tree và StandardScaler. Dù đạt hiệu năng cao trên tập dữ liệu chuẩn, mô hình lộ rõ điểm yếu khi đối mặt với dữ liệu kiểm thử tổng hợp (Synthetic Data):

- **Test Accuracy (Dữ liệu chuẩn):** 99.97%
- **Synthetic Test Accuracy:** Chỉ đạt 40%. Tất cả các mẫu tấn công giả lập đều bị phân loại sai thành Benign với độ tự tin (confidence) 100%.

### Nguyên nhân cốt lõi:
1. **Overfitting (Học vẹt):** Decision Tree đơn lẻ có xu hướng ghi nhớ các mẫu trong tập huấn luyện. Khi gặp dữ liệu có phân phối khác biệt (out-of-distribution), mô hình hoàn toàn mất khả năng khái quát hóa.
2. **Nhạy cảm với Outliers:** Việc sử dụng StandardScaler khiến dữ liệu bị méo mó khi xuất hiện các giá trị cực đoan (outliers) phổ biến trong các đợt tấn công DDoS.
3. **Mẫu Synthetic không thực tế:** Các mẫu tấn công giả lập được tạo ra ban đầu chứa những giá trị phi thực tế (Ví dụ: `Seq = 999,999` hoặc `TotBytes = 5,000,000` - vượt xa mức tối đa trong thực tế), khiến Z-score vượt xa khỏi phân phối đã học.

---

## 💡 2. CÁC GIẢI PHÁP ĐÃ TRIỂN KHAI

Để khắc phục triệt để vấn đề trên, toàn bộ quy trình huấn luyện đã được thiết kế lại và đóng gói trong tệp `retrain-model-FINAL-OPTIMIZED.ipynb`.

### 2.1. Nâng cấp lên Random Forest Classifier
Thay vì dùng một cây quyết định duy nhất, hệ thống đã chuyển sang sử dụng quần thể (Ensemble) gồm 100 cây quyết định (Random Forest).
- **Lợi ích:** Giảm thiểu phương sai (variance), ngăn chặn overfitting nhờ cơ chế Random Subspace và Bagging. Quyết định cuối cùng dựa trên bình chọn đa số (Majority Voting) giúp mô hình hoạt động ổn định và chính xác hơn.

### 2.2. Feature Engineering (Khai phá đặc trưng)
Hệ thống không chỉ dùng 24 tính năng nguyên bản mà trích xuất thêm 3 tính năng phái sinh (derived features) mang ý nghĩa chuyên môn về mạng:
1. **`BytesRatio` = `SrcBytes / (TotBytes + 1)`**: Phân tích sự bất đối xứng của luồng dữ liệu.
2. **`PktSizeRatio` = `sMeanPktSz / (dMeanPktSz + 1)`**: Phát hiện tỷ lệ bất thường về kích thước gói tin.
3. **`TTLDiff` = `|sTtl - dTtl|`**: Đo lường độ lệch Time-To-Live để phát hiện giả mạo IP (Spoofing).
➡️ **Tổng số features tăng từ 24 lên 27.**

### 2.3. Chuyển đổi sang RobustScaler
Thay thế StandardScaler bằng RobustScaler.
- **Lợi ích:** RobustScaler sử dụng trung vị (Median) và khoảng tứ phân vị (IQR) thay vì trung bình (Mean). Nhờ đó, quá trình chuẩn hóa không bị sai lệch bởi các giá trị nhiễu lớn (extreme outliers) sinh ra bởi các cuộc tấn công flooding.

### 2.4. Tối ưu hóa Siêu tham số (Hyperparameter Tuning)
Sử dụng `GridSearchCV` để tìm ra cấu hình tối ưu nhất nhằm cân bằng giữa việc học đặc trưng và tránh học vẹt:
- `n_estimators = 100`
- `max_depth = 20`
- `min_samples_split = 100`
- `min_samples_leaf = 50`
- `class_weight = 'balanced'` (Tự động bù đắp sự chênh lệch số lượng mẫu giữa nhãn Malicious và Benign).

---

## 🚀 3. KẾT QUẢ ĐẠT ĐƯỢC

Mô hình mới đã khắc phục hoàn toàn những yếu điểm trước đây và chính thức được đưa vào Production.

| Tiêu chí | Decision Tree (Cũ) | Random Forest (Mới) | Đánh giá |
|----------|-------------------|---------------------|----------|
| **Test Accuracy** | 99.97% | **99.97%** | ✅ Giữ vững hiệu năng |
| **ROC AUC** | ~1.0000 | **1.0000** | ✅ Hoàn hảo |
| **Độ chính xác thực tế (Real Data)** | Không đánh giá | **100% (120/120 mẫu)** | ✅ Tuyệt đối |
| **Khả năng khái quát hóa** | Kém | Rất Tốt | ✅ Cải thiện rõ rệt |

Chi tiết hơn về kết quả kiểm định cuối cùng có thể xem tại: `FINAL_MODEL_VALIDATION_REPORT.md`.

---

## 📁 4. TRẠNG THÁI TỆP TIN

Các tệp nháp và thuật toán cũ (như các file Python xử lý nháp hay file Notebook Decision Tree cũ) đã được dọn dẹp khỏi repository để tránh nhầm lẫn. 

Quy trình chuẩn duy nhất hiện tại được lưu tại:
👉 `model_development/retrain-model-FINAL-OPTIMIZED.ipynb`

Mô hình đã huấn luyện sẵn sàng để sử dụng được lưu tại thư mục `model/`:
- `random_forest_model_*.pkl`
- `scaler_*.pkl`
- `feature_names_*.pkl`
