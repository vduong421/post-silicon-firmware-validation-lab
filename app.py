import argparse
import json
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_test(device, test):
    kind = test["kind"]
    requirement = test["requirement"]
    subsystem = test["subsystem"]
    name = test["name"]
    expected = test.get("expected")
    actual = None
    passed = False

    if kind == "firmware_min_version":
        actual = device["firmware"]["version"]
        passed = tuple(map(int, actual.split("."))) >= tuple(map(int, expected.split(".")))
    elif kind == "register_equals":
        actual = device["registers"].get(test["register"])
        passed = actual == expected
    elif kind == "metric_max":
        actual = device["metrics"].get(test["metric"])
        passed = actual is not None and actual <= expected
    elif kind == "metric_min":
        actual = device["metrics"].get(test["metric"])
        passed = actual is not None and actual >= expected
    elif kind == "feature_enabled":
        actual = device["features"].get(test["feature"], False)
        passed = actual is True
    else:
        actual = "unsupported"

    return {
        "name": name,
        "kind": kind,
        "requirement": requirement,
        "subsystem": subsystem,
        "expected": expected,
        "actual": actual,
        "status": "PASS" if passed else "FAIL",
        "triage": "" if passed else test.get("triage", "Investigate failing validation case."),
    }


def summarize(results):
    total = len(results)
    passed = sum(1 for row in results if row["status"] == "PASS")
    by_subsystem = {}
    for row in results:
        bucket = by_subsystem.setdefault(row["subsystem"], {"PASS": 0, "FAIL": 0})
        bucket[row["status"]] += 1
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 3) if total else 0,
        "by_subsystem": by_subsystem,
        "failed_requirements": sorted({row["requirement"] for row in results if row["status"] == "FAIL"}),
    }


def write_markdown(path, device, results, summary):
    lines = [
        "# Firmware Validation Report",
        "",
        f"Device: {device['device_id']}",
        f"Firmware: {device['firmware']['version']}",
        f"Pass rate: {summary['pass_rate']:.1%}",
        "",
        "## Subsystem Summary",
        "",
    ]
    for subsystem, counts in summary["by_subsystem"].items():
        lines.append(f"- {subsystem}: {counts['PASS']} pass, {counts['FAIL']} fail")
    lines += ["", "## Failed Requirements", ""]
    if summary["failed_requirements"]:
        lines += [f"- {req}" for req in summary["failed_requirements"]]
    else:
        lines.append("- None")
    lines += ["", "## Test Results", ""]
    for row in results:
        lines.append(
            f"- {row['status']} | {row['requirement']} | {row['name']} | actual={row['actual']} expected={row['expected']}"
        )
        if row["triage"]:
            lines.append(f"  - Triage: {row['triage']}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", required=True)
    parser.add_argument("--tests", required=True)
    parser.add_argument("--out", default="report")
    args = parser.parse_args()

    device = load_json(args.device)
    tests = load_json(args.tests)
    results = [check_test(device, test) for test in tests]
    summary = summarize(results)
    report = {"device": device["device_id"], "summary": summary, "results": results}

    out = Path(args.out)
    Path(f"{out}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(f"{out}.md", device, results, summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
