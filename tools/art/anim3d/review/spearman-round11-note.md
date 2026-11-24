# Spearman round 11 — combined candidate, not PASS

2026-11-23 local / 2026-11-24 UTC. Branch `astra/unit-anim-3d-v2`.
The 256/160/64 px comparison is closer to the painting, especially the greaves,
spear-side cloak and shaft thickness. At 64 px it is clearly the same unit; at
256 px the small pale footwear and shoulder shell still identify the render.
The 160 px walk is cleaner but still stylized, and death/hit remain visibly below
the painting's craft. No PASS file was written.

## Evidence boundary

The new combined master, all five clips and every CPU review output were rebuilt
and inspected. Current round11 movie, triptych, contact sheet and feet sheet are
**Cycles CPU hybrid-fallback previews** (256 px, 16 samples), not final Eevee
renders. The selected final look is Fable A v3; its graph constructs successfully
on the combined rest and five clips, and does not change geometry, camera or
actions. The sandbox has no Metal, so the combined painted GPU image, 512 masters
and final atlas byte count remain unverified. The lead's no-argument GPU script
regenerates all of them; it does not relabel or upscale these CPU previews.

## What was kept or dropped

- Skill/critique: ported the initial skill branch through 4068abb5, then reviewed
  the late branch through 2c4c2030 and imported its new shared code. The critique
  branch's original CLI is superseded by the skill branch's wrapper/shared
  implementation. Latest critique scores 2 px-blurred colour at ZERO offset;
  only silhouette searches ±3 px. Old shifted colour is informational.
- Astra a, cfba440a: kept greave fit, tighter calf and seated shin contours.
  Its matched lane lower-leg overlap rose 78.31% → 83.02%, RGB error
  30.79 → 23.56, global IoU 0.90351 → 0.91033. Dropped sleeve smoothing/folds:
  shoulder overlap fell 88.75% → 88.64% for negligible colour gain. Human feet,
  soles, original weights and rest guard remain unchanged.
- Astra b, 3d62a71d: retained localized lining/fold pigment for the Cycles fallback
  (lane lining luminance 55.58 → 50.55 against painting 49.02; regional blurred
  ΔE 6.31 → 5.41). Fable's per-part painted look replaces these shader nodes in
  the final path. Do not count the fallback patch as a separate verified Eevee win.
- Astra c, 858030e7: kept broader source-calibrated walk, donor torso/carry blend,
  iterative evaluated-sole contact, and smoother attached shield in death.
  Lane evidence: mean ankle spacing 0.246 → 0.344 m; shield step 83.03° → 34.41°;
  head step 0.655 → 0.420 m. Tradeoffs disclosed by the lane: ankle height
  0.355 → 0.423 m and late cape travel 0.119 → 0.145 m. The combined rendered death
  still raises its feet and looks arranged. Idle and attack actions are unchanged.
- Fable A, ee83409f: selected its registered per-part emission paint, palette
  fills, shaded cream stone, lighter linen, leather foot pigment, cloak-coloured
  unseen shoulders, shorter warm contact shadows and display-space reduction.
  The art director explicitly preferred its materials. Its supplied v3 look on
  Fable B evidence reports IoU 0.9204 and raw zero-offset ΔE 6.80; its separately
  implemented blurred score is 4.41 and must not be conflated with our canonical
  linear-blur metric. The supplied painted clips hold up better than the hybrid.
  Removed render-time geometry widening; the combined master owns the shaft.
- Fable B, 91e3031c plus reviewed 45b549f2: kept the 6 px spear-side cloak flare
  and 4 px central hem extension. The shaft is genuinely 1.8× thicker in the
  master before projection. Did not stack its whole lower-body scaling on Astra
  A's already fitted greaves; its final larger foot variant lacks a matched
  combined contact/A-B result and remains a candidate. Its visual death/hit win
  is acknowledged: the art director and cloud reviewer prefer them. However,
  `collapse.py` explicitly replaces donor body motion with hand-keyed poses.
  This round's user instruction permits only the attack to be hand-keyed, so
  neither that body animation nor the late skill's conflicting exception is
  adopted. Astra C is the best verified donor-based candidate retained here.
  Fable B's walk additions are not a proven improvement over the checked Astra C
  walk; keep the donor-space calibration and measured contacts.

## Combined checks and measurements

Same-settings A/B: Cycles CPU, 256 px, 16 samples, seed 17, no denoising or adaptive
sampling, fixed R10 LUT on both renders (`spearman-r11-merge-ab.png`):

| Metric | R10 | R11 merge |
| --- | ---: | ---: |
| Canonical silhouette IoU | 0.903509 | 0.921945 |
| Blurred ΔE, zero offset, same LUT | 6.63194 | 6.41502 |
| Raw ΔE, zero offset, information only | 10.54877 | 10.28534 |

Production-style CPU preview uses denoising/adaptive sampling and its refitted
rest LUT: IoU **0.921945**, zero-offset blurred ΔE **5.98499**, raw ΔE **10.22221**.
Its old IoU-shifted colour would have been 7.22866 blurred / 14.46135 raw. This is
why the metric revision must be explicit, not presented as a new artistic gain.
Silhouette target 0.95 still fails. Passing whole-image colour does not fix feet.

- 32 tests passed: 23 kit, 4 critique, 2 pipeline, 3 look/calibration tests.
- Scene checks passed: 19,158 MPFB vertices, 53 bones, real articulated soles,
  finished shield relief clearance and unchanged calibrated camera.
