import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8005


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_test(device, test):
    kind = test["kind"]
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

    return {
        "name": test["name"],
        "requirement": test["requirement"],
        "subsystem": test["subsystem"],
        "expected": expected,
        "actual": actual,
        "status": "PASS" if passed else "FAIL",
        "triage": "" if passed else test.get("triage", ""),
    }


def summarize(results):
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    fail = total - passed

    by_sub = {}
    by_kind = {}
    failed_rows = [r for r in results if r["status"] == "FAIL"]

    for r in results:
        by_sub.setdefault(r["subsystem"], {"PASS": 0, "FAIL": 0})
        by_sub[r["subsystem"]][r["status"]] += 1
        by_kind[r.get("kind", "unknown")] = by_kind.get(r.get("kind", "unknown"), 0) + 1

    subsystem_pass_rates = {}
    for subsystem, counts in by_sub.items():
        sub_total = counts["PASS"] + counts["FAIL"]
        subsystem_pass_rates[subsystem] = round(counts["PASS"] / sub_total, 3) if sub_total else 0

    return {
        "total": total,
        "passed": passed,
        "failed_count": fail,
        "pass_rate": round(passed / total, 3) if total else 0,
        "by_subsystem": by_sub,
        "by_kind": by_kind,
        "subsystem_pass_rates": subsystem_pass_rates,
        "failed_requirements": sorted({r["requirement"] for r in failed_rows}),
        "failed_rows": failed_rows,
        "failed": failed_rows,
        "release_decision": "hold" if failed_rows else "ready",
    }


def deterministic_ai(summary):
    worst = summary.get("failed_rows", summary.get("failed", []))
    top_issue = worst[0]["requirement"] if worst else "None"

    return {
        "result": f"{summary['passed']}/{summary['total']} tests passed",
        "answer": f"{len(worst)} failures detected. Main issue: {top_issue}",
        "evidence": f"pass_rate={summary['pass_rate']}",
        "next_action": "Fix failing subsystem first",
        "recommendation": "Focus on performance + firmware issues",
        "decision": "Do not release if failures exist",
        "risks": [f["requirement"] for f in worst],
        "operator_actions": ["Inspect failing tests", "Re-run validation"]
    }


