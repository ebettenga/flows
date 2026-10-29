#!/usr/bin/env python3
"""Read the newest CSV's id and name from the Drive search step's answer.

The google-drive search answers in text, one file a line:
  orders.csv (text/csv) [id: 1abc..., path: My Drive/x] [created: ..., modified: 2026-10-29T07:52:15.814Z]
Output (flow): {"id": ..., "name": ..., "modified": ...}. Fails when it found none.
"""
import re
import sys

from flow import flow

text = flow.steps["find_csv"].output
m = re.search(r"^(?P<name>.+?) \([^)]*\) \[id: (?P<id>[^,\]]+)", text, re.M)
if not m:
    sys.exit(f"no CSV in that Drive folder; the search said: {text.strip()[:300]}")
modified = re.search(r"modified: ([^\]]+)\]", text[m.start():])
out = {"id": m["id"].strip(), "name": m["name"].strip(), "modified": modified[1].strip() if modified else ""}
print(f"newest: {out['name']} ({out['modified']})")
flow.set_output(out)
