# Classical harbour: hybrid v8

V8 is a code-only polish pass over the owner's v7 review candidate. The painting
set, camera, galley (including its oars and sail) and seven gulls are preserved.
144 frames at 24 fps; six threads; 960x540 by default, `--full` for 1920x1080.
The lead alone invokes Blender through the existing machine-wide lock.

## Changes

- Smoke: 128 base voxels with 2x Mantaflow noise, up from 96; domain 42x96x28,
  up from 32x88x28, with more room on the right. Wavelet strength 0.85 and spatial
  scale 2.6 add curl without raising the stable vorticity 0.15 / flame vorticity
  0.1. A WIND field points along picture-right, strength 0.65. Stronger pulsed
  density (4.6 ± 1.2), temperature (3.2 ± 0.45), fuel (2.4 times flicker) and
  upward inflow (19 ± 3) feed larger billows. Pre-roll remains -95..0; at most
  six substeps. Four-pixel EEVEE volume tiles retain finer curls at preview size. See the [Blender fluid API](https://docs.blender.org/api/main/bpy.types.FluidDomainSettings.html)
  for the wavelet controls.
- Smoke shader: **density gain stays 0.3**. A density-dependent multiplier
  thins wisps (0.35..1) while retaining denser cores; cores are darker ochre-grey,
  the underside warm, and thin upper smoke lighter. All density remains driven
  by the simulated grid. Side/ceiling feathers remain, with a new floor feather.
  Readback applies the same transfer and feathers. Height misses remain warnings.
- Fire: emitter grows from 2.1x1.4x2 to 2.6x1.6x2; slower fuel burning (0.85
  versus 1.1) and stronger inflow target taller licking tongues. **Flame flicker
  gain stays 5**. Point light and the scholars' reduced 0.24 masked spill are
  unchanged. A seeded pool of 48 emissive spark particles rises, curls right,
  cools and fades. Keyed meshes provide the particle lifecycle without a legacy
  particle API or a second simulation cache; emission follows the flame flicker.
- Water: stronger moving normals, ripple bands and sparse warm ivory glints,
  with soft thresholds to avoid binary sparkle popping. Original water mask,
  shoreline and ship reflection/contact projection remain attached to the paint.
- Banners: top-pinned blue cutouts have roughly twice the free-edge displacement;
  relief cloth, awnings and the galley sail retain their approved motion.
- Oars: larger short splash fans, broken ivory foam rings and 72 ballistic
  droplets follow the existing downstroke. Their origin is the rotated blade tip
  projected to the hull waterline; shoreline occlusion applies to every effect.
- Full resolution: camera, UVs, source-pixel polygons and masks remain in their
  original authoring space. Pixel readbacks/thresholds, brush radius and canvas
  tooth scale by 2. Loading a preview `.blend` for `--full` reapplies these
  settings, so both sizes reuse the same fluid bake. Use separate frame folders.

There is no density/flicker gain retune. Source plates and v7 artifacts remain
untouched; preparation writes to `masters/hybrid-v8`.

## Expected time, not a benchmark

The existing v7 report records 57.34 seconds baking and 103.83 seconds rendering
all 144 preview frames. V8's estimated six-thread budget on the same machine is:

| Output | Bake once | Render 144 frames |
| --- | --- | --- |
| 960x540 | 2–5 minutes (target under 8) | 2–4 minutes |
| 1920x1080 | Same bake; zero additional baking when reused | 6–12 minutes |

Estimates allow for the larger grid, hotter inflow, additional particles and
compositor scaling. Build, cache validation and encoding add overhead. The bake
report measures the 480-second target; it is not a hard timeout. No v8 runtime or
visual result is established until the lead runs Blender. Check flames for
blowout, plume edges/core contrast, scholar colour, glint shimmer and oar contact
in motion, not only stills.

## Exact commands

From the repository root:

```sh
export ERA_HYBRID=/Users/samcorcos/LegatumRuns/era-video-pilot/masters/hybrid-v8
export ERA_PYTHON=/Users/samcorcos/LegatumRuns/era-video-pilot/venv/bin/python
export OMP_NUM_THREADS=6
"$ERA_PYTHON" -m py_compile tools/art/era-video/hybrid/scene.py
"$ERA_PYTHON" tools/art/era-video/hybrid/scene.py \
  --masters "$ERA_HYBRID" --out "$ERA_HYBRID/frames-960" --prepare

# Only invoke this function while the lead holds the existing Blender lock.
# This function does not acquire the lock itself.
hybrid_v8() {
  /opt/homebrew/bin/blender -b --factory-startup --disable-autoexec -t 6 \
    --python-exit-code 1 -P tools/art/era-video/hybrid/scene.py -- \
    --masters "$ERA_HYBRID" "$@"
}
hybrid_v8 --out "$ERA_HYBRID/frames-960" --dry-run
hybrid_v8 --out "$ERA_HYBRID/frames-960" --bake-only
hybrid_v8 --out "$ERA_HYBRID/frames-960" --frames 1-1
hybrid_v8 --out "$ERA_HYBRID/frames-960" --frames 30-30
hybrid_v8 --out "$ERA_HYBRID/frames-960" --frames 100-100
hybrid_v8 --out "$ERA_HYBRID/frames-960" --frames 144-144
# Short motion check, then the full preview after reviewing those frames.
hybrid_v8 --out "$ERA_HYBRID/frames-960" --frames 49-72
hybrid_v8 --out "$ERA_HYBRID/frames-960" --frames 1-144
FRAMES=144 SIZE=960x540 bash tools/art/era-video/encode.sh \
  "$ERA_HYBRID/frames-960" "$ERA_HYBRID/classical-vfx-v8"
FRAMES=144 SIZE=960x540 "$ERA_PYTHON" tools/art/era-video/contact_sheet.py \
  "$ERA_HYBRID/frames-960" "$ERA_HYBRID/contact-vfx-v8.png"

# Reuse that bake: no second preparation or bake is necessary.
hybrid_v8 --full --out "$ERA_HYBRID/frames-1080" --frames 1-144
FRAMES=144 SIZE=1920x1080 bash tools/art/era-video/encode.sh \
  "$ERA_HYBRID/frames-1080" "$ERA_HYBRID/classical-vfx-v8-1080"
FRAMES=144 SIZE=1920x1080 "$ERA_PYTHON" tools/art/era-video/contact_sheet.py \
  "$ERA_HYBRID/frames-1080" "$ERA_HYBRID/contact-vfx-v8-1080.png"
```

## Validation boundary

Python preparation, compilation and static/source consistency checks can run in
this editing session. The prepared manifest hashes every input and generated
asset; `static-validation.json` records the Python checks. Bake completion, live
Blender 5.3 API compatibility, render composition and visual quality are pending
lead verification. No Blender process was launched and no commit was made.
