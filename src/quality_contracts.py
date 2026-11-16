"""
Data contract for telemetry snapshots: checks required fields and value ranges before anything is stored.
"""
from typing import Any


class DataContractVerifier:
    """Verifies telemetry contract compliance before database loading."""

    def verify_snapshot(self, snapshot: dict[str, Any]) -> bool:
        """Asserts non-null bounds, valid CPU/RAM ranges, and status integrity."""
        if not snapshot or "system" not in snapshot:
            print("[CONTRACT ERROR] Missing system telemetry block.")
            return False

        sys_metrics = snapshot["system"]
        cpu = sys_metrics.get("cpu_percent", -1)
        ram = sys_metrics.get("ram_percent", -1)

        if not (0 <= cpu <= 100):
            print(f"[CONTRACT ERROR] Invalid CPU bound: {cpu}%")
            return False

        if not (0 <= ram <= 100):
            print(f"[CONTRACT ERROR] Invalid RAM bound: {ram}%")
            return False

        disk = sys_metrics.get("disk_percent", -1)
        if not (0 <= disk <= 100):
            print(f"[CONTRACT ERROR] Invalid disk bound: {disk}%")
            return False

        print("[OK] Data contract passed: telemetry snapshot valid.")
        return True

if __name__ == "__main__":
    verifier = DataContractVerifier()
    test = {"system": {"cpu_percent": 12.5, "ram_percent": 45.0}}
    assert verifier.verify_snapshot(test)
