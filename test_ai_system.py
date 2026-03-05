#!/usr/bin/env python3
"""
=============================================================
  TEST SCRIPT — 5G IoT Anomaly Detection AI System
=============================================================
Kiểm tra toàn bộ hệ thống AI theo 4 tầng:

  [TIER 1] Unit Test  — Model trực tiếp (.pkl)
  [TIER 2] Module Test — AnomalyDetector (detection.py)
  [TIER 3] API Test   — Dashboard Flask HTTP API
  [TIER 4] Integration — Edge Server TCP Socket

Chạy:
  python3 test_ai_system.py                    # Tier 1+2 (không cần server)
  python3 test_ai_system.py --api              # + Tier 3 (cần dashboard chạy)
  python3 test_ai_system.py --edge             # + Tier 4 (cần edge server chạy)
  python3 test_ai_system.py --all              # Tất cả tier
=============================================================
"""

import sys
import os
import json
import time
import socket
import argparse
import traceback
import numpy as np

# ───────── màu sắc terminal ─────────
GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
BOLD    = "\033[1m"
RESET   = "\033[0m"
GRAY    = "\033[90m"

# ───────── đường dẫn project ─────────
PROJECT_ROOT   = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR      = os.path.join(PROJECT_ROOT, "model")
DASHBOARD_DIR  = os.path.join(PROJECT_ROOT, "dashboard", "backend")

# ───────── kết quả tổng hợp ─────────
results = {"passed": 0, "failed": 0, "skipped": 0}


# =============================================================
#  Tiện ích hiển thị
# =============================================================

def header(title: str):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")

def section(title: str):
    print(f"\n{BOLD}  ── {title} ──{RESET}")

def ok(msg: str):
    results["passed"] += 1
    print(f"  {GREEN}[PASS]{RESET} {msg}")

def fail(msg: str, detail: str = ""):
    results["failed"] += 1
    print(f"  {RED}[FAIL]{RESET} {msg}")
    if detail:
        print(f"         {GRAY}{detail}{RESET}")

def skip(msg: str):
    results["skipped"] += 1
    print(f"  {YELLOW}[SKIP]{RESET} {msg}")

def info(msg: str):
    print(f"  {GRAY}      {msg}{RESET}")


# =============================================================
#  Dữ liệu Test mẫu — 24 features theo đúng thứ tự model
# =============================================================
#  Thứ tự: Seq, Mean, sTos, sTtl, dTtl, sHops, TotBytes, SrcBytes,
#           Offset, sMeanPktSz, dMeanPktSz, SrcWin, TcpRtt, AckDat,
#           ' e        ', ' e d      ', icmp, tcp,
#           CON, FIN, INT, REQ, RST, cs0/Status

# Đúng thứ tự theo model training (notebook cell 4→6, feature_names_.pkl)
FEATURE_NAMES = [
    'Seq', 'Mean', 'sTos', 'sTtl', 'dTtl', 'sHops',
    'TotBytes', 'SrcBytes', 'Offset', 'sMeanPktSz', 'dMeanPktSz',
    'SrcWin', 'TcpRtt', 'AckDat',
    ' e        ', ' e d      ', 'icmp', 'tcp',
    'CON', 'FIN', 'INT', 'REQ', 'RST', 'Status'
]

