#!/usr/bin/python3
"""
Mô phỏng Mạng 5G-IoT với Mininet-WiFi
Kiến trúc: Edge Server - gNodeB - IoT Stations
"""

from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import sys
import os
import time
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
    print("Install with: sudo apt-get install mininet-wifi")
    sys.exit(1)

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
    # Edge Server - trung tâm phân tích (host thông thường)
    edge_server = net.addHost(
        'edge1',
        ip='10.0.0.100/24',
        mac='00:00:00:00:00:01'
    )
    
    info("*** Adding Access Point (gNodeB - 5G Base Station)\n")
    # Access Point giả lập 5G gNodeB
    ap1 = net.addAccessPoint(
        'ap1',
        ssid='5G-IoT-Network',
        mode='ac',          # 802.11ac ≈ 5G NR-U (Unlicensed)
        channel='36',       # 5 GHz band channel
        range=50,  # Phạm vi 50m
        position='50,50,0',
        failMode='standalone'
    )
    
    info("*** Adding IoT Sensor Stations\n")
    # Station 1 - IoT Sensor Node 1 (Temperature Sensor)
    sta1 = net.addStation(
        'sta1',
        ip='10.0.0.1/24',
        mac='00:00:00:00:00:11',
        position='30,40,0',
        range=20
    )
    
    # Station 2 - IoT Sensor Node 2 (Motion Sensor)  
    sta2 = net.addStation(
        'sta2',
        ip='10.0.0.2/24',
        mac='00:00:00:00:00:12',
        position='70,60,0',
        range=20
    )
    
    info("*** Configuring WiFi Nodes\n")
    net.configureWifiNodes()
    
    info("*** Creating Links\n")
    # Kết nối Edge Server với Access Point qua switch
    s1 = net.addSwitch('s1')
    net.addLink(edge_server, s1)
    net.addLink(s1, ap1)
    
    info("*** Starting Network\n")
    net.build()
    c0.start()
    s1.start([c0])
    ap1.start([c0])
    
    info("*** Configuring Routes\n")
    # IoT stations need a default route to reach the edge server via ap1
    sta1.cmd('ip route add default via 10.0.0.100 2>/dev/null || true')
    sta2.cmd('ip route add default via 10.0.0.100 2>/dev/null || true')
    
    info("\n*** Network Topology Created Successfully!\n")
    info("=" * 60 + "\n")
    info("Edge Server: %s (IP: %s)\n" % (edge_server.name, edge_server.IP()))
    info("Access Point: %s (SSID: 5G-IoT-Network)\n" % ap1.name)
    info("IoT Station 1: %s (IP: %s)\n" % (sta1.name, sta1.IP()))
    info("IoT Station 2: %s (IP: %s)\n" % (sta2.name, sta2.IP()))
    info("=" * 60 + "\n")
    
    return net, edge_server, ap1, sta1, sta2

def startEdgeServer(edge_server, model_dir, simu_dir,
                    dashboard_url='http://localhost:5000/api/metrics'):
    """Khởi động edge_server_with_dashboard.py bên trong Mininet node edge1"""
    info("\n*** Starting Edge Server (with dashboard) on edge1...\n")

    model_matches = sorted(glob.glob(f"{model_dir}/decision_tree_model_IMPROVED_*.pkl"))
    if not model_matches:
        model_matches = sorted(glob.glob(f"{model_dir}/decision_tree_model_*.pkl"))
    scaler_matches = sorted(glob.glob(f"{model_dir}/scaler_IMPROVED_*.pkl"))
    if not scaler_matches:
        scaler_matches = sorted(glob.glob(f"{model_dir}/scaler_*.pkl"))

    if not model_matches or not scaler_matches:
        info(f"ERROR: No model/scaler found in {model_dir}\n")
        info("  Train the model first: model_development/retrain-model-improved.ipynb\n")
        return False

    model_file  = model_matches[-1]
    scaler_file = scaler_matches[-1]
    info(f"  Model:  {os.path.basename(model_file)}\n")
    info(f"  Scaler: {os.path.basename(scaler_file)}\n")

    edge_server.cmd(f'cd {simu_dir}')
    cmd = (
        f"python3 -u edge_server_with_dashboard.py "
        f"{model_file} {scaler_file} {dashboard_url} "
        f"> /tmp/edge_server.log 2>&1 &"
    )
    edge_server.cmd(cmd)
    info("Edge Server started (log: /tmp/edge_server.log)\n")
    time.sleep(3)  # wait for socket to bind
    return True


