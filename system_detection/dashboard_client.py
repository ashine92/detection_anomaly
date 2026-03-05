#!/usr/bin/python3
"""
Dashboard Client - Gửi metrics đến monitoring dashboard
File này kết nối Edge Server với Dashboard để gửi network metrics
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
        except Exception as e:
            logger.warning(f"⚠ Dashboard not available - metrics won't be sent ({e})")
            self.enabled = False
    
    def send_metrics(self, device_id, timestamp, prediction, confidence,
                     probability_malicious, **raw_features):
        """
        Gửi kết quả từ Edge AI và raw features đến dashboard.
        Chỉ truyền tải dữ liệu đã có, không tính toán thêm.

        Args:
            device_id (str): ID thiết bị
            timestamp (str): Thời gian (từ Edge Server)
            prediction (str): 'Benign' hoặc 'Malicious'
            confidence (float): Xác suất của class dự đoán (max probability)
            probability_malicious (float): Xác suất thuộc class Malicious (= anomaly score)
            **raw_features: Các feature thực từ 24 features
                (tot_bytes, src_bytes, tcp_rtt, s_hops, s_ttl, d_ttl,
                 s_mean_pkt_sz, icmp, tcp_flag, rst_flag)

        Returns:
            dict or False: Detection result hoặc False nếu lỗi
        """
        if not self.enabled:
            return False

        try:
            data = {
                'timestamp':            timestamp,
                'device_id':            device_id,
                'prediction':           prediction,
                'confidence':           float(confidence),
                'probability_malicious': float(probability_malicious),
            }
            data.update(raw_features)  # tất cả raw feature values

            response = requests.post(self.dashboard_url, json=data, timeout=1)

            if response.status_code == 200:
                return response.json().get('detection', {})
            else:
                logger.error(f"✗ Dashboard error: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"✗ Error sending to dashboard: {e}")
            return False
    
    def send_batch(self, metrics_list):
        """
        Gửi nhiều metrics cùng lúc
        
        Args:
            metrics_list (list): List of dicts với keys: device_id, throughput, latency, packet_loss, rssi
        
        Returns:
            int: Số metrics gửi thành công
        """
        success_count = 0
        for metrics in metrics_list:
            if self.send_metrics(**metrics):
                success_count += 1
        return success_count


if __name__ == "__main__":
    # Test script
    print("Testing Dashboard Client...")
    
    client = DashboardClient()
    
    if client.enabled:
        print("\n✓ Connected to dashboard\n")
        
        # Test send
        print("Sending test metrics...")
        result = client.send_metrics(
            device_id="TestDevice",
            throughput=50.5,
            latency=25.3,
            packet_loss=0.5,
            rssi=-65.0
        )
        
        if result:
            print(f"✓ Metrics sent successfully!")
            print(f"  Anomaly: {result.get('is_anomaly')}")
            print(f"  Score: {result.get('anomaly_score'):.3f}")
            print(f"  Severity: {result.get('severity')}")
        else:
            print("✗ Failed to send metrics")
    else:
        print("✗ Dashboard not available")
        print("  Make sure dashboard is running on http://localhost:5000")
