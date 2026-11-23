# Historical setup checks and handoff

The task is **incomplete**: there are no rendered atlases and zero completed visual
passes. See `pass-0-setup.md` for environment failures, limitations and the resume command.

- `python3 tools/gates/check.py --checks-only`: exit **2**. This checkout requires
  the positional `branch` argument.
- Corrected `python3 tools/gates/check.py HEAD --checks-only`: exit **0**;
  `hygiene: PASS`, `public-claims: PASS`; reviewer checks disabled by the flag.
  **Scope limitation:** this checks committed HEAD. The new scaffold is untracked
  because the sandbox prevented staging, so this is not a gate approval of the
  new files or art.
- `git add tools/art/anim` and commit attempt: exit **128**, unable to create
  `.git/worktrees/lane-1/index.lock` (`Operation not permitted`). Per the task,
  leave the files for the runner to stage and commit. No push or PR was attempted.
- Python syntax compilation, gallery/capture JavaScript syntax and shell syntax:
  passed. Synthetic packing integration: **1 test passed** (160 temporary frames).
- Model-only builds and CPU projection audits: all four passed after fixes.
- Eevee rendering and Chromium screenshot/performance checks: blocked by host
  permissions. Cloud fallback: unusable credentials (`InvalidClientTokenId`).

Suggested runner commit message:

```
Prepare animation gallery and offline rig pipeline; record render blockers

Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>
```

Resume with working render/browser access, run at least three actual visual passes,
then re-run gates on the committed branch. The project still requires Claude art
review; the independent Codex source review was not that approval.
