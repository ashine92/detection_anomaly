# Anomaly Detection in 5G-IoT Networks

Hệ thống phát hiện anomaly cho mạng 5G-IoT với **Web Dashboard real-time**, **Edge Server AI**, và **Decision Tree 24 features**. Toàn bộ kết quả phát hiện đến từ Edge Server — không có mock, không có fake metrics.

---

## 📋 Project Structure

```
detection_anomaly/
├── README.md                       # File này
├── test_ai_system.py               # 🧪 Test suite toàn bộ hệ thống AI
│
├── dashboard/                      # 🌐 Web Monitoring Dashboard
│   ├── backend/
│   │   ├── app.py                  # Flask API — Routes & endpoints
│   │   ├── config.py               # Cấu hình server + model paths
│   │   ├── detection.py            # ⚠️ DEPRECATED — không còn được dùng
│   │   └── storage.py              # In-memory data storage
│   └── frontend/
│       └── index.html              # Real-time charts & tables
│
├── model/                          # 🤖 Trained Model Files
│   ├── decision_tree_model_20260305_223751.pkl   # Decision Tree (24 features)
│   ├── scaler_20260305_223751.pkl                # StandardScaler
│   └── feature_names_20260305_223751.pkl         # Tên 24 features
│
├── model_development/
│   └── train-model.ipynb           # Training notebook
│
├── dataset/
│   └── Encoded.csv                 # 5G-IoT traffic dataset
│
└── system_detection/               # 🔬 Network Simulation
    ├── edge_server_with_dashboard.py  # ⭐ Edge Server chính (port 5001)
    ├── edge_server.py              # Edge Server không có dashboard
    ├── iot_station.py              # IoT traffic generator (24 features)
    ├── dashboard_client.py         # HTTP client gửi kết quả → dashboard
    ├── run_auto_simulation.py      # Auto-start script
    ├── 5g_iot_mininet.py           # Mininet-WiFi topology
    └── ...
```

---

## 🏗️ Kiến trúc hệ thống

```
┌──────────────┐   24 features    ┌────────────────────────────┐
│  IoT Station │ ───────────────► │       Edge Server          │
│ (iot_station │   TCP :5001      │  edge_server_with_         │
│   .py)       │                  │  dashboard.py              │
└──────────────┘                  │                            │
                                  │  Decision Tree .pkl        │
                                  │  (24 features)             │
                                  │  → Benign / Malicious      │
                                  │  → probability_malicious   │
                                  │  → raw network features    │
                                  └──────────┬─────────────────┘
                                             │
                                  POST /api/metrics
                                  (prediction, confidence,
                                   probability_malicious,
                                   tot_bytes, tcp_rtt, ...)
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │    Web Dashboard    │
                                  │    app.py :5000     │
                                  │                     │
                                  │  Lưu trữ + Hiển thị │
                                  │  kết quả từ Edge AI │
                                  └──────────┬──────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │     Browser UI      │
                                  │  http://localhost   │
                                  │  :5000              │
                                  └─────────────────────┘
```

**Một tầng AI duy nhất** — toàn bộ phát hiện thực hiện tại Edge Server với model 24 features. Dashboard chỉ nhận, lưu trữ và hiển thị kết quả.

---

## 🚀 Cách vận hành

### Bước 1 — Khởi động Dashboard Backend (Terminal 1)

```bash
cd detection_anomaly/dashboard/backend
python3 app.py
```

Xác nhận thành công:
```
Edge AI Dashboard — nhận kết quả từ edge_server_with_dashboard.py
AI mode: edge_ai_24_features (không dùng detection.py)
👉 Open your browser: http://localhost:5000
```

### Bước 2 — Khởi động Edge Server (Terminal 2)

```bash
cd detection_anomaly/system_detection
python3 edge_server_with_dashboard.py
# Model paths được tự động tìm tại ../model/ — không cần truyền tham số
```

Hoặc chỉ định path tường minh:
```bash
python3 edge_server_with_dashboard.py \
    ../model/decision_tree_model_20260305_223751.pkl \
    ../model/scaler_20260305_223751.pkl
```

Xác nhận thành công:
```
✓ Model loaded successfully!
Server listening on 0.0.0.0:5001
Dashboard integration: ✅ Enabled
```

### Bước 3 — Chạy IoT Station (Terminal 3)

```bash
cd detection_anomaly/system_detection
python3 iot_station.py sta1 2 0.2
#                      ^    ^  ^
#               device_id  interval(s)  anomaly_rate(20%)
```

