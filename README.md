# flows

Workflows for **flow**, the Claude Code workflow hub. Each folder in this repo is one workflow the hub can list, show and run.

A workflow is a small YAML file describing a form (inputs) and a list of steps. Steps can be shell commands, flow agents, approval gates, prompts handed to your main Claude session, waits (for a file, a URL or a time), or other workflows run as child runs. Steps can be conditional (`if:`), retried, repeated over a list of items (`for_each:`), and required to leave files behind (`outputs:`). The hub fills in the form, runs the steps in order (or in parallel where allowed), streams output, and saves everything the run produces in its own folder.

## Layout

```
<id>/
  flow.yaml      # required: the workflow definition
  scripts/       # optional: helper scripts used by run steps
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
| `outputs` | no | file names in the run folder, listed with View links after a run |

### Inputs

| Field | Default | Meaning |
|---|---|---|
| `id` | (required) | snake_case |
| `label` | the id | text shown on the form |
| `type` | (required) | `text`, `textarea`, `number`, `boolean`, `date`, `select`, `file`, `folder` |
| `options` | | `select` only: the choices |
| `accept` | any | `file` only: allowed extensions, e.g. `[.csv]` |
| `multiple` | `false` | `file` only: allow several files |
| `default` | | prefilled value |
| `required` | `true` | whether the run can start without it |
| `help` | | hint text under the field |

A `file` or `folder` input's value is an absolute path.

### Steps

Every step has an `id` (snake_case) and a `title`, and **exactly one** kind:

| Kind | Value | What happens |
|---|---|---|
| `run` | shell command | run with `bash -c` in the workflow folder (or `cwd:`); output is streamed |
| `agent` | `light`, `medium`, `careful`, `heavy` or `fable` | a flow worker of that tier does the task in `prompt:` (required) |
| `approve` | question | the run pauses and shows the question with Approve / Reject; Reject fails the step, so what depends on it is skipped. Claude can answer it too when you say so (`decide_step`) |
| `claude` | prompt | handed to your main Claude session, which reports back when done |
| `wait` | `{ file: <path> }`, `{ url: <http(s) URL> }` or `{ until: "HH:MM" \| ISO date and time }` | checks every `interval` seconds until the file exists, the URL answers 2xx, or the local time is reached. The value is templated; a relative `file` is in the run folder; `HH:MM` means its next occurrence. The output is what it waited for |
| `uses` | a workflow id | runs that workflow as a child run, with `with:` as its inputs. The step goes until the child run ends: done if the child is done, failed otherwise. Its output is the child's run id and folder |

Optional step fields:

| Field | Meaning |
|---|---|
| `prompt` | the task text for an `agent` step |
| `cwd` | `run` only: working directory; templated |
| `after` | list of step ids this step waits for. Default: the previous step. `after: []` means it can start right away |
| `timeout` | `run` and `wait`: seconds before the step is stopped and fails. Default 600; 3600 for `wait` |
| `continue_on_fail` | `true`: a failure is reported, but the steps that wait for this one still run |
| `if` | a condition (see [Conditions](#conditions)), checked once the `after` steps have ended. False: the step is skipped, and the steps that wait for it still run |
| `retry` | `run` and `agent`: how many times to try again after a failed attempt (0 to 5; a timeout counts as a failed attempt). Default 0 |
| `retry_delay` | seconds between a failed attempt and the next. Default 10 |
| `outputs` | files (relative to the run folder, templated) the step must leave: once it otherwise succeeds, a missing one fails it with `missing output <path>` |
| `for_each` | `run` and `agent`: a list, or a template that gives items separated by newlines or commas (`"{{inputs.clients}}"`). The step runs once per item; see [for_each](#for_each) |
| `as` | `for_each` only: the item's template name. Default `item` |
| `max_parallel` | `for_each` only: how many items run at once. Default 3 |
| `interval` | `wait` only (beside `wait:` or inside it): seconds between checks. Default 15 |
| `with` | `uses` only: the child workflow's inputs, `<input id>: <value>`; values are templated |

Steps whose `after` steps are all done run in parallel, at most 6 `run` and `agent` steps (or `for_each` items) at a time; approvals, `claude`, `wait` and `uses` steps don't count. A failing step (non-zero exit, rejected approval, timeout, missing output, failed child run) stops everything that depends on it, unless it has `continue_on_fail: true` or the step after it has an `if:` with `always()` or `failure()`.

### Conditions

`if:` is an expression:

| Part | Examples |
|---|---|
| references | `inputs.<id>`, `steps.<id>.status` (`pending`, `running`, `waiting`, `done`, `failed`, `skipped`, `cancelled`, `interrupted`), `steps.<id>.output`, `steps.<id>.exit` (the exit code, or empty) |
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
| `{{item}}`, `{{<as>}}`, `{{item_index}}` | in a `for_each` step: the item and its index |

Filters go after a `|`, on any template:

| Filter | Value |
|---|---|
| `\| sh` | quoted for bash: `{{inputs.name \| sh}}` gives `'it'\''s'` for `it's` |
| `\| json` | a JSON string |

**In `run:` steps, never put a bare `"{{inputs.x}}"` in the command for a value a person types**: a `"` or `$(...)` in the value would be run as shell. Use `{{inputs.x | sh}}` (no quotes around it), or the environment variable: `"$FLOW_INPUT_X"`.

### Environment for run steps

| Variable | Value |
|---|---|
| `FLOW_RUN_DIR` | same as `{{run.dir}}` |
| `FLOW_RUN_ID` | the run's id |
| `FLOW_WORKFLOW_DIR` | the workflow's folder |
| `FLOW_INPUT_<ID>` | each input's value, id upper-cased (`source_file` becomes `FLOW_INPUT_SOURCE_FILE`) |
| `FLOW_ITEM`, `FLOW_ITEM_INDEX` | in a `for_each` step: the item and its index |

Plus anything listed under `env:`, which the hub checks is set before starting.

## Runs

Each run is saved in `~/.flow/runs/<workflow>/<timestamp>/`. That folder is `{{run.dir}}`: write anything you want to keep there, and name the useful files in `outputs:`. Each step's log is `<step>.log` there (`<step>[<i>].log` for `for_each` items); retries are noted in the log.

## Secrets

Never put a secret in a workflow. List the variable's **name** under `env:` and set its value in your shell or the hub's environment. The file is shared and committed; values are not.

## Adding a workflow

1. Make a folder named after the new id (kebab-case).
2. Write `flow.yaml` using the reference above. Start by copying one of the examples.
3. Put helper scripts in `scripts/` and call them with paths relative to the workflow folder (run steps start there).
4. Add a short `README.md` saying what it does and what it needs.
5. Check it parses and every `after` id exists, then commit.

## Examples

- [`repo-health-check`](repo-health-check/): parallel tests and lint for a repo, a docs audit by an agent, and a summary from your Claude session (`if: always()`, so it comes even when the audit fails).
- [`csv-summary`](csv-summary/): stats for a CSV, plain-language insights, an approval gate, and a combined report. Try it with `csv-summary/sample.csv`.
