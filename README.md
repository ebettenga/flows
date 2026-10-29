# flows

Workflows for **flow**, the Claude Code workflow hub. Each folder in this repo is one workflow the hub can list, show and run.

A workflow is a small YAML file describing a form (inputs) and a list of steps. Steps can be shell commands, Python scripts, MCP tool calls, HTTP requests, flow agents, approval gates, prompts handed to your main Claude session, waits (for a file, a URL or a time), or other workflows run as child runs. Steps can be conditional (`if:`), retried, repeated over a list of items (`for_each:`), and required to leave files behind (`outputs:`). The hub fills in the form, runs the steps in order (or in parallel where allowed), streams output, and saves everything the run produces in its own folder.

## Layout

```
<id>/
  flow.yaml      # required: the workflow definition
  scripts/       # optional: helper scripts used by run and python steps
  README.md      # optional: longer notes for humans
```

The folder name must equal the workflow's `id`.

## flow.yaml reference (spec v1)

```yaml
id: my-workflow
title: My workflow
description: |
  Markdown shown in the hub.
owner: Ethan Bettenga
tags: [example]
env: [SOME_API_KEY]
inputs:
  - id: source_file
    label: Source file
    type: file
    accept: [.csv]
steps:
  - id: first
    title: Do the thing
    run: ./scripts/do-thing.sh {{inputs.source_file | sh}} > "$FLOW_RUN_DIR/result.md"
    outputs: [result.md]
outputs: [result.md]
```

### Top-level fields

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | kebab-case; same as the folder name |
| `title` | yes | short title |
| `description` | yes | markdown shown in the hub |
| `owner` | yes | who maintains it |
| `tags` | no | list of strings for filtering |
| `env` | no | names of environment variables that must be set before the run starts |
| `inputs` | no | the form shown before a run |
| `steps` | yes | what the run does |
| `outputs` | no | files in the run folder (templated) that the run leaves for people: paths, or `{ file, title, chart }` mappings. Shown in the run's Results and Files. See [Outputs and Results](#outputs-and-results) |

### Inputs

| Field | Default | Meaning |
|---|---|---|
| `id` | (required) | snake_case |
| `label` | the id | text shown on the form |
| `type` | (required) | `text`, `textarea`, `number`, `boolean`, `date`, `select`, `file`, `folder` |
| `options` | | `select` only: the choices |
| `accept` | any | `file` only: allowed extensions, e.g. `[.csv]` |
| `multiple` | `false` | `file` only: allow several files |
| `contains` | | `folder` only: files the folder must hold, e.g. `[package.json]`. The hub then lists the folders on this Mac that hold them, by project name, and a run refuses a folder without them |
| `default` | | prefilled value |
| `required` | `true` | whether the run can start without it |
| `help` | | hint text under the field |

In `/flow-chart`, **Choose…** on a `file` input lists files that fit `accept` without browsing: ones you picked for it before, ones earlier runs made (labelled with the workflow and run), and Spotlight's matches on this Mac, newest first, with package folders, virtual environments and build output left out. A search box narrows all three, and **Browse folders** is there for anything else. A `folder` input with `contains:` lists matching projects the same way.

A `file` or `folder` input's value is an absolute path.

### Steps

Every step has an `id` (snake_case) and a `title`, and **exactly one** kind:

