#!/usr/bin/python3
"""
Edge Server - IoT Anomaly Detection Service
Chạy mô hình ML để phát hiện anomaly từ dữ liệu IoT
"""

import socket
import joblib
import numpy as np
import json
from datetime import datetime
import threading

class EdgeIoTDetectionServer:
    """Server phát hiện anomaly chạy trên Edge"""
    
    def __init__(self, model_path, scaler_path, host='10.0.0.100', port=5000):
        self.host = host
        self.port = port
        
        # Load mô hình đã lưu
        print(f"[{datetime.now()}] Loading ML model...")
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        print(f"[{datetime.now()}] Model loaded successfully!")
        
        # Statistics
        self.total_requests = 0
        self.benign_count = 0
        self.malicious_count = 0
        
    def detect_anomaly(self, features):
        """Phát hiện anomaly từ features"""
        # Reshape và scale
        features_array = np.array(features).reshape(1, -1)
        features_scaled = self.scaler.transform(features_array)
        
        # Dự đoán
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
        try:
            # Nhận dữ liệu
            data = client_socket.recv(4096).decode()
            request = json.loads(data)
            
            device_id = request.get('device_id', 'unknown')
            features = request.get('features', [])
            
            print(f"[{datetime.now()}] Request from {device_id} ({address[0]})")
            
            # Phát hiện anomaly
            result = self.detect_anomaly(features)
            result['device_id'] = device_id
            
            # Cập nhật statistics
            self.total_requests += 1
            if result['prediction'] == 'Benign':
                self.benign_count += 1
            else:
                self.malicious_count += 1
                print(f"  ⚠️  ALERT: Malicious activity detected from {device_id}!")
            
            # Gửi kết quả
            response = json.dumps(result)
            client_socket.send(response.encode())
            
            print(f"  → Prediction: {result['prediction']} (Confidence: {result['confidence']*100:.2f}%)")
            
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            client_socket.close()
    
    def start(self):
        """Start server"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        
        print("="*70)
        print("EDGE IoT DETECTION SERVER")
        print("="*70)
        print(f"Server started on {self.host}:{self.port}")
        print(f"Waiting for IoT device connections...")
        print("="*70)
        
        try:
            while True:
                client, address = server.accept()
                client_handler = threading.Thread(
                    target=self.handle_client,
                    args=(client, address)
                )
                client_handler.start()
        except KeyboardInterrupt:
            print("\n\nServer Statistics:")
            print(f"Total requests: {self.total_requests}")
            print(f"Benign: {self.benign_count}")
            print(f"Malicious: {self.malicious_count}")
            print("\nServer stopped.")
            server.close()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python3 edge_server.py <model_path> <scaler_path>")
        sys.exit(1)
    
    model_path = sys.argv[1]
    scaler_path = sys.argv[2]
    
    server = EdgeIoTDetectionServer(model_path, scaler_path)
    server.start()
