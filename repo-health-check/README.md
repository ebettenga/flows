# repo-health-check

Pick a repo folder. The workflow:

1. Runs `npm test` (repo root), `npm run lint` (repo root) and `npm test` (`server/`) in parallel, saving each log to the run folder as `spa_tests.txt`, `spa_lint.txt`, `api_tests.txt`. Each step fails if its command fails.
2. A medium agent compares both `package.json` script lists against `README.md`, `CLAUDE.md` and `server/README.md` and writes `docs-audit.md`.
3. Your Claude session reads the logs and the audit and writes `summary.md`.

Nothing in the repo is modified, and e2e tests are never run.

Needs: Node and installed dependencies in the repo and in `server/`. The repo must have a `server/` folder with its own `package.json`.

Note: steps run in sequence by dependency, so if a test or lint step fails, the audit and summary don't run. Look at the `.txt` logs for that run.
