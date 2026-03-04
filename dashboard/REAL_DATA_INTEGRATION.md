# 🔌 HƯỚNG DẪN GỬI DỮ LIỆU THẬT TỪ SIMULATION

## 📋 Tổng Quan

Bạn có 2 hệ thống:
1. **System Detection**: IoT Stations + Edge Server (detection với 24 features)
2. **Dashboard**: Monitoring system (cần 4 metrics: throughput, latency, packet_loss, rssi)

Để tích hợp, bạn cần **collect network metrics** từ Mininet và gửi đến dashboard.

---

## 🎯 OPTION 1: Tích Hợp Trực Tiếp với Edge Server

### Bước 1: Thêm Dashboard Client vào Edge Server

Tạo file `dashboard_client.py` trong `system_detection/`:

```python
#!/usr/bin/python3
"""
Dashboard Client - Gửi metrics đến monitoring dashboard
"""

import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DashboardClient:
    """Client để gửi network metrics đến dashboard"""
    
    def __init__(self, dashboard_url='http://localhost:5000/api/metrics'):
        self.dashboard_url = dashboard_url
        self.enabled = True
        
        # Test connection
        try:
            health_url = dashboard_url.replace('/api/metrics', '/health')
            response = requests.get(health_url, timeout=1)
            if response.status_code == 200:
                logger.info("✓ Dashboard connection successful")
            else:
                logger.warning("⚠ Dashboard not responding")
                self.enabled = False
        except:
            logger.warning("⚠ Dashboard not available - metrics won't be sent")
            self.enabled = False
    
    def send_metrics(self, device_id, throughput, latency, packet_loss, rssi):
        """
        Gửi network metrics đến dashboard để AI phân tích
        
        Args:
            device_id (str): ID thiết bị
            throughput (float): Throughput (Mbps)
            latency (float): Latency (ms)
            packet_loss (float): Packet loss (%)
            rssi (float): Signal strength (dBm)
        """
        if not self.enabled:
            return False
        
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "device_id": device_id,
                "throughput": float(throughput),
                "latency": float(latency),
                "packet_loss": float(packet_loss),
                "rssi": float(rssi)
            }
            
            response = requests.post(
                self.dashboard_url,
                json=data,
                timeout=1
            )
            
            if response.status_code == 200:
                result = response.json()
                detection = result.get('detection', {})
                
                # Log nếu phát hiện anomaly
                if detection.get('is_anomaly'):
                    logger.warning(
                        f"🚨 Dashboard AI detected anomaly for {device_id}: "
                        f"Score={detection['anomaly_score']:.3f}, "
                        f"Severity={detection['severity']}"
                    )
                
                return True
            else:
                logger.error(f"✗ Dashboard error: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Error sending to dashboard: {e}")
            return False
    
    def send_batch(self, metrics_list):
        """Gửi nhiều metrics cùng lúc"""
        for metrics in metrics_list:
            self.send_metrics(**metrics)
```

### Bước 2: Sửa Edge Server để Collect Network Metrics

Tạo file `edge_server_with_dashboard.py`:

