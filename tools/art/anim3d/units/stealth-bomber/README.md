# Stealth bomber — round 2 candidate

Closed cambered flying wing, raised centre section, recessed intake wells, convex
framed cockpit and carved support on one cream disc. Frozen camera projection
uses the original project painting; hidden composite surfaces use licensed generated
brushwork. Actual AO/Pointiness bakes drive gentle wear. No runtime wiring changes.

Round-one GPU evidence was inspected and preserved before editing. That GPU pass
succeeded. The new geometry recovers a broad, nearly horizontal wing behind the
painting's exact camera projection; round one was too steep in the top/side views.
A new ImageGen clean stone fill restores grain on the solid disc, retains the
original lower rim and removes the permanently painted support shadow. Intake
bevels are narrower. Three released bombs have real tail fins. The solid stand
falls continuously, and the deformed wreck settles on it instead of intersecting it.

## Review result

At 64 px the silhouette, scale and charcoal/cream identity match the painting.
At 256 px the stone and aircraft pigment are close, but the canopy remains softer,
the lower rim differs slightly and the crash still feels staged. Larger viewpoint
changes reveal approximate unseen paint. **No PASS marker: GPU round-two visual
acceptance remains pending.** Collision sampling is bounded, not a general exact
solver; the original mounting insertion is allowed only in the first death pose.

CPU Cycles, 12 samples: all 64 stage frames at actual 512 px, with verified 512 and
256 sets retained externally. All five clips total 40 frames (8/8/10/4/10).
The trimmed 160 px candidate is **163,190 bytes at Q90**. Rest alpha IoU is
0.96120; opaque-overlap RGB MAE is 5.86/255 (round-one GPU: 6.47). These are alignment
measurements, not art acceptance. CPU output is explicitly labelled.

External artifacts under `~/LegatumRuns/anim-pilot/`:

- `masters/stealth-bomber/`: editable plain/surface/painted and five clip blends,
  six 512 px bake maps, raw/graded 512 and 256 frames, grade, audit, build-source
  and pack receipts. Prior complete GPU evidence is in `driver-r1-gpu/`.
- `review/3d-v2/stealth-bomber-*`: plain, textured, details, rig poses, five strips
  and animated WebPs, rest/crossfade, top/front flight check, decoded atlas,
  `stealth-bomber-round2.mp4`, extracted video frames and CPU round-two receipt.
  The prior GPU reviews are in `stealth-bomber-round1-preserved/`.
- `assets/stealth-bomber/`: archived source, registered projection, grey fill and
  generated clean stone source/registered texture. Exact new generation prompt
  is in `stone-fill.prompt.txt`; hashes/licences are in `inputs.json`/`SOURCES.md`.

## Lead GPU handoff

From the repository root, with no positional arguments:

```sh
ROUND=2 tools/art/anim3d/units/stealth-bomber/gpu.sh
```

The executable script verifies the built master against its source scripts and
texture inputs, then uses gated plain `blender` calls for Metal Cycles GPU512 at
96 samples. It renders all nine stages sequentially, exports both master sizes,
audits the rig/geometry, rebuilds and validates the trimmed atlas, and writes the
eight-second H.264/yuv420p video and GPU receipt. It fails explicitly if Metal is
unavailable. It does not rebuild the model or write PASS. Motion-source signatures
prevent reusing old clip blends or frames after an animation edit.

To rebuild model/bakes, run `tools/art/anim3d/units/stealth-bomber/render.sh build`
from the repo root. Rebuilding invalidates downstream renders. Full commands and
trimmed JSON drawing semantics are in this family's `PLAYBOOK.md` chapter.

## Checks run

- Seven delivery regression tests passed, including stale build-input and motion
  rejection, bounded monotone grade, CPU rejection by the GPU gate, stale master
  rejection, missing-input GPU status and invalid video metadata rejection.
- Blender audit passed all five clips: closed principal volumes, broad flight
  plane, no tiny scales, finished projection surfaces, stationary disc, motion,
  loop closure, held death, triangle-interior disc clearance and evaluated-BVH
  stand/wing clearance. Terminal wing/stand gap: 0.01199 world units.
- Atlas validation passed all 40 counts, trim placement, exact reconstructed alpha,
  source/grade/motion hashes, gutters, no clipping, motion and held death.
- All 64 stage frames verified at 512 and 256 with raw/derived hashes.
- FFprobe verified H.264/yuv420p, 1600x348, 240 frames and eight seconds. Inspected
  all five strips, decoded atlas, rest/details and four extracted video frames.
- All unit Python sources parsed; shell syntax and `git diff --check` passed.

A correct rest silhouette and closed mesh can conceal a wrongly inclined wing:
always inspect top/side geometry. Terminal vertex-only contact missed collisions;
triangle interiors and the falling stand need separate checks. Rendering success
and these bounded checks do not establish visual acceptance.
