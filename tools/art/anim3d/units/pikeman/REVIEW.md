# Pikeman round 2 review

Status: CPU candidate complete; **not art approved**, PASS absent. Round-one GPU pass succeeded at 177646 bytes / quality 90. Its original sheets and movie are preserved in `review/3d-v2/pikeman-round1-gpu/`.

## Changes
- Fitted raised grip, swept helmet brim, narrower breastplate and bounded upper-body contour field, preserving true camera depth and original articulation before frozen painting UVs.
- Thinner bevelled cream stone disc, new image-generated clean stone top, original unobstructed lower rim and live contact AO. Generated alpha blends pigment only; it never cuts the geometry.
- Box-mapped generated steel/leather/skin fills, richer product lighting, normal-displaced cloth folds and continuous clothing/boot underlayers. Same automatic rest-fitted histogram grade across every clip.
- Applied finishing modifiers produced negative deform weights (one trouser weight was -0.949), causing a metre-long spike and a rejected clipped death frame. Clamping/normalizing finished weights fixes that defect; the scene audit now rejects it. Garments are restricted to their anatomical regions.
- No-argument GPU handoff now verifies a portable seal over the reviewed scripts, textures and masters before rendering. All six Blender skills used; no engine/rules/runtime UI changes.

## Evidence and verdict
Opened round-one GPU c/f, detail and all e strips, plus MP4 samples before/through review. Opened final CPU c/d/e, feet, split/crossfade and early/held MP4 frames. At 64px it reads as the same silver pikeman with the wide guard and long diagonal shaft. At 256px the stone and silhouette are closer, but it is **not hard to distinguish from the painting**: the raised glove and inside-arm gap, helmet highlight/edge registration, boot/greave contours and pike endpoint alignment still differ. Movement and collapse expose simpler gray surfaces and paint seams; attack remains modest. The spike/clipping bug is fixed, but passing the technical checks does not make all five clips artistically clean. No PASS.

## Exact final checks
- Python AST: 20 scripts passed. Both shell entry points: `bash -n` passed. `git diff --check` passed.
- Scene check passed: 53 bones, finished real meshes, frozen camera pigment, clean-stone UVs, positive normalized deform weights and safe scales.
- Six real Cycles AO/Pointiness bakes regenerated. All five rig audits passed; maximum wrist-axis distance 0.099563095 m, stationary base and held death. Wrist distance is not a finger-contact guarantee.
- All stages rendered sequentially on Cycles CPU at 256px / 16 samples; feet at 128px / 8 samples. 40 frames in rows 8/8/10/4/10.
- Trimmed 160px atlas: **174520 bytes, WebP quality 90**. Independent decoded alpha/offset reconstruction, source hashes, transparent margins, visible motion and pixel-identical held death all passed.
- Feet: minimum planted forward-axis dot 0.999999940; sampled virtual-ground stance residual 0.000001103283 m. This is an ankle-sample check, not a continuous sole collision solver.
- MP4: H.264 yuv420p, 1600x348, 240 frames, 8.0 seconds; five clips at 2x on cream, labelled CPU preview.
- Build-input seal: 35 current inputs verified. GPU script executable and syntax checked. Actual round-two GPU pass is pending the host; no GPU receipt or native512 round-two claim.
- `origin/master` has zero commits ahead of this branch; no fetch or merge needed. No Rust or runtime changes, so no engine/app builds were run.

## Lead command
```sh
ROUND=2 tools/art/anim3d/units/pikeman/gpu.sh
```
Run from repository root. Checks sealed inputs and Metal, regenerates/audits clips, renders every stage and 40 frames on Cycles GPU at 512, exports native512/gallery256 masters, produces feet and rest comparisons, packs and validates the 160px atlas, writes `pikeman-round2.mp4` and GPU receipt. Fails explicitly on unavailable GPU or stale inputs. Never writes PASS automatically.

Current editable blends, bakes and CPU256 masters are under `masters/pikeman/`; review images, animated WebPs, movie and running log are under `review/3d-v2/`. Round-one native512 masters remain historical until the GPU pass replaces them. Exact generated-fill prompt, IDs and hashes are in unit SOURCES.md/stone-fill.prompt.txt/assets.lock.json and external assets/SOURCES.md.

## Commit handoff
Git staging was denied creating `.git/worktrees/lane-3/index.lock` (Operation not permitted). All round-two changes remain uncommitted for the runner. The requested co-authored message is saved in external `review/3d-v2/pikeman-commit-message.txt`. No push, PR or PASS. Repository merge/art gates were not rerun against an outdated committed HEAD; the runner must run them on the resulting commit before landing.
