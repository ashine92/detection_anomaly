# 5G-IoT Anomaly Detection Dashboard

Real-time web dashboard for monitoring IoT network traffic and displaying AI-powered anomaly detection results from the Edge Server.

---

## Overview

The dashboard is a lightweight Flask web application that:
- Receives detection results sent by `edge_server_with_dashboard.py`
- Stores them in an in-memory FIFO queue
- Serves a browser-based frontend that auto-refreshes every 2 seconds
- Supports optional Mininet-WiFi topology context (wireless signal, AP info, bitrate)

```
edge_server_with_dashboard.py
        │
        │  POST /api/metrics  (AI result + raw features)
        ▼
┌──────────────────────┐
│  Flask Backend       │  :5000
│  app.py              │──────► frontend/index.html  (browser)
│  storage.py          │
│  config.py           │
└──────────────────────┘
```

---

## Directory Structure

```
dashboard/
├── README.md               ← This file
├── requirements.txt        ← Python dependencies
├── backend/
│   ├── app.py              ← Flask routes & API logic
│   ├── config.py           ← Centralized configuration
│   └── storage.py          ← In-memory data storage layer
└── frontend/
    └── index.html          ← Single-page dashboard UI
```

---

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`:

| Package | Version |
|---------|---------|
| Flask | 3.0.0 |
| flask-cors | 4.0.0 |
| numpy | ≥1.26.0 |
| scikit-learn | 1.3.0 |

---

## Installation

```bash
# From the project root
cd detection_anomaly

# (Optional) activate your virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r dashboard/requirements.txt
```

---

## Running the Dashboard

```bash
cd dashboard/backend
python app.py
```

The server starts on **http://localhost:5000** by default.

Open your browser at:
```
http://localhost:5000
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serve the frontend HTML |
| `POST` | `/api/metrics` | Receive AI detection result from Edge Server |
| `GET` | `/api/metrics` | Retrieve all stored metrics + statistics |
| `GET` | `/api/statistics` | Detailed statistics only |
| `GET` | `/api/topology` | Mininet-WiFi node/AP topology info |
| `POST` | `/api/reset` | Clear all stored data |
| `GET` | `/health` | Health check + system status |

### POST `/api/metrics` — Required Fields

```json
{
  "timestamp": "2026-03-09T10:00:00",
  "device_id": "iot-node-1",
  "prediction": "Malicious",
  "confidence": 0.97,
  "probability_malicious": 0.97
}
```

Optional Mininet-WiFi fields: `mininet_node`, `ap_ssid`, `signal_dbm`, `link_bitrate_mbps`, `ap_bssid`, `station_node`.

Optional raw network feature fields: `tot_bytes`, `src_bytes`, `tcp_rtt`, `s_hops`, `s_ttl`, `d_ttl`, `s_mean_pkt_sz`, `icmp`, `tcp_flag`, `rst_flag`.

### Anomaly Severity Levels

| Score | Severity |
|-------|----------|
| ≥ 0.90 | `critical` |
| ≥ 0.70 | `high` |
| ≥ 0.50 | `medium` |
| < 0.50 | `low` |

---

## Configuration

All settings are in [`backend/config.py`](backend/config.py):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `5000` | Server port |
| `MAX_DATA_POINTS` | `100` | Max metrics kept in memory |
| `MAX_ANOMALY_EVENTS` | `200` | Max anomaly events kept in memory |
| `REFRESH_INTERVAL` | `2000` ms | Frontend auto-refresh interval |
| `ANOMALY_THRESHOLD` | `0.7` | Score threshold for anomaly |

---

## Architecture Notes

- **No local AI model** — All detection is performed by `edge_server_with_dashboard.py` using a 24-feature Decision Tree. The dashboard only displays results.
- **In-memory storage** — Data is stored in a `deque` (FIFO). Data is lost on server restart. Can be extended to PostgreSQL/MongoDB.
- **CORS enabled** — Accepts requests from any origin by default (suitable for local development/Mininet environments).
- **Mininet-WiFi transparent** — The dashboard accepts and displays wireless context fields if present, but works equally well without them.

---

## Workflow with the Full System

```
1. Start dashboard backend:
   cd dashboard/backend && python app.py

2. Start edge server (in another terminal):
   cd system_detection && sudo python edge_server_with_dashboard.py

3. Start IoT simulation (in another terminal, requires Mininet-WiFi):
   cd system_detection && sudo python 5g_iot_mininet.py

4. Open browser: http://localhost:5000
```
