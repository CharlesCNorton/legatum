# Mechanised infantry — round 1

Round-1 candidate, not art approval. No PASS marker. The static painting remains
the runtime asset. All unit-specific work is in this directory.

## What exists

- Original eight-wheel APC with full-depth sloped armour, rear cabin frame,
  lowered ramp, turret/autocannon, wheel hubs and separate rolling tread.
- MPFB anatomical soldier, 53-bone rig, combat uniform/armour, helmet, pouches,
  straps, boots and rifle. Quaternius CC0 idle/walk/hit/death with rest-pose and
  bone-roll compensation; mechanical vehicle clips and authored attack.
- Actual AO and curvature bakes on hull, ramp and turret; frozen source painting
  UVs, hidden-surface painted fills, product lights and bounded source grade.
- Five keyed clip blends and forty CPU256 frames, immediate b/c/d/e/f/g review
  sheets, animated WebPs and decoded-atlas round-1 MP4 under external anim-pilot.
- A version-2, trimmed 160px WebP atlas candidate, lossless alpha and offsets,
  preserving 8/8/10/4/10 frames. Actual byte/quality receipts are in the external
  `review/3d-v2/mechanised-infantry-validation.json`.

## Honest visual verdict

At 256px the carrier's sand/olive brushwork and overall identity are much closer
than the plain model, but the soldier's helmet/face/arms do not register tightly
with the painting. His stance is too upright, the boots pick up light source
pixels, the rifle grip needs closer inspection, and death can hide too much of
him behind the ramp. The wheels lack the painting's convincing heavy rubber
finish. The rear cabin's physical depth/joins and wheel spacing need further
multi-view refinement; screen registration alone does not prove mechanical fit.
The cream base is flatter and less nuanced than the painting.

At 64px this reads as the same eight-wheel carrier plus one dismount; the soldier
is still a weaker, less distinct silhouette. This is not hard to distinguish
from the painting. The atlas passing a size or alpha gate does not change that.

The eight-frame top/front feet sheet and saved-scene audit verify forward foot
axes and lowest-sole contact. They do not certify absence of horizontal sliding,
weapon/hand intersections or ramp contact. The soldier retains the captured gait;
no post-retarget foot rotation patch is used. Rotating wheels retain physical rubber/painted-metal shaders rather than frozen
view-dependent source shading, which visibly wobbled under rotation. The removed
projection approach is not treated as finished wheel paint.

## Lead GPU pass

From this checkout's repo root, run:

```sh
ROUND=1 tools/art/anim3d/units/mechanised-infantry/gpu.sh
```

This rebuilds and renders all stages sequentially on Metal Cycles at actual
512px, retains 512/256 masters, runs the geometry/provenance/delivery checks and
creates the required five-clip 8-second H.264/yuv420p MP4. The sandbox's CPU
previews are not 512px masters or a GPU sign-off. Missing Metal fails before
replacing those previews. Inspect all GPU sheets again, especially soldier
projection, tire shading, grip, rear cabin joins, ramp collision and death.
