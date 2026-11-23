# Rifleman round 1

Candidate only; no PASS. CPU Cycles, 256px, six samples. GPU final renders have
not run in the sandbox. The executable `gpu.sh` is the complete driver handoff;
it rebuilds and renders on Cycles Metal GPU at 512px, exports 512/256 masters,
re-packs/validates, and writes `rifleman-round${ROUND}.mp4`.

## Exists

- External `masters/rifleman/plain.blend`, `rifleman.blend`, and five editable
  clip blends: MPFB anatomy/53-bone rig, continuous weighted blue coat/sleeves/
  trousers, kepi, crossbelts and brass, rifle/lock/trigger/barrel/sling.
- Frozen rest-camera painting UVs, existing generated pigment fills for unseen
  surfaces, physical material response, actual AO/Pointiness bakes, one measured
  frozen histogram grade, cream stone and three aimed product lights.
- CPU 256px raw/graded frames, three clay viewpoints, textured/detail comparisons,
  four attack poses, all five PNG strips/animated WebPs, rest split/crossfade,
  top/front feet cycle and eight-second decoded-atlas movie in external review.
- Candidate `app/src/assets/units/anim/rifleman.webp` and version-2 JSON. Logical
  160px cells, exact alpha/offset reconstruction, 8/8/10/4/10 samples. Anchor is
  projected from the stationary stone contact center, not the canvas midpoint.

## Verification

- Atlas: **179,188 bytes at quality 90**, 1182 x 749 packed pixels. All 40 samples
  present; bounds, trim offsets, decoded alpha, camera margin, visible motion,
  identical held-death frames, source/clip/frame/grade hashes and byte cap pass.
- MP4: H.264, yuv420p, 1600 x 348, 240 frames, 30 fps, eight seconds.
- Rig: 53 bones, original MPFB anatomy retained, stationary stone, nonzero scales,
  CC0 donor actions for idle/move/hit/death, two-hand attachment positions pass.
  Maximum sampled wrist error 0.000000649m (positions only, not finger contact).
- Walk: max foot heading 13.44 degrees from travel direction; four measured
  planted intervals, max virtual-ground ankle drift 0.000000218m. Top/front
  screenshots inspected. This does not prove heel/toe contact or all-frame
  collision correctness; there is no complete skin/cloth collision solver.
- Python syntax: 6 files passed. Bash syntax: 2 files passed. Working-file
  hygiene: 13 files, zero findings. `git diff --check` passed.
- No Rust, rules, runtime UI or animation-loader changes. Commit-based art/browser
  gates remain for the lead: Git index.lock was denied, so the runner must commit.

## Honest art verdict

At 256px the blue uniform, kepi and diagonal rifle match the identity and inherit
much of the original brushwork, but the rest pose is visibly distinguishable.
The coat/shoulder and trouser silhouette remains narrower and more angular,
boot outlines pick up pale projected edge colors, the rifle stock/sling do not
register exactly, and the base ellipse/edge still differs. Newly exposed surfaces
and the hand/finger pose need better craft. The firing pose has wrist attachment
but is not yet a convincing shoulder-stock contact; the held death is visibly
stiff. These are visual issues despite the structural checks passing.

At 64px it reads as the same blue-coated rifleman, though thinner and less grounded
than the painting. Do not promote on file size or successful render alone.

Non-obvious fixes this round: rigid upper/lower trouser cylinders open at knees,
so bind a continuous surface across both bones; camera-projected illumination
needs camera-only pigment to avoid lighting the rest of the scene; do not rotate
feet after retargeting to repair an incorrect rest basis; freeze one grade for
all clips; copy the held death PNG rather than re-rendering stochastic noise.