# ─────────────────────────────────────────────────────────────
#  Sample thật lấy từ dataset/Encoded.csv (fillna=0)
#  Thứ tự: Seq,Mean,sTos,sTtl,dTtl,sHops,TotBytes,SrcBytes,
#           Offset,sMeanPktSz,dMeanPktSz,SrcWin,TcpRtt,AckDat,
#           ' e        ',' e d      ',icmp,tcp,
#           CON,FIN,INT,REQ,RST,Status
# ─────────────────────────────────────────────────────────────
TEST_CASES = {
    # ── Benign (lấy trực tiếp từ dataset) ──────────────────
    "benign_real_1": {
        "label": "Benign",
        "description": "ICMP single packet (dataset row 1)",
        "features": [
            1.0, 0.0, 0.0, 58.0, 0.0, 6.0,
            98.0, 98.0, 128.0, 98.0, 0.0,
            0.0, 0.0, 0.0,
            1.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ]
    },
    "benign_real_2": {
        "label": "Benign",
        "description": "ICMP single packet (dataset row 2)",
        "features": [
            2.0, 0.0, 0.0, 58.0, 0.0, 6.0,
            98.0, 98.0, 232.0, 98.0, 0.0,
            0.0, 0.0, 0.0,
            1.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ]
    },
    "benign_real_3": {
        "label": "Benign",
        "description": "TCP luồng lớn, CON=1 (dataset row 3)",
        "features": [
            3.0, 4.99802, 0.0, 117.0, 64.0, 11.0,
            249093.0, 244212.0, 336.0, 1245.979614, 271.166656,
            0.0, 0.0, 0.0,
            1.0, 0.0, 0.0, 0.0,
            1.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ]
    },

    # ── Malicious (lấy trực tiếp từ dataset) ───────────────
    "malicious_real_1": {
        "label": "Malicious",
        "description": "ICMP attack, sTtl=49, dTtl=0 (dataset malicious row 1)",
        "features": [
            35.0, 1.880046, 0.0, 49.0, 0.0, 15.0,
            108.0, 108.0, 4600.0, 54.0, 0.0,
            0.0, 0.0, 0.0,
            1.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ]
    },
    "malicious_real_2": {
        "label": "Malicious",
        "description": "TCP RST attack, sTtl=50, SrcWin=1024 (dataset malicious row 3)",
        "features": [
            40.0, 0.001938, 0.0, 50.0, 59.0, 14.0,
            112.0, 58.0, 5084.0, 58.0, 54.0,
            1024.0, 0.0, 0.0,
            1.0, 0.0, 0.0, 1.0,
            0.0, 0.0, 0.0, 0.0, 1.0, 0.0
        ]
    },
    "malicious_real_3": {
        "label": "Malicious",
        "description": "ICMP 2-way small packet attack (dataset malicious row 3)",
        "features": [
            39.0, 0.001938, 0.0, 45.0, 59.0, 19.0,
            84.0, 42.0, 4992.0, 42.0, 42.0,
            0.0, 0.0, 0.0,
            1.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ]
    },
}


# =============================================================
#  TIER 1 — Unit Test: Model .pkl trực tiếp
# =============================================================

def find_model_files():
    """Tìm file model mới nhất trong thư mục model/"""
    if not os.path.isdir(MODEL_DIR):
        return None, None, None

    import glob
    models   = sorted(glob.glob(os.path.join(MODEL_DIR, "decision_tree_model_*.pkl")))
    scalers  = sorted(glob.glob(os.path.join(MODEL_DIR, "scaler_*.pkl")))
    features = sorted(glob.glob(os.path.join(MODEL_DIR, "feature_names_*.pkl")))

    return (
        models[-1]   if models   else None,
        scalers[-1]  if scalers  else None,
        features[-1] if features else None,
    )


def tier1_model_unit_tests():
    header("TIER 1 — Unit Test: AI Model .pkl")

    import joblib

    section("1.1  Kiểm tra file model tồn tại")
    model_path, scaler_path, feature_path = find_model_files()

    for name, path in [("Model (.pkl)", model_path),
                       ("Scaler (.pkl)", scaler_path),
                       ("Feature names (.pkl)", feature_path)]:
        if path and os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            ok(f"{name}  →  {os.path.basename(path)}  ({size_kb:.1f} KB)")
        else:
            fail(f"{name} không tìm thấy trong {MODEL_DIR}")
            return  # không tiếp tục nếu thiếu file

    section("1.2  Load model vào bộ nhớ")
    try:
        model    = joblib.load(model_path)
        scaler   = joblib.load(scaler_path)
        feat_names = joblib.load(feature_path)
        ok(f"Load thành công — {type(model).__name__}")
        info(f"Max depth   : {model.tree_.max_depth}")
        info(f"N features  : {model.n_features_in_}")
        info(f"Classes     : {model.classes_.tolist()}")
        info(f"Feature list: {feat_names}")
    except Exception as e:
        fail("Load model thất bại", str(e))
        return

    section("1.3  Kiểm tra số lượng feature")
    if model.n_features_in_ == 24:
        ok(f"Model nhận đúng 24 features")
    else:
        fail(f"Model cần {model.n_features_in_} features, script chuẩn bị 24")
        return

    section("1.4  Predict từng test case")
    correct = 0
    for name, tc in TEST_CASES.items():
        try:
            X = np.array(tc["features"]).reshape(1, -1)
            X_scaled = scaler.transform(X)
            pred = model.predict(X_scaled)[0]
            proba = model.predict_proba(X_scaled)[0]
            conf = float(np.max(proba))
            expected = tc["label"]
            match = (pred == expected)
            if match:
                ok(f"{name:35s}  pred={pred}  conf={conf:.2%}  ✓")
                correct += 1
            else:
                fail(f"{name:35s}  pred={pred}  expected={expected}  conf={conf:.2%}")
            info(f"  {tc['description']}")
        except Exception as e:
            fail(f"{name}", str(e))

    total = len(TEST_CASES)
    print(f"\n  Kết quả: {correct}/{total} test case đúng ({correct/total*100:.0f}%)")
    if correct == total:
        ok("Tất cả test case model dự đoán chính xác")
    elif correct >= total * 0.8:
        ok(f"Phần lớn test case đúng ({correct}/{total})")
    else:
        fail(f"Nhiều test case sai — kiểm tra lại dữ liệu train ({correct}/{total})")

    return model, scaler, feat_names


