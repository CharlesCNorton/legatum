# Spearman 0 A.D. round 2 — real-time GLB

Primary asset: `tools/art/anim3d/units/spearman-0ad/spearman.glb`.
SHA-256: `4d798919cf0b7358c244204283d6a3d1fd279b7e6c1d9abb3d46837647a20277`.

Verdict: technically ready for map integration and a useful game-motion candidate.
The bronze / crimson / sunburst identity is readable, props stay rigid, and the
native hoplite gait is substantially more credible than a manually posed body.
This is still a restrained low-poly flat-pigment pass, not final Civ 6-quality
painted art. The face and armour need more deliberate pigment detail, the thrust
could read more forcefully at the map angle, and the corrected fall needs the
lead's motion review. A passing contract is not art approval.

## What changed

- One self-contained GLB: **2,536 triangles, 29 joints, one skinned mesh,
  487,992 bytes**, figure **1.8528 m** including crest. All five clips at 30 fps.
- Added pinned native Corinthian helmet, crest and skinned hoplite cloak. Retained
  native body weights; removed unused helpers and normalized the strongest four
  influences. Spear → weapon_R, aspis → shield_arm, helmet → head; rigid props.
- One **1024 × 1024** RGB albedo atlas (20,346 bytes as a separate PNG),
  embedded in the GLB. Bronze, crimson, linen, leather, eye slots and twelve-ray
  sunburst. Flat pigment only: no baked shading/AO, normals or emission projection.
- `team` material covers crest, shield rim and cloak trim. Neutral atlas samples
  allow arbitrary runtime tint; default factor is crimson.
- Native attack_melee_05, death_b, idle_relax_01 and walk_relax; authored additive
  hit. Closed looping poses and matched the incoming tangent near the seam.
  Corrected weapon/shield orientation for floor clearance. Death's end is seated
  on the crest and shield; the body can sit roughly 3 cm above the plane there.
- Geometry is inside one fixed camera across all clips. Final sampled floor
  minima are {"attack": -2.2e-06, "death": -3.3e-06, "hit": -1e-07, "idle": -2e-07, "walk": -8e-07} m:
  no material ground penetration; negatives are floating-point noise.
- Sprites are rendered from this exact GLB, with direct GLB transforms for rigid
  props to avoid Blender 5.3's bone-parent re-import discrepancy. No alternate
  sprite-only model or pose. Camera pitch is 13.613°, matching the established
  preset; azimuth exposes the spear arm. Orthographic scale is 3.2271 m.

## Honest clip review

| Clip | Verdict |
| --- | --- |
| idle | Quiet breathing and small weight shifts. Upright spear and broad shield read well. Endpoints agree numerically; subtle motion is easy to miss at 160 px. |
| walk | Native alternating gait and cloak swing read as walking. Feet remain distinct in the sampled review. The in-place cycle expects the map to translate the actor; root-motion distance is not supplied. The 6 fps legacy sprite review runs more slowly than the native GLB. |
| attack | _05 gives a visible raised arm, forward jab and recovery. The shield does not fully conceal the arm, but the camera foreshortens the thrust and the shield dominates the silhouette. This is usable, not an emphatic final combat read. |
| hit | Short torso/head recoil with rigid shield movement and recovery. It reads as a hit at 160 px; secondary cloth movement is limited because this is an additive procedural reaction. |
| death | Native side collapse, rigid carried props, full spear and body stay framed. Socket clearance corrections prevent ground intersections. The shield settles unusually flat and the last body pose is supported by the crest; this deserves art-director review. |

The static diagnostics and **decoded H.264 frame sequences** were visually
inspected. Continuous browser playback was **not** observed in the sandbox.
The three.js CPU check loaded and evaluated all clips, checked actual motion,
loop endpoints, hierarchy and tint access; it does not establish browser pixels.

## Review outputs

All five exist, H.264, yuv420p, 160 × 160, cream background, three repeats:

| File | Unique frames | Game fps | Encoded frames | Duration |
| --- | ---: | ---: | ---: | ---: |
| spearman-0ad-r2-idle-160.mp4 | 12 | 4 | 36 | 9.000 s |
| spearman-0ad-r2-walk-160.mp4 | 16 | 6 | 48 | 8.000 s |
| spearman-0ad-r2-attack-160.mp4 | 18 | 14 | 54 | 3.857 s |
| spearman-0ad-r2-hit-160.mp4 | 8 | 12 | 24 | 2.000 s |
| spearman-0ad-r2-death-160.mp4 | 16 | 4 | 48 | 12.000 s |

