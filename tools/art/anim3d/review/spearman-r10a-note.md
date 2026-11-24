# Spearman round 10a — lower-leg and guard lane

Files changed in the checkout:
- tools/art/anim3d/units/spearman/lower_body.py (new anatomical fitting and leather construction)
- tools/art/anim3d/units/spearman/silhouette.py (three-line integration hook)
- tools/art/anim3d/units/spearman/check_lower_body.py (new invariant, footprint and dense-walk checks)
- tools/art/anim3d/units/spearman/lower_body_review.py (new fixed-grade native-size comparisons)
- tools/art/anim3d/PLAYBOOK.md (round-10a infantry section only)

## Verdict

**Keep as a modest improvement; not PASS.** The braced guard has a visibly broader sandal silhouette and fuller calves/greaves at 256 and 160 px. At 64 px the support is slightly stronger, but the gain is subtle. Ankles and lower legs still lack the painting's fully convincing weight and painted richness. The unit still has the known pale shoulder/back exposure, soft metal and cloak transitions, orange stone rim, stylized walk and abrupt feet-up collapse. Those material/motion problems belong to lanes b/c and were not edited here. No PASS file was written.

## Construction and scope

The original human feet are not widened or otherwise deformed. Radial anatomy fitting changes 752 calf vertices plus the two greaves in armature rest coordinates, excluding vertices carrying foot/ball weights. Separate 6mm leather welts are weighted to foot/ball above the original sole contact surface. The fixed-length thigh/calf solve closes the calf-to-ankle gaps; the formerly overextended spear-side ankle moves 25mm inward to permit a slight knee bend. Complete guard foot/ball pairs rotate about the anatomical vertical (left 55 degrees, right -12), before projection and source reference calibration. Locomotion resets the guard leg transforms to the original bind before source T-pose mapping, so these guard-only turns never leak into the walk. No camera-space foot fitting, bind edit or post-retarget toe rotation was introduced.

## A/B evidence

Shared review files: `spearman-r10a-256.png`, `spearman-r10a-160.png`, `spearman-r10a-64.png`, `spearman-r10a-lower-leg-detail.png`, `spearman-r10a-rest.png`. Each native-size comparison includes painting, R9 CPU, R10a CPU, crossfade and split. R9 and R10a use Cycles CPU, 256 px, 16 samples, seed 17, existing denoising, identical camera/lights and **one fixed R9 LUT**. Native 160/64 reductions use premultiplied linear-light Lanczos. The 64px painting uses the original 64px token. The enlarged lower-leg crop is explicitly labeled 4x detail.

| Diagnostic | R9 | R10a |
| --- | ---: | ---: |
| Lower-leg alpha IoU above stone | 71.96% | 73.21% |
| Figure above base alpha IoU | 88.87% | 88.98% |
| Whole-image alpha IoU | 89.83% | 89.94% |
| Lower-body RGB mean absolute error /255 | 31.37 | 30.27 |
| Left sole projected width at 256px | 13.18px | 16.95px |
| Right sole projected width at 256px | 13.18px | 16.02px |
| Combined sole span at 256px | 68.98px | 77.03px |

IoU is diagnostic, not an art score. The lower-leg crop includes some cloak/spear; RGB error includes contact shadows. Projected sole bounds are measured only after fitting, never used to deform feet. The sole-width gain comes from the guard orientation, not reshaped sole coordinates. Details and hashes: `spearman-r10a-metrics.json`, `spearman-r10a-geometry-checks.json`, and `lanes/spearman-r10a/inputs.json`.

## Verification

