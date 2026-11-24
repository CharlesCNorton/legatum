# Spearman round 12a — geometry candidate, not PASS

Lane-owned files relative to round-11 `01a69951`:

- `tools/art/anim3d/PLAYBOOK.md`
- `tools/art/anim3d/units/spearman/shell_fit.py`
- `tools/art/anim3d/units/spearman/foot_fit.py`
- `tools/art/anim3d/units/spearman/fit_preview.py`
- `tools/art/anim3d/units/spearman/fit_review.py`
- `tools/art/anim3d/units/spearman/fit_motion_preview.py`
- `tools/art/anim3d/units/spearman/check_fit.py`

## Baseline / Git boundary

Requested merge failed because the sandbox cannot create `.git/worktrees/lane-1/ORIG_HEAD.lock`.
Applied the round-11 tree diff to the initially clean worktree instead. The runner still needs
to perform the metadata merge/commit. Staging likewise failed at `index.lock`. The exact lane-only
patch is `spearman-r12a-code.patch`; `spearman-r12a-files.md` also lists the 51 imported baseline files.
`origin/master` (65028a9a) is already an ancestor of the round-11 baseline. Nothing was fetched or pushed.

Suggested commit: `Refine Spearman sandals and vertical shin without changing skin weights`

Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>

## Kept

- Anatomical rest X width 1.50x and Z volume 1.15x for feet, soles, welts and straps, blending into
  the ankle with ORIGINAL foot/ball weights. Y length is unchanged. All original topology,
  weights, binds and sole landmark indices are hash-identical to R11.
- Spear-side ankle 35mm inward and whole foot/ball guard turned 15 degrees BEFORE projection
  and donor mapping; fixed-length thigh/calf solve. The anatomical shin's horizontal knee/ankle
  difference at 256 is 8.686 -> 4.199px; ankle x 101.592 -> 104.501, knee x 110.277 -> 108.700.
- Shield-side calf skin tucked inside its greave using its calf weight, including mixed
  calf/foot vertices. Other geometry, upper-body guard, camera and lights are hash-identical.

## Evidence (matched Cycles CPU hybrid fallback, not Eevee GPU)

256px, 16 samples, seed 17, denoising/adaptive sampling off, one frozen R11 LUT.
Display-space premultiplied Lanczos reductions; own painted token at 64px.
Full render receipt including painting/master/LUT hashes: `spearman-r12a-render-receipt.json`.

| Metric | R11 CPU | Selected R12a CPU |
| --- | ---: | ---: |
| Canonical silhouette IoU | 0.921945 | 0.922863 |
| Canonical zero-offset blurred Delta-E | 6.41818 | 6.28594 |
| Lower-leg alpha overlap, box (90,177,171,210), alpha>32 | 0.86103 | 0.87772 |
| Lower-leg RGB MAE /255, same box on cream | 21.132 | 19.188 |
| Feet RGB MAE /255, box (80,206,172,225) on cream | 34.804 | 31.908 |

Do not compare these CPU values as an A/B against R11 GPU's 0.92749 / 4.59133.
The GPU painted look is better than the hybrid fallback shown here. Feet-box alpha overlap
is dominated by the stone; use the RGB error and actual images for that region.

Images: `spearman-r12a-256.png`, `-160.png`, `-64.png`, `-feet.png`, `-legs.png`, `-sleeve.png`.
The first three show painting / R11 CPU / chosen R12a CPU. `-rest.png` is the selected rest image.
`-critique-contact-sheet.png` shows all 40 regenerated CPU poses; `-g-feet-check.png` shows actual
lower legs top/front over all 33 walk samples. All have been visually inspected.
`critique.py` ran with preset spearman on the selected rest and all 40 current 160px CPU frames;
its canonical report and images are `spearman-r12a-critique-*`. Preset feet blurred Delta-E is
still 13.772, so footwear is clearly unfinished.

## Validation

- 32 tests passed: kit 23, critique 4, pipeline 2, look 3.
- Scene checks passed: 19,158 body vertices, 53 bones, real articulated soles, existing shield
  relief clearance, original camera and physical base.
- All five clips rebuilt from the selected master with fresh cloth caches. Correct frame counts
  8/8/10/4/10; held death frame rendered once and copied byte-for-byte.
- Existing full 40-pose audit: ZERO findings.
- Additional 40-pose audit of every sandal, strap and welt vertex against the real disc / ground:
  ZERO penetrations; minimum clearance +0.99997mm. Large death clearances are the existing lifted
  donor feet, not a claim of a well-staged death.
- Dense walk: all eight limits pass across 33 samples. Compensated sole slip 0.001975mm;
  planted floor error 0.00001365mm; planted heading 3.3817 degrees; readable heading 4.8889 degrees;
  loop seam 0; root correction 48.8784mm; IK correction 19.6299mm; sole translation 35.6160mm.
- All dense walk foot/ball rotations match R11 EXACTLY (maximum quaternion difference 0 radians).
- Original weights, binds, topology, sole IDs, unrelated geometry, upper-body pose, camera and
  lights match the preserved R11 master by hash (`spearman-r12a-checks.json`).
- Python syntax, Bash syntax, executable GPU handoff and `git diff --check` pass.
- No Rust/game/UI changes; no irrelevant full build. GPU/512 masters/current atlas size are not
  claimed as tested here. The app atlas remains the imported R11 output.

## Rejected / learned

1. Lengthening left/right feet 1.35x/1.20x looked fuller but demanded 58.688mm of sole contact
   correction, failing the unchanged 40mm limit. Width plus ankle height passed. Do not choose
   foot fitting on rest appearance alone or loosen the contact limits to keep it.
2. A 25-degree guard turn lost silhouette overlap. The selected 15-degree turn plus inward
   ankle improves the vertical shin. Pose first, then fit the greave contour, then freeze UVs.
3. A 32mm sleeve shortening lost local IoU (0.87611 -> 0.87451) for a tiny colour gain; rejected.
   This does not fix the angular shoulder or the little sleeve/skin sliver under the hand.
4. Protecting every body vertex with ANY foot weight also protected the protruding lower calf.
   Fit the calf by its original calf weight instead; the weights themselves never change.

## Honest verdict / lead handoff

A modest, contact-safe geometry improvement: more upright spear-side shin, cleaner opposite calf,
and broader sandals at 256/160. At 64 it remains clearly the same unit, with only a small lower-body
improvement. NOT a painting match or a PASS. CPU sandals still lack dark three-band strap definition,
lifted soles are pale, and the sleeve edge/shoulder still needs form work. The unchanged donor walk,
hit and death retain the known staging defects; this lane does not replace the motion lane's work.

Run the unchanged executable from the merged repo root:

```sh
ROUND=12 tools/art/anim3d/units/spearman/gpu.sh
```

It rebuilds geometry, the selected painted look, all clips, GPU stages, 512/256 masters, trimmed
160 atlas + JSON, validation, dense feet sheet, comparisons and eight-second round movie.
Revalidate contacts after combining this geometry with the new motion; root correction is already
48.88mm against the 50mm limit. No PASS file was written.
