# Post-Silicon Firmware Validation Lab

Role fit: firmware validation, post-silicon validation, hardware test, embedded test automation, SSD/NVMe validation, and computer engineering roles.

This project simulates a small hardware validation workflow: register checks, firmware version checks, IO stress cases, latency thresholds, failure signatures, and requirement coverage. It is intentionally lightweight, but the structure mirrors what validation teams care about: reproducible tests, clear pass/fail criteria, triage notes, and machine-readable reports.

## Features

- Loads device and test definitions from JSON.
- Runs firmware, register, IO, thermal, and latency validation checks.
- Produces JSON and Markdown reports for engineering review.
- Groups failures by subsystem and requirement ID.
- Includes sample device data and validation cases.

## Run

```bash
python app.py --device samples/device.json --tests samples/tests.json --out report
```

Outputs:

- `report.json`
- `report.md`

## Engineering Impact
- Built a Python firmware validation workflow that checks simulated device registers, firmware versions, IO paths, latency limits, thermal limits, and requirement coverage.
- Designed JSON-driven validation cases with pass/fail criteria and generated engineering-ready JSON and Markdown reports.
- Implemented failure triage by subsystem and requirement ID to mirror post-silicon and hardware validation review workflows.

## Project Workbench

Launch the production-style desktop workbench with:

```powershell
launch-workbench.bat
```

What it adds:

- Local-first AI copilot using `google/gemma-4-e4b` by default
- Operator-focused workbench for reviewing real project inputs and outputs
- System design, production-impact, and operational brief generation on demand
- Grounded responses based on this project's README, sample files, and deterministic outputs

