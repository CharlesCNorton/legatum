# Volumetric spearman comparison

A separate Blender mesh/armature experiment alongside the camera-projected relief
pilot. It is a comparison asset, not wired into the game and not approved final art.
The horseman is not modelled in this lane.

```sh
# Host: try Eevee; rebuild with CPU Cycles if the renderer exits unsuccessfully.
tools/art/anim3d/build.sh spearman
# Sandbox / reproducible delivered engine:
RENDER_ENGINE=CYCLES SAMPLES=16 tools/art/anim3d/build.sh spearman
# Eight selected poses only, or save the rig without rendering:
RENDER_ENGINE=CYCLES tools/art/anim3d/build.sh spearman --preview
RENDER_ENGINE=CYCLES tools/art/anim3d/build.sh spearman --model-only
~/LegatumRuns/anim-pilot/venv/bin/python tools/art/anim3d/validate.py
```

Requires Blender and Pillow in `~/LegatumRuns/anim-pilot/venv` (or `PYTHON`).
`BLENDER` selects a Blender executable. The build shares the relief pilot's atomic
`~/LegatumRuns/anim-pilot/blender.lock`, invokes one Blender process at a time with
`nice -n 10 -t 4`, and explicitly sets CPU rendering for Cycles. Do not remove a
lock owned by another lane. The sandbox may reject the nice adjustment; Blender
still uses four threads. Default Cycles samples: 12; delivery: 16.

All masters, embedded texture maps, preview PNGs and all forty frame PNGs are in
`~/LegatumRuns/anim-pilot/masters/spearman-3d/`. Rebuilding replaces those masters.
The script creates closed volume meshes for the limbs, cuirass, helmet, domed
shield, spear and stone. Cloth uses a thickened drape. Meshes are weighted to a
parented armature; analytic two-bone leg/arm poses and grip targets are baked to
forty frames. Three identical final death poses hold on the stationary stone.
The saved rig is editable; it is not a collection of pre-rendered image planes.

Paint comes from deterministic pigment strokes and small projected armour patches
sampled from the checked-in `spearman-256.png`. The shield's sunburst is drawn by
script. Rough diffuse shading, a small emission fill, texture bump and large area
lights suppress plastic specular highlights and give a soft contact shadow on the
stone. This is an approximation of the painting, not a claim to reproduce its
brushwork or anatomy. No external model/texture or generation service was used.
Source art provenance remains in `app/src/assets/PROVENANCE.md`; this derivative
art is CC BY 4.0 under `LICENSE-ART`, scripts are MIT under `LICENSE`.

Delivery is exactly the relief contract: 2560 × 1280 WebP, 256 px cells, anchor
(127,221), rows idle/move/attack/hit/death with 8/8/10/4/10 frames at
10/12/14/12/10 fps. Only idle and move loop. The packer keeps all forty frames,
tries qualities 80/70/60 and refuses to overwrite an atlas above 200,000 bytes.
It writes `app/src/assets/units/anim/spearman-3d.{webp,json}` plus five animated
review WebPs, a size report and `review/spearman-3d-vs-relief.png` outside git.
The review sheet is made from the **decoded delivery atlases**, at equal 256 px
and 64 px sizes. Each row shows the painting followed by two relief/3D pose pairs.

Serve the repository root and open `tools/art/anim/gallery/`. The added
**Relief vs 3D** section independently loads the two spearman atlases, plays all
five paired clips, offers pause/step per pair, and displays 256/80/64 px. It uses
shadow DOM so the relief gallery's missing-other-unit path cannot disable the
comparison. No existing relief scripts or app runtime files are changed.

CPU validation checks the delivery contract, all cell bounds, alpha, padding,
stationary exposed stone rim, distinct motion and the held raw death frames.
The Blender render additionally checks the evaluated skinned mesh and grip
positions. Browser playback/performance and the project's Claude art review are
lead-side checks; a syntax check is not a browser review. See the critique in
`../anim/review/3d-pass-1.md` for the measured result and visual limitations.
