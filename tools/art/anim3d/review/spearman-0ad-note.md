# Spearman 0 A.D. — round 3

Primary asset: `tools/art/anim3d/units/spearman-0ad/spearman.glb`.
SHA-256: `56ae39d8ebf1b65ebbbc40485e5bd0f706da539b77cac78fb9e8b413a17da0fb`.

Contract-valid real-time map candidate: **603,944 bytes, 2,536 triangles,
30 joints, one skinned mesh, one material, one draw call**, figure 1.8528 m.
One embedded 1024 × 1024 flat RGB albedo atlas; separate PNG 22,581 bytes.
GLB and PNG are below 2 MB combined and left in the worktree for the runner's commit.

## What changed

- Merged body and every prop into one indexed skinned primitive. Spear has one
  unit weight to weapon_R; shield/front/back/grip to shield_arm; helmet and crest
  to helmet, an identity child of head. Props retain rigid shapes.
- COLOR_0.r is the team weight for crest, shield rim and cloak trim; G/B=0, A=1.
  Vertex-region metadata makes actual prop weights and mask coverage auditable.
  Viewer uses a mask-aware shader, still one material. **The map shader must
  consume this channel as a mask, replacing default vertex-colour multiplication.**
  A generic glTF material renders the mask as black/red rather than pigment.
- Kept attack_melee_05 and turned the stance 22 degrees for a clearer thrust.
  At this map camera, projected spear-tip travel increases from about 0.58 to
  0.89 m. This is a whole-stance correction, not a stretching spear or arm.
- Relaxed death's head by 12 degrees, eased the tail and added four held frames.
  The body now touches the ground instead of hanging about 3 cm above it from
  the crest. Death duration is 2.0667 s.
- Checked skin interpolation at 120 fps. The previously clear 30 fps keys hid
  a 24 mm shield-floor intersection in death and a 4 mm walk dip. A conservative
  hip envelope now clears these without root motion or extra animation samples.
  Peak lift: death 24.39 mm, walk 4.42 mm, attack 0.36 mm. These are transient
  corrections, not a permanent floating offset. Idle and hit are unchanged.
- Added flat bronze cuirass/greave ornament and linen seams/hem stripes to the
  existing bronze, crimson and sunburst palette. No upstream textures, normals,
  AO, baked illumination or emission projection. No geometry increase.
- Sprite renderer imports the single skin directly. The old separate rigid-prop
  import workaround is gone. All outputs use the delivered GLB, one fixed
  13.613-degree-pitch camera and a frame enclosing every animation sample.

## Honest motion and art verdict

| Clip | Verdict from decoded sprite sequences and pose review |
| --- | --- |
| idle | Quiet, credible native breathing/weight shift. Motion remains very subtle at 160 px; the upright spear reads clearly. |
| walk | Alternating native gait and rigid carried props remain intact; only a maximum 4.42 mm clearance lift was added. The legacy 6 fps sprite playback is much slower than native-rate motion. Runtime foot sliding during map translation still needs review. |
| attack | Jab and recovery are more legible in profile, with greater screen-space tip travel. The hand still passes near the head/crest and the aspis remains visually dominant. Improved, but not a final emphatic combat read. |
| hit | Short restrained torso/head recoil and rigid shield movement. Serviceable at small scale, with limited cloth response. |
| death | Side collapse stays fully framed; body rests on the ground and the final pose holds still. The aspis covers much of the torso and the cloak remains simple native skinning. Ground clearance passes; this is not a general mesh/mesh collision simulation. |

This is a usable low-poly real-time unit with the correct identity. It is still
below finished Civ 6/Age of Empires art quality: pigment detail is restrained,
the face/armour are simple, and the cloak has no cloth simulation. The painting
was used as inspiration, not pixel matching. No final art PASS is claimed.
Continuous browser playback and the actual map shader were not observed here.

## Review files

All of the following exist in `~/LegatumRuns/anim-pilot/review/3d-v2/`:

| File | Source frames | Game fps | Encoded frames | Duration |
| --- | ---: | ---: | ---: | ---: |
| spearman-0ad-r3-idle-160.mp4 | 12 | 4 | 36 | 9 s |
| spearman-0ad-r3-walk-160.mp4 | 16 | 6 | 48 | 8 s |
| spearman-0ad-r3-attack-160.mp4 | 18 | 14 | 54 | 3.857 s |
| spearman-0ad-r3-hit-160.mp4 | 8 | 12 | 24 | 2 s |
| spearman-0ad-r3-death-160.mp4 | 16 | 4 | 48 | 12 s |

All H.264/yuv420p, 160 × 160, cream background, three repeats; ffprobe verified.
`spearman-0ad-r3-attack-fullrate.png` contains all 36 native attack samples.
`spearman-0ad-r3-decoded-review.png` was made from the actual encoded movies and
visually inspected. The death remains inside the frame throughout.
The sprite rates alter apparent timing; use the viewer for native-rate cadence.

