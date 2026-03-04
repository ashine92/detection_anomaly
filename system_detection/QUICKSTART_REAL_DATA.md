# 🚀 Quick Start - Real Data Integration

## Cách Chạy Nhanh (3 Bước)

### Bước 1: Khởi động Dashboard (Port 5000)
```bash
cd dashboard/backend
python app.py
```
✅ Dashboard chạy tại: http://localhost:5000

### Bước 2: Khởi động Edge Server với Dashboard (Port 5001)
```bash
cd system_detection

# Tìm model files
ls ../model/

# Chạy Edge Server (thay tên file cho đúng)
python edge_server_with_dashboard.py \
    ../model/decision_tree_model_20260227_205406.pkl \
    ../model/scaler_20260227_205406.pkl
```
✅ Edge Server lắng nghe tại **port 5001**, tự động gửi metrics đến Dashboard (port 5000)

### Bước 3: Test với Dữ Liệu Thật
```bash
# Terminal mới
cd system_detection
python test_real_data.py
```
✅ Script sẽ gửi traffic thật (normal + attack) đến Edge Server

---

## 💡 Hoặc Chạy IoT Stations Thực

Nếu bạn có IoT stations đang chạy:

```bash
# Test trên localhost (default: localhost:5001)
python3 iot_station.py sta1 2 0.2

# Hoặc specify edge server explicitly
python3 iot_station.py sta1 2 0.2 localhost 5001

# Trong Mininet (khi edge server chạy trên 10.0.0.100)
python3 iot_station.py sta1 2 0.2 10.0.0.100 5001
```

**Arguments:**
- `sta1`: Device ID
- `2`: Interval (giây giữa mỗi packet)
- `0.2`: Anomaly rate (20% là anomaly)
- `localhost`: Edge server IP (optional, default: localhost)
- `5001`: Edge server port (optional, default: 5001)

Edge Server sẽ tự động:
1. Nhận 24 features từ IoT station
2. Phát hiện anomaly bằng ML model
3. Tính toán network metrics (throughput, latency, packet loss, rssi)
4. Gửi đến Dashboard để AI phân tích thêm
5. Dashboard hiển thị real-time

---

## 🎯 Kết Quả Mong Đợi

**Edge Server Terminal:**
```
🟢 Prediction: Benign (Conf: 95.2%) | Metrics: 52.3 Mbps, 15.2 ms, 0.5% loss | Dashboard: ✓
🔴 Prediction: Malicious (Conf: 87.3%) | Metrics: 18.5 Mbps, 89.3 ms, 12.3% loss | Dashboard: ✓
🚨 Dashboard AI detected anomaly for IoT_Device_2: Score=0.856, Severity=high
```

**Dashboard (http://localhost:5000):**
- 📊 Real-time charts cập nhật
- 🔴 Anomaly events xuất hiện
- 📈 Statistics tính toán
- 🎨 Màu đỏ/xanh theo status

---

## 🔧 Troubleshooting

**Port already in use:**
```bash
# Dashboard (port 5000)
sudo lsof -i :5000
kill -9 <PID>

# Edge Server (port 5001)
sudo lsof -i :5001
kill -9 <PID>
```

**Dashboard không kết nối được:**
- Kiểm tra Dashboard có chạy không (curl http://localhost:5000/health)
- Xem log: "⚠ Dashboard not available"
- Edge Server vẫn chạy được, chỉ không gửi metrics

**Model không load được:**
```bash
# Verify model files
cd model/
ls -lh *.pkl

# Should see:
# decision_tree_model_*.pkl
# scaler_*.pkl
# feature_names_*.pkl
```

---

## 📚 Chi Tiết Hơn

Xem file: [REAL_DATA_INTEGRATION.md](../dashboard/REAL_DATA_INTEGRATION.md)

Có 2 options:
1. **Option 1**: Edge Server Integration (dễ, đang dùng)
2. **Option 2**: Mininet Monitor (metrics chính xác hơn, phức tạp hơn)
