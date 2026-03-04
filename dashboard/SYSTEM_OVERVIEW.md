# 🛡️ 5G-IoT ANOMALY DETECTION SYSTEM - COMPLETE GUIDE

## 📂 CẤU TRÚC DỰ ÁN HOÀN CHỈNH

```
detection_anomaly/
│
├── model/                                  # AI Models
│   ├── decision_tree_model_*.pkl          # Trained Decision Tree
│   ├── scaler_*.pkl                       # Feature scaler
│   └── feature_names_*.pkl                # Feature names
│
├── system_detection/                       # Mininet simulation
│   ├── 5g_iot_mininet.py
│   ├── edge_server.py
│   ├── iot_station.py
│   └── ...
│
└── dashboard/                              # 🆕 DASHBOARD SYSTEM (Clean Architecture)
    │
    ├── backend/                            # Backend API
    │   ├── app.py                         # ✅ Flask routes (main entry)
    │   ├── config.py                      # ✅ Configuration
    │   ├── detection.py                   # ✅ AI anomaly detection
    │   ├── storage.py                     # ✅ Data storage layer
    │   └── app_old.py                     # 📦 Backup
    │
    ├── frontend/                           # Frontend UI
    │   ├── index.html                     # ✅ Improved dashboard
    │   └── index_old.html                 # 📦 Backup
    │
    ├── requirements.txt                    # Python dependencies
    ├── test_dashboard.py                   # Test data generator
    ├── dashboard_integration.py            # Integration examples
    ├── start_dashboard.sh                  # Quick start script
    │
    ├── README.md                           # ⭐ Main documentation
    ├── ARCHITECTURE.md                     # 📘 Architecture details
    ├── QUICKSTART.md                       # 🚀 Quick start guide
    └── SYSTEM_OVERVIEW.md                  # 📋 This file
```

---

## 🎯 CLEAN ARCHITECTURE OVERVIEW

### Kiến trúc phân tầng (Layered Architecture)

```
┌─────────────────────────────────────────────────┐
│          FRONTEND LAYER (Presentation)          │
│                                                 │
│  • index.html - Dashboard UI                   │
│  • Chart.js visualization                      │
│  • Real-time updates (2s interval)             │
│  • Responsive design                           │
└─────────────────────────────────────────────────┘
                      ↕ HTTP/REST API
┌─────────────────────────────────────────────────┐
│           API LAYER (Routes)                    │
│                                                 │
│  • app.py                                      │
│    - POST /api/metrics  (receive + detect)     │
│    - GET  /api/metrics  (get dashboard data)   │
│    - POST /api/reset    (reset all data)       │
│    - GET  /health       (health check)         │
└─────────────────────────────────────────────────┘
                      ↕
┌─────────────────────────────────────────────────┐
│         BUSINESS LOGIC LAYER                    │
│                                                 │
│  • detection.py - AI Anomaly Detection         │
│    - Load trained model                        │
│    - Preprocess features                       │
│    - Predict anomaly (0-1 score)              │
│    - Classify severity                         │
└─────────────────────────────────────────────────┘
                      ↕
┌─────────────────────────────────────────────────┐
│         DATA LAYER (Storage)                    │
│                                                 │
│  • storage.py - Data Management                │
│    - In-memory storage (FIFO queues)           │
│    - Metrics data (max 100 points)             │
│    - Anomaly events (max 200 events)           │
│    - Statistics calculation                    │
└─────────────────────────────────────────────────┘
                      ↕
┌─────────────────────────────────────────────────┐
│         CONFIGURATION LAYER                     │
│                                                 │
│  • config.py - Centralized Config              │
│    - Model paths                               │
│    - Server settings                           │
│    - Thresholds                                │
└─────────────────────────────────────────────────┘
```

---

## 🔄 DATA FLOW (Luồng dữ liệu)

### 1. Receive Metrics Flow

