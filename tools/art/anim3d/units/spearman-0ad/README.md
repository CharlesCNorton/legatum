# Spearman — real-time 0 A.D. adaptation, round 5

`spearman.glb` is the primary asset. Sprites render this exact GLB, not an
alternate Blender scene. It contains **2,536 triangles, 30 joints, one skinned
mesh, one indexed primitive and one material**. The figure including crest is
**1.9361 m** tall. Metres, Y-up, +Z forward, feet centred at the origin. There is
one embedded **1024 × 1024** RGB base-colour atlas, with no normal map, AO,
baked illumination or emission projection. GLB and separate atlas total less
than 0.7 MB and belong in git.

Five in-place clips are sampled at 30 fps: `idle`, `walk`, `attack`, `hit`,
`death`. Idle/walk close their loop poses; the skeleton root never translates.
The spear, shield and helmet remain rigid within the single draw call.

## Round 5 changes

The aspis has a broad bronze sunburst on an oxidised bronze field with a dark
rim. The crest is wider across the helmet for readability at 160 px. Darker
bronze and crimson separate from skin and linen in greyscale. All markings are
flat pigment boundaries; no highlights or shadows are painted into the atlas.

`review.json` documents the **-30° display yaw about glTF +Y**. Both the sprite
renderer and viewer implement its inverse as a camera orbit. With the original
map-camera direction `(4, 1.8, 6.265)` this means camera azimuth **62.56°** and
pitch **13.613°**. This direction preserves the crest profile and exposes the
native attack's overarm spear travel. The opposite yaw foreshortened the thrust
in the full-rate sheet. The idle carrying arm now exposes the bronze cuirass beside the shield.
The GLB itself stays +Z forward; the old attack-only 22° stance turn is removed.
The map can read `asset.extras.display_yaw_degrees` as review guidance, not as a
rotation already baked into the geometry.

Idle uses a two-bone carrying-arm solve at unchanged bone lengths, followed
by a 35-degree forearm roll. The hand target moves 10 cm out, 22 cm back and
5 cm down; the shield follows the forearm with its original grip. Hit shares
this correction so it returns to the same guard. No idle prop offset is added.

Native `death_a` replaces the staged kneeling `death_b`. Its direct backward
collapse ends prone, with a 32-degree head relaxation, an eased finish and four
held final frames. The shield settles flat; a maximum 9.38 mm socket clearance
adjustment accounts for shield thickness instead of lifting the corpse. The
spear retains its clean 0.533-second world-space release beside the body, then
stays put. Single-bone rigid weights and the stationary skeleton root remain.
No object is hidden or scaled to zero.

Attack keeps `attack_melee_05`, retimed for takeback, drive and recovery. Its
hips move **13.25 cm toward +Z** in total while both ankles stay planted (maximum
horizontal interpolation drift **0.32 mm** at 120 fps). A two-bone leg solve
lowers the pelvis as necessary to preserve leg lengths. The shoulders follow
with four degrees of forward lean. Cape1/2/3 local rotation excursions are
halved relative to guard, reducing the stiff panel snap.

Hit is reauthored from the native idle guard: **14 degrees** of torso recoil at
frame **5**, three more degrees of head follow, and eased recovery by frame
**20**. The shield moves rigidly with the carrying arm. The clip remains 0.8 s.
Walk retains the reviewer-approved native gait; no extra bob or altered foot
placements were added.

The crest is 1.3x thicker and 1.2x taller than round 4. A 1.3x height trial
exceeded the contract's 1.95 m figure ceiling, so the final crest stops at
1.9361 m overall. The spear cross-section is 1.5x wider and its tip uses a new
bright bronze pigment swatch. No triangles were added. Fresh 48 px figure-height
renders of idle and attack sit beside the 160 px sprites in
`spearman-0ad-r5-readability-48.png`.

Each clip gets one fixed orthographic fit from all its evaluated vertices at
30 fps, projected into the camera plane. The target figure height is 70% of the
frame, reduced when needed to keep the full weapon/fall extent inside 92%.
There is no camera tracking or per-frame zoom. `viewer/framing.mjs` is shared by
the browser and its CPU runtime check; the Blender renderer implements the same
projection from `review.json` and records its measured fit.

## One draw call and team colour

Spear vertices carry one unit weight to `weapon_R`; shield/front/back/grip to
`shield_arm`; helmet/crest/support to `helmet` (an identity socket under `head`).
`mesh.extras.vertex_regions` records vertex ranges and attachments so the
validator checks actual weights rather than trusting labels.

**`COLOR_0.r` is team weight, not visible RGB colour.** Green/blue are zero,
alpha is one. Crest, shield rim and cloak trim have red=1; other vertices have
red=0. Team areas use neutral atlas samples: white for crest/trim and dark grey
for the shield rim, preserving the dark border for every player colour.
The main cloak remains crimson. The runtime shader must replace standard
vertex-colour multiplication with:

```glsl
diffuseColor.rgb *= mix(vec3(1.0), teamColorLinear, vColor.r);
```

