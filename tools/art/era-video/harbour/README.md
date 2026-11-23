# Classical harbour: painted VFX revision

Six seconds, 144 frames at 24 fps, 960×540, Eevee / 32 samples / six workers.
Requires the installed **Blender 5.3** API. All geometry, motion and effect masks are
procedural. The existing Classical painting supplies only a cropped painted
sky (source pixels x=460–890, y=15–200, top origin) and the pigment palette.
No downloads, text, game integration or committed masters.

The scene contains a modeled quay, limestone headland, Doric temple, houses and
cypresses; a trireme with 24 rowing oars, moving hull and foam wake; an Ocean modifier
with a `foam` vertex attribute; a pinned cloth sail and two pinned banners; a real
64-voxel Mantaflow fire/smoke beacon; 84 geometry-nodes instanced walkers and nine
collection-instanced flapping gulls. The camera follows the enlarged ship, then cranes above the mast and withdraws
to a wide of the harbour and acropolis, settling during the final 18 frames.
Water, smoke, cloth, rowing and crowds continue moving during the camera's settle.

Finishing: soft-banded sunlit pigment materials, screen-space water reflections,
mist-pass depth haze, backdrop-AOV edge light wrap, fire/sun Fog Glow, procedural
lens dirt multiplied by glare, warm colour grade, a radius-4 anisotropic Kuwahara
pass mixed at 78% with the original, and a soft vignette. No shader replaces the smoke
simulation; the material reads density and flame grids, while temperature drives
the gas simulation.

## Commands

Run from the repository root. **The lead runs final Eevee rendering inside the existing render lock.
Dry-run and CPU bake can run in the sandbox; do not render with Metal here.** These commands do not acquire that external lock.

```sh
export ERA_VFX=/Users/samcorcos/LegatumRuns/era-video-pilot/masters/vfx-v2
export ERA_PYTHON=/Users/samcorcos/LegatumRuns/era-video-pilot/venv/bin/python
export OMP_NUM_THREADS=6

# Build only; saves scene.blend and scene-report.json. No bake or render.
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P tools/art/era-video/harbour/scene.py -- \
  --masters "$ERA_VFX" --out "$ERA_VFX/frames" --dry-run

# CPU simulations only, including one second of pre-roll (-23..144).
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P tools/art/era-video/harbour/scene.py -- \
  --masters "$ERA_VFX" --out "$ERA_VFX/frames" --bake-only

# Lead only, under the render lock: bakes if needed, then renders all 144 PNGs.
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
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
axes. No volume scale is animated. The domain is fixed at 9×8×17 units, no expensive
noise upres; cloth uses 18×12 quads each, four solver steps, no self-collision.
The Ocean is evaluated procedurally rather than baked.

The v1 critique and v2 changes, CPU checks and remaining visual limitations are in
[`../review/vfx-v1-critique.md`](../review/vfx-v1-critique.md). V1 masters and its
rendered sequence remain intact; v2 uses `masters/vfx-v2`. The saved production
scene is Eevee. Optional review stills use Cycles CPU plus the CPU compositor and
must not be mistaken for an Eevee approval or a completed 144-frame delivery.

Budget: under about five minutes per CPU bake. Actual final timing and readback
results are recorded in the critique and `scene-report.json`. No commits made.
