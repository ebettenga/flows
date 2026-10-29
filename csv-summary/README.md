# csv-summary

Pick a CSV file and a title. The workflow:

1. `stats`: `scripts/summarize.py` writes `stats.md` (row/column counts, a type guess per column, min/max/mean/median for numeric columns, top 5 values for text columns) and prints a one-line summary.
2. `insights`: a light agent reads `stats.md` and writes 3-6 plain-language insights to `insights.md`.
3. `approve_report`: you approve or reject writing the report.
4. `report`: combines the title, `insights.md` and `stats.md` into `report.md`.

Needs: `python3` (standard library only).

Try it with `sample.csv` in this folder: 25 golf-shop orders (date, product, category, quantity, price, state).

Run the script by hand:

```
python3 scripts/summarize.py sample.csv /path/to/stats.md
```

The report step reads the title from `FLOW_INPUT_TITLE` rather than templating it into the shell command, so a title with quotes or `$` is safe.
