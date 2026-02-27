# Mô phỏng Mạng 5G-IoT với Mininet-WiFi

## Tổng quan
Hệ thống mô phỏng mạng 5G-IoT sử dụng Mininet-WiFi để phát hiện anomaly trong thời gian thực.

### Kiến trúc
```
┌──────────────────────────────────────────────────────────┐
│                    5G-IoT Network                         │
│                                                            │
│  ┌──────────┐         ┌──────────┐         ┌──────────┐  │
│  │   sta1   │         │   AP1    │         │  Edge    │  │
│  │ IoT Node │◄───────►│ gNodeB   │◄───────►│  Server  │  │
│  │10.0.0.1  │  WiFi   │ 5G Base  │  Wire   │10.0.0.100│  │
│  └──────────┘         │ Station  │         └──────────┘  │
│                       └──────────┘                        │
│  ┌──────────┐              ▲                              │
│  │   sta2   │              │                              │
│  │ IoT Node │──────────────┘                              │
│  │10.0.0.2  │     WiFi                                    │
│  └──────────┘                                             │
│                                                            │
│  Sensor Data ──► Edge Analysis ──► ML Detection           │
└──────────────────────────────────────────────────────────┘
```

### Các thành phần:
1. **Edge Server** (10.0.0.100): Chạy mô hình ML để phát hiện anomaly
2. **Access Point (ap1)**: Giả lập 5G gNodeB
3. **IoT Stations**: 
   - sta1 (10.0.0.1): Sensor node 1
   - sta2 (10.0.0.2): Sensor node 2

## Yêu cầu hệ thống

### Phần cứng
- RAM: Tối thiểu 4GB
- CPU: 2 cores trở lên
- Disk: 10GB trống

### Phần mềm
- OS: Ubuntu 20.04/22.04 hoặc WSL2 trên Windows
- Python: 3.8+
- Mininet-WiFi
- Các thư viện Python: scikit-learn, numpy, joblib

## Cài đặt

### 1. Cài đặt Mininet-WiFi

```bash
# Clone repository
git clone https://github.com/intrig-unicamp/mininet-wifi
cd mininet-wifi

# Cài đặt
sudo util/install.sh -Wlnfv

# Kiểm tra cài đặt
sudo mn --wifi --test pingall
```

### 2. Cài đặt Python Dependencies

```bash
pip3 install scikit-learn numpy joblib pandas
```

### 3. Copy các file

```bash
# Copy các file từ thư mục dự án
cp 5g_iot_mininet.py /path/to/project/
cp edge_server.py /path/to/project/
cp iot_station.py /path/to/project/
cp decision_tree_model_*.pkl /path/to/project/
cp scaler_*.pkl /path/to/project/
```

## Sử dụng

### Cách 1: Chạy thủ công (Recommended)

#### Bước 1: Khởi động Mininet-WiFi topology
```bash
sudo python3 5g_iot_mininet.py
```

Khi CLI xuất hiện:
```
mininet-wifi>
```

#### Bước 2: Khởi động Edge Server
Mở terminal mới trong Mininet CLI:
```bash
mininet-wifi> xterm edge1
```

Trong terminal edge1:
```bash
python3 edge_server.py decision_tree_model_20260227_205406.pkl scaler_20260227_205406.pkl
```

#### Bước 3: Khởi động IoT Stations
Mở terminal cho sta1:
```bash
mininet-wifi> xterm sta1
```

Trong terminal sta1:
```bash
python3 iot_station.py sta1 2 0.2
# sta1: device ID
# 2: gửi dữ liệu mỗi 2 giây
# 0.2: 20% dữ liệu là anomaly
```

Mở terminal cho sta2:
```bash
mininet-wifi> xterm sta2
```

Trong terminal sta2:
```bash
python3 iot_station.py sta2 3 0.15
# 3 giây interval, 15% anomaly rate
```

### Cách 2: Script tự động

```bash
chmod +x start_simulation.sh
sudo ./start_simulation.sh
```

## Kiểm tra kết nối

Trong Mininet CLI:

```bash
# Xem các node
mininet-wifi> nodes

# Xem links
mininet-wifi> links

# Ping test
mininet-wifi> sta1 ping -c 3 edge1

# Ping between stations
mininet-wifi> sta1 ping -c 3 sta2
```

## Giám sát

### Xem log Edge Server
Edge Server sẽ hiển thị:
- Requests từ IoT devices
- Predictions (Benign/Malicious)
- Confidence scores
- Statistics

### Xem log IoT Stations
Mỗi station hiển thị:
- Packet count
- Data type (Normal/Anomaly)
- Edge server response

## Tùy chỉnh

### Thay đổi anomaly rate
Chỉnh tham số thứ 3 khi chạy iot_station.py:
```bash
python3 iot_station.py sta1 2 0.5  # 50% anomaly
```

### Thay đổi sending interval
Chỉnh tham số thứ 2:
```bash
python3 iot_station.py sta1 5 0.2  # mỗi 5 giây
```

### Thay đổi IP/Port Edge Server
Sửa trong `edge_server.py` và `iot_station.py`:
```python
# edge_server.py
def __init__(self, model_path, scaler_path, host='10.0.0.100', port=5000):

# iot_station.py
def __init__(self, device_id, edge_ip='10.0.0.100', edge_port=5000):
```

## Troubleshooting

### Lỗi: "Mininet-WiFi not installed"
```bash
sudo util/install.sh -Wlnfv
```

### Lỗi: "Connection refused"
- Kiểm tra Edge Server đã chạy chưa
- Kiểm tra IP/Port đúng không
- Test ping: `sta1 ping edge1`

### Lỗi: "Model file not found"
- Kiểm tra đường dẫn đến file .pkl
- Copy file model vào cùng thư mục

### Lỗi: Permission denied
```bash
sudo python3 5g_iot_mininet.py
```

## Tham số mô hình

- **Model**: Decision Tree Classifier
- **Accuracy**: 99.96%
- **Features**: 24 network features
- **Classes**: Benign, Malicious

## Ví dụ Output

### Edge Server:
```
======================================================================
EDGE IoT DETECTION SERVER
======================================================================
Server started on 10.0.0.100:5000
Waiting for IoT device connections...
======================================================================

[2026-02-27 20:54:06] Request from sta1 (10.0.0.1)
  → Prediction: Benign (Confidence: 99.87%)

[2026-02-27 20:54:08] Request from sta2 (10.0.0.2)
  ⚠️  ALERT: Malicious activity detected from sta2!
  → Prediction: Malicious (Confidence: 98.54%)
```

### IoT Station:
```
======================================================================
IoT SENSOR STATION: sta1
======================================================================
Edge Server: 10.0.0.100:5000
Sending data every 2 seconds
Anomaly rate: 20.0%
======================================================================

[2026-02-27 20:54:06] Packet #1 - ✓ NORMAL DATA → Edge: Benign (99.9%)
[2026-02-27 20:54:08] Packet #2 - ⚠️  ANOMALY DATA → Edge: Malicious (98.5%)
```

## Dừng mô phỏng

1. Ctrl+C trên mỗi terminal (edge_server, stations)
2. Trong Mininet CLI: `exit`
3. Clean up: `sudo mn -c`

## Liên hệ

Nếu có vấn đề, report tại: [GitHub Issues](https://github.com/yourusername/5g-iot-simulation/issues)

## License

MIT License
