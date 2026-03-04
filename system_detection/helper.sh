#!/bin/bash
# Helper script - Kiểm tra trạng thái và cleanup

show_header() {
    echo "=============================================================="
    echo "  5G-IoT Anomaly Detection - System Helper"
    echo "=============================================================="
    echo
}

check_mininet() {
    echo "[*] Checking Mininet-WiFi installation..."
    if command -v mn &> /dev/null; then
        VERSION=$(mn --version 2>&1 | head -1)
        echo "    ✓ Mininet installed: $VERSION"
    else
        echo "    ✗ Mininet not found!"
        echo "    Install: cd ~/mininet-wifi && sudo util/install.sh -Wlnfv"
        return 1
    fi
}

check_python_deps() {
    echo "[*] Checking Python dependencies..."
    python3 -c "import sklearn, joblib, numpy" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "    ✓ Python packages installed"
    else
        echo "    ✗ Missing Python packages!"
        echo "    Install: sudo apt install python3-sklearn python3-joblib"
        return 1
    fi
}

check_model_files() {
    echo "[*] Checking model files..."
    MODEL_DIR="../model"
    if [ -f "$MODEL_DIR/decision_tree_model_"*.pkl ] && [ -f "$MODEL_DIR/scaler_"*.pkl ]; then
        echo "    ✓ Model files found"
        ls -lh "$MODEL_DIR"/*.pkl 2>/dev/null | awk '{print "      -", $9, "("$5")"}'
    else
        echo "    ✗ Model files not found in $MODEL_DIR/"
        return 1
    fi
}

check_running_processes() {
    echo "[*] Checking running processes..."
    
    # Check for Mininet
    if pgrep -f "mininet" > /dev/null; then
        echo "    ⚠  Mininet is running"
        pgrep -a -f "mininet" | head -3
    else
        echo "    ✓ No Mininet processes"
    fi
    
    # Check for edge server
    if pgrep -f "edge_server.py" > /dev/null; then
        echo "    ⚠  Edge server is running"
        pgrep -a -f "edge_server.py"
    else
        echo "    ✓ No edge server processes"
    fi
    
    # Check for IoT stations
    if pgrep -f "iot_station.py" > /dev/null; then
        echo "    ⚠  IoT stations are running"
        pgrep -a -f "iot_station.py"
    else
        echo "    ✓ No IoT station processes"
    fi
}

check_network_state() {
    echo "[*] Checking network state..."
    
    # Check OVS bridges
    BRIDGES=$(sudo ovs-vsctl list-br 2>/dev/null | wc -l)
    if [ $BRIDGES -gt 0 ]; then
        echo "    ⚠  OVS bridges exist: $BRIDGES"
        sudo ovs-vsctl list-br
    else
        echo "    ✓ No OVS bridges"
    fi
    
    # Check virtual interfaces
    INTFS=$(ip link show | grep -c "sta.*-wlan\|ap.*-wlan")
    if [ $INTFS -gt 0 ]; then
        echo "    ⚠  Virtual interfaces exist: $INTFS"
    else
        echo "    ✓ No virtual interfaces"
    fi
}

check_logs() {
    echo "[*] Checking log files..."
    
    if [ -f /tmp/edge_server.log ]; then
        LINES=$(wc -l < /tmp/edge_server.log)
        SIZE=$(du -h /tmp/edge_server.log | cut -f1)
        echo "    • edge_server.log: $LINES lines ($SIZE)"
    fi
    
    if [ -f /tmp/sta1.log ]; then
        LINES=$(wc -l < /tmp/sta1.log)
        SIZE=$(du -h /tmp/sta1.log | cut -f1)
        echo "    • sta1.log: $LINES lines ($SIZE)"
    fi
    
    if [ -f /tmp/sta2.log ]; then
        LINES=$(wc -l < /tmp/sta2.log)
        SIZE=$(du -h /tmp/sta2.log | cut -f1)
        echo "    • sta2.log: $LINES lines ($SIZE)"
    fi
    
    if [ ! -f /tmp/edge_server.log ] && [ ! -f /tmp/sta1.log ]; then
        echo "    ✓ No log files"
    fi
}

show_statistics() {
    echo "[*] Simulation statistics..."
    
    if [ -f /tmp/edge_server.log ]; then
        TOTAL=$(grep -c "Request from" /tmp/edge_server.log 2>/dev/null || echo "0")
        BENIGN=$(grep -c "Benign" /tmp/edge_server.log 2>/dev/null || echo "0")
        MALICIOUS=$(grep -c "Malicious" /tmp/edge_server.log 2>/dev/null || echo "0")
        ALERTS=$(grep -c "ALERT" /tmp/edge_server.log 2>/dev/null || echo "0")
        
        echo "    Total Requests: $TOTAL"
        echo "    Benign:         $BENIGN"
        echo "    Malicious:      $MALICIOUS"
        echo "    Alerts:         $ALERTS"
    else
        echo "    No statistics (no log file)"
    fi
}

do_cleanup() {
    echo "[*] Cleaning up..."
    
    # Cleanup Mininet
    echo "    - Running 'sudo mn -c'..."
    sudo mn -c 2>&1 | grep "Cleanup complete" || echo "    Done"
    
    # Kill processes
    echo "    - Killing Python processes..."
    sudo pkill -f "python3.*iot_station" 2>/dev/null
    sudo pkill -f "python3.*edge_server" 2>/dev/null
    sudo pkill -f "python3.*run_auto_simulation" 2>/dev/null
    
    # Remove logs
    if [ "$1" == "--remove-logs" ]; then
        echo "    - Removing log files..."
        sudo rm -f /tmp/edge_server.log /tmp/sta1.log /tmp/sta2.log
        echo "    ✓ Logs removed"
    fi
    
    echo "    ✓ Cleanup complete"
}

show_menu() {
    echo
    echo "Options:"
    echo "  1) Check system status"
    echo "  2) Show statistics"
    echo "  3) Cleanup (keep logs)"
    echo "  4) Cleanup (remove logs)"
    echo "  5) View edge server log"
    echo "  6) View station logs"
    echo "  7) Exit"
    echo
}

case "$1" in
    check|status)
        show_header
        check_mininet
        echo
        check_python_deps
        echo
        check_model_files
        echo
        check_running_processes
        echo
        check_network_state
        echo
        check_logs
        ;;
    
    stats|statistics)
        show_header
        show_statistics
        ;;
    
    cleanup)
        show_header
        do_cleanup
        ;;
    
    cleanup-all)
        show_header
        do_cleanup --remove-logs
        ;;
    
    logs)
        if [ -f /tmp/edge_server.log ]; then
            echo "=== Edge Server Log (last 30 lines) ==="
            tail -30 /tmp/edge_server.log
        else
            echo "No edge server log found"
        fi
        ;;
    
    *)
        show_header
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  check       - Check system status"
        echo "  stats       - Show simulation statistics"
        echo "  cleanup     - Cleanup network (keep logs)"
        echo "  cleanup-all - Cleanup everything (remove logs)"
        echo "  logs        - View edge server log"
        echo
        echo "Examples:"
        echo "  $0 check"
        echo "  $0 cleanup"
        echo "  $0 stats"
        echo
        echo "Interactive mode (no arguments):"
        
        while true; do
            show_menu
            read -p "Select option [1-7]: " choice
            echo
            
            case $choice in
                1)
                    check_mininet
                    echo
                    check_python_deps
                    echo
                    check_model_files
                    echo
                    check_running_processes
                    echo
                    check_network_state
                    echo
                    check_logs
                    ;;
                2)
                    show_statistics
                    ;;
                3)
                    do_cleanup
                    ;;
                4)
                    do_cleanup --remove-logs
                    ;;
                5)
                    if [ -f /tmp/edge_server.log ]; then
                        less /tmp/edge_server.log
                    else
                        echo "No edge server log found"
                    fi
                    ;;
                6)
                    if [ -f /tmp/sta1.log ]; then
                        echo "=== Station 1 Log ==="
                        cat /tmp/sta1.log
                    fi
                    echo
                    if [ -f /tmp/sta2.log ]; then
                        echo "=== Station 2 Log ==="
                        cat /tmp/sta2.log
                    fi
                    ;;
                7)
                    echo "Goodbye!"
                    exit 0
                    ;;
                *)
                    echo "Invalid option"
                    ;;
            esac
            
            echo
            read -p "Press Enter to continue..."
        done
        ;;
esac
