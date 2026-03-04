# 5G-IoT Anomaly Detection System with Mininet-WiFi

Hệ thống phát hiện anomaly trong mạng 5G-IoT sử dụng Machine Learning và mô phỏng mạng với Mininet-WiFi.

## 📋 Tổng quan

Dự án này mô phỏng một mạng 5G-IoT với:
- **Edge Server**: Chạy mô hình ML để phát hiện anomaly realtime
- **5G Access Point**: Giả lập gNodeB (5G base station)
- **IoT Stations**: Các sensor nodes gửi dữ liệu đến Edge Server

```
┌─────────────────────────────────────────────────────┐
│              5G-IoT Network Topology                 │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐                                   │
│  │ Edge Server  │  10.0.0.100                       │
│  │  (ML Model)  │                                   │
│  └──────┬───────┘                                   │
│         │                                            │
│         │                                            │
│  ┌──────┴───────┐                                   │
│  │  Access Point │  5G gNodeB                       │
│  │  (ap1)        │  SSID: 5G-IoT-Network            │
│  └──────┬───────┘                                   │
│         │                                            │
│         ├─────────────┬──────────────┐              │
│         │             │              │               │
│  ┌──────┴──────┐ ┌──────┴──────┐ ┌──┴───────┐     │
│  │   sta1      │ │   sta2      │ │  sta3... │     │
│  │ 10.0.0.1    │ │ 10.0.0.2    │ │          │     │
│  │ IoT Sensor  │ │ IoT Sensor  │ │          │     │
│  └─────────────┘ └─────────────┘ └──────────┘     │
│                                                      │
│  Flow: Sensor Data → Edge Analysis → ML Detection  │
└─────────────────────────────────────────────────────┘
```

## ✨ Tính năng

- ✅ Mô phỏng mạng 5G-IoT với Mininet-WiFi
- ✅ Phát hiện anomaly realtime bằng Decision Tree
- ✅ Edge computing architecture
- ✅ Hỗ trợ nhiều IoT stations
- ✅ Logging và monitoring chi tiết
- ✅ Auto-start script với giám sát realtime

## 🔧 Yêu cầu hệ thống

### Phần cứng
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB)
- **CPU**: 2 cores trở lên
- **Disk**: 10GB trống

### Phần mềm
- **OS**: Ubuntu 20.04/22.04/24.04 hoặc WSL2 trên Windows
- **Python**: 3.8+
- **Mininet-WiFi**: 2.7
- **Thư viện Python**: scikit-learn, numpy, joblib, pandas

## 📦 Cài đặt

### Bước 1: Cài đặt Mininet-WiFi

```bash
# Clone repository
cd ~
git clone https://github.com/intrig-unicamp/mininet-wifi
cd mininet-wifi

# Cài đặt (mất khoảng 5-10 phút)
sudo util/install.sh -Wlnfv

# Kiểm tra
sudo mn --wifi --test pingall
```

### Bước 2: Cài đặt Python Dependencies

```bash
# Sử dụng apt (khuyến nghị cho Ubuntu 24.04)
sudo apt install -y python3-sklearn python3-joblib python3-pandas \
                    python3-matplotlib python3-seaborn

# Hoặc dùng pip (nếu cần)
pip3 install --break-system-packages scikit-learn joblib pandas
```

### Bước 3: Chuẩn bị Files

Đảm bảo bạn có cấu trúc thư mục:
```
detection_anomaly/
├── model/
│   ├── decision_tree_model_20260227_205406.pkl
│   ├── scaler_20260227_205406.pkl
│   └── feature_names_20260227_205406.pkl
└── system_detection/
    ├── 5g_iot_mininet.py
    ├── edge_server.py
    ├── iot_station.py
    ├── run_auto_simulation.py
    ├── quick_start.sh
    └── start_simulation.sh
```

## 🚀 Cách sử dụng

### Cách 1: Quick Start (Khuyến nghị) 🌟

Script tự động khởi động và giám sát realtime:

```bash
cd system_detection
./quick_start.sh
```

