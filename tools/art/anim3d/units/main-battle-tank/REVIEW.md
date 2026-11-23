# Main battle tank — round 1

Candidate complete; **not art-approved**, no PASS marker. Static unit art remains active.

The editable, packed Blender model, rigid hierarchy and five clip blends are under
`~/LegatumRuns/anim-pilot/masters/main-battle-tank/`. The scene has a low cast dome,
beveled armour, separate skirts, six wheels per side, 124 independently animated
track links, rear fuel drum/canvas stowage and a long elevated gun. Six actual 512px
AO/Pointiness maps support camera-projected painted surfaces and generated hidden
olive fill. Running gear is separate from sprung chassis motion. A real bearing
collar closes the gap exposed by front-view review. The disc support plane follows
the registered belt run; its bottom rim stays fixed.

All requested b/c/details/d/e and rest crossfade/track-contact evidence exists under
`review/3d-v2/main-battle-tank-*`. Full CPU 256px frame sets and ungraded originals
are retained. `main-battle-tank-round1-cpu.mp4` shows all clips at 2x on cream.
**True 512px rendered masters remain pending the host GPU pass**; no CPU preview was
upscaled and labelled as a 512px original.

## Verified results

- Three closed-route unit tests pass: length/closure, constant speed, shoe tangent.
- Blender geometry/motion audit passes for all 40 samples: 124 links, 16 wheel
  pivots, safe scales, stationary base, wheel travel/radius consistency, gun recoil,
  source hashes, actual bakes and held death. Lowest shoe-to-support-plane distance
  is -0.00674 scene units (slight contact penetration, under one native pixel).
- Trimmed atlas validation passes: **176,488 bytes, WebP Q90, 1375x403**, 160x160
  logical cells, all 40 samples. Per-frame offsets reconstruct alpha exactly;
  transparent gutters and identical decoded terminal death samples pass.
- FFprobe/decoded-frame validation passes: H.264, yuv420p, 1600x348, 240 frames,
  eight seconds. Representative decoded frames were visually inspected.
- Python compilation, shell syntax and `git diff --check` pass.
- GPU entry point was exercised and correctly stopped at Metal preflight in the
  sandbox. It preserved CPU output. GPU rendering itself has **not** been verified.

## Visual verdict

At 64px the low tank, long elevated gun, rear stowage and cream disc read as the
same unit. At 256px the rest pose is substantially closer after projection, but
still distinguishable: cupola/MG silhouette is simplified, barrel sleeve/edge
alignment needs refinement, drum ends and track contours differ, and low-sample
smoke is grainy. Rotating wheels carry some of the painting's lighting; wider-angle
views expose stretched projection and approximate hidden surfaces. These are
round-two work, not a claim of premium parity. Native rest alpha IoU is 0.9091 and
opaque-overlap RGB MAE 10.02; these are diagnostics, not acceptance criteria.

The failed early gun fit is a useful lesson: fit the barrel axis independently of
its mantlet, and average mesh vertices before applying the object's world transform
when finding the muzzle. Otherwise translation gets divided by vertex count and
puts firing effects under the chassis.

## Lead command

From the repository root:

```sh
ROUND=1 tools/art/anim3d/units/main-battle-tank/gpu.sh
```

It runs explicit Metal Cycles at 512px/256 samples, all stages and all clips,
archives 512/256 masters, packs and validates the atlas, and makes the exact
`main-battle-tank-round${ROUND}.mp4` required by the driver. Review the GPU rest
comparison, contact sheet and movie before considering a PASS. The script never
writes a PASS marker automatically.
