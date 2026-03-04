# 5G-IoT Anomaly Detection Dashboard

A real-time web-based monitoring dashboard for 5G-IoT network anomaly detection. This system provides visualization and analysis of network metrics including throughput, latency, packet loss, and anomaly detection scores.

## 📋 Features

### Backend (Flask)
- ✅ RESTful API endpoints
- ✅ POST endpoint to receive JSON metrics data
- ✅ GET endpoint to serve data to frontend
- ✅ In-memory data storage (last 100 data points)
- ✅ Real-time statistics calculation
- ✅ CORS enabled for cross-origin requests
- ✅ Health check endpoint

### Frontend (HTML/CSS/JavaScript)
- ✅ Modern dark theme UI
- ✅ Real-time auto-refresh (1 second interval)
- ✅ Interactive Chart.js visualizations:
  - Throughput line chart
  - Latency line chart
  - Anomaly score line chart
- ✅ System status indicator (Green = Normal, Red = Anomaly)
- ✅ Statistics summary panel
- ✅ Anomaly events table with highlighting
- ✅ Responsive design
- ✅ Connection status indicator
- ✅ Data reset functionality

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Edge, Safari)

### Installation

1. **Navigate to the dashboard directory:**
   ```bash
   cd dashboard
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Dashboard

#### Step 1: Start the Backend Server

```bash
cd backend
python app.py
```

The Flask server will start on `http://localhost:5000`

You should see:
```
============================================================
5G-IoT Anomaly Detection Dashboard - Backend Server
============================================================
Starting Flask server on http://localhost:5000
API Endpoints:
  - POST /api/metrics  : Receive metrics data
  - GET  /api/metrics  : Retrieve dashboard data
  - POST /api/reset    : Reset all data
  - GET  /health       : Health check
============================================================
```

#### Step 2: Open the Frontend

Open the frontend HTML file in your web browser:

**Option 1: Direct file open**
```bash
cd ../frontend
# Then open index.html in your browser
```

**Option 2: Using Python HTTP server (recommended)**
```bash
cd ../frontend
python -m http.server 8080
```
Then navigate to: `http://localhost:8080`

The dashboard will automatically start fetching data from the backend every 1 second.

## 📡 Sending Data to the Dashboard

### From Your Simulation Code

To send metrics data from your 5G-IoT Mininet simulation, use HTTP POST requests:

```python
import requests
import json
from datetime import datetime

# Prepare metrics data
metrics_data = {
    "timestamp": datetime.now().isoformat(),
    "device_id": "IoT_Device_1",
    "throughput": 45.5,          # Mbps
    "latency": 12.3,             # ms
    "packet_loss": 0.5,          # %
    "rssi": -65,                 # dBm
    "anomaly_score": 0.3,        # 0-1
    "prediction_label": "normal" # "normal" or "anomaly"
}

# Send to dashboard
response = requests.post(
    'http://localhost:5000/api/metrics',
    json=metrics_data,
    headers={'Content-Type': 'application/json'}
)

print(response.json())
```

### Example: Integration with Mininet Simulation

Add this function to your simulation code:

```python
import requests
from datetime import datetime

def send_to_dashboard(device_id, throughput, latency, packet_loss, rssi, 
                     anomaly_score, prediction_label):
    """Send metrics to the monitoring dashboard"""
    try:
        data = {
            "timestamp": datetime.now().isoformat(),
            "device_id": device_id,
            "throughput": throughput,
            "latency": latency,
            "packet_loss": packet_loss,
            "rssi": rssi,
            "anomaly_score": anomaly_score,
            "prediction_label": prediction_label
        }
        
        response = requests.post(
            'http://localhost:5000/api/metrics',
            json=data,
            timeout=1
        )
        
        if response.status_code == 200:
            print(f"✓ Metrics sent to dashboard for {device_id}")
        else:
            print(f"✗ Failed to send metrics: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error sending to dashboard: {e}")

# Usage in your simulation loop
send_to_dashboard(
    device_id="IoT_Station_1",
    throughput=50.2,
    latency=15.6,
    packet_loss=0.3,
    rssi=-70,
    anomaly_score=0.85,
    prediction_label="anomaly"
)
```

### Testing with cURL

You can test the API directly using cURL:

```bash
curl -X POST http://localhost:5000/api/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-01-01T12:00:00",
    "device_id": "IoT_Device_1",
    "throughput": 45.5,
    "latency": 12.3,
    "packet_loss": 0.5,
    "rssi": -65,
    "anomaly_score": 0.3,
    "prediction_label": "normal"
  }'
```

### Testing with Python Script

Create a test script to simulate data:

