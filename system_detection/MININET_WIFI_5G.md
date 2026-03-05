# Mininet-WiFi trong hệ thống 5G-IoT Anomaly Detection

Tài liệu này mô tả chi tiết cách Mininet-WiFi được áp dụng để mô phỏng môi trường mạng 5G-IoT, bao gồm kiến trúc topology, cơ chế hoạt động từng thành phần, và luồng dữ liệu end-to-end.

---

## 1. Mininet-WiFi là gì?

Mininet-WiFi là extension của Mininet, cho phép tạo **mạng ảo hoàn chỉnh trực tiếp trong Linux kernel** bao gồm:

- **Wired nodes** (host, switch, controller) — từ Mininet gốc
- **Wireless nodes** (station, access point) — thêm bởi Mininet-WiFi
- **RF propagation model** — thông qua `wmediumd`, mô phỏng nhiễu, suy hao tín hiệu, phạm vi phủ sóng

Không giống emulator phần mềm thông thường, mỗi node trong Mininet-WiFi là một **Linux network namespace thực**, với:
- Interface mạng riêng (ảo nhưng hoạt động thực với kernel TCP/IP)
- Bảng định tuyến riêng
- Process space có thể chạy chương trình thực

---

## 2. Tại sao dùng Mininet-WiFi để mô phỏng 5G?

5G NR (New Radio) thực sự đòi hỏi phần cứng radio chuyên dụng (gNodeB, UE chipset). Trong nghiên cứu và giáo dục, Mininet-WiFi cung cấp cách tiếp cận khả thi:

| Thành phần 5G thực | Thay thế bằng Mininet-WiFi | Lý do chấp nhận được |
|---|---|---|
| 5G gNodeB (base station) | `OVSKernelAP` với `mode='ac'` (802.11ac 5GHz) | Cùng cơ chế wireless association, handover |
| 5G NR air interface | wmediumd interference model | Mô phỏng được path loss, nhiễu RF thực tế |
| UE (user equipment) | `Station` — wireless namespace | Có thể di chuyển, thay đổi tín hiệu |
| MEC/Edge Server | `Host` chạy Python process thực | Xử lý AI inference giống triển khai thật |
| 5G Core backhaul | OVS switch + Linux bridge | Routing, forwarding thực trong kernel |

> **Giới hạn**: Không mô phỏng được 5G protocol stack tầng thấp (PDCP, RLC, MAC) hay beamforming, massive MIMO. Đây là giả lập ở tầng IP trở lên.

---

## 3. Topology mạng

File: [`5g_iot_mininet.py`](5g_iot_mininet.py)

### 3.1 Sơ đồ

```
                     wmediumd RF interference model
                     (mode=ac, channel=36, 5GHz, range=50m)

  [sta1]  pos(30,40,0)  ))))  ·  ·  ·  ·  ·  ·
  IP: 10.0.0.1/24              ·                 ))))  [ap1 / OVSKernelAP]
  IoT Sensor Node 1            ·  RF propagation       ssid: 5G-IoT-Network
                               ·                       pos: 50,50,0
  [sta2]  pos(70,60,0)  ))))  ·                        |
  IP: 10.0.0.2/24                                      |  (wired backhaul)
  IoT Sensor Node 2                                    |
                                                  [s1 / OVSKernelSwitch]
                                                       |
                                                  [edge1]
                                                  IP: 10.0.0.100/24
                                                  edge_server_with_dashboard.py
                                                  port: 5001 (TCP socket)
                                                       |
                                                  [Dashboard: app.py]
                                                  IP: host machine (localhost)
                                                  port: 5000 (HTTP)
```

### 3.2 Thông số cấu hình

