# Animation iteration log

## Spearman — round 10 — 2026-11-23

Lane timestamps and merge start read from `~/LegatumRuns/anim-pilot/legatum/.progress/astra.log` (runner local time, America/New_York). Lane durations overlap; do not add them and call that elapsed wall time. Merge finish is an observed snapshot until the runner logs its completed turn.

| Task | Start | End / observation | Codex wall time | Evidence |
| --- | --- | --- | --- | --- |
| unit-anim-3d-spearman-a | 2026-11-23T21:12:01 | 2026-11-23T21:31:54 | 19m 53s | runner finished |
| unit-anim-3d-spearman-b | 2026-11-23T21:12:05 | 2026-11-23T21:34:40 | 22m 35s | runner finished |
| unit-anim-3d-spearman-c | 2026-11-23T21:12:05 | 2026-11-23T21:29:45 | 17m 40s | runner finished |
| unit-anim-3d-v2 | 2026-11-23T21:35:10 | 2026-11-23T21:48:54 | 13m 44s | observed through final verification; runner finish not yet logged |

- A retained: lower-leg overlap 71.96% → 73.21%; sole span 68.98 → 77.03 px. Oversized flares/outward knees rejected in lane.
- B retained: hit pale pixels 102 → 24 (256 px), 39 → 7 (160 px); rest shoulder RGB error 12.06 → 12.20/255 (slightly worse). Cape-only paint insufficient.
- C retained: death head step 1.277 → 0.655 m; ankle height .848 → .355 m; combined late cape travel .419 → .119 m (lane alone .146 m). Stronger walk attenuation rejected for contact failure. Shield still has an 83.03° sampled rotation step.
- Combined matched CPU rest (8 samples, fixed R9 grade): IoU .903515 → .902229; mean CIE76 ΔE 13.735 → 13.905. Final refitted R10 grade: ΔE 13.814. Both targets fail (IoU ≥.95 / ΔE ≤6). Region/motion improvements retained despite small global rest regression; no PASS.
- 40-pose audit: zero findings. Feet: .0018 mm compensated slip, 1.133 mm floor error, 2.618° planted heading, zero loop seam. CPU preview delivery: 183016 bytes, q80, 160 px trim, 40 records; exact alpha/offset/gutter/hold checks pass. Eight-second five-column movie validated.
- Human kit probe: MPFB 19158 vertices / 53-bone game rig; optional Rigify 930 bones with Armature PV; synthetic corrective .49999994 at half activation. Seven regression tests pass. These do not certify anatomical correctives or art approval.
- Source evidence: `review/3d-v2/spearman-round10-note.md`, `spearman-round10-metrics.json`, `spearman-round10-matched-rest-metrics.json`, `lanes/spearman-r10-merge/inputs.json`. GPU receipt is appended below by the handoff after it actually runs.

- Spearman round 10 GPU receipt: IoU 0.9039; mean CIE76 ΔE 14.05; atlas 197114 bytes / q85; 40 frames. Visual review pending.

## Spearman — round 11c motion lane — 2026-11-23

- Approximately 20 minutes including source review, two diagnostic experiments,
  cloth rebuilds, matched CPU renders and dense feet review; final runner time
  is authoritative. Round-10 source port required because ORIG_HEAD.lock was denied.
- Retain edge-down grip contact plus redistributed donor descent: shield maximum
  sample rotation 83.03 -> 34.41 degrees; head step .655 -> .420 m. Disclose sampled
  ankle .355 -> .423 m and late cape travel .119 -> .145 m; final two frames held.
- Walk ankle spacing .246 -> .344 m; idle carrying arms follow donor torso.
  Dense slip .0023 mm, floor error <.0001 mm, heading 2.618 degrees, seam zero.
  40-pose audit: zero findings; 7 regression tests pass. Rest/idle/attack/hit intact.
- Matched CPU 256/160/64 evidence: review/3d-v2/spearman-r11c-{rest,move,death}-*.png.
  33 top/front foot samples rendered. Raw rest critique .90351 IoU / 13.752 CIE76;
  no rest change, both art thresholds fail. GPU/atlas verification left to lead.
- Rejected: nearest feasible floor hinge alone (still 83.03 degrees); wider walk
  with one-pass sole translation (2.402 mm floor error, above the 2 mm limit).
