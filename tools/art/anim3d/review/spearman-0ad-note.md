# Spearman 0 A.D. — round 4 handoff

Primary deliverable: `tools/art/anim3d/units/spearman-0ad/spearman.glb`.
SHA-256: `d534283aa791de1936d680f825e939be97d00a2de54c2fb6a01d1299588f0e5f`.
601,936 bytes; separate atlas 20,584 bytes. Both remain below 2 MB and are in the
worktree, beside LICENSE-ART and updated PROVENANCE.md. No push or merge.

## Changes

- Bronze sunburst enlarged into a readable 12-ray device on an oxidised bronze
  field. Dark neutral rim keeps the COLOR_0 team mask. Flat pigment only.
- Bronze and crimson base colours darkened; skin and linen separate in greyscale.
  Approximate sRGB luma (0–255): bronze 99.4, linen 200.1, crimson 44.8, skin 144.5.
  These are pigment values, not baked directional shading.
- Existing crest hair widened 1.65x and support 1.30x, with no extra triangles.
- Display yaw is **-30 degrees around glTF +Y**, implemented as inverse camera
  orbit in both render.py and viewer.mjs, documented in review.json and GLB extras.
  Camera pitch remains 13.613 degrees. The GLB stays +Z forward. Removed the old
  attack-only 22-degree stance turn. Opposite yaw was rejected after the full-rate
  sheet showed a foreshortened thrust.
- Death spear releases from the initial grip, drops beside the body over 0.533 s,
  then holds. The existing weapon_R socket carries the baked trajectory; all spear
  vertices still have one unit weight to that bone. No extra mesh or draw call.
  Final spear centre is x=-0.82, z=+1.0 m in glTF ground coordinates. A 16-degree
  head relaxation keeps the widened crest from propping the corpse above ground.
- Each clip is framed from evaluated skinned vertices in camera-plane coordinates.
  One fixed camera per clip, no animated zoom. Viewer capture is 960 x 640 to keep
  the full fall/weapon extent and about 70% figure height. Square sprites retain
  every frame of the fall at a smaller scale.

## Verification

- Contract validator: **PASS**, full output below. One mesh/material/primitive,
  2,536 triangles, 30 joints, 1.8528 m figure, 1024 x 1024 atlas, five 30 fps clips,
  rigid single-bone props, COLOR_0 team regions, exact attribution.
- Contract regression tests: **14/14 passed**.
- Khronos gltf-validator 2.0.0-dev.3.10: **0 errors, 0 warnings, 0 infos, 0 hints**.
- three.js r170 GLTFLoader / AnimationMixer / team shader / framing CPU checks:
  **PASS** for every clip. Figure height in the 3:2 capture is
  attack 70.0%, death 70.0%, hit 69.0%, idle 69.9%, walk 70.0%.
- Ground clearance: **PASS**, 889 samples total at 120 fps. Worst penetration
  0.030 mm. Final body-floor distance 0.000085 mm; last-frame maximum motion
  0.00117 mm. These checks cover the final exported GLB, not the authoring master.
- Spear/figure mesh-edge crossings: **PASS**, 249 samples at 120 fps. Grip contact
  ends at 0.050 s; no crossing at or after the 0.1 s release allowance. The same
  check rejects the round 3 GLB, including the reported middle death frames.
  Scope: spear edges against other triangles; not a general body self-collision,
  coplanar-contact or cloth solver.
- Import-path audit: **0 unresolved local imports**. JavaScript syntax checks
  passed for viewer, recorder, framing and runtime checker. `git diff --check`
  passed. All 17 preserved source-file sizes and SHA-256 hashes match the manifest.
- All five sprite encodes: **PASS** via ffprobe, H.264/yuv420p, 160 x 160, cream
  background, exactly three repeats. Inspected the full-rate attack sheet, all
  walk/hit/death sprite poses and idle in greyscale. No cropped geometry in the
  inspected sprite frames. Browser pixels/native-time playback await the lead.

## Motion verdict

