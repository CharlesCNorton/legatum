# Spearman R11a — sleeve and greave shell

Files changed beyond round 10:
- tools/art/anim3d/PLAYBOOK.md
- tools/art/anim3d/units/spearman/lower_body.py
- tools/art/anim3d/units/spearman/shell_fit.py
- tools/art/anim3d/units/spearman/shell_preview.py
- tools/art/anim3d/units/spearman/shell_review.py

Full repository manifest, including 45 imported baseline files: spearman-r11a-files.md.

## Starting point and handoff

Requested merge of astra/unit-anim-3d-v2 was attempted first and denied at ORIG_HEAD.lock. Its anim3d source and existing spearman atlas were ported without touching the index. Input ref: aeacff7d6a1d630ca7935b4eb2852706eb08b6df. The branch already contains origin/master; its newer unrelated map work is retained. Staging was also denied at index.lock. No commit, push or PR was made. Runner handoff: lanes/spearman-r11a/lane-only.patch and commit-message.txt. The patch contains ONLY the five files above relative to the round-10 candidate; apply those deltas when choosing lane winners.

## Change

Round the sleeve boundary and add shallow 4.5mm rest-space cloth folds. Tuck calves under their armour; thicken the distal greave shell, including its foot-weighted vertices; fit the outer shin contours inward while retaining depth, and carry the chased decoration with them. All human foot/ball vertices, sole vertices, topology, skin weights, bind matrices, pose, camera and lights are unchanged. The R10 guard remains exactly intact: sole span 77.0268px.

## Matched rest evidence

Painting / round-10 CPU / R11a CPU / crossfade / split:
- spearman-r11a-256.png
- spearman-r11a-160.png
- spearman-r11a-64.png
- spearman-r11a-lower_legs-detail.png and spearman-r11a-shoulder-detail.png (4x pixels, not native quality evidence)

Cycles CPU, Blender 5.3.0, 256px, 16 samples, seed 17, denoising OFF, adaptive sampling OFF, dither 0, identical camera and lights, fixed R10 LUT on both. Raw images and render receipts remain in lanes/spearman-r11a/. These final numbers supersede preliminary 8-sample denoised iterations.

| Metric | R10 | R11a |
| --- | ---: | ---: |
| Lower-leg alpha overlap, box (90,177)-(166,211), unshifted alpha>32 | 78.3139% | 83.0156% |
| Lower-leg RGB MAE /255, cream composite | 30.7912 | 23.5601 |
| Shoulder overlap, box (99,98)-(128,131) | 88.7484% | 88.6364% |
| Shoulder RGB MAE /255 | 21.2825 | 21.1860 |
| Figure above base overlap | 88.9810% | 89.8746% |
| Whole-image unshifted overlap | 89.9435% | 90.6741% |
| critique.py IoU, alpha>8, best +/-3px | 0.903509 | 0.910334 |
| critique.py mean CIE76 delta-E | 13.7520 | 13.6130 |

Both critique thresholds still FAIL (IoU 0.95, delta-E 6). Regional overlap includes adjacent cloak/spear, and whole-image overlap includes the base; neither is a geometry-only score. The critique contact sheets use the explicitly labelled R10 decoded GPU clips as reference, not purported R11 production frames. Rest is the new CPU render. New all-clip atlas/cloth validation belongs to the lead GPU pass.

## Motion and checks

- shell_preview.py isolation PASS: 3,280 human foot-weighted vertices, original soles/contact IDs, all weights/topology, bind, entire guard pose, camera and lights identical.
- Rebuilt diagnostic move: 33 dense frames; maximum foot/ball matrix rotation delta 0.0 rad, position delta 0.0m versus R10. Welt floor minimum 0.107124m, above 0.105m stone.
- Actual top/front move render: spearman-r11a-g-feet-check.png. Compensated slip 0.001791mm, planted floor error 1.133235mm, planted heading 2.618409 degrees, loop seam 0. All enforced contact checks pass. Existing root correction 48.971mm remains close to its 50mm bound; this lane does not claim a gait improvement.
- Hit-1, death-3, death-8 matched A/B: spearman-r11a-poses-256.png and -160.png. These swap only changed mesh data into preserved R10 actions/baked cloth; pose motion is identical, but cloth is NOT newly simulated. The sleeve still looks angular; no shoulder-motion cure is claimed.
- check_scene.py PASS; 7/7 pipeline/critique/kit regression tests PASS; 68 Python files parse; three shell entry points pass bash -n; gpu.sh executable; git diff --check PASS.
- No Rust, mechanics or UI changes were authored; those build suites are outside this lane. No production GPU render or new atlas-size validation was run.

## Verdict and learning

Keep the lower-leg correction: cleaner, more coherent armour and a better ankle silhouette at 256 and 160. At 64 the improvement is small, with the same unit identity. This is NOT PASS: the painting still has richer transitions, a stronger spear and darker grounded sandals; the sleeve remains a hard shoulder in hit/death. The tiny sleeve rest RGB gain comes with a slight silhouette regression; it is optional for the lead to retain.

1. Foot-weighted armour is not foot anatomy. Excluding both from all fitting accidentally preserves a pinched ankle plate. Allow the armour shell to change while hash-checking the actual foot and sole.
2. Uniformly widening both calf and greave was rejected (preliminary lower-leg IoU 77.87% to 76.62%). The useful combination is tighter outer calf, fuller distal armour and inward shin-contour seating, without changing contact or bone rolls.
3. A small sleeve-boundary smoothing/fold pass is not enough to repair broad shoulder form in recoil. Regional RGB can improve a fraction while the motion silhouette is still visibly wrong.
4. Blender library loading mutates the assigned destination object-name list; pass a copy when retaining the names for a diagnostic geometry swap.

GPU lead command, from repo root after merging winners:

    ROUND=11 tools/art/anim3d/units/spearman/gpu.sh

The existing executable rebuilds projection, all five clips/cloth, stage previews, 512/256 masters, trimmed 160px atlas + JSON, decoded validation, top/front feet, critique, and the eight-second five-column H.264 movie. It must verify the <=200,000-byte atlas after the combined changes. No PASS file was written.
