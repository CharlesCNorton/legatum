# Classical harbour VFX v2 critique and v3 handoff

Reviewed the supplied six-frame contact sheet and frames 1, 87 and 144 against
`app/src/assets/eras/classical-1920.jpg`. The scene succeeds as a readable animated
harbour but fails the requested oil-painting finish. This is a visual judgment of
v2, not a claim that v3 has passed.

## Keep

- The water-level opening, ship following, crane above the mast and wide reveal.
  The temple remains legible and the composition opens without a cut.
- The ship's scale, path and placement, the waterfront and temple arrangement.
- The blue sea, moving ripples and reflections. These give the scene depth and life.
- Six seconds / 144 frames / 960×540 / six threads and the existing CLI.

## What breaks the painting match

1. **Surfaces are too clean and uniform.** Cream columns, flat red roofs and smooth
   green tree lobes read as manufactured miniatures. The painting has directional
   strokes, broken warm/cool colour inside each material, rough edge transitions
   and richly varied shadow masses. V2's elongated noise and normal-facing value
   ramp do not supply that information. Radius-4 Kuwahara smooths the simplified
   geometry without making its surfaces convincingly painted.
2. **The fire is a clipped white light shape.** In all three supplied full frames,
   the beacon's white centre dominates; the smoke is a small dark patch near the
   stoa roof. There is no substantial sunlit column reaching into the sky. A
   nonempty density-grid check alone could never establish that visual success.
3. **The wake is graphic punctuation.** Two strings of evenly spaced pale marks
   look like a navigation guide. They travel with the hull instead of leaving a
   broad, irregular field of decaying churn. The oars do not visibly disturb it.
4. **The distant landscape is a stack of cartoon silhouettes.** Smooth repeated
   peaks and nearly flat blue fills flatten the setting. The reference has rocky
   structure and atmospheric separation within the mountains themselves.
5. **Oars resemble thin slats.** Their repeated bright tips read as a comb in the
   wide views. Thicker shafts, broad tapered timber blades and local foam should
   make them read as working paddles.

The remaining simplified house silhouettes, repeated round crowns and sparse
human figures are also scale cues. V3 preserves this shot and its principal
geometry as instructed; a material/compositor pass cannot be assumed to erase
all those cues. The frame-grab comparison remains the acceptance test.

## Changes implemented for v3

- Added `harbour/paint_textures.py`, run with the supplied venv. Eight real painting
  patches supply albedo, normals, roughness and optional height maps. Rejected the
  first mirrored tile attempt after inspecting its kaleidoscopic patterns; final
  tiles feather only their boundaries. Foliage/timber crops were narrowed to
  exclude unrelated architecture/rigging. No new generated illustration or download.
- Removed the procedural grouped-value material shader. Stable metre-based UVs
  attach sampled pigment and tangent normals to the surfaces, including the cloth.
  Rock and sail now have distinct source patches instead of sharing quay/marble.
- Radius-6 anisotropic Kuwahara, 90% blend; canvas weave after the oil pass; reduced
  glare and protected the painted sky from the global foreground haze.
- Taller 14×12×34 gas domain, 80 base voxels, 2× noise, larger emitter, greater heat,
  initial upward velocity, buoyancy and vorticity, less crosswind and a 72-frame
  pre-roll. Lighter smoke albedo/lower optical density plus daylight volume rim.
  Temperature drives a Blackbody shader; flame density gates its emission.
- Deleted both dashed wake ribbons and hull-parented flecks. Added seeded
  world-space surface particles from the stern and immersed oar tips, with drift,
  finite lifetimes, an Ocean projection and shared Geometry Nodes instances.
  Their stored position keys survive `.blend` reload without Python handlers.
- Replaced sine-wave mountain meshes with two layers of the painting's mountain
  region, a traced soft skyline and different blue haze strengths.
- Thicker oar shafts, solid tapered timber blades, bevels and modeled shoulders.

## Verified without Blender

- Ran the texture preparation script and inspected its contact sheet and mountain
  alpha against a coordinate grid. Images and manifest live in `masters/vfx-v3/textures`.
- Ran `python3 -m py_compile` on both Python files.
- Verified all 36 generated image hashes, all eight normal fields' unit lengths,
  matching albedo tile edges, roughness bounds, canvas size and mountain alpha.
  `git diff --check` passed.
- Compared ASTs against the repository's v2 source: `sea()` and `lights_camera()`
  are unchanged, as are all six ship movement drivers. The longer pre-roll only
  extends the existing camera's initial pose before delivery starts.
- Read the shader wiring, particle lifetime/birth transforms, cache invalidation,
  noise-file coverage and thick, unanimated fluid-object guards.
- **No Blender process was started: no dry-run, bake, CPU still or render.**
  Runtime node/socket compatibility and visual performance are not yet verified.

## Lead review

Run every Blender command through the machine-wide lock, starting with dry-run,
then bake and frames 1, 87 and 144. Exact commands are in
[`../harbour/README.md`](../harbour/README.md#commands).

At native 960×540, compare those frames directly with the era painting. Check that
pigment direction survives the oil filter; stone has colour variation without
looking like tiled wallpaper; canvas is subtle rather than a screen-door pattern;
smoke billows well above the beacon with lit edges, without hitting a flat domain
ceiling; flame retains orange/yellow structure; wake spreads and fades in world
space; oar foam occurs on the immersed stroke; mountain edges have no card seams.
Then check short motion ranges for texture/normal shimmer and particle popping.

Estimated v3 bake: **2–5 minutes**, target under about eight minutes at six threads.
Estimated 144-frame Eevee render: **4–8 minutes**, excluding build/encoding. These
are estimates, not measurements. V2's local scene report records 22.81 seconds for
baking; its render log ends at approximately 124 seconds. Report v3 timing only
after the lead's locked run. No commits were made.