```python
# test_dashboard.py
import requests
import time
import random
from datetime import datetime

def generate_test_data(is_anomaly=False):
    """Generate random test data"""
    if is_anomaly:
        return {
            "timestamp": datetime.now().isoformat(),
            "device_id": f"IoT_Device_{random.randint(1, 5)}",
            "throughput": random.uniform(10, 30),    # Low throughput
            "latency": random.uniform(50, 150),      # High latency
            "packet_loss": random.uniform(5, 15),    # High packet loss
            "rssi": random.uniform(-90, -80),        # Weak signal
            "anomaly_score": random.uniform(0.7, 1.0),
            "prediction_label": "anomaly"
        }
    else:
        return {
            "timestamp": datetime.now().isoformat(),
            "device_id": f"IoT_Device_{random.randint(1, 5)}",
            "throughput": random.uniform(40, 80),    # Normal throughput
            "latency": random.uniform(5, 25),        # Normal latency
            "packet_loss": random.uniform(0, 2),     # Low packet loss
            "rssi": random.uniform(-70, -50),        # Good signal
            "anomaly_score": random.uniform(0, 0.5),
            "prediction_label": "normal"
        }

def send_test_data():
    """Continuously send test data to dashboard"""
    print("Starting test data generator...")
    print("Press Ctrl+C to stop")
    
    try:
        counter = 0
        while True:
            # Generate anomaly every 10th data point
            is_anomaly = (counter % 10 == 0)
            data = generate_test_data(is_anomaly)
            
            try:
                response = requests.post(
                    'http://localhost:5000/api/metrics',
                    json=data,
                    timeout=1
                )
                
                status = "ANOMALY" if is_anomaly else "NORMAL"
                print(f"[{counter}] Sent {status} data - Response: {response.status_code}")
                
            except Exception as e:
                print(f"Error sending data: {e}")
            
            counter += 1
            time.sleep(1)  # Send data every second
            
    except KeyboardInterrupt:
        print("\nStopped test data generator")

if __name__ == "__main__":
    send_test_data()
```

Run the test:
```bash
python test_dashboard.py
```

## 🎨 Dashboard Features Explained

### Statistics Panel
- **Average Throughput**: Mean throughput across all data points (Mbps)
- **Average Latency**: Mean latency across all data points (ms)
- **Total Anomalies**: Count of detected anomalies
- **Data Points**: Number of metrics received

### Charts
- **Throughput Chart**: Real-time line chart showing network throughput over time
- **Latency Chart**: Real-time line chart showing network latency over time
- **Anomaly Score Chart**: Real-time chart with color-coded segments (red > 0.7 threshold)

### System Status Indicator
- **Green (Normal)**: No anomalies detected, system operating normally
- **Red (Anomaly)**: Anomaly detected (score > 0.7 or prediction_label = "anomaly")
- Pulsing animation alerts user to anomalies

### Anomaly Events Table
- Displays all detected anomalies in reverse chronological order
- Rows with anomaly_score > 0.7 are highlighted in red
- Shows: timestamp, device_id, anomaly_score, throughput, latency, packet_loss

### Controls
- **Pause/Resume Auto-Refresh**: Stop/start automatic data fetching
- **Reset Data**: Clear all stored metrics and anomaly events

## 🔌 API Endpoints

### POST /api/metrics
Receive network metrics data from simulation

**Request Body:**
```json
{
    "timestamp": "2024-01-01T12:00:00",
    "device_id": "IoT_Device_1",
    "throughput": 45.5,
    "latency": 12.3,
    "packet_loss": 0.5,
    "rssi": -65,
    "anomaly_score": 0.3,
    "prediction_label": "normal"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Metrics received"
}
```

### GET /api/metrics
Retrieve dashboard data

**Response:**
```json
{
    "metrics": [...],
    "anomaly_events": [...],
    "statistics": {
        "avg_throughput": 45.2,
        "avg_latency": 15.6,
        "total_anomalies": 5
    },
    "data_count": 50
}
```

### POST /api/reset
Reset all stored data

**Response:**
```json
{
    "status": "success",
    "message": "Data reset"
}
```

### GET /health
Health check endpoint

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00",
    "data_points": 50,
    "anomalies_detected": 5
}
```

## 📁 Project Structure

```
dashboard/
├── backend/
│   └── app.py              # Flask server
├── frontend/
│   └── index.html          # Dashboard UI
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔧 Troubleshooting

### Backend server won't start
- Ensure port 5000 is not in use: `lsof -i :5000`
- Check Python version: `python --version` (need 3.7+)
- Reinstall dependencies: `pip install -r requirements.txt`

### Frontend shows "Disconnected"
- Ensure backend server is running
- Check browser console for errors (F12)
- Verify API URL in index.html (line 485): `http://localhost:5000`
- Check CORS is enabled in backend

### No data appearing
- Verify data is being sent to correct endpoint
- Check backend terminal for incoming requests
- Use browser Network tab (F12) to inspect API calls
- Test with cURL or test script

### Charts not updating
- Click "Resume Auto-Refresh" button
- Check browser console for JavaScript errors
- Verify Chart.js library is loading (check Network tab)

## 🎯 Customization

### Change refresh rate
Edit `REFRESH_INTERVAL` in index.html (line 486):
```javascript
const REFRESH_INTERVAL = 2000; // 2 seconds
```

### Change data point limit
Edit `MAX_DATA_POINTS` in app.py (line 14):
```python
MAX_DATA_POINTS = 200  # Store last 200 points
```

### Change anomaly threshold
The threshold is set to 0.7. To change:
- Backend: Check line 62 in app.py
- Frontend: Check line 578 for chart threshold line

### Change port numbers
- Backend: Line 155 in app.py: `app.run(port=5000)`
- Frontend: Update API_URL in index.html

## 📝 Notes

- Data is stored **in-memory** - restarting the backend will clear all data
- Maximum 100 data points are kept for charts (configurable)
- All anomaly events are stored (no limit by default)
- Dashboard auto-refreshes every 1 second
- Works best with modern browsers (Chrome, Firefox, Edge)

## 🚀 Production Deployment

For production use, consider:
1. Using a production WSGI server (gunicorn, uWSGI)
2. Adding database storage (PostgreSQL, MongoDB)
3. Implementing authentication
4. Adding HTTPS/SSL
5. Using environment variables for configuration
6. Adding logging and monitoring

## 📄 License

This dashboard is part of the 5G-IoT Anomaly Detection System project.

## 🤝 Support

For issues or questions, please refer to the main project documentation.
