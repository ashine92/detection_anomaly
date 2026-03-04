# Anomaly Detection in 5G-IoT Networks

Hệ thống phát hiện anomaly hoàn chỉnh cho mạng 5G-IoT với **Web Dashboard**, bao gồm phân tích dữ liệu, training model, mô phỏng mạng realtime, và monitoring UI.

## 📋 Project Structure

```
detection_anomaly/
├── dashboard/                      # 🌐 Web Monitoring Dashboard ⭐ NEW
│   ├── backend/                    # Flask REST API Server
│   │   ├── app.py                  # Main API endpoints
│   │   ├── config.py               # Configuration
│   │   ├── detection.py            # AI Anomaly Detector (4 metrics)
│   │   └── storage.py              # In-memory data storage
│   └── frontend/                   # HTML/CSS/JavaScript UI
│       └── index.html              # Real-time charts & stats
│
├── model/                          # 🤖 Machine Learning Models
│   ├── decision_tree_model_IMPROVED_*.pkl   # Trained Decision Tree (24 features)
│   ├── scaler_IMPROVED_*.pkl                # Feature StandardScaler
│   └── feature_names_IMPROVED_*.pkl         # Feature definitions
│
├── model_development/              # 📊 Data Analysis & Training
│   ├── explore-dataset.ipynb       # Original dataset exploration
│   └── retrain-model-improved.ipynb # Model training with hyperparameter tuning
│
├── dataset/                        # 📁 Training Dataset
│   └── Encoded.csv                 # 5G-IoT network traffic data
│
└── system_detection/               # 🔬 Network Simulation
    ├── 5g_iot_mininet.py          # Mininet-WiFi topology
    ├── edge_server_with_dashboard.py  # ML server + Dashboard integration ⭐
    ├── dashboard_client.py         # Dashboard API client
    ├── iot_station.py              # IoT sensor data generator
    ├── run_auto_simulation.py      # Auto-start script
    ├── quick_start.sh              # Quick start launcher
    ├── start_simulation.sh         # Tmux-based launcher
    ├── README.md                   # Detailed guide
    ├── QUICKSTART_REAL_DATA.md     # Quick reference
    └── WINDOWS_WSL2_SETUP.md       # WSL2 setup guide
```

## 🚀 Quick Start

### 1. Cài đặt Dependencies

```bash
# Install Mininet-WiFi
cd ~
git clone https://github.com/intrig-unicamp/mininet-wifi
cd mininet-wifi
sudo util/install.sh -Wlnfv

# Install Python packages
sudo apt install -y python3-sklearn python3-joblib python3-pandas python3-flask python3-flask-cors
```

### 2. Chạy Web Dashboard (Recommended)

```bash
# Terminal 1: Start Dashboard Backend
cd detection_anomaly/dashboard/backend
python3 app.py

# Terminal 2: Start Edge Server with Dashboard Integration
cd detection_anomaly/system_detection
python3 edge_server_with_dashboard.py ../model/decision_tree_model_IMPROVED_*.pkl ../model/scaler_IMPROVED_*.pkl

# Terminal 3: Run IoT Simulation
python3 iot_station.py sta1 2 0.2
```

**Access Dashboard**: Mở browser → `http://localhost:5000`

### 3. Hoặc Chạy Simulation Đơn Giản (Không Dashboard)

```bash
cd detection_anomaly/system_detection
./quick_start.sh
```

Xem hướng dẫn đầy đủ trong [system_detection/README.md](system_detection/README.md)

## 📚 Components

### 1. Web Dashboard (NEW!) 🌐
- **Location**: `dashboard/`
- **Purpose**: Real-time monitoring và visualization
- **Features**:
  - Real-time charts (throughput, latency, packet loss, RSSI)
  - AI-powered anomaly detection (4-metric lightweight model)
  - Device statistics và alerts
  - REST API endpoints (POST /metrics, GET /stats)
- **Tech Stack**: Flask 3.0 + Chart.js 4.4 + Clean Architecture
- **Port**: 5000 (backend và frontend)

