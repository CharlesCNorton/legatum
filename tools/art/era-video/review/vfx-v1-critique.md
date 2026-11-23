# Harbour VFX v1: critique and correction pass

Reviewed the supplied v1 contact sheet, frames 30 / 58 / 87 and
`app/src/assets/eras/classical-1280.jpg`. The lead's rejection is justified: motion
exists, but the painting's hierarchy, surface treatment and atmosphere do not.
The painting combines warm carved stone, deep blue water, densely inhabited terraces,
layered mountains and a substantial foreground. A large primitive temple over a
plain mound cannot carry that look, even with a finishing filter.

## What failed and what changed

| V1 evidence / cause | Change in `harbour/scene.py` |
| --- | --- |
| Pale water dominates frames 1–58. Foam was interpolated into the entire base-colour range, with a white endpoint at only 0.55. | Independent deep blue/teal water pigment. Foam coverage reduced; a clamped 0.72–0.96 crest mask is multiplied by ripple noise. IOR 1.333 and low roughness retain dielectric Fresnel reflections; physical sky, small ripple normals and a specular-only sun accent provide reflection/glint structure. Thin, broken wake strokes and smaller flecks follow the actual ocean with Shrinkwrap. |
| Fire reads as an orange ball; smoke has little mass or separation. | Larger 2.1 × 1.8 × 1.1 source, density 2.8, temperature 2.2, upward velocity 2.3, more combustion smoke/vorticity. Fixed 9 × 8 × 17 domain, 64 cells on the longest axis, no noise upres. Actual flame-grid emission is cubed and attenuated with height so upper smoke stays non-emissive; density rises above the open flame base. Warm point/underside area lights and stronger Fog Glow. No emissive sphere substitute. |
| Flat materials, grey illumination and practically invisible finishing. The old diffuse → Shader-to-RGB → emission path coloured brightness bands without surface texture or physical roughness. | Principled pigment materials with object-space elongated noise in albedo, roughness and bump; a soft normal-based pigment ramp retains colour grouping while real lights cast shadows. Warm sun at about 30° elevation, large cool fill, contact shadows, AgX Medium High Contrast, restrained exposure, warm grade and depth haze. Kuwahara changes from radius 2 / 45% mix to radius 4 / 78% mix at 960 × 540. |
| Ship becomes a sail occlusion, then disappears into a temple close-up. | Ship enlarged 1.35×, turned for a three-quarter view, hull bevels and strakes added, sail shortened. Hermite camera follows for the first portion, then rises above mast height while withdrawing. Lens eases from 32 to 27 mm. Final 18 frames settle on a harbour/acropolis wide with zero endpoint path velocity; all environmental animation continues. |
| Temple is a box on a faceted cone; roofs/houses do not establish a city. | Layered irregular limestone outcrop, eroded buttresses, ashlar retaining-wall courses, a terrace and 24 stair treads. Temple capitals, tympana, cornices, triglyphs, relief silhouettes and roof tile ridges. Coastal neighbourhoods of pitched-roof houses, a harbour stoa, olive trees, cargo and a waterfront that continues beyond the wide. Cypress silhouettes are softened and displaced. |
| Hard white sun disc and stretched painted mountain card. | Removed the sun sphere. The painting supplies only a sky crop, with a crop/card aspect ratio much closer to the original. Three real relief meshes supply mountain depth and parallax; distance haze separates the layers. The world sky supplies reflection lighting rather than using the painted card as the entire environment. |

## Skills applied

- `blender-rendering`: installed-API checks, Eevee reflections/AO/volumes, colour management, CPU compositor and low-cost CPU preview/readback.
- `blender-lighting`: aimed warm key, cool fill, practical smoke lighting, soft shadows and a specular-only glint accent.
- `blender-materials`: Principled dielectric water, IOR/roughness, procedural pigment, bump and actual flame-grid volume emission.
- `blender-cameras`: subject extent checks, three depth layers, widening crane and composed endpoint.
- `blender-animation`: continuous Hermite movement/easing, retained oar/cloth/bird motion and endpoint settle.
- `blender-modeling`: bevelled hull, smooth rounded forms, architectural detail, irregular terrain and repeating masonry.
- Repository `legatum-art`: premium painted direction and rejection of the mobile-game diorama look.

