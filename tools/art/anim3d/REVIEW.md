# Spearman review — round 8

**Not PASS.** At 256 px the hand and shoulder contour are slightly closer,
the crest ends higher beside the cheek, and the cream stone is paler with a
smoother bevel and softer shadows. Cheek shape, sandals, stance, shield edge
and base shading still distinguish the render from the painting. At 64 px it
reads as the same spearman, with a remaining difference in stance and base.
All evidence from this iteration is explicitly labelled CPU preview.

The requested round-7 GPU log is absent, and supplied images and movie are
CPU-labelled. No GPU success or failure was inferred. The received evidence is
preserved under `review/3d-v2/spearman-round7-preserved/`.

## Changes

The frozen rest-camera projection, original MPFB body and skin weights, real
beveled equipment, straps, cloth folds, and image-generated unseen fills remain.
Inverse-skin fitting expands the actual knuckle stack and adjusts the shoulder;
real crest volume now ends above the cheek and extends farther forward.

The stone has a 22mm five-segment bevel, restrained scan bump and finer pigment
variation. An elevated broad area key softens the previous diagonal shadows.
A small linear pigment lift brings the rendered cream closer to source samples.
Raw/graded pixel comparisons showed that the existing automatic grade improves
the figure overall; that single rest-fitted grade remains fixed for all clips.

The scene check verifies the new finish in addition to topology, original rig,
camera-only pigment, contact plane and actual shield relief clearance. GPU
handoff defaults to round 8 and logs the checkout revision, dirty input paths
and resolved Blender gate, alongside its existing stage/failure receipts.

## Verification

- CPU Cycles rest and all 40 frames: **256 px / 12 samples**. Detail inspection
  render: **512 px / 12 samples**, still CPU. Final GPU masters remain pending.
- Trimmed 160 px atlas: **181,968 bytes, quality 80**, all 8/8/10/4/10
  frames retained. SHA256 `33742c6d2b0128c92207db9649bf90d6d41d27955b490f55ea703feaad256218`.
- Independent decoded validation passes current hashes, clip timing, exact
  reconstructed alpha, offsets, gutters, bounds, visible motion, byte/quality
  limits and byte-identical held-death PNGs.
- Full saved-rig audit: **40 samples, zero findings**, including guard arm
  transitions, hand/shaft attachment, spear crossings, camera and floor bounds.
- Saved-scene checks pass: **19,158 body vertices / 53 bones**, 314 camera-gated
  painting materials, 280 unseen fills, all 12 raised shield rays clear.
- **2 pipeline regression tests pass**. **26 Python / 3 Bash / 2 JSON syntax checks pass**; **34-file hygiene**
  reports zero findings, and diff whitespace passes. Exact report:
  `spearman-round8-checks.json`.
- Movie verified: **H.264 yuv420p, 1600 × 352, 192 frames, 24 fps, 8 seconds**;
  all five decoded clips run simultaneously on cream.
- Rest diagnostic silhouette IoU: **0.8862**, versus round 7 **0.8839**;
  RGB union errors: **21.61 / 26.82 / 27.92**, versus **22.25 / 27.27 / 28.60**.
  These small improvements do not establish artistic equivalence.
- Opened clay, rest split/crossfade, details, rig poses, all five strips, decoded
  atlas and extracted round-8 movie frames. Motion remains readable, but raised
  arm/lifted foot projection stretch and pale fallen-pose seams remain.

No `spearman-PASS` was written.

## GPU handoff

From the repository root on the GPU host:

```sh
ROUND=8 tools/art/anim3d/units/spearman/gpu.sh
```

This executable checks Cycles GPU/Metal, rebuilds the projection and all five
clips, renders every stage and 40 frames at 512 px / 64 samples, fits one grade,
exports genuine 512/256 masters, packs and independently validates the trimmed
160 px atlas, and encodes all five decoded clips side by side for eight seconds.
It writes `spearman-round8.mp4`, all review images including the rest comparison,
`gpu-logs-spearman-r8.log` and a stage/status receipt. It never writes PASS.
Final GPU rendering and visual review remain required.

Masters remain outside git. No Rust, rules, WASM or UI runtime changed; the
game still displays its painting. No push, PR or master merge is part of this task.

Git staging failed because the sandbox denied the worktree `index.lock`.
Seven files remain for the runner to commit with the requested gpt-6-astra
co-author trailer. The branch already contains available `origin/master`.
