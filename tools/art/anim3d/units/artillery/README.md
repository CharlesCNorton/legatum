# Artillery resumed round 2 candidate

Run the complete host pass from the repository root:

```sh
ROUND=2 tools/art/anim3d/units/artillery/gpu.sh
```

The executable script rebuilds the true 3D gun, bakes AO/curvature, renders every review stage and
all 40 frames with Cycles Metal (512 px, default 64 samples), retains 512/256 masters, packs the
trimmed 160 px atlas, validates it, and encodes the eight-second five-clip MP4. It keeps its own
`artillery-gpu-pass-r${ROUND}.log`, failure/status file and verified GPU receipt. Unavailable Metal,
missing inputs, stale outputs, CPU masters and failed delivery checks cannot produce a success receipt.
It never writes an art PASS marker. The hardware GPU pass cannot run in this sandbox.

For CPU iteration:

```sh
RESOLUTION=256 SAMPLES=12 tools/art/anim3d/units/artillery/render.sh preview
~/LegatumRuns/anim-pilot/venv/bin/python tools/art/anim3d/units/artillery/deliver.py
```

`render.sh stills` publishes plain/rest/detail comparisons only. Inputs are the original painting
and existing generated olive fill in `~/LegatumRuns/anim-pilot/assets/artillery/`; no download is needed.
Editable masters and rendered frames remain outside git. Prior WIP evidence is preserved under
`masters/artillery/round1-wip/` and `review/3d-v2/artillery-round1-wip/`.

Round 2 fits complete circular wheels and thick shield plates to source landmarks, applies rigid
bevel/curve topology before frozen camera UVs, and uses visibility-tested camera-only painted
illumination. Hidden surfaces retain the generated olive fill and physical materials. Standard/None
avoids double tone-mapping; the warm stone has top/rim pigment, physical shading and live contact AO.
The automatic rest grade remains fixed across clips. There is no crew in this painting, no image
plane, no per-frame reprojection and no alpha-driven geometry replacement.

Move lifts the trails in the correct hinge directions. Every sampled pose seats both wheels on the
stone and refits the axle, including the damaged-carriage death. The audit checks all 40 samples plus
two loop endpoints for ground clearance and tire contact; it is not a general collision solver.
Identical atlas frames share a rectangle so the final death hold is pixel-identical after lossy decode.
Frame counts remain 8/8/10/4/10. The atlas contract is `version:2, layout:"trimmed-rows"`, with explicit
`sprites` rectangles/offsets and invariant frame anchor; see the artillery PLAYBOOK chapter.
The candidate is not wired into the game.

**Not art-approved; no PASS marker.** At 256 px the hubs/tread are muddier than the painting, trails
and axle construction are simpler, and shield/barrel registration and revealed surfaces still differ.
The stone is warmer but more uniform. At 64 px the same unit reads clearly, with a closer silhouette,
but it remains distinguishable. Silhouette IoU is 0.87784 versus round one's 0.8366; the shared base
contributes to this measurement, so it is not an approval score. Death reads as a disabled gun rather
than a complete wreck. Fresh GPU512 output needs visual review before acceptance.

Final round-2 CPU delivery: 178,156 bytes at Q80, 1521×563, all 40 samples at CPU256/Cycles12. Exact decoded alpha reconstruction, ground clearance, both tire contacts, all clip motion and pixel-identical decoded held death passed. MP4: H.264/yuv420p, 1600×348, 240 frames/eight seconds.

Nine Python syntax checks, two shell syntax checks, whitespace, executable handoff, missing-input
preflight and CPU-master rejection pass. Current 512px finals remain pending the host GPU pass;
old 512px evidence is archived in `round1-wip/512/` and `round1-512-stale/`. No Rust/UI code changed.
