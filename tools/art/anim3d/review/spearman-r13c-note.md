# Spearman round 13c — walk clearance and death ending

Lane files changed relative to round-12 candidate `07643cd4`:

- `tools/art/anim3d/PLAYBOOK.md` (new infantry R13c chapter only)
- `tools/art/anim3d/animate.py` (move-only shaping hook and receipt)
- `tools/art/anim3d/units/spearman/collapse.py` (last three death keys)
- `tools/art/anim3d/units/spearman/motion.py` (translation-only swing lowering and hip sway)
- `tools/art/anim3d/units/spearman/round13c_review.py` (repeatable CPU A/B evidence)

Git merge was attempted first but denied `ORIG_HEAD.lock`. The exact R12 content
was applied to the worktree with `git diff --binary HEAD astra/unit-anim-3d-v2`
and `git apply`, without changing Git metadata. `spearman-r13c-files.txt` lists
all 32 baseline-import paths separately from the five lane paths. The lead
should use `spearman-r13c-lane.patch` for the scoped delta, not port the whole
old lane branch. Reverse-apply check passes against this worktree. No commit
or push; the runner can use `lanes/spearman-r13c/commit-message.txt`.
`origin/master` is already an ancestor of the round-12 baseline; no fetch.

## Selected change and matched evidence

All A/Bs: same unchanged R12 master/look, Cycles CPU painted-look proxy, 256 px,
8 samples, seed 17, no denoising/adaptive sampling, display-space premultiplied
reduction. Frozen pigment and analytic sun/Cycles AO; no live Eevee cast shadow.
The 160/64 outputs are reductions of these renders, not independent GPU renders.
The 64 reference is the shipped painting token. Source clip hashes, camera,
Blender/settings and motion metrics are in `spearman-r13c-motion-metrics.json`.

| Measure | R12 | R13c |
| --- | ---: | ---: |
| Dense peak swing-sole clearance above contact plane | 114.229 mm | 76.154 mm |
| Dense peak ankle height | 422.556 mm | 390.821 mm |
| Delivered pelvis lateral range | 67.977 mm | 84.947 mm |
| Minimum delivered screen ankle separation at 256 | 14.9808 px | 14.9807 px |
| Compensated planted-sole slip | 0.00179 mm | 0.00427 mm |
| Planted sole floor error | 0.00037 mm | 0.00050 mm |
| Planted heading / readable heading | 5.142 / 9.175 deg | 5.142 / 9.175 deg |
| Loop seam | 0 | 0 |
| Final body vertices vertically over disc | 55.356% | 76.421% |
| Final head joint screen x at 256 | 72.454 px | 85.621 px |
| Death maximum head step | 528.516 mm | 528.516 mm |
| Death maximum shield rotation step | 65.533 deg | 65.533 deg |
| Late death cloak vertex travel | 187.703 mm | 164.659 mm |

The walk preserves the open Quaternius donor, its timing, support intervals,
virtual travel speed (1.04443 m/s), and retargeted foot/ball rotations. Only
swing clearance is reduced by one third; a 12 mm sine sway moves the pelvis
toward support with both ankle tracks preserved by IK. Intentional swing
lowering peaks at 38.076 mm and is recorded separately from contact corrections.
All eight existing limits pass at all 33 dense samples. Root contact correction
48.963 mm, foot-contact IK 19.943 mm and sole correction 28.185 mm remain below
the unchanged limits. Maximum foot/ball rotation-matrix residual is 5.78e-6,
inside the new 1e-5 preservation assertion. No authored foot-yaw correction.

Death keeps the accepted recoil, kneeling and collapse. Only its last three
keys change: pelvis registration up to +160 mm, slight head turn and a lowered,
forward carrying arm. The aspis remains strapped to the forearm (grip-distance
range 0.000125 mm). The early maximum step metrics remain unchanged. Body-over-
disc is a vertex-density-dependent geometric diagnostic, not load-bearing area.
Head and crest are more centered; feet move farther toward the opposite rim.
The two final source PNGs are byte-identical.

## Checks and artifacts

- 33 existing tests pass: kit 24, critique 4, pipeline 2, look 3.
- 40 saved/baked poses: **zero audit findings**, including real-disc/ground
  clearance, frame bounds, weapon crossings and arm transitions.
