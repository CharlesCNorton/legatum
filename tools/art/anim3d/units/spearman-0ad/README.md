# Spearman — real-time 0 A.D. adaptation, round 3

`spearman.glb` is the primary asset; all sprite reviews render this exact file.
It has **2,536 triangles, 30 joints, one skinned mesh, one indexed primitive and
one material**. Figure height including crest: **1.8528 m**. Metres, Y-up, +Z
forward, feet centred at the origin. One embedded **1024 × 1024** RGB albedo
atlas; no normal map, AO, baked illumination or emission projection.

Five clips are sampled at 30 fps: `idle`, `walk`, `attack`, `hit`, `death`.
Idle and walk close their loop poses. The skeleton root never translates.
The GLB plus separate atlas is below 2 MB and belongs in git. Masters, input
assets, frames and receipts remain under `~/LegatumRuns/anim-pilot/oad/`.

## One draw call and team colour

Every prop is part of the same skinned primitive. Spear vertices carry one unit
weight to `weapon_R`, shield vertices to `shield_arm`, helmet and crest vertices
to `helmet` (an identity socket under `head`). These parts remain rigid.
`mesh.extras.vertex_regions` records vertex ranges, part names and attachments
so the validator can inspect actual weights rather than trust a label.

**`COLOR_0.r` is the team weight, not visible RGB colour.** Green/blue are zero;
alpha is one. Crest, shield rim and cloak trim have red=1; all other vertices
have red=0. Their atlas samples are neutral white. The runtime shader must
replace standard vertex-colour multiplication with:

```glsl
diffuseColor.rgb *= mix(vec3(1.0), teamColorLinear, vColor.r);
```

Default team colour is sRGB `#a52627` (convert to linear before shading).
`asset.extras.team` and `material.extras.team` describe this contract.
`viewer/team-mask.mjs` demonstrates three.js integration without another material
or draw call. A generic glTF viewer that multiplies RGB vertex colours will show
black/non-team and red/team regions; that is not the intended shader.
Clone materials per independently tinted instance. The cloak's main field stays
crimson; its trim changes with the player.

## Motion and pigment

Native `attack_melee_05`, with the whole stance turned 22° to expose the thrust
at the review camera. Projected spear-tip lateral travel is about 0.89 m versus
0.58 m before the turn. The figure still faces +Z in its idle/locomotion basis.

Native `death_b` has a small head relaxation, an eased finish and four final held
frames. The body rests on the ground instead of hanging from the crest. A
post-export clearance envelope checks quarter-frame interpolation and adjusts
hip height at enclosing 30 fps keys. No skeleton-root motion or prop deformation.
`check_motion.py` independently checks ground clearance at 120 fps; it is not a
mesh/mesh collision solver or aesthetic approval.

The flat albedo adds bronze cuirass and greave ornament, linen seams and dyed hem
stripes to the existing Corinthian helmet, crimson cloak/crest and sunburst aspis.
No original 0 A.D. textures are used. This remains a low-poly pigment pass rather
than finished painterly hero art.

## Rebuild

From the repository root, with the preserved local inputs in `source-manifest.json`:

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman-0ad/paint_atlas.py tools/art/anim3d/units/spearman-0ad/spearman-albedo.png
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman-0ad/build.py
python3 tools/art/anim3d/validate_glb.py tools/art/anim3d/units/spearman-0ad/spearman.glb
python3 tools/art/anim3d/units/spearman-0ad/check_motion.py tools/art/anim3d/units/spearman-0ad/spearman.glb
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman-0ad/render.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman-0ad/package.py
```

`build.py` loads the preserved round-one master, authors separate rigid props,
exports, calls `merge.py` to transform all vertices into the shared bind space,
then calls `clearance.py`. `oad/r3/spearman.blend` is an authoring intermediate;
the finalized GLB is the appearance/motion authority. Blender 4.5 is unnecessary.
The delivered single skin imports into Blender 5.3 normally; no separate prop
transform workaround remains. The renderer reconstructs the mask-aware lit
material and fits one camera across all frames of all clips. `-- --quick` makes
four diagnostic poses per clip at 320 px. Game pitch: 13.613°; no per-frame fitting.

| Clip | Sprite frames | Game fps | GLB duration | Three-repeat sprite video |
| --- | ---: | ---: | ---: | ---: |
| idle | 12 | 4 | 2.000 s | 9 s |
| walk | 16 | 6 | 1.333 s | 8 s |
| attack | 18 | 14 | 1.167 s | 3.857 s |
| hit | 8 | 12 | 0.800 s | 2 s |
| death | 16 | 4 | 2.067 s | 12 s |

The legacy sprite rates alter apparent speed. Judge real-time cadence in the
viewer. All five `spearman-0ad-r3-<clip>-160.mp4` files and the 36-frame
`spearman-0ad-r3-attack-fullrate.png` live under
`~/LegatumRuns/anim-pilot/review/3d-v2/`. MP4s use H.264/yuv420p and cream background.

## Viewer and verification

Serve the repo with `python3 -m http.server 8765`, then open
`http://localhost:8765/tools/art/anim3d/viewer/index.html`. No build step; three.js
is pinned to 0.170.0 on jsDelivr. Clip selector, orbit, fixed map camera and team
colour are available. This is a local review page, not a deployment.

Run the recorder **outside the sandbox**, from this worktree root:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs
```

It starts/stops a loopback server, samples exact 30 fps frames, makes three-repeat
640 × 640 videos, and verifies streams with ffprobe. Outputs:
`~/LegatumRuns/anim-pilot/review/3d-v2/spearman-0ad-r3-<clip>-viewer.mp4`.
Host Playwright 1.56.1 needs its Chromium browser installed. Chromium is not
launched in this sandbox; CPU checks do not establish browser pixel correctness.

```sh
python3 -m unittest discover -s tools/art/anim3d -p test_validate_glb.py
python3 tools/art/anim3d/kit/check_imports.py
node --check tools/art/anim3d/viewer/viewer.mjs
node --check tools/art/anim3d/viewer/team-mask.mjs
node --check tools/art/anim3d/viewer/record.mjs
VIEWER_NODE_MODULES="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules" node tools/art/anim3d/viewer/check-runtime.mjs
GLTF_VALIDATOR_MODULE="$HOME/LegatumRuns/anim-pilot/oad/validator/node_modules/gltf-validator" node tools/art/anim3d/viewer/validate-khronos.mjs tools/art/anim3d/units/spearman-0ad/spearman.glb
```

Khronos validator is pinned locally to `2.0.0-dev.3.10`. The custom validator
checks one draw call, dimensions, weights, prop sockets, team-mask coverage,
30 fps samples, loop endpoints, atlas dimensions and attribution. Aesthetic
quality, gait velocity continuity and mesh/mesh intersections need visual review.

**Keep LICENSE-ART and PROVENANCE.md with redistributed copies.** This unit and
its adaptations are CC BY-SA 3.0, overriding the general repository art licence.
Credit is embedded in `asset.copyright`, `asset.extras` and the root extras:
“0 A.D. art by Wildfire Games, CC BY-SA 3.0; adapted for Legatum”.
