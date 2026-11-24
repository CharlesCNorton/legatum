# Spearman R14b — restrained cloak, CPU candidate

## Files changed relative to round 13

- tools/art/anim3d/animate.py
- tools/art/anim3d/units/spearman/cloak.py
- tools/art/anim3d/units/spearman/cloak_review.py
- tools/art/anim3d/PLAYBOOK.md (spearman chapter only)

Round-13 base: astra/unit-anim-3d-v2 at d7798046. `git merge` failed on
ORIG_HEAD.lock; the clean worktree was populated with its exact source diff.
All 29 inherited paths are listed separately in spearman-r14b-files.json.
The runner should merge the base normally, then apply spearman-r14b-lane-only.patch.
Staging also failed on index.lock. Commit message is in
spearman-r14b-commit-message.txt; nothing was pushed.

## Selection and changes

The latest art-director verdict (08:03Z, round-13 GPU clips) ranks round 13
first on move. Retained its donor walk, foot rotations, lower clearance and sway;
Fable D's post-retarget foot changes are not imported. Only cloak pin weights,
bending stiffness and air damping change for move and attack. Full shoulder
pins, geometry, UVs, materials, rig actions, camera and other clips are preserved.

Matched evidence: Cycles CPU, 256 px, 16 samples, seed 17, no denoise/adaptive
sampling, analytic painted-look proxy. Display-space premultiplied Lanczos makes
the 160/64 sheets. Rest rows intentionally use the same render: the master is
byte-for-byte unchanged. These are CPU comparisons, not round-14 GPU approval.

## Before / after

| Measure | R13 same-settings baseline | R14b |
| --- | ---: | ---: |
| Move chest-relative geometric left-edge sweep, px at 256 | 22.099 | 15.475 |
| Attack chest-relative geometric left-edge sweep, px at 256 | 10.371 | 7.958 |
| Move cloth endpoint p95 distance, mm | 182.154 | 132.670 |
| Move cloth endpoint maximum distance, mm | 220.079 | 215.201 |
| Attack cloth endpoint p95 distance, mm | 153.691 | 114.141 |
| Attack cloth endpoint maximum distance, mm | 169.460 | 160.602 |

The geometry metrics include hidden cloth and are NOT the director's 6 px
visible-flare estimate. Endpoint distances compare the first and final dense
samples (move includes the duplicate cycle endpoint; attack returns to guard).
Both improve, but neither cloak is perfectly periodic or settled.

The rejected 1.35x move-pin trial lowered sweep to 17.251 px but worsened the
maximum endpoint residual to 245.969 mm. The retained 1.8x setting avoids that
regression. Attack lower pins use .85x rather than R13's .65x. Air damping is
6/5, bending stiffness 2.0/1.2 for move/attack.

## Checks and limits

- 40-pose audit: zero findings; persistent cloth caches baked.
- Production `animate.py` rebuilt move and attack successfully. Dense cloth
  metrics and action hashes exactly match the separately rebaked candidate.
- Move/attack action hashes match their preserved R13 actions exactly; frozen
  idle and attack pass without changing frozen-actions.json.
- 33 dense feet samples, actual top/front renders: all eight limits pass.
  Slip 0.004234 mm; floor error 0.000106 mm; planted heading 5.142407 degrees;
  readable heading 9.175135 degrees; loop seam 0. Root correction 48.962723 mm,
  foot IK 19.943067 mm, sole correction 39.953811 mm (still close to 40 mm).
- 36 tests: kit 27, critique 4, pipeline 2, look 3; all pass. Blender import
  checker zero unresolved imports; Python AST, gpu.sh syntax, lane whitespace pass.
- Rest critique: IoU 0.950869, blurred delta-E 3.363570, raw 7.117816.
  Regions: head 3.818, torso 2.562, cloak 4.213, shield 2.187, legs 2.804,
  feet 5.512, base 3.253. Both agreed targets pass. No rest gain is claimed.
  Historical R13 GPU was 0.953676 / 3.512809; different renderer/resolution,
  so its difference from this CPU proxy is not a lane gain or regression.

## Evidence and verdict

- spearman-r14b-{move,attack,rest}-{256,160,64}.png: painting / R13 / candidate.
- spearman-r14b-{move,attack}.webp: animated A/B with painting.
- spearman-r14b-g-feet-check.png: all 33 actual top/front samples.
- spearman-r14b-cloth-metrics.json and spearman-r14b-critique-metrics.json.
- Source masters/clips, bakes and logs: lanes/spearman-r14b/.

Keep this as a modest cloth improvement for the lead's comparison. The cloak
stays fuller and its movement is less abrupt at 256; the change is subtle at
160 and barely visible at 64. Rest still reads as the painting's spearman at
160/64. At 256 the CPU proxy retains a hard base shadow and simpler sandals;
those are outside this lane. The cloth loop/return is not exact, and the CPU
proxy cannot certify the final Eevee cast shadows. No PASS written.

GPU handoff remains executable and unchanged from R13: run from repo root
`ROUND=14 tools/art/anim3d/units/spearman/gpu.sh`. It rebuilds all five clips,
renders all stages and 512/256 masters through the shared look path, checks
feet/frozen actions/audit/parity, packs and validates the trimmed 160 atlas,
and makes the required eight-second five-clip MP4 and rest comparison.
The shipped atlas in this worktree is the inherited R13 asset, not a new R14
GPU delivery. Lead must review the merged GPU result and atlas size.

## Learned for the cumulative skill

Measure secondary motion separately from rig action hashes. More damping alone
is not a monotonic improvement: the first trial lowered visible sweep while
worsening a hidden hem vertex's endpoint mismatch. Compare p95 and worst-vertex
return as well as the actual 160 px silhouette; preserve full shoulder pins.
Do not equate geometric full-cape sweep with an occlusion-aware visible-edge
measurement, and do not claim a seamless cloth loop from a zero foot seam.
