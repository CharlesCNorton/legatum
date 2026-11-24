# Spearman round 15c — retain round 14; dense-phase trial rejected

Files changed relative to R14: `tools/art/anim3d/PLAYBOOK.md`, `tools/art/anim3d/units/spearman/check_transitions.py`, `tools/art/anim3d/units/spearman/round15c_review.py`. Full worktree file list, including the R14 baseline import: `lanes/spearman-r15c/changed-files.txt`.

## Decision

Retain R14's phase-41 walk, combined cloth, and shield-readable death. No production pose, donor rotation, contact, material, camera, clip count or timing changes. Added explicit eight-frame/integer-sample checks, the isolated reproducible trial and the finding in the Spearman playbook chapter. No PASS file. Latest cloud review says retain R14 where metrics or clips regress, and hold after R15 for Sam.

Git merge of astra/unit-anim-3d-v2 (9c35ac22) was attempted first, after skill loading, but ORIG_HEAD.lock was denied. Applied its exact file diff onto the clean lane; origin/master is already an ancestor of that baseline. Staging/commit was also denied at index.lock. Runner handoff: `lanes/spearman-r15c/lane-only.patch` applies only this lane's three files against R14; `commit-message.txt` includes the requested coauthor. No fetch/push/PR/master merge.

## Experiment and matched evidence

Scanned all 32 existing dense integer phases of the contact-solved walk, keeping eight samples exactly four source frames apart (6 fps). The lowest worst-boundary error starts at dense frame 40 instead of 41. Same original bones, foot rotations, geometry, baked cloth and action; only delivered timestamps differ. All numbers below are full corresponding sole/cloth vertices at 160 px, not a visible-edge measurement.

| Metric | Retained R14 | Rejected phase 40 |
| --- | ---: | ---: |
| Idle → move sole maximum | 14.4112 px | 13.3732 px |
| Move → idle sole maximum | 9.4421 px | 10.3387 px |
| Worst of both boundaries | 14.4112 px | 13.3732 px |
| Worst cloth delivery step | 11.8892 px | 12.5258 px |
| Cloth last → first delivery step | 6.0168 px | 7.0039 px |
| Maximum per-step cloth p95 | 7.7371 px | 8.1598 px |

Only dense phase 41 is no worse than R14 on both sole boundaries. The 7.2% worst-boundary gain is not enough to justify worsening the exit and cloth. This phase search cannot make the toe-out painted guard identical to a forward-walking donor pose. No new hand-keyed entry, foot yaw correction, crossfade, offset or frame was smuggled into the loop.

The required matched Cycles CPU previews use the shared look renderer, 256 px / 8 samples / seed 17, analytical sun without Eevee cast shadows. Native 160 and 64 are display-space premultiplied reductions; 64 uses the original painting token. Files in the shared review folder:
- `spearman-r15c-boundaries-{256,160,64}.png`: painting, R14 and rejected trial entry/exit.
- `spearman-r15c-move-loop-{256,160,64}.png`: all eight combined-cloth poses, R14 against trial.
- `spearman-r15c-preserved-{256,160,64}.png`: painting, unchanged rest/idle and all ten shield-readable death frames.
- `spearman-r15c-feet-check.png`: freshly rendered 33-sample top/front cycle.
- `spearman-r15c-rejected-phase40.mp4`: rejected trial's five-clip CPU movie, not production.
- `spearman-r15c-metrics.json`: complete measured trial and critique.

## Verification and appearance

Exact comparisons: all 53 bone matrices, all sole vertices and all evaluated cloak vertices are identical over all 33 dense samples; action digest unchanged. Rest/idle/attack/hit/death blend files and look calibration files match R14 byte-for-byte. Frozen idle and attack digests pass. Fresh 33-sample feet checks: sole slip 0.004234 mm, floor error 0.000106 mm, planted heading 5.1424 degrees, readable heading 9.1751 degrees, foot-loop seam zero. All eight contact limits pass without relaxed thresholds. Idle/move duplicate cloth endpoints remain below 0.00004 px, though delivered frame differences can still get worse.

Trial 40-pose audit: zero findings. Final retained R14 40-pose audit: zero findings; all five selected blend files are byte-identical to R14. Final retained transitions: 14.4112 / 9.4421 px; hard cut remains explicitly unresolved. Python tests: 36/36 (27 kit, 4 critique, 2 pipeline, 3 look). Import resolution: zero unresolved; changed scripts parse; gpu.sh shell syntax/executable checks pass, and gpu.sh is byte-identical to R14. No Rust/UI changes or unrelated engine builds.

Rest critique was rerun: IoU 0.9512535964, zero-offset blurred CIE76 ΔE 3.3865985675, raw ΔE 7.2742619106; identical to R14 CPU, not an improvement over GPU. Regional blurred ΔE: head 3.738, torso 2.635, cloak 5.034, shield 2.222, legs 2.726, feet 5.447, base 3.232. All regional values remain under 6. Rejected trial atlas validates at 192,756 bytes, Q80, 40 frames; retained R14 CPU atlas was 192,682 bytes. Neither replaces the production GPU atlas.

Personally inspected matched 256/160 boundaries and every combined-cloth move pose, the 33 top/front feet views, and idle/death at 256/64. At 256 the tiny sampling difference does not solve the guard mismatch; the pale sole, smooth sandals and simplified cloak hem remain visible. At 160 the trial's exit is no better; at 64 the shield and crest preserve the unit and fallen-body identity. Retain R14 as the better overall choice. The rest is close to the painting but not indistinguishable at 256; no new artistic PASS claimed.

## Learned

An identical dense action and perfectly closed cloth endpoints do not guarantee better delivery: shifting an eight-frame sampling grid changes both the guard cuts and the largest inter-frame cloth steps. Optimize and report entry, exit, and combined-cloth delivery together; retain the old phase if one improves at the expense of the others. Here the 32-phase exhaustive check leaves R14 as the only nonregressing integer phase.

GPU lead command from repo root: `ROUND=15 tools/art/anim3d/units/spearman/gpu.sh`. It retains every stage, all 512/256 masters, trimmed 160 atlas/JSON, validation, top/front feet, critique, rest comparison and eight-second five-clip H.264 movie. No GPU run was attempted in the CPU sandbox. Use the production rebuild; do not copy the isolated rejected-phase40 blend into it.
