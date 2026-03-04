# Quick Reference Guide

## 🚀 Quick Start (30 seconds)

```bash
cd detection_anomaly/system_detection
./quick_start.sh
```

That's it! Simulation sẽ tự động start và hiển thị logs.

## 📋 Common Tasks

### Start Simulation
```bash
# Easiest way (recommended)
./quick_start.sh

# Auto mode with CLI
sudo python3 run_auto_simulation.py

# Manual mode
sudo python3 5g_iot_mininet.py
```

### Stop/Cleanup
```bash
# Quick cleanup
sudo mn -c

# Full cleanup (remove logs)
./helper.sh cleanup-all
```

### View Logs
```bash
# Edge server
tail -f /tmp/edge_server.log

# Stations
tail -f /tmp/sta1.log
tail -f /tmp/sta2.log

# Or use helper
./helper.sh logs
```

### Check Status
```bash
./helper.sh check
# or
./helper.sh status
```

### Statistics
```bash
# Use helper
./helper.sh stats

# Manual
grep -c "Request" /tmp/edge_server.log
grep -c "Malicious" /tmp/edge_server.log
grep "ALERT" /tmp/edge_server.log
```

## 🎯 Troubleshooting (3 steps)

1. **Cleanup first**
   ```bash
   sudo mn -c
   ```

2. **Check status**
   ```bash
   ./helper.sh check
   ```

3. **View errors**
   ```bash
   cat /tmp/edge_server.log
   ```

## 💡 Tips

- **Always cleanup before start**: `sudo mn -c`
- **Use helper.sh**: It checks everything
- **Check logs**: They tell you what's wrong
- **Port 5000**: Must be free for edge server

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Full documentation (START HERE) |
| `FILES_OVERVIEW.md` | Detailed file descriptions |
| `CHANGELOG.md` | What's been fixed |
| `WINDOWS_WSL2_SETUP.md` | For Windows users |
| This file | Quick reference |

## ⚡ One-Liners

```bash
# Full workflow
sudo mn -c && ./quick_start.sh

# Check and cleanup
./helper.sh check && ./helper.sh cleanup

# View stats
./helper.sh stats

# Test communication
sudo python3 -c "import socket; s=socket.socket(); s.connect(('10.0.0.100',5000)); print('OK')"
```

## 🔑 Key Commands

### Mininet CLI (when inside)
```bash
mininet-wifi> nodes              # List all nodes
mininet-wifi> links              # Show connections
mininet-wifi> sta1 ping edge1    # Test connectivity
mininet-wifi> xterm edge1        # Open terminal on edge1
mininet-wifi> exit               # Quit simulation
```

### Inside Node Terminals
```bash
# On edge1:
python3 -u edge_server.py ../model/decision_tree_model_*.pkl ../model/scaler_*.pkl

# On sta1:
python3 iot_station.py sta1 2 0.2
# Parameters: <id> <interval_sec> <anomaly_rate>
```

## 🎓 Learning Path

1. Read `README.md` (5 min)
2. Run `./helper.sh check` (1 min)
3. Try `./quick_start.sh` (2 min)
4. Read `FILES_OVERVIEW.md` (5 min)
5. Experiment with manual mode

## ⚠️ Common Errors

| Error | Solution |
|-------|----------|
| "timed out" | Fixed! Update to latest version |
| "No route to host" | Run `sudo mn -c` first |
| "File exists" | Cleanup: `sudo mn -c` |
| "Port in use" | Kill: `pkill -f edge_server` |
| Import error | Install: `sudo apt install python3-sklearn` |

## 📞 Get Help

1. Check `README.md` Troubleshooting section
2. View logs: `./helper.sh logs`
3. Check status: `./helper.sh check`
4. Read `CHANGELOG.md` for recent fixes

## 🎬 Example Session

```bash
# Terminal
$ cd detection_anomaly/system_detection
$ ./helper.sh check
✓ All checks passed

$ sudo mn -c
✓ Cleanup complete

$ ./quick_start.sh
[Starting simulation...]
[Monitoring logs...]
Edge Server: 10.0.0.100:5000
Request from sta1 → Benign (100.0%)
Request from sta2 → Benign (100.0%)
^C

$ ./helper.sh stats
Total Requests: 20
Benign: 18
Malicious: 2

$ ./helper.sh cleanup-all
✓ Cleanup complete
```

---

**Remember**: `./quick_start.sh` is your friend! 🚀
