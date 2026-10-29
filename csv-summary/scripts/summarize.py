#!/usr/bin/env python3
"""Summarize a CSV file as markdown.

Usage: summarize.py <input.csv> <output.md>

Writes row/column counts, a type guess per column, min/max/mean/median for
numeric columns and the top 5 values for text columns. Prints a one-line
summary to stdout. Standard library only.
"""
import csv
import os
import statistics
import sys
from collections import Counter
from datetime import date


def to_number(value):
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def is_date(value):
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def guess_type(values):
    if not values:
        return "empty"
    if all(to_number(v) is not None for v in values):
        if all(float(to_number(v)).is_integer() for v in values):
            return "integer"
        return "number"
    if all(is_date(v) for v in values):
        return "date"
    if all(v.lower() in ("true", "false", "yes", "no") for v in values):
        return "boolean"
    return "text"


def fmt(x):
    if float(x).is_integer():
        return f"{int(x):,}"
    return f"{x:,.2f}"


def cell(text):
    return str(text).replace("|", "\\|")


def main(argv):
    if len(argv) != 3:
        print("usage: summarize.py <input.csv> <output.md>", file=sys.stderr)
        return 2
    src, dest = argv[1], argv[2]

    with open(src, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            print(f"error: {src} is empty", file=sys.stderr)
            return 1
        rows = [r for r in reader if any(c.strip() for c in r)]

    columns = {name: [] for name in header}
    for row in rows:
        for i, name in enumerate(header):
            value = row[i].strip() if i < len(row) else ""
            if value:
                columns[name].append(value)

    lines = [
        f"## Stats: {os.path.basename(src)}",
        "",
        f"- Rows: {len(rows):,}",
        f"- Columns: {len(header)}",
        "",
        "### Columns",
        "",
        "| Column | Type | Non-empty | Distinct |",
        "|---|---|---|---|",
    ]
    types = {}
    for name, values in columns.items():
        types[name] = guess_type(values)
        lines.append(
            f"| {cell(name)} | {types[name]} | {len(values)} | {len(set(values))} |"
        )

    numeric = [n for n in header if types[n] in ("integer", "number")]
    if numeric:
        lines += [
            "",
            "### Numeric columns",
            "",
            "| Column | Min | Max | Mean | Median |",
            "|---|---|---|---|---|",
        ]
        for name in numeric:
            nums = [to_number(v) for v in columns[name]]
            lines.append(
                f"| {cell(name)} | {fmt(min(nums))} | {fmt(max(nums))} | "
                f"{fmt(statistics.mean(nums))} | {fmt(statistics.median(nums))} |"
            )

    text = [n for n in header if types[n] in ("text", "date", "boolean")]
    if text:
        lines += ["", "### Text columns (top 5 values)", ""]
        for name in text:
            lines.append(f"**{name}**")
            lines.append("")
            for value, count in Counter(columns[name]).most_common(5):
                lines.append(f"- {value}: {count}")
            lines.append("")

    with open(dest, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    print(
        f"{os.path.basename(src)}: {len(rows)} rows, {len(header)} columns "
        f"({len(numeric)} numeric, {len(text)} text) -> {dest}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
