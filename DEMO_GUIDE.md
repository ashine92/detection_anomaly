# Phát hiện Bất thường trong Mạng IoT sử dụng 5G
## Demo: Dashboard + Mininet-WiFi
### Real-time Anomaly Detection Visualization

---

## Mục lục

1. [Tổng quan](#tổng-quan)
2. [Setup Dashboard](#setup-dashboard)
3. [Khởi động Mininet-WiFi](#khởi-động-mininet-wifi)
4. [Dashboard Features](#dashboard-features)
5. [Demo Scenarios](#demo-scenarios)
6. [Pro Tips](#pro-tips)

---

## Tổng quan

### Yêu cầu chính

- **Dashboard Backend:** Flask API nhận predictions + lưu trữ metrics
- **Dashboard Frontend:** Real-time UI + live charts
- **Mininet-WiFi:** Mô phỏng mạng 5G-IoT với edge server + IoT stations
- **Attack Visualization:** Hiển thị attack types (7 loại) trên dashboard

---

## Setup Dashboard

### 1. Khởi động Dashboard Backend

```bash
cd /home/ashine/Downloads/detection_anomaly/dashboard/backend
python3 app.py
```

**Output mong đợi:**
```
 * Running on http://0.0.0.0:5000
 * Debug mode: off
```

### 2. Mở Dashboard Frontend

Mở browser:
```
http://localhost:5000
```

**Dashboard sẽ hiển thị:**
- 📊 Stats grid (Total Requests, Anomalies, Anomaly Rate, Avg Score)
- 📈 Live charts (Anomaly Score, TotBytes, Signal, Distribution)
- 🔴 Anomaly Events table
- 📋 Recent Metrics table  
- 🌐 Device Summary

---

## Khởi động Mininet-WiFi

### 1. Chạy Mininet Topology

```bash
cd /home/ashine/Downloads/detection_anomaly/system_detection
sudo python3 5g_iot_mininet.py
```

**Output Mininet-WiFi:**
```
*** Creating 5G-IoT Network with Mininet-WiFi
*** Adding Controller
*** Adding Edge Server
*** Adding Access Point (gNodeB - 5G Base Station)
*** Adding IoT Sensor Stations
*** Network Topology Created Successfully!

Edge Server: edge1 (IP: 10.0.0.100)
Access Point: ap1 (SSID: 5G-IoT-Network)
IoT Station 1: sta1 (IP: 10.0.0.1)
IoT Station 2: sta2 (IP: 10.0.0.2)

mininet-wifi>
```

### 2. Network Topology

```
┌──────────────────────┐
│  Edge Server (edge1) │
│   10.0.0.100        │
└──────────┬───────────┘
           │
      ┌────▼─────┐
      │  gNodeB  │ (5G Base Station)
      │   ap1    │
      └────┬─────┘
      ┌────┴─────┐
      │          │
   ┌──▼──┐   ┌───▼─┐
   │sta1 │   │sta2 │
   │IoT  │   │IoT  │
   └─────┘   └─────┘
```

---

## Demo Scenarios

Stations bắt đầu ở trạng thái **PAUSED** - dashboard sẽ trống.

Để bắt đầu gửi dữ liệu, từ **Mininet CLI** gửi lệnh trigger:

### Scenario 1: Normal Traffic

```bash
# Start sta1
mininet-wifi> sta1 touch /tmp/sta1_running

# Hoặc run sau này trong Mininet CLI (xem /tmp/sta1.log từng dòng):
mininet-wifi> sta1 tail /tmp/sta1.log

# Nếu muốn dừng lại:
mininet-wifi> sta1 rm /tmp/sta1_running
```

**Dashboard hiển thị:**
- ✓ Normal traffic (benign)
- Anomaly Score: 0.1 - 0.3 (low risk)

### Scenario 2: ICMP Flood Attack

```bash
# Start sta2 (có 15% xác suất tấn công)
mininet-wifi> sta2 touch /tmp/sta2_running

# Monitor attack
mininet-wifi> sta2 tail /tmp/sta2.log
```

**Dashboard hiển thị:**
- 🔴 Anomaly detected
- Attack Type: 🌊 ICMP Flood (88% confidence)
- Anomaly Score: 0.90 - 0.98 (critical)

### Scenario 3: Port Scan

```bash
# Dừng sta2, bắt đầu sta1 với anomaly tinggi
mininet-wifi> sta2 rm /tmp/sta2_running

# Hoặc tạo manual attack flow từ sta1
mininet-wifi> sta1 touch /tmp/sta1_running
```

**Dashboard hiển thị:**
- Attack Type: 🔍 Port Scan (88-90% confidence)

### Scenario 4: Start/Stop Multiple

```bash
# Bắt đầu cả hai
mininet-wifi> sta1 touch /tmp/sta1_running && sta2 touch /tmp/sta2_running

# Dừng tất cả
mininet-wifi> sta1 rm /tmp/sta1_running && sta2 rm /tmp/sta2_running

# Bắt đầu lại
mininet-wifi> sta1 touch /tmp/sta1_running && sta2 touch /tmp/sta2_running
```

---

## Dashboard Features

### 1. Stats Grid (Top)

- 📊 **Total Requests** - Total flows received
- 🚨 **Total Anomalies** - Flows detected as anomaly
- 📈 **Anomaly Rate** - % of anomalies
- 🎯 **Avg Anomaly Score** - Average P(Malicious)

### 2. Live Charts

- **Anomaly Score Over Time** - Red spikes = attacks detected
- **TotBytes Timeline** - Traffic volume pattern
- **Signal (dBm)** - WiFi signal strength (5G context)
- **Normal vs Anomaly Distribution** - Doughnut chart

### 3. Anomaly Events Table

Displays all detected anomalies with:
- Timestamp, Device ID, Severity, Attack Type
- Anomaly Score, TotBytes, SrcBytes, Flags
- Node, Signal, Bitrate

### 4. Recent Metrics Table

Shows latest network flows:
- Timestamp, Device ID, Status, Attack Type
- Raw network features (24 features)

### 5. Device Summary

Network topology aggregation:
- Device ID, Node, Station, AP SSID
- Signal, Bitrate, Total Packets, Anomaly Count

### 7 Attack Types Detected

| Type | Heuristic Rules | Confidence |
|------|-----------------|-----------|
| 🌊 ICMP Flood | icmp=1, d_ttl=0, tcp=0 | 88% |
| 🔍 Port Scan | tcp=1, tot_bytes≤5000 | 88-90% |
| ⚡ SYN Flood | tcp=1, tot_bytes≤5000, small packets | 85% |
| 🔴 Smurf Amp | icmp=1, d_ttl>0, large payload | 85% |
| 🔐 ICMP Tunnel | icmp=1, tot_bytes>10000 | 90% |
| 📋 FIN Scan | tcp=1, medium packets | 78% |
| ✓ Normal | benign traffic, large bidirectional flow | 95% |

---

## Pro Tips

### Before Demo

1. **Pre-warmup** (5 min trước)
   ```bash
   # Terminal 1: Start backend
   cd dashboard/backend && python3 app.py
   
   # Terminal 2: Start Mininet
   cd system_detection && sudo python3 5g_iot_mininet.py
   
   # Terminal 3: Monitor edge server logs
   tail -f /tmp/edge_server.log
   ```

2. **Browser Setup**
   - Open: `http://localhost:5000`
   - Resolution: 1920x1080 or higher
   - Zoom: 100%

3. **Dashboard will be EMPTY initially** - stations are in PAUSED state

### During Demo

**Stations start PAUSED!** Dashboard is clean unless you manually trigger.

**To START sending data** from Mininet CLI:
```bash
mininet-wifi> sta1 touch /tmp/sta1_running
mininet-wifi> sta2 touch /tmp/sta2_running
```

**To STOP sending data:**
```bash
mininet-wifi> sta1 rm /tmp/sta1_running
mininet-wifi> sta2 rm /tmp/sta2_running
```

**Watch the updates:**
- Dashboard charts update with new data every 2 seconds
- Edge server logs show predictions in real-time
- Station logs show packet transmission details

### Demo Flow Example

```bash
# 1. Setup
cd /home/ashine/Downloads/detection_anomaly/dashboard/backend
python3 app.py

# 2. In another terminal
cd /home/ashine/Downloads/detection_anomaly/system_detection
sudo python3 5g_iot_mininet.py

# 3. When Mininet CLI appears, do demo:
mininet-wifi> sta1 touch /tmp/sta1_running      # Start sta1 (normal data)
mininet-wifi> sta1 tail /tmp/sta1.log            # Watch logs
# [wait 10 seconds for dashboard to populate]

mininet-wifi> sta1 rm /tmp/sta1_running          # Stop sta1

mininet-wifi> sta2 touch /tmp/sta2_running       # Start sta2 (with anomalies)
mininet-wifi> sta2 tail /tmp/sta2.log
# [wait for anoma detected]

mininet-wifi> sta2 rm /tmp/sta2_running          # Stop sta2

mininet-wifi> exit                               # Exit CLI
```

### Demo Duration

- Setup: 5 min
- Mininet startup: 2 min
- 2-3 scenarios (controlled): 3-5 min each (6-15 min total)
- Dashboard overview: 3-5 min
- **Total: ~20-30 minutes** (much easier to control!)

### Easy Controls from CLI

| Action | Command |
|--------|---------|
| Start sta1 | `sta1 touch /tmp/sta1_running` |
| Stop sta1 | `sta1 rm /tmp/sta1_running` |
| Start sta2 | `sta2 touch /tmp/sta2_running` |
| Stop sta2 | `sta2 rm /tmp/sta2_running` |
| Start ALL | `sta1 touch /tmp/sta1_running && sta2 touch /tmp/sta2_running` |
| Stop ALL | `sta1 rm /tmp/sta1_running && sta2 rm /tmp/sta2_running` |
| Watch sta1 logs | `sta1 tail -f /tmp/sta1.log` |
| Watch sta2 logs | `sta2 tail -f /tmp/sta2.log` |
| Watch edge logs | `edge1 tail -f /tmp/edge_server.log` |

---

**Last Updated:** March 19, 2026

**Quick Start:**
```bash
# Terminal 1
cd /home/ashine/Downloads/detection_anomaly/dashboard/backend
python3 app.py

# Terminal 2
cd /home/ashine/Downloads/detection_anomaly/system_detection
sudo python3 5g_iot_mininet.py

# Browser
http://localhost:5000
```