Output mẫu:
```
✓ NORMAL DATA   → Edge: Benign    (100.0%)
⚠️ ANOMALY DATA → Edge: Malicious (100.0%)
```

**Truy cập Dashboard**: Mở browser → `http://localhost:5000`

### Chạy nhiều IoT Stations song song

```bash
python3 iot_station.py sta1 2 0.1   # Camera an ninh — 10% anomaly
python3 iot_station.py sta2 1 0.3   # Sensor cảm biến — 30% anomaly
python3 iot_station.py sta3 3 0.0   # Gateway — 100% benign
```

---

## 📊 Data Flow chi tiết

### 1. IoT Station → Edge Server (TCP Socket :5001)

```json
{
  "device_id": "sta1",
  "features": [
    3.0,      // [0]  Seq
    4.998,    // [1]  Mean (giây)
    0.0,      // [2]  sTos
    117.0,    // [3]  sTtl
    64.0,     // [4]  dTtl
    11.0,     // [5]  sHops
    249093.0, // [6]  TotBytes
    244212.0, // [7]  SrcBytes
    336.0,    // [8]  Offset
    1245.98,  // [9]  sMeanPktSz
    271.17,   // [10] dMeanPktSz
    0.0,      // [11] SrcWin
    0.0,      // [12] TcpRtt
    0.0,      // [13] AckDat
    1.0,      // [14] ' e        '
    0.0,      // [15] ' e d      '
    0.0,      // [16] icmp
    0.0,      // [17] tcp
    1.0,      // [18] CON
    0.0,      // [19] FIN
    0.0,      // [20] INT
    0.0,      // [21] REQ
    0.0,      // [22] RST
    0.0       // [23] Status
  ]
}
```

### 2. Edge Server → IoT Station (TCP Response)

```json
{
  "device_id": "sta1",
  "prediction": "Benign",
  "confidence": 1.0,
  "probability_benign": 1.0,
  "probability_malicious": 0.0,
  "timestamp": "2026-03-06 10:00:00"
}
```

### 3. Edge Server → Dashboard (POST /api/metrics)

```json
{
  "timestamp":             "2026-03-06 10:00:00",
  "device_id":             "sta1",
  "prediction":            "Benign",
  "confidence":            1.0,
  "probability_malicious": 0.0,
  "tot_bytes":             249093.0,
  "src_bytes":             244212.0,
  "tcp_rtt":               0.0,
  "s_hops":                11.0,
  "s_ttl":                 117.0,
  "d_ttl":                 64.0,
  "s_mean_pkt_sz":         1245.98,
  "icmp":                  0,
  "tcp_flag":              0,
  "rst_flag":              0
}
```

> **Lưu ý**: `anomaly_score = probability_malicious` (bằng 0.0 cho Benign, 1.0 cho Malicious rõ ràng). Không có throughput/latency/packet_loss/rssi — những thông số này đã bị xóa vì là giả lập.

---

## 🌐 Dashboard — Những gì được hiển thị

### Stats Cards (6 thẻ)

| Thẻ | Ý nghĩa | Nguồn dữ liệu |
|-----|---------|--------------|
| Total Requests | Tổng số gói nhận từ Edge | `storage.stats.total_requests` |
| Total Anomalies | Gói bị xét là Malicious | `storage.stats.total_anomalies` |
| Anomaly Rate | Tỉ lệ % | tính từ 2 trên |
| Avg Anomaly Score | Trung bình `probability_malicious` | `avg_anomaly_score` |
| Avg Confidence | Trung bình độ tin cậy model | `avg_confidence` |
| Data Points | Số điểm dữ liệu đang lưu | `counts.total_metrics` |

### Charts (3 biểu đồ — tất cả từ dữ liệu thực)

| Biểu đồ | Trục Y | Dữ liệu |
|---------|--------|---------|
| Anomaly Score (P_malicious) Over Time | 0–1 | `probability_malicious` |
| Model Confidence Over Time | 0–1 | `confidence` |
| TotBytes Over Time | bytes | `tot_bytes` |

### Tables

- **Recent Anomaly Events Log** — chỉ gói Malicious, mới nhất trên đầu
- **Recent Metrics Log** — 20 gói gần nhất (cả Benign và Malicious)

Các cột trong bảng: Timestamp, Device ID, Severity, Anomaly Score, Confidence, TotBytes, TcpRtt, sHops, sTtl/dTtl, Flags (ICMP/TCP/RST)

---