```python
#!/usr/bin/python3
"""
Edge Server với Dashboard Integration
Phát hiện anomaly VÀ gửi network metrics đến dashboard
"""

import socket
import joblib
import numpy as np
import json
from datetime import datetime
import threading
import logging
import time

# Import dashboard client
from dashboard_client import DashboardClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EdgeIoTDetectionServerWithDashboard:
    """Edge Server với dashboard monitoring"""
    
    def __init__(self, model_path, scaler_path, host='0.0.0.0', port=5000,
                 dashboard_url='http://localhost:5000/api/metrics'):
        self.host = host
        self.port = port
        
        # Load ML model (24 features)
        logger.info("Loading ML model...")
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        logger.info("✓ Model loaded successfully!")
        
        # Initialize dashboard client
        self.dashboard = DashboardClient(dashboard_url)
        
        # Statistics
        self.total_requests = 0
        self.benign_count = 0
        self.malicious_count = 0
        
        # Network metrics tracking (per device)
        self.device_metrics = {}
        
    def calculate_network_metrics(self, device_id, features, request_time):
        """
        Tính toán network metrics từ features và timing
        
        Features có sẵn:
        - TotBytes (index 6): Total bytes → dùng để tính throughput
        - TcpRtt (index 12): TCP Round Trip Time → latency
        - Có thể estimate packet loss từ các flag
        """
        try:
            # Extract relevant features
            tot_bytes = features[6]  # TotBytes
            tcp_rtt = features[12]   # TcpRtt (ms)
            src_bytes = features[7]  # SrcBytes
            
            # Calculate throughput (Mbps)
            # Giả sử mỗi request là 1 second interval
            if device_id not in self.device_metrics:
                self.device_metrics[device_id] = {
                    'last_bytes': tot_bytes,
                    'last_time': request_time
                }
                # First request - use default
                throughput = (tot_bytes * 8) / (1024 * 1024)  # Convert to Mbps
            else:
                prev = self.device_metrics[device_id]
                time_diff = request_time - prev['last_time']
                bytes_diff = tot_bytes - prev['last_bytes']
                
                if time_diff > 0:
                    throughput = (bytes_diff * 8) / (1024 * 1024 * time_diff)
                else:
                    throughput = 0
                
                # Update tracking
                self.device_metrics[device_id] = {
                    'last_bytes': tot_bytes,
                    'last_time': request_time
                }
            
            # Latency (từ TCP RTT)
            latency = tcp_rtt
            
            # Estimate packet loss (từ retransmission flags)
            # RST flag (index 22) và các flags khác
            rst_flag = features[22]
            packet_loss = 5.0 if rst_flag == 1 else np.random.uniform(0, 2)
            
            # Estimate RSSI (signal strength)
            # Dựa vào số hops và TTL
            s_hops = features[5]  # sHops
            # Nhiều hops → tín hiệu yếu hơn
            rssi = -50 - (s_hops * 2) + np.random.uniform(-5, 5)
            rssi = max(-90, min(-40, rssi))  # Giới hạn -90 đến -40 dBm
            
            return {
                'throughput': round(throughput, 2),
                'latency': round(latency, 2),
                'packet_loss': round(packet_loss, 2),
                'rssi': round(rssi, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            # Return default values
            return {
                'throughput': 50.0,
                'latency': 20.0,
                'packet_loss': 0.5,
                'rssi': -65.0
            }
    
    def detect_anomaly(self, features):
        """Phát hiện anomaly từ 24 features"""
        features_array = np.array(features).reshape(1, -1)
        features_scaled = self.scaler.transform(features_array)
        
        prediction = self.model.predict(features_scaled)[0]
        probability = self.model.predict_proba(features_scaled)[0]
        confidence = np.max(probability)
        
        return {
            'prediction': prediction,
            'confidence': float(confidence),
            'probability_benign': float(probability[0]),
            'probability_malicious': float(probability[1]),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def handle_client(self, client_socket, address):
        """Xử lý request từ IoT device"""
        request_time = time.time()
        
        try:
            # Nhận dữ liệu
            data = client_socket.recv(4096).decode()
            request = json.loads(data)
            
            device_id = request.get('device_id', 'unknown')
            features = request.get('features', [])
            
            logger.info(f"Request from {device_id} ({address[0]})")
            
            # 1. Phát hiện anomaly (24 features)
            result = self.detect_anomaly(features)
            result['device_id'] = device_id
            
            # 2. Calculate network metrics
            network_metrics = self.calculate_network_metrics(
                device_id, features, request_time
            )
            
            # 3. Send to dashboard
            self.dashboard.send_metrics(
                device_id=device_id,
                throughput=network_metrics['throughput'],
                latency=network_metrics['latency'],
                packet_loss=network_metrics['packet_loss'],
                rssi=network_metrics['rssi']
            )
            
            # Update statistics
            self.total_requests += 1
            if result['prediction'] == 'Benign':
                self.benign_count += 1
            else:
                self.malicious_count += 1
                logger.warning(f"⚠️ ALERT: Malicious activity from {device_id}!")
            
            # Send response
            response = json.dumps(result)
            client_socket.send(response.encode())
            
            logger.info(
                f"→ Prediction: {result['prediction']} "
                f"(Conf: {result['confidence']*100:.2f}%) | "
                f"Metrics: {network_metrics['throughput']:.1f} Mbps, "
                f"{network_metrics['latency']:.1f} ms"
            )
            
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            client_socket.close()
    
    def start(self):
        """Khởi động server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        
        logger.info("="*60)
        logger.info("Edge IoT Detection Server WITH DASHBOARD")
        logger.info("="*60)
        logger.info(f"Server listening on {self.host}:{self.port}")
        logger.info(f"Dashboard integration: {'✓ Enabled' if self.dashboard.enabled else '✗ Disabled'}")
        logger.info("="*60)
        
        try:
            while True:
                client_socket, address = server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.start()
                
        except KeyboardInterrupt:
            logger.info("\nShutting down server...")
            logger.info(f"Total requests: {self.total_requests}")
            logger.info(f"Benign: {self.benign_count} | Malicious: {self.malicious_count}")
        finally:
            server_socket.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python edge_server_with_dashboard.py <model_path> <scaler_path>")
        print("Example: python edge_server_with_dashboard.py ../model/decision_tree_model.pkl ../model/scaler.pkl")
        sys.exit(1)
    
    model_path = sys.argv[1]
    scaler_path = sys.argv[2]
    
    # Dashboard URL (có thể config)
    dashboard_url = "http://localhost:5000/api/metrics"
    
    server = EdgeIoTDetectionServerWithDashboard(
        model_path=model_path,
        scaler_path=scaler_path,
        dashboard_url=dashboard_url
    )
    
    server.start()
```