```
IoT Device/Simulation
       ↓
   Send POST /api/metrics
   {
       "timestamp": "...",
       "device_id": "IoT_Device_1",
       "throughput": 45.5,
       "latency": 12.3,
       "packet_loss": 0.5,
       "rssi": -65
   }
       ↓
   app.py (validate input)
       ↓
   detection.py (AI analysis)
       → preprocess_data()
       → model.predict()
       → calculate anomaly_score
       → classify severity
       ↓
   storage.py (save data)
       → add_metric()
       → add_anomaly_event() if anomaly
       → update_statistics()
       ↓
   Return Response
   {
       "status": "success",
       "detection": {
           "prediction_label": "normal",
           "anomaly_score": 0.234,
           "severity": "low"
       }
   }
```

### 2. Dashboard Data Flow

```
Browser (Frontend)
       ↓
   GET /api/metrics (every 2 seconds)
       ↓
   app.py (route handler)
       ↓
   storage.py (get_dashboard_data)
       → get_all_metrics()
       → get_anomaly_events()
       → get_statistics()
       ↓
   Return JSON
   {
       "metrics": [...],
       "anomaly_events": [...],
       "statistics": {...},
       "counts": {...}
   }
       ↓
   Frontend (index.html)
       → updateDashboard()
       → updateCharts()
       → updateTables()
       → updateStatistics()
```

---

## 🤖 AI DETECTION PIPELINE

```
Input Metrics
    ↓
[1] Feature Extraction
    • throughput
    • latency
    • packet_loss
    • rssi
    ↓
[2] Preprocessing
    • Convert to numpy array
    • Scale using trained scaler
    • Reshape for model input
    ↓
[3] Model Prediction
    • Decision Tree Classifier
    • Input: 4 features
    • Output: class (0=normal, 1=anomaly)
    • Probability: anomaly score (0-1)
    ↓
[4] Post-processing
    • Convert prediction to label
    • Calculate severity:
      - Critical: score >= 0.9
      - High: score >= 0.7
      - Medium: score >= 0.5
      - Low: score < 0.5
    ↓
Output Detection Result
    • prediction_label
    • anomaly_score
    • severity
    • is_anomaly
```

---

## 📊 MODULES BREAKDOWN

### 1. **app.py** (275 lines)
**Vai trò**: API endpoint handler
**Responsibilities**:
- Nhận HTTP requests
- Validate input data
- Orchestrate detection + storage
- Return responses

**Key Functions**:
```python
index()             # Serve frontend HTML
receive_metrics()   # POST - Receive + detect metrics
get_metrics()       # GET - Get dashboard data
reset_data()        # POST - Reset all data
health_check()      # GET - Health check
```

---

### 2. **detection.py** (250 lines)
**Vai trò**: AI anomaly detection
**Responsibilities**:
- Load trained models
- Preprocess input features
- Run predictions
- Calculate anomaly scores

**Key Functions**:
```python
_load_model()       # Load model files
preprocess_data()   # Normalize features
predict()           # Run model prediction
analyze_metrics()   # Complete analysis
```

---

### 3. **storage.py** (200 lines)
**Vai trò**: Data management
**Responsibilities**:
- Store metrics in memory
- Track anomaly events
- Calculate statistics
- Provide data access

**Key Functions**:
```python
add_metric()           # Add metric data
add_anomaly_event()    # Log anomaly
get_all_metrics()      # Get all data
get_dashboard_data()   # Get complete package
reset_all()            # Clear everything
```

---

### 4. **config.py** (60 lines)
**Vai trò**: Configuration
**Responsibilities**:
- Centralize all configs
- Environment settings
- Model paths
- Thresholds

**Key Configs**:
```python
HOST, PORT              # Server config
MAX_DATA_POINTS         # Storage limits
MODEL_PATH              # AI model paths
ANOMALY_THRESHOLD       # Detection threshold
REFRESH_INTERVAL        # Frontend config
```

