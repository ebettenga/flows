#!/usr/bin/env python3
"""Totals for an orders CSV: revenue, orders, units and average order, overall
and by category, state and product.

Usage: calculate.py <orders.csv> <out dir> <source name>
Writes <out dir>/calculations.csv (group,name,orders,units,revenue,share),
<out dir>/report.md and a revenue-by-category chart for the hub.
Output (flow): the overall totals, the top category and product, and `base`
(the source name without .csv, for the uploaded files' names).
Standard library only.
"""
import csv
import os
import sys
from collections import defaultdict

from flow import flow

src, out_dir, source_name = sys.argv[1:4]
NEEDED = ["product", "category", "quantity", "price"]

with open(src, newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
if not rows:
    sys.exit(f"{source_name} has no rows")
missing = [c for c in NEEDED if c not in rows[0]]
if missing:
    sys.exit(f"{source_name} has no {', '.join(missing)} column (it has {', '.join(rows[0])})")


def number(v):
    try:
        return float(str(v).replace(",", "").replace("$", ""))
    except ValueError:
        return 0.0


groups = {"category": defaultdict(lambda: [0, 0, 0.0]), "state": defaultdict(lambda: [0, 0, 0.0]), "product": defaultdict(lambda: [0, 0, 0.0])}
total = [0, 0, 0.0]
dates = sorted(r["date"] for r in rows if r.get("date"))
for r in rows:
    qty = number(r["quantity"])
    revenue = qty * number(r["price"])
    for acc in [total] + [groups[g][r.get(g) or "(none)"] for g in groups if g in r]:
        acc[0] += 1
        acc[1] += qty
        acc[2] += revenue

orders, units, revenue = total
lines = []
with open(os.path.join(out_dir, "calculations.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["group", "name", "orders", "units", "revenue", "share"])
    w.writerow(["total", "all", orders, int(units), f"{revenue:.2f}", "1.000"])
    for g, table in groups.items():
        for name, (o, u, rev) in sorted(table.items(), key=lambda kv: -kv[1][2]):
            w.writerow([g, name, o, int(u), f"{rev:.2f}", f"{rev / revenue:.3f}" if revenue else "0"])

money = lambda x: f"${x:,.2f}"
top = {g: max(t.items(), key=lambda kv: kv[1][2])[0] for g, t in groups.items() if t}
md = [f"# Orders report: {source_name}", ""]
if dates:
    md += [f"{dates[0]} to {dates[-1]}", ""]
md += [
    "| | |", "|---|---|",
    f"| Revenue | {money(revenue)} |",
    f"| Orders | {orders} |",
    f"| Units | {int(units)} |",
    f"| Average order | {money(revenue / orders)} |",
    "",
]
for g, t in groups.items():
    if not t:
        continue
    md += [f"## By {g}", "", f"| {g.title()} | Orders | Units | Revenue | Share |", "|---|---:|---:|---:|---:|"]
    for name, (o, u, rev) in sorted(t.items(), key=lambda kv: -kv[1][2])[:10]:
        md.append(f"| {name} | {o} | {int(u)} | {money(rev)} | {rev / revenue:.0%} |")
    md.append("")
with open(os.path.join(out_dir, "report.md"), "w") as f:
    f.write("\n".join(md))

cats = sorted(groups["category"].items(), key=lambda kv: -kv[1][2])
if cats:
    flow.chart("revenue-by-category", "bar", labels=[k for k, _ in cats], series=[{"name": "revenue", "values": [round(v[2], 2) for _, v in cats]}], title="Revenue by category")

base = os.path.splitext(source_name)[0]
print(f"{orders} orders, {money(revenue)} revenue")
flow.set_output({
    "base": base, "orders": orders, "units": int(units), "revenue": round(revenue, 2),
    "average": round(revenue / orders, 2), "top_category": top.get("category", ""),
    "top_product": top.get("product", ""), "from": dates[0] if dates else "", "to": dates[-1] if dates else "",
})
