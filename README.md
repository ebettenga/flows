# flows

Workflows for **flow**, the Claude Code workflow hub. Each folder in this repo is one workflow the hub can list, show and run.

A workflow is a small YAML file describing a form (inputs) and a list of steps. Steps can be shell commands, flow agents, approval gates, or prompts handed to your main Claude session. The hub fills in the form, runs the steps in order (or in parallel where allowed), streams output, and saves everything the run produces in its own folder.

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
    run: ./scripts/do-thing.sh "{{inputs.source_file}}"
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
| `approve` | question | the run pauses and shows the question with Approve / Reject; Reject stops the run |
| `claude` | prompt | handed to your main Claude session, which reports back when done |

Optional step fields:

| Field | Meaning |
|---|---|
| `prompt` | the task text for an `agent` step |
| `cwd` | `run` only: working directory; templated |
| `after` | list of step ids this step waits for. Default: the previous step. `after: []` means it can start right away |
| `timeout` | seconds before the step is stopped and fails |

Steps whose `after` steps are all done run in parallel, at most 3 at a time. A failing step (non-zero exit, rejected approval, timeout) stops everything that depends on it.

### Templates

Usable in any string value:

| Template | Value |
|---|---|
| `{{inputs.<id>}}` | the input's value |
| `{{steps.<id>.output}}` | a `run` step's stdout, trimmed; an `agent` step's answer |
| `{{run.dir}}` | this run's own output folder |

Quote templated paths in shell commands (`"{{inputs.csv}}"`); paths can contain spaces.

### Environment for run steps

| Variable | Value |
|---|---|
| `FLOW_RUN_DIR` | same as `{{run.dir}}` |
| `FLOW_INPUT_<ID>` | each input's value, id upper-cased (`source_file` becomes `FLOW_INPUT_SOURCE_FILE`) |

Plus anything listed under `env:`, which the hub checks is set before starting.

## Runs

Each run is saved in `~/.flow/runs/<workflow>/<timestamp>/`. That folder is `{{run.dir}}`: write anything you want to keep there, and name the useful files in `outputs:`.

## Secrets

Never put a secret in a workflow. List the variable's **name** under `env:` and set its value in your shell or the hub's environment. The file is shared and committed; values are not.

## Adding a workflow

1. Make a folder named after the new id (kebab-case).
2. Write `flow.yaml` using the reference above. Start by copying one of the examples.
3. Put helper scripts in `scripts/` and call them with paths relative to the workflow folder (run steps start there).
4. Add a short `README.md` saying what it does and what it needs.
5. Check it parses and every `after` id exists, then commit.

## Examples

- [`repo-health-check`](repo-health-check/): parallel tests and lint for a repo, a docs audit by an agent, and a summary from your Claude session.
- [`csv-summary`](csv-summary/): stats for a CSV, plain-language insights, an approval gate, and a combined report. Try it with `csv-summary/sample.csv`.
