# Anomaly Detection in 5G-IoT Networks

Hệ thống phát hiện anomaly cho mạng 5G-IoT với **Web Dashboard real-time**, **Edge Server AI**, và **Decision Tree 24 features**. Toàn bộ kết quả phát hiện đến từ Edge Server — không có mock, không có fake metrics.

Hệ thống hỗ trợ **2 chế độ vận hành**:
- **Standalone** — Chạy trực tiếp trên máy host, phù hợp để test nhanh
- **Mininet-WiFi 5G** — Mô phỏng mạng 5G với wireless nodes, AP, và edge computing

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
    ├── iot_station.py              # IoT traffic generator (24 features)
    ├── dashboard_client.py         # HTTP client gửi kết quả → dashboard
    ├── 5g_iot_mininet.py           # ⭐ Mininet-WiFi 5G topology
    └── ...
```

---

## 🏗️ Kiến trúc hệ thống

### Kiến trúc chung (cả 2 mode)

```
IoT Station(s) ──TCP :5001──► Edge Server (AI) ──POST /api/metrics──► Flask Dashboard
                               Decision Tree                           app.py :5000
                               24 features                            Browser :5000
                               Benign/Malicious
```

### Mininet-WiFi mode — Luồng dữ liệu đầy đủ

```
sta1 (10.0.0.1) ──WiFi──┐
                         ├──► ap1 (5G-IoT-Network) ──► s1 switch ──► edge1 (10.0.0.100)
sta2 (10.0.0.2) ──WiFi──┘                                                    │
                                                                    AI detect (24 features)
                                                                              │
                                                              POST http://10.0.0.254:5000
                                                                              │
                                                           s1 bridge (10.0.0.254) ← host IP
                                                                              │
                                                              Flask app.py (0.0.0.0:5000)
                                                                              │
                                                              http://localhost:5000 ← Browser
```

**Một tầng AI duy nhất** — toàn bộ phát hiện thực hiện tại Edge Server. Dashboard chỉ nhận, lưu trữ và hiển thị kết quả.

---

## 🔵 Mode 1 — Standalone (Localhost)

Chạy toàn bộ hệ thống trên máy host không cần Mininet. Phù hợp để test nhanh, debug model.

### Cài đặt

```bash
pip install flask flask-cors numpy scikit-learn joblib pandas requests
```

### Khởi động (3 terminal riêng, theo thứ tự)

**Terminal 1 — Dashboard:**
```bash
cd detection_anomaly/dashboard
python backend/app.py
# ✅ Chờ: * Running on http://0.0.0.0:5000
```

**Terminal 2 — Edge Server:**
```bash
cd detection_anomaly/system_detection
python edge_server_with_dashboard.py
# ✅ Chờ: Dashboard integration: ✅ Enabled
# ✅ Chờ: 💻 Standalone mode (not in Mininet)
```

**Terminal 3 — IoT Station:**
```bash
cd detection_anomaly/system_detection
python iot_station.py sta1 2 0.2
#                      ^    ^  ^
#               device_id  interval(s)  anomaly_rate(20%)
```

**Truy cập dashboard**: `http://localhost:5000`

### Chạy nhiều stations song song

```bash
python iot_station.py sta1 2 0.1   # Camera an ninh — 10% anomaly
python iot_station.py sta2 1 0.3   # Sensor cảm biến — 30% anomaly
python iot_station.py sta3 3 0.0   # Gateway — 100% benign
```

### Xác nhận hoạt động

```bash
curl -s http://localhost:5000/health | python3 -m json.tool
# "status": "healthy"
# "mininet_wifi": {"active": false, ...}

curl -s http://localhost:5000/api/topology | python3 -m json.tool
# "in_mininet": false
# "nodes": [{"device_id": "sta1", ...}]
```

---

## 📶 Mode 2 — Mininet-WiFi 5G (Mô phỏng mạng thực)

Mô phỏng mạng 5G-IoT hoàn chỉnh với wireless stations, Access Point (gNodeB), edge computing node. Dữ liệu wireless thực (RSSI, bitrate) được đưa vào pipeline AI.

### Yêu cầu

```bash
# Mininet-WiFi phải được cài sẵn
sudo apt-get install mininet        # hoặc build từ source
# mn_wifi Python package
pip install mininet-wifi            # hoặc: sudo pip install mininet-wifi

# Kiểm tra
python -c "from mn_wifi.net import Mininet_wifi; print('OK')"
```

### Topology được tạo tự động

```
edge1 (10.0.0.100) ── s1 ── ap1 (5G-IoT-Network, 802.11ac, ch36)
                                  ├── sta1 (10.0.0.1,  pos 30,40,0)
                                  └── sta2 (10.0.0.2,  pos 70,60,0)

s1 bridge: 10.0.0.254  ← host machine Flask reachable tại địa chỉ này
```

