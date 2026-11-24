# Spearman round 11b — folds and recessed values

Files authored: `tools/art/anim3d/PLAYBOOK.md`, `tools/art/anim3d/units/spearman/coverage.py`, `fold_paint.py`, `fold_preview.py`, `fold_review.py` (last three in that same unit directory). The complete incoming-round-10 file list is `lanes/spearman-r11b/changed-files.md`.

**Not PASS. Small, bounded surface improvement.** Keep the inner lining and hidden fold work as a candidate; shield-rim change is negligible and may reasonably be omitted by the lead. At 256 the shoulder remains an angular shell with too little modeled form; at 160 the dark lining is better but the overall craft gap remains. At 64 this is clearly the same unit, with little visible improvement. The thin spear, narrow cloak, pale footwear, and stylized collapse are unchanged, outside this lane.

## What changed

Broad frozen sleeve folds gather from the shoulder seam. Wool trough paint follows the existing modeled pleats and retains the round-10 coverage alpha. Unseen pteruges receive shaded ochre lining and dark sewn edges. A feathered mesh-space patch replaces tan projection contamination immediately below the skirt hem with deep red lining. Shield cavities use a maximum 99.5% projected pigment while highlights retain the existing 96%; no new noise or saturation adjustment. No geometry, UVs, rig, lighting, or motion edits.

The end of `coverage.apply` calls the new helper, so the existing GPU script includes this work through its normal projection rebuild. This was exercised on an isolated copy of `projection-input.blend`, with successful scene checks afterward.

## Evidence

Matched Cycles CPU 256 px / 16 samples / seed 17, denoising and adaptive sampling off; identical frozen round-10 LUT on both sides. No histogram refit. Comparisons include the painting and native 256/160/64 reductions:

- `spearman-r11b-rest-compare.png`
- `spearman-r11b-hit-1-compare.png`
- `spearman-r11b-death-8-compare.png`
- `spearman-r11b-fold-details.png` (explicit 3x nearest-neighbor inspection crops)
- `spearman-r11b-round11-contact-sheet.png` (all 40 current material previews)
- `spearman-r11b-g-feet-check.png`

Rest metrics, before -> after:

| Measurement | Before | After | Painting / limit |
| --- | ---: | ---: | ---: |
| Silhouette IoU | 0.903509 | 0.903509 | >=0.95 |
| Raw CIE76 | 13.760854 | 13.754339 | informational |
| Sigma-2 CIE76 | 7.684247 | 7.664212 | <=6 |
| Inner lining mean luminance | 55.578 | 50.552 | 49.017 |
| Inner lining sigma-2 CIE76 | 6.309 | 5.414 | lower is better |
| Cloak RGB MAE | 17.848 | 17.653 | lower is better |
| Shoulder RGB MAE | 11.894 | 11.804 | lower is better |
| Shield-rim sigma-2 CIE76 | 3.740 | 3.751 | small regression |
| Shield p90 luminance | 156.409 | 156.234 | 171.153 |

The global gain is negligible, not a major look-development win. Inner lining box is x119–137/y168–178 at 256; its earlier broader/lower box missed the actual pale patch. Blurred metrics use sigma 2 on cream-composited sRGB, the same best silhouette offset globally, and opaque same-position overlap in regions. This supplemental metric lives in the lane review to avoid concurrent shared-critique edits. The required `critique.py` ran unchanged and still reports failed raw-color/IoU targets. Full exact numbers and masks are in `spearman-r11b-metrics.json`.

On fixed material-ID masks, the exposed hit sleeve mean luminance decreases 109.110 -> 104.324 while its p90 remains 189.265 -> 189.026. Death pteruges lining decreases 132.971 -> 99.183 (239 pixels). These measure reduced pale exposure, not agreement with a nonexistent painted motion pose.

## Verification and limits

- All 41 A/B pose invariants pass: geometry, faces, weights, UVs, object transforms, rig poses/actions, camera and lights unchanged. Every baseline .blend hash matches the preserved lane snapshot, and the shader script hash matches the receipt.
- All 40 motion frames rendered from unchanged baked round-10 motion. Final death frame rendered once and copied; last two PNGs byte-identical. Native contact sheet and rest/hit/death comparisons visually inspected.
- Top/front feet cycle rerendered on CPU; 33 dense samples; slip 0.001791 mm, planted floor error 1.133235 mm, planted heading 2.618409 degrees, zero loop seam. Existing narrow walking stance remains a visual problem, unchanged here.
- Scene checks pass for both the A/B candidate and freshly rebuilt projection. Seven regression tests pass (pipeline 2, critique 2, kit 3); Python/Bash syntax and whitespace pass. GPU handoff remains executable.
- No GPU execution, new production atlas, 512 masters, or final GPU-size claim. CPU motion evidence is lossless 160 reductions, not a decoded shipped atlas. No PASS file written.
- `origin/master` is already an ancestor of this lane HEAD. Requested integration merge failed at ORIG_HEAD.lock. Applied the 44 incoming anim3d source files without modifying Git metadata. Staging also failed at index.lock. Runner must commit; exact co-authored message and lane-only patch are under `lanes/spearman-r11b/`. No push or PR.

## Rejected experiments and learned entries for the merge

- Whole replacement palettes plus broad rim darkening regressed raw CIE76 13.761 -> 13.999 and blurred 7.684 -> 7.916. Preserving source pigment is better than replacing it with nominally appropriate colors.
- Globally tightening the linear-RGB wool red/green gate removed tan contamination but also erased useful paint and made the lining too dark (mean 33.14 vs painting 49.02). A local, feathered mesh-space correction is safer.
- Preserve existing coverage alpha when refining frozen pigment. Forcing alpha to one replaces trusted seam colors even when the new palette seems correct; that was the main cause of the cloak regression.
- Material IDs located the pale inner patch on the cloak, while the revealed death underside is pteruges. Diagnose the actual surface before painting.
- Whole-image improvements can be negligible while one regional problem improves. Report both, preserve highlight percentiles, and inspect at native 160.

Lead command from repo root: `ROUND=11 tools/art/anim3d/units/spearman/gpu.sh`. It rebuilds all clips and all stages, exports 512/256 masters, packs/validates the trimmed 160 atlas, produces feet review and the required five-clip H.264 movie, then runs critique. The lead should judge this against the stronger Fable A material candidate mentioned in the newest reviewer feedback; do not claim this lane supersedes that look.
