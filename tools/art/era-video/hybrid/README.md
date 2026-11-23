# Classical harbour: hybrid v5

The v4 painting, camera, 144 frames, 24 fps, 960×540, six workers and CLI are
preserved. V5 makes the motion readable at delivery size. The lead's dry run
passed; its first bake finished in 38.78 seconds but failed smoke verification.
**The smoke stability fix below has not been run in Blender.** The lead owns all
Blender execution through the machine-wide lock. No commit or game integration.

## Changes

- **Hero galley:** the painted-texture hull is now 3.65 times its v4 size. It
  sails left from source pixel (825,550) to (400,550), with the bow facing its
  travel. Numerical projection gives a 146 px initial hull, 175 px final hull
  (18.2% of the frame), and 314 px centre travel (32.7%). Actual built bounds
  are checked before baking. A ray-projected shoreline/column matte keeps the
  ship behind foreground architecture. Original painted vessels remain.
- **Sail and oars:** two stronger top-pinned sail shape keys, eighteen rowing
  oars, eighteen stroke-synchronised splash fans and 36 staggered bow-spray
  droplets. Spray is animated geometry; there is no liquid bake.
- **Water:** broader moving normals, broken glints and travelling ripples over
  the original water mask, an ivory foam wake and a broken ochre sail reflection.
  Reflection is an artistic shader silhouette, not a physical planar reflection:
  the harbour is a nearly camera-facing relief surface. Its position and the
  wake follow the ship's current camera ray so they stay attached during the
  push. Shorelines and painted ships are excluded by the original water mask.
- **Brazier:** emitter centred on the painted bowl at (390,676). A fixed
  **24×52×16**, **72-voxel**, **2× noise** Mantaflow domain sits entirely in front
  of the relief. Stronger rising/drifting inflow, animated fuel/density/velocity,
  grey-ochre smoke, brighter flame-grid-gated blackbody emission, warm local light
  and glare. All scales are applied; domain/emitter transforms never animate.
  Pre-roll remains -47..144. Smoke/flame vorticity is now 0.15/0.1, noise strength
  0.5, with up to six adaptive substeps at CFL 2. The elongated domain has roughly
  the same base voxel count as v4; no other simulation is introduced.
- **Seven gulls:** approximately 11–25 px open wingspans, separate flap/glide
  phases, crossing paths through sky and harbour, and one nearer pass at Z=160.
- **Cloth:** two blue banners use their original painted pixels on top-pinned
  meshes with free lower edges. Preparation repairs only the wall hidden behind
  those cutouts. The awning retains the inward-masked relief deformation, now
  faster and stronger, with travelling light/shadow folds. Architecture stays
  pinned. Optional walkers are omitted.

The original source image remains unchanged. The displayed plate differs only in
local banner repairs hidden by the moving cutouts and masked cloth lighting.
Standard colour management, the v4 CG-only pigment finish and the fixed-lens 16%
physical push remain. The lead's Blender 5.3 `setv()` fix for same-named float and
colour sockets is retained verbatim; the compositor still uses
`scene.compositing_node_group` and the node-group output interface.

## Commands

Run from the repository root. New output directory preserves all v4 renders and
caches. Python preparation has already been run; rerun it after recipe changes.

```sh
export ERA_HYBRID=/Users/samcorcos/LegatumRuns/era-video-pilot/masters/hybrid-v5
export ERA_PYTHON=/Users/samcorcos/LegatumRuns/era-video-pilot/venv/bin/python
export OMP_NUM_THREADS=6

python3 -m py_compile tools/art/era-video/hybrid/scene.py
"$ERA_PYTHON" tools/art/era-video/hybrid/scene.py \
  --masters "$ERA_HYBRID" --out "$ERA_HYBRID/frames" --prepare

# Define and invoke ONLY while the lead holds the existing Blender lock.
# This function does not acquire the lock itself.
hybrid_v5() {
  /opt/homebrew/bin/blender -b --factory-startup --disable-autoexec -t 6 \
    --python-exit-code 1 -P tools/art/era-video/hybrid/scene.py -- \
    --masters "$ERA_HYBRID" --out "$ERA_HYBRID/frames" "$@"
}
hybrid_v5 --dry-run
hybrid_v5 --bake-only
hybrid_v5 --frames 1-1
hybrid_v5 --frames 72-72
hybrid_v5 --frames 144-144
# Review these stills and a short motion sample before the full run.
hybrid_v5 --frames 49-72
hybrid_v5 --frames 1-144

FRAMES=144 SIZE=960x540 bash tools/art/era-video/encode.sh \
  "$ERA_HYBRID/frames" "$ERA_HYBRID/classical-vfx-v5"
FRAMES=144 SIZE=960x540 "$ERA_PYTHON" tools/art/era-video/contact_sheet.py \
  "$ERA_HYBRID/frames" "$ERA_HYBRID/contact-vfx-v5.png"
```

