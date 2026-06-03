#!/usr/bin/python3
"""
IoT Station - Sensor Data Collector & Transmitter
Gửi dữ liệu cảm biến đến Edge Server để phân tích

Mininet-WiFi Integration:
- Tự động phát hiện nếu đang chạy trong Mininet node (qua env MININET_NODE)
- Đọc RSSI thực, bitrate, AP info từ kernel qua lệnh `iw dev`
- Gửi wireless stats kèm theo mỗi request đến Edge Server
"""

import socket
import json
import time
import random
import subprocess
import os
import numpy as np
from datetime import datetime


class MininetWirelessMonitor:
    """
    Đọc thông tin wireless thực tế khi station đang chạy trong Mininet-WiFi node.
    Dùng lệnh `iw dev <interface> link` để lấy RSSI, bitrate, BSSID từ kernel.
    Nếu không trong Mininet (interface không tồn tại), trả về None cho tất cả.
    """

    def __init__(self, device_id: str):
        self.device_id = device_id
        # Env var MININET_NODE được set bởi 5g_iot_mininet.py khi spawn process
        self.mininet_node = os.environ.get('MININET_NODE', None)
        # Wireless interface trong Mininet-WiFi: <node>-wlan0
        self.wlan_iface = f"{device_id}-wlan0"
        self.in_mininet = self._check_mininet()

        if self.in_mininet:
            print(f"[Mininet-WiFi] Node={self.mininet_node}  iface={self.wlan_iface}")
        else:
            print("[Mininet-WiFi] Not running in Mininet — wireless monitor disabled")

    def _check_mininet(self) -> bool:
        """Kiểm tra có interface wireless Mininet không."""
        if self.mininet_node is not None:
            return True
        # Fallback: thử kiểm tra interface có tồn tại không
        try:
            result = subprocess.run(
                ['ip', 'link', 'show', self.wlan_iface],
                capture_output=True, text=True, timeout=1
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_wireless_info(self) -> dict:
        """
        Đọc thông tin wireless từ kernel qua `iw dev <iface> link`.
        Returns dict với các keys:
            signal_dbm       (int|None)  — RSSI, e.g. -52
            link_bitrate_mbps (float|None) — tx bitrate, e.g. 300.0
            ap_bssid         (str|None)  — MAC của AP đang kết nối
            ap_ssid          (str|None)  — SSID (từ env var)
            mininet_node     (str|None)  — tên node Mininet
        """
        info = {
            'signal_dbm': None,
            'link_bitrate_mbps': None,
            'ap_bssid': None,
            'ap_ssid': os.environ.get('MININET_AP_SSID', None),
            'mininet_node': self.mininet_node,
        }

        if not self.in_mininet:
            return info

        try:
            result = subprocess.run(
                ['iw', 'dev', self.wlan_iface, 'link'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode != 0 or 'Not connected' in result.stdout:
                return info

            for line in result.stdout.splitlines():
                line = line.strip()
                # BSSID — first line: "Connected to aa:bb:cc:dd:ee:ff (on ...)"
                if line.startswith('Connected to'):
                    parts = line.split()
                    if len(parts) >= 3:
                        info['ap_bssid'] = parts[2]
                # signal: -52 dBm
                elif line.startswith('signal:'):
                    try:
                        info['signal_dbm'] = int(line.split()[1])
                    except (IndexError, ValueError):
                        pass
                # tx bitrate: 300.0 MBit/s ...
                elif line.startswith('tx bitrate:'):
                    try:
                        info['link_bitrate_mbps'] = float(line.split()[2])
                    except (IndexError, ValueError):
                        pass
        except Exception:
            pass

        return info


class IoTSensorStation:
    """IoT Station thu thập và gửi dữ liệu cảm biến"""

    def __init__(self, device_id, edge_ip='localhost', edge_port=5001):
        self.device_id = device_id
        self.edge_ip = edge_ip
        self.edge_port = edge_port
        # Mininet wireless monitor — hoạt động như stub nếu không trong Mininet
        self.wireless = MininetWirelessMonitor(device_id)
        
    def generate_sensor_data(self, anomaly=False):
        """
        Tạo dữ liệu cảm biến giả lập với 24 features
        ĐÚNG THỨ TỰ theo model training:
        ['Seq', 'Mean', 'sTos', 'sTtl', 'dTtl', 'sHops', 'TotBytes', 'SrcBytes', 
         'Offset', 'sMeanPktSz', 'dMeanPktSz', 'SrcWin', 'TcpRtt', 'AckDat', 
         ' e        ', ' e d      ', 'icmp', 'tcp', 'CON', 'FIN', 'INT', 'REQ', 
         'RST', 'Status']
        
        anomaly=True để tạo dữ liệu bất thường
        """
        if anomaly:
            # Chọn ngẫu nhiên một trong 2 kiểu tấn công thực tế từ dataset
            attack_type = random.choice(['icmp_scan', 'tcp_rst_scan'])

            if attack_type == 'icmp_scan':
                # ICMP Scanning Attack — calibrated to real dataset malicious rows
                # Verified samples: Seq=35-39, Mean=0.002-1.88, sTtl=45-49, dTtl=0,
                # sHops=15-19, TotBytes=84-108, Offset=4600-4992, sMeanPktSz=42-54, icmp=1
                pkt = random.choice([42, 54])
                features = [
                    float(random.randint(30, 50)),    # [0] Seq - thấp (35-39 trong dataset)
                    random.uniform(0.001, 2.0),      # [1] Mean - rất thấp (≤2.0)
                    0.0,                              # [2] sTos - 0
                    float(random.randint(44, 52)),    # [3] sTtl - 45-49 (spoofed)
                    0.0,                              # [4] dTtl - 0 (không có reply — đặc trưng chính!)
                    float(random.randint(13, 20)),    # [5] sHops - 15-19
                    float(pkt * 2),                  # [6] TotBytes - nhỏ (84-108)
                    float(pkt * 2),                  # [7] SrcBytes = TotBytes (1 chiều)
                    float(random.randint(4500, 5200)),# [8] Offset - cao (4600-4992)
                    float(pkt),                      # [9] sMeanPktSz - 42-54
                    0.0,                              # [10] dMeanPktSz - 0 (no dest reply)
                    0.0,                              # [11] SrcWin - 0
                    0.0,                              # [12] TcpRtt - 0
                    0.0,                              # [13] AckDat - 0
                    1,                                # [14] ' e        ' - set
                    0,                                # [15] ' e d      '
                    1,                                # [16] icmp - ICMP!
                    0,                                # [17] tcp
                    0,                                # [18] CON
                    0,                                # [19] FIN
                    0,                                # [20] INT
                    0,                                # [21] REQ
                    0,                                # [22] RST
                    0                                 # [23] Status
                ]
            else:
                # TCP RST Scan Attack — calibrated to real dataset malicious rows
                # Verified: Seq=40, Mean=0.002, sTtl=50, dTtl=59, sHops=14,
                # TotBytes=112, SrcBytes=58, Offset=5084, SrcWin=1024, tcp=1, RST=1
                src_pkt = random.choice([54, 58])
                dst_pkt = random.choice([54, 58])
                features = [
                    float(random.randint(35, 50)),    # [0] Seq - 35-40
                    random.uniform(0.001, 0.004),     # [1] Mean - cực thấp (~0.002)
                    0.0,                              # [2] sTos
                    float(random.randint(47, 53)),    # [3] sTtl - ~50
                    float(random.randint(59, 61)),    # [4] dTtl - ~59 (đặc trưng)
                    float(random.randint(12, 17)),    # [5] sHops - ~14
                    float(src_pkt + dst_pkt + 2),     # [6] TotBytes - nhỏ (~112)
                    float(src_pkt),                   # [7] SrcBytes - ~58
                    float(random.randint(4900, 5200)),# [8] Offset - ~5084
                    float(src_pkt),                   # [9] sMeanPktSz - ~58
                    float(dst_pkt),                   # [10] dMeanPktSz - ~54
                    1024.0,                           # [11] SrcWin - 1024 (đặc trưng TCP RST scan)
                    0.0,                              # [12] TcpRtt - ~0
                    0.0,                              # [13] AckDat - ~0
                    1,                                # [14] ' e        ' - set
                    0,                                # [15] ' e d      '
                    0,                                # [16] icmp
                    1,                                # [17] tcp - TCP!
                    0,                                # [18] CON
                    0,                                # [19] FIN
                    0,                                # [20] INT
                    0,                                # [21] REQ
                    1,                                # [22] RST - RESET!
                    0                                 # [23] Status
                ]
        else:
            # NORMAL TRAFFIC — calibrated to real dataset benign rows
            # Key benign traits: Mean≤5, TcpRtt≈0, AckDat≈0, high sTtl (≥60),
            # Offset varies widely, SrcWin often 0
            tot = random.randint(500, 6000)
            src = random.randint(tot // 2, tot)
            features = [
                float(random.randint(1, 100000)),      # [0] Seq - bình thường
                random.uniform(0.0, 3.0),              # [1] Mean - thấp (≤3 p95 benign)
                0.0,                                   # [2] sTos - 0 (mostly)
                float(random.randint(55, 250)),        # [3] sTtl - cao (bình thường ≥60)
                float(random.choice([0, 64])),         # [4] dTtl - 0 hoặc 64
                float(random.randint(1, 8)),           # [5] sHops - ít hops
                float(tot),                            # [6] TotBytes
                float(src),                            # [7] SrcBytes
                float(random.randint(128, 1000000)),   # [8] Offset - rộng (benign lớn)
                float(random.randint(40, 200)),        # [9] sMeanPktSz - p95=245
                float(random.randint(0, 100)),         # [10] dMeanPktSz
                0.0,                                   # [11] SrcWin - p95=0 trong benign
                0.0,                                   # [12] TcpRtt - ~0 (p95=0)
                0.0,                                   # [13] AckDat - ~0 (p95=0)
                1,                                     # [14] ' e        ' - set (72% benign)
                0,                                     # [15] ' e d      '
                0,                                     # [16] icmp
                0,                                     # [17] tcp
                0,                                     # [18] CON
                0,                                     # [19] FIN
                random.choice([0, 1]),                 # [20] INT
                random.choice([0, 1]),                 # [21] REQ
                0,                                     # [22] RST - hiếm trong benign
                random.choice([0, 1])                  # [23] Status
            ]
        
        return features
    
    def send_data(self, features):
        """Gửi dữ liệu đến Edge Server, kèm wireless info nếu trong Mininet."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.edge_ip, self.edge_port))

            # Đọc wireless info từ kernel (nếu có)
            winfo = self.wireless.get_wireless_info()

            request = {
                'device_id': self.device_id,
                'features':  features,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                # Mininet-WiFi context — None nếu không trong Mininet
                'wireless': {
                    'mininet_node':      winfo['mininet_node'],
                    'ap_ssid':           winfo['ap_ssid'],
                    'ap_bssid':          winfo['ap_bssid'],
                    'signal_dbm':        winfo['signal_dbm'],
                    'link_bitrate_mbps': winfo['link_bitrate_mbps'],
                }
            }

            sock.send(json.dumps(request).encode())
            response = sock.recv(4096).decode()
            result = json.loads(response)
            sock.close()
            return result

        except Exception as e:
            return {'error': str(e)}
    
    def run(self, interval=2, anomaly_rate=0.2, paused=False):
        """
        Chạy station - gửi dữ liệu hoặc pause
        interval: giây giữa mỗi lần gửi
        anomaly_rate: tỷ lệ tạo dữ liệu bất thường (0-1)
        paused: bắt đầu ở trạng thái paused
        
        DEMO CONTROL:
        - File trigger: /tmp/{device_id}_running
        - Tạo file để bắt đầu: touch /tmp/{device_id}_running
        - Xóa file để dừng:    rm /tmp/{device_id}_running
        """
        print("="*70)
        print(f"IoT SENSOR STATION: {self.device_id}")
        print("="*70)
        print(f"Edge Server: {self.edge_ip}:{self.edge_port}")
        print(f"Sending interval: {interval} seconds")
        print(f"Anomaly rate: {anomaly_rate*100}%")
        print(f"Status: {'⏸️  PAUSED (waiting for trigger)' if paused else '▶️  RUNNING'}")
        print()
        print("DEMO CONTROL (from Mininet CLI):")
        print(f"  To START:   sta1 touch /tmp/{self.device_id}_running")
        print(f"  To STOP:    sta1 rm /tmp/{self.device_id}_running")
        print("="*70)
        print()
        
        control_file = f'/tmp/{self.device_id}_running'
        packet_count = 0
        is_running = not paused
        
        # Nếu bắt đầu ở paused, xóa file control
        if paused and os.path.exists(control_file):
            os.remove(control_file)
        
        try:
            while True:
                # Kiểm tra file trigger để pause/resume
                file_exists = os.path.exists(control_file)
                
                if file_exists != is_running:
                    is_running = file_exists
                    if is_running:
                        print(f"[{datetime.now()}] ▶️  RESUMED - Starting to send data")
                    else:
                        print(f"[{datetime.now()}] ⏸️  PAUSED - Waiting for trigger file")
                
                if is_running:
                    packet_count += 1
                    
                    # Quyết định gửi dữ liệu bình thường hay bất thường
                    is_anomaly = random.random() < anomaly_rate
                    features = self.generate_sensor_data(anomaly=is_anomaly)
                    
                    print(f"[{datetime.now()}] Packet #{packet_count} - ", end='')
                    if is_anomaly:
                        print("⚠️  ANOMALY DATA", end=' ')
                    else:
                        print("✓ NORMAL DATA", end=' ')
                    
                    # Gửi dữ liệu
                    result = self.send_data(features)
                    
                    if 'error' in result:
                        print(f"→ ERROR: {result['error']}")
                    else:
                        pred = result['prediction']
                        conf = result['confidence']
                        winfo = result.get('wireless_echo', {})
                        sig = winfo.get('signal_dbm')
                        sig_str = f"  sig={sig}dBm" if sig is not None else ""
                        print(f"→ Edge: {pred} ({conf*100:.1f}%){sig_str}")
                    
                    time.sleep(interval)
                else:
                    # Pause mode - chỉ check file
                    time.sleep(0.5)
                
        except KeyboardInterrupt:
            print(f"\n\nStation stopped. Total packets sent: {packet_count}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 iot_station.py <device_id> [interval] [anomaly_rate] [edge_ip] [edge_port] [--paused]")
        print("\nExamples:")
        print("  python3 iot_station.py sta1")
        print("  python3 iot_station.py sta1 2 0.2")
        print("  python3 iot_station.py sta1 2 0.2 localhost 5001")
        print("  python3 iot_station.py sta1 2 0.2 10.0.0.100 5001  # For Mininet")
        print("  python3 iot_station.py sta1 2 0.2 10.0.0.100 5001 --paused  # Demo mode (paused)")
        print("\nDefaults:")
        print("  interval: 2.0 seconds")
        print("  anomaly_rate: 0.1 (10%)")
        print("  edge_ip: localhost")
        print("  edge_port: 5001")
        print("  paused: False (start running immediately)")
        print("\nDEMO CONTROL (file-based):")
        print("  To START:   touch /tmp/{device_id}_running")
        print("  To STOP:    rm /tmp/{device_id}_running")
        sys.exit(1)
    
    device_id = sys.argv[1]
    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    anomaly_rate = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2
    edge_ip = sys.argv[4] if len(sys.argv) > 4 else 'localhost'
    edge_port = int(sys.argv[5]) if len(sys.argv) > 5 else 5001
    paused = '--paused' in sys.argv
    
    station = IoTSensorStation(device_id, edge_ip=edge_ip, edge_port=edge_port)
    station.run(interval, anomaly_rate, paused=paused)
