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
        self._consecutive_failures = 0
        self._MAX_FAILURES = 10  # disable sau khi thất bại 10 lần liên tiếp

        # Test connection — chỉ log warning, KHÔNG disable nếu fail
        # (trong Mininet, bridge có thể chưa ready lúc init)
        try:
            health_url = dashboard_url.replace('/api/metrics', '/health')
            response = requests.get(health_url, timeout=2)
            if response.status_code == 200:
                logger.info(f"✓ Dashboard connected: {dashboard_url}")
            else:
                logger.warning(f"⚠ Dashboard health check returned {response.status_code} — will retry on each send")
        except Exception as e:
            logger.warning(f"⚠ Dashboard not reachable at init ({e}) — will retry on each send")
    
    def send_metrics(self, device_id, timestamp, prediction, confidence,
                     probability_malicious, mininet_ctx=None, **raw_features):
        """
        Gửi kết quả từ Edge AI và raw features đến dashboard.
        Nếu có Mininet context (chạy trong Mininet-WiFi), gửi kèm.

        Args:
            device_id (str)             : ID thiết bị
            timestamp (str)             : Thời gian (từ Edge Server)
            prediction (str)            : 'Benign' hoặc 'Malicious'
            confidence (float)          : Độ tin cậy model
            probability_malicious (float): P(Malicious) = anomaly score
            mininet_ctx (dict|None)     : Mininet-WiFi context (node, SSID, RSSI, bitrate)
            **raw_features              : Các feature thực từ 24 features

        Returns:
            dict or False
        """
        if not self.enabled:
            return False

        if not self.enabled:
            return False

        try:
            data = {
                'timestamp':             timestamp,
                'device_id':             device_id,
                'prediction':            prediction,
                'confidence':            float(confidence),
                'probability_malicious': float(probability_malicious),
            }
            data.update(raw_features)  # tot_bytes, tcp_rtt, s_ttl, ...

            # Flatten Mininet context vào record nếu có
            if mininet_ctx:
                for key, val in mininet_ctx.items():
                    if val is not None:          # chỉ gửi field có giá trị thực
                        data[key] = val

            response = requests.post(self.dashboard_url, json=data, timeout=1)

            if response.status_code == 200:
                # Reset failure counter khi thành công
                if self._consecutive_failures > 0:
                    logger.info("✓ Dashboard reconnected!")
                    self._consecutive_failures = 0
                return response.json().get('detection', {})
            else:
                logger.error(f"✗ Dashboard error: HTTP {response.status_code}")
                self._consecutive_failures += 1
                return False

        except Exception as e:
            self._consecutive_failures += 1
            if self._consecutive_failures == 1:
                # Chỉ log lần đầu, tránh spam log
                logger.error(f"✗ Error sending to dashboard: {e}")
            elif self._consecutive_failures >= self._MAX_FAILURES:
                logger.error(f"✗ Dashboard unreachable after {self._MAX_FAILURES} attempts — disabling client")
                self.enabled = False
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
