# Round 1 evidence

Candidate only; no PASS marker. The sculpted MPFB body and kit are true 3D, with
53 bones and five authored clips. Camera-projected paint, generated hidden fur,
real 256 px AO/curvature bakes and a fixed painting-derived grade are saved in the
editable external masters. No runtime code is changed.

Technical checks passed on the CPU candidate:

- 40 frames: idle 8, move 8, attack 10, hit 4, death 10; actual 512 px renders and
  retained 256 px masters. All output frames have transparent margins.
- Trimmed 160 px atlas: **183,202 bytes, WebP quality 80**. Rectangles, offsets,
  anchors, alpha, frame counts, source/clip/grade/frame hashes, actual motion,
  loop endpoints and held death were checked. A deliberately stale death render
  was rejected before repacking.
- Blender audit: real MPFB topology, 53 bones, six actual bake maps, positive
  scales, fixed cream base, moving skeletons, closed idle/move loops and held death.
- Video: **8.000 seconds, 240 frames, 1600 × 348, H.264, yuv420p**; all five clips
  side by side on cream, decoded from the trimmed atlas at 2x scale.
- Python parsing, shell syntax and whitespace checks passed. GPU rendering was
  not run in the sandbox; the complete lead pass is `gpu.sh`.

Visual verdict: at 64 px the fur, horn, red scarf and lookout pose identify the
scout, but the silhouette is narrower and the crouch differs from the painting.
At 256 px it is clearly below the painting: face/arm/waist registration is off,
parts of the boots sample the painting's base colour, cloth and skin seams are
visible, and the axe draw and crouched shuffle need more convincing articulation.
Death is contained and held but still stiff; the cloak can intersect the base.
GPU lighting will not fix those geometry/projection problems. Continue iteration.

Review files and the honest step log are in `review/3d-v2/`, prefixed
`barbarian-scout-`. The first-pass evidence is retained in
`barbarian-scout-first-pass/`. The latest rest comparison includes the original,
render, half split and crossfade; the MP4 is `barbarian-scout-round1.mp4`.

Delivery boundary: Git staging/commit and merging `origin/master` were blocked by
sandbox denial of `.git/worktrees/lane-21/index.lock` and `ORIG_HEAD.lock`. All
changes are left uncommitted for the runner. The two newer upstream commits are
browser-test/CI changes. The runner must merge them and then run the requested
determinism and pin tests; those post-merge tests were not run against an
unperformed merge. No push or pull request was attempted.
