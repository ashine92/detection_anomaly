# 🚀 QUICK START GUIDE

## Hướng dẫn chạy hệ thống trong 3 bước

---

## ⚡ Bước 1: Cài đặt Dependencies

```bash
cd dashboard
pip install -r requirements.txt
```

Cài đặt:
- Flask
- flask-cors  
- numpy
- scikit-learn

---

## 🖥️ Bước 2: Khởi động Backend Server

```bash
cd backend
python app.py
```

Bạn sẽ thấy:
```
======================================================================
  5G-IOT ANOMALY DETECTION DASHBOARD - BACKEND SERVER
======================================================================

🚀 Starting Flask server...

📊 Dashboard URL:
   • http://localhost:5000

🤖 AI Model Status:
   ✓ Trained Decision Tree model loaded
   ✓ Features: ['throughput', 'latency', 'packet_loss', 'rssi']
======================================================================

👉 Open your browser: http://localhost:5000
```

---

## 🌐 Bước 3: Mở Dashboard

Mở trình duyệt và truy cập:

```
http://localhost:5000
```

Bạn sẽ thấy dashboard với:
- ✅ 6 statistics cards (Total Requests, Anomalies, Rate, Avg Throughput, Latency, Data Points)
- ✅ 3 real-time charts (Throughput, Latency, Anomaly Score)
- ✅ 2 event tables (Anomaly Events, Recent Metrics)
- ✅ System status indicator (Green/Red)
- ✅ Auto-refresh mỗi 2 giây

---

## 🧪 Bước 4 (Optional): Test với Dữ Liệu Mẫu

Mở terminal mới:

```bash
cd dashboard
python test_dashboard.py
```

Bạn sẽ thấy:
```
✓ [0000] NORMAL   🟢 | Device: IoT_Device_3   | Throughput:  45.3 Mbps | Latency:  12.5 ms | AI Score: 0.234
✓ [0001] NORMAL   🟢 | Device: IoT_Device_1   | Throughput:  52.1 Mbps | Latency:  18.2 ms | AI Score: 0.412
...
🚨 [0010] ANOMALY 🔴 | Device: IoT_Device_2   | Throughput:  15.2 Mbps | Latency:  89.7 ms | AI Score: 0.856
```

Dashboard sẽ tự động cập nhật với dữ liệu test!

---

## 📊 Các tính năng chính

| Feature | Description |
|---------|------------|
| **AI Detection** | Tự động phát hiện anomaly bằng Decision Tree model |
| **Real-time Charts** | Biểu đồ cập nhật mỗi 2 giây |
| **Statistics** | Total Requests, Anomalies, Anomaly Rate (%) |
| **Status Indicator** | 🟢 Green = Normal, 🔴 Red = Anomaly |
| **Severity Levels** | Critical, High, Medium, Low |
| **Event Logging** | Log tất cả anomalies và metrics |

---

## 🔌 Gửi dữ liệu từ simulation

### Python Example:

```python
import requests
from datetime import datetime

data = {
    "timestamp": datetime.now().isoformat(),
    "device_id": "IoT_Device_1",
    "throughput": 45.5,      # Mbps
    "latency": 12.3,         # ms
    "packet_loss": 0.5,      # %
    "rssi": -65              # dBm
}

response = requests.post(
    'http://localhost:5000/api/metrics',
    json=data
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Prediction: {result['detection']['prediction_label']}")
print(f"Score: {result['detection']['anomaly_score']}")
```

### Response:

```json
{
    "status": "success",
    "message": "Metrics received and analyzed",
    "detection": {
        "prediction_label": "normal",
        "anomaly_score": 0.234,
        "severity": "low",
        "is_anomaly": false,
        "model_type": "trained"
    }
}
```

---

## 📁 Kiến trúc hệ thống

```
dashboard/
├── backend/
│   ├── app.py          # Flask API routes
│   ├── detection.py    # AI anomaly detection
│   ├── storage.py      # Data storage layer
│   └── config.py       # Configuration
│
├── frontend/
│   └── index.html      # Dashboard UI
│
└── model/              # AI models
    ├── decision_tree_model_*.pkl
    ├── scaler_*.pkl
    └── feature_names_*.pkl
```

---

## 🎯 API Endpoints

| Method | Endpoint | Description |
|--------|----------|------------|
| POST | `/api/metrics` | Nhận metrics + AI detection |
| GET | `/api/metrics` | Lấy data cho dashboard |
| POST | `/api/reset` | Reset tất cả dữ liệu |
| GET | `/health` | Health check |
| GET | `/api/statistics` | Lấy thống kê chi tiết |

---

## ⚙️ Customize

### Thay đổi auto-refresh interval

Edit `frontend/index.html`:
```javascript
const REFRESH_INTERVAL = 3000; // 3 seconds
```

### Thay đổi MAX data points

Edit `backend/config.py`:
```python
MAX_DATA_POINTS = 200  # Store last 200 points
```

### Thay đổi anomaly threshold

Edit `backend/config.py`:
```python
ANOMALY_THRESHOLD = 0.8  # More strict
```

---

## 🐛 Troubleshooting

### Backend không khởi động được
```bash
# Check Python version
python --version  # Need 3.7+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Dashboard không kết nối được backend
- ✅ Check backend có đang chạy không
- ✅ Verify URL: http://localhost:5000
- ✅ Check firewall/antivirus
- ✅ Try: http://127.0.0.1:5000

### Model không load được
- ✅ Check folder `model/` có 3 files .pkl
- ✅ Verify paths trong `config.py`
- ✅ Nếu không có model → Hệ thống dùng mock detection

### Charts không hiển thị
- ✅ Press F12 → Check console errors
- ✅ Clear browser cache
- ✅ Try different browser

---

## 📚 Tài liệu chi tiết

Xem **ARCHITECTURE.md** để hiểu:
- Clean architecture design
- Chi tiết từng module
- Best practices
- Future enhancements

---

## ✨ Hoàn tất!

Bây giờ bạn có:
- ✅ Backend server với AI anomaly detection
- ✅ Frontend dashboard hiện đại, real-time
- ✅ Test data generator
- ✅ Clean architecture, dễ mở rộng

**Enjoy monitoring your 5G-IoT network! 🎉**