| Kind | Value | What happens |
|---|---|---|
| `run` | shell command | run with `bash -c` in the workflow folder (or `cwd:`); output is streamed |
| `agent` | `light`, `medium`, `careful`, `heavy` or `fable` | a headless Claude with that tier's model and effort does the task in `prompt:` (required), with only what the step allows; see [Agent steps](#agent-steps) |
| `approve` | question | the run pauses and shows the question with Approve / Reject; Reject fails the step, so what depends on it is skipped. Claude can answer it too when you say so (`decide_step`) |
| `claude` | prompt | handed to your main Claude session, which reports back when done |
| `wait` | `{ file: <path> }`, `{ url: <http(s) URL> }` or `{ until: "HH:MM" \| ISO date and time }` | checks every `interval` seconds until the file exists, the URL answers 2xx, or the local time is reached. The value is templated; a relative `file` is in the run folder; `HH:MM` means its next occurrence. The output is what it waited for |
| `uses` | a workflow id | runs that workflow as a child run, with `with:` as its inputs. The step goes until the child run ends: done if the child is done, failed otherwise. Its output is the child's run id and folder |
| `python` | inline code, or `{ file, args, interpreter, requirements }` | runs a Python script with no shell; stdout is the output, or what it passes to `flow.set_output(...)`. See [Python steps](#python-steps) |
| `mcp` | `{ server, tool, args }` | calls a tool on one of your session's MCP servers; the text it returns is the output. See [MCP steps](#mcp-steps) |
| `http` | `{ method, url, headers, body, expect }` | sends one HTTP request; the response body is the output. See [HTTP steps](#http-steps) |
| `model` | `{ prompt, files, write, use, max_tokens, effort, system }` | one prompt to Claude with the `files` attached; the answer is the output, and is written to `write`. No agent starts and no tool runs, so it needs no permission (it works in auto mode). For writing and judgment from given text: insights, summaries, classifying. Counts as AI |

Optional step fields:

| Field | Meaning |
|---|---|
| `prompt` | the task text for an `agent` step (a `model` step has its own under `model:`) |
| `cwd` | `run` and `python`: working directory; templated |
| `after` | list of step ids this step waits for. Default: the previous step. `after: []` means it can start right away |
| `timeout` | `run`, `python`, `mcp`, `http` and `wait`: seconds before the step is stopped and fails. Default 600; 3600 for `wait` |
| `continue_on_fail` | `true`: a failure is reported, but the steps that wait for this one still run |
| `if` | a condition (see [Conditions](#conditions)), checked once the `after` steps have ended. False: the step is skipped, and the steps that wait for it still run |
| `retry` | `run`, `agent`, `python`, `mcp` and `http`: how many times to try again after a failed attempt (0 to 5; a timeout counts as a failed attempt). Default 0 |
| `retry_delay` | seconds between a failed attempt and the next. Default 10 |
| `outputs` | files (relative to the run folder, templated) the step must leave: once it otherwise succeeds, a missing one fails it with `missing output <path>` |
| `for_each` | `run`, `agent`, `python`, `mcp` and `http`: a list, or a template that gives items separated by newlines or commas (`"{{inputs.clients}}"`). The step runs once per item; see [for_each](#for_each) |
| `as` | `for_each` only: the item's template name. Default `item` |
| `max_parallel` | `for_each` only: how many items run at once. Default 3 |
| `interval` | `wait` only (beside `wait:` or inside it): seconds between checks. Default 15 |
| `with` | `uses` only: the child workflow's inputs, `<input id>: <value>`; values are templated |

Steps whose `after` steps are all done run in parallel, at most 6 `run`, `agent`, `python`, `mcp` and `http` steps (or `for_each` items) at a time; approvals, `claude`, `wait` and `uses` steps don't count. A failing step (non-zero exit, rejected approval, timeout, missing output, failed child run, an MCP error, an unexpected HTTP status) stops everything that depends on it, unless it has `continue_on_fail: true` or the step after it has an `if:` with `always()` or `failure()`.

### Conditions

`if:` is an expression:

| Part | Examples |
|---|---|
| references | `inputs.<id>`, `steps.<id>.status` (`pending`, `running`, `waiting`, `done`, `failed`, `skipped`, `cancelled`, `interrupted`), `steps.<id>.output`, `steps.<id>.exit` (the exit code, or empty), `steps.<id>.json.<path>` (see [JSON paths](#json-paths)) |
| values | `'text'` or `"text"`, numbers, `true`, `false` |
| comparisons | `==` `!=` `<` `<=` `>` `>=` (as numbers when both sides are numbers, else as text) |
| logic | `&&`, `\|\|`, `!`, parentheses |
| status checks | `always()`: true, and the step runs once its `after` steps have ended, even when one failed or was skipped (a cleanup or summary step). `failure()`: true when an `after` step failed |

A value on its own is true when it is not empty, `false` or `0`. Without `always()` or `failure()`, the step runs only when its `after` steps passed, as any step. Name in `steps.<id>` only steps this one waits for (directly or further back); others may not have ended yet. Quote a condition that starts with `!` (`if: "!failure()"`): YAML reads a bare `!` as a tag.

```yaml
  - id: deploy
    after: [tests]
    if: inputs.target == 'prod' && steps.tests.exit == 0
    run: ./deploy.sh
  - id: report
    after: [deploy]
    if: always()
    claude: Summarize the run.
```

### for_each

Each item runs as its own instance: `{{item}}` (or `{{<as>}}`) is the item and `{{item_index}}` its index from 0, in the command, prompt, `cwd` and `outputs`; `run` steps also get `FLOW_ITEM` and `FLOW_ITEM_INDEX`. Each item has its own log, `<step>[<i>].log`, and its own retries. The step is done once every item is done, and failed if any item failed (`continue_on_fail` works as usual); its output is a JSON array of the items' outputs. No items: done, with output `[]`.

```yaml
  - id: per_client
    for_each: "{{inputs.clients}}"
    as: client
    max_parallel: 2
    run: ./report.sh {{client | sh}} > "$FLOW_RUN_DIR/{{item_index}}.md"
```

### AI and fixed steps

### Agent steps

An agent step runs its own headless Claude (`claude -p --restricted`), not a subagent of your session, so it never waits on your permission prompts and never gets more than the step gives it:

| Field | Default | What it allows |
|---|---|---|
| `tools` | `[Read, Grep, Glob, Write]` | built-in tools from `Read`, `Grep`, `Glob`, `Write`, `Edit`, `WebSearch`, `WebFetch`. Nothing that runs commands or code: put commands in a `run` step before it |
| `read` | none | folders (templated, e.g. `"{{inputs.repo}}"`) it may read besides the run folder |
| `write` | none | folders it may write besides the run folder; it always may write the run folder |
| `budget` | `1` | dollars it may spend before it is stopped (at most 20) |
| `use`, `effort` | the tier's | a model alias or id, and an effort level, instead of the tier's |

It has no MCP servers and ignores your settings files; anything not allowed up front is refused, not asked. It runs on the Claude account the `claude` command is signed in to: run `claude auth login` once in a terminal. Its log shows each tool it used, what was refused, and what it cost.

`agent` and `claude` steps are **AI**: Claude does them, so they can give different results from run to run and cost usage. Every other kind is **fixed**: it runs the same way every time. The hub shows which is which. Use fixed steps wherever they can do the job, and AI steps only for judgment (summarising, writing prose, deciding). An AI step can later be *hardened*: once a run shows that its work was mechanical, replace it with a `python`, `mcp` or `http` step with the same id and `outputs:` (the `flow-author` skill does this with you).

### Python steps

```yaml
  - id: stats
    python:
      file: scripts/summarize.py        # relative to the workflow folder, or absolute
      args: ["{{inputs.csv}}", "--out", "{{run.dir}}/stats.md"]
      interpreter: .venv/bin/python     # optional; default python3; relative to the workflow folder
      requirements: [pandas]            # optional: import names checked before it runs
  - id: total
    python: |                           # inline code instead of file:
      from flow import flow
      orders = flow.steps["fetch"].json["orders"]
      flow.set_output({"total": sum(o["total"] for o in orders)})
```

- The step runs `[interpreter, file, ...args]` in the workflow folder (or `cwd:`), with **no shell**: each arg is passed as written, spaces and quotes included, so no `| sh` is needed. `args` is a list, or one string split like a shell line (`--title "{{inputs.title}}" --top 5`); templates are filled in each arg after splitting.
- Inline code (a string, or `code:` in the mapping) is saved as `.flow/<step>.py` in the run folder and run the same way. It is not templated: read values through `flow`.
- `requirements:` are checked first with `<interpreter> -c "import <name>"`; a missing one fails the step with `missing Python package <name> (install it into <interpreter>)`.
- The output is stdout, trimmed, unless the script calls `flow.set_output(value)`: then it is that value as JSON. stdout and stderr both go to the log.
- Python steps get the same `FLOW_*` variables as run steps, and `retry`, `timeout`, `for_each`, `outputs`, `if` and `continue_on_fail` work as for run steps.

The `flow` helper (standard library only; `.flow/flow.py` in the run folder, on `PYTHONPATH`):

| Name | Value |
|---|---|
| `flow.inputs` | the run's inputs, a dict of strings |
| `flow.steps["<id>"]` | a step as it was when this one started: `.status`, `.output`, `.json` (the output parsed as JSON, or `None`), `.files` (its `outputs:` as absolute paths), `.dir`, `.exit` |
| `flow.run_dir` | the run folder |
| `flow.item`, `flow.item_index` | in a `for_each` step: the item and its index (`None` otherwise) |
| `flow.set_output(value)` | makes `value` (anything `json.dumps` takes) the step's output |
| `flow.chart(name, type="bar", labels=[...], series=[{"name": ..., "values": [...]}], title=None, y_label=None)` | writes `<run dir>/<name>.chart.json` (the name slugged), a chart the hub draws in the run's Results; returns its path. See [Outputs and Results](#outputs-and-results) |

### Outputs and Results

Top-level `outputs:` entries are paths in the run folder (templated, like a step's `outputs:`), or mappings:

```yaml
outputs:
  - report.md                                   # a path
  - file: sales.csv                             # a mapping
    title: Totals by category                   # optional; default the file name
    chart: { type: bar, x: category, y: price, agg: sum }
```

| `chart:` field | Meaning |
|---|---|
| `type` | `bar` or `line` (required) |
| `x` | the column to group by (required) |
| `y` | a numeric column (`1,234.50` and `$40` count as numbers); empty cells are skipped |
| `agg` | `sum` (the default with `y`), `mean`, or `count` (the default without `y`; rows per group) |
| `top` | keep the `n` biggest groups, 1 to 50 (default 12) |
| `sort` | `value` (biggest first; the default for bars) or `label` (the default for lines, so dates read in order) |

Only a `.csv`, `.tsv` or `.json` output (a JSON array of objects, keys as columns) takes a `chart:`. A wrong field is reported by name (`outputs[1].chart.type: "pie" must be bar or line`). When a run's file can't be charted (no such column, a `y` value that isn't a number), the chart is replaced by a short note such as `chart: no column category`.

The run board's **Results** card shows, in order, each part only when it has something:

1. **Approvals**: every `approve` step: its question, approved / rejected / waiting / not reached, when it was decided, and the note given with the decision. A waiting one has Approve and Reject.
2. **Summaries**: each Markdown (`.md`) output, rendered (the first 80 lines; View opens the file).
3. **Charts**: each output with a `chart:`, then each `*.chart.json` file at the top of the run folder.
4. **Tables**: each CSV/TSV output without a `chart:`: the first 10 rows and 8 columns.

Then **Files** lists every output with a View link. Summaries and tables fold; the first two start open. Results reads files up to 2 MB.

A `*.chart.json` file (what `flow.chart` writes from a python step, or any step can write):

```json
{ "type": "line", "title": "Sales per day", "labels": ["2026-09-01", "2026-09-02"],
  "series": [{ "name": "total", "values": [120, 95.5] }], "yLabel": "sum of price" }
```

`type` is `bar` or `line`; each series has one number per label; two or more series draw as grouped bars or several lines with a legend (at most five). `title` and `yLabel` are optional.

```python
from flow import flow
flow.chart("sales by day", "line", labels=days, series=[{"name": "total", "values": totals}], y_label="sum of price")
# -> <run dir>/sales-by-day.chart.json
```

### MCP steps

```yaml
  - id: orders
    mcp:
      server: shopify                   # the server's name, as /mcp lists it
      tool: list-orders                 # the tool's name on that server
      args: { since: "{{inputs.week}}", limit: 50 }
```

Calls the tool with your session's own connection to that server. Every string in `args`, however deep, is templated; numbers and booleans stay as written. The output is the text the tool returns (its text blocks joined), so when that text is JSON, `{{steps.orders.json.<path>}}` works on it. A tool that reports an error, or a call that fails, fails the step with the message.

### HTTP steps

```yaml
  - id: fetch
    http:
      method: GET                       # default GET
      url: "https://api.example.com/orders?since={{inputs.week}}"
      headers: { Authorization: "Bearer {{env.SHOP_TOKEN}}" }
      body: { week: "{{inputs.week}}" } # a mapping is sent as JSON (content-type application/json); or a string
      expect: [200, 201]                # default: any 2xx
```

The output is the response body, trimmed. A status not in `expect` fails the step; the error gives the status and the start of the body.

### JSON paths

When a step's output is JSON, `{{steps.<id>.json.<path>}}` picks a value out of it: dotted keys and `[n]` indexes, as in `{{steps.fetch.json.orders[0].total}}`, or `{{steps.fetch.json}}` for all of it. Objects and arrays fill in as JSON text, other values as text, and a path that leads nowhere (or an output that is not JSON) as nothing. The same paths work in `if:`, where numbers compare as numbers: `if: steps.fetch.json.count > 0`.

### Child workflows (`uses`)

```yaml
  - id: stats
    uses: csv-summary
    with:
      csv: "{{inputs.csv}}"
      title: Weekly stats
```

The child's inputs are checked as when you start a run (required inputs, file types, inputs it does not have). The child is a run of its own, listed with the others; cancelling the parent cancels it. Workflows nest at most 3 deep, and a workflow cannot run itself, directly or further down the chain.

### Templates

Usable in any string value:

| Template | Value |
|---|---|
| `{{inputs.<id>}}` | the input's value |
| `{{steps.<id>.output}}` | a `run` step's stdout, trimmed; an `agent` step's answer (a done step's; empty otherwise) |
| `{{steps.<id>.files}}` | the step's `outputs:` as absolute paths, one per line |
| `{{steps.<id>.dir}}` | the run folder; for a `uses` step, the child run's folder |
| `{{run.dir}}` | this run's own output folder |
| `{{steps.<id>.json.<path>}}` | a value from a step's JSON output (see [JSON paths](#json-paths)) |
| `{{item}}`, `{{<as>}}`, `{{item_index}}` | in a `for_each` step: the item and its index |
| `{{env.<NAME>}}` | in `python` args, `mcp` args and `http` url, headers and body only: an environment variable listed under `env:` (see [Secrets](#secrets)) |

Filters go after a `|`, on any template:

| Filter | Value |
|---|---|
| `\| sh` | quoted for bash: `{{inputs.name \| sh}}` gives `'it'\''s'` for `it's` |
| `\| json` | a JSON string |

**In `run:` steps, never put a bare `"{{inputs.x}}"` in the command for a value a person types**: a `"` or `$(...)` in the value would be run as shell. Use `{{inputs.x | sh}}` (no quotes around it), or the environment variable: `"$FLOW_INPUT_X"`.

### Environment for run and python steps

| Variable | Value |
|---|---|
| `FLOW_RUN_DIR` | same as `{{run.dir}}` |
| `FLOW_RUN_ID` | the run's id |
| `FLOW_WORKFLOW_DIR` | the workflow's folder |
| `FLOW_INPUT_<ID>` | each input's value, id upper-cased (`source_file` becomes `FLOW_INPUT_SOURCE_FILE`) |
| `FLOW_ITEM`, `FLOW_ITEM_INDEX` | in a `for_each` step: the item and its index |

Plus anything listed under `env:`, which the hub checks is set before starting.

## Runs

Each run is saved in `~/.flow/runs/<workflow>/<timestamp>/`. That folder is `{{run.dir}}`: write anything you want to keep there, and name the useful files in `outputs:`. Each step's log is `<step>.log` there (`<step>[<i>].log` for `for_each` items); retries are noted in the log. Python steps keep their helper, context and inline code in `.flow/` there.

## Secrets

Never put a secret in a workflow. List the variable's **name** under `env:` and set its value in your shell or the hub's environment. The file is shared and committed; values are not.

Run steps read it as `$NAME`. Python, MCP and HTTP steps use `{{env.NAME}}` (only for names listed under `env:`; anywhere else it is an error). The value is read when the step runs, and wherever it would show up in a log, a step's output or an error it is replaced with `***`.

## Adding a workflow

1. Make a folder named after the new id (kebab-case).
2. Write `flow.yaml` using the reference above. Start by copying one of the examples.
3. Put helper scripts in `scripts/` and call them with paths relative to the workflow folder (run and python steps start there). Prefer fixed steps; use `agent` or `claude` only where judgment is needed.
4. Add a short `README.md` saying what it does and what it needs.
5. Check it with `validate_workflow` (ask Claude, or the `flow-author` skill), then commit.

## Examples

- [`repo-health-check`](repo-health-check/): parallel tests and lint for a repo, a docs audit by an agent, and a summary from your Claude session (`if: always()`, so it comes even when the audit fails).
- [`csv-summary`](csv-summary/): stats for a CSV (a python step), plain-language insights (an agent), an approval gate, and a combined report. Try it with `csv-summary/sample.csv`.
