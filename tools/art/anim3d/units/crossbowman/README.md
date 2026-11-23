# Crossbowman round 1

True 3D candidate built from MPFB anatomy and a 53-bone rig, with solid quilted
clothing, red cowl, kettle helmet, convex pavise and functioning crossbow geometry.
The original source painting is projected using frozen rest-camera UVs and
facing/occlusion masks. Hidden cloth uses the mounted family's generated linen;
materials include grain, worn roughness and actual AO/Pointiness bakes. Motion is
authored skeletal animation with a keyed drawstring, not simulated cloth or mocap.

Use the existing isolated Blender/MPFB/Pillow install from the family playbook.
From the repository root:

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/crossbowman/prepare.py
tools/art/anim3d/units/crossbowman/render.sh build
tools/art/anim3d/units/crossbowman/render.sh bake
tools/art/anim3d/units/crossbowman/render.sh animate
STAGE=c SAMPLES=6 tools/art/anim3d/units/crossbowman/render.sh render
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/crossbowman/post.py review c
```

Render stages `b c d e-idle e-move e-attack e-hit e-death` serially, with `c`
before other textured reviews so all frames use its one fixed histogram grade.
Run `post.py review <stage>` immediately after each render. `post.py pack`,
`post.py validate`, `post.py video`, and `render.sh audit` finish the candidate.
CPU previews are labelled as such in manifests and sheets. Frames and blends live
under `$ANIM_ROOT/masters/crossbowman/`, never in git. Painting and fill input
hashes are pinned in `inputs.json`; prepare refuses changed inputs.

The complete host GPU pass is one no-argument command:

```sh
ROUND=1 tools/art/anim3d/units/crossbowman/gpu.sh
```

It requires Cycles Metal GPU, rebuilds and renders every stage at 512 px, retains
512 and 256 masters, validates the trimmed 160 px WebP/JSON, and creates the
8-second five-clip H.264 review. It does not silently fall back to CPU. The
PLAYBOOK crossbowman chapter specifies the trim format and common anchor.

The atlas is a review candidate. The existing runtime remains untouched. No PASS
marker should be written until the painting/rest comparison and all five clips
meet the user's bar. Structural audits do not prove absence of every mesh
intersection, and histogram matching does not establish painting fidelity.