### 2. Model Development 📊
- **Location**: `model_development/`
- **Purpose**: Phân tích dataset, feature engineering, train models
- **Files**:
  - `explore-dataset.ipynb` - Dataset exploration ban đầu
  - `retrain-model-improved.ipynb` - Model training với hyperparameter tuning
- **Output**: Trained models trong folder `model/`
- **Method**: GridSearchCV với Decision Tree (max_depth, min_samples tuning)

### 3. Network Simulation 🔬
- **Location**: `system_detection/`
- **Purpose**: Mô phỏng mạng 5G-IoT với Mininet-WiFi
- **Core Files**:
  - `5g_iot_mininet.py` - Network topology setup
  - `edge_server_with_dashboard.py` - Edge server + ML detection + Dashboard integration
  - `iot_station.py` - IoT sensor data generator (24 features)
  - `dashboard_client.py` - API client cho dashboard
- **Features**:
  - Edge computing architecture
  - Realtime anomaly detection (24-feature model)
  - Multi-station support
  - Dashboard integration (gửi metrics realtime)
  - Comprehensive logging

### 4. ML Models 🤖
- **Location**: `model/`
- **Model Type**: Decision Tree Classifier
- **Features**: 24 network traffic features (Seq, Mean, sTtl, TotBytes, etc.)
- **Classes**: Benign / Malicious
- **Version**: IMPROVED (với hyperparameter tuning)
- **Training**: GridSearchCV với class_weight='balanced'
- **Performance**: Test accuracy ~99%, Synthetic test 80%+

## 🗂️ File Roles - Chi Tiết

### Core System Files

| File | Vai trò | Khi nào dùng |
|------|---------|--------------|
| `dashboard/backend/app.py` | REST API server, routing, CORS | Luôn chạy nếu dùng dashboard |
| `dashboard/backend/detection.py` | AI detector 4-metric (lightweight) | Tự động gọi bởi app.py |
| `dashboard/backend/storage.py` | In-memory data store | Tự động gọi bởi app.py |
| `dashboard/frontend/index.html` | Web UI với Chart.js | Mở trong browser |
| `system_detection/edge_server_with_dashboard.py` | Edge ML server + dashboard integration | Main server cho simulation |
| `system_detection/iot_station.py` | Generate IoT traffic (24 features) | Test traffic generation |
| `system_detection/dashboard_client.py` | API client library | Import bởi edge_server |
| `system_detection/5g_iot_mininet.py` | Mininet topology (chưa dùng với dashboard) | Future: full network sim |

### Model Files

| File | Nội dung | Được tạo bởi |
|------|----------|--------------|
| `decision_tree_model_IMPROVED_*.pkl` | Trained Decision Tree (24 features) | retrain-model-improved.ipynb |
| `scaler_IMPROVED_*.pkl` | StandardScaler cho features | retrain-model-improved.ipynb |
| `feature_names_IMPROVED_*.pkl` | Tên 24 features | retrain-model-improved.ipynb |

### Development Files

| File | Purpose | Dùng khi |
|------|---------|----------|
| `model_development/explore-dataset.ipynb` | Dataset EDA, initial training | Khám phá dataset lần đầu |
| `model_development/retrain-model-improved.ipynb` | Model training với tuning | Retrain model sau khi có dataset mới |
| `dataset/Encoded.csv` | Training data (5G-IoT traffic) | Input cho model training |

### Documentation Files

| File | Nội dung |
|------|----------|
| `README.md` | Tổng quan project (file này) |
| `system_detection/README.md` | Chi tiết simulation setup |
| `system_detection/QUICKSTART_REAL_DATA.md` | Quick reference guide |
| `system_detection/FILES_OVERVIEW.md` | File structure details |
| `system_detection/WINDOWS_WSL2_SETUP.md` | WSL2 installation guide |
| `system_detection/CHANGELOG.md` | Version history |

## � Dashboard Features

**Real-time Visualization**
- 📊 4 real-time charts: Throughput, Latency, Packet Loss, RSSI
- 📈 Auto-updating every 1 second
- 🎯 Color-coded metrics (green=good, yellow=warning, red=critical)

