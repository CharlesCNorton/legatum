# Spearman — real-time 0 A.D. adaptation, round 2

`spearman.glb` is the primary asset. The 2D reviews are renders of that GLB.
It contains 2,536 triangles, one skinned mesh, 29 joints, rigid head/helmet/crest,
spear and shield nodes, and one embedded 1024 × 1024 RGB atlas. The figure is
1.853 m tall including its crest, Y-up, metres, facing +Z, feet at the origin.
There are five sampled 30 fps clips: `idle`, `walk`, `attack`, `hit`, `death`.
No normal map, AO texture, baked lighting or emission-projected unit material.

The material `team` covers crest hair, the shield rim and cloak trim. Its atlas
samples are neutral white and its default baseColorFactor is crimson. Replace
that factor / three.js `material.color` for any player's colour. Clone materials
per instance before independently tinting multiple units. The main cloak remains
crimson; the trim changes with the team. Both materials use the same atlas.

The GLB and separate atlas are below 2 MB combined and belong in git. The atlas
is embedded, so runtime loading only needs the GLB. **Keep LICENSE-ART and
PROVENANCE.md with redistributed copies**; their asset-specific CC BY-SA 3.0
terms override the general repository art licence. Credit is also embedded in
`asset.copyright`, `asset.extras` and the root's extras.

## Rebuild

Run from the repository root. Heavy inputs and outputs stay under
`~/LegatumRuns/anim-pilot`. `source-manifest.json` pins the preserved input blend
and all upstream geometry/motion files. Rebuild assumes that local cache exists;
it does not silently download different sources. `dae.py` parses data only.
The original import converter is retained at `oad/import_hoplite.py` with its
round-one import report. Blender 4.5 is unnecessary for rebuilding round two.

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman-0ad/paint_atlas.py tools/art/anim3d/units/spearman-0ad/spearman-albedo.png
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman-0ad/build.py
python3 tools/art/anim3d/validate_glb.py tools/art/anim3d/units/spearman-0ad/spearman.glb
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman-0ad/render.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman-0ad/package.py
```

For a low-cost diagnostic, append `-- --quick` to the render command. The master
is `oad/r2/spearman.blend`; the delivered GLB's material tint metadata is finalized
after Blender export. Treat the GLB as the appearance authority.

The renderer sets 30 fps **before** import. It ignores Blender's hidden bone
shape collection when fitting the camera. Bone-parented rigid objects do not
round-trip correctly through the Blender 5.3 importer in this asset, even with
`bone_heuristic='BLENDER'`. Therefore their transforms are evaluated directly
from the GLB's sampled node hierarchy with linear translation/scale and quaternion
slerp. Skin animation is imported normally. This is a rendering compatibility
step; the renderer makes no new artistic pose corrections. three.js loads the
GLB normally without this step.

Camera: same 13.613° pitch as the existing Spearman game preset, azimuth adjusted
to `(4, -6.265, 1.8)` in Blender so the spear arm remains readable. One orthographic
frame encloses **every** sample of **every** clip, including the entire spear and
fall. The review floor is a shadow catcher composited over cream `#f8f4e8`.

The 2D outputs follow the existing game's rates in `kit/atlas.py` with this
round's requested higher frame counts:

| Clip | Sprite frames | 2D fps | GLB duration | Three-repeat MP4 duration |
| --- | ---: | ---: | ---: | ---: |
| idle | 12 | 4 | 2.000 s | 9 s |
| walk | 16 | 6 | 1.333 s | 8 s |
| attack | 18 | 14 | 1.167 s | 3.857 s |
| hit | 8 | 12 | 0.800 s | 2 s |
| death | 16 | 4 | 1.933 s | 12 s |

These sprite counts and legacy rates change apparent playback speed. The viewer
plays the authoritative 30 fps GLB timing; judge real-time cadence there. The
full-rate attack sheet contains all 36 source samples at their actual timestamps.
No game loader, engine rules or currently shipped sprite assets were changed.

## Viewer and checks

Serve the repository locally (`python3 -m http.server 8765`) and open
`http://localhost:8765/tools/art/anim3d/viewer/index.html`. three.js is pinned to
0.170.0 on jsDelivr; its CDN modules need network access. The viewer has all five
clips, orbit, fixed map pitch, pause and team colour. No build step or hosting.

Run Chromium recording **outside the sandbox**, from the worktree root:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs
```

The task-local Playwright package is 1.56.1; the host needs its Chromium browser
installed. The recorder starts/stops its own loopback server, samples every frame
at 30 fps, repeats each clip three times, encodes H.264/yuv420p and verifies the
stream. Outputs: `~/LegatumRuns/anim-pilot/review/3d-v2/spearman-0ad-r2-<clip>-viewer.mp4`.
It records at 640 × 640 and writes a validation receipt. Chromium was not launched
in this sandbox. The browser page and viewer MP4s still need host verification.

```sh
python3 -m unittest discover -s tools/art/anim3d -p test_validate_glb.py
python3 tools/art/anim3d/kit/check_imports.py
node --check tools/art/anim3d/viewer/viewer.mjs
node --check tools/art/anim3d/viewer/record.mjs
VIEWER_NODE_MODULES="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules" node tools/art/anim3d/viewer/check-runtime.mjs
GLTF_VALIDATOR_MODULE="$HOME/LegatumRuns/anim-pilot/oad/validator/node_modules/gltf-validator" node tools/art/anim3d/viewer/validate-khronos.mjs tools/art/anim3d/units/spearman-0ad/spearman.glb
```

Khronos `gltf-validator` is pinned locally to `2.0.0-dev.3.10`. Optional reinstall:
`npm --cache /tmp/legatum-npm-cache install --prefix "$HOME/LegatumRuns/anim-pilot/oad/validator" gltf-validator@2.0.0-dev.3.10`.
The CPU three.js check tests loading, dimensions, named clips, motion, loop poses,
rigid hierarchy and tint material access; it does not claim browser pixel validation.

The custom validator measures skin bounds, triangles, joints, weights, embedded
image dimensions, transform conventions, actual 30 fps samples and loop endpoint
agreement. It also checks rigid parent names, material use and attribution. Exact
pigment style, team-region coverage and continuous game feel remain visual checks.

Review notes and all encoded movies live in
`~/LegatumRuns/anim-pilot/review/3d-v2/spearman-0ad-note.md`.
