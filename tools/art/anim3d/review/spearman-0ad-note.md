# Spearman 0 A.D. — round 5 candidate handoff

Primary deliverable: `tools/art/anim3d/units/spearman-0ad/spearman.glb`.
SHA-256: `3c4e74a929d8e619874d45d5e3b2849d0e35d00d9675c1d1e4a9d17bfb5cf3ab`.

**Candidate for lead playback review; not art-approved.** The contract, Khronos,
CPU runtime, exported combat motion and clearance checks pass. I inspected the
rendered 160 px sequences/contact sheets, the full-rate attack sheet, and the
48 px figure-height comparison. Chromium playback/recording was not run here.

## What changed

- Idle carrying arm opens outward with a fixed-length two-bone solve and a
  35-degree forearm roll. The bronze cuirass now reads beside the aspis; the
  original grip and rigid shield attachment remain. Hit shares this guard.
- Death uses **death_a** instead of death_b. It falls backward directly, ends
  prone, eases into rest and holds the final four keys. The full clip is 1.4 s;
  there is no kneeling hold. The head relaxes 32 degrees so the crest does not
  suspend the body. A maximum 9.38 mm shield-socket clearance correction lays
  the shield down instead of lifting the corpse. The body touches the ground.
- The spear keeps the clean 0.533 s release beside the body. The thicker shaft
  still passes the 120 fps post-release crossing check.
- Attack retains attack_melee_05 with a longer takeback and faster thrust,
  **13.25 cm total forward hip drive**, planted ankles, reachable fixed-length
  legs, and four degrees of shoulder follow. Cape1/2/3 local swing is halved.
- Hit is reauthored over idle: **14-degree torso recoil peaking on frame 5**,
  three-degree neck follow, and eased recovery by frame 20 (0.8 s total).
- Walk stays unchanged: the round-four and round-five walk joint positions
  match exactly at all 41 exported samples. New crest/spear dimensions apply
  to every clip.
- Crest thickness is another **1.3x**, height **1.2x**. A 1.3x height trial made
  the figure 1.9784 m and failed the unchanged 1.95 m contract ceiling; the
  accepted figure is **1.9361 m**. Spear cross-section is **1.5x** wider and its
  tip has a brighter bronze pigment swatch. No triangles were added.
- Kept round four's sunburst, darker flat pigments, wider crest, -30-degree
  display yaw, separate per-clip camera fit, clean spear release, one-draw-call
  contract, team mask and licence. GLB remains +Z forward, Y-up, metres.
- Recorder now targets r5 and partitions capture frames by GLB SHA-256, so a
  shortened death cannot accidentally reuse stale trailing frames.

## Feedback coverage

Re-read `spearman-0ad-FEEDBACK.md` after the new 2026-11-25 01:18Z playback notes
arrived. All seven items are addressed: preserved walk; added attack commitment
and cape damping; replaced weak hit; shortened death; opened idle per Sam's
explicit priority; checked tight viewer framing; produced a real 48 px
figure-height render beside the 160 px sprites. Framing is measured over all
30 fps evaluated poses, with one fixed camera per clip. Viewer figure fractions:
attack 70.00%, death 70.00%, hit 70.00%, idle 70.00%, walk 70.00%.
The square death sprite is smaller to retain the entire fall and spear; the
960x640 viewer keeps approximately 70% figure height.

## Honest clip verdicts

| Clip | Verdict from rendered sequence / exported motion |
| --- | --- |
| idle | Clear torso, crest, sunburst and upright spear; quiet breathing. The shield is more edge-on but still recognizable. |
| walk | Retained the reviewer-approved gait, clean feet and loop. The legacy 6 fps sprite cadence is slower than the native 1.333 s GLB cycle. |
| attack | More committed weight transfer over stable feet; takeback, thrust and recovery are distinct. The cloak is less whippy, though this low-poly cape remains visibly simple. |
| hit | Readable torso/head recoil rather than only a spear wobble; peak and recovery are verified. Lead should confirm that one play at native speed is sufficiently emphatic. |
| death | Direct fall with no staged kneel, grounded prone finish, held corpse and separate spear. Whole extent is framed. Ground and spear checks do not prove every possible body self-intersection. |

At 48 px figure height the enlarged red crest and shaft remain legible; the
bronze/linen/crimson separation survives. Fine sunburst rays and cuirass detail
naturally simplify. This is an isolated cream-background check, not validation
against trees in the live 3D map.

## Files and playback

GLB: **578,452 bytes**, **2,536 triangles**, **30 joints**, one skinned
mesh, one indexed primitive, one material/draw call. Atlas: **1024x1024**, RGB,
**20,606 bytes** separately; embedded in the GLB.
No normal map, AO, baked lighting or projection. Both final files are in git scope.
PROVENANCE.md names the exact 0 A.D. files at
`61a3b9507d974084e6badb88a0826bd89a6d5b8b`; LICENSE-ART accompanies the GLB.
Required credit is in copyright and extras.

Review directory: `~/LegatumRuns/anim-pilot/review/3d-v2/`:

