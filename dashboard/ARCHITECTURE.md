# 🛡️ 5G-IoT Anomaly Detection Dashboard - CLEAN ARCHITECTURE

## 📋 Tổng Quan Hệ Thống

Hệ thống giám sát và phát hiện bất thường mạng 5G-IoT theo thời gian thực với:
- **Backend**: Flask API với tích hợp AI Model (Decision Tree)
- **Frontend**: Dashboard hiện đại, responsive với Chart.js
- **Architecture**: Clean code, dễ mở rộng, modular design

---

## 📁 Cấu Trúc Thư Mục

```
dashboard/
├── backend/
│   ├── app.py                 # Flask API routes (main entry point)
│   ├── config.py              # Configuration management
│   ├── detection.py           # AI anomaly detection logic  
│   ├── storage.py             # Data storage layer
│   └── app_old.py             # Backup of old version
│
├── frontend/
│   ├── index.html             # Dashboard UI (improved version)
│   └── index_old.html         # Backup of old version
│
├── requirements.txt           # Python dependencies
├── test_dashboard.py          # Test data generator
├── dashboard_integration.py   # Integration examples
├── start_dashboard.sh         # Quick start script
├── README.md                  # This file
└── ARCHITECTURE.md            # Architecture documentation
```

---

## 🏗️ Clean Architecture Explained

### 1. **app.py** - API Routes Layer
```python
Trách nhiệm:
- Định nghĩa các API endpoints
- Validate request data
- Gọi detection.py để phân tích
- Gọi storage.py để lưu trữ
- Trả response về client

Endpoints:
- POST /api/metrics   → Nhận metrics, chạy AI detection
- GET  /api/metrics   → Lấy dữ liệu cho dashboard
- POST /api/reset     → Reset toàn bộ dữ liệu
- GET  /health        → Health check
- GET  /api/statistics→ Lấy thống kê chi tiết
```

### 2. **detection.py** - AI Detection Logic
```python
Trách nhiệm:
- Load AI model (Decision Tree)
- Tiền xử lý dữ liệu (preprocessing)
- Chạy model.predict()
- Tính toán anomaly score
- Phân loại severity (critical/high/medium/low)

Class: AnomalyDetector
Methods:
- _load_model()        → Load model, scaler, feature names
- preprocess_data()    → Chuẩn hóa input features
- predict()            → Dự đoán anomaly
- analyze_metrics()    → Phân tích tổng thể
```

### 3. **storage.py** - Data Persistence Layer
```python
Trách nhiệm:
- Lưu trữ metrics data (in-memory - FIFO queue)
- Lưu trữ anomaly events
- Tính toán statistics (avg, rates, counts)
- Cung cấp data cho dashboard

Class: DataStorage
Methods:
- add_metric()         → Thêm metric mới
- add_anomaly_event()  → Lưu sự kiện anomaly
- get_all_metrics()    → Lấy tất cả metrics
- get_dashboard_data() → Lấy dữ liệu cho dashboard
- reset_all()          → Xóa toàn bộ dữ liệu
```

### 4. **config.py** - Configuration Management
```python
Trách nhiệm:
- Quản lý cấu hình tập trung
- Path đến model files
- Thresholds và parameters
- Environment configs (dev/prod)

Configurations:
- Server: HOST, PORT, DEBUG
- Storage: MAX_DATA_POINTS, MAX_ANOMALY_EVENTS
- Model: MODEL_PATH, SCALER_PATH, FEATURE_NAMES_PATH
- Detection: ANOMALY_THRESHOLD
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy

### Bước 1: Cài đặt Dependencies

```bash
cd dashboard
pip install -r requirements.txt
```

**Dependencies cần thiết:**
- Flask==3.0.0
- flask-cors==4.0.0
- numpy==1.24.3
- scikit-learn==1.3.0

### Bước 2: Khởi động Backend Server

```bash
cd backend
python app.py
```

**Kết quả:**
```
======================================================================
  5G-IOT ANOMALY DETECTION DASHBOARD - BACKEND SERVER
