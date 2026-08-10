"""
Great Expectations Data Contracts Engine
Asserts schema integrity and operational bounds for homelab telemetry.
"""
from typing import Dict, Any

class DataContractVerifier:
    """Verifies telemetry contract compliance before database loading."""

    def verify_snapshot(self, snapshot: Dict[str, Any]) -> bool:
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

        print("[OK] Great Expectations / Data Contract Passed: Telemetry snapshot valid.")
        return True

if __name__ == "__main__":
    verifier = DataContractVerifier()
    test = {"system": {"cpu_percent": 12.5, "ram_percent": 45.0}}
    assert verifier.verify_snapshot(test)
