#!/usr/bin/python3
"""
Automated 5G-IoT Mininet-WiFi Simulation
Tự động chạy edge server và IoT stations bên trong Mininet network
"""

from mininet.log import setLogLevel, info
import sys
import time
import os
import glob

# Import Mininet-WiFi components
try:
    from mn_wifi.net import Mininet_wifi
    from mn_wifi.node import Station, OVSKernelAP
    from mn_wifi.cli import CLI
    from mn_wifi.link import wmediumd
    from mn_wifi.wmediumdConnector import interference
except ImportError:
    print("Error: Mininet-WiFi not installed!")
    sys.exit(1)

from mininet.node import Controller, OVSKernelSwitch

def create5GIoTTopology():
    """Tạo topology mạng 5G-IoT"""
    
    info("*** Creating 5G-IoT Network with Mininet-WiFi\n")
    
    # Khởi tạo mạng với WiFi
    net = Mininet_wifi(
        controller=Controller,
        switch=OVSKernelSwitch,
        accessPoint=OVSKernelAP,
        link=wmediumd,
        wmediumd_mode=interference
    )
    
    info("*** Adding Controller\n")
    c0 = net.addController('c0')
    
    info("*** Adding Edge Server\n")
    edge_server = net.addHost(
        'edge1',
        ip='10.0.0.100/24',
        mac='00:00:00:00:00:01'
    )
    
    info("*** Adding Access Point (gNodeB - 5G Base Station)\n")
    ap1 = net.addAccessPoint(
        'ap1',
        ssid='5G-IoT-Network',
        mode='ac',          # 802.11ac ≈ 5G NR-U (Unlicensed)
        channel='36',       # 5 GHz band channel
        position='50,50,0',
        range=50
    )
    
    info("*** Adding IoT Sensor Stations\n")
    sta1 = net.addStation(
        'sta1',
        ip='10.0.0.1/24',
        mac='00:00:00:00:00:11',
        position='30,50,0',
        range=20
    )
    
    sta2 = net.addStation(
        'sta2',
        ip='10.0.0.2/24',
        mac='00:00:00:00:00:12',
        position='70,50,0',
        range=20
    )
    
    info("*** Configuring WiFi Nodes\n")
    net.configureWifiNodes()
    
    info("*** Creating Links\n")
    # Kết nối Edge Server trực tiếp với AP (không dùng switch để tránh routing issues)
    net.addLink(edge_server, ap1)
    
    info("*** Starting Network\n")
    net.build()
    c0.start()
    ap1.start([c0])
    
    info("*** Configuring Routes\n")
    # Wait for network to stabilize
    time.sleep(3)
    
    return net, edge_server, ap1, sta1, sta2

def startEdgeServer(edge_server, model_dir, dashboard_url='http://localhost:5000/api/metrics'):
    """Khởi động Edge Server với Dashboard integration trên node edge1"""
    info("\n*** Starting Edge Server (with dashboard) on edge1...\n")

    # Auto-detect latest model and scaler files via glob
    model_matches = sorted(glob.glob(f"{model_dir}/decision_tree_model_IMPROVED_*.pkl"))
    if not model_matches:
        model_matches = sorted(glob.glob(f"{model_dir}/decision_tree_model_*.pkl"))
    scaler_matches = sorted(glob.glob(f"{model_dir}/scaler_IMPROVED_*.pkl"))
    if not scaler_matches:
        scaler_matches = sorted(glob.glob(f"{model_dir}/scaler_*.pkl"))

    if not model_matches or not scaler_matches:
        info(f"ERROR: No model/scaler pkl found in {model_dir}\n")
        info("  Run the training notebook first: model_development/retrain-model-improved.ipynb\n")
        return False

    model_file = model_matches[-1]   # latest
    scaler_file = scaler_matches[-1]
    info(f"  Model:  {os.path.basename(model_file)}\n")
    info(f"  Scaler: {os.path.basename(scaler_file)}\n")

    # Launch edge_server_with_dashboard.py inside the Mininet edge1 node
    cmd = (
        f"python3 -u edge_server_with_dashboard.py "
        f"{model_file} {scaler_file} {dashboard_url} "
        f"> /tmp/edge_server.log 2>&1 &"
    )
    edge_server.cmd(cmd)

    info("Edge Server started (log: /tmp/edge_server.log)\n")
    time.sleep(3)  # Wait for server to bind the socket
    return True

