# Byzantine heir animation candidate

True MPFB anatomy and a 53-bone rig carry the lamellar armour, crown, embroidered
purple mantle, boots and standard. Frozen camera UVs project the source painting
onto finished 3D geometry; generated silk/linen/leather/metal fills cover unseen
surfaces. A frozen camera-ray visibility mask rejects occluded source pixels.
Masters and raw assets stay under `~/LegatumRuns/anim-pilot/`.
The original painting remains the game asset. This candidate has no visual PASS.

## Rebuild and CPU review

From the repository root, using the existing isolated environment:

```sh
source tools/art/anim3d/env.sh
# Only when rebuilding the original model:
tools/art/anim3d/units/byzantine-heir/run.sh build
blender -b --disable-autoexec --python-exit-code 1 --python tools/art/anim3d/units/byzantine-heir/bake.py
# Start here when refining the existing baked checkpoint:
blender -b --disable-autoexec --python-exit-code 1 --python tools/art/anim3d/units/byzantine-heir/refine.py
tools/art/anim3d/units/byzantine-heir/run.sh animate
export CYCLES_DEVICE=CPU RESOLUTION=256 SAMPLES=12 ROUND=3
for stage in b c e-idle e-move e-attack e-hit e-death g-feet; do
  tools/art/anim3d/units/byzantine-heir/run.sh "$stage"
  "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/byzantine-heir/deliver.py review "$stage"
done
blender -b --disable-autoexec --python-exit-code 1 --python tools/art/anim3d/units/byzantine-heir/audit.py
for action in pack validate video; do
  "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/byzantine-heir/deliver.py "$action"
done
```

`refine.py` restarts from `projection-input.blend`, refreshed by a successful bake.
`finish_geometry.py` binds flexible boot cuffs and skirt/hem weights without
moving the posed surface, lowers the rear collar, fits the hair cap and adds dark
woven breeches. Round 3 adds low leather lasts, a sewn two-leg tunic lining,
dense deformable hems, depth-fitted jewels and a registered stone rim.
`garment.py` folds the fallen tunic toward the ground with anatomical clearance;
the shoulder wrap stays attached. Finished-surface projection preserves the painting's illumination
with a camera-only pigment branch. Product lights and the fixed histogram grade
remain active; no material alpha hides geometry.

`motion.py` uses licensed CMU standing, walking and rug-pull fall recordings for
idle/move/hit/death. Hit is a balance-loss excerpt, not a recorded weapon impact.
Death retargets released arms as well as the torso/legs; only the weapon attack is
hand-authored. Cloth folds and settling are authored deformation, not simulation.
Source URLs, licences and hashes are in SOURCES.md and motion.lock.json.

Audit checks the rig, finished UV registration, stationary base, nonzero scales,
clip entry, evaluated boot/shoe overlap in all 40 poses, planted foot direction
and travel-compensated stance slip, plus jewel-to-backing clearance. Packing verifies master/clip/render hashes,
fixed-grade provenance, all 8/8/10/4/10 frames, lossless alpha, trim offsets and
identical held-death pixels. None of these technical checks establishes art approval.

## Lead GPU handoff

```sh
ROUND=3 tools/art/anim3d/units/byzantine-heir/gpu.sh
```

Executable, no arguments, strict Metal Cycles at 512 px / 48 samples. Produces
512/256 masters, all review sheets and clips, top/front feet, the painting/render/
50% crossfade comparison, a trimmed 160 px atlas at Q75 or higher and <=200,000
bytes, and an eight-second H.264/yuv420p MP4 showing all five clips at 2x on cream.
The script checks GPU availability, retains failed-stage status and tees the full
transcript into the driver's log. It never creates a PASS file automatically.

Prior GPU evidence is preserved in `masters/byzantine-heir/driver-r1-gpu/` and
`driver-r2-gpu/`.
Current critique and exact check results are in the external unit log. The head,
cloak contour, stone finish and fallen cloth still differ from the painting; review the new GPU
pass before approval. See this unit's PLAYBOOK chapter for the trim-offset schema.
