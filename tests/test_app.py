from app import check_test, summarize


def test_check_test_passes_firmware_and_register_cases():
    device = {
        "firmware": {"version": "1.4.2"},
        "registers": {"NVME_READY": "0x01"},
        "metrics": {},
        "features": {},
    }

    fw = check_test(device, {
        "kind": "firmware_min_version",
        "requirement": "FW-001",
        "subsystem": "firmware",
        "name": "firmware version",
        "expected": "1.4.0",
    })
    reg = check_test(device, {
        "kind": "register_equals",
        "requirement": "NVME-002",
        "subsystem": "nvme",
        "name": "ready bit",
        "register": "NVME_READY",
        "expected": "0x01",
    })

    assert fw["status"] == "PASS"
    assert reg["status"] == "PASS"


def test_summarize_tracks_failed_requirements():
    results = [
        {"status": "PASS", "subsystem": "firmware", "requirement": "FW-001"},
        {"status": "FAIL", "subsystem": "performance", "requirement": "PERF-102"},
    ]

    summary = summarize(results)

    assert summary["total"] == 2
    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert summary["failed_requirements"] == ["PERF-102"]
