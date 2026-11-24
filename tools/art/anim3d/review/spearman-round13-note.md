# Spearman round 13 — combined candidate, CPU review / GPU pending

Not a PASS. Final GPU rendering and the pixel-parity gate still require the lead's host. CPU evidence is isolated under `lanes/spearman-r13-merge`; the shipped atlas remains the previous GPU round until the host pass.

## Selection by evidence and latest director verdict

- **Skill/critique:** ported the new consolidated SKILL, LOG, status reference, gridded regional crop, tests and Blender import checker from `astra/unit-anim-3d-skill`. The critique branch's older monolithic CLI is already superseded by the shared kit and its blurred/region metrics; retained the newer implementation. Git refused `ORIG_HEAD.lock`; these are scoped source ports, not recorded branch merges. Exact branch SHAs are in the lane's `source-branches.json`.
- **Astra a, proportions:** dropped the additional 3/10 mm inward ankle tweak. Its matched CPU IoU gain was only .935824 → .936745, zero-offset .936121, while Fable C fixes the actual 2.7–3.3 px vertical misregistration. Do not stack two ankle fits.
- **Astra b, materials:** dropped its overlapping look changes as a bundle. Base ΔE improved 4.772 → 4.004, but feet 13.327 → 13.360 did not improve. Its darker rim would chase the obsolete delivery-path discrepancy: Fable C's direct look already measures the rim correctly. Adopted C's more effective stone/shadow/sandal treatment; no claim that the b-lane base gain is additive.
- **Astra c, motion:** kept its lower walk clearance, phase-locked sway and donor-rotation invariant, extracted to `kit/walk.py`. Lane peak swing clearance 114.2 → 76.2 mm and pelvis range 68.0 → 84.9 mm. Kept its final collapse registration and clearer shield; body-over-disc diagnostic 55.4% → 76.4% on the lane's master. These are source-lane comparisons, not freshly measured combined values.
- **Fable A/B:** retained A's registered per-part painted look and B's underlying leg/foot/cloth/base form and keyed collapse. Their earlier rest (.938 IoU, 4.56 blurred ΔE with A's look) is superseded by C's rest; no old master/atlas copied into this candidate.
- **Fable C:** selected the painted guard registration, fitted disc and cloak, ankle-following ground shadow, side-band gradient and mild leather tone. Source-lane matched CPU IoU .9394 → .9513 and blurred ΔE 4.55 → 3.31; its standalone 1280 Eevee evidence scored .9534 / 3.35, feet 5.38, base 3.26. Those GPU numbers are historical candidate evidence, not this merge's final render. The 06:40Z director says feet, straps, shins, lip and base now match and rest reads identically at 160/64.
- **Fable D:** dropped the death after the new 06:40Z verdict: shield floats over the body in frames 5–6 and the ending is less calm than Astra c. Dropped its walk-foot pitch/yaw edits (post-retarget orientation correction is prohibited). Kept only the earlier spear landing timing, to clear the kneeling figure sooner; must pass the all-pose shaft audit.
- **Idle, attack, hit:** idle donor and R12 donor hit retained. Attack choreography retained but planted legs now target the new guard; old frozen action fingerprints are intentionally invalid until the rebuilt clips are visually reviewed and re-pinned.

## Merge fixes and reuse

Attack leg targets derive from neutral calf tails, preserving the ankle offset. The walk's complete donor track follows the guard's mean ankle registration. An ankle-only attempt failed (29.82 mm slip) and was removed; the constant whole-track shift passes (0.0042 mm slip, 0.0001 mm floor error, zero loop seam). No foot yaw correction, camera movement or frame-dependent sprite offset is used.

The look CLI and delivery renderer now share `configure_render` and `render_frame`, explicitly including 100% resolution. `gpu.sh` renders rest through both entry points and requires exact pixel equality before delivery. CPU calibration is labelled a proxy; the host regenerates the complete GPU look calibration.

The kit already contains MPFB/game rig, opt-in Rigify and corrective helpers, painterly graphs, registered projection/seam fills, studio presets, Quaternius and KayKit retarget maps/contact locks and critique. This round adds donor-preserving `kit/walk.py` and the new imported gridded crops/import checker. No CMU or Rigify retarget map is claimed; Quaternius remains the tested human preset. Heavy assets stay outside git.

## Remaining visible gaps (provisional until the combined CPU sheets below)

1. At 256 px, spear-side cloak between arm and hip is slightly narrow (C evidence: 579 vs painted 632 px in x98–112/y120–175); at 160 it is a small red-mass difference. Restoring the earlier flare requires a measured A/B, not an untested stack on the winning guard.
2. At 256, the back of the ground shadow is a little strong/hard (x105–170/y214–222); it can read as a dark seam at 160. The stone and sandals are much closer overall. CPU has no cast-shadow term; judge this on the host Eevee pass.
3. Small surface remnants at 256: pale/red sliver under the spear hand (~106,123), dark skirt linen (source-lane luminance 98 vs 105) and a simplified cloak hem. These mostly disappear at 160/64.
4. Walk still exposes a lighter sole during toe-off; death must be checked for the shaft crossing the knees after the faster landing. Review those at actual 160 px motion, not just a rest score.

### Automated critique: spearman-round13 (Cycles CPU proxy / 8 samples / decoded 160 atlas; GPU pending)

- Silhouette IoU: **0.9513** (target ≥ 0.95; PASS). Best of ±3 px offsets: render x=+0, y=+0.
- Tone/colour ΔE on blurred images (sigma 2 px, CIE76): **3.39** (target ≤ 6; PASS), at zero offset over 11572 overlapping pixels including base. Information only: raw per-pixel ΔE 7.27; at the IoU offset blurred 3.39, raw 7.27.
- Regions (blurred ΔE): head_crest 3.7, torso 2.6, cloak_spear_side 5.0, shield 2.2, legs 2.7, feet 5.4, base 3.2.
- Painting mask: alpha; frames: idle 8, move 8, attack 10, hit 4, death 10.
- Rest: `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r13-merge/preview/rest/00.png`. Contact sheet uses `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r13-merge/review/3d-v2/spearman-decoded-160`.

FOCUS a: Measure a local cloak-flare A/B (arm to hip) on the new guard; preserve the feet, knee registration, shield and helmet that now match.
FOCUS b: Soften the far ground-shadow edge, identify the forearm sliver by material ID, and compare skirt midtones without darkening already-correct sandals.
FOCUS c: Judge merged clip transitions and spear landing at 160 px; retain donor foot rotations and all eight contact limits, with top/front feet evidence.
