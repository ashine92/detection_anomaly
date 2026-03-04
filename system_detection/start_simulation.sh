#!/bin/bash
# Automated 5G-IoT Mininet-WiFi Simulation Launcher
# Sử dụng tmux để chạy multiple terminals

echo "======================================================================"
echo "5G-IoT Network Simulation with Mininet-WiFi"
echo "======================================================================"

# Kiểm tra tmux
if ! command -v tmux &> /dev/null; then
    echo "Installing tmux..."
    sudo apt-get update
    sudo apt-get install -y tmux
fi

# Kiểm tra Mininet-WiFi
if ! sudo mn --version &> /dev/null; then
    echo "Error: Mininet not installed!"
    echo "Please install Mininet-WiFi first:"
    echo "  git clone https://github.com/intrig-unicamp/mininet-wifi"
    echo "  cd mininet-wifi && sudo util/install.sh -Wlnfv"
    exit 1
fi

# Kiểm tra model files
MODEL_FILE="/home/ashine/Downloads/detection_anomaly/model/decision_tree_model_20260227_205406.pkl"
SCALER_FILE="/home/ashine/Downloads/detection_anomaly/model/scaler_20260227_205406.pkl"

if [ ! -f "$MODEL_FILE" ]; then
    echo "Error: Model file not found: $MODEL_FILE"
    exit 1
fi

if [ ! -f "$SCALER_FILE" ]; then
    echo "Error: Scaler file not found: $SCALER_FILE"
    exit 1
fi

echo ""
echo "Starting simulation..."
echo ""

# Tạo tmux session
SESSION="5g-iot-sim"
tmux new-session -d -s $SESSION

# Window 0: Mininet-WiFi
tmux rename-window -t $SESSION:0 'Mininet'
tmux send-keys -t $SESSION:0 "sudo python3 5g_iot_mininet.py" C-m

# Đợi Mininet khởi động
sleep 5

# Window 1: Edge Server
tmux new-window -t $SESSION:1 -n 'Edge-Server'
tmux send-keys -t $SESSION:1 "python3 edge_server.py $MODEL_FILE $SCALER_FILE" C-m

# Đợi Edge Server khởi động
sleep 2

# Window 2: IoT Station 1
tmux new-window -t $SESSION:2 -n 'Station-1'
tmux send-keys -t $SESSION:2 "python3 iot_station.py sta1 2 0.2" C-m

# Window 3: IoT Station 2
tmux new-window -t $SESSION:3 -n 'Station-2'
tmux send-keys -t $SESSION:3 "python3 iot_station.py sta2 3 0.15" C-m

echo "======================================================================"
echo "Simulation started!"
echo "======================================================================"
echo ""
echo "Tmux windows:"
echo "  0: Mininet-WiFi topology"
echo "  1: Edge Server (ML detection)"
echo "  2: IoT Station 1 (20% anomaly)"
echo "  3: IoT Station 2 (15% anomaly)"
echo ""
echo "Commands:"
echo "  tmux attach -t $SESSION    # Attach to session"
echo "  Ctrl+B then number         # Switch windows"
echo "  Ctrl+B then d              # Detach from session"
echo "  tmux kill-session -t $SESSION  # Stop all"
echo ""
echo "======================================================================"

# Attach to session
tmux attach -t $SESSION
