# Hunter-killer round 1

CPU candidate; **not PASS**. The rest image reads as the same walker at 64 px, and frozen painting projection gives convincing panel wear at 256 px. It is still distinguishable from the painting: the cream disc is too smooth, its rim/edge highlights are flatter, the leg/foot silhouettes and upper hull proportions differ, and the projection is visibly stretched in alternate views. The move is stiff on-the-spot mechanical stepping rather than convincing advancing locomotion; the compact attack and folding death need timing/art review. The original prompt explicitly asks for a four-legged machine, so aircraft motion and animal mocap would be the wrong category.

## Delivered

- Unit-isolated build/material/rig/render/review/delivery scripts, provenance, input hashes and no-argument executable `gpu.sh`.
- External editable model/plain/finished masters, five keyed clip scenes, six AO/Pointiness bakes, and all forty CPU256 RGBA frames under `~/LegatumRuns/anim-pilot/masters/hunter-killer/`.
- Every required b/c/details/d/e/f/g review image, five animated WebPs, running log and round-1 MP4 under `~/LegatumRuns/anim-pilot/review/3d-v2/`.
- Candidate `app/src/assets/units/anim/hunter-killer.webp` + JSON: 160 px logical frames, per-frame trim offsets, 8/8/10/4/10 samples, Q90, **182,178 bytes**. No runtime wiring replaces the painting.

## Verification

- Complete CPU final pipeline: exit 0, Cycles, eight samples, actual 256 px renders; atlas validation passed all forty alpha/trim reconstructions, bounds, motion, size/quality and held-death checks. Idle/move boundary-to-largest-internal-difference ratios .789/.783.
- Geometry audit: 62 manifold closed meshes, four rigid IK legs, six baked maps, zero sampled planted-foot error, maximum segment-length error 2.63e-7 Blender units. Saved endpoint transforms meet the knees/feet, base stays fixed, loop endpoints close and no zero/near-zero scale is used. Not a full collision audit.
- FFprobe: 1600x348, H.264, yuv420p, 240 frames, exactly eight seconds. Decoded representative MP4 frames visually inspected.
- Python AST and shell syntax checks passed; `git diff --check` passed.
- The GPU entry point was exercised: input hashes and scene audit passed, then it stopped explicitly with `No Metal device; refusing CPU fallback`, as expected in this sandbox. CPU evidence was preserved. **Actual GPU512 masters and independent GPU verification are pending**; previews were not upscaled and no GPU success is claimed.

## Lead command

Run from this checkout's repo root on the Metal host:

```sh
ROUND=1 tools/art/anim3d/units/hunter-killer/gpu.sh
```

This renders every stage and all clips at GPU512, retains 512/256 masters, creates the atlas, validates it, regenerates every review image and the MP4, and writes the GPU receipt only on verified success. No PASS marker is created automatically.

Non-obvious lessons: register the mechanical mount in physical space as well as the image; a tiny painted turret gap became a floating turret until a full-depth overlapping socket was added. Projected paint can hide disconnected geometry, so retain plain alternate views. A nearly straight rear leg left too little reach for upward idle bob; compress the chassis instead of stretching links or sliding feet. The stone must not carry projected feet when legs move.

Git staging/commit were attempted and refused by the sandbox (`.git/worktrees/lane-14/index.lock: Operation not permitted`). Changes remain uncommitted for the runner. `origin/master` is already an ancestor of the starting HEAD; no merge was required. Rust/UI code is unchanged, so their build suites were not run. The commit-based browser art gate cannot validate this uncommitted candidate; lead art approval remains pending.
