# Classical harbour: painted VFX v3

144 frames, 24 fps, 960×540 output and internal resolution; Blender 5.3 Eevee,
32 samples, six workers. The v2 camera/lens animation, ship movement and blue Ocean
are retained. No game integration or committed masters.

`paint_textures.py` uses Pillow/numpy to extract eight material patches directly
from `app/src/assets/eras/classical-1920.jpg`: marble, terracotta, quay stone,
foliage, hull timber, sail cloth, rock and blue cloth. It preserves the source
brushwork, feathers tile boundaries, and derives tangent normals, roughness and
height from luminance. The scene uses albedo/normal/roughness maps with rest-space
UVs; maps are packed into the blend. Height maps are also provided for inspection.
All crops, hashes and source attribution are in `textures/manifest.json`.

The sky and two layered mountain cards use the painting itself, with a soft traced
skyline and increasingly blue distance haze. There are no procedural mountain
ridges. The finish uses a radius-6 anisotropic Kuwahara pass at 90%, followed by a
fixed 960×540 canvas weave multiplied at 70%. Bloom is reduced to retain flame
colour. The simple architecture/figures are still the v2 models; visual approval
requires the lead's rendered frames, not a syntax check.

The beacon has a fixed 14×12×34 domain, 80 base voxels on the longest axis, 2×
noise detail, greater buoyancy/vorticity and three seconds of pre-roll (-71..144).
Smoke is non-emissive except where the flame grid drives blackbody-coloured
emission; a volume-only daylight rim and warm underside light reveal its density.
Every fluid object has applied unit scale, closed geometry and nonzero dimensions.
No domain scale animation. The top of the domain vents smoke.

The wake is a seeded particle buffer: births at the stern and immersed oar blades,
world-space drift, lifetime expansion/dissolution, and projection onto the actual
Ocean surface. Geometry Nodes instances share one foam mesh. Absolute shape keys
store positions, so cached scene reloads need no handlers or extra simulation.
This is analytic surface-particle advection, not a liquid solve. The old dashed
ribbons are removed. Oars now have thicker round shafts and solid tapered timber
blades with beveled edges. Cloth remains physically baked.

## Commands

Run from the repository root. **Every Blender invocation, including dry-run and
bake, must be run by the lead inside the existing machine-wide Blender lock.**
The commands below do not acquire that external lock. Do not run them concurrently.
Texture prep and `py_compile` do not invoke Blender and may run directly.

```sh
export ERA_VFX=/Users/samcorcos/LegatumRuns/era-video-pilot/masters/vfx-v3
export ERA_PYTHON=/Users/samcorcos/LegatumRuns/era-video-pilot/venv/bin/python
export OMP_NUM_THREADS=6

"$ERA_PYTHON" tools/art/era-video/harbour/paint_textures.py --out "$ERA_VFX/textures"
python3 -m py_compile tools/art/era-video/harbour/scene.py tools/art/era-video/harbour/paint_textures.py

# Define once; invoke only inside the lead's machine-wide lock.
harbour_v3() {
  /opt/homebrew/bin/blender -b --factory-startup --disable-autoexec -t 6 \
    --python-exit-code 1 -P tools/art/era-video/harbour/scene.py -- \
    --masters "$ERA_VFX" --out "$ERA_VFX/frames" "$@"
}
harbour_v3 --dry-run
harbour_v3 --bake-only

# Review representative stills before committing to the full sequence.
harbour_v3 --frames 1-1
harbour_v3 --frames 87-87
harbour_v3 --frames 144-144
# After the lead's look review:
harbour_v3

FRAMES=144 SIZE=960x540 bash tools/art/era-video/encode.sh \
  "$ERA_VFX/frames" "$ERA_VFX/classical-vfx-v3"
FRAMES=144 SIZE=960x540 "$ERA_PYTHON" tools/art/era-video/contact_sheet.py \
  "$ERA_VFX/frames" "$ERA_VFX/contact-vfx-v3.png"
```

CLI unchanged: `--masters`, `--out`, `--frames`, `--dry-run`, `--bake-only`.
Prep writes textures under the chosen masters directory; it must precede Blender.
Explicit frame ranges overwrite those PNGs; simulation always covers the full shot.
Encode verifies frame count, size and timing and produces both MP4 and WebM.

## Cache and review

`scene.blend` is the pre-bake master. `cache/baked.blend` includes packed cloth
caches and references external Mantaflow files under `cache/fluid/{data,noise}`.
Completion requires base/noise bake flags, files for every simulation frame,
nonzero smoke readback and cloth deformation. Signature includes the scene source,
painting, texture manifest and Blender version. Prep/source or texture changes
invalidate the cache. Missing/changed image files fail explicitly, never fall back
to procedural shaders. Use `cache/baked.blend` for standalone inspection.

The bake target is **2–5 minutes**, below the requested approximately eight-minute
budget. The 144-frame render estimate is **4–8 minutes**, plus build and encoding.
These are unmeasured v3 estimates, based on v2's recorded 22.81-second bake and
approximately 124-second render. The base voxel count remains modest; 2× noise,
longer pre-roll, particle evaluation, UV textures and a stronger compositor add
cost. The lead's bake/render logs are the timing authority.

Read [`../review/vfx-v2-critique.md`](../review/vfx-v2-critique.md) for the visual
verdict and acceptance checks. No Blender invocation was made in the v3 editing
pass. Preparation, image inspection, syntax compilation and static preservation
checks were run; Blender API/runtime, bake timing and final appearance await the lead.

API references used while reading the script:
[gas buoyancy settings](https://docs.blender.org/api/5.1/bpy.types.FluidDomainSettings.html),
[noise scaling](https://docs.blender.org/api/main/bpy.types.FluidDomainSettings.html),
[absolute shape-key evaluation](https://docs.blender.org/api/5.2/bpy.types.Key.html).