---

### 5. **index.html** (800 lines)
**Vai trò**: Dashboard UI
**Responsibilities**:
- Display real-time data
- Visualize with charts
- Show statistics
- Auto-refresh

**Key Sections**:
```html
- Header with system status
- 6 Statistics cards
- 3 Real-time charts
- 2 Event tables
- Control buttons
- Auto-refresh logic
```

---

## 🚀 QUICK START COMMANDS

```bash
# 1. Install dependencies
cd dashboard
pip install -r requirements.txt

# 2. Start backend (Terminal 1)
cd backend
python app.py

# 3. Open dashboard (Browser)
http://localhost:5000

# 4. Test with data (Terminal 2)
cd dashboard
python test_dashboard.py
```

---

## 📈 FEATURES COMPARISON

### Before (Old Version)
- ❌ No AI detection integration
- ❌ Manual anomaly score input required
- ❌ Monolithic code structure
- ❌ Basic UI design
- ❌ 1 second refresh (too fast)

### After (New Version - Clean Architecture)
- ✅ **Automatic AI detection** using trained model
- ✅ **Clean architecture** (app/detection/storage/config)
- ✅ **Improved UI** with better design
- ✅ **Severity levels** (critical/high/medium/low)
- ✅ **2 second refresh** (optimal)
- ✅ **Better error handling**
- ✅ **Comprehensive documentation**

---

## 🎯 USE CASES

### 1. Development & Testing
```bash
# Use mock detection if no model
MODEL_TYPE = 'mock'  # in config.py
```

### 2. Production with Trained Model
```bash
# Use trained model
MODEL_TYPE = 'trained'  # in config.py
MODEL_PATH = 'path/to/model.pkl'
```

### 3. Integration with Mininet Simulation
```python
from dashboard_integration import DashboardClient

dashboard = DashboardClient()
dashboard.send_metrics(device_id, throughput, latency, ...)
```

---

## 📚 DOCUMENTATION FILES

| File | Purpose |
|------|---------|
| **README.md** | Main documentation with full details |
| **ARCHITECTURE.md** | Clean architecture explanation |
| **QUICKSTART.md** | Quick start guide (3 minutes) |
| **SYSTEM_OVERVIEW.md** | This file - High-level overview |

---

## 🔮 FUTURE ENHANCEMENTS

### Backend
- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] WebSocket for real-time push
- [ ] User authentication
- [ ] API rate limiting
- [ ] Caching with Redis

### Frontend
- [ ] Advanced visualizations
- [ ] Export data (CSV/Excel)
- [ ] Customizable layouts
- [ ] Dark/Light theme toggle
- [ ] Mobile app

### AI/ML
- [ ] Model retraining pipeline
- [ ] Ensemble models
- [ ] Online learning
- [ ] Explainable AI
- [ ] Predictive analytics

---

## ✅ CHECKLIST

Hệ thống đã hoàn thành:
- ✅ Clean architecture với 4 modules tách biệt
- ✅ AI anomaly detection tích hợp sẵn
- ✅ Dashboard UI hiện đại, responsive
- ✅ Real-time updates (2 second interval)
- ✅ Statistics tracking & visualization
- ✅ Severity classification (4 levels)
- ✅ Event logging (anomalies + metrics)
- ✅ Test data generator
- ✅ Comprehensive documentation
- ✅ Integration examples
- ✅ Quick start guide

---

## 📞 SUPPORT

Nếu gặp vấn đề:
1. ✅ Read **QUICKSTART.md** for quick setup
2. ✅ Check **ARCHITECTURE.md** for details
3. ✅ Review code comments in files
4. ✅ Test with `test_dashboard.py`
5. ✅ Check backend logs in terminal

---

**Version**: 2.0 - Clean Architecture Edition  
**Last Updated**: March 4, 2026  
**Status**: ✅ Production Ready
