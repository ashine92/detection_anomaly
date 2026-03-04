"""
5G-IoT Anomaly Detection Dashboard - Flask Backend
Real-time monitoring API server with AI-powered anomaly detection

Clean Architecture:
- app.py: API routes and request handling
- detection.py: AI model and anomaly detection logic
- storage.py: Data persistence layer
- config.py: Configuration management
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
import logging

# Import our modules
from config import current_config as config
from detection import detector
from storage import storage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=config.CORS_ORIGINS)

# Path to frontend directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')


# ============================================================
# API Routes
# ============================================================

@app.route('/')
def index():
    """
    Serve the frontend dashboard HTML
    """
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/api/metrics', methods=['POST'])
def receive_metrics():
    """
    Receive network metrics and perform AI-powered anomaly detection
    
    Expected JSON format:
    {
        "timestamp": "2024-01-01T12:00:00",
        "device_id": "IoT_Device_1",
        "throughput": 45.5,
        "latency": 12.3,
        "packet_loss": 0.5,
        "rssi": -65
    }
    
    Process flow:
    1. Validate input data
    2. Run AI model for anomaly detection
    3. Store metrics and results
    4. Return detection results
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['timestamp', 'device_id', 'throughput', 
                          'latency', 'packet_loss', 'rssi']
        
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Extract metrics for AI model
        metrics = {
            'throughput': float(data['throughput']),
            'latency': float(data['latency']),
            'packet_loss': float(data['packet_loss']),
            'rssi': float(data['rssi'])
        }
        
        # ========== AI ANOMALY DETECTION ==========
        # Run detection model
        detection_result = detector.analyze_metrics(metrics)
        
        # Prepare complete data record
        complete_data = {
            'timestamp': data['timestamp'],
            'device_id': data['device_id'],
            'throughput': metrics['throughput'],
            'latency': metrics['latency'],
            'packet_loss': metrics['packet_loss'],
            'rssi': metrics['rssi'],
            'anomaly_score': detection_result['anomaly_score'],
            'prediction_label': detection_result['prediction_label'],
            'severity': detection_result['severity'],
            'received_at': datetime.now().isoformat()
        }
        
        # Store in data storage
        storage.add_metric(complete_data)
        
        # If anomaly detected, store in anomaly events
        if detection_result['is_anomaly']:
            anomaly_event = {
                'timestamp': data['timestamp'],
                'device_id': data['device_id'],
                'anomaly_score': detection_result['anomaly_score'],
                'severity': detection_result['severity'],
                'throughput': metrics['throughput'],
                'latency': metrics['latency'],
                'packet_loss': metrics['packet_loss'],
                'rssi': metrics['rssi'],
                'detected_at': datetime.now().isoformat()
            }
            storage.add_anomaly_event(anomaly_event)
            
            logger.warning(f"🚨 ANOMALY DETECTED - Device: {data['device_id']}, "
                          f"Score: {detection_result['anomaly_score']:.3f}, "
                          f"Severity: {detection_result['severity']}")
        
        # Return success response with detection results
        return jsonify({
            'status': 'success',
            'message': 'Metrics received and analyzed',
            'detection': detection_result
        }), 200
    
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error processing metrics: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """
    Retrieve dashboard data
    
    Returns complete data package for frontend:
    - All metrics data points
    - Recent anomaly events
    - Statistics summary
    """
    try:
        dashboard_data = storage.get_dashboard_data()
        return jsonify(dashboard_data), 200
    
    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reset', methods=['POST'])
def reset_data():
    """
    Reset all stored data
    Clears metrics, anomaly events, and statistics
    """
    try:
        storage.reset_all()
        logger.info("📝 All data reset")
        
        return jsonify({
            'status': 'success',
            'message': 'All data has been reset'
        }), 200
    
    except Exception as e:
        logger.error(f"Error resetting data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    Returns system status and statistics
    """
    stats = storage.get_statistics()
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': detector.model_loaded,
        'model_type': 'trained' if detector.model_loaded else 'mock',
        'statistics': stats
    }), 200


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    Get detailed statistics
    """
    try:
        stats = storage.get_statistics()
        return jsonify(stats), 200
    
    except Exception as e:
        logger.error(f"Error retrieving statistics: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# Application Startup
# ============================================================

if __name__ == '__main__':
    print("=" * 70)
    print("  5G-IoT ANOMALY DETECTION DASHBOARD - BACKEND SERVER")
    print("=" * 70)
    print(f"\n🚀 Starting Flask server...")
    print(f"\n📊 Dashboard URL:")
    print(f"   • http://localhost:{config.PORT}")
    print(f"   • http://127.0.0.1:{config.PORT}")
    print(f"\n🔌 API Endpoints:")
    print(f"   • POST /api/metrics      - Receive metrics (with AI detection)")
    print(f"   • GET  /api/metrics      - Get dashboard data")
    print(f"   • GET  /api/statistics   - Get statistics")
    print(f"   • POST /api/reset        - Reset all data")
    print(f"   • GET  /health           - Health check")
    print(f"\n🤖 AI Model Status:")
    if detector.model_loaded:
        print(f"   ✓ Trained Decision Tree model loaded")
        print(f"   ✓ Features: {detector.feature_names}")
    else:
        print(f"   ⚠ Using mock detection mode (model files not found)")
    print(f"\n💾 Storage Configuration:")
    print(f"   • Max metrics: {config.MAX_DATA_POINTS}")
    print(f"   • Max anomaly events: {config.MAX_ANOMALY_EVENTS}")
    print("=" * 70)
    print(f"\n👉 Open your browser: http://localhost:{config.PORT}\n")
    
    # Run Flask application
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
