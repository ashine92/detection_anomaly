#!/usr/bin/env python3
"""
Test script for 5G-IoT Anomaly Detection Dashboard
Generates random test data and sends it to the dashboard backend
Backend will automatically perform AI anomaly detection
"""

import requests
import time
import random
from datetime import datetime
import argparse


def generate_test_data(is_anomaly=False):
    """
    Generate random test data
    
    Backend will automatically detect anomalies using AI model.
    We just generate realistic network metrics here.
    
    Args:
        is_anomaly (bool): Whether to generate anomalous patterns
    
    Returns:
        dict: Test metrics data (without anomaly_score/prediction_label)
    """
    if is_anomaly:
        # Anomalous patterns: low throughput, high latency, high packet loss
        return {
            "timestamp": datetime.now().isoformat(),
            "device_id": f"IoT_Device_{random.randint(1, 5)}",
            "throughput": random.uniform(10, 30),    # Low throughput
            "latency": random.uniform(50, 150),      # High latency
            "packet_loss": random.uniform(5, 15),    # High packet loss
            "rssi": random.uniform(-90, -80)         # Weak signal
        }
    else:
        # Normal patterns: good throughput, low latency, low packet loss
        return {
            "timestamp": datetime.now().isoformat(),
            "device_id": f"IoT_Device_{random.randint(1, 5)}",
            "throughput": random.uniform(40, 80),    # Normal throughput
            "latency": random.uniform(5, 25),        # Normal latency
            "packet_loss": random.uniform(0, 2),     # Low packet loss
            "rssi": random.uniform(-70, -50)         # Good signal
        }


def send_test_data(api_url, interval=1, anomaly_frequency=10):
    """
    Continuously send test data to dashboard
    
    Args:
        api_url (str): Dashboard API endpoint URL
        interval (float): Time between data points (seconds)
        anomaly_frequency (int): Send anomaly every N data points
    """
    print("=" * 70)
    print("5G-IoT Anomaly Detection Dashboard - Test Data Generator")
    print("=" * 70)
    print(f"API Endpoint: {api_url}")
    print(f"Data Interval: {interval} seconds")
    print(f"Anomaly Frequency: Every {anomaly_frequency} data points")
    print("=" * 70)
    print("Press Ctrl+C to stop\n")
    
    counter = 0
    
    try:
        while True:
            # Generate test data (backend will detect anomalies)
            is_anomaly_pattern = (counter % anomaly_frequency == 0) and counter > 0
            data = generate_test_data(is_anomaly_pattern)
            
            try:
                response = requests.post(
                    api_url,
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=2
                )
                
                if response.status_code == 200:
                    result = response.json()
                    detection = result.get('detection', {})
                    
                    # Get AI detection results
                    prediction = detection.get('prediction_label', 'unknown')
                    score = detection.get('anomaly_score', 0.0)
                    severity = detection.get('severity', 'low')
                    
                    # Display with AI detection results
                    is_anomaly = prediction == 'anomaly'
                    status_icon = "🚨" if is_anomaly else "✓"
                    status_text = f"{prediction.upper():8s}"
                    
                    # Color-coded severity
                    severity_icon = {
                        'critical': '🔴',
                        'high': '🟠', 
                        'medium': '🟡',
                        'low': '🟢'
                    }.get(severity, '⚪')
                    
                    print(f"{status_icon} [{counter:04d}] {status_text} {severity_icon} | "
                          f"Device: {data['device_id']:15s} | "
                          f"Throughput: {data['throughput']:5.1f} Mbps | "
                          f"Latency: {data['latency']:6.1f} ms | "
                          f"AI Score: {score:.3f}")
                else:
                    print(f"✗ [{counter:04d}] Error - HTTP {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                print(f"✗ [{counter:04d}] Connection Error - Is the backend running?")
            except requests.exceptions.Timeout:
                print(f"✗ [{counter:04d}] Timeout Error")
            except Exception as e:
                print(f"✗ [{counter:04d}] Error: {e}")
            
            counter += 1
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print(f"Test Data Generator Stopped")
        print(f"Total Data Points Sent: {counter}")
        print(f"Approximate Anomaly Patterns: {counter // anomaly_frequency}")
        print("=" * 70)


def check_backend_health(health_url):
    """
    Check if backend is running and healthy
    
    Args:
        health_url (str): Health check endpoint URL
    
    Returns:
        bool: True if backend is healthy
    """
    try:
        response = requests.get(health_url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Backend is healthy")
            print(f"  - Data points: {data.get('data_points', 0)}")
            print(f"  - Anomalies detected: {data.get('anomalies_detected', 0)}")
            return True
        else:
            print(f"✗ Backend returned HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend - Is it running?")
        print("   Start backend with: cd backend && python app.py")
        return False
    except Exception as e:
        print(f"✗ Error checking backend health: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate test data for 5G-IoT Anomaly Detection Dashboard'
    )
    parser.add_argument(
        '--url',
        default='http://localhost:5000/api/metrics',
        help='Dashboard API endpoint URL (default: http://localhost:5000/api/metrics)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=1.0,
        help='Time between data points in seconds (default: 1.0)'
    )
    parser.add_argument(
        '--anomaly-freq',
        type=int,
        default=10,
        help='Send anomaly every N data points (default: 10)'
    )
    parser.add_argument(
        '--no-health-check',
        action='store_true',
        help='Skip backend health check'
    )
    
    args = parser.parse_args()
    
    # Extract base URL for health check
    base_url = args.url.rsplit('/api/', 1)[0]
    health_url = f"{base_url}/health"
    
    # Check backend health before starting
    if not args.no_health_check:
        print("Checking backend health...")
        if not check_backend_health(health_url):
            print("\nCannot proceed without backend connection.")
            exit(1)
        print()
    
    # Start sending test data
    send_test_data(args.url, args.interval, args.anomaly_freq)
