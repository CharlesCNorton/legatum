# Stealth fighter — round 1 candidate

Original true-3D, bevelled stealth aircraft with a gold canopy, twin fins,
recessed intakes, separate exhausts and articulated stabilizers. The source
painting is registered onto finished surfaces; hidden surfaces use a licensed
generated metal fill. The cream stone disc and curved support retain the
painting's composition. Five clips contain 8/8/10/4/10 frames.

From the repository root:

```sh
tools/art/anim3d/units/stealth-fighter/render.sh build
# Low-cost inspection first; each stage publishes its own review.
RESOLUTION=256 SAMPLES=8 tools/art/anim3d/units/stealth-fighter/render.sh c
source tools/art/anim3d/env.sh
RESOLUTION=256 "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/stealth-fighter/deliver.py c
# Complete final GPU pass on the host, including all reviews and video:
ROUND=1 tools/art/anim3d/units/stealth-fighter/gpu.sh
```

GPU handoff explicitly selects Metal Cycles and never silently falls back to
CPU. It uses saved masters, renders every stage at native 512, retains 256
copies, packs/validates the 160px trimmed candidate, checks geometry and writes
`stealth-fighter-round${ROUND}.mp4`. The movie reconstructs the decoded atlas
using trim offsets and the fixed anchor. It is eight seconds, H.264/yuv420p,
1600x348, 240 frames. Host logs, status and hash-bound receipt are in the review
folder. GPU visual review is outstanding.

Masters: `$ANIM_ROOT/masters/stealth-fighter/`. Reviews and running log:
`$ANIM_ROOT/review/3d-v2/stealth-fighter-*`. Sources/licences are in `SOURCES.md`;
full source and derived image hashes in `inputs.json`. No masters in git.

`deliver.py validate` checks the candidate's hashes, all 40 sprites, alpha,
trim offsets, motion, transparent gutters and exact decoded terminal hold.
Identical frames share a rectangle, preventing lossy-compression flicker.
`audit.py` checks closed manifold principal meshes, nonzero dimensions,
finished projection surfaces, control-pivot placement, loop closure, stationary
base and physical wreck contact. Five unittest checks exercise stale-source
rejection, the GPU boundary, grade bounds, failed preflight and movie metadata.

At 64px the silhouette, flight attitude and colour identity match the painting
well. At 256px the projection is close, but bevel/engine joins remain coarse in
alternate views, fine stone grain is weaker and the projected lighting remains
attached to moving surfaces. The small attack projectile is subdued; the crash
reads as a controlled descent with a bent wing more than a violent impact.
These are round-2 targets, not painting-parity approval. No PASS marker and no
app runtime change.
