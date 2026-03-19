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

Trong Mininet CLI, chạy các lệnh sau và xem dashboard cập nhật real-time:

### Scenario 1: Normal Traffic

```bash
mininet-wifi> sta1 ping -c 5 edge1
```

**Dashboard hiển thị:**
- Status: ✓ Normal
- Attack Type: ✓ Normal 
- Anomaly Score: 0.1 - 0.3 (low)

### Scenario 2: ICMP Flood Attack

```bash
mininet-wifi> sta2 timeout 10 ping -i 0.01 -s 100 edge1
```

**Dashboard hiển thị:**
- Status: 🔴 Anomaly
- Attack Type: 🌊 ICMP Flood (88% confidence)
- Anomaly Score: 0.90 - 0.98 (critical)

### Scenario 3: TCP Port Scan

```bash
mininet-wifi> sta1 timeout 5 hping3 -S edge1
```

**Dashboard hiển thị:**
- Status: 🔴 Anomaly
- Attack Type: 🔍 Port Scan (88-90% confidence)
- Anomaly Score: 0.85 - 0.95

### Scenario 4: TCP SYN Flood

```bash
mininet-wifi> sta1 timeout 5 hping3 -S --flood edge1
```

**Dashboard hiển thị:**
- Status: 🔴 Anomaly
- Attack Type: ⚡ SYN Flood (85% confidence)
- Anomaly Score: 0.88 - 0.95

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

3. **Terminal Font**
   - Use large font (12-14pt) for readability

### During Demo

1. **Watch Dashboard Update**
   - Charts should update every 2 seconds
   - Anomaly events table shows new rows as attacks happen
   - Attack Type column shows heuristic classification

2. **Mininet CLI Commands**
   - After running attack, dashboard should show anomaly spike within 2 seconds
   - Check edge server logs in Terminal 3 for real-time predictions

3. **Flow**
   - Start with normal traffic (builds confidence)
   - Then show attacks progressively (Normal → ICMP → Port Scan → SYN Flood)
   - Highlight real-time detection

### Demo Duration

- Setup: 5 min
- Mininet startup: 2 min
- 4 scenarios: 1-2 min each (4-8 min total)
- Dashboard overview: 5 min
- **Total: ~20-25 minutes**

### Backup Plans

If anything fails:
1. Pre-record 2-min video of each scenario
2. Have pre-populated database JSON
3. Screenshot of expected dashboard state

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
