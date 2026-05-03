import json
import random
from pathlib import Path

random.seed(42)

device = {
    "device_id": "ssd-eval-board-a3",
    "firmware": {"version": "1.4.2"},
    "registers": {
        "BOOT_STATUS": "0x01",
        "PCIE_LINK_WIDTH": "x4",
        "PCIE_SPEED": "Gen4",
        "NVME_READY": "0x01",
        "THERMAL_STATE": "nominal",
        "POWER_STATE": "PS0",
    },
    "features": {
        "smart_health": True,
        "error_log_page": True,
        "power_state_transition": False,
        "secure_erase": True,
        "telemetry_log": True,
    },
    "metrics": {
        "read_latency_us_p99": 820,
        "write_latency_us_p99": 1250,
        "thermal_celsius_peak": 71,
        "io_error_rate_ppm": 3,
        "sustained_iops": 94000,
        "nand_program_us": 680,
        "pcie_retrain_count": 1,
        "firmware_boot_ms": 420,
    },
}

base_tests = [
    ("Firmware version supports validation plan", "firmware_min_version", "firmware", "FW-001", "1.4.0", "Update firmware before full regression."),
    ("PCIe link trains to x4", "register_equals", "pcie", "PCIE-010", "x4", "Check lane config and retimer logs."),
    ("NVMe controller ready bit is set", "register_equals", "nvme", "NVME-002", "0x01", "Collect controller initialization trace."),
    ("Read latency p99 below target", "metric_max", "performance", "PERF-101", 900, "Inspect queue depth and firmware throttling."),
    ("Write latency p99 below target", "metric_max", "performance", "PERF-102", 1100, "Review NAND program latency and write cache behavior."),
    ("Peak thermal inside envelope", "metric_max", "thermal", "THERM-004", 75, "Check fan curve and workload duty cycle."),
    ("Error log page available", "feature_enabled", "diagnostics", "DIAG-020", None, "Enable diagnostic feature flag and rerun smoke test."),
]

tests = []
for name, kind, subsystem, req, expected, triage in base_tests:
    test = {
        "name": name,
        "kind": kind,
        "subsystem": subsystem,
        "requirement": req,
        "expected": expected,
        "triage": triage,
    }
    if kind == "register_equals":
        test["register"] = "PCIE_LINK_WIDTH" if subsystem == "pcie" else "NVME_READY"
    if kind == "metric_max":
        test["metric"] = {
            "PERF-101": "read_latency_us_p99",
            "PERF-102": "write_latency_us_p99",
            "THERM-004": "thermal_celsius_peak",
        }[req]
    if kind == "feature_enabled":
        test["feature"] = "error_log_page"
    tests.append(test)

subsystems = ["firmware", "pcie", "nvme", "performance", "thermal", "diagnostics", "power"]
metric_options = [
    ("read_latency_us_p99", "metric_max", 950),
    ("write_latency_us_p99", "metric_max", 1150),
    ("thermal_celsius_peak", "metric_max", 78),
    ("io_error_rate_ppm", "metric_max", 5),
    ("sustained_iops", "metric_min", 88000),
    ("nand_program_us", "metric_max", 640),
    ("pcie_retrain_count", "metric_max", 0),
    ("firmware_boot_ms", "metric_max", 500),
]

for i in range(8, 201):
    metric, kind, expected = random.choice(metric_options)
    subsystem = random.choice(subsystems)
    tests.append({
        "name": f"{subsystem.upper()} validation case {i:03d}",
        "kind": kind,
        "subsystem": subsystem,
        "requirement": f"{subsystem.upper()}-{100+i}",
        "metric": metric,
        "expected": expected,
        "triage": f"Review {subsystem} telemetry, compare expected vs actual, and rerun case {i:03d}.",
    })

Path("samples").mkdir(exist_ok=True)
Path("samples/device.json").write_text(json.dumps(device, indent=2), encoding="utf-8")
Path("samples/tests.json").write_text(json.dumps(tests, indent=2), encoding="utf-8")
print(f"[OK] Generated {len(tests)} firmware validation tests")