Default team colour is sRGB `#a52627`, converted to linear before shading.
`asset.extras.team` and `material.extras.team` describe this interface;
`viewer/team-mask.mjs` demonstrates it without another draw call. Clone
materials per independently tinted instance. A generic glTF viewer using
ordinary vertex-colour multiplication will display the data mask incorrectly.

## Rebuild and verify

From the worktree root, with the preserved inputs in `source-manifest.json`:

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman-0ad/paint_atlas.py tools/art/anim3d/units/spearman-0ad/spearman-albedo.png
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman-0ad/build.py
python3 tools/art/anim3d/validate_glb.py tools/art/anim3d/units/spearman-0ad/spearman.glb
python3 -m unittest discover -s tools/art/anim3d -p test_validate_glb.py
python3 tools/art/anim3d/units/spearman-0ad/check_combat.py tools/art/anim3d/units/spearman-0ad/spearman.glb
python3 tools/art/anim3d/units/spearman-0ad/check_motion.py tools/art/anim3d/units/spearman-0ad/spearman.glb
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman-0ad/check_spear.py tools/art/anim3d/units/spearman-0ad/spearman.glb
python3 tools/art/anim3d/kit/check_imports.py
VIEWER_NODE_MODULES="$ANIM_ROOT/oad/viewer-runtime/node_modules" node tools/art/anim3d/viewer/check-runtime.mjs
GLTF_VALIDATOR_MODULE="$ANIM_ROOT/oad/validator/node_modules/gltf-validator" node tools/art/anim3d/viewer/validate-khronos.mjs tools/art/anim3d/units/spearman-0ad/spearman.glb
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman-0ad/render.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman-0ad/package.py
```

`build.py` loads the preserved round-one master, exports authored rigid props,
merges into one skin with `merge.py`, and applies `clearance.py` to the GLB.
`oad/r5/spearman.blend` is an authoring intermediate: the finalized GLB is the
motion/appearance authority. Blender 4.5 is unnecessary for this rebuild.
`render.py -- --quick` produces four diagnostic poses per clip at 320 px.

The contract validator checks mesh/material/draw count, dimensions, rigid
weights, sockets, team-mask coverage, atlas, 30 fps samples, loop endpoints and
attribution. `check_motion.py` checks ground clearance at 120 fps.
`check_combat.py` verifies the exported hip drive, planted ankles, fixed leg
lengths and hit timing. `check_spear.py` needs NumPy and checks spear mesh edges against figure/shield
triangles at 120 fps, excluding the first 0.1 s of grip release. It rejects the
round 3 spear trajectory. These checks do not establish general body self-collision,
velocity continuity, browser pixels or aesthetic approval.

## Review outputs

All five sprite MP4s are in `~/LegatumRuns/anim-pilot/review/3d-v2/`, named
`spearman-0ad-r5-<clip>-160.mp4`. H.264, yuv420p, 160 × 160, cream background,
three repeats. The 36-frame contact sheet is `spearman-0ad-r5-attack-fullrate.png`.

| Clip | Sprite frames | Game fps | GLB duration | Three-repeat sprite duration |
| --- | ---: | ---: | ---: | ---: |
| idle | 12 | 4 | 2.000 s | 9 s |
| walk | 16 | 6 | 1.333 s | 8 s |
| attack | 18 | 14 | 1.167 s | 3.857 s |
| hit | 8 | 12 | 0.800 s | 2 s |
| death | 16 | 4 | 1.400 s | 12 s |

The legacy sprite rates change apparent speed. Use the real-time viewer for
native cadence. Masters, frames and verification receipts live in
`~/LegatumRuns/anim-pilot/oad/r5/`; the review note is
`~/LegatumRuns/anim-pilot/review/3d-v2/spearman-0ad-note.md`.

Serve the repo with `python3 -m http.server 8765`, then open
`http://localhost:8765/tools/art/anim3d/viewer/index.html`. No build step;
three.js is pinned to 0.170.0. Clip selection, orbit, fixed map view and team
colour are available. No site is deployed.

Run the recorder **outside the sandbox**, from this worktree root:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs
```

It starts/stops a loopback server, captures exact 30 fps frames, writes three
repeats at 960 × 640, and verifies streams with ffprobe. Outputs are
`spearman-0ad-r5-<clip>-viewer.mp4` in the review directory. The 3:2 frame keeps the full death spear extent while retaining about 70%
figure height. The receipt includes per-clip framing measurements and the GLB
SHA-256, so older recordings cannot be mistaken for this build. Host Playwright 1.56.1 needs Chromium installed.
The agent does not launch Chromium in the sandbox; viewer MP4s must be generated on the host for this asset. Capture frames are
partitioned by asset hash so stale frames cannot lengthen a shortened clip.

## Attribution

**Keep LICENSE-ART and PROVENANCE.md beside redistributed GLBs.** This unit,
its atlas and derived renders are CC BY-SA 3.0, overriding the repository's
general art licence. Credit is embedded in `asset.copyright` and `asset.extras`:
“0 A.D. art by Wildfire Games, CC BY-SA 3.0; adapted for Legatum”. Provenance
names the exact source files at commit
`61a3b9507d974084e6badb88a0826bd89a6d5b8b` and our modifications.
