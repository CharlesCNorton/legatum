# Barbarian pikeman — driver round 3

Status: **candidate, not an art pass**. No PASS marker. Incoming round2 GPU
rendering succeeded at 184344 bytes/Q90; its movie, comparisons, editable master
and raw/graded 512px renders are preserved in `masters/barbarian-pikeman/driver-r2-gpu/`.

This revision keeps true MPFB anatomy, thick weighted garments, finished bevels,
cloth folds, real straps, six AO/Pointiness bakes, product lights and the fixed
17-quantile histogram grade. New original ImageGen pigment fills cover unseen
quilted linen, trousers, leather and skin. A registered clean stone plate colors
the solid disc with live AO. The disc's depth and position match the painting
more closely. The full helmet bowl now covers the measured skull; the inner
brim follows that correction. The baldric and upper sleeve fit are refined.

One shared pike axis registers the shaft endpoints to the painting and supplies
geometry, animation and independent audits. The rear boot's original guard
orientation now matches the painting. Camera-plane boot compression was rejected
because it distorted the walking toe. Quaternius CC0 library foot rotations remain
unchanged after retargeting. Sparse source pose channels reset before sampling.
The original attack now has a readable thrust; its wind-up was reduced after the
validator caught the tip at the top boundary. All frame counts remain 8/8/10/4/10.

At **256px**, the shaft/base alignment and front painting are closer, but the
face, helmet contour, upper-sleeve patch, boot shape and lower-arm silhouette
remain visibly different. Revealed shoulder/back surfaces have richer pigment
but still lack the painting's authored finish. At **64px**, the buff/red figure,
kettle helmet and long diagonal pike read as the same unit; rest is still
distinguishable. The thrust reads better. The fall remains stiff through the
raised-leg transition. This does not yet meet the hard-to-distinguish art bar.

Final checks: Cycles CPU12/256, all ten review stages, 40 animation samples,
16 front/top foot views; scene, packed-source hashes, camera registration and
40-frame rig audit pass. Maximum wrist/shaft distance is 11.34cm; this measures
wrists, not palm contact. Sampled toe-stance residual is 0.000001062m and maximum
forward yaw 1.73 degrees; neither proves complete heel/cloth collision clearance.
The 160px trimmed atlas is **174990 bytes at Q90**, with lossless alpha. All clip
counts, trim reconstruction, margins, motion, hashes and identical decoded held
death pass. The movie is H.264/yuv420p, 1600x348, 240 frames, 8.000 seconds.
All 18 Python files, two shell scripts, asset JSON and whitespace checks pass.
All five strips, native rest/details, feet and decoded movie frames were inspected.

Metal preflight rejects the unavailable device in this sandbox; the GPU receipt
rejects CPU previews. Round3 GPU512/256 rendering and visual review remain pending:

```sh
ROUND=3 tools/art/anim3d/units/barbarian-pikeman/gpu.sh
```

The executable no-argument handoff verifies packed sources and device, rebuilds
clips, audits, renders all stages at GPU512, retains 512/256 masters, grades,
trims, validates and encodes the eight-second movie. It writes a fresh receipt
only on success and never writes the art PASS marker. No Rust or runtime UI changed.
