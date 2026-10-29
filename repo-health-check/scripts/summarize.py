"""Turn each suite's test report into one summary.md and a small JSON output.

Usage: summarize.py <out_path> <suite>...
where each suite is name|kind|report|log|subdir, kind being jest or pytest, and
subdir the tests' folder inside the repo that on-develop.sh logged as "REPO: ...".
"""
import json
import os
import re
import sys

from flow import flow


def tail(path, n=30):
    if not os.path.exists(path):
        return "(no log)"
    return "".join(open(path, errors="replace").readlines()[-n:])


def repo_dir(log, subdir):
    if os.path.exists(log):
        for line in open(log, errors="replace"):
            if line.startswith("REPO: "):
                return os.path.normpath(os.path.join(line[len("REPO: "):].strip(), subdir))
    return "/"


def skipped_reason(log):
    if os.path.exists(log):
        for line in open(log, errors="replace"):
            if line.startswith("SKIPPED:"):
                return line[len("SKIPPED:"):].strip()
    return None


def jest(report, log, app_dir):
    if not os.path.exists(report):
        return None
    r = json.load(open(report))
    counts = {
        "passed": r.get("numPassedTests", 0),
        "failed": r.get("numFailedTests", 0),
        "skipped": r.get("numPendingTests", 0),
    }
    failures = []
    for suite in r.get("testResults", []):
        name = os.path.relpath(suite.get("name", ""), app_dir)
        failed = [a for a in suite.get("assertionResults", []) if a.get("status") == "failed"]
        if suite.get("status") == "failed" and not failed:
            # The suite itself broke (syntax error, failed import, ...).
            failures.append((name, "(suite failed to run)", suite.get("message", "")))
        for a in failed:
            failures.append((name, a.get("fullName", ""), "\n".join(a.get("failureMessages", []))))
    return counts, failures


def pytest(report, log, app_dir):
    # No report file: pytest runs in the backend container, so read its log.
    if not os.path.exists(log):
        return None
    text = re.sub(r"\x1b\[[0-9;]*m", "", open(log, errors="replace").read())
    # The last "3 failed, 120 passed in 30.1s" line (framed in ==== without -q).
    final = [l for l in text.splitlines() if re.match(r"^=* ?\d+ (passed|failed|errors?|skipped|deselected)\b.* in [\d.]+s", l) or "no tests ran" in l]
    if not final:
        return None
    found = dict((k, int(n)) for n, k in re.findall(r"(\d+) (passed|failed|skipped|errors?|deselected)", final[-1]))
    counts = {
        "passed": found.get("passed", 0),
        "failed": found.get("failed", 0) + found.get("error", 0) + found.get("errors", 0),
        "skipped": found.get("skipped", 0),
    }
    failures = []
    for m in re.finditer(r"^(FAILED|ERROR) (\S+?)(?:::(\S+))?(?: - (.*))?$", text, re.M):
        failures.append((m.group(2), m.group(3) or f"({m.group(1).lower()})", m.group(4) or ""))
    return counts, failures


out_path, *suites = sys.argv[1:]
rows, sections, results = [], [], {}
for spec in suites:
    name, kind, report, log, subdir = spec.split("|")
    app_dir = repo_dir(log, subdir)
    reason = skipped_reason(log)
    parsed = None if reason else {"jest": jest, "pytest": pytest}[kind](report, log, app_dir)

    if reason:
        status, counts, failures = "SKIPPED", None, []
        sections += [f"## {name}: skipped", "", reason, ""]
    elif parsed is None:
        status, counts, failures = "DID NOT RUN", None, []
        sections += [f"## {name}: did not run", "", "Last lines of the log:", "", "```", tail(log).rstrip(), "```", ""]
    else:
        counts, failures = parsed
        status = "FAIL" if counts["failed"] or failures else "PASS"
        if failures:
            sections += [f"## {name}: failures", ""]
            for file, test, msg in failures:
                # Drop stack frames inside dependencies; keep the message and our own frames.
                msg = [l for l in msg.strip().splitlines() if "node_modules" not in l and "site-packages" not in l]
                sections += [f"### `{file}`: {test}", "", "```", *msg[:15], "```", ""]

    c = counts or {}
    rows.append(f"| {name} | **{status}** | {c.get('passed', '')} | {c.get('failed', '')} | {c.get('skipped', '')} |")
    results[name] = {"status": status, **(counts or {}), "failures": len(failures)}

ok = all(r["status"] == "PASS" for r in results.values())
lines = [
    "# Tests on develop", "",
    f"**Result: {'PASS' if ok else 'FAIL'}**", "",
    "| Repo | Result | Passed | Failed | Skipped |", "|---|---|---|---|---|",
    *rows, "", *sections,
]
open(out_path, "w").write("\n".join(lines))
flow.set_output({"ok": ok, "suites": results})
sys.exit(0 if ok else 1)