def startIoTStation(station, device_id, interval, anomaly_rate, edge_ip, edge_port=5001):
    """Khởi động IoT Station trên node — truyền IP của edge server trong Mininet"""
    info(f"\n*** Starting IoT Station {device_id} -> Edge {edge_ip}:{edge_port}...\n")

    # Pass edge_ip so the station connects to the Mininet edge node, not localhost
    cmd = (
        f"python3 iot_station.py {device_id} {interval} {anomaly_rate} "
        f"{edge_ip} {edge_port} "
        f"> /tmp/{device_id}.log 2>&1 &"
    )
    station.cmd(cmd)

    info(f"{device_id} started (log: /tmp/{device_id}.log)\n")

def runSimulation():
    """Chạy mô phỏng tự động"""
    setLogLevel('info')
    
    # Lấy đường dẫn model
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(os.path.dirname(current_dir), 'model')
    
    info("\n")
    info("="*70 + "\n")
    info("  5G-IoT ANOMALY DETECTION SIMULATION (AUTO MODE)\n")
    info("="*70 + "\n")
    
    # Tạo topology
    net, edge_server, ap1, sta1, sta2 = create5GIoTTopology()
    
    info("\n*** Network Topology Created!\n")
    info("=" * 60 + "\n")
    info("Edge Server: %s (IP: %s)\n" % (edge_server.name, edge_server.IP()))
    info("Access Point: %s (SSID: 5G-IoT-Network)\n" % ap1.name)
    info("IoT Station 1: %s (IP: %s)\n" % (sta1.name, sta1.IP()))
    info("IoT Station 2: %s (IP: %s)\n" % (sta2.name, sta2.IP()))
    info("=" * 60 + "\n")
    
    # Test connectivity
    info("\n*** Testing Network Connectivity...\n")
    result = sta1.cmd('ping -c 2 %s' % edge_server.IP())
    if '0% packet loss' in result:
        info("✓ Network connectivity OK\n")
    else:
        info("⚠ Network connectivity issue!\n")
    
    # Chuyển working directory cho các node
    edge_server.cmd(f'cd {current_dir}')
    sta1.cmd(f'cd {current_dir}')
    sta2.cmd(f'cd {current_dir}')
    
    # Khởi động Edge Server
    ok = startEdgeServer(edge_server, model_dir)
    if not ok:
        info("\n*** ABORTED: Could not find model files. Stop network.\n")
        net.stop()
        return

    # Lấy IP của edge server trong Mininet để các IoT stations kết nối đúng
    edge_ip = edge_server.IP()

    # Khởi động IoT Stations — truyền edge_ip thay vì dùng localhost
    startIoTStation(sta1, 'sta1', 2, 0.2, edge_ip)   # 2 s/packet, 20% anomaly
    startIoTStation(sta2, 'sta2', 3, 0.15, edge_ip)  # 3 s/packet, 15% anomaly
    
    info("\n")
    info("="*70 + "\n")
    info("  SIMULATION RUNNING\n")
    info("="*70 + "\n")
    info("Monitor logs:\n")
    info("  - Edge Server: tail -f /tmp/edge_server.log\n")
    info("  - Station 1:   tail -f /tmp/sta1.log\n")
    info("  - Station 2:   tail -f /tmp/sta2.log\n")
    info("\n")
    info("Mininet commands:\n")
    info("  - edge1 cat /tmp/edge_server.log  # View edge server log\n")
    info("  - sta1 cat /tmp/sta1.log          # View station 1 log\n")
    info("  - sta2 cat /tmp/sta2.log          # View station 2 log\n")
    info("  - xterm edge1                      # Open terminal on edge1\n")
    info("  - xterm sta1                       # Open terminal on sta1\n")
    info("\n")
    info("Type 'exit' to stop simulation\n")
    info("="*70 + "\n")
    
    # Mở CLI
    CLI(net)
    
    info("\n*** Stopping Network\n")
    net.stop()

if __name__ == '__main__':
    runSimulation()
