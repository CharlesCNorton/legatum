# Arquebusier animation candidate

True 3D MPFB anatomy, original Renaissance kit and four CC0 Quaternius clips and an authored matchlock attack.
The existing painting remains in the game. This candidate is not art-approved.
The arquebusier chapter of `../../PLAYBOOK.md` records the method and atlas format.

Run CPU stages sequentially from the repository root:

```sh
for stage in refine project bake b c animate preview feet pack; do
  tools/art/anim3d/units/arquebusier/render.sh "$stage"
done
```

`refine.py` preserves an unmodified external input checkpoint, fits full-depth
geometry and finishes rigid surfaces before frozen camera projection. `scene.py`
owns projection, editable clips and rendering; `bake.py` produces actual AO and
Pointiness maps. Original generated unseen-surface fills remain in use.
`finish.py` owns the fixed rest grade, reviews, trimmed atlas, independent decoded
validation and MP4. `test_delivery.py` exercises the alpha/grade contracts.
`audit.py` checks topology, transforms, stationary stone, motion and held poses;
it does not establish full garment or hand/weapon collision clearance.

Host GPU handoff, no arguments:

```sh
ROUND=2 tools/art/anim3d/units/arquebusier/gpu.sh
```

The pass regenerates clips, audits, renders every stage at native 512 px with
Cycles GPU, retains 256 px derivatives, verifies device/blend provenance, then
packs, validates and encodes all five decoded clips. `ROUND` is supplied by the
driver. It records its own transcript and failed-stage status; a success receipt
still requires visual review. No script writes the art PASS marker.

External assets: `~/LegatumRuns/anim-pilot/assets/arquebusier/`, with provenance
in `assets/SOURCES.md` and the original fill prompt beside these scripts.
Masters/checkpoints/bakes/raw frames: `~/LegatumRuns/anim-pilot/masters/arquebusier/`.
Reviews and the honest round log: `~/LegatumRuns/anim-pilot/review/3d-v2/arquebusier-*`.

Known art risks remain the morion outline, projected unseen-surface seams, tailoring at bent
joints, firing shoulder pose and the mechanics of the fall. Judge actual 256/64 px
comparisons and the movie; successful packing does not establish painting parity.

`bind_fit.py` calibrates real ankle pivots and costume depth before retargeting.
`retarget.py` verifies the installed CC0 library hashes and compensates rest pose
and bone roll. `feet.py` renders all eight move samples from front and above,
measures virtual-ground stance error and foot yaw, and publishes `g-feet-check`.
These checks do not replace inspection of the actual shoe and cloth surfaces.
