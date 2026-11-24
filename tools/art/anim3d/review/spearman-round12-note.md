FOCUS a: (reviewer) Legs at rest are still slightly A-framed: make the shins more vertical and bring the feet a little closer together so they sit on the painted feet in the crossfade (on both sides). Form base: Fable B's stance.py. Keep B's measured shield/helmet spans. Re-measure IoU.
FOCUS b: (reviewer) In the look pass (Fable A's look.py): darker brown sandals; a soft base contact shadow on the top around the feet and a darker gradient down the side band; a slightly darker shield rim value. Measure blurred ΔE per region at zero offset.
FOCUS c: (reviewer) Death end pose: keep the collapse but end with more of the body on the base and the head and crest readable, e.g. lying on his side facing the camera with the shield beside him. Walk: lower the trailing foot lift (it reads as a march) and add a little hip sway; keep the feet check passing.

# Spearman round 12 — combined candidate (CPU review; GPU pass pending)

Not PASS. Source ports on astra/unit-anim-3d-v2; Git refused ORIG_HEAD.lock.
The lead must run `ROUND=12 tools/art/anim3d/units/spearman/gpu.sh` from this
checkout. The shipped atlas remains the round-11 GPU atlas until that pass.

## Selected work

- Skill branch d7a87b11: latest SKILL, LOG and kit measurement/image helpers ported.
  Critique branch afa9a90f was inspected; the current kit critique already
  supersedes it (zero-offset blurred colour, regional reporting, focus-safe notes).
- Fable A ee83409f: retained the painted Eevee look, per-part projection/seam
  fill, calibrated registration and display-space reduction already in round 11.
- Fable B 28da82cb: selected measured greave/ankle shaping, guard placement,
  seated straps, cloak flare/hem, disc diameter/band and authored forward death.
  Did not import its old duplicated kit, old materials or permissive contact bounds.
- Astra A 190749cb: original-length foot fitting wins on contact. Selected its
  width-without-lengthening rule; dropped its competing shin/guard fit because
  Fable's same-region silhouette was stronger in the director's review. Did
  not stack both deformations. Sleeve shortening had already lost its A/B.
- Astra B e1c58d74: retained frozen brown sole undersides, shadowed skirt lining,
  rear shoulder continuity. Its own rest colour regressed very slightly
  (blurred 4.509 → 4.514) for the motion win (lining luminance 101 → 83).
  Shared implementation now lives in kit/continuity.py, called by the unit wrapper.
- Astra C 3ac739c9: selected KayKit Hit_B (CC0), wider Quaternius walk tracks
  and reduced walk shoulder swing. Dropped its donor death: improved over r11,
  but Fable's shield/crest ending is more readable at 64 and 160. The director's
  alleged Fable "cloak fin" was the crest; no corrective flattening was applied.

## Integration failures and decisions

Fable's x1.42 foot length failed the unchanged 40 mm contact bound: 42.6 mm
sole correction, then 56.5 mm root correction with the support IK solve.
The combined candidate uses x1.50 width, original length and x1.18 height,
plus Fable's guard/strap/shin fit. This deliberately sacrifices some of the
standalone Fable rest silhouette to retain a valid walking foot. Support-foot
IK preserves donor foot rotation and limb lengths; no check was loosened.

Idle and attack keep their source choreography. They must be rebuilt on the
changed guard and geometry, so this is a form rebase, not a claim that the
round-11 action or .blend hashes remain identical. The round-12 action receipt
pins the locally checked result for the GPU rebuild; the final appearance still
needs the lead's review.

The CPU painted-look proxy uses the real frozen pigment and Cycles AO, but an
analytic sun instead of Eevee Shader-to-RGB and no live cast shadow. GPU colour,
contact shadows and final byte size must be measured again; CPU and GPU numbers
are not interchangeable.

### Automated critique: spearman-round12 (Cycles CPU painted-look proxy, 256 px / 8 samples, decoded 160 atlas; not GPU)

- Silhouette IoU: **0.9394** (target ≥ 0.95; FAIL). Best of ±3 px offsets: render x=+0, y=+0.
- Tone/colour ΔE on blurred images (sigma 2 px, CIE76): **4.55** (target ≤ 6; PASS), at zero offset over 11574 overlapping pixels including base. Information only: raw per-pixel ΔE 8.35; at the IoU offset blurred 4.55, raw 8.35.
- Regions (blurred ΔE): head_crest 3.7, torso 2.7, cloak_spear_side 4.4, shield 2.2, legs 2.9, feet 13.4, base 4.7.
- Painting mask: alpha; frames: idle 8, move 8, attack 10, hit 4, death 10.
- Rest: `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r12-merge/preview/rest/00.png`. Contact sheet uses `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r12-merge/review/3d-v2/spearman-decoded-160`.

## Final CPU evidence and honest verdict

Same settings: Cycles CPU, 256 px, 8 samples, seed 17, no denoising/adaptive,
painted-look proxy and display-space reduction. Matched R11 → R12:

| Measure | R11 | R12 |
| --- | ---: | ---: |
| Silhouette IoU | 0.924358 | **0.939372** |
| Blurred zero-offset ΔE | 4.4881 | **4.5530** |
| Raw ΔE (information only) | 8.2024 | 8.3472 |
| Feet regional blurred ΔE | 13.9604 | 13.3515 |
| Cloak spear-side ΔE | 3.0501 | 4.3706 |
| Base ΔE | 3.8784 | 4.7462 |

Silhouette improves; colour slightly regresses. These are not the 512 px GPU
numbers. The 0.95 IoU target still fails; the colour target passes. Do not round
0.939372 up to claim the reviewer's 0.94 candidate threshold passed.

The contact-strength-only A/B is a small win: 100% → 40% contact changes global
blurred ΔE 4.5745 → 4.5530 and base ΔE 4.8554 → 4.7462. It does not fix sandal
straps or establish that final Eevee shadow edges are correct.

- **33 tests pass:** 24 kit, 4 critique, 2 pipeline, 3 look. Python compilation,
  Bash syntax and whitespace checks pass. All source/license hashes verify.
- Rebuilt master and all five baked clips; scene checks pass; all 40 poses
  audit with **zero findings**. Rest sole clearance **1.000 mm** on both feet
  (was 3.000 mm); the new 2 mm rest gate passes.
- Walk: **33 dense samples**, all eight limits pass; compensated sole slip
  **0.00179 mm**, floor error **0.000366 mm**, planted heading **5.142°**,
  readable heading **9.175°**, seam **0**. Root correction **48.963 mm**,
  foot IK **19.943 mm**, sole correction **28.186 mm**. Heading is a regression
  from the smaller-foot lane C and near the 10° limit; no threshold was relaxed.
- CPU preview atlas: **190,952 bytes, Q80**, 160 px trimmed cells and all
  **8/8/10/4/10** frames; decoded alpha, offsets, gutters, bounds, motion and held
  death validate. Shipped atlas was not overwritten.
- Movie verified **1600×352, H.264 yuv420p, 192 frames, 8 seconds**. Viewed movie
  samples, all 40 decoded cells, native 256/160/64 comparison and full feet sheet.
- Rebased idle/attack action receipts verify. They are pinned for repeatability,
  not represented as byte-identical to round 11. Existing choreography is kept.

## Remaining visible gaps, ranked

1. **Sandals/ankles (256: x 82–110 and 145–170, y 206–225).** Feet ΔE 13.35 is
   still far above 6, while every other region is below 5. Instep/strap bands
   remain soft and the sole edge heavy; the painting has three crisp dark bands
   and a thin sole. At 160 the feet read as small brown masses rather than
   articulated sandals. Original-length feet avoid the failed contact budget
   but do not reproduce the painted toe footprint exactly.
2. **Stone and contact (x 75–180, y 215–244).** Base ΔE rose 3.88 → 4.75 despite
   the shadow-strength win. The top/rim shape fits better, but the side remains
   uniform and the warm shadow behind the feet is weak in this CPU proxy.
   At 160 it still reads flatter than the painting. GPU cast-shadow review is
   required; no claim that the foot-slab issue is fully solved on Eevee.
3. **Cloak (x 98–113, y 118–176; hem x 120–165, y 175–195).** Spear-side colour
   regresses 3.05 → 4.37 after the form change; lit folds are not as rich as the
   painting. The final Fable centre scallop is included, but side hem contours
   still read cleaner and more geometric at 256. At 160 this is subtler than feet.
4. **Motion.** Both legs separate and the pale sole flashes are reduced, but
   the walk still lifts the trailing foot like a march. Hit frames 1 and 2 are
   close in silhouette. Fable's early spear tip and shield-facing corrections
   are included; its death is more recognizable than Astra C's low heap, though
   the face-down torso/head remain partly hidden under the shield at 64.
5. **Small residual form and paint seams.** Spear-hand sleeve sliver near
   (106,123), some noisy/soft painted edges at 256, and modest stance mismatch.
   At 64 the unit identity, crest, shield and spear read correctly and are close
   to the token; the base/feet and motion still prevent painting-level approval.

Artifacts: `spearman-round12-restpose-compare.png`, `spearman-round12-crossfade.png`,
`spearman-round12-contact-sheet.png`, `spearman-r12-merge-sizes.png`,
`spearman-g-feet-check.png`, `spearman-round12.mp4`; all current round-12 review
pixels are explicitly CPU evidence until the lead's GPU handoff overwrites them.
The 05:17Z art-director update was read during the merge; no PASS file was written.

### Automated critique: spearman-round12 (Eevee painted GPU 512 masters / display-space decoded 160 atlas)

- Silhouette IoU: **0.9384** (target ≥ 0.95; FAIL). Best of ±3 px offsets: render x=+0, y=+0.
- Tone/colour ΔE on blurred images (sigma 2 px, CIE76): **4.72** (target ≤ 6; PASS), at zero offset over 11544 overlapping pixels including base. Information only: raw per-pixel ΔE 7.52; at the IoU offset blurred 4.72, raw 7.52.
- Regions (blurred ΔE): head_crest 3.7, torso 2.9, cloak_spear_side 4.8, shield 2.4, legs 3.4, feet 12.9, base 4.8.
- Painting mask: alpha; frames: idle 8, move 8, attack 10, hit 4, death 10.
- Rest: `/Users/samcorcos/LegatumRuns/anim-pilot/masters/spearman/256/rest.png`. Contact sheet uses `/Users/samcorcos/LegatumRuns/anim-pilot/review/3d-v2/spearman-decoded-160`.

### Delivery receipt (GPU final render, visual review pending)

- 40 frames; 160 px trimmed atlas: 186556 bytes, quality 80; decoded validation PASS.
- Walk: planted slip 0.0018 mm; floor error 0.000 mm; heading 5.142°.
- Movie: five clips, 1600×352, H.264 yuv420p, 192 frames / 8 seconds. No art PASS issued.

FOCUS a: Match sandal instep height, strap bands and remaining shin contour without lengthening feet beyond the contact budget.
FOCUS b: Review final GPU foot shadows, sandal tone and cloak lit folds; preserve the lining/sole continuity wins.
FOCUS c: Reduce the march-like swing-foot lift and separate the hit peak/recovery at 160; preserve the readable death and contact-clean walk.
