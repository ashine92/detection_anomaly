#!/usr/bin/python3
"""
Automated 5G-IoT Mininet-WiFi Simulation
Tự động chạy edge server và IoT stations bên trong Mininet network
"""

from mininet.log import setLogLevel, info
import sys
import time
import os

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
        mode='g',
        channel='1',
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

def startEdgeServer(edge_server, model_dir):
    """Khởi động Edge Server trên node edge1"""
    info("\n*** Starting Edge Server on edge1...\n")
    
    model_file = f"{model_dir}/decision_tree_model_20260227_205406.pkl"
    scaler_file = f"{model_dir}/scaler_20260227_205406.pkl"
    
    # Chạy edge_server trong background trên node edge1 với unbuffered output
    cmd = f"python3 -u edge_server.py {model_file} {scaler_file} > /tmp/edge_server.log 2>&1 &"
    edge_server.cmd(cmd)
    
    info("Edge Server started (log: /tmp/edge_server.log)\n")
    time.sleep(2)  # Đợi server khởi động

def startIoTStation(station, device_id, interval, anomaly_rate):
    """Khởi động IoT Station trên node"""
    info(f"\n*** Starting IoT Station {device_id}...\n")
    
    # Chạy iot_station trong background
    cmd = f"python3 iot_station.py {device_id} {interval} {anomaly_rate} > /tmp/{device_id}.log 2>&1 &"
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
    startEdgeServer(edge_server, model_dir)
    
    # Khởi động IoT Stations
    startIoTStation(sta1, 'sta1', 2, 0.2)  # Gửi mỗi 2 giây, 20% anomaly
    startIoTStation(sta2, 'sta2', 3, 0.15)  # Gửi mỗi 3 giây, 15% anomaly
    
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
