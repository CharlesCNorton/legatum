# Spearman round 10 — combined candidate

**Not PASS.** All three lanes offer useful, limited improvements. The 3D reconstruction still differs visibly from the painting. This note distinguishes lane A/B evidence from newly rebuilt combined CPU evidence; a final GPU pass remains for the lead.

## Lane decisions

- **A — retained** from `597b10c9`: fuller calves and greaves, articulated sandal welts, and a broader guard orientation. The source human feet, soles, original weights and bind matrices remain intact. Lane evidence: lower-leg silhouette overlap **71.96% → 73.21%**, projected sole span **68.98 → 77.03 px**. The more grounded support is visible at 256/160; subtle at 64. Rejected experiments from this lane (oversized flares and excessive outward knees) were not imported.
- **B — retained** from `56d294ee`: warmer unseen linen/skin, cinnabar rear shoulder coverage and darker broad cloak folds. Lane same-settings hit evidence: pale shoulder pixels **102 → 24 at 256**, **39 → 7 at 160**. Rest shoulder error slightly worsened **12.06 → 12.20/255**; this is a motion-coverage win, not a claimed rest-colour win. Repainting only the cape was insufficient because the sleeve supplies much of the exposed pale patch. The small rest difference does not outweigh the clearer hit/death improvement.
- **C — retained** from `9c06a96c`: 90% donor-space walk influence, source-pose blends to restrain death recoil, shield retained at the arm with floor-aware hinge response, and more damped cape/crest settling. Lane death metrics: largest sampled head step **1.277 → 0.655 m**, maximum ankle height **0.848 → 0.355 m**, late cape travel **0.419 → 0.146 m**. This produces a readable knee yield and fall instead of the prior feet-up recoil. Keep attack/idle and the round-9 restored hit pins. Stronger walk attenuation that broke contact was not imported.
- No submitted final lane improvement was dropped. Historical round-9 copies of the atlas and shared files in B/C were excluded; only their current deltas were ported. The skill (`bd12b8c2`) and critique (`afa9a90f`) branches were also ported. Git merge locks are denied in this sandbox; these are source ports, not merge commits.

## Remaining visible gaps, ranked

1. **Shoulder anatomy and hidden garment paint.** At 256 the rear shoulder remains a hard, angular shell, with broad plain colour where the painting has shaped folds and transitions. Warm coverage reduces the pale interruption but does not model or paint the missing surface. At 160 the patch is less glaring, but the shoulder changes shape abruptly in hit/death.
2. **Lower-leg mass and coherent rest silhouette.** The support is wider and the greaves fuller, yet the painting has heavier ankles, broader footwear and a more convincingly braced knee/hip relationship. The render still feels narrower and less weighted. This remains visible at 160; the same-unit identity is clear at 64, without matching the painting's craft.
3. **Death shield and motion weight.** The fall is calmer, but the shield visibly hinges as it approaches the stone and the final support can look arranged. The walk remains stylized despite passing contact tests. These are broad movement issues visible at 160 and 64; numerical slip checks cannot certify natural motion.
4. **Value structure and stone.** At 256 the painting has deeper cloak/inner-leg cavities, a darker shield rim and more deliberate bright bronze edges. The render's base is too uniformly orange/regular and its broad surfaces softer. At 160 these broad tone differences matter more than extra weave. Do not increase global saturation to fix missing shadows.

## Reusable work and verification

The new `tools/art/anim3d/kit/` owns the MPFB rig factory and optional Rigify/corrective helpers, painterly cavity-pigment node group, frozen projection and geodesic seam fill, matched camera/light preset, Quaternius rest/roll retargeting with heel/toe locks, premultiplied linear-light resizing, and critique/report generation. Spearman imports these through its existing scripts. It retains its original 53-bone rig; no unverified Rigify migration or corrective sculpture is being claimed. CMU/Rigify motion maps and multi-view PaintUV baking are not implemented by this extraction.

CPU masters and clips are isolated in `~/LegatumRuns/anim-pilot/lanes/spearman-r10-merge/`. CPU atlases are isolated via `ATLAS_OUTPUT`; the checked-in GPU atlas is retained until the lead's pass. The final GPU handoff rebuilds all five clips, stages, 512/256 masters, a decoded/validated trimmed 160 atlas (quality ≥75, ≤200,000 bytes), 8-second five-column H.264 movie, feet sheet, native 256 triptych, crossfade and 160 contact sheet. It runs `critique.py` and appends numbers here before the focus lines.

Run from the repository root: `ROUND=10 tools/art/anim3d/units/spearman/gpu.sh`. No PASS file is justified or written.

FOCUS a: Refine the shoulder/sleeve shell and the remaining ankle/greave mass against the painting at 256/160, preserving real foot geometry and the wider guard's contact.
FOCUS b: Paint coherent shoulder/back/underside folds and restore dark cloak, inner-thigh and shield-rim values; preserve highlights and avoid orange saturation or finer noise as substitutes.
FOCUS c: Smooth the arm-attached shield's floor hinge during collapse and improve walk weight using donor motion; retain clean contacts, attack/idle and restored hit pins.
