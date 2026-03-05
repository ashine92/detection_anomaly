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
from storage import storage
# Note: detection.py (4-metric AI) is no longer used.
# All anomaly detection is performed by edge_server_with_dashboard.py
# using the full 24-feature Decision Tree model.

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
    Receive real AI results + raw features from Edge Server.
    Expected JSON (sent by edge_server_with_dashboard.py):
    {
        "timestamp":             "2026-03-06 12:00:00",
        "device_id":             "sta1",
        "prediction":            "Benign" | "Malicious",
        "confidence":            0.99,
        "probability_malicious": 0.0,      ← this is the anomaly score
        "tot_bytes":             98.0,
        "src_bytes":             98.0,
        "tcp_rtt":               0.0,
        "s_hops":                6.0,
        "s_ttl":                 58.0,
        "d_ttl":                 0.0,
        "s_mean_pkt_sz":         98.0,
        "icmp":                  0,
        "tcp_flag":              0,
        "rst_flag":              0
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required = ['timestamp', 'device_id', 'prediction',
                    'confidence', 'probability_malicious']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

        prediction   = data['prediction']          # 'Benign' or 'Malicious'
        confidence   = float(data['confidence'])
        # anomaly_score = probability of being Malicious (0.0 = definitely benign)
        anomaly_score = round(float(data['probability_malicious']), 4)

        is_anomaly       = (prediction == 'Malicious')
        prediction_label = 'anomaly' if is_anomaly else 'normal'

        if anomaly_score >= 0.9:
            severity = 'critical'
        elif anomaly_score >= 0.7:
            severity = 'high'
        elif anomaly_score >= 0.5:
            severity = 'medium'
        else:
            severity = 'low'

        detection_result = {
            'prediction_label':    prediction_label,
            'anomaly_score':       anomaly_score,
            'confidence':          round(confidence, 4),
            'severity':            severity,
            'is_anomaly':          is_anomaly,
            'model_type':          'edge_ai_24_features',
        }

        # Build the stored record — only real values, nothing computed
        RAW_FEATURE_KEYS = [
            'tot_bytes', 'src_bytes', 'tcp_rtt', 's_hops',
            's_ttl', 'd_ttl', 's_mean_pkt_sz',
            'icmp', 'tcp_flag', 'rst_flag',
        ]
        complete_data = {
            'timestamp':       data['timestamp'],
            'device_id':       data['device_id'],
            'prediction_label': prediction_label,
            'anomaly_score':   anomaly_score,
            'confidence':      round(confidence, 4),
            'severity':        severity,
            'received_at':     datetime.now().isoformat(),
        }
        for key in RAW_FEATURE_KEYS:
            if key in data:
                complete_data[key] = data[key]

        storage.add_metric(complete_data)

        if is_anomaly:
            storage.add_anomaly_event({**complete_data,
                                       'detected_at': complete_data['received_at']})
            logger.warning(f"ANOMALY — {data['device_id']} "
                           f"score={anomaly_score:.4f} severity={severity}")
        else:
            logger.info(f"Normal  — {data['device_id']} "
                        f"score={anomaly_score:.4f} conf={confidence:.2%}")

        return jsonify({
            'status': 'success',
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
        'ai_mode': 'edge_ai_24_features',
        'ai_description': 'Decision Tree, 24 network flow features, running on Edge Server',
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
    print(f"\n🤖 AI Mode: Edge AI — 24-feature Decision Tree (runs on Edge Server)")
    print(f"   Dashboard displays Edge AI results only. No local AI model.")
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
