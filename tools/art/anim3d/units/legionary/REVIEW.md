# Legionary round 2

Improved review candidate; **not art-approved, no PASS marker**. The game still
uses the existing painting. The unit-local source and complete host command are
in the Infantry: legionary chapter of `../../PLAYBOOK.md`.

At **256 px**, the fitted shoulder yoke no longer sticks up around the neck.
Finished-surface projection preserves much more of the source metal, skin and
cloth shading; measured cream stone is close to the painting. The face/helmet
outline, pilum grip, arm proportions and oversized rectangular shield silhouette
still differ. At **64 px**, Roman identity is strong, but pose and silhouette are
still distinguishable. Silhouette overlap improved from .713 to .745; that is
not a visual acceptance threshold. Attack remains restrained; death remains a
stiff folded pose with conspicuous newly exposed skin and projected seams.

The left fingers previously protruded through the scutum. A regression check on
preserved geometry found 719 intersecting triangle pairs before the fix and zero
afterward. Retracting the wrist and gradually tilting it back during peak attack
cleared the stronger held skin/scutum audit across all 40 samples. The audit also
passes stationary base, original body/rig counts, scale, floor and pilum/rigid-kit
checks. It still warns that terminal skin is at .204 m; the body rests over the
dropped shield and worn kit. This is not a full body/cloth collision solver.

Verified **Cycles CPU / 8-sample** delivery:

- All 40 clip frames and eight diagnostic images retained at genuine 512 px,
  with matching 256 px copies and current model/clip/grade/raw-image hashes.
- 160 px trimmed atlas: **197,774 bytes, Q85, 1066 x 766**. All 8/8/10/4/10
  playback samples remain. Premultiplied bicubic reduction retains 8-bit alpha;
  identical logical frames share storage within their clip row.
- Validator passes source margins, exact decoded alpha at reconstructed offsets,
  transparent padding, source hashes, motion and identical decoded held death.
- Decoded review MP4: **1600 x 348, H.264/yuv420p, 240 frames, eight seconds**.
- Python syntax (12 scripts), Bash syntax (2 scripts), executable GPU entry point,
  missing-master failure/status preflight and CPU-as-GPU rejection pass.

External files live under `~/LegatumRuns/anim-pilot/`: editable rest/clip masters,
raw and graded frames in `masters/legionary/`; review strips, animated WebPs,
rest comparison, decoded atlas, round MP4 and validation reports in `review/3d-v2/`.
Prior evidence is retained in `masters/legionary/round1-cpu/`; the diagnosed
pre-clearance scene is `masters/legionary/round2-before-hand-clearance.blend`.

The required executable no-argument host handoff is:

```sh
ROUND=2 tools/art/anim3d/units/legionary/gpu.sh
```

It rebuilds all clips, renders every stage using Cycles GPU at 512 px, exports
256 px copies, audits, checks provenance, packs/validates, and encodes the trimmed
atlas MP4. It retains a transcript and failed-command/status receipt. It rejects
missing Metal and never silently substitutes CPU. Actual GPU rendering and the
lead's visual review remain outstanding; CPU success is not a GPU or art pass.

Working-file hygiene line checks pass across all 14 changed/new files, and
`git diff --check` passes. The baseline HEAD gate identified matrix multiplication
without spaces as false email addresses; operator spacing is now corrected with
identical Python ASTs. Its art-set Chromium renderer still exits 1 in the sandbox.
Revision-based gates must run on the runner's new commit. Git staging/commit was
blocked by `.git/worktrees/lane-7/index.lock` permission; changes are left for the
runner to commit with the requested co-author trailer. No push or PR was made.
