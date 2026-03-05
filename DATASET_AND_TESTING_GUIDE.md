# Dataset & Testing Guide — 5G IoT Anomaly Detection

## 1. Ý nghĩa các cột trong Dataset

Dataset ghi lại **network flow** (luồng mạng) từ môi trường IoT/5G. Tổng số bản ghi: **1,215,890 rows × 96 cột**. Model sử dụng **24 features** (`df.iloc[:,0:24]`).

---

### 1.1 Nhóm Thống kê Luồng Mạng (Numeric)

| Cột | Kiểu | Ý nghĩa | Ví dụ |
|---|---|---|---|
| `Seq` | int | Số thứ tự luồng trong dataset | 1, 2, 3 … |
| `Mean` | float | Thời gian trung bình của luồng (giây). Luồng tấn công thường rất ngắn | 4.998, 0.001 |
| `sTos` | float | Source Type of Service — mức ưu tiên QoS của gói nguồn (0–255, DSCP) | 0.0, 10.0 |
| `sTtl` | float | Source TTL — Time-To-Live từ nguồn. Phản ánh số hop tối đa | 117.0, 64.0 |
| `dTtl` | float | Destination TTL — TTL phía đích. NaN = không có phản hồi (đáng ngờ) | 64.0, NaN |
| `sHops` | float | Số hop mạng từ nguồn đến đích | 11.0, 1.0 |
| `TotBytes` | int | Tổng bytes toàn luồng (cả 2 chiều). Scan/flood có giá trị rất nhỏ | 249093, 48 |
| `SrcBytes` | int | Bytes gửi từ phía nguồn | 244212, 48 |
| `Offset` | int | Byte offset của luồng trong file capture | 336, 0 |
| `sMeanPktSz` | float | Kích thước gói trung bình từ nguồn (bytes) | 1245.98, 48.0 |
| `dMeanPktSz` | float | Kích thước gói trung bình từ đích (bytes). 0 = không có reply | 271.17, 0.0 |
| `SrcWin` | float | TCP Window size của nguồn — kiểm soát flow control. NaN = non-TCP | 65535.0, NaN |
| `TcpRtt` | float | TCP Round-Trip Time (giây). Cao = mạng bất thường | 0.042, 0.0 |
| `AckDat` | float | Thời gian từ khi gửi data → nhận ACK (giây) | 0.0, 0.001 |

---

### 1.2 Nhóm Encoded Flags (One-hot 0/1)

Các cột có tên dạng `' e        '` và `' e d      '` là **encoded protocol flags** được tạo ra từ công cụ capture (Argus/NetFlow). Chúng mã hóa loại sự kiện mạng:

| Cột | Ý nghĩa |
|---|---|
| ` e        ` | Flag sự kiện mặc định (normal event) |
| ` e d      ` | Flag sự kiện dạng "data" |

---

### 1.3 Giao thức Mạng (One-hot 0/1)

| Cột | Ý nghĩa |
|---|---|
| `icmp` | 1 nếu luồng dùng ICMP (ping, traceroute, ICMP flood) |
| `tcp` | 1 nếu luồng dùng TCP (HTTP, SSH, TCP scan…) |

---

### 1.4 Trạng thái Kết nối — Connection State (One-hot 0/1)

Đây là nhóm **quan trọng nhất** để phân biệt Benign/Malicious:

| Cột | Ý nghĩa | Dấu hiệu |
|---|---|---|
| `CON` | Kết nối bình thường, đang duy trì (handshake đầy đủ) | **Benign** |
| `FIN` | Kết nối kết thúc sạch (có FIN handshake) | **Benign** |
| `INT` | Luồng nội bộ (bị ngắt trước khi hoàn thành) | Trung tính |
| `REQ` | Chỉ có Request, không có Response — một chiều | **Đáng ngờ** |
| `RST` | Kết nối bị reset đột ngột | **Malicious** |

---

### 1.5 Cột khác

| Cột | Ý nghĩa |
|---|---|
| `Status` | Encoded trạng thái tổng hợp của luồng (dạng số sau encode) |
| `cs0` | DSCP CS0 marking — gói best-effort priority (QoS = 0). 1 = áp dụng |

---

### 1.6 Label (Output)

| Giá trị | Ý nghĩa |
|---|---|
| `Benign` | Lưu lượng bình thường |
| `Malicious` | Tấn công / hành vi bất thường |

---

## 2. Xây dựng mẫu Test cho Hệ thống

### 2.1 Cấu trúc Input → Output

```
[IoT Device] → gửi 24 features (JSON) → [Edge Server / Dashboard API]
                                               ↓ model.predict()
                                         ← trả về prediction + confidence
```

---

### 2.2 Mẫu test — Benign (Lưu lượng bình thường)

**Đặc điểm:** `Mean` lớn, `TotBytes` lớn, kết nối TCP đầy đủ (`CON=1`), có reply (`dMeanPktSz` > 0)