def startIoTStation(station, device_id, interval, anomaly_rate, edge_ip,
                    simu_dir, edge_port=5001):
    """Khởi động IoT Station bên trong Mininet node — truyền IP edge server"""
    info(f"\n*** Starting IoT Station {device_id} -> Edge {edge_ip}:{edge_port}\n")
    station.cmd(f'cd {simu_dir}')
    cmd = (
        f"python3 iot_station.py {device_id} {interval} {anomaly_rate} "
        f"{edge_ip} {edge_port} "
        f"> /tmp/{device_id}.log 2>&1 &"
    )
    station.cmd(cmd)
    info(f"{device_id} started (log: /tmp/{device_id}.log)\n")


def testConnectivity(net, edge_server, sta1, sta2):
    """Test kết nối giữa các node"""
    info("\n*** Testing Network Connectivity\n")
    
    # Ping từ stations đến edge server
    info("Testing sta1 -> edge_server: ")
    result1 = sta1.cmd('ping -c 3 %s' % edge_server.IP())
    
    info("Testing sta2 -> edge_server: ")
    result2 = sta2.cmd('ping -c 3 %s' % edge_server.IP())
    
    # Ping giữa 2 stations
    info("Testing sta1 -> sta2: ")
    result3 = sta1.cmd('ping -c 3 %s' % sta2.IP())
    
    info("\n*** Connectivity Test Completed\n")

def runSimulation():
    """Chạy mô phỏng mạng và tự động khởi động edge server + IoT stations"""
    setLogLevel('info')

    # Resolve path to system_detection/ and model/
    simu_dir  = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(os.path.dirname(simu_dir), 'model')

    # Tạo topology
    net, edge_server, ap1, sta1, sta2 = create5GIoTTopology()

    # Test connectivity
    testConnectivity(net, edge_server, sta1, sta2)

    # Khởi động Edge Server bên trong Mininet
    ok = startEdgeServer(edge_server, model_dir, simu_dir)
    if not ok:
        info("\n*** ABORTED: No model files found. Stopping network.\n")
        net.stop()
        return

    # Lấy IP của edge node  trong mạng Mininet
    edge_ip = edge_server.IP()

    # Khởi động các IoT Stations — kết nối đến edge_ip chứ không phải localhost
    startIoTStation(sta1, 'sta1', 2, 0.2,  edge_ip, simu_dir)  # 2 s, 20% anomaly
    startIoTStation(sta2, 'sta2', 3, 0.15, edge_ip, simu_dir)  # 3 s, 15% anomaly

    info("\n*** Starting CLI (type 'exit' to quit)\n")
    info("Useful commands:\n")
    info("  - nodes: show all nodes\n")
    info("  - links: show all links\n")
    info("  - net: show network info\n")
    info("  - sta1 ping edge1: ping from station to edge server\n")
    info("  - edge1 tail -f /tmp/edge_server.log  # live edge log\n")
    info("  - sta1  tail -f /tmp/sta1.log          # live station 1 log\n")
    info("  - sta2  tail -f /tmp/sta2.log          # live station 2 log\n")
    info("  - xterm sta1: open terminal on station\n")
    info("\n")

    # Mở CLI để tương tác
    CLI(net)

    info("\n*** Stopping Network\n")
    net.stop()

if __name__ == '__main__':
    runSimulation()