Script này sẽ:
- Cleanup network cũ
- Start edge server và IoT stations
- Hiển thị logs realtime mỗi 5 giây
- Thống kê requests (Total, Benign, Malicious)

### Cách 2: Tự động hoàn toàn

```bash
cd system_detection

# Cleanup trước
sudo mn -c

# Khởi động simulation
sudo python3 run_auto_simulation.py
```

Khi Mininet CLI xuất hiện, sử dụng các lệnh:

```bash
# Xem log edge server
mininet-wifi> edge1 tail -f /tmp/edge_server.log

# Xem log station 1
mininet-wifi> sta1 cat /tmp/sta1.log

# Xem log station 2
mininet-wifi> sta2 cat /tmp/sta2.log

# Ping test
mininet-wifi> sta1 ping -c3 edge1

# Thoát
mininet-wifi> exit
```

### Cách 3: Thủ công (Control hoàn toàn)

**Terminal 1** - Khởi động topology:
```bash
sudo mn -c
sudo python3 5g_iot_mininet.py
```

**Terminal 2** - Edge Server (trong Mininet CLI):
```bash
mininet-wifi> xterm edge1
# Trong cửa sổ edge1:
cd /path/to/system_detection
python3 -u edge_server.py ../model/decision_tree_model_*.pkl ../model/scaler_*.pkl
```

**Terminal 3** - IoT Station 1:
```bash
mininet-wifi> xterm sta1
# Trong cửa sổ sta1:
cd /path/to/system_detection
python3 iot_station.py sta1 2 0.2
# Tham số: <device_id> <interval_seconds> <anomaly_rate>
```

**Terminal 4** - IoT Station 2:
```bash
mininet-wifi> xterm sta2
# Trong cửa sổ sta2:
cd /path/to/system_detection
python3 iot_station.py sta2 3 0.15
```

### Cách 4: Tmux Mode (Nhiều terminal)

```bash
chmod +x start_simulation.sh
sudo ./start_simulation.sh
```

Lệnh tmux hữu ích:
- `tmux attach -t 5g-iot-sim` - Attach vào session
- `Ctrl+B` rồi `0-3` - Chuyển giữa các window
- `Ctrl+B` rồi `d` - Detach khỏi session
- `tmux kill-session -t 5g-iot-sim` - Dừng tất cả

## 📊 Monitoring và Logs

### Xem logs realtime

```bash
# Edge Server
sudo tail -f /tmp/edge_server.log

# Station 1
sudo tail -f /tmp/sta1.log

# Station 2
sudo tail -f /tmp/sta2.log
```

### Thống kê

```bash
# Tổng số requests
sudo grep -c "Request from" /tmp/edge_server.log

# Benign traffic
sudo grep -c "Benign" /tmp/edge_server.log

# Malicious traffic (anomaly detected)
sudo grep -c "Malicious" /tmp/edge_server.log

# Xem các anomaly alerts
sudo grep "ALERT" /tmp/edge_server.log
```

### Output mẫu

**IoT Station:**
```
[2026-03-01 00:12:11] Packet #1 - ✓ NORMAL DATA → Edge: Benign (100.0%)
[2026-03-01 00:12:13] Packet #2 - ⚠️  ANOMALY DATA → Edge: Benign (100.0%)
[2026-03-01 00:12:15] Packet #3 - ⚠️  ANOMALY DATA → Edge: Malicious (95.2%)
```

**Edge Server:**
```
[2026-03-01 00:12:11] Request from sta1 (10.0.0.1)
  → Prediction: Benign (Confidence: 100.00%)
[2026-03-01 00:12:13] Request from sta1 (10.0.0.1)
  ⚠️  ALERT: Malicious activity detected from sta1!
  → Prediction: Malicious (Confidence: 95.20%)
```

## 🔧 Cấu hình

### Thay đổi tham số IoT Station

Trong file `iot_station.py` hoặc khi chạy:
```bash
python3 iot_station.py <device_id> <interval> <anomaly_rate>

# Ví dụ:
python3 iot_station.py sta1 5 0.3
# Gửi mỗi 5 giây, 30% dữ liệu anomaly
```