### Khởi động (BẮT BUỘC đúng thứ tự)

**Bước 1 — Dọn dẹp môi trường cũ (mỗi lần start mới):**
```bash
sudo mn -c
sudo pkill -f "edge_server_with_dashboard.py" 2>/dev/null
sudo pkill -f "iot_station.py" 2>/dev/null
```

**Bước 2 — Terminal 1: Start Flask Dashboard TRƯỚC:**
```bash
cd detection_anomaly/dashboard
python backend/app.py
# ✅ Chờ: * Running on http://0.0.0.0:5000
```
> ⚠️ **Bắt buộc start Flask trước Mininet.** Nếu start sau, edge server sẽ fail health check lúc init và cần restart thủ công.

**Bước 3 — Terminal 2: Start Mininet-WiFi (dùng sudo):**
```bash
cd detection_anomaly/system_detection
sudo python 5g_iot_mininet.py
```

Script tự động thực hiện:
1. Tạo topology (edge1 + ap1 + sta1 + sta2)
2. Gán IP `10.0.0.254` cho OVS bridge `s1` → Flask reachable từ Mininet nodes
3. Thêm OpenFlow rule `actions=normal` cho bridge `s1`
4. Start Edge Server bên trong `edge1` với `MININET_NODE=edge1`
5. Start IoT Stations với `MININET_NODE=sta1/sta2`
6. Mở Mininet CLI

**Bước 4 — Kiểm tra trong Mininet CLI:**
```
mininet-wifi> edge1 tail -15 /tmp/edge_server.log
```
Kết quả mong đợi:
```
✓ Dashboard connected: http://10.0.0.254:5000/api/metrics
📶 Mininet-WiFi mode: node=edge1  AP=5G-IoT-Network
Dashboard integration: ✅ Enabled
🟢 [Benign] conf=100% p_mal=0.0000 | TotBytes=... sig=-76dBm | Dashboard: ✓
```

**Bước 5 — Xác nhận từ terminal thường:**
```bash
curl -s http://localhost:5000/api/topology | python3 -m json.tool
```
Kết quả mong đợi:
```json
{
    "in_mininet": true,
    "node_count": 2,
    "nodes": [
        {
            "device_id": "sta1",
            "mininet_node": "edge1",
            "ap_ssid": "5G-IoT-Network",
            "last_signal_dbm": -76,
            "last_link_bitrate_mbps": 54.0
        }
    ],
    "topology": {
        "ssid": "5G-IoT-Network",
        "bssid": "..."
    }
}
```

### Các lệnh hữu ích trong Mininet CLI

```
# Xem topology
mininet-wifi> nodes
mininet-wifi> links
mininet-wifi> dump

# Xem logs realtime
mininet-wifi> edge1 tail -f /tmp/edge_server.log
mininet-wifi> sta1  tail -f /tmp/sta1.log
mininet-wifi> sta2  tail -f /tmp/sta2.log

# Test connectivity
mininet-wifi> sta1 ping -c 3 10.0.0.100
mininet-wifi> edge1 curl -s http://10.0.0.254:5000/health

# Xem wireless info
mininet-wifi> sta1 iw dev sta1-wlan0 link

# Xem MININET_NODE đã được set chưa
mininet-wifi> edge1 env | grep MININET

# Mở terminal riêng
mininet-wifi> xterm edge1

# Thoát
mininet-wifi> exit
```

### Xử lý sự cố Mininet

**Dashboard vẫn `✗` sau khi Mininet start:**
```bash
# Kiểm tra OVS flow rules
sudo ovs-ofctl dump-flows s1

# Nếu trống → thêm thủ công
sudo ovs-ofctl add-flow s1 "priority=1,actions=normal"
```
Sau đó restart edge server trong Mininet CLI:
```
mininet-wifi> edge1 pkill -f edge_server_with_dashboard.py
mininet-wifi> edge1 cd /home/ashine/Downloads/detection_anomaly/system_detection && MININET_NODE=edge1 MININET_AP_SSID=5G-IoT-Network python3 -u edge_server_with_dashboard.py /home/ashine/Downloads/detection_anomaly/model/decision_tree_model_20260305_223751.pkl /home/ashine/Downloads/detection_anomaly/model/scaler_20260305_223751.pkl http://10.0.0.254:5000/api/metrics > /tmp/edge_server.log 2>&1 &
```

**`in_mininet: false` dù đã chạy 5g_iot_mininet.py:**

Kiểm tra thứ tự start: Flask **phải** chạy trước `sudo python 5g_iot_mininet.py`.

