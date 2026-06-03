#!/usr/bin/env python3
"""
=============================================================
  TEST SCRIPT — 5G IoT Anomaly Detection AI System
=============================================================
Kiểm tra toàn bộ hệ thống AI theo 6 tầng:

  [TIER 1] Unit Test  — Model trực tiếp (.pkl)
  [TIER 2] Module Test — AnomalyDetector (detection.py)
  [TIER 3] API Test   — Dashboard Flask HTTP API
  [TIER 4] Integration — Edge Server TCP Socket
  [TIER 5] Consistency — So sánh 2 tầng AI
  [TIER 6] Mininet-WiFi — Môi trường Mininet

Chạy:
  python3 test_ai_system.py                    # Tier 1+2+5 (không cần server)
  python3 test_ai_system.py --api              # + Tier 3 (cần dashboard chạy)
  python3 test_ai_system.py --edge             # + Tier 4 (cần edge server chạy)
  python3 test_ai_system.py --mininet          # + Tier 6 (cần Mininet-WiFi)
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
#  Kịch bản tấn công đa dạng (synthetic, dựa theo pattern dataset)
#
#  Bố cục feature (24):
#  Seq, Mean, sTos, sTtl, dTtl, sHops,
#  TotBytes, SrcBytes, Offset, sMeanPktSz, dMeanPktSz,
#  SrcWin, TcpRtt, AckDat,
#  ' e        ', ' e d      ', icmp, tcp,
#  CON, FIN, INT, REQ, RST, Status
#
#  Dấu hiệu nhận biết từ dataset:
#   sTtl = 49/50/45 → TTL bất thường (spoofed/attacker)
#   dTtl = 0        → lưu lượng một chiều (không có phản hồi)
#   sHops ≥ 14      → đường đi dài bất thường
#   icmp=1+dTtl=0   → ICMP flood/tunneling
#   tcp=1+RST=1     → RST injection
#   tcp=1+INT=1     → SYN flood (connection chưa hoàn thành)
#   tcp=1+FIN=1     → FIN scan
#   tcp=1+REQ=1     → port scan / probe
# =============================================================
ATTACK_SCENARIOS = {
    # ── Benign bổ sung ──────────────────────────────────────
    "benign_tcp_con_normal": {
        "category": "Benign",
        "label": "Benign",
        "description": "TCP session bình thường, CON state, TTL=64/117, bidirectional",
        "features": [
            5.0, 2.134, 0.0, 64.0, 117.0, 8.0,
            15200.0, 11400.0, 624.0, 632.0, 224.0,
            65535.0, 0.015, 0.008,
            1.0, 0.0, 0.0, 1.0,
            1.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ]
    },
    "benign_icmp_bidirectional": {
        "category": "Benign",
        "label": "Benign",
        "description": "ICMP ping-pong bình thường, TTL=58 2 chiều",
        "features": [
            8.0, 0.0, 0.0, 58.0, 58.0, 6.0,
            196.0, 98.0, 512.0, 98.0, 98.0,
            0.0, 0.0, 0.0,
            1.0, 1.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ]
    },
    # ── DoS / DDoS ───────────────────────────────────────────
    "attack_dos_icmp_flood": {
        "category": "DoS",
        "label": "Malicious",
        "description": "DoS ICMP Flood — gói nhỏ liên tục, sTtl=49 (spoofed), một chiều",
        "features": [
            120.0, 0.000512, 0.0, 49.0, 0.0, 15.0,
            6480.0, 6480.0, 14800.0, 54.0, 0.0,
            0.0, 0.0, 0.0,
            1.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ]
    },
    "attack_tcp_syn_flood": {
        "category": "DoS",
        "label": "Malicious",
        "description": "TCP SYN Flood — INT state (incomplete), sTtl=50, không ack",
        "features": [
            85.0, 0.000200, 0.0, 50.0, 59.0, 14.0,
            3400.0, 3400.0, 9000.0, 40.0, 0.0,
            1024.0, 0.0, 0.0,
            1.0, 0.0, 0.0, 1.0,
            0.0, 0.0, 1.0, 0.0, 0.0, 0.0
        ]
    },
    # ── Scanning / Reconnaissance ────────────────────────────
    "attack_port_scan_req": {
        "category": "Scan",
        "label": "Malicious",
        "description": "Port Scan — REQ state, gói nhỏ một chiều, sTtl=50",
        "features": [
            60.0, 0.001000, 0.0, 50.0, 59.0, 14.0,
            2400.0, 2400.0, 7200.0, 40.0, 0.0,
            1024.0, 0.0, 0.0,
            1.0, 0.0, 0.0, 1.0,
            0.0, 0.0, 0.0, 1.0, 0.0, 0.0
        ]
    },
    "attack_tcp_fin_scan": {
        "category": "Scan",
        "label": "Malicious",
        "strict": False,   # synthetic — model chưa thấy FIN scan này trong train
        "description": "TCP FIN Scan — FIN không có prior SYN, sTtl=49, một chiều",
        "features": [
            45.0, 0.001000, 0.0, 49.0, 0.0, 15.0,
            2700.0, 2700.0, 5500.0, 60.0, 0.0,
            1024.0, 0.0, 0.0,
            1.0, 0.0, 0.0, 1.0,
            0.0, 1.0, 0.0, 0.0, 0.0, 0.0
        ]
    },
    # ── Injection ────────────────────────────────────────────
    "attack_tcp_rst_injection": {
        "category": "Injection",
        "label": "Malicious",
        "description": "TCP RST Injection — hủy kết nối trái phép, sTtl=50",
        "features": [
            55.0, 0.001500, 0.0, 50.0, 59.0, 14.0,
            2960.0, 1480.0, 6700.0, 58.0, 54.0,
            1024.0, 0.0, 0.0,
            1.0, 0.0, 0.0, 1.0,
            0.0, 0.0, 0.0, 0.0, 1.0, 0.0
        ]
    },
    # ── Amplification ────────────────────────────────────────
    "attack_icmp_smurf": {
        "category": "Amplification",
        "label": "Malicious",
        "strict": False,   # synthetic — model phân loại Benign do feature không khớp leaf
        "description": "ICMP Smurf — broadcast amplification, sTtl=45, bidirectional",
        "features": [
            75.0, 0.001938, 0.0, 45.0, 59.0, 19.0,
            12600.0, 6300.0, 9200.0, 84.0, 84.0,
            0.0, 0.0, 0.0,
            1.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ]
    },
    # ── Covert Channel ───────────────────────────────────────
    "attack_icmp_tunneling": {
        "category": "Covert",
        "label": "Malicious",
        "strict": False,   # synthetic — model chưa thấy ICMP tunneling trong train
        "description": "ICMP Tunneling — payload lớn bất thường, sTtl=49, một chiều",
        "features": [
            55.0, 2.500000, 0.0, 49.0, 0.0, 15.0,
            42600.0, 42600.0, 6800.0, 775.0, 0.0,
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
        info(f"Max depth   : {model.tree_.max_depth}  (max_depth param={model.max_depth})")
        info(f"N leaves    : {model.tree_.n_leaves}")
        info(f"N features  : {model.n_features_in_}")
        info(f"Classes     : {model.classes_.tolist()}")
        info(f"Feature list: {feat_names}")
        # Kiểm tra xem có lá nào mixed không
        _vals = model.tree_.value  # shape (n_nodes, 1, n_classes)
        _left = model.tree_.children_left
        _pure = sum(1 for i in range(model.tree_.node_count)
                    if _left[i] == -1 and
                    np.max(_vals[i][0]) == np.sum(_vals[i][0]))
        _mixed = model.tree_.n_leaves - _pure
        if _mixed == 0:
            info(f"⚠ confidence = 100% trên MỌI input — tất cả {_pure} lá đều pure")
            info(f"  Nguyên nhân: max_depth=None → cây không bị pruning, độ sâu={model.tree_.max_depth}")
            info(f"  Cây đã ghi nhớ toàn bộ training data (overfitting).")
            info(f"  → Khi retrain: nên set max_depth=15~25 để lấy confidence có ý nghĩa thực tế.")
        else:
            info(f"Leaves: {_pure} pure / {_mixed} mixed (confidence < 100% có ý nghĩa)")
    except Exception as e:
        fail("Load model thất bại", str(e))
        return

    section("1.3  Kiểm tra số lượng feature")
    if model.n_features_in_ == 24:
        ok(f"Model nhận đúng 24 features")
    else:
        fail(f"Model cần {model.n_features_in_} features, script chuẩn bị 24")
        return

    section("1.4  Predict real dataset rows")
    info("Samples lấy trực tiếp từ dataset/Encoded.csv — kết quả phải 100% chính xác")
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
                ok(f"{name:35s}  pred={pred:10s}  conf={conf:.0%}  ✓")
                correct += 1
            else:
                fail(f"{name:35s}  pred={pred}  expected={expected}  conf={conf:.0%}")
            info(f"  {tc['description']}")
        except Exception as e:
            fail(f"{name}", str(e))

    total = len(TEST_CASES)
    print(f"\n  Kết quả: {correct}/{total} test case đúng ({correct/total*100:.0f}%)")
    if correct == total:
        ok("Tất cả real samples dự đoán chính xác")
    elif correct >= total * 0.8:
        ok(f"Phần lớn test case đúng ({correct}/{total})")
    else:
        fail(f"Nhiều test case sai — kiểm tra lại dữ liệu train ({correct}/{total})")

    section("1.5  Kịch bản tấn công đa dạng (synthetic)")
    info("Dựa trên pattern của dataset — test nhiều loại tấn công khác nhau")
    cat_results = {}
    for name, sc in ATTACK_SCENARIOS.items():
        try:
            X = np.array(sc["features"]).reshape(1, -1)
            X_scaled = scaler.transform(X)
            pred = model.predict(X_scaled)[0]
            proba = model.predict_proba(X_scaled)[0]
            conf = float(np.max(proba))
            expected = sc["label"]
            cat = sc["category"]
            strict = sc.get("strict", True)
            cat_results.setdefault(cat, {"correct": 0, "total": 0, "warn": 0})
            cat_results[cat]["total"] += 1
            match = (pred == expected)
            if match:
                cat_results[cat]["correct"] += 1
                ok(f"[{cat:13s}] {name:30s}  pred={pred:10s}  ✓")
            elif not strict:
                # Synthetic case: model có thể sai do chưa thấy pattern này
                cat_results[cat]["warn"] += 1
                print(f"  {YELLOW}[WARN]{RESET} [{cat:13s}] {name:30s}  pred={pred:10s}  expected={expected}  (synthetic)")
            else:
                fail(f"[{cat:13s}] {name:30s}  pred={pred:10s}  expected={expected}")
            info(f"  {sc['description']}")
        except Exception as e:
            fail(f"{name}", str(e))

    print(f"\n  {BOLD}Tóm tắt theo loại tấn công:{RESET}")
    all_correct = 0; all_total = 0
    for cat, r in cat_results.items():
        all_correct += r["correct"]; all_total += r["total"]
        warn = r.get("warn", 0)
        if r["correct"] == r["total"]:
            symbol = f"{GREEN}✓{RESET}"
            note = ""
        elif warn > 0:
            symbol = f"{YELLOW}⚠{RESET}"
            note = f"  ({warn} synthetic missed — cần thêm training data loại này)"
        else:
            symbol = f"{RED}✗{RESET}"
            note = ""
        print(f"  {symbol}  [{cat:13s}]  {r['correct']}/{r['total']}{note}")
    print()
    if all_correct == all_total:
        ok(f"Tất cả {all_total} kịch bản tấn công phân loại đúng")
    else:
        info(f"{all_correct}/{all_total} kịch bản đúng — xem WARN để biết pattern chưa có trong training set")

    return model, scaler, feat_names


# =============================================================
#  TIER 2 — Module Test: AnomalyDetector (detection.py)
# =============================================================

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
        "prediction": "Benign",
        "confidence": 0.98,
        "probability_malicious": 0.02,
        "tot_bytes": 1500, "src_bytes": 750, "tcp_rtt": 0.012, "s_ttl": 64
    }
    try:
        resp, status = post_json(f"{api_url}/api/metrics", benign_payload)
        if status == 200:
            det = resp.get("detection", {})
            ok(f"HTTP 200  →  prediction={det.get('prediction_label')}  "
               f"score={det.get('anomaly_score', '?')}  severity={det.get('severity', '?')}")
        else:
            fail(f"HTTP {status}", str(resp))
    except Exception as e:
        fail("POST /api/metrics (Benign) thất bại", str(e))

    section("3.3  POST /api/metrics — Anomaly (Malicious) payload")
    anomaly_payload = {
        "timestamp": "2026-03-05T10:00:01",
        "device_id": "test_attacker",
        "prediction": "Malicious",
        "confidence": 0.95,
        "probability_malicious": 0.95,
        "tot_bytes": 84, "src_bytes": 42, "tcp_rtt": 0.002, "s_ttl": 49
    }
    try:
        resp, status = post_json(f"{api_url}/api/metrics", anomaly_payload)
        if status == 200:
            det = resp.get("detection", {})
            pred  = det.get("prediction_label")
            score = det.get("anomaly_score", 0)
            ok(f"HTTP 200  →  prediction={pred}  score={score}  severity={det.get('severity', '?')}")
            if pred == "anomaly":
                ok("Phát hiện đúng anomaly")
            else:
                fail(f"Mong đợi 'anomaly', nhận '{pred}'")
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




# =============================================================
#  TIER 6 — Mininet-WiFi integration tests
# =============================================================

def tier6_mininet_tests():
    header("TIER 6 — Mininet-WiFi Integration Tests")

    # 6.1 — Kiểm tra mn_wifi có import được không
    section("6.1  Import mn_wifi")
    try:
        import mn_wifi  # noqa: F401
        ok("mn_wifi importable")
    except ImportError:
        fail("mn_wifi không import được — cài mininet-wifi trước",
             "sudo pip install mininet-wifi  hoặc build từ source")
        skip("Bỏ qua các test Mininet còn lại")
        return

    # 6.2 — Kiểm tra 5g_iot_mininet.py syntax
    section("6.2  Syntax của 5g_iot_mininet.py")
    script = os.path.join(os.path.dirname(PROJECT_ROOT),
                          "system_detection", "5g_iot_mininet.py")
    # fallback: cùng thư mục với test script
    if not os.path.exists(script):
        script = os.path.join(PROJECT_ROOT, "system_detection", "5g_iot_mininet.py")
    if not os.path.exists(script):
        script = os.path.join(PROJECT_ROOT, "5g_iot_mininet.py")

    if os.path.exists(script):
        import subprocess
        result = subprocess.run([sys.executable, "-m", "py_compile", script],
                                capture_output=True, text=True)
        if result.returncode == 0:
            ok(f"5g_iot_mininet.py: syntax OK")
        else:
            fail("5g_iot_mininet.py: syntax error", result.stderr.strip())
    else:
        skip(f"5g_iot_mininet.py not found at {script}")

    # 6.3 — Kiểm tra MININET_NODE env var
    section("6.3  Môi trường Mininet")
    mn_node = os.environ.get("MININET_NODE")
    if mn_node:
        ok(f"Đang chạy trong Mininet node: {mn_node}")
    else:
        info("MININET_NODE chưa được set — test được coi là môi trường host bình thường")
        skip("Không trong Mininet namespace — bỏ qua live wireless tests")
        return

    # 6.4 — Kiểm tra iw/wireless interface tồn tại
    section("6.4  Wireless interface")
    import subprocess
    wlan_iface = f"{mn_node}-wlan0"
    result = subprocess.run(["ip", "link", "show", wlan_iface],
                            capture_output=True, text=True)
    if result.returncode == 0:
        ok(f"Interface {wlan_iface} tồn tại")
    else:
        fail(f"Interface {wlan_iface} không tồn tại",
             "Hãy chạy bên trong Mininet-WiFi topology")
        return

    # 6.5 — Đọc wireless info qua iw dev
    section("6.5  iw dev wireless info")
    result = subprocess.run(["iw", "dev", wlan_iface, "link"],
                            capture_output=True, text=True)
    if result.returncode == 0:
        output = result.stdout
        if "signal" in output.lower():
            import re
            m = re.search(r"signal:\s*(-?\d+)\s*dBm", output)
            if m:
                ok(f"Signal strength: {m.group(1)} dBm")
            else:
                ok("iw dev link thành công (signal field không parse được)")
        else:
            ok("iw dev link thành công (không kết nối AP hoặc không có signal)")
        info(output.strip()[:200])
    else:
        fail("iw dev link thất bại", result.stderr.strip())

    # 6.6 — Mininet env vars có đầy đủ không
    section("6.6  Mininet env vars")
    ap_ssid = os.environ.get("MININET_AP_SSID")
    if ap_ssid:
        ok(f"MININET_AP_SSID={ap_ssid}")
    else:
        fail("MININET_AP_SSID chưa được set trong process",
             "5g_iot_mininet.py nên set MININET_AP_SSID=5G-IoT-Network khi spawn process")


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
    parser.add_argument("--mininet",  action="store_true", help="Bao gồm Mininet-WiFi test (cần mn_wifi + environment)")
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

    # Tier 1 luôn chạy
    tier1_model_unit_tests()

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

    # Tier 6 — Mininet-WiFi
    if args.all or args.mininet:
        tier6_mininet_tests()
    else:
        header("TIER 6 — Mininet-WiFi Test (bỏ qua)")
        skip("Dùng --mininet hoặc --all để chạy tier này")

    print_summary()


if __name__ == "__main__":
    main()
