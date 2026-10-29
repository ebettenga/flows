# Drive orders report

Newest CSV in a Drive folder → totals → summary email → calculations saved to another Drive folder.

Every step is fixed (no AI): two python scripts do the work, and the google-drive MCP server does the Drive steps. There's an approval before anything is saved to Drive or emailed.

- `scripts/pick_latest.py`: reads the newest file's id from the Drive search.
- `scripts/calculate.py`: works out the totals overall and by category, state and product, and writes `calculations.csv` and `report.md`.
- `scripts/compose_email.py`: writes `email.md` for the picked recipients.

The recipients input is a `select` with `multiple: true` and `remember: true`: it offers every address used before.

**Test folders:** on the `ethan` Google account:
- `flow-test/incoming` (`1xQiLfZp5LQDeVwRLbkpYHzA9m1xG51Tj`) holds two sample orders CSVs.
- `flow-test/reports` (`16GaASy58VsyC5TV4rwWRV52x8PVPLn5Q`) gets the results.

**The google-drive MCP server** comes from the Sunday Rolls app's `.mcp.json`, so the workflow runs in sessions opened there.

**Sending the email:** the `send_email` step calls `send_message` on the **gee-sweet** MCP server, which is `mcp-gee-sweet` run from GitHub `main` (`uvx --from git+https://github.com/khuisman/mcp-gee-sweet@main mcp-gee-sweet`), with Gmail from PR #786. It's registered in Claude Code's user config and signed in with the token in `~/.config/mcp-gee-sweet/token.json`. It sends from the Google account that server is signed in as. The step runs only after `approve_send`. For a run without prompts, the session needs an allow rule for `mcp__gee-sweet__send_message`, like the Drive ones.
