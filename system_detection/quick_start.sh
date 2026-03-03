#!/bin/bash
# Quick Start Script cho 5G-IoT Anomaly Detection Simulation

echo "=============================================================="
echo "  5G-IoT Anomaly Detection - Quick Start"
echo "=============================================================="
echo

# Cleanup trước
echo "[1/3] Cleaning up old network..."
sudo mn -c 2>&1 | grep "Cleanup complete"

echo
echo "[2/3] Starting simulation..."
echo "    - Edge Server: 10.0.0.100:5000"
echo "    - IoT Station 1: sending every 2s (20% anomaly rate)"
echo "    - IoT Station 2: sending every  3s (15% anomaly rate)"
echo

# Chạy simulation
cd "$(dirname "$0")"
sudo python3 run_auto_simulation.py &
SIM_PID=$!

# Đợi simulation khởi động
sleep 15

echo
echo "[3/3] Monitoring logs..."
echo "=============================================================="
echo

# Monitor logs
for i in {1..20}; do
    clear
    echo "=============================================================="
    echo "  5G-IoT Simulation Monitor (Update #$i)"
    echo "  Press Ctrl+C to stop"
    echo "=============================================================="
    echo
    echo "--- EDGE SERVER (Latest 10 requests) ---"
    sudo tail -10 /tmp/edge_server.log 2>/dev/null | grep "Request\|Prediction\|ALERT" || echo "No logs yet..."
    echo
    echo "--- STATISTICS ---"
    TOTAL=$(sudo grep -c "Request from" /tmp/edge_server.log 2>/dev/null || echo "0")
    BENIGN=$(sudo grep -c "Benign" /tmp/edge_server.log 2>/dev/null || echo "0")
    MALICIOUS=$(sudo grep -c "Malicious" /tmp/edge_server.log 2>/dev/null || echo "0")
    echo "Total Requests: $TOTAL"
    echo "Benign: $BENIGN"
    echo "Malicious: $MALICIOUS"
    echo
    echo "Full logs: /tmp/edge_server.log, /tmp/sta1.log, /tmp/sta2.log"
    echo "=============================================================="
    
    sleep 5
done

echo
echo "Stopping simulation..."
sudo pkill -P $SIM_PID
sudo mn -c 2>&1 | grep "Cleanup complete"

echo
echo "Done!"