```python
# Access Point (gNodeB giả lập)
ap1 = net.addAccessPoint(
    'ap1',
    ssid    = '5G-IoT-Network',
    mode    = 'ac',      # 802.11ac — Wi-Fi 5, băng tần 5GHz
    channel = '36',      # Channel 36 — 5.18 GHz (U-NII-1 band)
    range   = 50,        # Phủ sóng 50 mét
    position= '50,50,0', # Tọa độ (x, y, z) trong mặt phẳng 2D
    failMode= 'standalone'
)

# IoT Station 1
sta1 = net.addStation(
    'sta1',
    ip      = '10.0.0.1/24',
    position= '30,40,0',  # 28.3m từ ap1 — trong range
    range   = 20          # Phạm vi phát của station (ảnh hưởng đến RSSI)
)
```

---

## 4. Cơ chế RF với wmediumd

Mininet-WiFi sử dụng `wmediumd` — daemon kernel-level điều phối medium access giữa các node wireless:

```python
net = Mininet_wifi(
    link         = wmediumd,
    wmediumd_mode= interference   # Bật mô hình nhiễu RF
)
```

**interference mode** tính toán:
- **Path loss** dựa trên khoảng cách giữa các node và model log-distance
- **Signal strength (RSSI)** — `sta1` ở (30,40,0) cách `ap1` ở (50,50,0) ≈ 22.4m
- **SNR** ảnh hưởng đến throughput (link rate thay đổi tự động)
- Nếu station di chuyển ra khỏi `range=50m`, kết nối bị ngắt (disassociation)

---

## 5. Luồng khởi động hệ thống

Khi chạy `sudo python3 5g_iot_mininet.py`:

```
Bước 1: Tạo topology
        create5GIoTTopology()
        → Khởi tạo Mininet_wifi với wmediumd
        → Tạo controller c0 (OpenFlow)
        → Tạo host edge1, AP ap1, switch s1, station sta1/sta2
        → net.configureWifiNodes() — thiết lập wireless interface ảo (wlan0)
        → net.build() + start controllers/switches

Bước 2: Cấu hình routing
        sta1.cmd('ip route add default via 10.0.0.100')
        sta2.cmd('ip route add default via 10.0.0.100')
        → IoT stations định tuyến mọi traffic qua Edge Server

Bước 3: Test connectivity
        testConnectivity()
        → sta1 ping -c3 edge1 (10.0.0.100)
        → sta2 ping -c3 edge1
        → sta1 ping -c3 sta2

Bước 4: Khởi động Edge Server TRONG namespace của edge1
        edge_server.cmd(
          "python3 edge_server_with_dashboard.py model.pkl scaler.pkl ... &"
        )
        → Process bind socket tại 10.0.0.100:5001
        → Gửi metrics ra ngoài namespace đến localhost:5000 (dashboard)

Bước 5: Khởi động IoT Stations TRONG namespace của sta1, sta2
        sta1.cmd("python3 iot_station.py sta1 2 0.2 10.0.0.100 5001 &")
        sta2.cmd("python3 iot_station.py sta2 3 0.15 10.0.0.100 5001 &")
        → TCP packets đi qua wireless link ảo → ap1 → s1 → edge1

Bước 6: Mở Mininet CLI
        → Operator có thể tương tác trực tiếp với từng node
```

---

