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

### Automated critique: spearman-round10 (CPU 256 px / 8 samples; decoded 160 atlas)

- Silhouette IoU: **0.9022** (target ≥ 0.95; FAIL). Best of ±3 px offsets: render x=+0, y=+1.
- Mean CIE76 ΔE: **13.81** (target ≤ 6; FAIL), over 11212 overlapping pixels including base after that offset.
- Painting mask: alpha; frames: idle 8, move 8, attack 10, hit 4, death 10.
- Rest: `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r10-merge/masters/spearman-3d-v2/renders/c/three-quarter.png`. Contact sheet uses `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r10-merge/review/3d-v2/spearman-decoded-160`.

### Delivery receipt (CPU preview)

- 40 frames; 160 px trimmed atlas: 183016 bytes, quality 80; decoded validation PASS.
- Walk: planted slip 0.0018 mm; floor error 1.133 mm; heading 2.618°.
- Movie: five clips, 1600×352, H.264 yuv420p, 192 frames / 8 seconds. No art PASS issued.

### Combined CPU checks and honest comparison

- Cycles CPU, 256 px / 8 samples, fixed seed 17: master plus all five clips rebuilt. **40-pose audit: zero findings.** Scene/material checks pass; the merged lower-body check preserves foot geometry, soles, bind matrices, weights, original body topology, upper pose, camera and lights. The walk uses lane C's 90% donor influence, so lane A's unchanged-walk comparison is not claimed for the combined clip.
- **Matched rest A/B, same 8 samples and fixed round-9 grade:** IoU **0.903515 → 0.902229**; mean CIE76 ΔE **13.735 → 13.905**. This small global regression is disclosed. The broader support and much better revealed-shoulder/collapse behavior justify retention, but the round does **not** improve every metric. The final round-10 fitted grade gives ΔE **13.814**. Threshold >8 / ±3 px metrics are not interchangeable with the older >32 / unshifted silhouette score (current latter: 0.8989).
- **Feet:** all checks pass, including 33 dense samples and zero loop seam. Measured slip **0.0018 mm**, floor error **1.133 mm**, planted heading **2.618°**. The actual top/front rendered geometry was inspected.
- **Motion:** combined death head step **0.6553 m**, maximum ankle **0.3553 m**, late cape travel **0.1188 m**; final pose held exactly. The attached shield's maximum sampled rotation step remains **83.03°**. Grip distance variation is below **0.000001 m**; attachment continuity does not make the hinge look natural.
- **Reusable human probe passed:** MPFB body **19,158 vertices**, game rig **53 bones**, native MPFB Rigify generation **930 bones**, both Armature and preserved-volume Armature PV retained. Synthetic corrective reaches **0.49999994** at half activation. This verifies code mechanics, not anatomical corrective sculpture.
- **Seven regression tests passed:** pipeline 2, critique 2, kit image/note 3. Python/Bash syntax and whitespace passed. No Rust, game rules or UI changes; those build suites do not apply. GPU renders/atlas size remain unverified until the lead runs the handoff.
- Reviewed merged 256/160/64 rest images, hit/death strips, all 40 decoded 160 cells, top/front feet, and encoded-movie metadata. This is not a claim of human real-time playback review.

### Final handoff status

- All stage previews now exist, including the plain three-view geometry, detail crops and attack rig poses. The decoded movie was sampled and inspected; its five columns and cream layout are correct. Comparison detail crops intentionally magnify 256 CPU pixels and are not 512 GPU detail evidence.
- Final checks: **65 Python files parse**, three shell entry points pass Bash syntax, **7/7 regression tests**, `git diff --check`, executable GPU handoff, required CPU output files and final focus-line ordering all pass.
- Git staging failed with `index.lock: Operation not permitted`; the runner must commit the source changes. Exact input refs and the required co-authored commit message are saved in `lanes/spearman-r10-merge/inputs.json` and `commit-message.txt`. No push or PR was performed. The checked-in app atlas was not replaced by the CPU preview.

### Automated critique: spearman-round10 (GPU 512 masters / decoded 160 atlas)

- Silhouette IoU: **0.9039** (target ≥ 0.95; FAIL). Best of ±3 px offsets: render x=+0, y=+1.
- Mean CIE76 ΔE: **14.05** (target ≤ 6; FAIL), over 11207 overlapping pixels including base after that offset.
- Painting mask: alpha; frames: idle 8, move 8, attack 10, hit 4, death 10.
- Rest: `/Users/samcorcos/LegatumRuns/anim-pilot/masters/spearman/256/rest.png`. Contact sheet uses `/Users/samcorcos/LegatumRuns/anim-pilot/review/3d-v2/spearman-decoded-160`.

### Delivery receipt (GPU final render, visual review pending)

- 40 frames; 160 px trimmed atlas: 197114 bytes, quality 85; decoded validation PASS.
- Walk: planted slip 0.0018 mm; floor error 1.133 mm; heading 2.618°.
- Movie: five clips, 1600×352, H.264 yuv420p, 192 frames / 8 seconds. No art PASS issued.

FOCUS a: Refine the shoulder/sleeve shell and the remaining ankle/greave mass against the painting at 256/160, preserving real foot geometry and the wider guard's contact.
FOCUS b: Paint coherent shoulder/back/underside folds and restore dark cloak, inner-thigh and shield-rim values; preserve highlights and avoid orange saturation or finer noise as substitutes.
FOCUS c: Smooth the arm-attached shield's floor hinge during collapse and improve walk weight using donor motion; retain clean contacts, attack/idle and restored hit pins.
