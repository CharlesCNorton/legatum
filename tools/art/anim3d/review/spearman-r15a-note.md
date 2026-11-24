# Spearman round 15a — retain sandal detail; reject cloak trial

## Changed files relative to round 14

- tools/art/anim3d/PLAYBOOK.md
- tools/art/anim3d/units/spearman/look_textures.py
- tools/art/anim3d/units/spearman/look_receipt.py
- tools/art/anim3d/units/spearman/sandal_paint.py (new)
- tools/art/anim3d/units/spearman/round15a_review.py (new)

Round-14 baseline is astra/unit-anim-3d-v2 at 9c35ac22. The requested merge
failed on ORIG_HEAD.lock; its exact file delta was applied instead, including
new/deleted files. This is a content port, not a completed Git merge. Staging
also failed on index.lock. Runner handoff: lanes/spearman-r15a/r15a-only.patch,
changed-files.txt and commit-message.txt. file-scope.json lists every imported
baseline path separately from the five authored files. No push or PR.

## Retained change

The straps already existed as seated, thick geometry. Part-mask erosion was
removing their narrow painted bands, and the skin pass then replaced exposed
toes with blurred leather. Share the original registered pigment across leather
and skin inside each foot footprint. Preserve all original surface alpha,
geometry, weights, bone motion, pose, sole support and base. No new asset or
licence is involved. New paint dependency participates in calibration receipts.

Final master plus all five clip blends are byte-identical to R14, recorded in
lanes/spearman-r15a/final-scene-parity.json. Above row 204, the rerender differs
by at most one channel level, with mean error 0.0000814 (sample noise only).

## Same-settings CPU evidence

These are Cycles CPU analytical-light proxies, 256 px, eight samples, seed 17,
no denoise, original camera and freshly appropriate CPU calibration. The final
baseline rerender reproduces archived R14 CPU metrics to sample noise; none of
the gains below is a GPU-to-CPU comparison.

| Measure | R14 CPU | Retained R15a CPU |
| --- | ---: | ---: |
| Silhouette IoU | 0.951254 | 0.951254 |
| Blurred delta-E | 3.386549 | 3.297989 |
| Raw delta-E (information) | 7.274271 | 7.148674 |
| head_crest blurred delta-E | 3.7378 | 3.7378 |
| torso blurred delta-E | 2.6345 | 2.6347 |
| cloak_spear_side blurred delta-E | 5.0335 | 5.0336 |
| shield blurred delta-E | 2.2225 | 2.2224 |
| legs blurred delta-E | 2.7261 | 2.7278 |
| feet blurred delta-E | 5.4466 | 4.7171 |
| base blurred delta-E | 3.2322 | 3.2160 |

Fine-detail measurements at fixed 256 px boxes, raw RGB mean absolute error:
left instep (94,209)-(108,218) 19.62 → 13.62; right toes
(153,214)-(165,220) 25.65 → 14.50. Painting right-toe p90 luminance is 157;
R14 is 111, retained R15a 140. Detail is restored but still softer than the
painting. These box metrics supplement, not replace, the shared critique.

Evidence: spearman-r15a-compare-{256,160,64}.png; -sandals-detail.png;
-cloak-detail.png (retained, unchanged); -{idle,move,attack,hit,death}-ab-160.png;
-g-feet-check.png; -contact-sheet.png; -metrics.json; spearman-r15a.mp4.

## Cloak trial — do not merge by default

Measured only the wool grid; feet, base, camera and rig stayed identical across
326 objects. Added about 1–2 px of lower-hip flare and traced shallow scallops.
The actual upper edge was already wide enough; the visible shield-side tail
ends at y182–185, not a universal y190. The trial raised IoU .951254 → .953536,
lowered cloak blurred delta-E 5.034 → 4.581, and increased the defined red-pigment
area in x98–112/y120–175 from 480 to 514 pixels (painting 529). This pigment mask
is explicitly r>1.5g, r>1.7b, alpha>128, not the director's different area count.

After rebuilding all five clips, idle's maximum periodic cloth correction rose
71.203 → 98.969 mm. Move improved 273.062 → 159.759 mm. All 40 poses still audited
cleanly, frozen actions matched and the still-frame strips looked stable, but
this was not an across-the-board improvement. Follow the newest reviewer:
retain R14's cloak/cloth instead of introducing that idle regression. The
production project.py is unchanged from R14. The experiment's rest_cloak.py,
check_rest_details.py, master, clips and metrics remain in lanes/spearman-r15a;
images are explicitly named spearman-r15a-cloak-trial-*.png. It is not wired
into gpu.sh or shipped source.

## Verification and honest verdict

- 36 Python tests passed: kit 27, critique 4, pipeline 2, look 3.
- Final 40-pose audit: zero findings. Frozen idle/attack action checks pass.
- Fresh final top/front foot review: all 33 samples rendered; all eight foot
  limits pass. Contact slip 0.004234 mm, floor error 0.000106 mm, planted/readable
  headings 5.142/9.175 degrees, loop seam zero. No post-retarget rotation edits.
- Final CPU atlas: 192842 bytes, Q80, 160 px trimmed cells, 40 records; decoded
  contract/alpha/trim/offset/gutter/motion/held-death validation PASS.
- Movie: H.264, yuv420p, 1600x352, 24 fps, 192 frames, exactly eight seconds.
- Python parsing, import check (zero unresolved), gpu.sh syntax and executable
  bit pass. No Rust/UI changes; no unrelated engine build. GPU script itself
  remains exactly the R14 baseline, retaining every stage, 512/256 masters,
  trimmed atlas, validation, feet review, rest comparison and ROUND movie.
- Inspected the rest at 256/160/64, enlarged sandals/cloak, all clip strips and
  all 33 top/front foot samples. Keep the sandal fix: at 256 the toes/instep read
  closer to the painting; at 160 the difference is subtle, at 64 essentially
  invisible. The paint remains a little softer than the source. Rest cloak
  flare/hem polish remains open. No claim to fix lane b's sole/shadow or lane c's
  boundary cut. No art PASS; final GPU visual review is still the lead's work.

Lead command, from repo root after merging the five-file lane patch:
`ROUND=15 tools/art/anim3d/units/spearman/gpu.sh`.
Do not ship the CPU preview atlas. Final lane output is under
lanes/spearman-r15a/final; the parent lane directory is the rejected cloak trial.

## Learned for the cumulative skill

1. Before modeling missing fine detail, inspect the source, part-ID ownership
   and derived texture. Fine per-part erosion can delete already modeled strap
   edges; nearby skin filled from that leather then deletes toe highlights.
   Sharing original pigment across the registered foot's leather/skin footprint
   recovered detail with no geometry or contact changes.
2. Check review coordinates against the painting: here a blanket 4 px flare or
   y190 right hem would overshoot. Measured local contour changes improved rest.
3. Even a 1–2 px rest-cloth edit changes the simulation. Rebuild and compare
   each clip: better rest and walk can still cost idle. Keep R14 when a candidate
   introduces a regression; preserve rejected measurements for the next attempt.