Recipes were adapted to installed Blender 5.3, not copied blindly. Its sky node uses
`MULTIPLE_SCATTERING` / `aerosol_density`, replacing the older recipe's
`NISHITA` / `dust_density`. The compositor remains the existing 5.3 node-group API.

## Validation and limits

Outputs are in `masters/vfx-v2`; v1 images/video/cache are preserved. Delivery remains
144 frames, 24 fps, 960 × 540, six render threads and six OpenMP workers. Eevee
samples rise from 12 to 32, with 64 volume samples and volume shadows. Final Eevee
speed must therefore be measured again; v1's 1–2 seconds/frame is not a v2 measurement.

Final `--dry-run` and `--bake-only` both exited 0. The final CPU bake took
**22.81 seconds** (fluid plus all three cloth caches), well inside five minutes.
The scene contains 1,060 objects. Fluid checks enforce applied unit scale, nonzero
thickness on every axis, and no domain/emitter animation. The cache manifest
covers every simulation frame from -23 through 144.

A separate Blender process reopened `cache/baked.blend`: sampled smoke maxima
were 2.75–2.78 and flame maxima 0.975–0.977, with 2,024–4,498 density samples above
0.05 at frames 1, 48, 96 and 144. Between 0 and 0.78% of evaluated viewport ocean
attribute samples passed the 0.72 crest threshold; this is a geometry diagnostic,
not a rendered-pixel coverage measurement. Packed cloth deformation is recorded
in `cache-validation.json`. Run logs and reproducible CPU review scripts are saved
under `masters/vfx-v2/logs/` and `masters/vfx-v2/cpu-review/`. `git diff --check` passed.

CPU previews use Cycles with 20 samples, six threads and the CPU compositor. They
are look/composition checks, not final Eevee frames: direct light, indirect fill,
reflections and volumes can differ. The three 960 × 540 stills (30 / 87 / 144) were inspected. A 12-frame CPU
preview (48–59) was also encoded and its motion contact sheet inspected; ffprobe
verified 480 × 270, 24 fps, 12 frames and 0.5 seconds. This small diagnostic is
separate from the unchanged full-resolution delivery settings. No Metal rendering
or full animation render was performed. The saved production scene remains Eevee.

CPU review exposed hull clipping during the crane, over-emissive upper smoke,
and a visible sky-card/ground-slab edge in the final wide; all were revised. Seven projected framing checks cover frames
1, 30, 58, 87, 115, 126 and 144. The revised hull bounds remain within the frame;
the sail's projected bounding rectangle stays below 5% of image area. The final
temple roof spans about 20% of image width, with the waterfront and ship still
present, rather than filling the image with a close-up.

This pass is visibly more textured and spatially layered in CPU previews, but it
is not yet an approved match to the painting. The figures, hull and city still
have procedural simplifications; the reference has substantially richer carved
architecture, vegetation and inhabited foreground detail. The lead should judge
the final Eevee contact sheet and a short motion preview for reflection stability,
flame/smoke separation, wake contact and temporal brush shimmer before approval.

## Commands

Run from the repository root. The interface and delivery settings are unchanged;
only the masters destination is new to preserve v1. `--disable-autoexec` is explicit.
The lead retains the external lock for final Eevee rendering.

```sh
export ERA_VFX=/Users/samcorcos/LegatumRuns/era-video-pilot/masters/vfx-v2
export OMP_NUM_THREADS=6

blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P tools/art/era-video/harbour/scene.py -- \
  --masters "$ERA_VFX" --out "$ERA_VFX/frames" --dry-run

blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P tools/art/era-video/harbour/scene.py -- \
  --masters "$ERA_VFX" --out "$ERA_VFX/frames" --bake-only

# Lead, under the existing render lock:
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P tools/art/era-video/harbour/scene.py -- \
  --masters "$ERA_VFX" --out "$ERA_VFX/frames"

FRAMES=144 SIZE=960x540 bash tools/art/era-video/encode.sh \
  "$ERA_VFX/frames" "$ERA_VFX/classical-vfx-v2"
```

CPU review reproduction (does not modify the saved Eevee scene):

```sh
blender -b --disable-autoexec "$ERA_VFX/cache/baked.blend" \
  --python-exit-code 1 -P "$ERA_VFX/cpu-review/check.py"
```

Nothing was committed.
