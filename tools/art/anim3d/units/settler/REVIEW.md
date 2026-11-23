# Settler driver round 2

**Not art-approved. No PASS marker.** The static painting remains in use.

The round-one host GPU pass succeeded: 175,038 bytes at Q85, forty actual
512/256 masters and an eight-second movie. Its evidence is preserved under
`masters/settler/driver-r1-gpu/` and `review/3d-v2/settler-driver-r1-gpu/`.

## Changes and visual verdict

A single frozen camera projection, orthographic visibility rays and tolerance for
short self-intersections recover the face, cloth pattern and staff grain previously
lost to material masks. Generated hidden fills, real thickness/bevels/straps, ten
AO/curvature bakes, product lights and automatic rest histogram grade remain.
The hood crown slopes toward the reference and the shawl joins front to back.
The stone is physically shaded so walking leaves no painted-foot ghost shadow.

Quaternius CC0 idle/walk/hit/death replace manual motion. Rest/roll calibration
preserves full rotations. The walk uses source timing (eight samples, 6 fps),
translation-only stance stabilization and native knee IK for the loaded carrier;
COPY_ROTATION retains the captured feet, checked by the audit. Complete linen
and olive robes follow pelvis/thigh/calf weights. Death is calibrated sideways,
includes library finger motion, releases the staff and holds its terminal sample.

At **256 px**, the face and painted surfaces are much closer, but the hood opening,
robe hem, sleeve shapes, small sandals and simpler base still differ visibly.
The current CPU silhouette IoU is 0.852668; this does not establish painting parity.
At **64 px**, staff, pack, hood and rust/olive/ivory identity read clearly; stance
and garment mass remain distinguishable. All five clips were inspected, including
the actual decoded movie. The fall is articulated instead of a rigid plank, but
raised arms and cloth settling remain awkward. Feet, sleeve joins and exposed
undersides still need art refinement. **Five clean clips and rest parity are not
claimed.** GPU64/512 review of this revision remains pending.

## Checks

- Cycles CPU8/256: plain/rest/details/poses, all 40 frames and front/top feet.
- Geometry audit: PASS, including 53 bones, body topology, zero rest hem key,
  evaluated first-frame geometry, native foot rotations, fixed base, exact loops,
  held death and ten bake hashes. Binding preserves rest vertices within 0.01 mm.
- Foot diagnostic: PASS; maximum stance residual 0.000007862 m relative to one
  virtual ground speed; maximum lateral ankle-to-toe offset 0.005097 m.
  This is an in-place walk, not a claim of stationary feet on a stationary disc.
- Preview pack plus independent validation: PASS, **182,384 bytes at Q85**,
  160px logical cells, all 8/8/10/4/10 samples, exact alpha restoration, trim offsets,
  transparent raw/export margins and identical decoded terminal death.
- Movie: PASS, H.264/yuv420p, 1600 x 352, 192 frames, eight seconds, five decoded
  atlas clips at 2x on cream. Representative decoded frames visually inspected.
- Python syntax: 17 files PASS. Bash syntax: two entry points PASS. Whitespace PASS.
- Working-tree hygiene: 19 changed text files, zero findings. Git commit was
  blocked by the sandbox index.lock permission; the runner must commit.
- GPU provenance gate rejects current CPU evidence as expected. New 512px GPU
  masters are not claimed; the previous actual GPU masters are preserved.

## GPU handoff

From the repository root, no arguments (ROUND supplied by the driver):

```sh
tools/art/anim3d/units/settler/gpu.sh
```

This renders every stage, regenerates clips, writes GPU512/64 masters and 256px
exports, renders front/top feet, audits, packs/validates the trimmed atlas and
writes `settler-round${ROUND}.mp4`. The transcript is now also teed to the driver's
log. A receipt requires current GPU evidence, including the feet diagnostic.
Review the GPU pixels before accepting the candidate. The script never writes PASS.
