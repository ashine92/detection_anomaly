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

# Import dashboard client
from dashboard_client import DashboardClient

logging.basicConfig(
    level=logging.INFO,
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

    def detect_anomaly(self, features):
        """Phát hiện anomaly từ 24 features"""
        try:
            features_array = np.array(features).reshape(1, -1)
            features_scaled = self.scaler.transform(features_array)

            prediction = self.model.predict(features_scaled)[0]
            probability = self.model.predict_proba(features_scaled)[0]
            confidence = np.max(probability)

            # Use class index dynamically instead of hardcoding [0]/[1]
            classes = self.model.classes_.tolist()
            benign_idx     = classes.index('Benign')    if 'Benign'    in classes else 0
            malicious_idx  = classes.index('Malicious') if 'Malicious' in classes else 1

            return {
                'prediction': prediction,
                'confidence': float(confidence),
                'probability_benign':    float(probability[benign_idx]),
                'probability_malicious': float(probability[malicious_idx]),
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

            # 2. Trích xuất trực tiếp các feature thực từ 24 features (không tính toán thêm)
            # Features: [0]Seq [1]Mean [2]sTos [3]sTtl [4]dTtl [5]sHops
            #           [6]TotBytes [7]SrcBytes [8]Offset [9]sMeanPktSz [10]dMeanPktSz
            #           [11]SrcWin [12]TcpRtt [13]AckDat [16]icmp [17]tcp [22]RST
            raw_features = {
                'tot_bytes':      round(float(features[6]),  4),
                'src_bytes':      round(float(features[7]),  4),
                'tcp_rtt':        round(float(features[12]), 4),
                's_hops':         round(float(features[5]),  4),
                's_ttl':          round(float(features[3]),  4),
                'd_ttl':          round(float(features[4]),  4),
                's_mean_pkt_sz':  round(float(features[9]),  4),
                'icmp':           int(features[16]),
                'tcp_flag':       int(features[17]),
                'rst_flag':       int(features[22]),
            }

            # 3. Gửi đến dashboard: kết quả AI thực + raw features (không fake)
            dashboard_result = self.dashboard.send_metrics(
                device_id=device_id,
                timestamp=result['timestamp'],
                prediction=result['prediction'],
                confidence=result['confidence'],
                probability_malicious=result['probability_malicious'],
                **raw_features
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
                f"{status_symbol} [{result['prediction']}] "
                f"conf={result['confidence']*100:.0f}% "
                f"p_mal={result['probability_malicious']:.4f} | "
                f"TotBytes={features[6]} TcpRtt={features[12]} sHops={features[5]} | "
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
    # model_path and scaler_path are now optional — defaults are set below
    
    # Default paths relative to this script's location
    _base = os.path.dirname(os.path.abspath(__file__))
    _model_dir = os.path.join(_base, '..', 'model')
    _default_model  = os.path.join(_model_dir, 'decision_tree_model_20260305_223751.pkl')
    _default_scaler = os.path.join(_model_dir, 'scaler_20260305_223751.pkl')

    model_path  = sys.argv[1] if len(sys.argv) > 1 else _default_model
    scaler_path = sys.argv[2] if len(sys.argv) > 2 else _default_scaler
    dashboard_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:5000/api/metrics"

    # Verify files exist
    if not os.path.exists(model_path):
        print(f"✗ Error: Model file not found: {model_path}")
        print(f"  Expected: {model_path}")
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