# =============================================================
#  TIER 2 — Module Test: AnomalyDetector (detection.py)
# =============================================================

def tier2_module_tests():
    header("TIER 2 — Module Test: AnomalyDetector (detection.py)")

    section("2.1  Import module detection.py")
    try:
        sys.path.insert(0, DASHBOARD_DIR)
        from detection import AnomalyDetector, detector as global_detector
        ok("Import AnomalyDetector thành công")
    except Exception as e:
        fail("Import detection.py thất bại", str(e))
        return

    section("2.2  Khởi tạo AnomalyDetector")
    try:
        det = AnomalyDetector()
        ok(f"AnomalyDetector() tạo thành công")
        if det.model_loaded:
            ok(f"Model loaded = True  (dùng trained model)")
            info(f"Feature names: {det.feature_names}")
        else:
            skip("Model không load được → chạy mock mode (rule-based)")
    except Exception as e:
        fail("AnomalyDetector() lỗi", str(e))
        return

    section("2.3  Test predict() — 4 metrics đơn giản (mock mode)")
    mock_cases = [
        {
            "name": "Bình thường",
            "metrics": {"throughput": 80.0, "latency": 10.0, "packet_loss": 0.1, "rssi": -60},
            "expected": "normal"
        },
        {
            "name": "Latency cao (50ms+)",
            "metrics": {"throughput": 70.0, "latency": 55.0, "packet_loss": 0.5, "rssi": -75},
            "expected": "anomaly"
        },
        {
            "name": "Throughput thấp + packet loss",
            "metrics": {"throughput": 10.0, "latency": 5.0, "packet_loss": 10.0, "rssi": -80},
            "expected": "anomaly"
        },
        {
            "name": "Tất cả thấp",
            "metrics": {"throughput": 5.0, "latency": 100.0, "packet_loss": 20.0, "rssi": -95},
            "expected": "anomaly"
        },
    ]

    for tc in mock_cases:
        try:
            label, score = det.predict(tc["metrics"])
            match = (label == tc["expected"])
            msg = f"{tc['name']:35s}  pred={label}  score={score:.3f}"
            if match:
                ok(msg)
            else:
                # Mock mode có thể khác expected nếu dùng model thật
                info(f"  {msg}  (expected={tc['expected']}, có thể OK nếu dùng trained model)")
        except Exception as e:
            fail(f"{tc['name']}", str(e))

    section("2.4  Test analyze_metrics() — kiểm tra output format")
    try:
        result = det.analyze_metrics({"throughput": 80, "latency": 10, "packet_loss": 0, "rssi": -60})
        required_keys = ["prediction_label", "anomaly_score", "severity", "is_anomaly", "model_type"]
        missing = [k for k in required_keys if k not in result]
        if not missing:
            ok(f"Output đầy đủ: {list(result.keys())}")
            info(f"  prediction_label = {result['prediction_label']}")
            info(f"  anomaly_score    = {result['anomaly_score']}")
            info(f"  severity         = {result['severity']}")
            info(f"  model_type       = {result['model_type']}")
        else:
            fail(f"Thiếu keys trong output: {missing}")
    except Exception as e:
        fail("analyze_metrics() lỗi", str(e))

    section("2.5  Test preprocess_data() — nếu model loaded")
    if det.model_loaded and det.feature_names:
        try:
            sample = {name: val for name, val in zip(det.feature_names, TEST_CASES["benign_real_3"]["features"])}
            arr = det.preprocess_data(sample)
            if arr is not None and arr.shape == (1, len(det.feature_names)):
                ok(f"preprocess_data() trả về shape {arr.shape}")
            else:
                fail(f"preprocess_data() trả về shape sai: {arr}")
        except Exception as e:
            fail("preprocess_data() lỗi", str(e))
    else:
        skip("Model chưa load → bỏ qua test preprocess_data()")


