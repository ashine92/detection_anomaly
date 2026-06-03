"""
Data Storage Module
Manages in-memory storage for metrics and anomaly detection results

This module provides a clean interface for data persistence.
Can be easily extended to use database (PostgreSQL, MongoDB) in the future.
"""

from collections import deque
from datetime import datetime
import statistics
from typing import Dict, List, Optional
from config import current_config as config


class DataStorage:
    """
    In-memory data storage with FIFO queues
    
    Stores:
    - Edge AI detection results + raw network features
    - Anomaly events
    - Running statistics
    """
    
    def __init__(self):
        """Initialize storage with empty collections"""
        # Metrics data (limited size FIFO queue)
        self.metrics_data = deque(maxlen=config.MAX_DATA_POINTS)
        
        # Anomaly events only
        self.anomaly_events = deque(maxlen=config.MAX_ANOMALY_EVENTS)
        
        # Statistics tracking
        self.stats = {
            'total_requests':   0,
            'total_anomalies':  0,
            'anomaly_rate':     0.0,
            'avg_anomaly_score': 0.0,  # average probability_malicious
            'avg_confidence':   0.0,   # average model confidence
            'last_update':      None
        }
    
    def add_metric(self, metric_data: Dict) -> None:
        """
        Store a new metric data point
        
        Args:
            metric_data (dict): Contains network metrics and detection results
                Required keys: throughput, latency, packet_loss, rssi,
                              anomaly_score, prediction_label, device_id
        """
        # Add received timestamp
        if 'received_at' not in metric_data:
            metric_data['received_at'] = datetime.now().isoformat()
        
        # Store in metrics queue
        self.metrics_data.append(metric_data)
        
        # Update request counter
        self.stats['total_requests'] += 1
        
        # Update statistics
        self._update_statistics()
    
    def add_anomaly_event(self, event_data: Dict) -> None:
        """
        Store an anomaly event
        
        Args:
            event_data (dict): Anomaly event details
        """
        # Add detection timestamp
        if 'detected_at' not in event_data:
            event_data['detected_at'] = datetime.now().isoformat()
        
        # Store in anomaly events queue
        self.anomaly_events.append(event_data)
        
        # Update anomaly counter
        self.stats['total_anomalies'] += 1
        
        # Update statistics
        self._update_statistics()
    
    def get_all_metrics(self) -> List[Dict]:
        """
        Get all stored metrics
        
        Returns:
            list: All metric data points
        """
        return list(self.metrics_data)
    
    def get_recent_metrics(self, count: int = 20) -> List[Dict]:
        """
        Get most recent N metrics
        
        Args:
            count (int): Number of recent metrics to retrieve
        
        Returns:
            list: Recent metric data points
        """
        all_metrics = list(self.metrics_data)
        return all_metrics[-count:] if len(all_metrics) >= count else all_metrics
    
    def get_anomaly_events(self, count: Optional[int] = None) -> List[Dict]:
        """
        Get anomaly events
        
        Args:
            count (int, optional): Number of events. If None, returns all.
        
        Returns:
            list: Anomaly event records
        """
        all_events = list(self.anomaly_events)
        
        if count is None:
            return all_events
        
        return all_events[-count:] if len(all_events) >= count else all_events
    
    def get_statistics(self) -> Dict:
        """
        Get current statistics
        
        Returns:
            dict: Statistics summary
        """
        return self.stats.copy()
    
    def reset_all(self) -> None:
        """
        Clear all data and reset statistics
        Useful for testing or starting fresh
        """
        self.metrics_data.clear()
        self.anomaly_events.clear()
        
        self.stats = {
            'total_requests':    0,
            'total_anomalies':   0,
            'anomaly_rate':      0.0,
            'avg_anomaly_score': 0.0,
            'avg_confidence':    0.0,
            'last_update':       None
        }
    
    def _update_statistics(self) -> None:
        """Update running statistics after adding new data"""
        if len(self.metrics_data) > 0:
            scores = [m.get('anomaly_score', 0.0) for m in self.metrics_data]
            self.stats['avg_anomaly_score'] = round(statistics.mean(scores), 4)

            confs = [m.get('confidence', 0.0) for m in self.metrics_data]
            self.stats['avg_confidence'] = round(statistics.mean(confs), 4)

        if self.stats['total_requests'] > 0:
            rate = (self.stats['total_anomalies'] / self.stats['total_requests']) * 100
            self.stats['anomaly_rate'] = round(rate, 2)
        else:
            self.stats['anomaly_rate'] = 0.0

        self.stats['last_update'] = datetime.now().isoformat()
    
    def get_dashboard_data(self) -> Dict:
        """
        Get complete data for dashboard display
        
        Returns:
            dict: Complete data package for frontend
        """
        return {
            'metrics': self.get_all_metrics(),
            'recent_metrics': self.get_recent_metrics(30),
            'anomaly_events': self.get_anomaly_events(50),
            'statistics': self.get_statistics(),
            'counts': {
                'total_metrics': len(self.metrics_data),
                'total_anomalies': len(self.anomaly_events)
            }
        }


# ========== Global Storage Instance ==========
# Singleton pattern - single storage instance shared across the app
storage = DataStorage()
