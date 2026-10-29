"""Write the digest: a header with the filter's counts, then the child run's report.

Usage: digest.py <out.md>
Reads the filter step's output and the summary step's run folder through `flow`.
"""
import os
import sys

from flow import flow

out = sys.argv[1]
f = flow.steps["filter"].json or {}
summary = flow.steps["summary"]
title = flow.inputs.get("title") or "Orders digest"
column, value = flow.inputs.get("column", ""), flow.inputs.get("value", "")

lines = [f"# {title}", "", f"**{column} = {value}**: {f.get('rows', 0)} of {f.get('of', 0)} orders.", ""]
report = os.path.join(summary.dir, "report.md") if summary.dir else ""

if summary.status == "done" and report and os.path.exists(report):
    lines += ["---", "", open(report, encoding="utf-8").read().strip(), ""]
elif summary.status == "skipped":
    lines += ["No orders matched, so there was nothing to summarize.", ""]
else:
    lines += [f"The summary didn't finish (it ended **{summary.status}**), so there's no report to include.", ""]

with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print(f"wrote {out}")
