# Spearman round 11c — motion candidate

**Not PASS. Recommend retaining the motion changes for the lead's comparison.**
Scope: attached shield floor response, donor collapse timing and walk weight.
Rest master, camera, materials, geometry, original weights, idle, attack and hit
are unchanged; the three retained clip files are byte-identical to round 10.

## Files and integration

Lane changes relative to `astra/unit-anim-3d-v2` (`aeacff7d`):
- `tools/art/anim3d/animate.py`
- `tools/art/anim3d/kit/retarget.py`
- `tools/art/anim3d/units/spearman/motion.py`
- `tools/art/anim3d/units/spearman/feet.py`
- `tools/art/anim3d/units/spearman/feet_sheet.py`
- `tools/art/anim3d/units/spearman/round11c_preview.py`
- `tools/art/anim3d/PLAYBOOK.md` (Spearman chapter only)
- `tools/art/anim3d/LOG.md` (round-11c entry only)

The requested merge failed on the sandbox's `ORIG_HEAD.lock` restriction. The
round-10 anim3d source/atlas delta was ported onto the clean checkout; unrelated
newer master work was retained. This is not a merge commit. Exact refs,
`round10-baseline.patch`, `lane-only.patch`, `files-changed.md` and commit message
are in `~/LegatumRuns/anim-pilot/lanes/spearman-r11c/`. Use the **lane-only** patch
on the lead's round-10 source, not the baseline port. No push or PR.

## Same-settings evidence

All comparisons use Cycles CPU, 256 px, 16 samples, seed 17, no denoising or
adaptive sampling, the same camera/lights/master and one fixed round-10 LUT.
160/64 reductions use linear-light premultiplied alpha. The before frames were
rerendered from the copied round-10 clips, not compared against GPU frames.

- `spearman-r11c-death-{256,160,64}.png`
- `spearman-r11c-move-{256,160,64}.png`
- `spearman-r11c-rest-{256,160,64}.png` (same unchanged master on both sides)
- `spearman-r11c-g-feet-check.png` (33 dense samples, real top/front geometry)
- `spearman-r11c-contact-sheet.png` (40 lossless reduced CPU cells)
- `spearman-r11c-metrics.json` (before/after metrics and receipts)

| Measured quantity | Round 10 | Round 11c |
| --- | ---: | ---: |
| Largest delivered shield rotation, death | 83.032 deg | 34.414 deg |
| Largest delivered head step, death | 0.6553 m | 0.4199 m |
| Shield grip-distance variation, death | 0.000161 mm | 0.000149 mm |
| Maximum sampled ankle height, death | 0.3553 m | 0.4226 m (worse) |
| Late cape travel, death | 0.1188 m | 0.1452 m (more settling) |
| Mean ankle spacing, move | 0.2462 m | 0.3438 m |
| Relative to 0.592 m rest stance | 42% | 58% |
| Largest shield rotation step, move | 1.434 deg | 5.690 deg |
| Head vertical range, move | 0.0562 m | 0.0687 m |
| Compensated sole slip, move | 0.0018 mm | 0.0023 mm |
| Planted floor error, move | 1.133 mm | <0.0001 mm |
| Planted heading, move | 2.618 deg | 2.618 deg |
| Loop seam, move | 0 mm | 0 mm |

Walk root correction 48.880 mm, foot IK 19.635 mm, total sole translation
35.728 mm: all within unchanged 50/50/40 mm limits, but the root and sole
corrections remain near their caps. Swing sole clearance is 104/139 mm (left/right);
this donor still reads as a stylized high step. Source influence remains 0.90.

The shield uses an edge-down geometric preference and damped donor heading
about the existing grip, then a face-up floor-clearance hinge. It is not a
rigid-body simulation. Donor time is redistributed across the collapse; source
joint motion still comes from Death01 and the existing donor-local recoil blend.
Walk broadening is a rest/roll calibration change to thigh/calf axes; target foot
orientation is never edited. Idle carrying arms inherit walking donor torso
rotations before retargeting. No new asset or download.

## Verdict and remaining gaps

At 256 and 160 the shield stays upright through the crouch instead of becoming
a tray, and the extra torso-descent frame removes the largest collapse jump.
The final shield support still looks arranged, with feet/weapon extending past
the base. The mid-fall helmet/crest and pale underside are still poor. The walk
has clearer lateral support and equipment motion, but retains a stylized march
and more bob than the reviewer's requested subtle weight shift. At 64 the unit
identity is clear and the changed motion reads; its craft still does not match
the painting. Rest's thin dark spear, pale footwear and angular exposed surfaces
remain outside this lane. No art PASS is justified.

`critique.py` ran on this rest and all 40 lossless reduced 160 frames: IoU
0.903509 / raw unblurred CIE76 13.7520. Both legacy targets fail. Rest A/B is
identical; do not call the difference from R10's 8-sample/denoised or GPU metrics
an improvement. The latest reviewer requested blurred/per-region colour metrics;
that shared-tool change is left for the lead rather than mixed into this motion lane.

## Verification and GPU handoff

- Full saved 40-pose audit: **0 findings**, including equipment crossings,
  real-disc/ground contact, camera bounds and arm transitions.
- Dense walk: **all 8 checks pass**, 33 samples. Inspected all top/front frames.
- Rest master and idle/attack/hit: **byte-identical**. Attack/hit measured rows,
  cloth pin hashes and clip hashes also match baseline exactly.
- **7 unique regression tests pass** (pipeline 2, critique 2, kit 3).
- All anim3d Python files parse; Bash syntax passes for env/render/gpu; GPU entry
  point remains executable; whitespace and lane-patch reverse check pass.
- CPU 256/160/64 comparisons, full 40-cell contact sheet and feet images inspected.
  This is image/sequence review, not a claim of real-time video playback review.
- `gpu.sh` remains unchanged from round 10 and still owns final stages, 512/256
  masters, trimmed 160 atlas validation, critique and the 8-second five-clip MP4.
  Run **`ROUND=11 tools/art/anim3d/units/spearman/gpu.sh`** from repo root after merge.
  Final GPU quality and <=200 KB atlas size for this new motion remain unverified.
  The existing round-10 GPU atlas is retained; no CPU atlas was written to the app.

## Learned for the lead's skill merge

1. Measure the carried arm before blaming a floor solver: choosing the nearest
   feasible floor orientation alone left the same 83.03-degree jump. Edge-down
   carrying preference, damping and more samples through descent reduced it.
2. Preserve some anatomical leg spread in reference calibration, with unchanged
   foot mapping, to broaden support without a foot-yaw or mesh hack. Source torso
   rotation can drive the idle carrying-arm layer so equipment shares walk weight.
3. A skinned sole may not move by the exact amount of a bone translation. The
   first 35%-spread experiment failed at 2.402 mm floor error; convergence on the
   evaluated sole fixed it without relaxing any contact or correction limit.
4. Report secondary regressions: redistributing fall samples lowered head/shield
   jumps but exposed a higher ankle sample and more late cloth travel.

Git staging was attempted and failed with `index.lock: Operation not permitted`.
Changes are uncommitted; the runner must commit with the saved co-author message.

Latest feedback checked at completion: the 03:36Z art-director review prefers
Fable B's death/hit over Astra round 10 and finds no walk winner. That review does
not evaluate these R11c previews. This lane establishes improvement over R10,
not superiority to Fable B. Compare this walk in the merge; the shield/contact
mechanism may be reusable even if Fable B's whole collapse wins.
