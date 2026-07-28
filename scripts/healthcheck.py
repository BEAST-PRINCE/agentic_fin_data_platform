import sys
import os
import time
import socket
import argparse
import urllib.request
import urllib.error

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "healthcheck.log")

def log(msg: str):
    print(msg)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def check_tcp(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def check_http(url: str, timeout: float = 3.0) -> bool:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'HealthCheck/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 204, 301, 302)
    except Exception:
        return False

def check_duckdb() -> bool:
    try:
        import duckdb
        conn = duckdb.connect(":memory:")
        res = conn.execute("SELECT 1").fetchone()
        conn.close()
        return res[0] == 1
    except Exception:
        return False

SERVICES = {
    "Kafka": ("tcp", "127.0.0.1", 9092),
    "MinIO": ("http", "http://localhost:9000/minio/health/live", 9000),
    "Qdrant": ("http", "http://localhost:6333/readyz", 6333),
    "Prometheus": ("http", "http://localhost:9090/-/healthy", 9090),
    "Grafana": ("http", "http://localhost:3000/api/health", 3000),
    "DuckDB": ("duckdb", None, None),
    "FastAPI": ("http", "http://localhost:8000/health", 8000),
    "Dashboard": ("http", "http://localhost:5173", 5173)
}

INFRA_SERVICES = ["Kafka", "MinIO", "Qdrant", "Prometheus", "Grafana", "DuckDB"]

def run_single_check(name: str) -> bool:
    stype, target, port = SERVICES[name]
    if stype == "tcp":
        return check_tcp(target, port)
    elif stype == "http":
        if check_http(target):
            return True
        # Fallback to simple TCP port check if HTTP endpoint returns non-200 or is loading
        return check_tcp("127.0.0.1", port)
    elif stype == "duckdb":
        return check_duckdb()
    return False

def main():
    parser = argparse.ArgumentParser(description="Platform Health Checker")
    parser.add_argument("--mode", choices=["full", "infra", "backend", "frontend"], default="full", help="Check mode")
    parser.add_argument("--wait", action="store_true", help="Wait/retry until target services are ready")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retries when waiting")
    parser.add_argument("--interval", type=float, default=5.0, help="Interval in seconds between retries")
    args = parser.parse_args()

    # Clear previous log on fresh invocation
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"=== Healthcheck Started: {time.ctime()} (Mode: {args.mode}) ===\n")

    if args.mode == "infra":
        targets = INFRA_SERVICES
    elif args.mode == "backend":
        targets = ["FastAPI"]
    elif args.mode == "frontend":
        targets = ["Dashboard"]
    else:
        targets = list(SERVICES.keys())

    if args.wait:
        log(f"Waiting for {args.mode} services to become ready (Max retries: {args.max_retries})...")
        for attempt in range(1, args.max_retries + 1):
            log(f"\n--- Attempt {attempt} of {args.max_retries} ---")
            all_ready = True
            for name in targets:
                ok = run_single_check(name)
                status_str = "Ready" if ok else "Not Ready"
                log(f"{name:<18} .... {status_str}")
                if not ok:
                    all_ready = False
            if all_ready:
                log(f"\nAll {args.mode} services are Ready!")
                sys.exit(0)
            if attempt < args.max_retries:
                time.sleep(args.interval)
        
        log(f"\n[ERROR] Timeout waiting for {args.mode} services.")
        sys.exit(1)
    else:
        log("Platform Health\n")
        all_ok = True
        for name in targets:
            ok = run_single_check(name)
            status_str = "PASS" if ok else "FAIL"
            log(f"{name:<18} .... {status_str}")
            if not ok:
                all_ok = False
        
        if not all_ok:
            sys.exit(1)
        sys.exit(0)

if __name__ == "__main__":
    main()