======================================================================

🚀 Starting Flask server...

📊 Dashboard URL:
   • http://localhost:5000
   • http://127.0.0.1:5000

🔌 API Endpoints:
   • POST /api/metrics      - Receive metrics (with AI detection)
   • GET  /api/metrics      - Get dashboard data
   • GET  /api/statistics   - Get statistics
   • POST /api/reset        - Reset all data
   • GET  /health           - Health check

🤖 AI Model Status:
   ✓ Trained Decision Tree model loaded
   ✓ Features: ['throughput', 'latency', 'packet_loss', 'rssi']

💾 Storage Configuration:
   • Max metrics: 100
   • Max anomaly events: 200
======================================================================

👉 Open your browser: http://localhost:5000
```

### Bước 3: Mở Dashboard

Mở trình duyệt và truy cập:
```
http://localhost:5000
```

### Bước 4: Test với Dữ Liệu Mẫu

Mở terminal mới:
```bash
cd dashboard
python test_dashboard.py
```

**Kết quả bạn sẽ thấy:**
```
======================================================================
5G-IoT Anomaly Detection Dashboard - Test Data Generator
======================================================================
API Endpoint: http://localhost:5000/api/metrics
Data Interval: 1.0 seconds
Anomaly Frequency: Every 10 data points
======================================================================
Press Ctrl+C to stop

✓ [0000] NORMAL   | Device: IoT_Device_3   | Throughput:  45.3 Mbps | Latency:  12.5 ms | Score: 0.234
✓ [0001] NORMAL   | Device: IoT_Device_1   | Throughput:  52.1 Mbps | Latency:  18.2 ms | Score: 0.412
...
🚨 [0010] ANOMALY | Device: IoT_Device_2   | Throughput:  15.2 Mbps | Latency:  89.7 ms | Score: 0.856
```

---

## 📊 Tính Năng Dashboard

### 1. **Statistics Cards**
- ✅ **Total Requests**: Tổng số requests nhận được
- ✅ **Total Anomalies**: Tổng số anomaly phát hiện
- ✅ **Anomaly Rate (%)**: Tỷ lệ anomaly
- ✅ **Avg Throughput (Mbps)**: Throughput trung bình
- ✅ **Avg Latency (ms)**: Latency trung bình
- ✅ **Data Points**: Số lượng metrics đang lưu

### 2. **Real-time Charts**
- ✅ **Throughput Over Time**: Biểu đồ throughput theo thời gian
- ✅ **Latency Over Time**: Biểu đồ latency theo thời gian
- ✅ **Anomaly Score Trend**: Xu hướng anomaly score

### 3. **Event Tables**
- ✅ **Anomaly Events Log**: Bảng log các sự kiện anomaly
  - Hiển thị: Timestamp, Device ID, Severity, Score, Metrics
  - Highlight đỏ cho anomalies
  - Severity badges (Critical/High/Medium/Low)

- ✅ **Recent Metrics Log**: Bảng log 20 metrics gần nhất
  - Hiển thị: Timestamp, Device ID, Status, Score, Metrics
  - Màu xanh 🟢 = Normal
  - Màu đỏ 🔴 = Anomaly

### 4. **Controls**
- ⏸️ **Pause/Resume Auto-Refresh**: Tạm dừng/tiếp tục cập nhật tự động
- 🗑️ **Reset All Data**: Xóa toàn bộ dữ liệu

### 5. **Status Indicators**
- ✅ **Connection Status**: Hiển thị kết nối backend
- ✅ **System Status**: 
  - 🟢 Green badge = Normal
  - 🔴 Red pulsing badge = Anomaly Detected

### 6. **Design Features**
- ✅ Dark theme chuyên nghiệp
- ✅ Responsive design (mobile-friendly)
- ✅ Smooth animations và transitions
- ✅ Auto-refresh mỗi 2 giây
- ✅ Color-coded status (Green/Red/Yellow)

---

## 🔌 API Usage Examples

### 1. Gửi Metrics từ Simulation (POST)

```python
import requests
from datetime import datetime

