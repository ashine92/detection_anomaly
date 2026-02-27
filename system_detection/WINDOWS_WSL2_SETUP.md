# Hướng dẫn chạy mô phỏng trên Windows (WSL2)

## Bước 1: Cài đặt WSL2 Ubuntu

1. Mở PowerShell với quyền Administrator:
```powershell
wsl --install -d Ubuntu-22.04
```

2. Khởi động lại máy tính

3. Mở Ubuntu từ Start Menu, tạo username/password

## Bước 2: Cài đặt Mininet-WiFi trong WSL2

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y git make gcc python3 python3-pip

# Clone Mininet-WiFi
cd ~
git clone https://github.com/intrig-unicamp/mininet-wifi
cd mininet-wifi

# Install Mininet-WiFi
sudo util/install.sh -Wlnfv

# Test installation
sudo mn --wifi --test pingall
```

## Bước 3: Cài đặt Python packages

```bash
pip3 install scikit-learn numpy joblib pandas matplotlib seaborn
```

## Bước 4: Copy files từ Windows vào WSL2

Files cần copy:
- `5g_iot_mininet.py`
- `edge_server.py`  
- `iot_station.py`
- `decision_tree_model_20260227_205406.pkl`
- `scaler_20260227_205406.pkl`
- `feature_names_20260227_205406.pkl`
- `start_simulation.sh`

### Cách 1: Qua Windows filesystem
```bash
# Windows filesystem được mount tại /mnt/
cd ~
mkdir 5g-iot-project
cd 5g-iot-project

# Copy từ Windows (thay đổi đường dẫn phù hợp)
cp /mnt/d/Study/DH/"IoT in 5G"/*.py .
cp /mnt/d/Study/DH/"IoT in 5G"/*.pkl .
cp /mnt/d/Study/DH/"IoT in 5G"/*.sh .
```

### Cách 2: Dùng VS Code với WSL extension
1. Cài đặt extension "WSL" trong VS Code
2. Ctrl+Shift+P → "WSL: Connect to WSL"
3. Copy files qua File Explorer

## Bước 5: Chạy mô phỏng

### Option A: Tự động (khuyến nghị)
```bash
cd ~/5g-iot-project
chmod +x start_simulation.sh
sudo ./start_simulation.sh
```

### Option B: Thủ công

**Terminal 1** - Mininet-WiFi:
```bash
sudo python3 5g_iot_mininet.py
```

**Terminal 2** - Edge Server (trong Mininet CLI):
```bash
mininet-wifi> xterm edge1
# Trong terminal edge1:
python3 edge_server.py decision_tree_model_20260227_205406.pkl scaler_20260227_205406.pkl
```

**Terminal 3** - IoT Station 1:
```bash
mininet-wifi> xterm sta1
# Trong terminal sta1:
python3 iot_station.py sta1 2 0.2
```

**Terminal 4** - IoT Station 2:
```bash
mininet-wifi> xterm sta2
# Trong terminal sta2:
python3 iot_station.py sta2 3 0.15
```

## Bước 6: Kiểm tra kết quả

### Kiểm tra kết nối
Trong Mininet CLI:
```bash
mininet-wifi> sta1 ping -c 3 edge1
mininet-wifi> sta1 ping -c 3 sta2
```

### Quan sát logs
- **Edge Server**: Hiển thị requests và predictions
- **Stations**: Hiển thị packets và responses

## Dừng mô phỏng

```bash
# Tắt từng terminal: Ctrl+C
# Thoát Mininet: exit
# Clean up
sudo mn -c
```

## Troubleshooting

### Lỗi: X11 display not found
```bash
export DISPLAY=:0
```

### Lỗi: Cannot connect to edge server
Kiểm tra firewall trong WSL2:
```bash
sudo ufw status
sudo ufw allow 5000/tcp
```

### Lỗi: Model file not found
Kiểm tra đường dẫn:
```bash
ls -la *.pkl
pwd
```

### Lỗi: Permission denied
```bash
sudo python3 5g_iot_mininet.py
```

## Network Architecture

```
Windows 10/11
    │
    │ WSL2
    ▼
┌───────────────────────────────────┐
│  Ubuntu 22.04 (WSL2)              │
│                                   │
│  ┌─────────────────────────────┐ │
│  │   Mininet-WiFi Network      │ │
│  │                             │ │
│  │  Edge Server ←→ AP ←→ Stations│ │
│  │  (10.0.0.100)   │   (sta1/2)│ │
│  └─────────────────────────────┘ │
│                                   │
└───────────────────────────────────┘
```

## Monitoring với tmux

Nếu dùng `start_simulation.sh`:
```bash
# Attach vào session
tmux attach -t 5g-iot-sim

# Switch giữa các windows
Ctrl+B rồi nhấn số: 0, 1, 2, 3

# Detach (không tắt)
Ctrl+B rồi nhấn d

# Kill session
tmux kill-session -t 5g-iot-sim
```

## Visualization (Optional)

Để xem network trong GUI:
```bash
# Install X server cho Windows
# Download VcXsrv: https://sourceforge.net/projects/vcxsrv/

# Configure DISPLAY in WSL
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0

# Run với GUI
sudo python3 5g_iot_mininet.py
```

## Performance Tips

1. Tăng RAM cho WSL2: Tạo file `.wslconfig` trong `C:\Users\<username>\`:
```
[wsl2]
memory=4GB
processors=2
```

2. Restart WSL:
```powershell
wsl --shutdown
wsl
```

## Next Steps

1. Thử nghiệm với anomaly rates khác nhau
2. Thu thập metrics để phân tích
3. Tùy chỉnh network topology
4. Thêm nhiều IoT stations

## Tài liệu tham khảo

- Mininet-WiFi: http://mininet-wifi.github.io/
- WSL2: https://docs.microsoft.com/en-us/windows/wsl/
- 5G-NIDD Dataset: https://ieee-dataport.org/documents/5g-nidd-comprehensive-network-intrusion-detection-dataset
