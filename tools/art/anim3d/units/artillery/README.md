# Artillery round 1 candidate

Run the full host pass from repository root, with the driver's `ROUND` variable:

```sh
tools/art/anim3d/units/artillery/gpu.sh
```

This rebuilds the model and bakes, renders all stages and 40 frames with Cycles Metal at 512 px,
retains 512/256 masters, packs the trimmed 160 px WebP at quality >=75 and <=200,000 bytes,
validates source hashes/offsets/motion/death hold, and writes the eight-second five-clip MP4.
External inputs are in `~/LegatumRuns/anim-pilot/assets/artillery/`; no network needed after setup.
`render.sh stills` renders only the plain and textured comparison; `render.sh preview` runs all clips.
Both use CPU unless `CYCLES_DEVICE=GPU` is explicitly set. Use `SAMPLES=8 RESOLUTION=256` for previews.

The gun has a mechanical object hierarchy rather than a human skeleton. There is no crew in this
painting. Model and clips are editable `.blend` files under `masters/artillery/`; original source,
generated unseen-surface olive fill, projection, AO and curvature images are packed into the master.
The five clips are authored keys, not screen-space warps. No camera or base animation is used.

The atlas uses the documented `version:2, layout:"trimmed-rows"` extension in the artillery chapter
of `../../PLAYBOOK.md`. A consumer must use each clip's `sprites` rectangles and offsets; a fixed-cell
reader cannot interpret it. This change creates a candidate and does not wire it into the game.

Round 1 is **not art approved**. At 256 px, the far wheel/camera perspective and shield outline differ
from the painting, and the wheel/shield projection still has registration and painted-light artifacts.
At 64 px it reads as the same artillery class, but looks more regular and synthetic than the painting.
Review `artillery-f-restpose-compare.png`, `artillery-c-details.png`, and all five strips and animations
before any PASS decision. The GPU result requires fresh visual review.

The first CPU pass retains 512 px and 256 px sets at eight Cycles samples, plus b/c/detail/rig pose
sheets, per-clip strips/WebPs and a rest-pose crossfade. Its alpha silhouette IoU is 0.8366 at 256 px
(the shared base contributes to this figure; it is not an approval score). The firing flash's initial
parent-space error was repaired in all saved clips and the visible attack sample was rerendered;
`repair_flash.py` records that narrow round-1 repair. Fresh builds create it correctly.

Verified round-1 delivery: **183,530 bytes at quality 80**, 1545×560 atlas, 40 logical 160px frames.
All decoded alpha masks reconstruct exactly at the recorded offsets; frame margins, actual clip
motion, source hashes and held death pass. The review MP4 is 240 frames / eight seconds, H.264
`yuv420p`, 1600×348. Python compilation, shell syntax, and diff whitespace checks pass. The GPU path
is prepared but not executed in the sandbox. Git cannot create this worktree's index.lock, so the
runner must commit with `Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>`.
