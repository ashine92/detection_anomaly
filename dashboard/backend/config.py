"""
Configuration Module
Centralized configuration for the 5G-IoT Anomaly Detection System
"""

import os

# Base directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
MODEL_DIR = os.path.join(PROJECT_ROOT, 'model')


class Config:
    """Base configuration class"""
    
    # ========== Server Configuration ==========
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True
    
    # ========== Data Storage Configuration ==========
    MAX_DATA_POINTS = 100  # Maximum metrics to keep in memory
    MAX_ANOMALY_EVENTS = 200  # Maximum anomaly events to store
    
    # ========== AI Model Configuration ==========
    import glob
    model_files = glob.glob(os.path.join(MODEL_DIR, 'random_forest_model_*.pkl'))
    if model_files:
        MODEL_PATH = max(model_files, key=os.path.getctime)
        timestamp = os.path.basename(MODEL_PATH).split('_')[-1].split('.')[0]
        SCALER_PATH = glob.glob(os.path.join(MODEL_DIR, f'scaler_*_{timestamp}.pkl'))[0] if glob.glob(os.path.join(MODEL_DIR, f'scaler_*_{timestamp}.pkl')) else glob.glob(os.path.join(MODEL_DIR, 'scaler_*.pkl'))[0]
        FEATURE_NAMES_PATH = glob.glob(os.path.join(MODEL_DIR, f'feature_names_*_{timestamp}.pkl'))[0] if glob.glob(os.path.join(MODEL_DIR, f'feature_names_*_{timestamp}.pkl')) else glob.glob(os.path.join(MODEL_DIR, 'feature_names_*.pkl'))[0]
    else:
        MODEL_PATH = os.path.join(MODEL_DIR, 'random_forest_model_OPTIMIZED_20260603_220451.pkl')
        SCALER_PATH = os.path.join(MODEL_DIR, 'scaler_OPTIMIZED_20260603_220451.pkl')
        FEATURE_NAMES_PATH = os.path.join(MODEL_DIR, 'feature_names_OPTIMIZED_20260603_220451.pkl')
    
    # Model type: 'trained' or 'mock'
    MODEL_TYPE = 'trained'  # Use trained model if files exist
    
    # ========== Detection Thresholds ==========
    ANOMALY_THRESHOLD = 0.7  # Anomaly score threshold
    
    # Feature columns expected by the model
    FEATURE_COLUMNS = [
        'throughput',
        'latency', 
        'packet_loss',
        'rssi'
    ]
    
    # ========== Dashboard Configuration ==========
    REFRESH_INTERVAL = 2000  # Frontend auto-refresh interval (ms)
    
    # ========== CORS Configuration ==========
    CORS_ORIGINS = '*'  # Allow all origins (restrict in production)
    
    # ========== Logging ==========
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    CORS_ORIGINS = ['http://localhost:5000']


# Select configuration based on environment
ENV = os.getenv('FLASK_ENV', 'development')
if ENV == 'production':
    current_config = ProductionConfig()
else:
    current_config = DevelopmentConfig()
