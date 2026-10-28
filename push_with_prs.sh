#!/usr/bin/env bash
# Push the staged history to GitHub, one pull request per feature stage.
# Usage: bash push_with_prs.sh <github-username> <repo-name>
set -euo pipefail
USER_NAME="${1:?github username}"; REPO="${2:-pantry-sim}"
mapfile -t COMMITS < <(git rev-list --reverse HEAD)
NAMES=(stage-1 stage-2 stage-3 stage-4 stage-5 stage-6 experiments docs stage-7-refactor stage-8-simplify)

gh repo create "$USER_NAME/$REPO" --public --description "SimPy campus food bank simulator" || true
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$USER_NAME/$REPO.git"

# Stages 1-2 go straight to main (project setup).
git push -f origin "${COMMITS[1]}:refs/heads/main"

# Every later stage becomes its own PR.
for i in $(seq 2 $((${#COMMITS[@]} - 1))); do
  BRANCH="feature/${NAMES[$i]}"
  TITLE="$(git log -1 --format=%s "${COMMITS[$i]}")"
  BODY="$(git log -1 --format=%b "${COMMITS[$i]}")"
  git push -f origin "${COMMITS[$i]}:refs/heads/$BRANCH"
  gh pr create --repo "$USER_NAME/$REPO" --base main --head "$BRANCH" \
     --title "$TITLE" --body "${BODY:-$TITLE}"
  gh pr merge --repo "$USER_NAME/$REPO" "$BRANCH" --merge --delete-branch
  sleep 2
done
git fetch origin && git branch -u origin/main 2>/dev/null || true
echo "Done: https://github.com/$USER_NAME/$REPO/pulls?q=is%3Apr"