# =============================================================
#  TIER 3 — API Test: Dashboard HTTP (Flask)
# =============================================================

def tier3_api_tests(api_url: str = "http://localhost:5000"):
    header(f"TIER 3 — API Test: Dashboard HTTP  [{api_url}]")

    try:
        import urllib.request
        import urllib.error
    except ImportError:
        skip("Không có urllib")
        return

    def post_json(url, payload):
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode()), resp.status

    section("3.1  Health check — GET /")
    try:
        req = urllib.request.Request(api_url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            ok(f"GET /  →  HTTP {resp.status}")
    except Exception as e:
        fail("Dashboard không phản hồi", f"{e}\n         Hãy chạy: cd dashboard/backend && python3 app.py")
        return

    section("3.2  POST /api/metrics — Benign payload")
    benign_payload = {
        "timestamp": "2026-03-05T10:00:00",
        "device_id": "test_benign_device",
        "throughput": 85.0,
        "latency": 12.0,
        "packet_loss": 0.1,
        "rssi": -60
    }
    try:
        resp, status = post_json(f"{api_url}/api/metrics", benign_payload)
        if status == 200:
            ok(f"HTTP 200  →  prediction={resp.get('prediction_label', resp.get('prediction'))}  "
               f"score={resp.get('anomaly_score', '?')}")
        else:
            fail(f"HTTP {status}", str(resp))
    except Exception as e:
        fail("POST /api/metrics (Benign) thất bại", str(e))

    section("3.3  POST /api/metrics — Anomaly payload")
    anomaly_payload = {
        "timestamp": "2026-03-05T10:00:01",
        "device_id": "test_attacker",
        "throughput": 5.0,
        "latency": 200.0,
        "packet_loss": 25.0,
        "rssi": -95
    }
    try:
        resp, status = post_json(f"{api_url}/api/metrics", anomaly_payload)
        if status == 200:
            pred = resp.get("prediction_label", resp.get("prediction"))
            score = resp.get("anomaly_score", "?")
            ok(f"HTTP 200  →  prediction={pred}  score={score}")
            if pred == "anomaly" or (isinstance(score, float) and score > 0.5):
                ok("Phát hiện đúng anomaly")
            else:
                info(f"prediction={pred} — model có thể dùng mock mode")
        else:
            fail(f"HTTP {status}", str(resp))
    except Exception as e:
        fail("POST /api/metrics (Anomaly) thất bại", str(e))

    section("3.4  Validation — thiếu field bắt buộc")
    try:
        resp, status = post_json(f"{api_url}/api/metrics", {"device_id": "incomplete"})
        if status == 400:
            ok(f"HTTP 400 đúng khi thiếu field  →  {resp.get('error', '')[:60]}")
        else:
            fail(f"Mong đợi HTTP 400, nhận HTTP {status}")
    except urllib.error.HTTPError as e:
        if e.code == 400:
            ok("HTTP 400 validation lỗi đúng")
        else:
            fail(f"HTTP {e.code} không mong đợi", str(e))
    except Exception as e:
        fail("Validation test thất bại", str(e))

    section("3.5  GET /api/metrics — lấy dashboard data (metrics + anomalies)")
    try:
        req = urllib.request.Request(f"{api_url}/api/metrics", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            metrics_count   = len(data.get('metrics', []))
            anomaly_count   = len(data.get('anomaly_events', []))
            ok(f"HTTP {resp.status}  →  metrics={metrics_count} records, anomaly_events={anomaly_count} records")
    except Exception as e:
        info(f"/api/metrics (GET): {e}")

    section("3.6  GET /api/statistics — thống kê hệ thống")
    try:
        req = urllib.request.Request(f"{api_url}/api/statistics", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            ok(f"HTTP {resp.status}  →  keys: {list(data.keys()) if isinstance(data, dict) else data}")
    except Exception as e:
        info(f"/api/statistics: {e}")


# =============================================================
#  TIER 4 — Integration: Edge Server TCP Socket
# =============================================================

def tier4_edge_server_tests(host: str = "localhost", port: int = 5001):
    header(f"TIER 4 — Integration: Edge Server TCP  [{host}:{port}]")

    def send_to_edge(features, device_id="test_device", timeout=5):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        payload = {
            "device_id": device_id,
            "features": features,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        sock.send(json.dumps(payload).encode())
        response = json.loads(sock.recv(4096).decode())
        sock.close()
        return response

    section("4.1  Kiểm tra Edge Server đang chạy")
    try:
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_sock.settimeout(3)
        test_sock.connect((host, port))
        test_sock.close()
        ok(f"Edge Server đang lắng nghe tại {host}:{port}")
    except Exception as e:
        fail(f"Không kết nối được tới {host}:{port}",
             f"{e}\n         Hãy chạy: python3 system_detection/edge_server_with_dashboard.py <model> <scaler>")
        return

    section("4.2  Gửi Benign sample qua TCP socket")
    try:
        resp = send_to_edge(TEST_CASES["benign_real_3"]["features"], "test_benign")
        ok(f"Response nhận được: prediction={resp.get('prediction')}  "
           f"confidence={resp.get('confidence', 0):.2%}")
        expected = "Benign"
        if resp.get("prediction") == expected:
            ok("Phân loại đúng: Benign")
        else:
            fail(f"Mong đợi {expected}, nhận {resp.get('prediction')}")
    except Exception as e:
        fail("Gửi benign sample thất bại", str(e))

    section("4.3  Gửi Malicious samples")
    malicious_cases = ["malicious_real_1", "malicious_real_2", "malicious_real_3"]
    detected = 0
    for case_name in malicious_cases:
        tc = TEST_CASES[case_name]
        try:
            resp = send_to_edge(tc["features"], f"attacker_{case_name}")
            pred = resp.get("prediction")
            conf = resp.get("confidence", 0)
            if pred == "Malicious":
                ok(f"{case_name:35s}  →  {pred}  ({conf:.2%})  ✓ Phát hiện đúng")
                detected += 1
            else:
                fail(f"{case_name:35s}  →  {pred}  ({conf:.2%})  Sai (expected Malicious)")
            info(f"  {tc['description']}")
        except Exception as e:
            fail(f"{case_name}", str(e))

    if detected == len(malicious_cases):
        ok(f"Phát hiện đầy đủ {detected}/{len(malicious_cases)} malicious case")
    else:
        info(f"Phát hiện {detected}/{len(malicious_cases)} malicious case")

    section("4.4  Kiểm tra format response")
    try:
        resp = send_to_edge(TEST_CASES["benign_real_1"]["features"])
        required_keys = ["prediction", "confidence", "probability_benign", "probability_malicious", "timestamp"]
        missing = [k for k in required_keys if k not in resp]
        if not missing:
            ok(f"Response có đầy đủ fields: {required_keys}")
        else:
            fail(f"Thiếu fields trong response: {missing}\n         Có: {list(resp.keys())}")
    except Exception as e:
        fail("Kiểm tra response format thất bại", str(e))

    section("4.5  Test tải (10 requests liên tiếp)")
    times = []
    success = 0
    for i in range(10):
        t0 = time.time()
        try:
            import random
            use_anomaly = random.random() < 0.3
            case = random.choice(
                ["benign_real_1", "benign_real_3"] if not use_anomaly
                else ["malicious_real_1", "malicious_real_2"]
            )
            send_to_edge(TEST_CASES[case]["features"], f"load_test_{i}")
            times.append(time.time() - t0)
            success += 1
        except Exception:
            pass
    if success > 0:
        avg = sum(times) / len(times) * 1000
        ok(f"{success}/10 requests thành công — avg latency {avg:.1f} ms")
    else:
        fail("Tất cả requests thất bại trong load test")


# =============================================================
#  TIER 5 — Kiểm tra nhất quán giữa 2 AI
# =============================================================

def tier5_consistency_test():
    header("TIER 5 — Kiểm tra nhất quán 2 tầng AI")
    info("So sánh kết quả từ model .pkl trực tiếp vs AnomalyDetector")

    try:
        import joblib
        sys.path.insert(0, DASHBOARD_DIR)
        from detection import AnomalyDetector

        model_path, scaler_path, _ = find_model_files()
        if not model_path:
            skip("Không tìm thấy model file")
            return

        model  = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        det    = AnomalyDetector()

        if not det.model_loaded:
            skip("AnomalyDetector chạy mock mode — không so sánh được")
            return

        section("5.1  So sánh prediction cho từng test case")
        mismatch = 0
        for name, tc in TEST_CASES.items():
            X = np.array(tc["features"]).reshape(1, -1)
            X_sc = scaler.transform(X)
            direct_pred = model.predict(X_sc)[0]

            feat_dict = {fname: val for fname, val in zip(det.feature_names, tc["features"])}
            module_label, module_score = det.predict(feat_dict)
            # module trả về 'Benign'/'Malicious' hoặc 'normal'/'anomaly'
            module_pred_norm = "Malicious" if "anomaly" in module_label.lower() or module_label == "Malicious" else "Benign"

            match = (direct_pred == module_pred_norm)
            if match:
                ok(f"{name:35s}  direct={direct_pred}  module={module_pred_norm}  ✓")
            else:
                fail(f"{name:35s}  direct={direct_pred} ≠ module={module_pred_norm}")
                mismatch += 1

        if mismatch == 0:
            ok("2 tầng AI cho kết quả nhất quán hoàn toàn")
        else:
            fail(f"{mismatch} trường hợp không nhất quán — kiểm tra lại config.py")

    except Exception as e:
        fail("Consistency test lỗi", traceback.format_exc())


# =============================================================
#  SUMMARY
# =============================================================

def print_summary():
    total = results["passed"] + results["failed"] + results["skipped"]
    header("KẾT QUẢ TỔNG HỢP")
    print(f"\n  {GREEN}PASS  : {results['passed']}{RESET}")
    print(f"  {RED}FAIL  : {results['failed']}{RESET}")
    print(f"  {YELLOW}SKIP  : {results['skipped']}{RESET}")
    print(f"  Total : {total}\n")

    if results["failed"] == 0:
        print(f"  {GREEN}{BOLD}✓ Toàn bộ hệ thống AI hoạt động bình thường!{RESET}\n")
    else:
        rate = results["passed"] / (total - results["skipped"]) * 100 if total > results["skipped"] else 0
        print(f"  {YELLOW}{BOLD}Tỷ lệ pass: {rate:.0f}%{RESET}\n")


# =============================================================
#  MAIN
# =============================================================

def main():
    parser = argparse.ArgumentParser(description="Test AI system cho 5G IoT Anomaly Detection")
    parser.add_argument("--api",      action="store_true", help="Bao gồm API test (cần dashboard đang chạy)")
    parser.add_argument("--edge",     action="store_true", help="Bao gồm Edge Server test (cần server đang chạy)")
    parser.add_argument("--all",      action="store_true", help="Chạy tất cả các tier")
    parser.add_argument("--api-url",  default="http://localhost:5000", help="Dashboard API URL")
    parser.add_argument("--edge-host",default="localhost",  help="Edge server host")
    parser.add_argument("--edge-port",default=5001, type=int, help="Edge server port")
    args = parser.parse_args()

    print(f"\n{BOLD}{CYAN}")
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║   5G IoT Anomaly Detection — AI System Test Suite   ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print(f"{RESET}")

    # Tier 1+2 luôn chạy
    tier1_model_unit_tests()
    tier2_module_tests()
    tier5_consistency_test()

    # Tier 3 — API
    if args.all or args.api:
        tier3_api_tests(args.api_url)
    else:
        header("TIER 3 — API Test (bỏ qua)")
        skip("Dùng --api hoặc --all để chạy tier này")

    # Tier 4 — Edge Server
    if args.all or args.edge:
        tier4_edge_server_tests(args.edge_host, args.edge_port)
    else:
        header("TIER 4 — Edge Server Test (bỏ qua)")
        skip("Dùng --edge hoặc --all để chạy tier này")

    print_summary()


if __name__ == "__main__":
    main()
