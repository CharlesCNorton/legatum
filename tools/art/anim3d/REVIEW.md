# Spearman review — round 5

**Not PASS.** At 256 px the shield contour, shoulder fit and feet are closer to
the painting, but the base profile/lighting, sleeve edge and crest remain easy
to distinguish. At 64 px it reads as the same gold/red/cream spearman; the base
and stance still prevent a one-for-one match. Lifted feet and the raised shoulder
show projection stretching, and death reveals pale surfaces near the back.
Five clips exist and their mechanical checks pass; they are not visually approved.
No `spearman-PASS` was written.

## Changes

Registered the whole convex shield before seating its boss and rays. Plain-clay
review exposed a surviving round-4 defect: the raw shell used for ray intersection
did not include Solidify, so several raised rays remained partly buried. The
intersection now uses the evaluated shell; the new clay sheet shows the relief
above that surface. Every dependent clip and render was rebuilt after this fix.

A smooth fitting field seats the spear-side shoulder and shin and broadens the
other sandal's real toe and sole. Inverting the blended bone matrices preserves
MPFB topology and original weights. No cutout, billboard or per-frame projection
is used. Existing image-generated backside fills, beveled straps, folds, the
physical stationary stone disc and cloth simulation remain intact.

Standard/None preserves already-painted illumination instead of compressing it
again through AgX. The existing 96% pigment / 4% physical blend and one frozen
histogram grade remain. A less orange warm key, soft cool fill and low stone
pigment emission improve the palette while retaining live contact shadows.

The GPU handoff now checks device availability before cloth baking, rebuilds
projection from the clean checkpoint, retains its round-specific GPU log and
records the failed stage. The supplied round-4 GPU log was missing; supplied
images and manifests were CPU previews. No prior GPU success is claimed.

## Final checks

- CPU Cycles, 256 px / 12 samples for rest and all 40 clip frames; 512 px CPU
  detail preview. Final GPU master export has not run.
- Trimmed 160 px atlas: **196,706 bytes, quality 85, 40 frames**;
  counts 8/8/10/4/10. SHA256 `1992a323636f4afea9b3b807bed63d5ec1ad3322d33674df8a945787ebd5b57a`.
- Decoded validation PASS: current master/clip/grade/frame hashes, timing,
  crop offsets, exact alpha, gutters, camera margins, visible motion, byte cap
  and quality. Held death PNGs are byte-identical.
- Saved-rig audit: **40 samples, zero findings**; 19,158 body vertices, 53 bones,
  persistent cloth, stationary base, floor/camera bounds, grip and spear clearance.
  This is not a full skin/cloth collision solver.
- **2 regression tests pass**; syntax passes for **24 Python, 3 Bash, 2 JSON**
  files. **32 text files / zero hygiene findings**; diff whitespace passes.
- Movie verified with ffprobe: H.264 yuv420p, **1600 × 352**, **192 frames at
  24 fps**, **8 seconds**, all five decoded clips side by side at 2x.
- Rest silhouette IoU **0.8644**, versus round 4 **0.8511**. Union RGB errors
  **30.30 / 35.57 / 35.50**, versus **33.54 / 38.35 / 39.69**. Diagnostics only,
  not art approval. All final strips, details, clay, rig poses, decoded atlas
  and movie contact frames were opened and inspected.

No Rust, rules, WASM or UI runtime changed. Browser/art integration review remains
with the lead; the animation renderer is not enabled by this task.

## GPU handoff

From the repository root on the GPU host:

```sh
ROUND=5 tools/art/anim3d/units/spearman/gpu.sh
```

This requests Cycles GPU/Metal at 512 px / 64 samples, all stages and clips,
512/256 master export to `ANIM_ROOT/masters/spearman/`, trimmed atlas validation,
rest comparisons and `spearman-round5.mp4`. The script fails explicitly without
a GPU and never writes PASS. Editable source and CPU previews remain in
`masters/spearman-3d-v2/`; received evidence is preserved in
`review/3d-v2/spearman-round4-preserved/`. The running log and exact report are
`review/3d-v2/spearman-log.md` and `spearman-final-report.json`.

Non-obvious findings: intersect the evaluated support surface, including thickness
modifiers, before seating relief; preserve original skin weights by inverting the
rest-pose deformation when fitting anatomy; painted illumination needs deliberate
color management rather than a second photographic tone map.

Git staging was denied at this worktree's `index.lock`; the runner must commit
these changes. Available `origin/master` is already contained (zero missing
commits). No fetch, merge, push or PR was attempted. Commit trailer:
`Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>`.