---

## 🚀 OPTION 2: Collect Metrics Trực Tiếp từ Mininet

Nếu bạn muốn lấy metrics thực từ Mininet (chính xác hơn):

### Bước 1: Thêm Network Monitor vào Mininet Script

Tạo file `mininet_network_monitor.py`:

```python
#!/usr/bin/python3
"""
Mininet Network Monitor - Thu thật metrics từ Mininet
"""

import time
import requests
from datetime import datetime
import subprocess
import re


class MininetNetworkMonitor:
    """Monitor network metrics từ Mininet nodes"""
    
    def __init__(self, dashboard_url='http://localhost:5000/api/metrics'):
        self.dashboard_url = dashboard_url
    
    def get_interface_stats(self, node, interface='wlan0'):
        """Lấy stats từ network interface"""
        try:
            # Get RX/TX bytes
            cmd = f"ifconfig {interface}"
            result = node.cmd(cmd)
            
            # Parse RX bytes và TX bytes
            rx_match = re.search(r'RX packets.*?bytes (\d+)', result)
            tx_match = re.search(r'TX packets.*?bytes (\d+)', result)
            
            rx_bytes = int(rx_match.group(1)) if rx_match else 0
            tx_bytes = int(tx_match.group(1)) if tx_match else 0
            
            return rx_bytes, tx_bytes
        except:
            return 0, 0
    
    def measure_latency(self, node, target_ip):
        """Đo latency bằng ping"""
        try:
            result = node.cmd(f'ping -c 1 -W 1 {target_ip}')
            match = re.search(r'time=([\d.]+) ms', result)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0.0
    
    def measure_throughput(self, node, interface='wlan0', interval=1.0):
        """Đo throughput thực"""
        rx1, tx1 = self.get_interface_stats(node, interface)
        time.sleep(interval)
        rx2, tx2 = self.get_interface_stats(node, interface)
        
        # Calculate throughput (Mbps)
        rx_throughput = ((rx2 - rx1) * 8) / (1024 * 1024 * interval)
        tx_throughput = ((tx2 - tx1) * 8) / (1024 * 1024 * interval)
        
        # Return average
        return (rx_throughput + tx_throughput) / 2
    
    def get_signal_strength(self, node, interface='wlan0'):
        """Lấy RSSI từ WiFi interface"""
        try:
            result = node.cmd(f'iwconfig {interface}')
            match = re.search(r'Signal level[=:](-?\d+)', result)
            if match:
                return float(match.group(1))
        except:
            pass
        return -65.0  # Default
    
    def monitor_node(self, node, device_id, target_ip, interval=2.0):
        """
        Monitor một node và gửi metrics đến dashboard
        
        Args:
            node: Mininet node object
            device_id: Device identifier
            target_ip: IP để ping test
            interval: Monitoring interval (seconds)
        """
        print(f"[{datetime.now()}] Starting monitor for {device_id}")
        
        try:
            while True:
                # Collect metrics
                throughput = self.measure_throughput(node)
                latency = self.measure_latency(node, target_ip)
                rssi = self.get_signal_strength(node)
                
                # Estimate packet loss (có thể improve)
                # Ping 10 packets và đếm loss
                ping_result = node.cmd(f'ping -c 10 -W 1 {target_ip}')
                loss_match = re.search(r'(\d+)% packet loss', ping_result)
                packet_loss = float(loss_match.group(1)) if loss_match else 0.0
                
                # Send to dashboard
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "device_id": device_id,
                    "throughput": round(throughput, 2),
                    "latency": round(latency, 2),
                    "packet_loss": round(packet_loss, 2),
                    "rssi": round(rssi, 2)
                }
                
                try:
                    response = requests.post(
                        self.dashboard_url,
                        json=data,
                        timeout=1
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        detection = result.get('detection', {})
                        
                        status = "🔴 ANOMALY" if detection.get('is_anomaly') else "🟢 NORMAL"
                        print(f"[{device_id}] {status} | "
                              f"T:{throughput:.1f}Mbps L:{latency:.1f}ms "
                              f"P:{packet_loss:.1f}% R:{rssi:.0f}dBm")
                    
                except Exception as e:
                    print(f"[{device_id}] Dashboard error: {e}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n[{device_id}] Monitor stopped")


# Usage example trong Mininet script
def monitor_iot_stations(net, station_names, edge_ip, dashboard_url):
    """
    Thêm vào Mininet script để monitor các stations
    
    Example:
        from mininet_network_monitor import MininetNetworkMonitor, monitor_iot_stations
        
        # Sau khi khởi tạo network
        monitor_iot_stations(
            net=net,
            station_names=['sta1', 'sta2', 'sta3'],
            edge_ip='10.0.0.100',
            dashboard_url='http://localhost:5000/api/metrics'
        )
    """
    import threading
    
    monitor = MininetNetworkMonitor(dashboard_url)
    threads = []
    
    for sta_name in station_names:
        station = net.get(sta_name)
        device_id = f"IoT_Station_{sta_name}"
        
        thread = threading.Thread(
            target=monitor.monitor_node,
            args=(station, device_id, edge_ip),
            daemon=True
        )
        thread.start()
        threads.append(thread)
    
    return threads
```

