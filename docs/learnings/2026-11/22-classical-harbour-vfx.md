# Classical harbour VFX pilot

The owner rejected the Classical camera-drift clip as "just a still image". The
replacement test lives in `tools/art/era-video/harbour/`: real procedural geometry,
Ocean foam, rowing, simulated cloth and Mantaflow smoke, instanced walkers/gulls,
and a substantial camera crane. The painting supplies only a sky/mountain crop.

Blender 5.3 findings from a non-rendering build and CPU bake:

- Eevee does not expose the object-index pass needed by the initial light-wrap
  graph. A named VALUE shader AOV on the backdrop provides the mask instead.
- The compositor uses shared shader Math/Mix nodes and a node-group output;
  several pre-5.3 compositor node identifiers no longer exist. This pilot
  explicitly requires the installed 5.3 API.
- A cloth bake can report success and write `.bphys` files while a subsequently
  reopened scene still evaluates the rest mesh. This occurred with the pilot's
  named disk caches. Packing its small cloth caches into `cache/baked.blend`
  restored deformation after reload. Verify evaluated local-space vertices at
  several frames, not only `is_baked` or file presence.
- Mantaflow negative pre-roll frames use suffixes such as `_-0023.uni`, whereas
  Python's `f'{-23:04d}'` yields `-023`. Cache validation must handle the sign.
- All fluid objects have applied scale and real thickness on all three axes;
  the domain is never scaled to zero. CPU baking succeeded inside this sandbox.

No scene frames were rendered. Synthetic moving-rectangle fixtures verified the
144-frame / 960×540 override and the unchanged 168-frame / 1920×1080 encode defaults
with actual H.264/VP9 ffprobe readback. They are not visual evidence for the scene.