From this worktree root, **outside the sandbox**, run:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs
```

Expected new host outputs (not generated by this lane):
`~/LegatumRuns/anim-pilot/review/3d-v2/spearman-0ad-r3-{idle,walk,attack,hit,death}-viewer.mp4`.
The recorder starts its own loopback server, samples at 30 fps, repeats three
times, and verifies H.264/yuv420p 640 × 640 streams. three.js is pinned at r170.

## Exact checks

- Custom contract validator: PASS, output below.
- Khronos gltf-validator 2.0.0-dev.3.10: 0 errors, 0 warnings, 0 infos, 0 hints.
- Contract corruption tests: 14/14 passed (including extra primitive/material,
  missing mask, empty team region and blended prop weights).
- three.js r170 CPU GLTFLoader/AnimationMixer: PASS for all five clips, one
  skinned mesh/material, 30 joints, mask shader plumbing, motion and loop poses.
- JavaScript syntax: viewer.mjs, team-mask.mjs, record.mjs, check-runtime.mjs and
  validate-khronos.mjs all passed.
- anim3d static import check: 0 unresolved local imports.
- 120 fps ground audit: PASS, worst penetration approximately 0.030 mm,
  final body height 0.000000085 m;
  last death-frame maximum vertex movement 0.000000416 m.
- ffprobe: all five movies match codec, size, format, frame count and game rate.
- git diff --check: PASS. No Rust, rules, app runtime or shipped sprite change;
  no unrelated Cargo/app build suites were run.
- origin/master is already an ancestor of HEAD; no fetch or merge needed.

First valid round-three checkpoint: `oad/r3/contract-first.glb` (597,004 bytes).
Attempted to stage and commit it immediately, but git could not create
`.git/worktrees/lane-6/index.lock` (Operation not permitted). Changes are left
uncommitted for the runner, as instructed. No push or merge was attempted.
Commit message: `oad/r3/commit-message.txt`.

The feedback contract addition was read and implemented. Referenced licence
commit 0ca57b93 is absent locally; no fetch was performed. Existing adjacent
LICENSE-ART preserves Wildfire Games' text, share-alike terms and the exact
approved credit. PROVENANCE.md identifies the pinned 0 A.D. source files and
all round-three changes. Credit and licence remain embedded in the GLB.

## Validator output

```json
{
  "valid": true,
  "glb": "/Users/samcorcos/LegatumRuns/anim-pilot/legatum/.claude/worktrees/lane-6/tools/art/anim3d/units/spearman-0ad/spearman.glb",
  "bytes": 603944,
  "triangles": 2536,
  "joints": 30,
  "skinned_meshes": 1,
  "atlas_px": [
    1024,
    1024
  ],
  "figure_height_m": 1.8528,
  "feet_centre_m": [
    -0.0206,
    0.0168,
    0.0089
  ],
  "meshes": 1,
  "materials": 1,
  "draw_calls": 1,
  "team_regions": [
    "crest",
    "shield rim",
    "cloak trim"
  ],
  "rigid_vertices": {
    "crest": 71,
    "crest_base": 104,
    "Greek head": 107,
    "helmet": 197,
    "aspis": 145,
    "Aspis back": 65,
    "Aspis handgrip": 40,
    "spear": 88
  },
  "clips": {
    "attack": {
      "duration_s": 1.166667,
      "fps": 30,
      "loop_endpoint_max_error": 0.0003755
    },
    "death": {
      "duration_s": 2.066667,
      "fps": 30,
      "loop_endpoint_max_error": 1.5220499
    },
    "hit": {
      "duration_s": 0.8,
      "fps": 30,
      "loop_endpoint_max_error": 0
    },
    "idle": {
      "duration_s": 2.0,
      "fps": 30,
      "loop_endpoint_max_error": 1e-06
    },
    "walk": {
      "duration_s": 1.333333,
      "fps": 30,
      "loop_endpoint_max_error": 1.2e-06
    }
  },
  "errors": [],
  "review_required": [
    "Flat albedo, exact team region coverage, seamless velocity and game feel require visual review."
  ]
}
```

```json
{
  "numErrors": 0,
  "numWarnings": 0,
  "numInfos": 0,
  "numHints": 0,
  "messages": [],
  "truncated": false
}
```

## Next

Run the host recorder, verify team tint with the actual map shader, and judge
native-rate attack and death in a three-figure squad. Final art approval remains
with the lead. Further polish should focus on armour/face pigment and cloak
motion while retaining the one-draw-call contract.

Non-obvious implementation lessons: one-bone prop vertices must be transformed
into shared inverse-bind space before merging; simply joining arrays offsets
props. COLOR_0 masks require bypassing default glTF colour multiplication in
both three.js and Blender. Clear 30 fps keys do not guarantee floor clearance
between keys; rigid shield rotation needed the interpolated audit.
