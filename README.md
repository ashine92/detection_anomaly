# Anomaly Detection in 5G-IoT Networks

Hệ thống phát hiện anomaly hoàn chỉnh cho mạng 5G-IoT, bao gồm phân tích dữ liệu, training model, và mô phỏng mạng realtime.

## 📋 Project Structure

```
detection_anomaly/
├── model/                          # Machine Learning Models
│   ├── decision_tree_model_*.pkl   # Trained Decision Tree
│   ├── scaler_*.pkl                # Feature scaler
│   └── feature_names_*.pkl         # Feature definitions
│
├── model development/              # Data Analysis & Training
│   └── explore-dataset.ipynb       # Jupyter notebook
│
└── system_detection/               # Network Simulation ⭐
    ├── 5g_iot_mininet.py          # Network topology
    ├── edge_server.py              # ML detection server
    ├── iot_station.py              # IoT sensor nodes
    ├── run_auto_simulation.py      # Auto-start script
    ├── quick_start.sh              # Quick start with monitoring
    ├── start_simulation.sh         # Tmux-based launcher
    ├── README.md                   # Chi tiết hướng dẫn
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
sudo apt install -y python3-sklearn python3-joblib python3-pandas
```

### 2. Chạy Simulation

```bash
cd detection_anomaly/system_detection
./quick_start.sh
```

Hoặc xem hướng dẫn đầy đủ trong [system_detection/README.md](system_detection/README.md)

## 📚 Components

### 1. Model Development
- **Location**: `model development/explore-dataset.ipynb`
- **Purpose**: Phân tích dataset, feature engineering, train models
- **Output**: Trained models trong folder `model/`

### 2. Network Simulation
- **Location**: `system_detection/`
- **Purpose**: Mô phỏng mạng 5G-IoT với Mininet-WiFi
- **Features**:
  - Edge computing architecture
  - Realtime anomaly detection
  - Multi-station support
  - Comprehensive logging

### 3. ML Models
- **Location**: `model/`
- **Models**: Decision Tree Classifier
- **Features**: 24 network traffic features
- **Classes**: Benign / Malicious

## 🎯 Use Cases

1. **Research**: Nghiên cứu anomaly detection trong mạng 5G-IoT
2. **Education**: Học về edge computing và ML deployment
3. **Testing**: Test ML models trong môi trường mạng mô phỏng
4. **Development**: Phát triển và đánh giá thuật toán mới

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Anomaly Detection System                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [Data Collection] → [Model Training] → [Deployment]    │
│         ↓                   ↓                  ↓         │
│   explore-dataset       model/         system_detection │
│      .ipynb             *.pkl           (Mininet-WiFi)  │
│                                                          │
│  Flow:                                                   │
│  1. Analyze network traffic data                        │
│  2. Train ML model (Decision Tree)                      │
│  3. Deploy on Edge Server                               │
│  4. Detect anomalies realtime in 5G-IoT network         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 🔧 Requirements

- **OS**: Ubuntu 20.04+ or WSL2
- **RAM**: 4GB+ (8GB recommended)
- **Python**: 3.8+
- **Mininet-WiFi**: 2.7
- **Jupyter**: For model development

## 📖 Documentation

- **Main Guide**: [system_detection/README.md](system_detection/README.md)
- **WSL2 Setup**: [system_detection/WINDOWS_WSL2_SETUP.md](system_detection/WINDOWS_WSL2_SETUP.md)
- **Model Development**: See Jupyter notebook in `model development/`

## 🛠️ Development Workflow

1. **Data Analysis** → Explore dataset using Jupyter notebook
2. **Model Training** → Train và save models vào `model/`
3. **Testing** → Test models trong simulation
4. **Tuning** → Adjust parameters và retrain nếu cần

## 📈 Performance

- **Latency**: < 10ms per prediction
- **Throughput**: 100+ requests/second
- **Accuracy**: Depends on model training (see notebook)

## 🎓 Learning Resources

Trong project này bạn sẽ học:
- Network simulation với Mininet-WiFi
- Edge computing architecture
- ML model deployment
- 5G-IoT concepts
- Python socket programming
- Realtime data processing

## 🐛 Troubleshooting

Xem [system_detection/README.md](system_detection/README.md) phần Troubleshooting.

Common issues:
- Mininet installation → See installation guide
- Network routing → Use `sudo mn -c` before start
- Model loading → Check sklearn version compatibility

## 📝 TODO / Future Work

- [ ] Thêm ML models: Random Forest, Neural Network
- [ ] Web dashboard cho monitoring
- [ ] Database integration (InfluxDB, MySQL)
- [ ] Support nhiều edge servers (distributed)
- [ ] Load balancing giữa các servers
- [ ] Advanced attack scenarios
- [ ] Performance benchmarking tools

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

**Getting Started**: Xem [system_detection/README.md](system_detection/README.md) để bắt đầu!
