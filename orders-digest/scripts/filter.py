"""Keep the rows of a CSV whose <column> equals <value> (case-insensitive).

Usage: filter.py <orders.csv> <column> <value> <out.csv>
Output (flow): {"rows": <kept>, "of": <total>, "file": <out.csv>}
"""
import csv
import sys

from flow import flow

source, column, value, out = sys.argv[1:5]

with open(source, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    if column not in (reader.fieldnames or []):
        sys.exit(f"{source} has no column {column!r} (columns: {', '.join(reader.fieldnames or [])})")
    rows = list(reader)
    fields = reader.fieldnames

kept = [r for r in rows if (r.get(column) or "").strip().lower() == value.strip().lower()]

with open(out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(kept)

print(f"kept {len(kept)} of {len(rows)} rows where {column} = {value}")
flow.set_output({"rows": len(kept), "of": len(rows), "file": out})