### Bước 2: Sửa Mininet Script

Trong file `5g_iot_mininet.py`, thêm:

```python
from mininet_network_monitor import monitor_iot_stations

# ... (code khởi tạo network)

# Sau khi network start
print("Starting network monitoring...")
monitor_threads = monitor_iot_stations(
    net=net,
    station_names=['sta1', 'sta2', 'sta3'],
    edge_ip='10.0.0.100',  # Edge server IP
    dashboard_url='http://localhost:5000/api/metrics'  # Dashboard URL
)

# Keep running
CLI(net)

# Cleanup
net.stop()
```

---

## 📝 CÁCH CHẠY

### Setup 1: Dashboard + Edge Server Integrated

```bash
# Terminal 1: Start Dashboard
cd dashboard/backend
python app.py

# Terminal 2: Start Edge Server với Dashboard
cd system_detection
python edge_server_with_dashboard.py ../model/decision_tree_model*.pkl ../model/scaler*.pkl

# Terminal 3: Run IoT Stations
python iot_station.py
```

### Setup 2: Dashboard + Mininet Monitor

```bash
# Terminal 1: Start Dashboard
cd dashboard/backend
python app.py

# Terminal 2: Run Mininet với Monitor
sudo python 5g_iot_mininet.py

# Mininet sẽ tự động gửi metrics đến dashboard
```

---

## 🎯 WHICH OPTION TO CHOOSE?

**Option 1 (Edge Server Integration)**:
- ✅ Dễ implement
- ✅ Không cần modify Mininet
- ⚠️ Metrics được estimate từ features

**Option 2 (Mininet Monitor)**:
- ✅ Metrics chính xác từ network
- ✅ Real WiFi signal strength
- ⚠️ Cần modify Mininet script
- ⚠️ Tốn resource hơn (ping tests)

**Khuyến nghị**: Bắt đầu với **Option 1** (dễ hơn), sau đó improve với **Option 2** nếu cần metrics chính xác hơn.

---

## 📊 KẾT QUẢ MONG ĐỢI

Khi chạy, bạn sẽ thấy:

**Edge Server Console**:
```
[2026-03-04 10:30:15] Request from IoT_Device_1 (10.0.0.10)
→ Prediction: Benign (Conf: 95.2%) | Metrics: 52.3 Mbps, 15.2 ms
[2026-03-04 10:30:17] Request from IoT_Device_2 (10.0.0.11)  
🚨 Dashboard AI detected anomaly for IoT_Device_2: Score=0.856, Severity=high
→ Prediction: Malicious (Conf: 87.3%) | Metrics: 18.5 Mbps, 89.3 ms
```

**Dashboard**:
- Real-time charts updating
- Anomaly events appearing
- Statistics calculating
- Status changing 🟢/🔴

---

Bạn muốn tôi tạo files này luôn không? Hoặc cần customize thêm gì?