Full-rate attack: `spearman-0ad-r2-attack-fullrate.png` (all 36 native samples,
labelled at 30 fps). Decoded review: `spearman-0ad-r2-decoded-review.png`.
Stream evidence: `spearman-0ad-r2-video-validation.json`.

Timing caveat: the requested larger sprite counts at the existing game rates
change apparent speed relative to the GLB (especially walk and death). The GLB
has native durations: idle 2.0 s, walk 1.333 s, attack 1.167 s, hit 0.8 s,
death 1.933 s. The viewer preserves those timings.

## Browser handoff

The static three.js page is `tools/art/anim3d/viewer/index.html`, pinned to
three.js 0.170.0. It supports clip selection, orbit, map camera, pause and tint.
The recorder samples exact times at 30 fps and makes three-repeat 640 px MP4s.

From this worktree root, **outside the sandbox**:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs
```

Expected outputs (not yet generated):
`~/LegatumRuns/anim-pilot/review/3d-v2/spearman-0ad-r2-{idle,walk,attack,hit,death}-viewer.mp4`.
The host needs Chromium available to Playwright 1.56.1. The recorder starts its
own loopback server. No account, build step, deployment or public hosting.

## Verification

- Custom contract validator: **PASS**, output below.
- Khronos gltf-validator 2.0.0-dev.3.10: **0 errors, 0 warnings, 0 infos, 0 hints**.
- Contract corruption regression suite: **9/9 passed**.
- three.js r170 GLTFLoader / AnimationMixer CPU smoke: **PASS**, all five clips.
- `kit/check_imports.py`: **0 unresolved local imports**, full anim3d tree.
- `node --check`: viewer, recorder, CPU check and Khronos wrapper **all passed**.
- `ffprobe`: all five encoded movies verified for codec, dimensions, pixel format,
  fps and exact three-repeat frame count. Decoded samples inspected.
- Broader `tools/gates/check.py HEAD --base origin/master --checks-only`: **FAIL**. Hygiene flags four pre-existing matrix `@` expressions in `units/spearman/donor_motion.py` and `round12c_review.py` as email addresses; the shared art distinctness renderer also fails. Public-claims passes. These failures are outside this unit and were not silently waived.
- `git diff --check`: **PASS**. No Rust or app runtime code changed; no Cargo/app
  build suites run for this isolated art/tooling task.
- Source feedback file was present but **empty**. Referenced licence commit
  `0ca57b93` was unavailable locally; the retained upstream licence and Sam's
  explicit approval are documented beside the GLB. No git fetch was performed.

```json
{
  "valid": true,
  "glb": "/Users/samcorcos/LegatumRuns/anim-pilot/legatum/.claude/worktrees/lane-6/tools/art/anim3d/units/spearman-0ad/spearman.glb",
  "bytes": 487992,
  "triangles": 2536,
  "joints": 29,
  "skinned_meshes": 1,
  "atlas_px": [
    1024,
    1024
  ],
  "figure_height_m": 1.8528,
  "feet_centre_m": [
    0.0178,
    0.0168,
    0.0059
  ],
  "team_meshes": [
    "crest",
    "aspis",
    "body"
  ],
  "clips": {
    "attack": {
      "duration_s": 1.166667,
      "fps": 30,
      "loop_endpoint_max_error": 0
    },
    "death": {
      "duration_s": 1.933333,
      "fps": 30,
      "loop_endpoint_max_error": 1.4234886
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

Khronos output:

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

Heavy inputs/master/frames are under `~/LegatumRuns/anim-pilot/oad/` and `oad/r2/`.
The GLB, PNG, provenance, licence and reproducible scripts are small enough for git.
The first valid GLB checkpoint was committed by the runner as **1fd17e09** after
this sandbox's commit attempt failed on index.lock. Final refinements and tools
remain for the runner to commit; commit text is `oad/r2/commit-message.txt`.
No push or merge was performed by this lane.

## Next

1. Run the host recorder and inspect continuous native-rate motion plus team tint
   and arbitrary orbit angles in the actual map shader.
2. Judge the attack's foreshortened thrust and death's shield/crest-supported settle.
3. Refine helmet/armour pigment and cloth detail while retaining a flat albedo.

FOCUS a: preserve the proven native body/rig; inspect final fall contact.
FOCUS b: richer intentional armour/face pigment without baked light.
FOCUS c: stronger thrust read and native-rate browser review.