- 40-pose audit: zero findings. All eight foot limits pass over 33 dense samples.
- Planted slip 0.00227 mm (R10 0.0018 mm, slightly worse but far below 1 mm);
  planted floor error 0.0000211 mm (R10 1.133 mm); heading 2.6184°; loop seam 0.
  Root correction 48.8804 mm of 50 mm allowed and sole translation 35.7282 mm
  of 40 mm allowed are close enough to their limits to remain warnings.
- Idle action hash `057f5cef51f6b2199b5834af980f67b1920b0e954f12b50f63d875298dcda227`
  and attack `667d83498c04185fb13b1142c58274ef864aec7ae5222f07f73360d9d5168a6e`
  match R10 exactly. Material-layer invariants pass for rest and all five clips.
- CPU preview atlas: **188,730 bytes, q80, all 40 frames**. Exact decoded alpha,
  trim offsets, anchors, bounds, gutters, source motion and held death pass.
  The previous app atlas is retained until the GPU script packs the new final.
- Movie verified with ffprobe: H.264 yuv420p, 1600×352, 24 fps, 192 frames / 8 s,
  all five clips side by side on cream. Inspected contact sheet, movie sample,
  256/160/64 A/B, hit/death strips and dense top/front feet sheet.
- Python compilation, Bash syntax and `git diff --check` pass. No Rust/UI rules
  changed; origin/master is already an ancestor of this branch.

## Visible gaps, ranked

1. **Feet, ankles and shin stance** (256 box x60–200, y206–222): canonical blurred
   ΔE is 15.7, the largest regional error. Feet remain too small and light;
   raised soles are pale disks. At 160 px the feet lose the painting's broad,
   dark strapped-sandal read. At 64 px the lower body still feels finer/lighter.
   Fable v3 foot pigment should help colour, but it cannot create missing volume.
   Test a real rest-space sandal/anatomy fit, with regenerated contacts, rather
   than rotating retargeted feet or declaring a bone-only check sufficient.
2. **Death and hit silhouettes**: at 160 px death still sits before falling back,
   lifts both feet and exposes pale underside; its spear becomes horizontal too
   abruptly and occupies a large diagonal. Hit frames 1–2 squash the crest and
   show an angular shoulder/cape mass. Fable B is visibly better here but is
   authored body motion. A better CC0 donor/retarget must achieve that staged
   collapse and flinch within the user's motion constraint. Keep idle/attack frozen.
3. **Spear arm, sleeve and greave contour**: the thin sliver under the hand and
   faceted shoulder are visible at 256; left shin still leans more than the
   painting and the right calf/ornament edge needs inspection on clean GPU pixels.
   These survive texture polish. Whole IoU remains 0.9219, short of 0.95.
4. **Material continuity away from rest**: hybrid CPU still has dark shaft pigment
   and pale exposed soles/shoulder. Fable A v3 specifically improves these, but
   its painted highlights on rotated attack/death surfaces must be reviewed on
   the new combined GPU renders. At 160 px a bright underside is more damaging
   than missing microtexture. Do not treat this CPU colour as the selected final.
5. **Cloak and base refinement**: wider cloak is a clear silhouette win, but CPU
   cloak tone remains uneven; rest regional blurred ΔE 5.2. Base is 5.9, with
   its band/contact still less nuanced than the painting. Fable stone is selected;
   verify the short warm shadow, lip and diameter after the GPU pass.

## Reuse and handoff

`kit/` now includes the incoming human/Rigify/corrective helpers, projection and
seam fill, studio preset, retarget/contact, atlas/grade/regions/audit helpers,
registration, quicklook, part painting, and painted node graph. Spearman directly
uses the shared graph and part-paint code (duplicate implementations removed),
configurable premultiplied image resize, and shared feet failure limits. Heavy
assets remain external. Rigify and anatomical corrective authoring remain opt-in;
no migration or verified CMU-to-Rigify mapping is claimed.

Run from this worktree root on the GPU host:

```sh
ROUND=11 tools/art/anim3d/units/spearman/gpu.sh
```

It rebuilds projection and every clip; prepares ID/part-paint/ramp calibration;
renders plain, textured, detail, rig and every clip on GPU; exports 512/256
masters; packs/validates the 160 atlas at q≥75 and ≤200,000 bytes; writes the
round11 movie, exact 768×256 triptych, crossfade, 160 contact sheet and feet check;
runs canonical critique and appends numbers above the FOCUS lines. All filenames
are checked before status becomes complete. No automatic art PASS.

The source correction stays in Fable's texture registration on the frozen UVs;
changing project.py's UV formula as well would double-correct the paint. A later
projection-calibration cleanup must switch both together and prove the same image.

Git's ORIG_HEAD lock was denied, so changes were ported by scoped source diff.
No push or master merge was performed. A full patch and commit message are in
`lanes/spearman-r11-merge/` for the runner if its Git permissions differ.

FOCUS a: Match real sandal/ankle volume, vertical shin and sleeve silhouette against 256/160 references; preserve original weights and revalidate every contact after any foot fitting.
FOCUS b: Run and inspect the selected Fable A v3 GPU look on the combined master; fix sole/shoulder/lining continuity and verify base contact without a second grade or double registration.
FOCUS c: Find/retarget a better CC0 death and hit matching Fable B's staged collapse/flinch, retaining only authored weapon attack; improve camera-visible step separation and preserve frozen idle/attack hashes.
