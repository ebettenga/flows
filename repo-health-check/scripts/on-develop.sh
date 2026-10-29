#!/usr/bin/env bash
# Usage: on-develop.sh <repo> <names> <subdir> <command...>
#
# Checks out an up-to-date develop in <repo>, runs <command> in <repo>/<subdir>,
# then puts the repo back on the branch (or commit) it started on.
# Refuses to touch a repo with uncommitted changes.
#
# <repo> may be empty: then the first of the space-separated <names> found in
# ~/Documents/repos is used, so the workflow runs for anyone without setup.
set -uo pipefail

repo=$1 names=$2 subdir=$3
shift 3

if [ -z "$repo" ]; then
  for name in $names; do
    if [ -d "$HOME/Documents/repos/$name/.git" ]; then repo="$HOME/Documents/repos/$name"; break; fi
  done
  if [ -z "$repo" ]; then
    echo "SKIPPED: no repo found at ~/Documents/repos/{${names// /,}}; pick its folder in the form."
    exit 3
  fi
fi
echo "REPO: $repo"

if [ -n "$(git -C "$repo" status --porcelain --untracked-files=no)" ]; then
  echo "SKIPPED: $repo has uncommitted changes; commit or stash them to test develop."
  git -C "$repo" status --short --untracked-files=no
  exit 3
fi

start=$(git -C "$repo" branch --show-current)
[ -n "$start" ] || start=$(git -C "$repo" rev-parse HEAD)
restore() {
  git -C "$repo" checkout -q "$start" && echo "Restored $repo to $start."
}
trap restore EXIT

set -e
git -C "$repo" fetch -q origin develop
if git -C "$repo" show-ref -q --verify refs/heads/develop; then
  git -C "$repo" checkout -q develop
  git -C "$repo" merge -q --ff-only origin/develop
else
  git -C "$repo" checkout -q -b develop --track origin/develop
fi
echo "$repo on develop at $(git -C "$repo" log -1 --format='%h %s')"
set +e

cd "$repo/$subdir"
"$@"
