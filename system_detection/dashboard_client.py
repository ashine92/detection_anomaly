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
    
    def send_metrics(self, device_id, throughput, latency, packet_loss, rssi):
        """
        Gửi network metrics đến dashboard để AI phân tích
        
        Args:
            device_id (str): ID thiết bị
            throughput (float): Throughput (Mbps)
            latency (float): Latency (ms)
            packet_loss (float): Packet loss (%)
            rssi (float): Signal strength (dBm)
        
        Returns:
            dict or False: Detection result hoặc False nếu lỗi
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
                
                return detection
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
