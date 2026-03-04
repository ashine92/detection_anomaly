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
    
    def __init__(self, device_id, edge_ip='10.0.0.100', edge_port=5000):
        self.device_id = device_id
        self.edge_ip = edge_ip
        self.edge_port = edge_port
        
    def generate_sensor_data(self, anomaly=False):
        """
        Tạo dữ liệu cảm biến giả lập với 24 features
        anomaly=True để tạo dữ liệu bất thường
        """
        if anomaly:
            # Dữ liệu bất thường (giả lập tấn công)
            features = [
                random.randint(5000, 10000),  # Seq - cao bất thường
                random.uniform(1000, 2000),    # Mean - cao
                random.randint(0, 255),        # sTos
                random.randint(200, 255),      # sTtl - cao
                random.randint(200, 255),      # dTtl - cao
                random.randint(50, 100),       # sHops - nhiều
                random.randint(100000, 500000),# TotBytes - rất lớn
                random.randint(50000, 250000), # SrcBytes - lớn
                random.randint(0, 10000),      # Offset
                random.randint(1000, 2000),    # sMeanPktSz - lớn
                random.randint(1000, 2000),    # dMeanPktSz - lớn
                random.randint(50000, 65535),  # SrcWin
                random.uniform(100, 500),      # TcpRtt - cao
                random.randint(50000, 100000), # AckDat - lớn
                random.randint(0, 1),          # e
                random.randint(0, 1),          # e d
                random.randint(0, 1),          # icmp
                random.randint(0, 1),          # tcp
                random.randint(0, 1),          # CON
                random.randint(0, 1),          # FIN
                random.randint(0, 1),          # INT
                random.randint(0, 1),          # REQ
                random.randint(0, 1),          # RST
                random.randint(0, 1)           # Status
            ]
        else:
            # Dữ liệu bình thường
            features = [
                random.randint(1, 1000),       # Seq - bình thường
                random.uniform(100, 500),      # Mean
                random.randint(0, 255),        # sTos
                random.randint(64, 128),       # sTtl
                random.randint(64, 128),       # dTtl
                random.randint(1, 10),         # sHops
                random.randint(500, 5000),     # TotBytes
                random.randint(200, 2000),     # SrcBytes
                random.randint(0, 1000),       # Offset
                random.randint(100, 500),      # sMeanPktSz
                random.randint(100, 500),      # dMeanPktSz
                random.randint(1000, 10000),   # SrcWin
                random.uniform(10, 50),        # TcpRtt
                random.randint(1000, 5000),    # AckDat
                random.randint(0, 1),          # e
                random.randint(0, 1),          # e d
                random.randint(0, 1),          # icmp
                1,                             # tcp
                random.randint(0, 1),          # CON
                random.randint(0, 1),          # FIN
                0,                             # INT
                random.randint(0, 1),          # REQ
                0,                             # RST
                random.randint(0, 1)           # Status
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
            
            sock.close()
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    def run(self, interval=2, anomaly_rate=0.1):
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
        print("Usage: python3 iot_station.py <device_id> [interval] [anomaly_rate]")
        print("Example: python3 iot_station.py sta1 2 0.2")
        sys.exit(1)
    
    device_id = sys.argv[1]
    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    anomaly_rate = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1
    
    station = IoTSensorStation(device_id)
    station.run(interval, anomaly_rate)