```json
{
  "device_id": "IoT_Camera_01",
  "features": [
    1001,      // Seq
    4.998,     // Mean (giây) — luồng dài
    0.0,       // sTos
    117.0,     // sTtl
    64.0,      // dTtl — có reply từ đích
    11.0,      // sHops
    249093,    // TotBytes — lớn
    244212,    // SrcBytes
    336,       // Offset
    1245.98,   // sMeanPktSz — gói lớn
    271.17,    // dMeanPktSz — có gói reply
    65535.0,   // SrcWin — TCP window bình thường
    0.042,     // TcpRtt
    0.001,     // AckDat
    1.0,       // e (flag mặc định)
    0.0,       // e d
    0.0,       // icmp
    1.0,       // tcp
    1.0,       // CON — kết nối đầy đủ ✓
    0.0,       // FIN
    0.0,       // INT
    0.0,       // REQ
    0.0,       // RST
    1.0        // cs0
  ]
}
```

**Expected Output:**
```json
{
  "prediction": "Benign",
  "confidence": 0.97,
  "probability_benign": 0.97,
  "probability_malicious": 0.03
}
```

---

### 2.3 Mẫu test — Malicious (TCP RST Scan / Port Scan)

**Đặc điểm:** `Mean` cực nhỏ, `TotBytes` nhỏ, `RST=1` + `REQ=1`, không có reply (`dMeanPktSz=0`, `dTtl=0`)

```json
{
  "device_id": "Suspicious_Device_X",
  "features": [
    9999,      // Seq
    0.0001,    // Mean — cực ngắn (scan nhanh)
    0.0,       // sTos
    64.0,      // sTtl
    0.0,       // dTtl — KHÔNG có reply từ đích ⚠
    1.0,       // sHops
    48,        // TotBytes — cực nhỏ ⚠
    48,        // SrcBytes
    0,         // Offset
    48.0,      // sMeanPktSz
    0.0,       // dMeanPktSz — không có gói reply ⚠
    0.0,       // SrcWin
    0.0,       // TcpRtt
    0.0,       // AckDat
    0.0,       // e
    0.0,       // e d
    0.0,       // icmp
    1.0,       // tcp
    0.0,       // CON
    0.0,       // FIN
    0.0,       // INT
    1.0,       // REQ — chỉ request, không có response ⚠
    1.0,       // RST — bị reset ngay ⚠
    0.0        // cs0
  ]
}
```

**Expected Output:**
```json
{
  "prediction": "Malicious",
  "confidence": 0.95,
  "probability_benign": 0.05,
  "probability_malicious": 0.95
}
```

---

### 2.4 Mẫu test — Malicious (ICMP Flood)

**Đặc điểm:** `icmp=1`, `Mean` nhỏ, `TotBytes` nhỏ, không có TCP

```json
{
  "device_id": "Flooder_Device",
  "features": [
    5555,      // Seq
    0.005,     // Mean — nhanh ⚠
    0.0,       // sTos
    64.0,      // sTtl
    0.0,       // dTtl
    2.0,       // sHops
    84,        // TotBytes — nhỏ (ICMP echo = 84 bytes)
    84,        // SrcBytes
    0,         // Offset
    84.0,      // sMeanPktSz
    0.0,       // dMeanPktSz
    0.0,       // SrcWin
    0.0,       // TcpRtt
    0.0,       // AckDat
    0.0,       // e
    0.0,       // e d
    1.0,       // icmp ⚠ — giao thức ICMP
    0.0,       // tcp
    0.0,       // CON
    0.0,       // FIN
    0.0,       // INT
    1.0,       // REQ ⚠
    0.0,       // RST
    0.0        // cs0
  ]
}
```

---

### 2.5 Bảng tóm tắt phân biệt Benign vs Malicious

| Feature | Benign | Malicious |
|---|---|---|
| `Mean` (giây) | > 1.0 | < 0.01 |
| `TotBytes` | Lớn (> 10,000) | Nhỏ (< 200) |
| `dMeanPktSz` | > 0 (có reply) | = 0 (không có reply) |
| `dTtl` | > 0 | = 0 hoặc NaN |
| `CON` hoặc `FIN` | = 1 | = 0 |
| `RST` | = 0 | = 1 |
| `REQ` | = 0 | = 1 (không có response) |
| `TcpRtt` | Có giá trị > 0 | = 0 |

---

## 3. Cách gửi Request để Test

### Dùng Edge Server (port 5000 — TCP socket):
```python
import socket, json

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 5000))

payload = {
    "device_id": "test_device",
    "features": [1001, 4.998, 0.0, 117.0, 64.0, 11.0, 249093, 244212,
                 336, 1245.98, 271.17, 65535.0, 0.042, 0.001,
                 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
}
client.send(json.dumps(payload).encode())
response = json.loads(client.recv(4096).decode())
print(response)
client.close()
```

### Dùng Dashboard API (HTTP):
```bash
curl -X POST http://localhost:5000/api/metrics \
  -H "Content-Type: application/json" \
  -d '{"throughput": 80, "latency": 15, "packet_loss": 0.1, "rssi": -65}'
```

> **Lưu ý:** Dashboard API (detection.py mock mode) dùng 4 metrics đơn giản hóa.  
> Edge Server dùng đầy đủ 24 features từ dataset.
