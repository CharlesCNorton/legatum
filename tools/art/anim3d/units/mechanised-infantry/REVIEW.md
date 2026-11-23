# Mechanised infantry — driver round 2

Review candidate, not art approval. No PASS marker. The static painting remains
in use; this branch does not change runtime wiring.

## Changes after the supplied GPU review

The incoming GPU pass succeeded: 182,722 bytes at Q85, GPU512 masters and the
round-1 review video. All incoming evidence is preserved externally under
`masters/mechanised-infantry/driver-r1-gpu/`. The empty driver log was caused by
redirection; gpu.sh now tees to both logs.

- Refit camera azimuth and near-wheel placement; derive opposite wheels from
  the near wheelbase and physical hull width. Added rear suspension armour.
- Original generated circular wheel albedo maps in axle coordinates onto real
  tires, hubs and tread. It rotates without rotating a painted ellipse or a
  directional source shadow; product lights supply the highlights.
- Original generated stone occlusion fill textures the real bevelled disc,
  with fresh contact AO and an alpha-safe pigment fallback. Reduced rim depth
  while retaining the support plane at z=.15.
- Refit the soldier's step, hands and rifle. Added continuous weighted folded
  sleeves, strap buckles and cloth on covered anatomical surfaces.
- Apply bevel/thickness geometry in bind space before frozen projection; compute
  visibility against evaluated meshes. Separate source pigment masks prevent a
  second soldier on the ramp and restrict human projection to its source region.
- Retain Quaternius idle/walk/hit/death and its foot rotations. A whole-character
  foreground displacement during the captured fall improves terminal visibility.
  Foot-angle checks now use the actual rig travel direction.
- Correct footwear binding from anatomical rest, and calibrate guard ankles
  before donor sampling. The first full audit caught an incorrect raised-boot
  pitch; the corrected binding passed the same unchanged 35-degree direction
  and 3mm contact gates. Audit receipts are bound to all five clip blends.
- Check every pinned external source at delivery, including the two new fills.
  Prompts, generation identities and licences are in this directory.

## Honest visual verdict

At 256px, wheels now have painted wear and the base has grain and contact tone;
these are substantial improvements over the flat round-1 materials. The soldier
is closer in size and stance. It remains distinguishable from the painting:
wheel sidewalls/tread are coarse, the equal-size wheels miss the painting's
perspective progression, and the soldier's face, supporting hand and clothing
are less precise. The stone is too uniformly warm. Alternate views still expose
awkward hull/cabin depth and attachment relationships; a fixed-camera pigment
match does not certify a mechanically coherent model.

At 64px, the APC-plus-one-dismount identity and silhouette are consistent with
the painting, but the darker wheel band and less distinct soldier remain visible.
No technical size, provenance or motion check is a visual approval.

Final CPU checks: 40 frames at 256px/eight samples; five clip blends; geometry
audit passed (maximum move foot yaw 27.531 degrees, lowest-sole error below
0.001mm). Trimmed 160px atlas is **186,040 bytes at Q85**, with exact reconstructed
alpha/offsets and held last two death frames. MP4 validation passed: 240 frames,
8.000 seconds, 1600x348, H.264/yuv420p; decoded .25s/.85s frames inspected.
Python compilation, shell syntax and whitespace checks passed. gpu.sh was
exercised here and correctly failed at Metal preflight with exit 1, leaving
the verified CPU outputs intact. Its logging uses a regular pipe, since shell
process substitution through /dev/fd is denied in this sandbox.

All five strips and top/front foot samples must be inspected after the GPU pass.
The foot audit checks direction and lowest-sole contact; it does not certify
horizontal slip, rifle grip or body/ramp collisions. The death pose remains a
priority for review. CPU256 at eight samples cannot certify GPU512 fine detail.

## Lead GPU pass

From this checkout's repository root:

```sh
ROUND=2 tools/art/anim3d/units/mechanised-infantry/gpu.sh
```

No arguments. It requires Metal, rebuilds/bakes every stage, renders Cycles GPU
512px at 64 samples, retains 512/256 masters, publishes b/c/details/d/e/f/g,
runs geometry/provenance checks, packs the trimmed 160px atlas at Q75 or above
and at most 200,000 bytes, validates offsets/alpha/held death, and encodes all
five clips side by side into an eight-second H.264/yuv420p round-2 MP4.
Missing Metal fails at preflight before replacing CPU render evidence. GPU
receipts explicitly retain `art_approved: false`.
