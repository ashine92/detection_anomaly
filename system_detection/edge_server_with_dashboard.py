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
import sys
import os
import random

# Import dashboard client
from dashboard_client import DashboardClient

logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG to see feature details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EdgeIoTDetectionServerWithDashboard:
    """Edge Server với dashboard monitoring"""
    def __init__(self, model_path, scaler_path, host='0.0.0.0', port=5001,
                 dashboard_url='http://localhost:5000/api/metrics'):
        self.host = host
        self.port = port
        
        # Load ML model (24 features)
        logger.info("Loading ML model...")
        try:
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            logger.info("✓ Model loaded successfully!")
        except Exception as e:
            logger.error(f"✗ Failed to load model: {e}")
            raise
        
        # Initialize dashboard client
        logger.info("Connecting to dashboard...")
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
        
        Features mapping (24 features - CORRECT ORDER):
        [0] Seq, [1] Mean, [2] sTos, [3] sTtl, [4] dTtl, [5] sHops, 
        [6] TotBytes, [7] SrcBytes, [8] Offset, [9] sMeanPktSz, 
        [10] dMeanPktSz, [11] SrcWin, [12] TcpRtt, [13] AckDat, 
        [14] ' e        ', [15] ' e d      ', [16] icmp, [17] tcp, 
        [18] CON, [19] FIN, [20] INT, [21] REQ, [22] RST, [23] Status
        
        Returns:
            dict: {throughput, latency, packet_loss, rssi}
        """
        try:
            # Extract relevant features
            tot_bytes = features[6]    # TotBytes
            src_bytes = features[7]    # SrcBytes
            tcp_rtt = features[12]     # TcpRtt (ms) - latency
            s_hops = features[5]       # sHops
            seq = features[0]          # Seq (packet sequence)
            mean = features[1]         # Mean
            rst_flag = features[22]    # RST flag
            fin_flag = features[19]    # FIN flag
            
            # 1. Calculate throughput (Mbps)
            # Sử dụng TotBytes và timing
            if device_id not in self.device_metrics:
                self.device_metrics[device_id] = {
                    'last_bytes': tot_bytes,
                    'last_time': request_time,
                    'last_seq': seq
                }
                # First request - estimate từ bytes
                throughput = (tot_bytes * 8) / (1024 * 1024)
            else:
                prev = self.device_metrics[device_id]
                time_diff = request_time - prev['last_time']
                bytes_diff = tot_bytes - prev['last_bytes']
                
                if time_diff > 0 and bytes_diff > 0:
                    throughput = (bytes_diff * 8) / (1024 * 1024 * time_diff)
                else:
                    throughput = (tot_bytes * 8) / (1024 * 1024)
                
                # Update tracking
                self.device_metrics[device_id] = {
                    'last_bytes': tot_bytes,
                    'last_time': request_time,
                    'last_seq': seq
                }
            
            # Ensure reasonable range
            throughput = max(0.1, min(1000, throughput))
            
            # 2. Latency (từ TCP RTT)
            latency = tcp_rtt if tcp_rtt > 0 else 10.0
            latency = max(1.0, min(500, latency))
            
            # 3. Packet loss (%)
            # Estimate từ RST flag và abnormal patterns
            if rst_flag == 1:
                packet_loss = random.uniform(5, 20)  # High loss khi có RST
            elif fin_flag == 0 and seq > 10000:
                packet_loss = random.uniform(2, 10)  # Moderate loss
            else:
                packet_loss = random.uniform(0, 2)   # Low loss
            
            packet_loss = max(0, min(100, packet_loss))
            
            # 4. Estimate RSSI (signal strength)
            # Dựa vào số hops và latency
            rssi_base = -50
            hop_penalty = s_hops * 3
            latency_penalty = min(30, latency / 5)
            
            rssi = rssi_base - hop_penalty - latency_penalty + np.random.uniform(-3, 3)
            rssi = max(-95, min(-30, rssi))  # Giới hạn -95 đến -30 dBm
            
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
        try:
            features_array = np.array(features).reshape(1, -1)
            features_scaled = self.scaler.transform(features_array)
            
            # DEBUG: Show raw and scaled features for analysis
            logger.debug(f"Raw features (first 8): {features[:8]}")
            logger.debug(f"Scaled features (first 8): {features_scaled[0][:8]}")
            
            prediction = self.model.predict(features_scaled)[0]
            probability = self.model.predict_proba(features_scaled)[0]
            confidence = np.max(probability)
            
            # Log if prediction seems wrong
            if features[0] > 50000 and prediction == 'Benign':
                logger.warning(f"⚠️ Possible misclassification! High Seq={features[0]} but predicted Benign")
                logger.warning(f"   Features: Seq={features[0]}, TotBytes={features[6]}, TcpRtt={features[12]}, RST={features[22]}")
            
            return {
                'prediction': prediction,
                'confidence': float(confidence),
                'probability_benign': float(probability[0]),
                'probability_malicious': float(probability[1]) if len(probability) > 1 else 0.0,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {
                'prediction': 'Error',
                'confidence': 0.0,
                'probability_benign': 0.0,
                'probability_malicious': 0.0,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def handle_client(self, client_socket, address):
        """Xử lý request từ IoT device"""
        request_time = time.time()
        
        try:
            # Nhận dữ liệu
            data = client_socket.recv(4096).decode()
            if not data:
                return
                
            request = json.loads(data)
            
            device_id = request.get('device_id', f'unknown_{address[0]}')
            features = request.get('features', [])
            
            if len(features) != 24:
                logger.warning(f"Invalid features length: {len(features)} (expected 24)")
                return
            
            logger.info(f"Request from {device_id} ({address[0]})")
            
            # 1. Phát hiện anomaly (24 features)
            result = self.detect_anomaly(features)
            result['device_id'] = device_id
            
            # 2. Calculate network metrics
            network_metrics = self.calculate_network_metrics(
                device_id, features, request_time
            )
            
            # 3. Send to dashboard
            dashboard_result = self.dashboard.send_metrics(
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
                logger.warning(f"⚠️  ALERT: Malicious activity from {device_id}!")
            
            # Send response
            response = json.dumps(result)
            client_socket.send(response.encode())
            
            # Log status
            status_symbol = "🔴" if result['prediction'] != 'Benign' else "🟢"
            dashboard_status = "✓" if dashboard_result else "✗"
            
            logger.info(
                f"{status_symbol} Prediction: {result['prediction']} "
                f"(Conf: {result['confidence']*100:.1f}%) | "
                f"Metrics: {network_metrics['throughput']:.1f} Mbps, "
                f"{network_metrics['latency']:.1f} ms, "
                f"{network_metrics['packet_loss']:.1f}% loss | "
                f"Dashboard: {dashboard_status}"
            )
            
        except Exception as e:
            logger.error(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
    
    def print_stats(self):
        """In thống kê định kỳ"""
        while True:
            time.sleep(60)  # Every minute
            if self.total_requests > 0:
                benign_pct = (self.benign_count / self.total_requests) * 100
                malicious_pct = (self.malicious_count / self.total_requests) * 100
                
                logger.info(
                    f"📊 Stats: Total={self.total_requests} | "
                    f"Benign={self.benign_count} ({benign_pct:.1f}%) | "
                    f"Malicious={self.malicious_count} ({malicious_pct:.1f}%)"
                )
    
    def start(self):
        """Khởi động server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.host, self.port))
        except OSError as e:
            logger.error(f"✗ Cannot bind to {self.host}:{self.port} - {e}")
            logger.error("  Port may already be in use. Try different port or kill existing process.")
            sys.exit(1)
        
        server_socket.listen(5)
        
        logger.info("="*70)
        logger.info("🚀 Edge IoT Detection Server WITH DASHBOARD")
        logger.info("="*70)
        logger.info(f"Server listening on {self.host}:{self.port}")
        logger.info(f"Dashboard integration: {'✅ Enabled' if self.dashboard.enabled else '❌ Disabled'}")
        logger.info(f"Model: {type(self.model).__name__}")
        logger.info("="*70)
        
        # Start stats thread
        stats_thread = threading.Thread(target=self.print_stats, daemon=True)
        stats_thread.start()
        
        try:
            while True:
                client_socket, address = server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
        except KeyboardInterrupt:
            logger.info("\n" + "="*70)
            logger.info("🛑 Shutting down server...")
            logger.info(f"📊 Final Stats:")
            logger.info(f"   Total requests: {self.total_requests}")
            logger.info(f"   Benign: {self.benign_count}")
            logger.info(f"   Malicious: {self.malicious_count}")
            logger.info("="*70)
        finally:
            server_socket.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python edge_server_with_dashboard.py <model_path> <scaler_path> [dashboard_url]")
        print("\nExample:")
        print("  python edge_server_with_dashboard.py ../model/decision_tree_model.pkl ../model/scaler.pkl")
        print("  python edge_server_with_dashboard.py ../model/decision_tree_model.pkl ../model/scaler.pkl http://192.168.1.100:5000/api/metrics")
        sys.exit(1)
    
    model_path = sys.argv[1]
    scaler_path = sys.argv[2]
    dashboard_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:5000/api/metrics"
    
    # Verify files exist
    if not os.path.exists(model_path):
        print(f"✗ Error: Model file not found: {model_path}")
        sys.exit(1)
    if not os.path.exists(scaler_path):
        print(f"✗ Error: Scaler file not found: {scaler_path}")
        sys.exit(1)
    
    server = EdgeIoTDetectionServerWithDashboard(
        model_path=model_path,
        scaler_path=scaler_path,
        dashboard_url=dashboard_url
    )
    
    server.start()
