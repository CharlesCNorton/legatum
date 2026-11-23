# Classical harbour: rough 3D VFX test

Six seconds, 144 frames at 24 fps, 960×540, Eevee / 12 samples / six workers.
Requires the installed **Blender 5.3** API. All geometry, motion and effect masks are
procedural. The existing Classical painting supplies only a cropped sky/far-mountain
card (source pixels x=460–890, y=15–340, top origin) and the pigment palette.
No downloads, text, game integration or committed masters.

The scene contains a modeled quay, limestone headland, Doric temple, houses and
cypresses; a trireme with 24 rowing oars, moving hull and foam wake; an Ocean modifier
with a `foam` vertex attribute; a pinned cloth sail and two pinned banners; a real
48-voxel Mantaflow fire/smoke beacon; 42 geometry-nodes instanced walkers and nine
collection-instanced flapping gulls. The camera travels from water level past the
ship and cranes toward the temple, easing to rest during the final 18 frames.
Water, smoke, cloth, rowing and crowds continue moving during the camera's settle.

Finishing: soft-banded sunlit pigment materials, screen-space water reflections,
mist-pass depth haze, backdrop-AOV edge light wrap, fire/sun Fog Glow, procedural
lens dirt multiplied by glare, warm colour grade, a small anisotropic Kuwahara
pass mixed with the original, and a soft vignette. No shader replaces the smoke
simulation; the domain uses actual density, temperature and flame grids.

## Commands

Run from the repository root. **The lead runs bake/render outside the sandbox,
inside the lead's existing lock.** These commands do not acquire that external lock.

```sh
export ERA_VFX=/Users/samcorcos/LegatumRuns/era-video-pilot/masters/vfx
export ERA_PYTHON=/Users/samcorcos/LegatumRuns/era-video-pilot/venv/bin/python
export OMP_NUM_THREADS=6

# Build only; saves scene.blend and scene-report.json. No bake or render.
blender -b --factory-startup --python-exit-code 1 \
  -P tools/art/era-video/harbour/scene.py -- \
  --masters "$ERA_VFX" --out "$ERA_VFX/frames" --dry-run

# CPU simulations only, including one second of pre-roll (-23..144).
blender -b --factory-startup --python-exit-code 1 \
  -P tools/art/era-video/harbour/scene.py -- \
  --masters "$ERA_VFX" --out "$ERA_VFX/frames" --bake-only

# Lead only, under the render lock: bakes if needed, then renders all 144 PNGs.
blender -b --factory-startup --python-exit-code 1 \
  -P tools/art/era-video/harbour/scene.py -- \
  --masters "$ERA_VFX" --out "$ERA_VFX/frames"

# Add --frames 1-12 for a short motion check; 72-84 / 126-144 for later checks.
# Explicit ranges overwrite only those PNGs; simulation always covers the full shot.
FRAMES=144 SIZE=960x540 bash tools/art/era-video/encode.sh \
  "$ERA_VFX/frames" "$ERA_VFX/classical-harbour"
FRAMES=144 SIZE=960x540 "$ERA_PYTHON" tools/art/era-video/contact_sheet.py \
  "$ERA_VFX/frames" "$ERA_VFX/contact-sheet.png"
```

`encode.sh` still defaults to 168 / 1920×1080 without overrides. Contact sheets
retain contiguous-preview support when overrides are omitted; with `FRAMES` set
they require the complete sequence. Output names are `frame_0001.png` onward.

## Cache and limits

`scene.blend` is the pre-bake master. `cache/baked.blend` is the canonical scene
for rendering, with fluid files in `cache/fluid/` and the small cloth point caches packed
inside `cache/baked.blend`. No external cloth-file lookup is needed.
The builder validates the completion manifest (script + painting + Blender version,
file sizes and presence); missing/stale/incomplete caches trigger a fresh bake.
A bake exception never writes a completion marker. To force a fresh bake, remove
only `cache/complete.json` and rerun `--bake-only`. Do not open the pre-bake master
and expect cached cloth; use `cache/baked.blend` after a successful bake.

All fluid geometry is closed, has applied unit scale and nonzero thickness on all
axes. No volume scale is animated. The domain is fixed at 6×6×11 units, no expensive
noise upres; cloth uses 18×12 quads each, four solver steps, no self-collision.
The Ocean is evaluated procedurally rather than baked.

Weakest parts: rough hull/architecture and crowd silhouettes; stylized ribbon wake
rather than a hydrodynamic solve; sail has no mast/hull collision; a stretched
skyline crop; low-resolution smoke; synchronized phases within each gull/figure
variant. The painterly finish, framing, motion and reflections need visual review
by the lead. **Under 4 s/frame and under 10 min/bake are targets; actual bake results are recorded below.** No rendered frames have been inspected or produced in the sandbox.

Verified in the sandbox (2026-11-22): the final `--dry-run` passed; the CPU bake
completed in **11.83 seconds**; a separate process reopened `cache/baked.blend`
and verified moving cloth vertices, nonzero smoke density and the Ocean foam
attribute at frames 1, 48, 96 and 144. `cache-validation.json` records the readback.
Synthetic moving-rectangle fixtures passed H.264/VP9 frame-count, size and rate
checks for both 144/960×540 and 168/1920×1080, plus both contact sheets. These are
codec tests, not scene renders. No scene PNGs were rendered, and nothing was committed.
