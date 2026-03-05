"""
Anomaly Detection Module — DEPRECATED / KHÔNG CÒN ĐƯỢC SỬ DỤNG
=================================================================
Module này (4-metric rule-based AI) đã bị vô hiệu hoá.

Tất cả phát hiện anomaly hiện nay được thực hiện bởi:
  → edge_server_with_dashboard.py  (24-feature Decision Tree)

Dashboard chỉ nhận và hiển thị kết quả từ Edge AI.
File này được giữ lại để tham khảo, KHÔNG được import trong app.py.
"""

import pickle
import joblib
import numpy as np
import os
from typing import Dict, Tuple, Optional
from config import current_config as config
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    AI-powered anomaly detection system
    
    Loads trained model and performs real-time anomaly detection
    on incoming network metrics.
    """
    
    def __init__(self):
        """Initialize detector and load AI model"""
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.model_loaded = False
        
        # Load model on initialization
        self._load_model()
    
    def _load_model(self) -> None:
        """
        Load trained model, scaler, and feature names from disk
        """
        try:
            # Check if model files exist
            if not all([
                os.path.exists(config.MODEL_PATH),
                os.path.exists(config.SCALER_PATH),
                os.path.exists(config.FEATURE_NAMES_PATH)
            ]):
                logger.warning("Model files not found. Using mock detection mode.")
                self.model_loaded = False
                return
            
            # Load Decision Tree model
            with open(config.MODEL_PATH, 'rb') as f:
                self.model = joblib.load(f)
            logger.info(f"✓ Model loaded: {config.MODEL_PATH}")
            
            # Load scaler (for feature normalization)
            with open(config.SCALER_PATH, 'rb') as f:
                self.scaler = joblib.load(f)
            logger.info(f"✓ Scaler loaded: {config.SCALER_PATH}")
            
            # Load feature names
            with open(config.FEATURE_NAMES_PATH, 'rb') as f:
                self.feature_names = joblib.load(f)
            logger.info(f"✓ Feature names loaded: {self.feature_names}")
            
            self.model_loaded = True
            logger.info("✓ Anomaly detection model ready!")
            
        except Exception as e:
            logger.error(f"✗ Error loading model: {e}")
            self.model_loaded = False
    
    def preprocess_data(self, metrics: Dict) -> Optional[np.ndarray]:
        """
        Preprocess raw metrics data for model input
        
        Args:
            metrics (dict): Raw network metrics
                Expected keys: throughput, latency, packet_loss, rssi
        
        Returns:
            np.ndarray: Preprocessed feature array, or None if error
        """
        try:
            # Extract features in correct order
            features = []
            for feature_name in self.feature_names:
                if feature_name in metrics:
                    features.append(float(metrics[feature_name]))
                else:
                    logger.warning(f"Missing feature: {feature_name}")
                    return None
            
            # Convert to numpy array
            features_array = np.array(features).reshape(1, -1)
            
            # Scale features using loaded scaler
            if self.scaler is not None:
                features_scaled = self.scaler.transform(features_array)
            else:
                features_scaled = features_array
            
            return features_scaled
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {e}")
            return None
    
    def predict(self, metrics: Dict) -> Tuple[str, float]:
        """
        Perform anomaly detection on network metrics
        
        Args:
            metrics (dict): Network metrics
                {
                    'throughput': float,
                    'latency': float,
                    'packet_loss': float,
                    'rssi': float
                }
        
        Returns:
            tuple: (prediction_label, anomaly_score)
                - prediction_label: 'normal' or 'anomaly'
                - anomaly_score: float between 0 and 1
        """
        # If model not loaded, use mock detection
        if not self.model_loaded:
            return self._mock_predict(metrics)
        
        try:
            # Preprocess metrics
            features = self.preprocess_data(metrics)
            
            if features is None:
                logger.error("Preprocessing failed, using mock detection")
                return self._mock_predict(metrics)
            
            # Get prediction — model returns string class: 'Benign' or 'Malicious'
            prediction = self.model.predict(features)[0]
            
            # Get prediction probabilities (anomaly score)
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(features)[0]
                classes = self.model.classes_.tolist()
                # Anomaly score = probability of 'Malicious' class
                malicious_idx = classes.index('Malicious') if 'Malicious' in classes else 1
                anomaly_score = float(probabilities[malicious_idx])
            else:
                anomaly_score = 1.0 if prediction == 'Malicious' else 0.0
            
            # Convert prediction to label
            prediction_label = 'anomaly' if prediction == 'Malicious' else 'normal'
            
            logger.info(f"Prediction: {prediction_label} (score: {anomaly_score:.3f})")
            
            return prediction_label, anomaly_score
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self._mock_predict(metrics)
    
    def _mock_predict(self, metrics: Dict) -> Tuple[str, float]:
        """
        Mock prediction when model is not available
        Uses simple rule-based detection for testing
        
        Args:
            metrics (dict): Network metrics
        
        Returns:
            tuple: (prediction_label, anomaly_score)
        """
        # Simple rule-based detection
        # Anomaly if: low throughput OR high latency OR high packet loss
        
        throughput = metrics.get('throughput', 50)
        latency = metrics.get('latency', 20)
        packet_loss = metrics.get('packet_loss', 0)
        
        # Calculate anomaly score based on thresholds
        score = 0.0
        
        if throughput < 30:  # Low throughput
            score += 0.3
        if latency > 50:  # High latency
            score += 0.4
        if packet_loss > 5:  # High packet loss
            score += 0.3
        
        # Clip score to [0, 1]
        score = min(1.0, score)
        
        # Determine label
        prediction_label = 'anomaly' if score >= config.ANOMALY_THRESHOLD else 'normal'
        
        return prediction_label, score
    
    def analyze_metrics(self, metrics: Dict) -> Dict:
        """
        Complete analysis of network metrics
        
        Performs prediction and returns detailed results
        
        Args:
            metrics (dict): Raw network metrics
        
        Returns:
            dict: Analysis results with prediction and explanation
        """
        # Get prediction
        prediction_label, anomaly_score = self.predict(metrics)
        
        # Determine severity
        if anomaly_score >= 0.9:
            severity = 'critical'
        elif anomaly_score >= 0.7:
            severity = 'high'
        elif anomaly_score >= 0.5:
            severity = 'medium'
        else:
            severity = 'low'
        
        # Build result
        result = {
            'prediction_label': prediction_label,
            'anomaly_score': round(anomaly_score, 4),
            'severity': severity,
            'is_anomaly': prediction_label == 'anomaly',
            'model_type': 'trained' if self.model_loaded else 'mock',
            'metrics_analyzed': {
                'throughput': metrics.get('throughput'),
                'latency': metrics.get('latency'),
                'packet_loss': metrics.get('packet_loss'),
                'rssi': metrics.get('rssi')
            }
        }
        
        return result


# ========== Global Detector Instance ==========
# Singleton pattern - single detector instance shared across the app
detector = AnomalyDetector()
