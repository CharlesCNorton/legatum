# Landship driver round 2

Round-one GPU pass succeeded: 40 frames, quality90, 188748 bytes, valid video and
geometry. Its complete evidence is preserved externally in
`~/LegatumRuns/anim-pilot/masters/landship/driver-r1-gpu/`.

Round2 improves the actual cab, camera elevation, track ridges and cream disc;
adds generated clean stone and a tiny sponson occlusion fill; corrects the barrel
axis, hollow bore and mantlet recoil pivot; replaces the round flash and opaque
smoke balls with a tapered gas jet and finite closed volume smoke. Frozen painting
UVs, real AO/curvature bakes, product lighting and one automatic rest-derived
histogram grade remain. No cutout geometry or composited subject image is used.

The generated originals are external
`~/LegatumRuns/anim-pilot/assets/landship/{stone,gun}-fill-source.png`.
Built-in ImageGen prompts are `stone-fill.prompt.txt` and `gun-fill.prompt.txt`;
source IDs/licences are in SOURCES.md and exact inputs in assets.lock.json.

Final CPU checks (512px, Cycles CPU, 8 samples, denoised):

- All nine render stages and five clips completed; real 512px and downsampled
  256px painted masters retained under `~/LegatumRuns/anim-pilot/masters/landship/`.
- 160px logical frames, 40 frames, trimmed atlas **1354x521, quality90,
  176628 bytes**. Exact alpha reconstruction, source/frame/grade hashes,
  transparent gutters, motion and identical final death samples passed.
- Saved-scene audit passed: closed manifold hull/sponson, 128 track shoes,
  six actual bakes, stationary stone, no track penetration, closed mechanical
  cycle and held death transforms.
- H.264/yuv420p video **1600x348, 240 frames, 8 seconds** passed FFprobe;
  decoded frames at 0, 0.23, 0.7 and 1.93 seconds inspected.
- Eight Python files parse; both shell entrypoints pass bash syntax;
  diff whitespace clean. Build-input check passes; changed-source and
  CPU-as-GPU rejection checks pass.

Review images, animation WebPs, comparison sheets and the CPU video are current at
`~/LegatumRuns/anim-pilot/review/3d-v2/landship-*`.
The running log records failed intermediate checks and their corrections.

At256, painted armour remains rich and the physical match is improved, but cab
roof, base rim and muzzle/hidden-patch detail are still distinguishable from the
painting. Opaque silhouette IoU improved from 0.939798 to **0.951851**; bounds are
painting (13,54,243,201), render (13,55,241,200). At64 it clearly reads as the same
Early Tank; IoU 0.951882, with a slight width difference. Five clips show grounded
mechanical motion, recoil and a held smoking wreck. Smoke remains grainy at CPU8,
and moving tread pigment requires GPU loop review. **No landship-PASS**.

Lead handoff, executable with no arguments from this repository root:

```sh
ROUND=2 tools/art/anim3d/units/landship/gpu.sh
```

It checks sealed build inputs and geometry, requires Metal, rerenders every stage
at GPU512, retains 512/256 masters, packs/validates the atlas, generates all reviews
including the rest crossfade and top/front tracks, and decodes/verifies
`landship-round${ROUND}.mp4`. Final checks reject CPU receipts. It never grants
art approval. No runtime renderer or static painting was changed.

Commit attempt blocked by sandbox denial of Git index.lock; changes are left
uncommitted for the runner. No push or PR. The pre-fetched origin/master is
already contained in this branch. No Rust/UI code changed; validation was the
full task-specific CPU pipeline above.
