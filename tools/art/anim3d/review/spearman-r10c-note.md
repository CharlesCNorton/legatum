# Spearman round 10c — motion only

Files changed relative to round 9:
- tools/art/anim3d/PLAYBOOK.md
- tools/art/anim3d/animate.py
- tools/art/anim3d/infantry/retarget.py
- tools/art/anim3d/units/spearman/SOURCES.md
- tools/art/anim3d/units/spearman/motion.py
- tools/art/anim3d/units/spearman/motion_metrics.py
- tools/art/anim3d/units/spearman/round10_review.py

The complete working-tree file list, including ten imported round-9 baseline files, is spearman-r10c-files.json. External assets/SOURCES.md and spearman-log.md were appended; masters, logs and rendered evidence are under lanes/spearman-r10c and this review directory.

## Verdict

Useful motion improvement, **not PASS**. The collapse now has readable knee yield and torso descent, substantially less feet-up/free-arm recoil, a shield that remains attached, and less late cape movement. The end pose lies farther across the base. The walk improvement is modest: its maximum delivered ankle height changes only 430.6 to 422.6 mm, and it still looks like a stylized march at 160 px. At 256 px the collapse is more controlled, but shoulder/back paint gaps remain; at 160 and 64 px the reduced kick and attached shield are readable. Rest is pixel-identical to round 9: narrow legs/feet, pale exposed surfaces and the painting gap remain outside this lane's scope.

Reviewed native-size CPU sheets, every delivered death frame, and top/front rendered feet. Animated 160px WebP comparisons are supplied; this is not a claim of final GPU/decoded-atlas playback approval. No PASS file written.

## Changes

- Complete source Walk_Loop NLA influence 92% -> 90%, before rest/roll retargeting. Same cadence, carrying-arm layer, source foot orientations, contact thresholds and atlas contract.
- Death01 source time remapping separates knee yield and torso descent. During recoil, blend the donor's own terminal local leg rotations; blend local Idle_Loop arm poses (85% shield arm, 65% free arm) as the torso falls. Original source curves are not edited. No new human joint keys or post-retarget foot rotations.
- Register the donor's floor-length fall 40 cm toward the disc center. The existing evaluated body/armour ground solver still adjusts height. This is geometric placement, not a new physics simulation.
- Replace disconnected world-space shield release with grip-preserving rotation. Evaluated shell geometry triggers the minimum floor-clear hinge rotation. Spear release remains, with crossing audits.
- Death-only partial cape pins retain 35% instead of 15%, bending stiffness .8, air damping 4. Full shoulder pins retained. Crest response is near critically damped, 16mm cap. Original hit cloth pins/settings and all attack/hit action output are retained.

## Same-settings evidence

Both R9 and R10c were rendered from the same round-9 master, with the same camera, Cycles CPU / 256 px / 16 samples / seed 17, identical rest LUTs and painting. PNG calibration hashes differ only at file level; rest output PNGs are byte-identical. Receipt includes painting/master/source hashes, camera, Blender build and color transform. 160/64 reductions are previews, not 512px masters.

| Measurement | R9 | R10c |
| --- | ---: | ---: |
| Largest delivered death head-position step | 1.277 m | 0.655 m |
| Highest delivered death ankle | .848 m | .355 m |
| Largest delivered shield rotation step | 137.48 deg | 83.03 deg |
| Shield-center-to-grip distance range | 1.142 m | .000000161 m |
| Late cape max vertex travel (sample 7 -> held final) | .419 m | .146 m |

These are descriptive measurements, not an artistic score. The shield still has a large sampled turn. Geometric root lift during death increases from .145 to .274 m when the body is fitted over the raised disc; inspect the descent in the lead's GPU movie before acceptance. A less stylized captured donor may ultimately improve the walk more than further attenuation.

Walk: 33 dense frames, 32 planted samples; slip .001791 mm, floor error 1.133235 mm, planted heading 2.618409 deg, readable heading 3.350822 deg, loop seam 0. Virtual speed 1.044429 m/s. Root correction 48.971 mm stays below the unchanged 50mm bound; foot IK correction 19.946 mm. All current gates pass.

Checks: 40 poses / zero audit findings; maximum arm transition error .001134 mm; hit pin hash identical; saved attack and hit blends identical to baseline; final death PNG samples 08/09 byte-identical. 40 Python files parse; two pipeline regression tests pass; Bash syntax, executable GPU handoff and git diff --check pass. Dense monotone time remapping, exact recovery envelopes and bounded spring decay checked. Scene checks passed. No Rust/UI changes or unrelated build suite.

Requested critique.py could not run: that file is absent from this checkout and the round-9 branch. The attempted command returned file-not-found; do not represent it as a passed critique.

## Evidence / handoff

- spearman-r10c-rest-compare.png, spearman-r10c-move-compare.png, spearman-r10c-death-compare.png: painting / R9 / R10c, native 256/160/64.
- spearman-r10c-move.webp, spearman-r10c-death.webp: painting / R9 / R10c animated 160px comparisons.
- spearman-r10c-feet-check.png: full top/front cycle.
- spearman-r10c-metrics.json: before/after measurements, receipts and check results.
- Isolated master/clip/render output: ~/LegatumRuns/anim-pilot/lanes/spearman-r10c/masters/spearman-3d-v2/.

Run from the merged checkout: `ROUND=10 tools/art/anim3d/units/spearman/gpu.sh`. The existing executable handoff is unchanged relative to R9 and rebuilds all stages, 512/256 masters, trimmed 160px atlas, validation, feet sheet and round movie. Final GPU rendering, atlas size and decoded playback remain lead-side checks.

Git merge was denied at ORIG_HEAD.lock; staging was denied at index.lock. Round-9 art source/files were applied to the working tree from d30bc137 instead. No unrelated engine changes, fetch, master merge, push or PR. origin/master is already an ancestor of HEAD. The runner should merge the R9 branch, then apply lanes/spearman-r10c/round10c-only.patch. The seven-file patch excludes imported R9 geometry/material/atlas changes; commit-message.txt includes the requested co-author line.

## Learned

- Donor attenuation is not monotonic in contact quality: 82% split stance into two intervals and 88% exceeded the 50mm root correction limit. Reject those settings rather than loosening checks.
- Timing alone cannot remove a donor's exaggerated recoil. Blending its own settled local leg pose before retargeting reduced kick without rotating target feet.
- Keeping a shield parented is insufficient: the unarmed donor can still swing it through the floor. Combine a carried source-arm layer with a geometry-based hinge about the grip.
- Rest identity and restored hit pin hashes are useful regression evidence when changing motion. Rest/atlas audits alone do not establish weight or painted quality.
