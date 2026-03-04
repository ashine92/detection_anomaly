# Project Files Overview

## Core Files (Sử dụng chính)

### Network Simulation Scripts

1. **5g_iot_mininet.py**
   - Định nghĩa topology mạng 5G-IoT
   - Tạo Edge Server, Access Point, IoT Stations
   - Cung cấp Mininet CLI cho manual control
   - Sử dụng: `sudo python3 5g_iot_mininet.py`

2. **edge_server.py**
   - Edge Computing server với ML model
   - Socket server listen trên port 5000
   - Load Decision Tree model để phát hiện anomaly
   - Xử lý requests từ IoT stations và trả về predictions
   - Sử dụng: `python3 edge_server.py <model.pkl> <scaler.pkl>`

3. **iot_station.py**
   - Giả lập IoT sensor node
   - Generate network traffic data (24 features)
   - Gửi data đến Edge Server qua TCP
   - Có thể config anomaly rate
   - Sử dụng: `python3 iot_station.py <id> <interval> <anomaly_rate>`

### Automation Scripts

4. **run_auto_simulation.py** ⭐ (Recommended)
   - Auto-start toàn bộ simulation
   - Khởi động edge server và stations tự động
   - Topology đã fix (direct link, no switch)
   - Logs vào /tmp/*.log
   - Sử dụng: `sudo python3 run_auto_simulation.py`

5. **quick_start.sh** 🚀 (Easiest)
   - Wrapper script cho run_auto_simulation.py
   - Tự động cleanup, start, và monitor
   - Hiển thị logs + statistics realtime
   - Loop monitoring mỗi 5 giây
   - Sử dụng: `./quick_start.sh`

6. **start_simulation.sh**
   - Legacy script sử dụng tmux
   - Start multiple terminals trong tmux session
   - Phù hợp nếu muốn xem từng component riêng
   - Sử dụng: `sudo ./start_simulation.sh`

## Documentation Files

7. **README.md**
   - Hướng dẫn đầy đủ về project
   - Installation guide
   - Usage examples
   - Troubleshooting
   - **ĐỌC FILE NÀY TRƯỚC!**

8. **WINDOWS_WSL2_SETUP.md**
   - Hướng dẫn cài đặt cho Windows users
   - WSL2 setup instructions
   - File copy methods
   - Tmux usage guide

9. **README_OLD.md**
   - README phiên bản cũ (reference only)
   - Có thể xóa nếu không cần

## Model Files (trong ../model/)

10. **decision_tree_model_*.pkl**
    - Trained Decision Tree Classifier
    - Input: 24 network features
    - Output: Benign / Malicious

11. **scaler_*.pkl**
    - StandardScaler cho feature normalization
    - Transform features before prediction

12. **feature_names_*.pkl**
    - Tên các features (24 features)
    - Reference cho data generation

## Recommended Workflow

### For First-Time Users:
```bash
# 1. Đọc README.md
cat README.md

# 2. Cleanup
sudo mn -c

# 3. Quick start
./quick_start.sh
```

### For Development:
```bash
# 1. Manual control với Mininet CLI
sudo python3 5g_iot_mininet.py

# 2. Trong CLI, start components:
mininet-wifi> xterm edge1
mininet-wifi> xterm sta1
mininet-wifi> xterm sta2
```

### For Testing:
```bash
# Auto mode với logs
sudo python3 run_auto_simulation.py

# Monitor trong terminal khác:
tail -f /tmp/edge_server.log
tail -f /tmp/sta1.log
```

## Files To Ignore/Delete

- **README_OLD.md** - Old documentation (can delete)
- **/tmp/*.log** - Runtime logs (clear after use)
- **mn*.apconf** - Temporary Mininet files (already deleted)

## Key Differences Between Scripts

| Feature | quick_start.sh | run_auto_simulation.py | 5g_iot_mininet.py | start_simulation.sh |
|---------|---------------|----------------------|------------------|-------------------|
| Auto-start | ✅ | ✅ | ❌ Manual | ✅ (tmux) |
| Monitoring | ✅ Realtime | ❌ Check logs | ❌ | ❌ |
| CLI Access | ❌ | ✅ | ✅ | ✅ (per window) |
| Complexity | 🟢 Easy | 🟡 Medium | 🔴 Advanced | 🟡 Medium |
| Best For | Quick demo | Auto testing | Development | Multi-terminal |

## Quick Reference Commands

```bash
# Cleanup network
sudo mn -c

# Quick start (recommended)
./quick_start.sh

# Auto mode
sudo python3 run_auto_simulation.py

# Manual mode
sudo python3 5g_iot_mininet.py

# View logs
tail -f /tmp/edge_server.log
sudo grep "ALERT" /tmp/edge_server.log

# Statistics
sudo grep -c "Request" /tmp/edge_server.log
sudo grep -c "Malicious" /tmp/edge_server.log

# Kill processes
sudo pkill -f "python3.*iot_station"
sudo pkill -f "python3.*edge_server"
```

## File Dependencies

```
run_auto_simulation.py
├── requires: 5g_iot_mininet.py (topology logic)
├── calls: edge_server.py (on edge1 node)
├── calls: iot_station.py (on sta1, sta2 nodes)
└── needs: ../model/*.pkl files

quick_start.sh
└── calls: run_auto_simulation.py

start_simulation.sh
├── calls: 5g_iot_mininet.py
├── calls: edge_server.py
└── calls: iot_station.py
```

## Important Notes

1. **Always cleanup before start**: `sudo mn -c`
2. **Check logs for errors**: `/tmp/edge_server.log`
3. **Port 5000 must be free**: Edge server port
4. **Run with sudo**: Mininet requires root
5. **Model files required**: Must be in ../model/

## Getting Help

- Read README.md for detailed guide
- Check /tmp/*.log files for errors
- Use `sudo mn -c` to reset network
- See Troubleshooting section in README.md
