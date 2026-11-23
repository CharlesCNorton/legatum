# Classical harbour: hybrid v4

The painting is the set. `scene.py` imports the projection, edge-aware depth mesh,
inpainted backplate and deformation checks from `../build_scene.py`. It does not
rebuild the city from primitives or apply an oil filter to the whole painting.
Delivery is 144 PNGs, 24 fps, six seconds, **960×540 internally and externally**,
Eevee with 32 samples and six render/OpenMP workers. No game integration.

## What moves

- **Camera:** a real 16% forward dolly, drifting 12 units right and 11 up toward
  the acropolis, at a fixed focal length. About 19% enlargement by the end;
  0.75-second acceleration and final 0.75-second deceleration. The eight-unit
  relief keeps camera-only principal stretches between 0.925 and 1.077, with no
  folded triangles. This is restrained 2.5D parallax, not an orbit around unseen
  sides of buildings. Motion of water, ships and smoke continues through the settle.
- **Harbour water:** a separate depth-fitted, tessellated surface covers the
  original water mask. Rest UVs project the painting's water pigment onto it;
  animated noise drives real bump normals and warm reflected glints. A thin,
  interrupted V wake and subtle contact tone follow the boat. No white foam
  particles, replacement cyan colour or water simulation. The painted water
  underneath is the feather-edge fallback; shorelines and painted vessels stay
  fixed. This uses the requested normal-mapped surface option, not Ocean.
- **One sailing galley:** a small rounded hull, keel, deck, mast and stays in open
  water above the original ships. It traverses source pixels (470,407) to
  (550,407), with slight roll; a billowed shape-key sail and eighteen separate
  round-shaft oars with thick blades move independently. Linen and hull textures
  are actual painting crops. Existing painted vessels are retained; no inpainting
  of ships is needed. The new boat is deliberately harbour-scale, about 38 output
  pixels long before the push, rather than the oversized v3 hero boat.
- **Foreground brazier:** a closed Mantaflow fire/smoke inflow at source pixel
  (365,676), with flame-grid-gated blackbody emission, warm flickering light and
  non-emissive billowing smoke. One fixed **10×24×10** domain, **64 base voxels** on
  its longest axis, **2× noise**, and two seconds of pre-roll (-47..144).
  All fluid scales are applied and never animated; every axis has real thickness.
  Picture-up is +Y, so scene gravity points -Y. The plume fades before its open
  ceiling. A custom Eevee volume range follows the shallow set's distance over
  the whole shot, avoiding coarse sampling across hundreds of empty units.
- **Cloth:** the original conservative cloth mask deforms the painted sails and
  right blue banners in place; preparation adds the right awning interior. The
  inherited two shape modes keep silhouettes, poles and building edges pinned.
  This selects the permitted painted-cloth displacement option; there is no
  additional cloth-simulation bake.
- **Five gulls:** shared tapered wing meshes, asynchronous flapping and world-space
  travel across the sky. Small warm charcoal strokes. Optional walkers are skipped.

The original image uses an unlit emission material and Standard colour management
so its pigments stay intact. Warm upper-left sunlight and cool ambient fill shade
CG. A shader AOV restricts the warm grade, radius-2 Kuwahara at 25%, and faint
canvas grain to CG surfaces. Smoke remains naturally soft without Kuwahara.
Restrained HDR glare handles fire and any bright sun glints; no global blur,
contrast grade or grain is applied to the painting.

## Preparation and commands

Run from the repository root. **The lead must run every Blender invocation,
including `--dry-run`, through the existing machine-wide Blender lock.** The
function below does not acquire that lock. Do not invoke it concurrently.
Python preparation and syntax checks can run directly.

