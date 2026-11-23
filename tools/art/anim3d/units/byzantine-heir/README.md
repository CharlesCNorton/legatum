# Byzantine heir: round 1 candidate

The infantry MPFB rig carries a new crown, lamellar kit, ivory tunic, boots,
embroidered purple mantle and standard. This is a true 3D character with static
camera-projected UVs and generated unseen-surface fills. The original painting
remains the game asset. This candidate has not passed the painting comparison.

## Rebuild

Run from the repository root with the already installed MPFB/Pillow environment:

```sh
source tools/art/anim3d/env.sh
tools/art/anim3d/units/byzantine-heir/run.sh build
blender -b --disable-autoexec --python-exit-code 1 --python tools/art/anim3d/units/byzantine-heir/bake.py
tools/art/anim3d/units/byzantine-heir/run.sh animate
for stage in b c e-idle e-move e-attack e-hit e-death; do
  tools/art/anim3d/units/byzantine-heir/run.sh "$stage"
  "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/byzantine-heir/deliver.py review "$stage"
done
blender -b --disable-autoexec --python-exit-code 1 --python tools/art/anim3d/units/byzantine-heir/audit.py
for action in pack validate video; do
  "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/byzantine-heir/deliver.py "$action"
done
```

Rebuilding invalidates downstream clips and renders; hashes prevent stale packing.
The scripts expect the source painting and generated texture sheet under
`$ANIM_ROOT/assets/byzantine-heir/`. `prepare.py` aligns the source alpha footprint
to the committed 256 px token. The exact generated fill prompt is adjacent.
Material bakes and all editable `.blend` files stay in the external unit master
folder. The plain master is retained separately for the geometry review.

## Lead GPU handoff

```sh
ROUND=1 tools/art/anim3d/units/byzantine-heir/gpu.sh
```

No arguments. Cycles Metal, 48 samples, 512 px; GPU availability is checked.
Retains 512 and 256 masters, writes all review stages, packs/validates the 160 px
trimmed atlas, audits the rig/base/scales, and encodes the eight-second, five-clip
H.264 yuv420p MP4. See the unit chapter in `PLAYBOOK.md` for the exact trim schema.

The character uses authored skeletal and cloth deformation keys, not a cloth
physics bake. The atlas is a review candidate; technical validation is not a PASS.
Check the latest external log and `byzantine-heir-FEEDBACK.md` before each round.
