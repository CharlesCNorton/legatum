# Barbarian scout, 3D round 2

Run from the repository root. Read the infantry scout chapter in
`tools/art/anim3d/PLAYBOOK.md` for the source, rig, projection, grade, review and
trimmed-atlas contract. Uses the shared MPFB install and the painting/fur inputs
under `~/LegatumRuns/anim-pilot/assets/barbarian-scout/`.

- `rebuild.sh`: build the crouched MPFB bind pose and original kit, fit finished bind geometry/skeleton, apply frozen
  camera UVs/generated fur, bake AO/curvature, and save five keyed clip masters.
- `render.sh b|c|d|e-idle|e-move|e-attack|e-hit|e-death|all`: gated Cycles render,
  default CPU / 512 px / 8 samples (use RESOLUTION=256 for previews); immediate review publication for each stage.
- `gpu.sh`: the complete no-argument lead pass. Metal Cycles, 512/256 masters,
  every stage review, trimmed 160 px atlas, validation and `round${ROUND}.mp4`.
  Rebuilds from existing external inputs; no downloads. Defaults to 64 samples.
  Retains a round transcript/status and rejects missing Metal or non-native masters.
- `post.py pack|validate|video`: source/grade-checked delivery and trim-aware video.
- `audit.py`: Blender-side anatomy, bones, bakes, source hashes, base, scales,
  actual motion, loop closure and held death checks, plus diagnostic bounds.

All actual models, raw and graded frames, texture maps, audits and pack reports
stay in `~/LegatumRuns/anim-pilot/masters/barbarian-scout/`. The shipped atlas is
only a candidate and no runtime code is changed. Never treat a byte-size or
structural pass as art approval. The first immediate reviews are retained under
`review/3d-v2/barbarian-scout-first-pass/`; current reviews use the requested flat
filenames and the running log records both passes.

Known first-round risks to inspect: proportions of the crouch and raised arm,
registration of projected features on the face and shoulders, cloth/skin seams,
boot and knee grounding, the axe draw/hand grip, and death settling. Do not create
`barbarian-scout-PASS` until the rest painting match and all motion pass review.
