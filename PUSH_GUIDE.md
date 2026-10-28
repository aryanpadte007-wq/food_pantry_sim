# Pushing to GitHub (with pull requests)

The repo already contains 10 commits, one per stage. The brief rewards readable
commits **and pull requests for new features**, so push it like this.

## Option A: automatic (needs GitHub CLI `gh`, logged in with `gh auth login`)
```bash
cd pantry_sim
bash push_with_prs.sh your-github-username pantry-sim
```
This creates the repo, pushes Stages 1–2 to `main`, then opens and merges one
pull request per later stage (Stage 3, 4, 5, 6, experiments, docs, Stage 7 refactor, Stage 8 simplify).

## Option B: manual
```bash
git log --oneline --reverse          # see the 10 commits in order
git remote add origin https://github.com/<you>/pantry-sim.git
git push origin <stage2-hash>:refs/heads/main
# for each later commit, in order:
git push origin <hash>:refs/heads/feature/stage-3
# then open a PR feature/stage-3 -> main on GitHub, merge it, repeat
```

## Before you push
- Read every file. You must be able to explain it (see `docs/QA.md`).
- Check your unit's AI-use policy. Commits include a `Co-Authored-By: Claude` line; keep it unless the policy says otherwise.
- Confirm the SSU FoodBank hours and update `open_minutes` if they changed.