# Prepare metrics data
data = {
    "timestamp": datetime.now().isoformat(),
    "device_id": "IoT_Station_1",
    "throughput": 45.5,      # Mbps
    "latency": 12.3,         # ms
    "packet_loss": 0.5,      # %
    "rssi": -65              # dBm
}

# Send to API
response = requests.post(
    'http://localhost:5000/api/metrics',
    json=data
)

print(response.json())
```

**Response:**
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

### 2. Lấy Dashboard Data (GET)

```python
import requests

response = requests.get('http://localhost:5000/api/metrics')
data = response.json()

print(f"Total Requests: {data['statistics']['total_requests']}")
print(f"Total Anomalies: {data['statistics']['total_anomalies']}")
print(f"Anomaly Rate: {data['statistics']['anomaly_rate']}%")
```

### 3. Reset Data (POST)

```python
import requests

response = requests.post('http://localhost:5000/api/reset')
print(response.json())
```

---

## 🔬 Tích Hợp với Simulation

### Option 1: Sử dụng DashboardClient Class

```python
from dashboard_integration import DashboardClient

# Initialize client
dashboard = DashboardClient()

# In your simulation loop
for iteration in simulation:
    # ... collect metrics ...
    
    # Send to dashboard
    dashboard.send_metrics(
        device_id="IoT_Device_1",
        throughput=throughput,
        latency=latency,
        packet_loss=packet_loss,
        rssi=rssi,
        # Model will auto-detect and add:
        # - anomaly_score
        # - prediction_label  
    )
```

### Option 2: Direct POST Request

```python
import requests
from datetime import datetime

