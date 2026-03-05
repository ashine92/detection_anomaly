#!/usr/bin/python3
"""
IoT Station - Sensor Data Collector & Transmitter
Gửi dữ liệu cảm biến đến Edge Server để phân tích
"""

import socket
import json
import time
import random
import numpy as np
from datetime import datetime

class IoTSensorStation:
    """IoT Station thu thập và gửi dữ liệu cảm biến"""
    
    def __init__(self, device_id, edge_ip='localhost', edge_port=5001):
        self.device_id = device_id
        self.edge_ip = edge_ip
        self.edge_port = edge_port
        
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
        """Gửi dữ liệu đến Edge Server"""
        try:
            # Tạo socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            # Kết nối đến Edge Server
            sock.connect((self.edge_ip, self.edge_port))
            
            # Tạo request
            request = {
                'device_id': self.device_id,
                'features': features,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Gửi dữ liệu
            sock.send(json.dumps(request).encode())
            
            # Nhận kết quả
            response = sock.recv(4096).decode()
            result = json.loads(response)
            # print(f"\nReceived from edge: {result}")
            sock.close()
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    def run(self, interval=2, anomaly_rate=0.2):
        """
        Chạy station - liên tục gửi dữ liệu
        interval: giây giữa mỗi lần gửi
        anomaly_rate: tỷ lệ tạo dữ liệu bất thường (0-1)
        """
        print("="*70)
        print(f"IoT SENSOR STATION: {self.device_id}")
        print("="*70)
        print(f"Edge Server: {self.edge_ip}:{self.edge_port}")
        print(f"Sending data every {interval} seconds")
        print(f"Anomaly rate: {anomaly_rate*100}%")
        print("="*70)
        print()
        
        packet_count = 0
        
        try:
            while True:
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
                    print(f"→ Edge: {pred} ({conf*100:.1f}%)")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\nStation stopped. Total packets sent: {packet_count}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 iot_station.py <device_id> [interval] [anomaly_rate] [edge_ip] [edge_port]")
        print("\nExamples:")
        print("  python3 iot_station.py sta1")
        print("  python3 iot_station.py sta1 2 0.2")
        print("  python3 iot_station.py sta1 2 0.2 localhost 5001")
        print("  python3 iot_station.py sta1 2 0.2 10.0.0.100 5001  # For Mininet")
        print("\nDefaults:")
        print("  interval: 2.0 seconds")
        print("  anomaly_rate: 0.1 (10%)")
        print("  edge_ip: localhost")
        print("  edge_port: 5001")
        sys.exit(1)
    
    device_id = sys.argv[1]
    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    anomaly_rate = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2
    edge_ip = sys.argv[4] if len(sys.argv) > 4 else 'localhost'
    edge_port = int(sys.argv[5]) if len(sys.argv) > 5 else 5001
    
    station = IoTSensorStation(device_id, edge_ip=edge_ip, edge_port=edge_port)
    station.run(interval, anomaly_rate)
