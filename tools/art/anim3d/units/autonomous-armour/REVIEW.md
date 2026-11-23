# Autonomous armour — round 2 candidate

**Not art-approved; no PASS marker.** All current previews are Cycles CPU,
256 px, eight samples. Fresh 512 px GPU masters remain the host-side handoff.
The original painting remains in the game; this is an unwired animation candidate.

The broader hull/track gauge, shorter turret, lower camera and finished-surface
projection fit the painting more closely. Source pigment is now camera-only,
with visibility/facing masks and Standard/None display colour. Existing generated
olive fill and three actual AO/curvature bake pairs remain. Rotating gear excludes
misregistered source wheel images; neutralized generated pigment, live AO and
physical shading finish the wheels. The stone has a deeper rim and real bevel.

At 256 px, running-gear size/spacing, panel registration, antenna placement and
stone shading still differ visibly. Wheels remain too uniform, and the base is
flatter than the source. At 64 px it reads as the same autonomous tracked vehicle,
but its silhouette and surface richness remain distinguishable. Whole-image alpha
IoU improves from .90558 to .92617; above row 190 it improves from .88114 to .90816.
Those measurements do not establish artistic equivalence.

All five clips retain 8/8/10/4/10 samples. Wheel rotation now agrees with tread
travel, with matching physical distances and periodic geometry at the move seam.
The wider gauge and tread-ridge thickness enter contact calculations. The saved
scene audit measures contact at .239903–.240000 m against the .24 m stone top.
Death has a stronger turret cant, drooped gun, disabled optics and bent aerials;
the last two source frames are identical. Inspected all strips and decoded-video
contact frames: no obvious camera-edge clipping or base movement. Motion remains
restrained, and this inspection is not a full interpenetration solver.

Final CPU delivery:

- Forty 256 px clip masters, plus plain/rest/details/pose/top/front review masters.
- Trimmed 160 px atlas: **198,432 bytes at WebP quality 90**, exact decoded 8-bit alpha.
- Atlas validation passes counts, offsets, bounds, hashes, motion, held death and
  loop seams; seam/largest internal-step ratios are idle 1.00283 and move .98190.
- Saved-scene audit passes geometry, stationary base, rolling direction/distance,
  track closure/contact, safe scales and frozen UVs (maximum error .0000153 px).
- Round-two MP4: **1600×348, H.264/yuv420p, 240 frames, eight seconds**, all clips
  side by side on cream, reconstructed from trimmed atlas offsets.
- Eight Python files, two Bash entry points and diff whitespace pass syntax checks.
- GPU missing-input and interrupted-rebuild preflights fail as intended and record
  their failing stage. Independent GPU verification rejects CPU-labelled masters.

The executable, no-argument host entry point, from this checkout, is:

```sh
ROUND=2 tools/art/anim3d/units/autonomous-armour/gpu.sh
```

It audits, renders every stage serially on Cycles Metal GPU at 512 px / 96 samples,
retains 512/256 masters, fits the frozen rest grade, packs/validates the atlas,
encodes the decoded-atlas movie, then independently verifies stage provenance,
export hashes and video metadata. It retains a transcript, failure status and a
round-specific success receipt. Missing Metal fails instead of falling back to CPU.
A build-pending marker prevents a stopped model/clip rebuild from appearing ready.
No script writes PASS; the GPU images still need visual review against the painting.

Masters remain under `~/LegatumRuns/anim-pilot/masters/autonomous-armour/`, with
round-one CPU evidence preserved in `round1-cpu/` and this round in `round2-cpu/`.
Review images, movie, measurements, validation receipts and the honest step log
are under `~/LegatumRuns/anim-pilot/review/3d-v2/autonomous-armour-*`.

Commit attempt was blocked by sandbox denial of
`.git/worktrees/lane-2/index.lock`; the runner must commit these changes.
`origin/master` was verified as an ancestor of HEAD; no merge was needed.
The lead still owns the GPU render and visual/art gate before integration.