## 🔌 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/` | Dashboard UI (index.html) |
| `POST` | `/api/metrics` | Nhận kết quả từ Edge Server |
| `GET` | `/api/metrics` | Lấy toàn bộ data (metrics + anomaly_events + statistics) |
| `POST` | `/api/reset` | Xóa toàn bộ dữ liệu |
| `GET` | `/health` | Health check |

**Required fields cho POST `/api/metrics`**:
`timestamp`, `device_id`, `prediction`, `confidence`, `probability_malicious`
(thiếu bất kỳ field nào → HTTP 400)

---

## 🧪 Test Suite

```bash
# Tier 1+2+5 — không cần server
python3 test_ai_system.py

# + Tier 3 — cần Dashboard đang chạy
python3 test_ai_system.py --api

# + Tier 4 — cần cả Dashboard + Edge Server
python3 test_ai_system.py --edge

# Tất cả tiers
python3 test_ai_system.py --all
```

| Tier | Nội dung | Cần server? |
|------|----------|-------------|
| **1** — Unit | Load `.pkl`, predict 6 samples thật từ dataset | ❌ |
| **2** — Module | `AnomalyDetector` import, `predict()` | ❌ |
| **3** — API | HTTP POST/GET đến Flask | ✅ Dashboard |
| **4** — Integration | TCP socket, 3 malicious + 1 benign + load test 10 req | ✅ Edge + Dashboard |
| **5** — Consistency | So sánh trực tiếp `.pkl` vs `AnomalyDetector` | ❌ |

**Kết quả hiện tại**: 38 PASS / 1 FAIL / 0 SKIP (97%)

---

## 🔍 Nhận diện nhanh Benign vs Malicious

| Feature | Benign | Malicious |
|---------|--------|-----------|
| `dTtl` | > 0 (có reply TTL) | = 0 (ICMP scan) |
| `Mean` (giây) | > 1.0 (long flow) | < 0.01 (rapid probe) |
| `TotBytes` | Lớn (> 10,000) | Nhỏ (< 200) |
| `dMeanPktSz` | > 0 (bidirectional) | = 0 (no reply) |
| `RST` | = 0 | = 1 (TCP RST scan) |
| `SrcWin` | varies | = 1024 (fixed, TCP RST) |

---

## 🔧 Cài đặt

```bash
pip install flask flask-cors numpy scikit-learn joblib pandas
```

Hoặc:
```bash
cd detection_anomaly/dashboard
python3 -m venv ../venv
source ../venv/bin/activate
pip install -r requirements.txt
```

**Yêu cầu**: Python 3.8+, scikit-learn ≥ 1.4, Flask 3.0+

---

## 🐛 Troubleshooting

### Edge Server báo "Port already in use"
```bash
lsof -i :5001 | grep LISTEN
kill -9 <PID>
```

### Dashboard không nhận dữ liệu
- Kiểm tra Edge Server đang chạy và kết nối được đến `http://localhost:5000/api/metrics`
- Xem log của Edge Server: dòng `Dashboard: ✓` xác nhận gửi thành công

### sklearn InconsistentVersionWarning
Model được train với sklearn 1.7.1. Chỉ là warning, không ảnh hưởng kết quả. Để loại bỏ, retrain bằng `train-model.ipynb` trên máy hiện tại rồi cập nhật timestamp trong `dashboard/backend/config.py` và trong `__main__` của `edge_server_with_dashboard.py`.

### Retrain model — cập nhật timestamp

Sau khi retrain, sửa 2 chỗ:

**`dashboard/backend/config.py`**:
```python
MODEL_PATH  = os.path.join(MODEL_DIR, 'decision_tree_model_YYYYMMDD_HHMMSS.pkl')
SCALER_PATH = os.path.join(MODEL_DIR, 'scaler_YYYYMMDD_HHMMSS.pkl')
```

**`system_detection/edge_server_with_dashboard.py`** (block `__main__`):
```python
_default_model  = os.path.join(_model_dir, 'decision_tree_model_YYYYMMDD_HHMMSS.pkl')
_default_scaler = os.path.join(_model_dir, 'scaler_YYYYMMDD_HHMMSS.pkl')
```

---

## 📄 Tài liệu liên quan

- [dashboard/README.md](dashboard/README.md) — Chi tiết dashboard
- [system_detection/README.md](system_detection/README.md) — Chi tiết simulation + Mininet
- [system_detection/QUICKSTART_REAL_DATA.md](system_detection/QUICKSTART_REAL_DATA.md) — Quick reference