- `spearman-0ad-r5-idle-160.mp4`
- `spearman-0ad-r5-walk-160.mp4`
- `spearman-0ad-r5-attack-160.mp4`
- `spearman-0ad-r5-hit-160.mp4`
- `spearman-0ad-r5-death-160.mp4`
- `spearman-0ad-r5-attack-fullrate.png` (all 36 frames)
- `spearman-0ad-r5-readability-48.png` (fresh small-scale renders)
- `spearman-0ad-r5-video-validation.json` (asset hash and ffprobe receipts)

Each MP4 is H.264/yuv420p, 160x160, cream background, three repeats. Source
counts/rates: idle 12/4 fps, walk 16/6, attack 18/14, hit 8/12, death 16/4.
These existing game rates change apparent duration: 9, 8, 3.857, 2 and 12 s
respectively for three repeats. Native GLB durations are 2, 1.333, 1.167, 0.8,
and 1.4 s. Judge native cadence in the host viewer.

From this worktree root, outside the sandbox:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs
```

This writes `spearman-0ad-r5-<clip>-viewer.mp4` for all five clips and a hash-bound
viewer receipt in the review directory, 960x640, 30 fps, three repeats. No r5
viewer files were present at the final local inventory; the agent has not
created or viewed them. Older recordings cannot approve this asset hash.

Authoring master, frames, logs and all verification receipts:
`~/LegatumRuns/anim-pilot/oad/r5/`. `spearman.blend` is an authoring intermediate;
render.py imports the final GLB, which includes the export/clearance corrections.

## Checks and limits

- Contract validator: PASS; exact output below.
- Validator regression suite: **14 tests passed**.
- Khronos: **0 errors, 0 warnings, 0 infos, 0 hints**.
- three.js 0.170.0 GLTFLoader / AnimationMixer / team shader / framing CPU check: PASS.
- 120 fps ground check: PASS. Worst penetration is numerical, **0.0206 mm**;
  final death body ground height **0.00017 mm**, held last-key motion **0.00254 mm**.
- Combat check: PASS. Hip drive **132.46 mm**, horizontal ankle drift **0.319 mm**,
  leg-length variation **0.0023 mm**. Hit **13.997 degrees**, peak frame **5**,
  recovered by **20**.
- Spear check: PASS, **169 samples**, zero post-release intersections after 0.1 s;
  only the intended initial grip contacts through 0.0417 s are reported.
- Source manifest: **18 files verified**, zero hash mismatches.
- Blender import check: **0 unresolved imports**. Recorder `node --check`: PASS.
- MP4 ffprobe checks: PASS for all five clips, including frame counts and formats.
- `git diff --check`: PASS.
- Repository-wide `python3 tools/gates/art.py` did **not** pass: its legacy art-set
  renderer `tools/art/render-sets.mjs` exited 1. Its truncated error did not expose
  the underlying reason. It ran on HEAD, not these uncommitted assets, and does
  not replace the GLB checks. Lead/host art review remains outstanding.
- Requested `git show 0ca57b93:LICENSE-ART` and the named branch ref were unavailable
  in this checkout. No fetch was attempted. The existing unit-specific Wildfire
  Games licence, provenance and embedded credit are retained; Sam's explicit
  source approval governs this task.

Useful lesson: a shield pivot below its shell thickness must be laid flat before
applying a small socket clearance correction. Lifting the entire actor to fix
that prop can leave a prone body visibly hovering. Likewise, a planted-foot lunge
needs a reachable knee solve: forcing a distant ankle stretches the lower leg.

## Contract validator output

```json
{
  "valid": true,
  "glb": "/Users/samcorcos/LegatumRuns/anim-pilot/legatum/.claude/worktrees/lane-6/tools/art/anim3d/units/spearman-0ad/spearman.glb",
  "bytes": 578452,
  "triangles": 2536,
  "joints": 30,
  "skinned_meshes": 1,
  "atlas_px": [
    1024,
    1024
  ],
  "figure_height_m": 1.9361,
  "feet_centre_m": [
    -0.0206,
    0.0168,
    0.009
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
      "loop_endpoint_max_error": 0.0003331
    },
    "death": {
      "duration_s": 1.4,
      "fps": 30,
      "loop_endpoint_max_error": 5.9781834
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

Next: lead runs the host recorder and judges attack commitment, hit readability
and corpse settling at native speed; then checks the 48 px silhouette in the
3D map under trees. No owner approval or full browser rendering is claimed.

FOCUS a: retain the larger crest/shaft; check the live-map silhouette at working zoom.
FOCUS b: retain the flat dark pigments and sunburst; validate with the map's light ramp.
FOCUS c: play the new lunge, recoil and direct fall at 30 fps before art approval.

## Git handoff

Commit could not be made: creating `.git/worktrees/lane-6/index.lock` returned
Operation not permitted. All changes remain unstaged for the runner. Scoped
binary patch: `~/LegatumRuns/anim-pilot/oad/r5/spearman-0ad-r5.patch`. Commit
message with the required co-author line: `~/LegatumRuns/anim-pilot/oad/r5/commit-message.txt`.
`origin/master` is already an ancestor of HEAD. No fetch, push or master merge
was performed.
