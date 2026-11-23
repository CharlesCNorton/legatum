# Jet fighter 3D animation candidate

Run from repository root. All Blender calls use the plain `blender` PATH gate. The model is a closed longitudinal silver fuselage, thick swept airfoils, tail, rounded canopy, recessed intake, panel relief and a curved stone pedestal. The painting is projected once onto the finished rest geometry. Unseen surfaces use painted silver fill with physical metal shading. No image cards or render-time silhouette masks.

CPU round:

```sh
tools/art/anim3d/units/jet-fighter/render.sh build
source tools/art/anim3d/env.sh
for stage in b c d e-idle e-move e-attack e-hit e-death g; do
  CYCLES_DEVICE=CPU RESOLUTION=256 SAMPLES=8 tools/art/anim3d/units/jet-fighter/render.sh "$stage"
  "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/jet-fighter/deliver.py "$stage"
done
blender -b --disable-autoexec --python-exit-code 1 --python tools/art/anim3d/units/jet-fighter/audit.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/jet-fighter/deliver.py pack
```

The build command requires the original source and painted fill recorded in SOURCES.md. It registers the painting, constructs the model and physically bakes AO/Pointiness on fuselage and wings. Render b before bake when reviewing a new construction. Changing geometry requires rebuilding and rerendering all clips; changing render.py invalidates clip receipts.

Host handoff, no arguments:

```sh
ROUND=1 tools/art/anim3d/units/jet-fighter/gpu.sh
```

The host script requires Metal, renders every review stage and all 40 frames at native 512px, exports 512/256 masters, grades once from the rest pose, packs/validates a trimmed 160px atlas at quality >=75 and <=200,000 bytes, and writes the eight-second five-clip H.264/yuv420p round video. It fails rather than silently falling back to CPU. CPU images are previews and never counted as 512px masters.

All editable scenes, bakes and frame masters are in `$ANIM_ROOT/masters/jet-fighter/`; immediate stage reviews and running log are in `$ANIM_ROOT/review/3d-v2/`. No app runtime or rules are changed. The candidate stays unapproved until the lead reviews the GPU images against the original at 256/64px. `jet-fighter-PASS` is never written automatically by technical checks.
