# Archer — round 2

Improved art candidate, not approved or connected to the game runtime. No PASS
marker. At 256 px the recurved bow, broader drawing arm, painted cloth/leather
and warm stone are closer to the painting. The squared elbow, face/gaze, crest
and shoulder drape still differ; motion reveals simpler unpainted surfaces.
At 64 px the unit is recognizable as the same archer but remains distinguishable.
Rest alpha silhouette overlap improved from approximately .744 to .790.

`refine.py` finishes actual solid/beveled/subdivided geometry before `paint.py`
freezes the painting camera UVs. It freezes MPFB macro morphs while retaining
skin weights and the live 53-bone rig; fits the drawing-arm contour through
inverse skin transforms; reshapes the thick crest and complete swept bow; and
calibrates product lighting and physical stone. Camera-only projected pigment
preserves painted illumination, with existing generated fills, native skin,
cloth weave, AO and curvature underneath. Standard/None plus one fixed rest
histogram grade avoids a second contrast compression. This is full-depth 3D
geometry, not a cutout, alpha silhouette, or per-frame camera projection.

The original five 8/8/10/4/10-frame clips remain. Move now grounds the finished
sandal sole instead of the foot-bone origin. Death interpolates limb poles and
foot orientations from the rest pose, fixing its entry jump. The bow releases
and settles; the arrow uses keyed visibility. Final death samples are identical.
The drawn-bow walk remains stiff; cloth is modeled rather than simulated and
the audit is not a complete collision solver.

Round-two evidence, 2026-11-23:

- All 40 current Cycles CPU/12-sample frames at 256 px, transparent PNG masters,
  all stage reviews, five animated WebPs, rest split/crossfade and decoded atlas.
- An actual 512 px CPU detail render is retained. All prior 512/256 round-one
  evidence is preserved in `masters/archer/round1-cpu/`; current final GPU512
  masters are pending, not represented by upscaled previews.
- Trimmed 160 px atlas: **894×753**, **191,284 bytes**, **quality 90**, all forty
  samples. Premultiplied bicubic reduction, exact lossless alpha and offsets.
  `pack.py --preview` explicitly marks this CPU256 delivery as a preview.
- `validate.py` passes current source/clip/grade/frame hashes, clip timing,
  reconstruction, exact alpha, gutters, margins, visible motion and held death.
- `audit.py` passes finished-surface UV registration (<.01 token pixel), frozen
  morphs, 53 bones, fixed base, safe scales, string/nock contact, walking sole
  contact, death-entry continuity and exact loop closure.
- `archer-round2.mp4` is verified H.264/yuv420p, 1600×348, 240 frames, eight
  seconds, five decoded clips at 2x on cream. Review images were inspected.
- Python AST checks pass for 15 files; Bash syntax passes for three scripts;
  whitespace checks pass. Missing-input GPU preflight fails with a recorded
  stage/status and no success receipt. GPU master validation rejects CPU images.

The required executable host entry point is:

```sh
ROUND=2 tools/art/anim3d/units/archer/gpu.sh
```

It audits and renders every stage on Cycles Metal at GPU512/64 samples, writes
512/256 masters, checks actual render provenance and saved blend hashes, packs
and validates the 160 px atlas, and writes the round MP4. `gpu-round.sh` delegates
to it. The script keeps a transcript and failure status; a success receipt still
requires visual review and never creates PASS. Metal execution cannot be tested
in this sandbox and remains for the lead. The browser/art gate and final art
review remain integration gates, not evidence supplied by these pipeline checks.

Non-obvious findings: freeze static macro morphs before inverse skin fitting;
finish real modifiers before camera UV calibration; sample actual sole geometry
for grounding; match elbow/knee poles as well as hand/foot targets at clip entry.
Closely overlapping crest tufts need continuous pigment coverage rather than
independent visibility samples at their boundaries. Source-color agreement and
silhouette overlap do not establish anatomical or animation quality.
