# Phalangite round 2

Candidate, not approved for runtime use. No `phalangite-PASS` marker: painting
parity and clean finger/equipment contact have not been established.

The editable scene is `~/LegatumRuns/anim-pilot/masters/phalangite/phalangite.blend`.
`plain.blend` preserves the original morphable MPFB source; `fitted-plain.blend`
contains the revised full-depth fit; five articulated scenes live in `clips/`.
All masters, bakes, source textures, raw frames and provenance remain outside git.
Round-1 blend checkpoints and review sheets are preserved externally.

## Changes and visual verdict

Round 2 fits the real arm/sleeve, helmet, complete shield, greave and sandal
geometry through inverse skin transforms. The MPFB macro mix is frozen on the
working copy, preserving all 19,158 vertices, original skin weights and 53 bones.
Rigid thickness/bevels are finished before frozen UV projection. Camera-only
painted pigment avoids lighting the source illumination twice, while generated
linen/bronze fills, real AO/curvature and product lights remain. Short nape locks
have round physical volume. The stone has a warm top, darker rim and live contact
shade, without painted feet. A source-paint exclusion removes the duplicate spear
line from the armour. One automatic rest grade is reused across all clips.

At 256 px, the arm volume, shield wear, low helmet and cream stone are substantially
closer than round 1. The face, shoulder contour, hands, greaves and stone rim are
still simpler or differently shaped than the painting. At 64 px, the same unit
reads clearly, but the pose and highlights remain distinguishable. A histogram
match is not art approval, and the unchanged camera plus local geometry fitting
is not an exact camera solution.

Death folds both legs before grounding, removing the old ankle-supported hover.
The five clips remain authored skeletal animation, with modelled cloth folds.
The thrust is restrained and hands need further work: the existing palm proxy
reports up to 7.1 cm error and does not measure fitted finger contact. Shield/arm
and cloth/skin intersections are not exhaustively checked. No cloth simulation
or new motion capture is claimed.

## Delivery and verification

The executable, no-argument host entry point is:

```sh
ROUND=2 tools/art/anim3d/units/phalangite/gpu.sh
```

It regenerates clips, audits, renders every stage at Cycles Metal/512, verifies
all 48 GPU masters and their 256px copies, packs/validates the trimmed 160px atlas,
and encodes the decoded atlas into an eight-second five-column review movie.
It records a transcript, failure status and round-specific completion receipt;
that receipt explicitly leaves visual approval false. Metal rendering cannot run
inside this sandbox. CPU-labelled files are previews, even when 512px.

Bicubic reduction preserves lossless alpha. Validation reconstructs all 40 frames
at their trim offsets and compares alpha byte-for-byte; it checks hashes, bounds,
padding, frame counts, timing, size and Q75 floor. Identical adjacent samples share
an atlas rectangle, making the held death identical in decoded RGB as well.
The geometry audit verifies native topology, finished-surface frozen UVs,
camera-only pigment, six actual bake images, source hashes, stationary base,
loop boundary poses and held death. It is not a full collision solver.

GPU missing-input and CPU-master rejection checks passed. Python/Bash syntax and
whitespace checks passed. Fresh GPU output still needs visual review before PASS.

## Recorded final CPU checks

- All 48 stage/master PNGs at 512 px and 48 matching 256 px copies exist;
  all 40 clip frames use Cycles CPU, 512 px, 8 samples.
- Trimmed atlas: **181,278 bytes at Q90**, 1600×800, 160px logical cells,
  unchanged 8/8/10/4/10 playback samples. Full decoded-alpha, offset, padding,
  source/frame/grade hash, motion and held-death validation passed.
- Final saved-scene audit passed, including finished-surface UV alignment,
  original topology/weights, stationary base and root transforms at loop/hold.
- MP4: **H.264/yuv420p, 1600×360, 192 frames, 8 seconds**; ffprobe passed.
  Decoded movie contact frames and all five PNG strips were visually inspected.
- Pinned painting/generated-fill hashes, eight Python syntax checks, both Bash
  scripts and whitespace checks passed. GPU preflight rejection checks passed.
- Rest silhouette IoU at alpha128: 0.802801. This does not establish art parity.

No Rust, WASM or UI code changed. GPU rendering and final art acceptance remain
outstanding; neither CPU validation nor this review creates a PASS marker.

Commit creation was attempted with the required co-author trailer, but the sandbox
denied `.git/worktrees/lane-14/index.lock`. Changes remain for the runner to commit.
