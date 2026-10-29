# Orders digest

Filters an orders CSV down to one category, state or product, runs **CSV summary** on the result as a child run, and wraps the child's report in a digest.

It's the example of a workflow using a workflow:

| Step | Kind | What it does |
|---|---|---|
| `filter` | python (fixed) | `scripts/filter.py`: keeps rows where the column equals the value; outputs `{"rows", "of", "file"}` |
| `summary` | uses `csv-summary` | Runs CSV summary on `filtered.csv`, only `if: steps.filter.json.rows > 0`. Its approve step waits for you inside the child run |
| `digest` | python (fixed) | `scripts/digest.py`, `if: always()`: writes `digest.md` from the filter's counts and the child's `report.md` (via `{{steps.summary.dir}}`), or says why there's no report |

Outputs: `digest.md`, `filtered.csv`. The child's own files stay in its run folder.

Try it: orders `csv-summary/sample.csv`, filter on `category`, value `Apparel`.