The CLI remains `--masters`, `--out`, `--frames`, `--dry-run`, `--bake-only`,
`--prepare`, and optional `--source`. The default source is the sibling `classical`
directory. Only preparation imports Pillow/OpenCV; Blender uses bundled NumPy.
`--dry-run` builds and saves without baking; `--bake-only` bakes all simulation
frames; render ranges reuse the verified bake.

## Validation and review

`prepared.json` records recipe/source/asset hashes, painting crops and CC BY 4.0
provenance. The signature also includes the base builder and Blender version.
Incomplete or stale task-owned caches are rebuilt. Completion requires every
base/noise UNI frame and nonzero density at frames 1, 48, 96 and 144. V5 also checks
that smoke actually extends up the image (at least 8 world units at frame 1 and 12
thereafter), rather than accepting density confined to the emitter. This reads
the noise-grid dimensions explicitly. The bake report records actual seconds and
whether the eight-minute target was met; there is no process-killing watchdog.

Python-only checks passed: syntax, asset preparation, source hashes, unchanged
camera/CLI/socket helper, projected ship size/travel and reflection alignment,
and sampled cloth/camera strain with no folded triangles. Results are in
`masters/hybrid-v5/static-validation.json`. The lead-side scene also checks actual
hull projection and inherited evaluated cloth strain before baking.

**Still requires the lead's Blender run after the fix:** 5.3 API execution, smoke height and
appearance, bake time under 480 seconds, banner cutout registration, shoreline
occlusion, sail/reflection match, and readable motion at 960 wide. Review full
frames and motion, not only enlarged crops. The failed v5 bake's 38.78 seconds
leaves substantial headroom for doubling the substep cap from three to six;
the corrected bake's runtime remains unmeasured.

### Smoke bake diagnosis

Python readback of the failed bake's gzip/MNT3 UNI files reproduces the 2.89-unit
frame-1 noise height. Base XYZ resolution is 33×72×22; noise is 66×144×44.
X is contiguous, so reshaping to ZYX and reducing axes (0,2) correctly measures
Y. Direct SDNA inspection of `cache/baked.blend` confirms an unrotated,
unit-scale domain and enabled scene gravity `(0,-9.81,0)`. The domain's default
`(0,0,-9.81)` fallback was unused; it now explicitly matches the scene.

The 48-frame pre-roll is not the cause: noise height already reached 36.11 units
at frame -24, then collapsed to 2.89 at frame 1 while the base grid still spanned
12.28. Cached velocity components grew from 3.26 at frame -47 to 1,022 at -24 and
1,527 at frame 0, with strong motion on every axis. Heat stayed near 3 and the
inflow remained active. This indicates excessive curl reinforcement at the old
smoke/flame vorticity 2.5/2.0, exhausting the three-substep budget and flushing
the open domain, rather than absent buoyancy or a measurement-axis error.

The fix reduces confinement and wavelet strength and raises the substep cap;
positive density/heat buoyancy (2/3), temperature (2), pulsed +Y inflow (about 6),
pre-roll, domain thickness and the 8/12-unit verification thresholds are retained.
Build and readback now check gravity/orientation and report all three plume spans.
Offline measurements are in `masters/hybrid-v5/failed-bake-diagnosis.json`.

API checks used the installed 5.3 fluid UI and Blender's primary sources:
[fluid RNA](https://github.com/blender/blender/blob/main/source/blender/makesrna/intern/rna_fluid.cc)
for properties, ranges and noise-grid readback, and
[Mantaflow smoke integration](https://github.com/blender/blender/blob/main/intern/mantaflow/intern/strings/smoke_script.h)
for gravity-directed buoyancy. The main branch is a static reference, not runtime
verification of the installed build.
