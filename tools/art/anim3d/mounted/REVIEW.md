# Horseman — resumed round 2, 22 November 2026

**Not approved; no PASS marker.** The painting is still visibly better.

At 256 px, the raised spear now clears the face, the base width is closer, the
horse's head registers more closely, and direct painting UVs reduce the earlier
misplaced colour streaks. The horse remains too slight and angular; its rear
leg shapes are awkward, the rider's face/helmet and cloth lack the painting's
craft, and the saddle/torso proportions still differ. Some tack appears rigid or
intersecting despite its measured endpoints. At 64 px it reads as an ancient
horseman, but its narrow silhouette and smaller horse do not match the painting.
Higher GPU samples cannot fix those anatomical differences.

Movement now uses the licensed source Walk cycle instead of the exaggerated
canter. Tail locks hang from the moving tail root with authored sway. Reins are
keyed between the bit and rider's hand. Attack/hit begin from the registered
rest; death lowers the spear during the fall, slumps the arms, releases the spear
and holds its final two frames. All five clips exist and were visually inspected
as strips. They are candidates, not a claim of five artistically clean clips.

## Verified CPU evidence

- Cycles CPU, 8 samples, gated Blender, three threads.
- Atlas: **199,202 bytes**, **quality 90**, **1038 x 756**; 40 trimmed 160 px
  frames in 8/8/10/4/10 clip rows. Full RGB; 32 alpha levels (max error 4/255).
- `mounted/validate.py`: zero findings. Exact reconstructed quantized alpha,
  rectangle bounds/non-overlap, frame counts, timing, motion, source hashes,
  clipping margins, quality/size cap and identical held terminal source pixels.
- `mounted/audit.py`: five clips, zero errors. True weighted geometry, saddle
  attachment, stationary base, ground bounds, four hoof-region support heights,
  both rein endpoints at every sample and held terminal geometry. This is not
  exhaustive collision detection.
- Review MP4: **240 frames, 8 seconds, 1600 x 348, H.264 yuv420p**, verified with
  ffprobe. All five clips reconstructed from trimmed rectangles at 2x on cream.
- Python syntax: all **22** mounted/unit Python files pass. Both mounted render
  and unit GPU shell scripts pass `bash -n`; `git diff --check` passes.

A premature pack attempt correctly refused mixed old/new grade hashes while the
render batch was still running. Full 8-bit alpha exceeded the cap at quality 75;
32-level alpha and clearing invisible RGB allowed quality 90 without dropping
frames. Validation then found one clipped death spear tip; its pose was fixed
and the final pack above passed. No failure was treated as approval.

## External evidence and GPU handoff

Under `~/LegatumRuns/anim-pilot/review/3d-v2/`:

- `horseman-f-restpose-compare.png`: painting, render, split and crossfade.
- `horseman-packed-review.png`: painting/render/decoded delivery at 256 and 64.
- `horseman-b-plain.png`, `horseman-c-textured-lit.png`, `horseman-c-details.png`,
  `horseman-d-rig-poses.png`, all five `horseman-e-*-strip.png` and `.webp`.
- `horseman-round2.mp4` and its ffprobe JSON.
- `horseman-{pack,validation,rig-audit}.json` and running `horseman-log.md`.

Editable packed masters remain in external `masters/horseman-3d/`. Current CPU
256 image sets and the 512 detail render are copied to `masters/horseman/`.
**The full 512 GPU master set has not run in this sandbox.** The required
executable handoff rebuilds current paint/animation, runs audits, renders every
stage using Cycles Metal, retains 512/256 masters, packs/validates delivery,
emits all review images and writes the driver's movie:

```sh
ROUND=2 tools/art/anim3d/units/horseman/gpu.sh
```

Run from the repo root with host Metal access. Default samples: 64. Reinspect the
GPU output; the current CPU byte count does not predict the GPU pack size. The
packer refuses delivery above 200,000 bytes at quality 75. The script never writes
PASS. No runtime loader or game rules changed, and the candidate remains unwired.

## Runner commit

The already-fetched `origin/master` is an ancestor of HEAD; no merge was needed.
Staging and committing were attempted, but the sandbox denied
`.git/worktrees/lane-6/index.lock`. Changes remain uncommitted for the runner.
The prepared external `review/3d-v2/horseman-commit-message.txt` contains the
requested co-author footer. Nothing was pushed and no PR was created.