### Thay đổi IP/Port Edge Server

Trong `edge_server.py`:
```python
def __init__(self, model_path, scaler_path, host='0.0.0.0', port=5000):
```

Trong `iot_station.py`:
```python
def __init__(self, device_id, edge_ip='10.0.0.100', edge_port=5000):
```

### Thêm IoT Stations

Trong `5g_iot_mininet.py` hoặc `run_auto_simulation.py`:
```python
sta3 = net.addStation(
    'sta3',
    ip='10.0.0.3/24',
    mac='00:00:00:00:00:13',
    position='50,70,0',
    range=20
)
```

## 🐛 Troubleshooting

### Lỗi: "Unable to locate package mininet-wifi"

Mininet-WiFi không có trong repos mặc định. Phải cài từ source (xem Bước 1).

### Lỗi: "RTNETLINK answers: File exists"

Network interfaces cũ chưa được cleanup:
```bash
sudo mn -c
```

### Lỗi: "No route to host" hoặc "timed out"

Kiểm tra:
1. Edge server đã khởi động chưa: `netstat -tuln | grep 5000`
2. Ping test: `sta1 ping -c3 edge1` trong Mininet CLI
3. Xem error logs: `cat /tmp/edge_server.log`

### Lỗi: "X has 25 features, but StandardScaler is expecting 24"

Đã fix trong phiên bản hiện tại. Nếu vẫn gặp, kiểm tra `iot_station.py` có 24 features (không có cs0).

### Warning: sklearn version mismatch

```
InconsistentVersionWarning: Trying to unpickle estimator from version 1.7.1 when using version 1.4.1
```

Warning này an toàn, model vẫn hoạt động bình thường. Để loại bỏ, retrain model với sklearn version hiện tại.

## 📁 Cấu trúc Files

```
system_detection/
├── 5g_iot_mininet.py          # Định nghĩa topology mạng
├── edge_server.py              # ML detection server
├── iot_station.py              # IoT sensor simulator
├── run_auto_simulation.py      # Auto start script (khuyến nghị)
├── quick_start.sh              # Quick start với monitoring
├── start_simulation.sh         # Tmux-based start script
├── README.md                   # File này
└── WINDOWS_WSL2_SETUP.md       # Hướng dẫn cho WSL2 users
```

## 🔬 Về ML Model

Model sử dụng Decision Tree được train trên dataset mạng có 24 features:
- Seq, Mean, sTos, sTtl, dTtl, sHops
- TotBytes, SrcBytes, Offset
- sMeanPktSz, dMeanPktSz, SrcWin
- TcpRtt, AckDat
- Protocol flags: e, e_d, icmp, tcp
- Connection states: CON, FIN, INT, REQ, RST, Status

**Output**: 
- `Benign`: Traffic bình thường
- `Malicious`: Anomaly/Attack detected

## 📝 Cleanup

Sau khi kết thúc:

```bash
# Stop Mininet và cleanup interfaces
sudo mn -c

# Xóa logs (optional)
sudo rm /tmp/*.log

# Kill processes nếu cần
sudo pkill -f "python3.*iot_station"
sudo pkill -f "python3.*edge_server"
```

## 🤝 Đóng góp

Issues và PRs được chào đón! Các cải tiến có thể:
- Thêm ML models khác (Random Forest, SVM, Neural Networks)
- Visualization dashboard
- Support cho nhiều edge servers
- Load balancing
- Database logging

## 📄 License

Dự án giáo dục, sử dụng tự do với attribution.

## 👥 Tác giả

Anomaly Detection in 5G-IoT Networks - 2026

## 🔗 Tài liệu tham khảo

- [Mininet-WiFi Documentation](https://mininet-wifi.github.io/)
- [Mininet-WiFi GitHub](https://github.com/intrig-unicamp/mininet-wifi)
- [Scikit-learn Documentation](https://scikit-learn.org/)

---

**Lưu ý**: Đây là mô phỏng cho mục đích học tập và nghiên cứu. Trong môi trường production thực tế, cần xem xét thêm về security, scalability, và reliability.