- Scene checks passed: original 19,158 body vertices, 53 bones, 316 painted materials, camera and existing surface pipeline preserved.
- Original 3,280 foot-weighted body vertices, all body weights/topology, original sole coordinates/weights/contact IDs, bind matrices, upper-body pose, camera and lights are hash-identical to R9.
- All five full clips and cloth caches rebuilt. Audit: **40 poses, zero findings**.
- Dense walk comparison: **33 frames; zero foot/ball rotation difference and zero foot/ball head-position difference** from R9. Source rest/roll retargeting is preserved.
- Foot checks: 33 dense frames / 33 planted samples; maximum planted heading **2.544 degrees**, readable heading **3.467 degrees**, compensated sole slip **0.00216mm**, floor error **1.080mm**, loop seam **0**. Virtual speed **1.05058m/s**. New welt minimum Z **0.106926m**, above the 0.105m stone. All existing limits passed.
- Actual top/front feet across the cycle: `spearman-r10a-g-feet-check.png`. Plain front/hero/side geometry: `spearman-r10a-b-plain.png`.
- All 40 transparent CPU frames rendered at 256px/16 samples. All five clip strips and WebPs are `spearman-r10a-e-<clip>-strip.png` and `spearman-r10a-e-<clip>.webp`. Held death 08/09 is byte-identical. These motion renders use one freshly fitted candidate rest grade, independently of the fixed-R9-LUT A/B sheets.
- Isolated preview atlas: **197,268 bytes, quality 85, 160px, 40 frames (8/8/10/4/10)**. Validation passes current hashes, clip timing, trim offsets/anchors, alpha, gutters, bounds, visible motion, held death and byte limit. It stays in `lanes/spearman-r10a/preview-atlas/`; no app atlas was changed.
- `spearman-r10a-motion.mp4`: decoded trimmed atlas, five simultaneous clips, cream background, 2x; **1600x352 H.264 yuv420p, 24fps, 192 frames, 8 seconds**. All strips, feet sheet, decoded atlas and movie samples inspected. `spearman-r10a-movie-check.png` shows samples every half-second at native 160px, not a claim of real-time playback review.
- Python syntax 4/4, Bash syntax, executable GPU script, two pipeline regression tests and `git diff --check` passed. Pinned Quaternius glTF/bin/license hashes passed. `critique.py` does not exist in this checkout. No Rust/UI code or new third-party assets/downloads.

## What the lead should run

From the merged checkout: `ROUND=10 tools/art/anim3d/units/spearman/gpu.sh`.
The script is unchanged and includes the new geometry through its project hook. It still renders every stage, all clips, 512/256 masters, the trimmed 160px atlas, validation, feet sheet, rest comparison and round-numbered movie. This lane only produced CPU previews; final GPU appearance and final GPU atlas size remain unverified.

## Learnings for the cumulative skill

1. A narrow projected sandal can be a guard orientation problem even when the anatomical sole is correctly sized. Rotate the complete foot/ball pair in the authored guard before calibration, and verify that locomotion's rest reset keeps source-space foot transforms unchanged. Never compensate by widening the human foot or editing animated foot yaw.
2. The neutral calf endpoint and translated ankle can disagree. Solve the chain to the actual planted ankle before freezing paint; an overextended leg cannot be made braced by moving its knee alone. Preserve lengths and report the ankle displacement.
3. Grow body-derived calf armour radially in anatomical coordinates and exclude foot-weighted anatomy. A larger distal flare or more outward knee pole is not automatically better: both tested variants worsened silhouette overlap and were rejected.
4. Chased decoration expanded with a generic calf-volume field can float beyond its shell and become a loose loop. Leaving the existing chase radius while filling the greave avoided that artifact here.
5. New footwear geometry needs its own evaluated floor check: preserving the original sole/contact IDs alone cannot prove that an added welt clears the ground.

## Git and handoff

`astra/unit-anim-3d-v2` at d30bc137 is already an ancestor of this lane, and the animation source matched R9 before edits. The requested merge command was blocked while writing ORIG_HEAD.lock; no merge content was needed. `origin/master` is also already an ancestor. Staging failed with `index.lock: Operation not permitted`, so the five files remain uncommitted for the runner. Commit text with the required co-author is in `lanes/spearman-r10a/commit-message.txt`. No push, PR, master merge, upload or shared final-master overwrite was performed.
