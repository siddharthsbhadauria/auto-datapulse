"""
Auto-DataPulse Main Pipeline Entrypoint & Daemon Loop
Orchestrates telemetry collection, Great Expectations contract verification, DuckDB persistence, and daily Git report publishing.
"""
import os
import sys
import json
import time
from datetime import datetime, timezone

from src.collector import TelemetryCollector
from src.quality_contracts import DataContractVerifier
from src.git_publisher import GitPublisher

def run_pipeline():
    print("[INFO] Executing Auto-DataPulse Pipeline on UGREEN NAS...")

    # 1. Capture Telemetry Snapshot
    collector = TelemetryCollector()
    snapshot = collector.capture_metrics()

    # 2. Great Expectations Data Contract Verification
    verifier = DataContractVerifier()
    if not verifier.verify_snapshot(snapshot):
        print("[FATAL] Telemetry contract check failed! Aborting pipeline execution step.")
        return

    # 3. Persistence (DuckDB / JSON Backup)
    os.makedirs("data", exist_ok=True)
    db_path = os.path.join("data", "telemetry.duckdb")
    json_path = os.path.join("data", "telemetry_snapshots.jsonl")

    # Append to JSONL Backup
    with open(json_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot) + "\n")
        
    try:
        import duckdb
        conn = duckdb.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_snapshots (
                timestamp VARCHAR,
                cpu_percent DOUBLE,
                ram_used_gb DOUBLE,
                ram_total_gb DOUBLE,
                ram_percent DOUBLE,
                disk_used_gb DOUBLE,
                disk_total_gb DOUBLE,
                disk_percent DOUBLE,
                status VARCHAR
            )
        """)
        
        sys_info = snapshot["system"]
        conn.execute("""
            INSERT INTO telemetry_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot["timestamp"],
            sys_info["cpu_percent"],
            sys_info["ram_used_gb"],
            sys_info["ram_total_gb"],
            sys_info["ram_percent"],
            sys_info["disk_used_gb"],
            sys_info["disk_total_gb"],
            sys_info["disk_percent"],
            snapshot["status"]
        ))
        conn.close()
        print(f"[SUCCESS] Saved snapshot to DuckDB database: {db_path}")
    except ImportError:
        print(f"[SUCCESS] Saved snapshot to JSONL storage: {json_path}")
    except Exception as e:
        print(f"[PERSISTENCE NOTICE] {e}")

    # 4. Git Daily Report Publishing via API
    publisher = GitPublisher()
    publisher.publish_daily_report(snapshot)

    print("[SUCCESS] Auto-DataPulse Pipeline step completed successfully.")

def start_daemon():
    poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "900"))
    print(f"==================================================================")
    print(f"🚀 Auto-DataPulse Homelab Daemon Started")
    print(f"⏱️  Polling Interval: {poll_interval} seconds ({poll_interval // 60} minutes)")
    print(f"==================================================================")

    while True:
        try:
            run_pipeline()
        except Exception as e:
            print(f"[ERROR] Daemon pipeline error: {e}")

        print(f"⏳ Sleeping for {poll_interval} seconds ({poll_interval // 60}m) before next pulse...\n")
        time.sleep(poll_interval)

if __name__ == "__main__":
    # If running in GitHub Actions CI or with --once, execute a fast single validation pass (~25s)
    if os.getenv("CI", "false").lower() == "true" or "--once" in sys.argv:
        print("[INFO] CI environment detected. Running single validation pass...")
        run_pipeline()
    else:
        start_daemon()