INDEX_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Post-Silicon Firmware Validation Lab</title>
<style>
:root{
  --bg:#0b1220;
  --panel:#172033;
  --panel2:#111827;
  --line:#2b3b55;
  --text:#f8fafc;
  --muted:#94a3b8;
  --blue:#60a5fa;
  --green:#22c55e;
  --red:#ef4444;
  --amber:#f59e0b;
}
*{box-sizing:border-box}
body{
  margin:0;
  font-family:Arial,system-ui;
  background:linear-gradient(135deg,#020617,#0f172a 45%,#111827);
  color:var(--text);
}
.container{max-width:1320px;margin:auto;padding:26px}
.hero{
  background:linear-gradient(135deg,#172033,#0f172a);
  border:1px solid var(--line);
  border-radius:22px;
  padding:28px;
  margin-bottom:22px;
  box-shadow:0 18px 50px rgba(0,0,0,.28);
}
.hero-row{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}
h1{font-size:40px;margin:0 0 10px;letter-spacing:-.5px}
.sub{color:var(--muted);font-size:17px;line-height:1.45}
.badge{background:#172554;color:#93c5fd;border:1px solid #2563eb;border-radius:999px;padding:9px 14px;font-weight:800;white-space:nowrap}
.card{
  background:rgba(23,32,51,.94);
  border:1px solid rgba(148,163,184,.16);
  border-radius:18px;
  padding:22px;
  margin-bottom:20px;
  box-shadow:0 12px 30px rgba(0,0,0,.20);
}
.title{color:var(--blue);font-size:22px;font-weight:800;margin-bottom:14px}
.top-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:20px}
.metric-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}
.metric{background:var(--panel2);border:1px solid var(--line);border-radius:14px;padding:18px;text-align:center}
.label{color:#cbd5e1;font-size:13px}.value{font-size:31px;font-weight:900;margin-top:7px}
.good{color:var(--green)}.bad{color:var(--red)}.warn{color:var(--amber)}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
input{flex:1;min-width:290px;background:#0f172a;color:white;border:1px solid var(--line);border-radius:12px;padding:13px;font-size:15px}
button{background:#3b82f6;color:white;border:0;border-radius:12px;padding:12px 15px;font-weight:800;cursor:pointer}
button.secondary{background:#0f172a;color:#93c5fd;border:1px solid var(--line)}
.status{margin-top:10px;color:var(--amber);font-weight:800}
.page-status{color:var(--muted);font-weight:700;margin:8px 0 18px}
.progress-wrap{height:12px;background:#020617;border:1px solid var(--line);border-radius:999px;overflow:hidden;margin-bottom:8px}
.progress-bar{height:100%;width:0%;background:linear-gradient(90deg,#2563eb,#22c55e);transition:width .25s ease}
.answer,.ai-box{background:#0f172a;border:1px solid var(--line);border-radius:14px;padding:16px;line-height:1.55}
.chart-row{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.bar{display:flex;align-items:center;gap:10px;margin:10px 0}
.bar-label{width:170px;color:#cbd5e1;font-size:14px}
.track{flex:1;background:#020617;border-radius:999px;overflow:hidden;height:18px}
.fill{height:18px;background:linear-gradient(90deg,#2563eb,#38bdf8)}
.bar-value{width:64px;text-align:right;color:#e2e8f0}
table{width:100%;border-collapse:collapse}
th,td{padding:12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{color:var(--blue);background:#0f172a}
tr:hover{background:#243044}
.pill{display:inline-block;border-radius:999px;padding:5px 9px;font-weight:800;font-size:12px}
.pill-pass{background:rgba(34,197,94,.12);color:#86efac;border:1px solid rgba(34,197,94,.35)}
.pill-fail{background:rgba(239,68,68,.12);color:#fca5a5;border:1px solid rgba(239,68,68,.35)}
@media(max-width:950px){.top-grid,.chart-row,.metric-grid{grid-template-columns:1fr}.hero-row{display:block}.badge{display:inline-block;margin-top:14px}}
</style>
</head>
<body>
<div class="container">

<section class="hero">
  <div class="hero-row">
    <div>
      <h1>Post-Silicon Firmware Validation Lab</h1>
      <div class="sub">Internal validation dashboard for firmware readiness, register checks, metric limits, requirement coverage, and AI-assisted triage.</div>
    </div>
    <div class="badge">Local AI Validation Copilot</div>
  </div>
</section>

<div class="progress-wrap"><div id="progressBar" class="progress-bar"></div></div>
<div id="pageStatus" class="page-status">Ready.</div>

<section class="top-grid">
  <div class="card">
    <div class="title">AI Analyst</div>
    <div id="ai" class="ai-box"></div>
  </div>

  <div class="card">
    <div class="title">Ask Local AI</div>
    <div class="row">
      <input id="q" placeholder="Ask about top risks, root cause, subsystem debug, or release readiness">
      <button onclick="ask()">Ask</button>
    </div>
    <div class="row" style="margin-top:12px">
      <button class="secondary" onclick="preset('What are the top validation risks?')">Top Risks</button>
      <button class="secondary" onclick="preset('What is the likely root cause?')">Root Cause</button>
      <button class="secondary" onclick="preset('Which subsystem should I debug first?')">Subsystem Debug</button>
      <button class="secondary" onclick="preset('Is this firmware ready for release?')">Release Decision</button>
    </div>
    <p id="status" class="status"></p>
<div id="chat" class="answer">Ask a question or click one of the sample buttons to get a grounded validation answer.</div>
  </div>
</section>

<section class="card">
  <div class="title">Validation Metrics</div>
  <div class="metric-grid">
    <div class="metric"><div class="label">Total Tests</div><div id="total" class="value"></div></div>
    <div class="metric"><div class="label">Passed</div><div id="passed" class="value good"></div></div>
    <div class="metric"><div class="label">Failed</div><div id="failed" class="value bad"></div></div>
    <div class="metric"><div class="label">Pass Rate</div><div id="passRate" class="value warn"></div></div>
    <div class="metric"><div class="label">Release</div><div id="release" class="value"></div></div>
  </div>
</section>

<section class="chart-row">
  <div class="card">
    <div class="title">Pass / Fail by Subsystem</div>
    <div id="subsystemChart"></div>
  </div>
  <div class="card">
    <div class="title">Test Type Breakdown</div>
    <div id="kindChart"></div>
  </div>
</section>

<section class="card">
  <div class="title">Subsystem Pass Rate Ranking</div>
  <div id="rateChart"></div>
</section>

<section class="card">
  <div class="title">Detailed Validation Results</div>
  <table id="table"></table>
</section>

</div>

<script>
let DATA=null;
function pct(x){return ((x||0)*100).toFixed(1)+"%";}
function preset(q){document.getElementById("q").value=q;}

function barChart(target,obj){
  const entries=Object.entries(obj||{});
  const max=Math.max(...entries.map(([k,v])=>typeof v==="number"?v:(v.PASS||0)+(v.FAIL||0)),1);
  let html="";
  entries.forEach(([k,v])=>{
    const value=typeof v==="number"?v:(v.PASS||0)+(v.FAIL||0);
    const label=typeof v==="number"?value:`${v.PASS||0} pass / ${v.FAIL||0} fail`;
    html+=`<div class="bar"><div class="bar-label">${k}</div><div class="track"><div class="fill" style="width:${(value/max)*100}%"></div></div><div class="bar-value">${label}</div></div>`;
  });
  document.getElementById(target).innerHTML=html || "No data";
}

function rateChart(target,obj){
  let html="";
  Object.entries(obj||{}).forEach(([k,v])=>{
    html+=`<div class="bar"><div class="bar-label">${k}</div><div class="track"><div class="fill" style="width:${v*100}%"></div></div><div class="bar-value">${pct(v)}</div></div>`;
  });
  document.getElementById(target).innerHTML=html || "No data";
}

function setProgress(value,msg){
  document.getElementById("progressBar").style.width=value+"%";
  document.getElementById("pageStatus").innerText=msg;
}

async function load(){
  setProgress(15,"Loading validation data...");
  const r=await fetch("/data");
  const d=await r.json();
  setProgress(55,"Rendering deterministic validation output...");
  DATA=d;
  const s=d.summary;
  const ai=d.ai;

  document.getElementById("total").innerText=s.total;
  document.getElementById("passed").innerText=s.passed;
  document.getElementById("failed").innerText=s.failed_count ?? (Array.isArray(s.failed) ? s.failed.length : s.failed);
  document.getElementById("passRate").innerText=pct(s.pass_rate);
  document.getElementById("release").innerText=s.release_decision || (s.failed ? "hold" : "ready");
  const failedCount = s.failed_count ?? (Array.isArray(s.failed) ? s.failed.length : s.failed);
  document.getElementById("release").className="value " + (failedCount ? "bad" : "good");

  document.getElementById("ai").innerHTML=`
    <b>Result:</b> ${ai.result}<br><br>
    <b>Answer:</b> ${ai.answer}<br><br>
    <b>Evidence:</b> ${ai.evidence}<br><br>
    <b>Next Action:</b> ${ai.next_action}<br><br>
    <b>Recommendation:</b> ${ai.recommendation}<br><br>
    <b>Decision:</b> ${ai.decision}
  `;

  barChart("subsystemChart",s.by_subsystem);
  barChart("kindChart",s.by_kind);
  rateChart("rateChart",s.subsystem_pass_rates);

  let html="<tr><th>Status</th><th>Requirement</th><th>Subsystem</th><th>Test</th><th>Actual</th><th>Expected</th><th>Triage</th></tr>";
  d.results.forEach(row=>{
    const pill=row.status==="PASS" ? "pill pill-pass" : "pill pill-fail";
    html+=`<tr>
      <td><span class="${pill}">${row.status}</span></td>
      <td>${row.requirement}</td>
      <td>${row.subsystem}</td>
      <td>${row.name}</td>
      <td>${row.actual}</td>
      <td>${row.expected}</td>
      <td>${row.triage||""}</td>
    </tr>`;
  });
  document.getElementById("table").innerHTML=html;
  setProgress(100,"Dashboard ready.");
}

async function ask(){
  const q=document.getElementById("q").value.trim();
  if(!q){return;}
  document.getElementById("status").textContent="Running Local AI...";
  document.getElementById("status").style.color="#f59e0b";
  const r=await fetch("/chat",{method:"POST",body:q});
  const d=await r.json();
  document.getElementById("status").textContent="Local AI Finished";
  document.getElementById("status").style.color="#22c55e";
  document.getElementById("chat").innerHTML=`
    <b>Answer:</b> ${d.answer}<br><br>
    <b>Evidence:</b> ${d.evidence}<br><br>
    <b>Next Action:</b> ${d.next_action}<br><br>
    <b>Recommendation:</b> ${d.recommendation}<br><br>
    <b>Decision:</b> ${d.decision}
  `;
}

load();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(INDEX_HTML.encode())
            return

        if self.path == "/data":
            device = load_json("samples/device.json")
            tests = load_json("samples/tests.json")
            results = [check_test(device, t) for t in tests]
            summary = summarize(results)
            ai = deterministic_ai(summary)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"summary": summary, "ai": ai}).encode())

    def do_POST(self):
        if self.path == "/chat":
            length = int(self.headers.get("content-length", 0))
            q = self.rfile.read(length).decode().lower()

            device = load_json("samples/device.json")
            tests = load_json("samples/tests.json")
            results = [check_test(device, t) for t in tests]
            summary = summarize(results)
            ai = deterministic_ai(summary)

            failed = summary.get("failed_rows", summary.get("failed", []))
            failed_count = summary.get("failed_count", len(failed))
            by_subsystem = summary.get("by_subsystem", {})
            failed_requirements = summary.get("failed_requirements", [])
            pass_rate = round(summary.get("pass_rate", 0) * 100, 1)

            if "risk" in q or "top" in q:
                answer = {
                    "answer": f"Top validation risks are the failed requirements: {failed_requirements[:8]}.",
                    "evidence": f"Failed tests={failed_count}, pass_rate={pass_rate}%, subsystem breakdown={by_subsystem}.",
                    "next_action": "Start with the failed requirements that belong to subsystems with the highest FAIL count.",
                    "recommendation": "Prioritize performance, PCIe, NVMe, and firmware failures before passing subsystems.",
                    "decision": "Hold release until top failed requirements are fixed."
                }

            elif "root" in q or "cause" in q or "why" in q:
                worst = failed[0] if failed else None
                answer = {
                    "answer": f"Likely root-cause area is {worst['subsystem'] if worst else 'none'} because it owns the first failing validation case.",
                    "evidence": f"{worst['requirement'] if worst else 'No failed requirement'} actual={worst['actual'] if worst else 'n/a'} expected={worst['expected'] if worst else 'n/a'} triage={worst['triage'] if worst else 'n/a'}.",
                    "next_action": worst["triage"] if worst else "Run extended validation.",
                    "recommendation": "Use actual-vs-expected gap plus triage note as the first debug path.",
                    "decision": "Debug root-cause candidate before rerunning full regression."
                }

            elif "subsystem" in q or "debug" in q:
                sorted_subsystems = sorted(
                    by_subsystem.items(),
                    key=lambda item: item[1].get("FAIL", 0),
                    reverse=True
                )
                top = sorted_subsystems[0] if sorted_subsystems else ("none", {"PASS": 0, "FAIL": 0})
                answer = {
                    "answer": f"Debug {top[0]} first because it has {top[1].get('FAIL', 0)} failed tests.",
                    "evidence": f"Subsystem breakdown={by_subsystem}.",
                    "next_action": f"Assign an owner to {top[0]} and inspect all failed requirements in that subsystem.",
                    "recommendation": "Use subsystem clustering to avoid debugging isolated failures randomly.",
                    "decision": "Start subsystem triage before release signoff."
                }

            elif "release" in q or "ready" in q or "ship" in q:
                decision = "hold" if failed else "ready"
                answer = {
                    "answer": f"Firmware release decision is {decision}.",
                    "evidence": f"Pass rate={pass_rate}%, failed_tests={failed_count}, failed_requirements={failed_requirements}.",
                    "next_action": "Fix all failed requirements and rerun the validation suite.",
                    "recommendation": "Do not ship firmware with open validation failures.",
                    "decision": "Hold release." if failed else "Proceed to next validation stage."
                }

            else:
                answer = {
                    "answer": ai["answer"],
                    "evidence": ai["evidence"],
                    "next_action": ai["next_action"],
                    "recommendation": ai["recommendation"],
                    "decision": ai["decision"]
                }

            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(answer).encode())


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"http://{HOST}:{PORT}")
    server.serve_forever()
