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

Resumed round 2: after build/bake, run `refine.py` with the isolated Blender
environment, then regenerate animation and previews. Refinement restarts from
`projection-input.blend`; successful baking refreshes that checkpoint. The GPU
entry point includes refinement, keeps its own round log/status, verifies final
GPU/master provenance and never declares visual PASS. CPU previews are 256 px;
current GPU512/48 masters require the host pass.

Feedback 23 supersedes the authored march: `motion.py` retargets licensed CMU
standing/walk/fall recordings for idle/move/hit/death; only the weapon attack
remains authored. See SOURCES.md and motion.lock.json for source identity/licence.
The GPU pass includes `g-feet`, eight top/front views, and records exact source
samples and removed root motion in clip metadata. Foot orientation is not
hand-corrected after retargeting. Final measurements and the honest visual
verdict are in the external round log; this remains a review candidate.

Final round-2 CPU candidate: all forty 256 px / CPU12 frames; 160 px trimmed
atlas 199,854 bytes at Q90; atlas/geometry/foot/video checks pass. Sampled stance
slip is below 0.001 mm after root-travel compensation; planted foot yaw <3.7°.
Eight-second H.264/yuv420p MP4 and top/front foot sheet are in the review folder;
evidence is preserved in `masters/byzantine-heir/round2-cpu`. No PASS: rigid ankle
cuffs separate at strong pitch, the fallen skirt needs refinement, and rest
head/cloth/finial still differ. GPU512/48 verification remains the host handoff.
