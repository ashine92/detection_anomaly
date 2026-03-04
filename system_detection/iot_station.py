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
            # ATTACK TRAFFIC - DDoS/Flooding patterns
            # Đặc điểm: High throughput, nhiều packets, high rate, abnormal flags
            features = [
                random.randint(50000, 100000),    # [0] Seq - rất cao (flood)
                random.uniform(2000, 5000),       # [1] Mean - cao bất thường
                random.choice([0, 8, 16]),        # [2] sTos - abnormal priority
                random.randint(30, 50),           # [3] sTtl - TTL thấp (spoofed)
                random.randint(30, 50),           # [4] dTtl - TTL thấp
                random.randint(15, 30),           # [5] sHops - nhiều hops
                random.randint(500000, 2000000),  # [6] TotBytes - RẤT LỚN
                random.randint(250000, 1000000),  # [7] SrcBytes - rất lớn
                random.randint(0, 100),           # [8] Offset
                random.randint(1200, 1500),       # [9] sMeanPktSz - max packet size
                random.randint(1200, 1500),       # [10] dMeanPktSz
                random.randint(50000, 65535),     # [11] SrcWin - maximum window
                random.uniform(150, 500),         # [12] TcpRtt - latency cao
                random.randint(100000, 500000),   # [13] AckDat - lớn
                0,                                # [14] ' e        ' - flag
                1,                                # [15] ' e d      ' - flag set
                0,                                # [16] icmp - not ICMP
                1,                                # [17] tcp - TCP protocol
                1,                                # [18] CON - connection flag
                0,                                # [19] FIN - no FIN (incomplete)
                1,                                # [20] INT - interrupt flag
                1,                                # [21] REQ - request flag
                1,                                # [22] RST - RESET flag (attack!)
                1                                 # [23] Status - active
            ]
        else:
            # NORMAL TRAFFIC - Realistic IoT sensor communication
            # Đặc điểm: Low/moderate traffic, normal TTL, complete connections
            features = [
                random.randint(1, 10000),         # [0] Seq - bình thường
                random.uniform(100, 800),         # [1] Mean - moderate
                0,                                # [2] sTos - normal priority
                random.randint(60, 128),          # [3] sTtl - normal TTL
                random.randint(60, 128),          # [4] dTtl - normal TTL
                random.randint(1, 8),             # [5] sHops - ít hops
                random.randint(1000, 50000),      # [6] TotBytes - moderate
                random.randint(500, 25000),       # [7] SrcBytes - moderate
                random.randint(0, 100),           # [8] Offset
                random.randint(200, 800),         # [9] sMeanPktSz - normal size
                random.randint(200, 800),         # [10] dMeanPktSz
                random.randint(5000, 32000),      # [11] SrcWin - normal window
                random.uniform(5, 80),            # [12] TcpRtt - latency thấp
                random.randint(1000, 10000),      # [13] AckDat - moderate
                1,                                # [14] ' e        ' - flag
                0,                                # [15] ' e d      ' - flag
                0,                                # [16] icmp - not ICMP
                1,                                # [17] tcp - TCP protocol
                1,                                # [18] CON - connection established
                1,                                # [19] FIN - clean close
                0,                                # [20] INT - no interrupt
                1,                                # [21] REQ - normal request
                0,                                # [22] RST - no reset (normal)
                1                                 # [23] Status - active
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
            print(f"Received from edge: {result}")
            sock.close()
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    def run(self, interval=2, anomaly_rate=0.8):
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
    anomaly_rate = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8
    edge_ip = sys.argv[4] if len(sys.argv) > 4 else 'localhost'
    edge_port = int(sys.argv[5]) if len(sys.argv) > 5 else 5001
    
    station = IoTSensorStation(device_id, edge_ip=edge_ip, edge_port=edge_port)
    station.run(interval, anomaly_rate)