## 6. Luồng dữ liệu end-to-end

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [sta1 namespace]                                                        │
│  iot_station.py                                                          │
│  generate_sensor_data(anomaly=True/False)                                │
│      → 24 network flow features (Seq, Mean, sTtl, dTtl, TotBytes, ...)  │
│                                                                          │
│  send_data(features)                                                     │
│      → TCP connect(10.0.0.100, 5001)                                    │
│      → JSON: {"device_id":"sta1", "features":[...24...]}                │
└─────────────────┬───────────────────────────────────────────────────────┘
                  │  TCP SYN → kernel → wlan0 (ảo) → wmediumd → ap1
                  │  (đi qua wireless medium, bị ảnh hưởng bởi path loss)
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  [ap1] OVSKernelAP                                                       │
│  Forward frame → s1 (OVS switch) → edge1                                │
└─────────────────┬───────────────────────────────────────────────────────┘
                  │  Wired backhaul (Linux veth pair)
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  [edge1 namespace]                                                       │
│  edge_server_with_dashboard.py                                           │
│                                                                          │
│  handle_client(socket, address)                                          │
│      → Nhận 24 features                                                  │
│      → detect_anomaly(features)                                          │
│            scaler.transform(features_array)                              │
│            model.predict() → "Benign" / "Malicious"                     │
│            model.predict_proba() → probability_malicious                 │
│      → Trích raw features: tot_bytes, tcp_rtt, s_ttl, d_ttl, ...        │
│      → Gửi response về sta1 qua TCP                                     │
│      → dashboard.send_metrics(...)  →  HTTP POST → localhost:5000        │
│         (ra khỏi Mininet namespace, đến host thật)                       │
└─────────────────┬───────────────────────────────────────────────────────┘
                  │  HTTP POST /api/metrics (ra host machine)
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  [Host machine — ngoài Mininet]                                          │
│  dashboard/backend/app.py  :5000                                         │
│      → Nhận: prediction, confidence, probability_malicious, raw features │
│      → anomaly_score = probability_malicious                             │
│      → storage.add_metric() / storage.add_anomaly_event()               │
│      → Frontend poll GET /api/metrics mỗi 2 giây                        │
│      → Browser: http://localhost:5000                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Điểm khác biệt giữa chạy thủ công và qua Mininet

| Khía cạnh | Chạy thủ công (3 terminal) | Qua Mininet-WiFi |
|---|---|---|
| Network isolation | Tất cả dùng chung `localhost` | Mỗi node có network namespace riêng |
| Địa chỉ edge server | `localhost:5001` | `10.0.0.100:5001` (IP thực trong mạng ảo) |
| Wireless | Không có | wmediumd: RF path loss, interference, RSSI |
| IoT station → Edge | Loopback (không qua mạng thật) | TCP đi qua wlan0 ảo → AP → switch → edge |
| Vị trí / di chuyển | Không áp dụng | Station có tọa độ, có thể di chuyển |
| Tắt mạng | Không thể | `net.stop()` dọn dẹp toàn bộ namespace |
| Mininet CLI | Không có | `sta1 ping edge1`, `xterm sta1`, v.v. |

---

## 8. Các lệnh hữu ích trong Mininet CLI

Sau khi `5g_iot_mininet.py` khởi động, Mininet CLI cho phép tương tác trực tiếp:

```bash
# Xem tất cả nodes và links
mininet> nodes
mininet> links
mininet> net

# Kiểm tra kết nối
mininet> sta1 ping -c3 edge1
mininet> sta2 ping -c5 10.0.0.100

# Xem log trực tiếp
mininet> edge1 tail -f /tmp/edge_server.log
mininet> sta1  tail -f /tmp/sta1.log
mininet> sta2  tail -f /tmp/sta2.log

# Mở terminal riêng cho từng node
mininet> xterm sta1
mininet> xterm edge1

# Xem thông tin wireless
mininet> sta1 iw dev sta1-wlan0 info
mininet> sta1 iw dev sta1-wlan0 link    # signal strength, bitrate

# Xem interface và IP
mininet> sta1 ip addr
mininet> edge1 ip addr

# Thêm IoT station thủ công trong CLI
mininet> sta1 python3 iot_station.py sta1_manual 1 0.5 10.0.0.100 5001 &

# Thoát và dọn dẹp mạng
mininet> exit
```

---

## 9. Cấu trúc file liên quan