**`Connection refused` từ edge1 khi curl dashboard:**
```bash
# Kiểm tra IP bridge s1
ip addr show s1 | grep "10.0.0.254"

# Nếu không có → thêm thủ công
sudo ip addr add 10.0.0.254/24 dev s1
sudo ip link set s1 up
sudo ovs-ofctl add-flow s1 "priority=1,actions=normal"
```

### Mininet Wireless fields trong Dashboard

Khi chạy Mininet mode, các cột sau xuất hiện trong bảng dashboard:

| Field | Ý nghĩa | Ví dụ |
|-------|---------|-------|
| `Node` | Tên Mininet node | `edge1`, `sta1` |
| `Signal (dBm)` | RSSI từ `iw dev` | `-76` |
| `Bitrate (Mbps)` | Link bitrate | `54.0` |
| `AP SSID` | Tên Access Point | `5G-IoT-Network` |

---

## 📊 So sánh 2 Mode

| Tiêu chí | Standalone | Mininet-WiFi 5G |
|----------|-----------|-----------------|
| Yêu cầu | Python packages | + mininet-wifi, sudo |
| Dashboard URL | `http://localhost:5000` | `http://localhost:5000` (từ host) |
| Edge → Dashboard | `http://localhost:5000` | `http://10.0.0.254:5000` |
| `in_mininet` | `false` | `true` |
| `signal_dbm` | `null` | `-76` (dBm thực) |
| `ap_ssid` | `null` | `"5G-IoT-Network"` |
| Wireless simulation | ❌ | ✅ wmediumd interference |
| `/api/topology` | nodes rỗng | nodes đầy đủ |
| Log Edge Server | `💻 Standalone mode` | `📶 Mininet-WiFi mode` |

---

## 🔌 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/` | Dashboard UI (index.html) |
| `POST` | `/api/metrics` | Nhận kết quả từ Edge Server |
| `GET` | `/api/metrics` | Lấy toàn bộ data (metrics + anomaly_events + statistics) |
| `GET` | `/api/topology` | Mininet-WiFi topology (nodes, AP, signal) |
| `POST` | `/api/reset` | Xóa toàn bộ dữ liệu |
| `GET` | `/health` | Health check + Mininet status |

**Required fields cho POST `/api/metrics`**:
`timestamp`, `device_id`, `prediction`, `confidence`, `probability_malicious`

**Optional Mininet fields** (tự động thêm khi chạy Mininet mode):
`mininet_node`, `station_node`, `ap_ssid`, `ap_bssid`, `signal_dbm`, `link_bitrate_mbps`

---

## 🧪 Test Suite

```bash
# Tier 1+2+5 — không cần server
python3 test_ai_system.py

# + Tier 3 — cần Dashboard đang chạy
python3 test_ai_system.py --api

# + Tier 4 — cần cả Dashboard + Edge Server
python3 test_ai_system.py --edge

# + Tier 6 — cần Mininet-WiFi
python3 test_ai_system.py --mininet

# Tất cả tiers
python3 test_ai_system.py --all
```

| Tier | Nội dung | Cần server? |
|------|----------|-------------|
| **1** — Unit | Load `.pkl`, predict samples thật từ dataset | ❌ |
| **2** — Module | `AnomalyDetector` import, `predict()` | ❌ |
| **3** — API | HTTP POST/GET đến Flask | ✅ Dashboard |
| **4** — Integration | TCP socket, mal/benign + load test | ✅ Edge + Dashboard |
| **5** — Consistency | So sánh `.pkl` vs `AnomalyDetector` | ❌ |
| **6** — Mininet | mn_wifi import, syntax, wireless interface | ✅ Mininet |

---

## 🔧 Cài đặt

```bash
# Standalone
pip install flask flask-cors numpy scikit-learn joblib pandas requests

# Mininet-WiFi (thêm)
sudo apt-get install mininet
pip install mininet-wifi
```

---

## 🐛 Troubleshooting chung

### Edge Server báo "Port already in use"
```bash
lsof -i :5001 | grep LISTEN
kill -9 <PID>
```

### sklearn InconsistentVersionWarning
Model train với sklearn 1.7.1. Chỉ là warning, không ảnh hưởng kết quả. Retrain bằng `train-model.ipynb` để loại bỏ.

### Dashboard không nhận dữ liệu (Standalone)
Kiểm tra Edge Server log: dòng `Dashboard: ✓` xác nhận gửi thành công. Nếu `Dashboard: ✗`, kiểm tra Flask có đang chạy không.

---

## 📄 Tài liệu liên quan

- [dashboard/README.md](dashboard/README.md) — Chi tiết dashboard
- [system_detection/README.md](system_detection/README.md) — Chi tiết simulation
- [system_detection/QUICKSTART_REAL_DATA.md](system_detection/QUICKSTART_REAL_DATA.md) — Quick reference


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