**AI Detection**
- 🤖 Dual-layer detection:
  - Edge Server: 24-feature Decision Tree (deep analysis)
  - Dashboard: 4-metric AI detector (lightweight, real-time)
- ⚡ Adaptive thresholds based on traffic patterns
- 📍 Per-device tracking

**Statistics**
- 📊 Total devices, metrics received
- ⚠️ Anomaly count và detection rate
- 🔴 Real-time alerts cho anomalies
- 📋 Latest 10 metrics trong table

**API Endpoints**
- `POST /metrics` - Receive metrics từ edge server
- `GET /stats` - Get current statistics
- `GET /` - Serve dashboard UI

## �🎯 Use Cases

1. **Research**: Nghiên cứu anomaly detection trong mạng 5G-IoT
2. **Education**: Học về edge computing, ML deployment, web dashboard
3. **Testing**: Test ML models trong môi trường mạng mô phỏng
4. **Development**: Phát triển và đánh giá thuật toán mới
5. **Monitoring**: Real-time visualization và alerting system

## 📊 System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│               5G-IoT ANOMALY DETECTION SYSTEM                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐   │
│  │   Dataset    │  →   │    Model     │  →   │ Deployment   │   │
│  │  (CSV File)  │      │  Training    │      │ (Edge+Dash)  │   │
│  └──────────────┘      └──────────────┘      └──────────────┘   │
│        ↓                      ↓                      ↓            │
│   dataset/            model_development/     system_detection/   │
│  Encoded.csv         retrain-model-         edge_server_with_    │
│  (Training)          improved.ipynb         dashboard.py         │
│                      (GridSearchCV)                               │
│                           ↓                                       │
│                      model/                                       │
│                   decision_tree_                                  │
│                   IMPROVED_*.pkl                                  │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                    RUNTIME ARCHITECTURE                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────┐                                                  │
│  │ IoT Station │  [24 features]                                   │
│  │ (sta1, sta2)│ ───────────┐                                     │
│  └─────────────┘            │                                     │
│        │                    ↓                                     │
│        │            ┌──────────────────┐                          │
│        │            │   Edge Server    │  [Port 5001]             │
│        │            │  + ML Detection  │                          │
│        │            │  (24-feature DT) │                          │
│        │            └────────┬─────────┘                          │
│        │                     │                                    │
│        │                     │ POST /metrics                      │
│        │                     ↓                                    │
│        │            ┌──────────────────┐                          │
│        │            │  Web Dashboard   │  [Port 5000]             │
│        └───────────→│  + AI Detection  │                          │
│     [4 metrics]     │  (4-metric AI)   │                          │
│                     └────────┬─────────┘                          │
│                              │                                    │
│                              ↓                                    │
│                     ┌─────────────────┐                          │
│                     │  Browser UI     │                          │
│                     │  (Charts/Stats) │                          │
│                     └─────────────────┘                          │
│                                                                    │
│  Flow:                                                             │
│  1. IoT Stations generate traffic (Normal/Attack patterns)        │
│  2. Edge Server detects với 24-feature ML model                   │
│  3. Send metrics to Dashboard API (throughput, latency, etc.)     │
│  4. Dashboard AI detects anomalies (4 metrics - lightweight)      │
│  5. Real-time visualization trên browser                          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow

1. **IoT Station** → Generate 24 features (Seq, sTtl, TotBytes, RST...)
2. **Edge Server** → ML prediction (Benign/Malicious) → Send to Dashboard
3. **Dashboard** → Receive metrics → AI detection → Store → Visualize
4. **Browser** → Real-time charts update every second

## 🔧 Requirements

- **OS**: Ubuntu 20.04+ or WSL2
- **RAM**: 4GB+ (8GB recommended for model training)
- **Python**: 3.8+
- **Mininet-WiFi**: 2.7
- **Python Packages**:
  - scikit-learn 1.4.1+ (ML models)
  - Flask 3.0+ (Dashboard backend)
  - flask-cors (API CORS support)
  - pandas, numpy (Data processing)
  - joblib (Model persistence)
