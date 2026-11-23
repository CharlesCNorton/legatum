# Archer — driver round 2

Art candidate, not approved or connected to the runtime. No PASS marker.
At 256 px the rounded drawing elbow, shallower warm stone ellipse and textured
rim are closer to the painting. The face/gaze, shoulder drape and crest still
differ. At 64 px the unit reads as the same archer but remains distinguishable.
The rest silhouette overlap is approximately .808 (prior .790); this measures
shape, not art quality.

The existing fixed camera projects the original painting onto finished, real
3D surfaces. Generated hidden-surface fills, actual AO/curvature, beveled straps,
thick cloth folds, product lighting and one automatic rest histogram grade
remain. The tunic and borders now deform with pelvis/thigh weights, inverse-bound
in the painted pose so projection registration remains exact. Cloth is modeled,
not simulated; shoulder and underside reveals still need refinement.

Feedback 23 replaces the previous partial CMU gait and authored hit/death with
CC0 Quaternius Idle_Loop, Walk_Loop, Hit_Chest and Death01. Rest/roll-compensated
Blender constraints transfer rotations; carrying arms layer open idle motion.
Only the bow attack is hand-authored. There are no post-retarget foot rotation
patches. Root corrections of at most 2.91 cm regularize sampled stance against
virtual travel; the measured toe residual is below .002 mm. This is a sampled
contact check, not a complete heel/toe or cloth collision solver. The front/top
feet sheet exposes all eight samples.

The fall blends out of the painted guard, turns diagonally, stays framed and
holds its final sample. Its quiver-supported landing and exposed shoulders
remain less convincing than the painting; it is not a five-clean-clips sign-off.

The lead's preceding GPU pass succeeded: forty real 512/256 masters, 190,436-byte
Q90 atlas, validated eight-second H.264 movie. That evidence is archived under
`masters/archer/driver-r1-gpu/` and `review/3d-v2/archer-driver-r1-gpu/`.
Current CPU previews supersede the gallery, not that historical GPU receipt.
Current reports are `archer-audit.json`, `archer-foot-contact.json`,
`archer-comparison.json`, `archer-validation.json` and `archer-video.json`.

Current checks: all forty CPU256/24 frames plus a real CPU512/24 detail master;
scene/projection/foot audit PASS; trimmed atlas **193,944 bytes, Q90,
1217×750**, all forty 160 px samples; full decoded
validation PASS; H.264/yuv420p 1600×348, 240 frames/eight seconds PASS.
Python syntax (16 files), Bash syntax (3 scripts) and whitespace checks pass.
GPU validation correctly rejects the current CPU preview.

Run the complete new host pass from the repository root:

```sh
ROUND=2 tools/art/anim3d/units/archer/gpu.sh
```

It audits, renders every stage plus feet at Cycles Metal 512/64, retains actual
512/256 masters, validates provenance, packs the trimmed 160 px atlas at Q>=75
and <=200,000 bytes, validates all forty frames and emits the decoded-atlas
round movie. Success receipts never create an art PASS. The new GPU pass is
pending; CPU checks cannot certify Metal or final art parity.

Non-obvious findings: project after finishing geometry; inverse-bind cloth to
retain the painted rest; include equipment and transitional fall frames in
clipping review; inspect feet below the torso with the top camera's near clip.
