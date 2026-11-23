# Hunter-killer driver round 2

**Not PASS.** At 64 px this reads as the same unit, with closer outer legs and a less plastic cream base. At 256 px the stone grain and silhouettes improve on round 1, but the turret and joint shapes remain simplified, the base highlight is too continuous, and some projected armour loses depth when moving. Movement is still deliberate in-place mechanical stepping; it does not convincingly advance. No PASS marker was written.

## Changes and evidence

- Opened the lead GPU c/f, every clip strip and sampled round-1 MP4 frames before editing. Round 1 actually succeeded: 187,526 bytes at Q90 and verified GPU512/256 masters. Archived its review files and master frames in `masters/hunter-killer/driver-r1-gpu/`.
- Refitted full-depth outer upper armour and three shin contours; moved the far-left foot inward and widened the stone bevel. Kept the closed mechanical rig, six AO/Pointiness bakes, original projected painting, generated olive backfill and product lights.
- Built-in ImageGen supplied a clean stone occlusion fill, registered to the base and feathered into the original lower rim. The real mesh carries it; alpha never cuts geometry and no source feet are painted on the fixed disc. Prompt: `stone-fill.prompt.txt`; bitmap: external `assets/hunter-killer/stone-fill-source.png`; input hash and licence recorded.
- Lengthened overlapping foot swings, reduced fore-aft travel after the rear leg reached its IK limit, added chassis weight shift and stronger recoil/recovery. All rigid links keep their lengths and planted feet retain their positions.
- Added sealed recipe/input/scene checks before final rendering and GPU work. Incomplete or stale builds now fail explicitly. `gpu.sh` defaults to round 2 and still renders every stage, all masters, atlas, validation and movie.
- Review c/f labels state CPU/GPU. Detail crops now compare both images at native 256 px; previously the original 1024 source was compared against an enlarged 256 render.

## Exact checks

- Complete CPU pipeline: exit 0; Cycles CPU, 256 px, 16 samples. All b/c/details/d/g stages plus 8/8/10/4/10 clip frames, five animated WebPs, f comparison and round-2 MP4 regenerated. No CPU preview was upscaled to a 512 master; existing round-1 GPU512 files remain historical until the new GPU pass.
- Trimmed 160 px atlas: **193,792 bytes, WebP Q90** (Q95 was 250,144 bytes). All 40 frames retained; transparent alpha/trim reconstruction, frame bounds, clip metadata, motion, provenance and held death passed. Idle/move loop seam ratios 0.781931/0.734352.
- Geometry audit: **62 closed manifold meshes**, four IK legs, six baked maps, zero sampled planted-foot error, maximum segment-length error **2.626983e-7** Blender units; fixed base and closed loop endpoints. This is not a complete collision audit.
- FFprobe: **1600x348 H.264 yuv420p, 240 frames, exactly 8 seconds**. All five strips, top/front foot sheet and decoded MP4 contact sheet inspected; no detached parts or frozen painted feet observed in those views.
- Preflight positive check and intentional incomplete/stale-recipe rejection checks passed. Python AST, shell syntax and whitespace checks passed. No Rust or UI changes, so their build suites were not run.
- Round-2 GPU512 rendering remains pending on the lead's Metal host. The current CPU evidence is not a GPU or art sign-off.

## Lead command

```sh
ROUND=2 tools/art/anim3d/units/hunter-killer/gpu.sh
```

Run from this checkout on the GPU host. No arguments needed. It verifies sealed masters, renders every stage serially at GPU512/96 samples, creates 256 gallery frames and the trimmed atlas, validates provenance and video, and publishes the round-2 receipt. Review painting parity before setting PASS.

Non-obvious findings: a near-extended rear leg limits fore-aft swing well before the visible front legs do; preserve link lengths and reduce travel rather than forcing the solver. A source-projected base must exclude feet and shadows, or motion leaves ghost contacts. Detail comparisons must use matching resolution. Changes to a script must invalidate the baked scenes as well as render hashes.

Git staging/commit attempted; sandbox denied `.git/worktrees/lane-15/index.lock` (Operation not permitted). Changes remain uncommitted for the runner. `origin/master` is already an ancestor of HEAD. No push or PR. Commit trailer: `Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>`.
