# Spearman 0 A.D. — round 6, hit only

Primary asset: `tools/art/anim3d/units/spearman-0ad/spearman.glb`.
SHA-256: `84bf794f543fd4a1af2d1b9c2b48c89a6c52533a00d7803e553b49a22513f92c`.
**578,476 bytes; 2,536 triangles; 30 joints; one mesh, material and draw call;
1024 × 1024 embedded base-colour atlas; 1.9361 m figure height.**
The adjacent atlas is unchanged and the combined deliverables remain under 2 MB.

Only hit changed. Frozen comparison against approved round 5 SHA-256
`3c4e74a929d8e619874d45d5e3b2849d0e35d00d9675c1d1e4a9d17bfb5cf3ab` proves identical sampler data for
attack, death, walk and idle, and identical geometry, atlas, materials, skin,
team mask, hierarchy and attribution. No full rebuild or mesh re-export was
used. The r6 copies of approved movies/sheets are byte-identical to r5.

## Hit and measurement

25 sampled keys at 30 fps, duration 0.8 s. Frames 0–4 move the pelvis 15 cm
back and 6.5 cm down, with 14° spine plus 11° chest bend. The drop is 1.5 cm
stronger than the feedback's approximate 5 cm to retain small-scale readability.
The neck adds 9° follow and peaks at frame 5, one frame after the torso.
The carrying arm moves the rigid shield backward/outward. The spear tip dips;
a fixed-length arm solve lifts the actual grip 9 cm relative to the sinking
pose so the butt stays clear. The rear foot steps 15 cm back during frames 4–8,
with 4.5 cm swing clearance. Frames 8–24 ease back to idle-zero. All **87** hit
channels have first and last values exactly equal to the corresponding idle-zero
values. The skeleton root has zero translation or matrix change.

Acceptance on the **eight delivered 160 px RGBA sprite samples**, shared fixed
camera with idle, no moving crop/zoom:

| Measurement | Round 6 | Requirement |
| --- | ---: | ---: |
| Alpha-weighted centroid maximum pairwise distance | 11.4674 px | ≥8 px |
| Opaque-silhouette centroid maximum pairwise distance | 11.6116 px | ≥8 px |
| Top excursion, alpha ≥128 | 17 px | ≥8 px |

Opaque centroid/top use alpha ≥128; alpha-weighted centroid weights each pixel
by alpha/255. Both definitions are recorded to avoid an opaque-mask versus
alpha-weighting ambiguity. Full figure includes props. Lossless RGBA samples
are the measurement authority, not colour thresholds on H.264. Round 5's saved
samples under this opaque definition measured
1.3106 px centroid travel and
2 px top travel. This is consistent with the
reviewer's weak-reaction finding; codec/threshold differences explain small
numerical differences from their 1 px / 3 px report.

The first trial missed at 7.84 px centroid / 7 px top. A deeper drop and spear
dip exposed 8 cm of spear-butt penetration; lifting the grip anatomically and
correcting the shield's outward swing resolved it. Final 120 fps ground audit:
minimum hit height **-0.001253642 m**, within the existing 2 mm tolerance. This
is not a claim of mathematically zero penetration or general self-collision QA.

## Review files

All paths below are under `/Users/samcorcos/LegatumRuns/anim-pilot/review/3d-v2`:

- `spearman-0ad-r6-hit-160.mp4`: 160 × 160, H.264/yuv420p, 8 frames at 12 fps,
  three repetitions, 24 encoded frames, 2.000 s.
- `spearman-0ad-r6-hit-vs-idle-160.mp4`: 320 × 180, two 160 px panels plus labels,
  H.264/yuv420p, 108 frames at 12 fps, 9.000 s. Three comparison cycles: hit plays
  at 12 fps then holds the recovered idle-zero pose; idle completes its 12 frames
  at 4 fps. This preserves both game rates while showing three full repetitions.
- `spearman-0ad-r6-hit-contact.png`: all eight delivered hit samples.
- `spearman-0ad-r6-{idle,walk,attack,death}-160.mp4`,
  `spearman-0ad-r6-attack-fullrate.png`, `spearman-0ad-r6-readability-48.png`:
  copied byte-for-byte from the approved r5 evidence.
- `spearman-0ad-r6-hit-validation.json`: measurement, frozen-data and video receipts.

Native GLB hit timing is 0.8 s. The inherited 8-frame/12-fps sprite schedule
plays it in 0.667 s. Raw 30 fps hit frames and comparison masters are under
`/Users/samcorcos/LegatumRuns/anim-pilot/oad/r6/frames/`; all heavy outputs remain outside git.

Motion verdict: **hit now has a clearly different silhouette from idle**, with
an immediate recoil, outward shield jolt, spear dip and eased recovery. I
inspected the rendered poses and encoded-frame evidence. The numerical gate
passes, but the lead's playing-speed browser review is still required. Attack,
death, walk and idle retain the reviewer's round 5 pass; no new aesthetic claim
or changes are made for them. The 48 px accepted evidence is unchanged.

## Checks

- `validate_glb.py`: PASS (full output below).
- Khronos gltf-validator: PASS, 0 errors/warnings/infos/hints (output below).
- Repository-wide `tools/gates/art.py`: FAILED in the `render-sets.mjs` subprocess (the gate renders unrelated art sets through Chromium). No broad art-gate pass is claimed; host review remains necessary.
- Contract validator unit tests: 14/14 PASS.
- `check_combat.py`: PASS; 15 cm recoil, 6.5 cm drop, 25° spine/chest bend,
  frame-5 neck peak, 15 cm catching step, stationary root and idle recovery.
  The unchanged attack remains 13.246 cm drive / 0.319 mm ankle drift.
- `check_motion.py`: PASS for all five clips at 120 fps (809 samples total).
- `check_spear.py`: PASS, 169 death samples, no post-release crossings.
- Three.js r170 CPU GLTFLoader/AnimationMixer/team-mask/framing check: PASS.
  This is not a Chromium/WebGL pixel check.
- `kit/check_imports.py`: PASS, zero unresolved local imports.
- `node --check viewer/record.mjs`: PASS.
- `package_hit.py`: PASS, frozen-data/atlas equality, both centroid definitions,
  top excursion, ffprobe H.264/yuv420p/dimension/frame-count checks.

```json
{
  "valid": true,
  "glb": "/Users/samcorcos/LegatumRuns/anim-pilot/legatum/.claude/worktrees/lane-6/tools/art/anim3d/units/spearman-0ad/spearman.glb",
  "bytes": 578476,
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

## Host recorder handoff

The recorder now accepts `--round` and defaults to 6; framing/rendering behavior
is unchanged. Run **outside the sandbox**, from this worktree root:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs --round 6
```

It produces `spearman-0ad-r6-<clip>-viewer.mp4` and a receipt with the current
GLB hash. No browser capture was run in this sandbox. Prior viewer captures do
not certify this revised hit; regenerate and review at speed before approval.

Licence/provenance remain adjacent to the GLB and the exact required credit
is embedded. `git show 0ca57b93:LICENSE-ART` failed because that object is absent
from this checkout; the existing asset-specific CC BY-SA 3.0 licence and exact
0 A.D. source provenance were read and retained. Round 6 introduces no new
third-party inputs.

Next: lead regenerates viewer clips and judges this hit once beside idle.

Commit handoff: Git could not create `.git/worktrees/lane-6/index.lock` (Operation not permitted). Changes remain uncommitted for the runner. `oad/r6/commit-message.txt` contains the required co-author trailer; `oad/r6/spearman-r6.patch` includes the binary GLB and both new scripts. No push was attempted. `origin/master` is already an ancestor of HEAD.