| Clip | Verdict from the rendered frame sequence |
| --- | --- |
| idle | Stable guard; sunburst and crest now read at 160 px. The shield still hides part of the torso and carrying arm from this view. Motion is deliberately restrained. |
| walk | Native gait reads as alternating steps, with a rigid carried spear/shield and visible cloak response. Loop endpoints pass. Foot slip against map travel speed and velocity continuity still need runtime review. |
| attack | Native attack_melee_05 now shows the overarm spear sweep/thrust in profile. Clearer than the opposite yaw, but broad/slow anticipation remains. No claim of AoE/Civ polish from a validator. |
| hit | Short procedural flinch with shield movement and recovery; readable but mild, not mocap-quality impact. |
| death | Shaft drops to one side, stays separate, and final body is grounded and held. The native clip has a staged crouch before the fall; the 4 fps stopgap sprite rate exaggerates that pause. Square framing makes the figure about 50% tall to include the complete spear footprint. |

This is a stronger, contract-ready strategy-game asset with recognisable bronze,
crimson and sunburst identity. It remains visibly low-poly with flat albedo. Lead
art approval and live-map/browser playback are outstanding; I am not marking an
art PASS. No general body self-intersection clearance is claimed.

## Files and host recording

Sprite files (all regenerated for this GLB):

- `/Users/samcorcos/LegatumRuns/anim-pilot/review/3d-v2/spearman-0ad-r4-idle-160.mp4`
- `/Users/samcorcos/LegatumRuns/anim-pilot/review/3d-v2/spearman-0ad-r4-walk-160.mp4`
- `/Users/samcorcos/LegatumRuns/anim-pilot/review/3d-v2/spearman-0ad-r4-attack-160.mp4`
- `/Users/samcorcos/LegatumRuns/anim-pilot/review/3d-v2/spearman-0ad-r4-hit-160.mp4`
- `/Users/samcorcos/LegatumRuns/anim-pilot/review/3d-v2/spearman-0ad-r4-death-160.mp4`

Full-rate sheet: `/Users/samcorcos/LegatumRuns/anim-pilot/review/3d-v2/spearman-0ad-r4-attack-fullrate.png`.
Video receipt: `/Users/samcorcos/LegatumRuns/anim-pilot/review/3d-v2/spearman-0ad-r4-video-validation.json` (includes GLB hash).
Heavy master, frames and JSON receipts: `/Users/samcorcos/LegatumRuns/anim-pilot/oad/r4/`.

The viewer MP4s are **not regenerated by this sandbox run**. Existing r4-named
viewer files, if present from the earlier lead run, are stale relative to this
asset. From the worktree root, outside the sandbox, run:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs
```

This generates `/Users/samcorcos/LegatumRuns/anim-pilot/review/3d-v2/spearman-0ad-r4-<clip>-viewer.mp4` for all five clip names,
at exact 30 fps and three repeats. The viewer receipt contains the GLB SHA-256 and
framing measurements. Next: review these videos and the map squad with the team
mask shader, then decide whether the remaining idle occlusion and staged death
need another motion round.

Git staging failed with `Operation not permitted` creating
`.git/worktrees/lane-6/index.lock`; changes are left for the runner to commit.
The fetched `origin/master` has no commits outside this branch (`HEAD..origin/master`
count 0), so no merge was needed. No Rust/game rules changed; engine checks were
not run. The requested licence commit `0ca57b93` and branch
`claude/project-thread-yarkpd` are absent locally. The existing unit-local
Wildfire Games CC BY-SA 3.0 licence was retained with the exact required credit;
source provenance records the requested 0 A.D. commit and exact files.

Non-obvious learnings: camera-space evaluated-vertex bounds avoid excessive
world-AABB padding; the sign of a display yaw must be judged against the full-rate
attack, not just an idle pose; widening a crest can alter the corpse's ground
support; rigid single-bone props can release through an animated leaf socket
without adding a draw call. No shared learnings files were edited.

## Contract validator output

```json
{
  "valid": true,
  "glb": "/Users/samcorcos/LegatumRuns/anim-pilot/legatum/.claude/worktrees/lane-6/tools/art/anim3d/units/spearman-0ad/spearman.glb",
  "bytes": 601936,
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
      "loop_endpoint_max_error": 0.0003753
    },
    "death": {
      "duration_s": 2.066667,
      "fps": 30,
      "loop_endpoint_max_error": 3.7910993
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