- **Browser**: Chrome/Firefox (for Dashboard UI)
- **Jupyter**: For model development (optional)

## 📖 Documentation

- **Main Guide**: [system_detection/README.md](system_detection/README.md)
- **Quick Reference**: [system_detection/QUICKSTART_REAL_DATA.md](system_detection/QUICKSTART_REAL_DATA.md)
- **WSL2 Setup**: [system_detection/WINDOWS_WSL2_SETUP.md](system_detection/WINDOWS_WSL2_SETUP.md)
- **File Overview**: [system_detection/FILES_OVERVIEW.md](system_detection/FILES_OVERVIEW.md)
- **Model Training**: See Jupyter notebooks in `model_development/`

## 🛠️ Development Workflow

1. **Data Analysis** → Explore dataset using Jupyter notebook
2. **Model Training** → Train và save models vào `model/`
3. **Testing** → Test models trong simulation
4. **Tuning** → Adjust parameters và retrain nếu cần

## 📈 Performance

**Edge Server (24-feature ML Model)**
- Latency: < 10ms per prediction
- Throughput: 100+ requests/second
- Test Accuracy: ~99% (on training dataset)
- Synthetic Test: 80%+ (attack pattern detection)

**Dashboard AI (4-metric Detector)**
- Detection Rate: 70-90% on real traffic
- Response Time: Real-time (< 100ms)
- False Positive: Low (adaptive thresholds)

**System Resources**
- CPU: ~5-10% (idle), 20-30% (active simulation)
- Memory: ~500MB total
- Network: Minimal overhead

## 🎓 Learning Resources

Trong project này bạn sẽ học:
- **Network Simulation**: Mininet-WiFi, SDN concepts
- **Edge Computing**: Distributed architecture, low-latency processing
- **ML Deployment**: Model serving, feature engineering, hyperparameter tuning
- **Web Development**: Flask REST API, Chart.js, real-time data
- **5G-IoT Concepts**: Network features, traffic analysis
- **Python**: Socket programming, async processing, clean architecture
- **Data Processing**: Pandas, StandardScaler, feature normalization
- **DevOps**: Multi-process management, logging, monitoring

## 🐛 Troubleshooting

Xem [system_detection/README.md](system_detection/README.md) phần Troubleshooting.

Common issues:
- Mininet installation → See installation guide
- Network routing → Use `sudo mn -c` before start
- Model loading → Check sklearn version compatibility

## 📝 TODO / Future Work

**Completed ✅**
- [x] Web dashboard cho monitoring (Flask + Chart.js)
- [x] AI-powered anomaly detection (dual-model architecture)
- [x] Model hyperparameter tuning (GridSearchCV)
- [x] Dashboard integration với edge server
- [x] Real-time visualization
- [x] Clean architecture (backend separation)

**In Progress / Future**
- [ ] Thêm ML models: Random Forest, Neural Network, XGBoost
- [ ] Database integration (InfluxDB, MySQL) thay cho in-memory
- [ ] Support nhiều edge servers (distributed architecture)
- [ ] Load balancing giữa các servers
- [ ] Advanced attack scenarios (DDoS variants, zero-day)
- [ ] Performance benchmarking tools
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Authentication & Authorization
- [ ] Alert notifications (email, Slack, webhook)

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Model accuracy tuning
- Additional attack patterns
- Visualization improvements
- Documentation enhancements
- Performance optimizations

## 📄 License

Educational project - Free to use with attribution

## 👥 Authors

IoT Security Research - 2026

---

**Getting Started**: 
- 🌐 **Web Dashboard**: Xem phần [Quick Start](#-quick-start) để chạy dashboard
- 🔬 **Simulation**: Xem [system_detection/README.md](system_detection/README.md) để setup Mininet
- 🤖 **Model Training**: Xem [model_development/retrain-model-improved.ipynb](model_development/retrain-model-improved.ipynb)

**Support**: Mở browser → `http://localhost:5000` để xem dashboard!
