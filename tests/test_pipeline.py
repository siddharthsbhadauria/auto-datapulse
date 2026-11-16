import pytest

from src.collector import TelemetryCollector
from src.quality_contracts import DataContractVerifier

GOOD = {"system": {"cpu_percent": 12.5, "ram_percent": 45.0, "disk_percent": 30.0}}


def test_contract_accepts_valid_snapshot():
    assert DataContractVerifier().verify_snapshot(GOOD)


@pytest.mark.parametrize("field", ["cpu_percent", "ram_percent", "disk_percent"])
def test_contract_rejects_out_of_range(field):
    bad = {"system": {**GOOD["system"], field: 140.0}}
    assert not DataContractVerifier().verify_snapshot(bad)


def test_contract_rejects_missing_block():
    assert not DataContractVerifier().verify_snapshot({})


def test_collector_reads_real_host_metrics():
    snap = TelemetryCollector().capture_metrics()
    assert snap["timestamp"].endswith("Z")
    assert DataContractVerifier().verify_snapshot(snap)
