# Spearman round 13b — look lane

Lane-authored repository files (only):
- tools/art/anim3d/units/spearman/look.py
- tools/art/anim3d/PLAYBOOK.md (Spearman chapter only)

Baseline: astra/unit-anim-3d-v2 at 07643cd4, round-12 GPU candidate. Git merge failed creating ORIG_HEAD.lock (Operation not permitted). Applied the exact binary file delta from the clean starting tree instead; all 33 baseline files outside the two lane edits match that commit byte-for-byte, including the atlas and gpu.sh. The full baseline filename inventory is `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r13b/baseline-files.txt`. No merge or commit was recorded. Runner handoff: `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r13b/lane-only.patch` and `commit-message.txt`. Do not interpret the baseline imports as new lane work.

## Change and evidence

The look remains render-time only. Straps receive 0.85 linear pigment gain; anatomical insteps and the sole underside/lining continuity are retained. Outer shield-rim cavities receive 0.80 gain fading smoothly out before the highlights. Material cache keys distinguish straps and outer rims from soles/shells while reusing the frozen part textures.

Stone keeps its measured cream top, adds a brighter bevel lip and restrained descending side gradient. Close contact AO is 25 mm / 40%, plus 280 mm / 18% faint top-only AO; both follow evaluated geometry. Shadow tint is warm brown (150,105,70). No projected feet, static shadow patch, new geometry or per-frame fitting.

Matched A/B: same saved R12 master, Blender 5.3.0, Cycles CPU analytic-sun proxy, 256 px, 16 samples, seed 17, no denoising/adaptive, Standard/None, ungraded. The proxy has real AO but no Eevee cast shadow. Images reduced to 160 and 64 in display space. These numbers must not be compared directly to R12 GPU 512 masters.

- Global zero-offset blurred CIE76 (sigma 2): **4.5771 -> 4.4525**.
- IoU: **0.935824 -> 0.935824**; alpha arrays byte-identical. Both best offsets are (0,0).
- All rest/clip geometry, faces, weights, UVs, transforms, camera, pose and action invariants pass before/after look application. Master SHA256: `adccf1c096d7765c71d56a7eaac6c46f965964752e3e2ce8f9694cf333915a04`.

| Region | R12 CPU | R13b CPU |
| --- | ---: | ---: |
| head_crest | 3.8141 | 3.8141 |
| torso | 2.5673 | 2.5678 |
| cloak_spear_side | 4.4606 | 4.4606 |
| shield | 2.1732 | 2.1672 |
| legs | 2.9283 | 2.9326 |
| feet | 13.3272 | 13.3598 |
| base | 4.7722 | 4.0043 |
| base_top | 9.3301 | 9.1701 |
| base_side | 3.8090 | 2.8554 |
| shield_rim | 2.2848 | 2.2818 |

The first seven rows use canonical kit Spearman boxes. Extra diagnostic boxes: base_top=(78,213,177,230), base_side=(78,231,177,243), shield_rim=(139,110,180,174); the last is a box, not a material-isolated rim score.

Review outputs:
- spearman-r13b-compare-256.png / -160.png / -64.png: painting | matched R12 CPU | R13b CPU.
- spearman-r13b-clips-160.png: all 40 fresh CPU frames (8 samples).
- spearman-r13b-feet-check.png: fresh 33-sample top/front geometry check, original diagnostic materials (not the final painted look).
- spearman-r13b-round13-*: actual critique.py output, full 8/8/10/4/10 frames. The saved rest is `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r13b/after.png`.
- Intermediate renders, receipts, rejection images and scripts are retained under `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r13b`; no new asset download.

## Checks

- 33 existing tests pass: 24 kit, 4 critique, 2 pipeline, 3 look.
- Python syntax for all anim3d Python files, gpu.sh Bash syntax/executable bit, git diff --check pass.
- The skill's kit/check_imports.py does not exist in this checkout. Reported as unavailable; changed code imports and builds its graphs successfully in Blender for the rest and all five clips.
- Actual critique.py run: colour PASS (4.4525), silhouette FAIL (0.935824); no art PASS.
- All 40 CPU frames rendered and inspected at 160; final death hold PNGs identical. Existing brown soles and shadowed lining remain visible through move/death.
- Fresh feet check: 33 dense samples, all eight limits pass, slip 0.001794 mm, planted floor error 0.000366 mm, planted heading 5.142 degrees, readable heading 9.175 degrees, seam 0. Foot/body motion is unchanged.
- GPU execution not available in the sandbox. Shipped R12 atlas stays byte-identical, 186556 bytes; no R13 atlas size claim.

## Rejected tests and learned

1. Broad instep + strap gain 0.65: feet error 13.327 -> 13.896; rejected. The feet-region average includes pale stone exposed where the current foot is narrower than the painting, so darkening every foot pixel is the wrong response to that average. Retained strap-only 0.85 for the requested darker leather; the final feet regression **13.327 -> 13.360** is disclosed, not called a win.
2. Strong lower-band darkening to (208,156,101), with a lifted top: base 4.772 -> 4.849, global 4.577 -> 4.810; rejected. Keep the cream top and use a modest gradient.
3. Increasing broad AO to 0.35 instead of 0.18 slightly helped feet but worsened base 4.002 -> 4.083; rejected.
4. The narrow dark sole silhouette persists with contact AO completely disabled (no-contact base 4.704; feet 13.311). It is not only a shadow blob. Do not try to hide it with heavier AO; remaining sole/instep shape belongs to lane a.
5. Local per-object shader changes need distinct material cache keys; part-only caching otherwise lets the first shell/sole silently override rim/strap settings.

## Honest verdict and GPU handoff

Keep the stone change: a visible but modest improvement at 256 and 160. Shield-rim change is subtle. At 64 the same unit reads clearly, but sandals remain small/blocky and the base still lacks some painted irregularity and the directional back shadow. At 256 the three strap bands still do not read like the painting; this lane does not claim a form fix. No PASS.

The final 06:16Z R12 feedback was rechecked. No new feedback arrived during the run. GPU contact depth must be re-evaluated after merging lane a because its larger/higher insteps alter AO. Do not increase darkness solely to conceal remaining sole geometry.

Lead runs from the merged repository root:
`ROUND=13 tools/art/anim3d/units/spearman/gpu.sh`

That existing executable remains intact and performs all stages/clips, recalibration, 512/256 masters, trimmed 160 atlas+JSON, validation, top/front feet sheet, critique and round-13 H.264 movie. It does not write PASS automatically.