```sh
export ERA_HYBRID=/Users/samcorcos/LegatumRuns/era-video-pilot/masters/hybrid
export ERA_PYTHON=/Users/samcorcos/LegatumRuns/era-video-pilot/venv/bin/python
export OMP_NUM_THREADS=6

# Already prepared in this editing pass; rerun after changing scene.py or inputs.
"$ERA_PYTHON" tools/art/era-video/hybrid/scene.py \
  --masters "$ERA_HYBRID" --out "$ERA_HYBRID/frames" --prepare
python3 -m py_compile tools/art/era-video/hybrid/scene.py

# Define once; call only while the lead holds the machine-wide Blender lock.
hybrid_v4() {
  /opt/homebrew/bin/blender -b --factory-startup --disable-autoexec -t 6 \
    --python-exit-code 1 -P tools/art/era-video/hybrid/scene.py -- \
    --masters "$ERA_HYBRID" --out "$ERA_HYBRID/frames" "$@"
}
hybrid_v4 --dry-run
hybrid_v4 --bake-only

# Review stills before spending time on the full sequence.
hybrid_v4 --frames 1-1
hybrid_v4 --frames 73-73
hybrid_v4 --frames 144-144
# Following visual review:
hybrid_v4 --frames 1-144

FRAMES=144 SIZE=960x540 bash tools/art/era-video/encode.sh \
  "$ERA_HYBRID/frames" "$ERA_HYBRID/classical-hybrid-v4"
FRAMES=144 SIZE=960x540 "$ERA_PYTHON" tools/art/era-video/contact_sheet.py \
  "$ERA_HYBRID/frames" "$ERA_HYBRID/contact-hybrid-v4.png"
```

The existing CLI shape is retained: `--masters`, `--out`, `--frames`, `--dry-run`,
`--bake-only`. `--prepare` is a Python-only extra and imports neither `bpy` nor
Blender. `--source` optionally selects existing Classical plates; its default is
`--masters`'s sibling `classical` directory. Existing `depth.py` and `plates.py`
outputs are reused without rerunning depth inference or altering the originals.
Preparation needs the provided venv's NumPy, Pillow and OpenCV; Blender uses its
bundled NumPy only. Blender 5.3 is required for the compositor node API.

`--dry-run` builds, checks and saves `scene.blend`, without baking or rendering.
`--bake-only` bakes the whole simulation range regardless of `--frames` and writes
`cache/baked.blend`. A render reuses a valid bake or builds and bakes first. Frame
ranges use global shot numbering and overwrite only the requested PNGs, so missing
ranges can be rendered independently. No Python handlers or custom drivers are
needed when reopening the baked scene.

## Files, cache, timing and review

`plates/` holds copies of the existing depth and inpainted background plus the
expanded cloth mask. `textures/` holds hull, sail and canvas crops.
`prepared.json` records input/output hashes, crop coordinates and source licence
(existing Legatum art, CC BY 4.0; see `LICENSE-ART`). Derived assets and caches stay
outside git. The original painting and Classical master directory are untouched.

The cache signature includes this script, the reused depth builder, every prepared
asset hash and the Blender version. Changes require preparation again as needed
and invalidate the simulation. A completion marker requires successful base/noise
bake flags, nonempty files for **every** simulation frame and nonzero smoke density
readback at frames 1, 48, 96 and 144. Incomplete caches are rebuilt. The only cache
folder removed during a rebuild is this task's `--masters/cache/fluid` directory.
The bake is saved separately from the editable pre-bake master; take the external
`cache/fluid` folder with `cache/baked.blend` when moving it.

**Unmeasured estimates:** 2–6 minutes for the smoke bake (target under eight minutes),
4–10 minutes for all 144 frames, plus build and encoding. The small fixed domain
and absence of Ocean/cloth solves keep the budget bounded, but wall time still
needs measurement on the lead's machine. `scene-report.json` records actual bake
seconds, whether the eight-minute target was met, render range and render seconds.
There is no background watchdog that terminates the lead's Blender process.

Verified without Blender in this editing pass: `py_compile`, reproducible asset
preparation and hashes, source crop/placement inspection, camera endpoint/easing,
and seven numerical samples of the inherited projection with the new cloth
amplitude. No folds; combined cloth/camera principal stretches were 0.865–1.139
(within the builder's 0.75–1.25 animated-deformation bound). The preparation and
numerical report are in the hybrid masters; `static-validation.json` is a record
of this editing pass, not a substitute for the Blender build's evaluated checks.

**Not verified:** Blender execution/API compatibility, actual Mantaflow buoyancy,
bake/render timing, volume appearance, mask registration during the move, CG
occlusion or final visual quality. No Blender process was launched. Before full
rendering, review the first/middle/last stills for crisp architecture, water-edge
registration, hull contact, visible thin oars, upright opaque smoke rather than a
pink halo, and pinned banner/awning edges. Inspect a short motion range for flicker
and the final camera settle. A successful bake is not visual acceptance.

API references consulted alongside the existing 5.3 harbour code and installed
Blender UI source: [Mantaflow domain settings](https://docs.blender.org/api/5.2/bpy.types.FluidDomainSettings.html).
