"""
Telemetry collector: reads host CPU, memory, disk usage and disk I/O counters with psutil.
"""
from datetime import UTC, datetime
from typing import Any

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

class TelemetryCollector:
    """Collects one telemetry snapshot from the host."""

    def capture_metrics(self) -> dict[str, Any]:
        """Returns CPU, RAM, disk usage and disk I/O for this host."""
        if not HAS_PSUTIL:
            # Never write placeholder numbers: a fake reading would poison the anomaly models downstream.
            raise RuntimeError("psutil is not installed; cannot read host metrics.")
        cpu_usage = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()

        cpu_val = float(cpu_usage)
        ram_total = round(mem.total / (1024 ** 3), 2)
        ram_used = round(mem.used / (1024 ** 3), 2)
        ram_pct = float(mem.percent)
        disk_total = round(disk.total / (1024 ** 3), 2)
        disk_used = round(disk.used / (1024 ** 3), 2)
        disk_pct = float(disk.percent)
        r_bytes = disk_io.read_bytes if disk_io else 0
        w_bytes = disk_io.write_bytes if disk_io else 0
        snapshot = {
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "system": {
                "cpu_percent": cpu_val,
                "ram_total_gb": ram_total,
                "ram_used_gb": ram_used,
                "ram_percent": ram_pct,
                "disk_total_gb": disk_total,
                "disk_used_gb": disk_used,
                "disk_percent": disk_pct
            },
            "disk_io": {
                "read_bytes": r_bytes,
                "write_bytes": w_bytes
            },
            "status": "HEALTHY"
        }
        return snapshot

if __name__ == "__main__":
    collector = TelemetryCollector()
    metrics = collector.capture_metrics()
    print("[INFO] Captured Telemetry Snapshot:")
    print(metrics)