def send_to_dashboard(metrics):
    """Send metrics to dashboard for AI detection"""
    try:
        data = {
            "timestamp": datetime.now().isoformat(),
            "device_id": metrics['device_id'],
            "throughput": metrics['throughput'],
            "latency": metrics['latency'],
            "packet_loss": metrics['packet_loss'],
            "rssi": metrics['rssi']
        }
        
        response = requests.post(
            'http://localhost:5000/api/metrics',
            json=data,
            timeout=1
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Sent | Prediction: {result['detection']['prediction_label']}")
            return True
        else:
            print(f"✗ Error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
```

---

## 🤖 AI Model Details

### Model Information
- **Type**: Decision Tree Classifier
- **Algorithm**: Scikit-learn DecisionTreeClassifier
- **Training Date**: 2026-02-27
- **Features**: 4 network metrics
- **Classes**: 0 (Normal), 1 (Anomaly)

### Input Features
1. **throughput** (Mbps) - Network throughput
2. **latency** (ms) - Network latency
3. **packet_loss** (%) - Packet loss percentage
4. **rssi** (dBm) - Signal strength

### Model Files
```
model/
├── decision_tree_model_20260227_205406.pkl  # Trained model
├── scaler_20260227_205406.pkl               # Feature scaler
└── feature_names_20260227_205406.pkl        # Feature names
```

### Detection Process
1. **Input**: Raw metrics (throughput, latency, packet_loss, rssi)
2. **Preprocessing**: Scale features using loaded scaler
3. **Prediction**: Model predicts class (0 or 1)
4. **Probability**: Get anomaly probability score (0-1)
5. **Severity**: Classify severity based on score
   - Critical: score >= 0.9
   - High: score >= 0.7
   - Medium: score >= 0.5
   - Low: score < 0.5
6. **Output**: prediction_label, anomaly_score, severity

---

## 📈 Monitoring & Statistics

### Thống kê được tính toán tự động:
- **Total Requests**: Đếm từ khi server khởi động
- **Total Anomalies**: Đếm số anomalies phát hiện
- **Anomaly Rate (%)**: (Total Anomalies / Total Requests) × 100
- **Avg Throughput**: Mean của tất cả throughput values
- **Avg Latency**: Mean của tất cả latency values

### Cập nhật Real-time:
- Dashboard auto-refresh mỗi **2 giây**
- Statistics được tính lại sau mỗi metric mới
- Charts update mượt mà không reload trang

---

## 🔧 Troubleshooting

### Lỗi: Model files not found
```
⚠ Using mock detection mode (model files not found)
```
**Giải pháp**: 
- Kiểm tra folder `model/` có chứa 3 files .pkl
- Cập nhật path trong `config.py` nếu cần

### Lỗi: Connection refused
```
✗ Disconnected from Backend Server
```
**Giải pháp**:
- Kiểm tra backend server có đang chạy không
- Verify port 5000 không bị block
- Check firewall settings

### Lỗi: CORS error
```
Access to fetch at ... has been blocked by CORS policy
```
**Giải pháp**:
- Đã enable CORS trong `app.py`
- Kiểm tra `config.py` → CORS_ORIGINS

### Charts không hiển thị
**Giải pháp**:
- Check browser console (F12) for errors
- Verify Chart.js CDN loaded
- Clear browser cache

---

## 🚦 Testing Scenarios

### Test 1: Normal Traffic
```python
python test_dashboard.py --anomaly-freq 100
```
→ Hầu hết data sẽ là Normal (green status)

### Test 2: High Anomaly Rate
```python
python test_dashboard.py --anomaly-freq 5
```
→ Mỗi 5 data points có 1 anomaly (red status)

### Test 3: Continuous Anomalies
```python
python test_dashboard.py --anomaly-freq 1
```
→ Mọi data point đều anomaly (stress test)

---

## 📝 Best Practices

### 1. Data Storage
- Hiện tại: In-memory (mất khi restart)
- Production: Chuyển sang database (PostgreSQL/MongoDB)
- Extend `storage.py` để thêm DB support

### 2. Security
- Production: Enable authentication
- Restrict CORS origins
- Use HTTPS/SSL
- Add rate limiting

### 3. Scalability
- Use Redis cho caching
- Implement WebSocket cho real-time updates
- Add message queue (RabbitMQ/Kafka)
- Deploy với Docker/Kubernetes

### 4. Monitoring
- Add logging framework (logging/loguru)
- Implement alerting system
- Use Prometheus + Grafana
- Add health checks

---

## 🎯 Future Enhancements

### Backend
- [ ] Database integration (PostgreSQL)
- [ ] WebSocket support for real-time push
- [ ] User authentication & authorization
- [ ] API rate limiting
- [ ] Caching with Redis
- [ ] Background task processing
- [ ] Email/SMS alerts on anomalies

### Frontend
- [ ] Advanced data visualization
- [ ] Customizable dashboard layouts
- [ ] Export data (CSV/Excel)
- [ ] Historical data analysis
- [ ] Dark/Light theme toggle
- [ ] Multi-language support
- [ ] Mobile app (React Native)

### ML/AI
- [ ] Model retraining pipeline
- [ ] Multiple model support (ensemble)
- [ ] Online learning
- [ ] Explainable AI (SHAP values)
- [ ] Anomaly type classification
- [ ] Predictive analytics

---

## 📞 Support & Contact

Nếu gặp vấn đề hoặc có câu hỏi:
1. Check ARCHITECTURE.md để hiểu chi tiết architecture
2. Xem code comments trong các files
3. Test với `test_dashboard.py`
4. Review logs trong terminal

---

## 📄 License

This project is part of the 5G-IoT Anomaly Detection System.

---

**Tạo bởi**: AI-Powered 5G-IoT Security Team  
**Ngày cập nhật**: March 4, 2026  
**Version**: 2.0 - Clean Architecture Edition