- Full top/front geometry sheet rendered over 33 move samples. All eight feet
  limits pass; the sheet uses diagnostic materials, not the final painted look.
- Scene checks pass. Master, idle, attack and hit `.blend` SHA256 values are
  identical to R12; accepted idle/attack action receipts also pass.
- CPU preview atlas: **191,980 bytes, Q80**, trimmed 160 px cells, all 40 frames;
  decoded alpha, bounds, offsets, gutters, motion and death hold validate.
- CPU movie: H.264 yuv420p, 1600x352, 24 fps, 192 frames, exactly 8 seconds.
  Viewed all 40 decoded cells, movie samples, feet sheet and native-size A/Bs.
- `critique.py`: rest **IoU 0.9393718** (fails 0.95), blurred zero-offset
  **delta-E 4.5483** (passes 6); regions head 3.738, torso 2.601, cloak 4.464,
  shield 2.206, legs 2.812, feet 13.285, base 4.725. Rest is unchanged; do not
  attribute tiny differences from the older R12 CPU/GPU captures to this lane.
- Python syntax, Bash syntax, whitespace and static Blender import checks pass.
  The prescribed `kit/check_imports.py` is absent on the R12 branch; ran the
  exact version from `astra/unit-anim-3d-skill` in the external lane directory
  against `tools/art/anim3d`: zero unresolved imports. No shared-script port.
- No new downloads, image generation, geometry, materials, source licence or
  rest camera changes. The checked-in atlas has only the exact R12 baseline
  update; CPU output never replaces it.

Review files (all in this directory):
`spearman-r13c-{move,death,rest}-{256,160,64}.png`,
`spearman-r13c-death-ending.png`, `spearman-r13c-{move,death}.webp`,
`spearman-r13c.mp4`, `spearman-r13c-movie-samples.png`,
`spearman-r13c-g-feet-check.png`, `spearman-r13c-critique-*.png`,
`spearman-r13c-{motion-metrics,feet-metrics,audit,delivery}.json`.
Editable masters/caches and lossless previews: `lanes/spearman-r13c/`.

## Honest verdict and merge guidance

Keep the walk candidate: the lift is visibly quieter at 160, track separation
and contact survive, and sway is subtle. It still retains the donor's pronounced
toe-down swing; it is not a completely different naturalistic walk. The tiny
numerical slip increase is disclosed above and remains far below 1 mm.

Death is a reviewable tradeoff. More body and the head are over the base, and
crest/shield/spear retain unit identity at 64. The shield face is clearer but
covers more torso at 256/160, and the feet extend farther right. Prefer it only
if that staging reads better beside the accepted R12 ending; the late keys can
be omitted independently of the walk. No claim that the already accepted
round-12 death was broken. No change to the early spear crossing or hit.

At 256 and 64 the unchanged rest remains recognizably close to the painting,
but sandal articulation/tone and base shading are still the visible gaps.
Feet delta-E remains above the regional target. No art PASS file was written.

The executable `tools/art/anim3d/units/spearman/gpu.sh` is unchanged and syntax-
checked. Lead must run from the merged repository root:

```sh
ROUND=13 tools/art/anim3d/units/spearman/gpu.sh
```

It rebuilds projection/look/all five clips, all GPU stages, 512/256 masters,
trimmed 160 atlas and validation, feet audit, rest comparison/critique and
`spearman-round13.mp4`. GPU rendering and final GPU byte size are not verified
by this CPU lane. Recheck contact after merging any foot-form changes.

## Learned for the cumulative skill

- Lower swing clearance relative to the measured support sole before the final
  floor solve; reducing an absolute ankle height can be undone by the root
  contact correction. Translation-only IK can preserve donor foot/ball rotations
  and support timing while reducing the march (114.23 -> 76.15 mm here).
- Shift hips toward support while compensating both ankle targets; this gives
  more pelvis sway without planted slip or narrowing the visible tracks.
- Measure the collapsed body against the actual disc footprint. More body on
  the disc does not automatically mean a better sprite: inward registration
  increased coverage 55.36 -> 76.42%, but the shield hides more torso and the
  opposite feet move outward. Keep staging and readability judgments separate.
