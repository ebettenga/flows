# repo-health-check

One button that runs the unit tests of four repos on `develop`. They all start at the same time:

| Step | Repo | Found at, when its folder is left blank | What it runs |
|---|---|---|---|
| MWA | frontend-app | `~/Documents/repos/frontend-app` or `frontend` | Jest in `frontend/web-app` |
| PWA | listener-web-app | `~/Documents/repos/listener-web-app` or `pwa` | Jest |
| Switchboard | switchboard | `~/Documents/repos/switchboard` | Jest in `frontend/switch-board` |
| Backend | web-application | `~/Documents/repos/web-application` or `backend` | `make ci-test-unit` |

If you keep a repo somewhere else, pick its folder in the form.

## What each step does to the repo

`scripts/on-develop.sh` handles the git side:

1. **Skips the repo** if it has uncommitted changes to tracked files. It never stashes or overwrites your work.
2. Fetches and checks out `develop`, fast-forwarded to `origin/develop`.
3. Runs the tests.
4. Puts the repo back on the branch, or the commit, it started on, even if the tests fail.

The backend's `make ci-test-unit` does three things, the same way CI does:
1. Builds a separate `application_ci` database from the fixtures committed in the repo.
2. Runs `alembic upgrade head` on that database.
3. Runs `tests/unit`.

Your dev database is never touched, so migrations from your feature branch can't break the run.

## The result

`scripts/summarize.py` writes `summary.md`. It has one row per repo (pass, fail, skipped, or did not run), followed by each failing test with its file and message. The run fails if any repo did not pass.

There are no AI steps, and e2e tests never run.

## Needs

- The [flow plugin](https://github.com/ebettenga/claude-config) in Claude Code. Clone this repo to `~/Documents/flows`, then run it from `/flow-chart`.
- `node_modules` installed in the three JS repos (`yarn install` with `COMPONENT_LIB_ACCESS_KEY` set). The workflow doesn't reinstall them, so after `develop` changes dependencies, install again.
- Docker running. The backend step starts the repo's compose stack if it isn't already up.
