# Horseman — round 3, 23 November 2026

**Not art-approved; no PASS marker.** The painting remains visibly better at
256 px. At 64 px the class reads, but the horse and rider silhouette differs.

Finished horse, cloth and helmet surfaces now precede frozen projection UVs.
Static MPFB macro shapes are frozen while retaining native anatomy and weights.
Camera-only painted illumination preserves source brushwork without turning it
into scene lighting. Existing generated fills and scanned/baked physical surfaces
remain on unseen areas. Spatial masks retain skin highlights and dark linen folds.
The shoulder/seat fit, swept solid crest fibres, fuller curved tail, solid beveled
baldric and cream stone are revised. The original round strap doubled the painted
strap; the replacement ribbon is ray-fitted to the posed shirt.

The walk no longer floats above the disc: grounding now lowers hovering soles as
well as raising penetration. All eight walk samples have an actual lowest hoof
at **.112 m**, and the audit rejects samples above .135 m. Attack retains authored
gallop suspension. Reins still join the bit to the hand, and death holds its last
two source samples. These checks are not exhaustive collision detection.

## Verified CPU delivery

- Cycles CPU, 12 samples, three threads through the shared Blender gate.
- All 40 frames: idle 8, move 8, attack 10, hit 4, death 10.
- Trimmed 160 px atlas: **172,900 bytes, quality 85**, 1057 x 756.
  Quality 90 was 200,410 bytes, so the packer selected Q85. Full RGB, 32 alpha
  levels, maximum 4/255 alpha error; no dropped frames.
- Atlas validator: **zero findings**; source hashes, reconstructed quantized
  alpha, rectangle bounds, timing, motion, margins and terminal hold pass.
- Geometry audit: **five clips, zero errors**, including the tighter walk support.
- MP4: **8 seconds, 240 frames, 1600 x 348, H.264 yuv420p**. All five decoded
  clips at 2x on cream. Inspected native 256/64 sheets, every clip strip,
  decoded-atlas comparison and sampled movie contact frames.
- Four master-gate regression tests pass. Missing-input preflight records a
  failure before Blender; the GPU gate correctly rejects current CPU images.
- 26 Python files parse; both shell scripts pass bash -n; whitespace checks pass.

The first premature packing attempt correctly rejected mixed old/new hashes.
Its old-atlas movie was moved out of review; the final movie above was regenerated
only after the complete, validated pack. Rest silhouette IoU: **.7378 at 256** and
**.7445 at 64**. These measurements do not establish painted parity.

## Remaining visual gaps

At 256 px the horse is too slender and angular, the rear legs are awkward, and
the rider's face, crest orientation, drapery and saddle proportions remain unlike
the painting. The tail has more mass but reads as a dark bundle rather than fine
painted hair. Some tack and falling-body intersections still need visual work.
At 64 px the figure is recognizable but narrower and stiffer than the painting.
All five clips exist; they are not yet five artistically clean, approved clips.
Higher GPU sample counts cannot fix these geometry and pose differences.

## Evidence and GPU handoff

Current review: `~/LegatumRuns/anim-pilot/review/3d-v2/horseman-*`, including
`horseman-f-restpose-compare.png`, `horseman-packed-review.png`, and
`horseman-round3.mp4`. Prior evidence is in `masters/horseman/round2-cpu`;
this round's CPU evidence is archived in `masters/horseman/round3-cpu`.
Editable packed blends remain in `masters/horseman-3d`. Current image sets are
256 px CPU previews plus an actual 512 px CPU detail image. **A complete fresh
512/256 GPU pass remains pending; no GPU completion receipt or art PASS exists.**

From this checkout, on the host with Metal:

```sh
ROUND=3 tools/art/anim3d/units/horseman/gpu.sh
```

The executable takes no arguments. It verifies Metal, rebuilds paint and all
clips, audits, renders every stage at GPU512/64 samples, exports actual 512/256
masters, verifies current blend/grade/pixel hashes, packs and validates, then
encodes the round MP4. Its transcript and status retain failure evidence; a
completion receipt is written only after all stages succeed and leaves art
approval false. It never writes PASS. The game still uses its painting.

Non-obvious findings: finish surfaces before UV capture; pale skin and dark
cloth cannot be selected reliably with a hue threshold; a source-painted strap
and mismatched physical strap create a double line; grounding needs both signs.

## Runner commit

The already-fetched origin/master is an ancestor of HEAD. Git staging failed
creating `.git/worktrees/lane-6/index.lock` with Operation not permitted. Changes
remain uncommitted for the runner; the external `horseman-commit-message.txt`
contains the requested co-author footer. Nothing was pushed or merged.
