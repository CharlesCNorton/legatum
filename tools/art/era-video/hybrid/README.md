# Classical harbour: hybrid v9

Six painted flame cards replace the brazier's Mantaflow fire/smoke. No fluid
objects, bake, pre-roll, cache or smoke-grid verification remains. `--bake-only`
is retained as a build/save-only compatibility alias. The lead alone runs
Blender through the existing machine-wide lock; editing agents prepare/compile.

The camera, crisp painting, seven gulls, water glints, two blue banners, oar foam,
144 frames at 24 fps, six threads and `--full` framing are retained.

## Changes

- `--prepare` generates six RGBA flame textures from seeded OpenCV pigment
  strokes: deep orange edges, ochre bodies and warm ivory cores. Narrow tapered
  cards curl through pinned-base UV noise and independent shape-key/scale motion.
  They bypass the CG brush blur, with modest additive emission and the existing
  restrained compositor halo. The scholars' 0.24 masked spill and point light stay.
- A pool of 60 sparks has 42–43 visibly alive (alpha above 0.08) on every delivery
  frame. Camera-compensated streaks are 2.4–3.8 px long at 960, twice that at 1080;
  particles rise, drift, cool and fade. Absolute frame timing supports stills and
  out-of-order frame renders without a cache.
- A soft painted plume with shaded lobes rises from source pixel (680,350), on
  the distant right-hand bay headland, with a tiny warm fire point. It uses haze
  colours and local relief depth, with slow drift; there is no foreground smoke.
- The galley keeps its geometry/scale but follows a short offshore path, source
  x=530→480 at y=347, replacing the long crossing through the painted ships.
  The root is lowered 0.903 world units; the water clips the lower keel at local
  z=-0.22, with a matching dark wet band. Reflection begins immediately below
  the contact, and the bow spray and oar foam follow the revised waterline.
- Twelve conservative painted-ship boxes cover the horizon sails, harbour
  boats, large galley and docked craft. Python projects them and a conservative
  full hero-ship box through all 144 frames. The minimum is **3.864 px at 960**
  (**7.728 px at 1080**), at frame 103, against the tiny eastern lateen. This
  includes the camera move and sampled relief depth. `scene-report.json` records
  every frame. The Blender dry-run independently checks evaluated mesh boxes,
  verifies the Python projection against the actual camera, and rejects a
  clearance below three preview pixels. These are geometric checks; the lead
  still reviews the result in motion.

Textures are procedural derivatives in the painting's palette; no downloads.
Original plates and v8 artifacts are untouched. Output is `masters/hybrid-v9`.

## Exact commands

From the repository root:

```sh
export ERA_HYBRID=/Users/samcorcos/LegatumRuns/era-video-pilot/masters/hybrid-v9
export ERA_PYTHON=/Users/samcorcos/LegatumRuns/era-video-pilot/venv/bin/python
"$ERA_PYTHON" -m py_compile tools/art/era-video/hybrid/scene.py
"$ERA_PYTHON" tools/art/era-video/hybrid/scene.py \
  --masters "$ERA_HYBRID" --out "$ERA_HYBRID/frames-960" --prepare

# Lead only, while holding the existing Blender lock. This function does not acquire it.
hybrid_v9() {
  /opt/homebrew/bin/blender -b --factory-startup --disable-autoexec -t 6 \
    --python-exit-code 1 -P tools/art/era-video/hybrid/scene.py -- \
    --masters "$ERA_HYBRID" "$@"
}
hybrid_v9 --out "$ERA_HYBRID/frames-960" --dry-run
# No bake command is needed.
hybrid_v9 --out "$ERA_HYBRID/frames-960" --frames 1-144
hybrid_v9 --full --out "$ERA_HYBRID/frames-1080" --frames 1-144

FRAMES=144 SIZE=960x540 bash tools/art/era-video/encode.sh \
  "$ERA_HYBRID/frames-960" "$ERA_HYBRID/classical-vfx-v9"
FRAMES=144 SIZE=960x540 "$ERA_PYTHON" tools/art/era-video/contact_sheet.py \
  "$ERA_HYBRID/frames-960" "$ERA_HYBRID/contact-vfx-v9.png"
FRAMES=144 SIZE=1920x1080 bash tools/art/era-video/encode.sh \
  "$ERA_HYBRID/frames-1080" "$ERA_HYBRID/classical-vfx-v9-1080"
FRAMES=144 SIZE=1920x1080 "$ERA_PYTHON" tools/art/era-video/contact_sheet.py \
  "$ERA_HYBRID/frames-1080" "$ERA_HYBRID/contact-vfx-v9-1080.png"
```

## Validation boundary

Preparation, compilation, deterministic asset checks, all-frame Python clearance
and spark lifecycle checks ran without Blender. `prepared.json` hashes every
asset; `static-validation.json` records checks. `texture-review.png` is a texture
inspection sheet, not a scene render. Live Blender 5.3 API compatibility, evaluated
mesh clearance and visual quality remain for the lead. No commit was made.
