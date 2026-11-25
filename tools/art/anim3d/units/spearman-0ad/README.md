# Spearman — painted premium round 3

`spearman.glb` is the primary asset. Both review renderers load that exact GLB.
It contains **spearman_LOD0 (at most 10,000 triangles)** and **spearman_LOD1
(at most 3,000 triangles)**, sharing **30 joints and one material**. Each LOD
has one indexed skinned primitive; display only one at a time. There is no
MSFT_lod extension. The viewer defaults to LOD0 and provides an explicit LOD
selector. Metres, Y-up, +Z forward; display yaw stays in the camera.

The three embedded 1024-square WebP textures are base colour, tangent-space normal, and ORM
(R occlusion, G roughness, B metallic), all on UV0, derived from 2048 masters.
The GLB requires EXT_texture_webp and KHR_mesh_quantization.
COLOR_0 red is the team weight, interpreted with `viewer/team-mask.mjs`.
The painted lane intentionally includes stronger form shading in albedo and
uses rougher, less metallic bronze than a conventional PBR bronze material.
This is a round-three art candidate, not a premium-quality approval.

All five round-six clips and the skeleton are preserved exactly, including the
hit reaction and the round-five attack/death fixes. `check_painted.py` verifies
that independently of geometry and texture changes. Read PROVENANCE.md and
SOURCES.md for the source licence, original asset hash and build details.

## Rebuild the painted candidate

Run from this worktree. Preserve the approved input once; never use the new
painted GLB as its own input:

```sh
source tools/art/anim3d/env.sh
mkdir -p "$ANIM_ROOT/lanes/spearman-0ad-painted-r3"
git show 5199b147:tools/art/anim3d/units/spearman-0ad/spearman.glb > "$ANIM_ROOT/lanes/spearman-0ad-painted-r3/approved-r6.glb"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman-0ad/painted.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman-0ad/painted_deliver.py
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman-0ad/painted_render.py -- --stills
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman-0ad/painted_render.py
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman-0ad/painted_render.py -- --joints
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman-0ad/painted_render.py -- --turntable
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman-0ad/painted_review.py
```

`painted_forms.py` applies the round-two body bulk, pleated tunic, rounded
horsehair arc, wider lined cloak and shaped knees to the round-one builder.
`painted_human.py` fits a muscular MPFB 2.0.18 CC0 body to the approved rest
pose and transfers native weights by nearest-face interpolation, limited to four.
`painted_premium.py` closes the Corinthian face and nape, rebuilds the rounded
horsehair volume and muscular cuirass, lowers the shoulder drape, integrates
the team trim into the cloak surface, and preserves the circular shield outline.
The unchanged native joint axes and keys remain the only motion source.

Simplification runs on outer surfaces before thickness. LOD1 removes the marked
inner shell before simplifying, then rebuilds thickness. Triangulation precedes
UV packing and baking. Tangent normals are hemisphere-corrected and limited to
25 degrees after Cycles transfer to prevent opposing-shell bake rays producing
black shading. This is bounded baked relief, not unmodified high-poly normals.

`painted_export.py` repackages the saved master without repeating Cycles bakes.
The master and baking copies remain under ANIM_ROOT. No changes to game rules,
in-game art selection or the production renderer are made by these scripts.
The old flat atlas remains only for the historical builder below.

## Verify and record

```sh
python3 tools/art/anim3d/validate_glb.py tools/art/anim3d/units/spearman-0ad/spearman.glb
python3 tools/art/anim3d/units/spearman-0ad/check_painted.py "$ANIM_ROOT/lanes/spearman-0ad-painted-r3/approved-r6.glb" tools/art/anim3d/units/spearman-0ad/spearman.glb
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman-0ad/check_painted_contact.py tools/art/anim3d/units/spearman-0ad/spearman.glb
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman-0ad/check_painted_joints.py tools/art/anim3d/units/spearman-0ad/spearman.glb
python3 -m unittest discover -s tools/art/anim3d -p 'test_validate*.py' -v
GLTF_VALIDATOR_MODULE="$ANIM_ROOT/oad/validator/node_modules/gltf-validator" node tools/art/anim3d/viewer/validate-khronos.mjs tools/art/anim3d/units/spearman-0ad/spearman.glb
VIEWER_NODE_MODULES="$ANIM_ROOT/oad/viewer-runtime/node_modules" node tools/art/anim3d/viewer/check-runtime.mjs
```