```
system_detection/
├── 5g_iot_mininet.py           # ← File chính — tạo topology + chạy simulation
│     create5GIoTTopology()     #   Tạo ap1, sta1, sta2, edge1, s1
│     startEdgeServer()         #   Chạy edge_server_with_dashboard.py trong edge1
│     startIoTStation()         #   Chạy iot_station.py trong sta1/sta2
│     testConnectivity()        #   Ping test
│     runSimulation()           #   Entry point
│
├── edge_server_with_dashboard.py   # Chạy trong namespace của edge1
│     host = '0.0.0.0'             # Bind mọi interface trong namespace
│     port = 5001                  # TCP socket lắng nghe
│     dashboard_url = http://localhost:5000  # Ra ngoài namespace → host
│
├── iot_station.py                  # Chạy trong namespace của sta1/sta2
│     edge_ip  = '10.0.0.100'      # IP thực trong mạng Mininet
│     edge_port = 5001
│
├── dashboard_client.py             # Import bởi edge_server
│     dashboard_url → POST /api/metrics lên host:5000
│
├── mn3980_ap1-wlan1.apconf         # Config file được tạo tự động bởi Mininet-WiFi
└── mn4425_ap1-wlan1.apconf         # cho hostapd (AP daemon) — tên thay đổi mỗi lần chạy
```

---

## 10. Cách chạy

### Yêu cầu

```bash
# Mininet-WiFi (cần cài trước)
cd ~
git clone https://github.com/intrig-unicamp/mininet-wifi
cd mininet-wifi
sudo util/install.sh -Wlnfv

# Python packages
sudo apt install -y python3-sklearn python3-joblib python3-flask python3-flask-cors
# hoặc
pip install scikit-learn joblib flask flask-cors numpy
```

### Khởi động

```bash
# Terminal 1 — Dashboard (chạy trên host, NGOÀI Mininet)
cd detection_anomaly/dashboard/backend
python3 app.py

# Terminal 2 — Simulation (cần sudo để tạo network namespaces)
cd detection_anomaly/system_detection
sudo python3 5g_iot_mininet.py
```

> **Lưu ý quan trọng**: `5g_iot_mininet.py` cần `sudo` vì Mininet tạo network namespaces và virtual interfaces ở tầng kernel. Dashboard `app.py` **không** cần sudo và phải chạy trước để Edge Server có thể kết nối ngay khi khởi động.

### Dọn dẹp nếu gặp lỗi

```bash
# Xóa mạng Mininet còn sót lại
sudo mn -c

# Kill process còn zombie
pkill -f iot_station.py
pkill -f edge_server_with_dashboard.py
```

---

## 11. Lý do dashboard chạy ngoài Mininet

Dashboard `app.py` được thiết kế chạy trên **host machine** (không phải trong namespace Mininet) vì:

1. **Browser access**: Browser của người dùng kết nối `localhost:5000` — nếu Flask nằm trong Mininet namespace, browser sẽ không tìm thấy
2. **Dashboard URL**: Edge Server dùng `http://localhost:5000/api/metrics` — `localhost` trong namespace `edge1` trỏ đến `10.0.0.100`, không phải host machine. Tuy nhiên, Mininet-WiFi cho phép namespace giao tiếp với host qua veth pairs mặc định, nên `localhost:5000` từ `edge1` vẫn đến được host
3. **Persistent monitoring**: Dashboard cần tồn tại độc lập với vòng đời của simulation Mininet

---

## 12. Topology mở rộng (có thể phát triển)

Topology hiện tại có thể mở rộng để mô phỏng phức tạp hơn:

```
# Thêm nhiều AP (multi-cell 5G)
ap2 = net.addAccessPoint('ap2', ssid='5G-Cell-2', position='150,50,0')

# Thêm nhiều IoT stations
for i in range(1, 11):
    net.addStation(f'sta{i}', ip=f'10.0.{i//256}.{i%256}/24')

# Di chuyển station (handover simulation)
net.mobility(sta1, 'setPosition', time=5,  position='30,40,0')
net.mobility(sta1, 'setPosition', time=20, position='130,50,0')  # Di chuyển sang cell 2

# Thêm QoS (giới hạn bandwidth để giả lập 5G throughput slice)
net.addLink(ap1, s1, bw=1000, delay='1ms')   # 1 Gbps backhaul
```