The lead runs this host-only capture, outside the sandbox:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs --prefix spearman-0ad-painted-r3 --out "$HOME/LegatumRuns/anim-pilot/review/3d-v2"
```

It writes `<prefix>-<clip>-viewer.mp4`, `<prefix>-turntable.mp4` and a validation
receipt with the asset SHA-256. It also writes `<prefix>-viewer-idle.png` and
`<prefix>-vs-panel-viewer.png` using actual MeshStandardMaterial/ACES pixels.
The turntable is 12 seconds at 30 fps. Viewer
clips repeat three times at native timing. CPU sprite movies repeat three times
at game sampling rates (idle/death 4, walk 6, attack 14, hit 12 fps); their
rounding to whole frames is recorded in the video receipt. The 160-square
camera contains the entire weapon/death extent, so attack and death fill less
of the square than the 960-by-640 browser capture. Camera fitting is fixed per
clip, not tracked per frame. CPU stills use Cycles/AgX; the browser uses ACES. The CPU turntable is a separate
`<prefix>-turntable-cycles.mp4` (256 px, 12 seconds, 8 fps). The joint sheet samples
shoulders, elbows and knees in every clip. The numeric joint check detects severe
LBS axis collapse; it does not certify collisions or visual deformation quality.
The contract now enforces a strict 2,000,000-byte download ceiling.

## Historical round-six motion baseline

The sections below document the approved motion input and earlier builders.
They describe the old single-mesh flat-atlas assets, not the current packaging.
Do not run them on top of the painted candidate.

## Round 6: hit only

`hit.py` changes only the existing hit sample bytes in the delivered GLB. It
uses idle frame zero as its source; it does not import/re-export meshes or
resample other clips. Attack, death, walk, idle, geometry, atlas, team mask and
contract metadata are unchanged. `package_hit.py` verifies this against the
preserved round 5 GLB and carries the four accepted sprite movies and the
48 px/attack sheets forward byte for byte.

The 25 keys at 30 fps make a **0.8 s** reaction. Frames 0–4 recoil 15 cm backward
at the pelvis and drop 6.5 cm, with 25° combined spine/chest bend. Neck recoil
peaks on frame 5. The shield arm swings back/out with its rigid aspis; the spear
tip dips while a fixed-length arm solve keeps its butt above the floor. The rear
foot catches the weight with a 15 cm step during frames 4–8. Frames 8–24 ease
back to the exact idle-zero channel values; the skeleton root stays fixed.

On the eight delivered 160 px RGBA samples, the opaque alpha-mask centroid
travels **11.61 px**, the alpha-weighted centroid **11.47 px**, and the top moves
**17 px**. Centroid travel is maximum pairwise Euclidean distance; opaque mask
and top use alpha >= 128. Both centroid definitions clear the requested 8 px.
Hit/idle comparison renders use the same fixed camera. This measures the full
figure with its props, with no cropping, tracking or pose-dependent zoom.

Run the hit-only rebuild and review from the worktree root:

```sh
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman-0ad/hit.py
ANIM_ROUND=6 ANIM_CLIPS=hit,idle ANIM_SHARED_FIT=1 ANIM_FULLRATE=1 blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman-0ad/render.py
"$HOME/LegatumRuns/anim-pilot/venv/bin/python" tools/art/anim3d/units/spearman-0ad/package_hit.py
```

The source evidence for packaging is `oad/r6/approved-r5.glb`, the approved
round 5 asset (SHA-256 `3c4e74a929d8e619874d45d5e3b2849d0e35d00d9675c1d1e4a9d17bfb5cf3ab`),
plus `oad/r5/frames/` and the round 5 video receipt. These heavy local inputs
are under `~/LegatumRuns/anim-pilot/`. `hit.py` is idempotent and can run on
either round 5 or round 6. For a full historical rebuild below, run `hit.py`
after `build.py` to apply round 6.

Review files are `review/3d-v2/spearman-0ad-r6-<clip>-160.mp4` and
`spearman-0ad-r6-hit-vs-idle-160.mp4`. The standalone hit is eight samples at
12 fps repeated three times (2 s). The comparison is 320 × 180 with two 160 px
panels and labels: three 3-second cycles, each playing hit at 12 fps then holding
idle-zero while the right panel completes its 12-frame idle at 4 fps. This
preserves both game rates. Native GLB playback is 0.8 s; the legacy sprite
schedule compresses that to 0.667 s. `oad/r6/hit-review.json` records metrics,
asset hashes, frozen-data checks and ffprobe results.

Contract validation passes; Khronos reports zero errors, warnings, infos or
hints. The 120 fps ground check passes (hit minimum -1.254 mm, inside the
existing 2 mm tolerance). Three.js CPU loading/mixing/framing passes. Browser
capture and the reviewer's playing-speed verdict remain for the lead.

## Approved round 5 baseline (retained except hit)

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

The superseded round 5 hit used the native idle guard: **14 degrees** of torso recoil at
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

Run the round 6 recorder **outside the sandbox**, from this worktree root:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs --round 6
```

It starts/stops a loopback server, captures exact 30 fps frames, writes three
repeats at 960 × 640, and verifies streams with ffprobe. Outputs are
`spearman-0ad-r6-<clip>-viewer.mp4` in the review directory. The 3:2 frame keeps the full death spear extent while retaining about 70%
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
