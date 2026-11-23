# Knight round 2 — candidate, not PASS

Reviewed the incoming GPU c/f comparisons, all five clip strips and sampled
round-one MP4 frames before changing the model. Prior evidence is preserved in
external `masters/knight/driver-r1-gpu/`. The GPU pass failed at `Death must hold`:
re-rendering the same terminal source sample produced different pixels. Repeated
samples now copy one rendered PNG, then share one atlas rectangle. The exact
hold check remains strict.

## Changes

- Closed tapered helmet crown; trim and other static curves now follow the same
  fitting/projection pass as their surfaces. Removed misplaced inherited mane
  geometry that made black wedges beside the glove.
- Shorter folded caparison, continuous weighted lower-leg fitting, fitted glove,
  projected full-depth tail attached to the native tail bone, shaded/grained
  cream stone rim and pinned generated steel/leather fills on unseen surfaces.
- Skin correctives retain source hoof lift and all source foot rotations; a
  translation-only constraint keeps standing-clip soles within the disc.
  Death hands settle onto the horse after release. This is contact adaptation of
  licensed motion, not a cloth simulation or a proof of slide-free locomotion.
- During move, a small rigid lance grip-slide preserves an 8px master margin
  through the native saddle bob, with camera and base unchanged.
- Current-master hashes guard clip rendering. GPU handoff invalidates stale
  validation/movie receipts; plain review shows the finished sculpted geometry.

## Exact checks

- Source preflight: **10 pinned source hashes passed**.
- CPU Cycles: every required stage at **512 px, 8 samples**, plus retained graded
  **256 px** masters. Forty clip frames; all sixteen front/top gait samples.
- Scene audit: five source actions, frame counts, current-master hashes,
  stationary base, nonzero scales, hoof penetration and standing-clip disc
  footprint checks passed: **120/120 sampled soles inside the disc**, maximum
  radius **0.7815 m** against the **0.8058 m** disc. Full sole coordinates are
  recorded in audit.json. Death uses the whole-body plane solver.
- Trimmed **160 px atlas: 199,272 bytes at quality 85**, all **40 frames**.
  Hashes, timing/counts, bounds/non-overlap, trim reconstruction, transparency,
  clipping margins, motion presence and exact decoded death hold passed.
  Alpha quantization error is at most **5/255**.
- Round-two movie: **240 frames, 8 seconds, 1600×348, H.264, yuv420p** verified.
  Sampled movie frames, rest split/crossfade, clip strips and feet views inspected.
- **18 Python scripts parse**; shell entry points pass `bash -n`; `git diff --check`
  passes. Matrix-operator spacing preserves identical ASTs and resolves hygiene
  false positives. Current unit files pass the hygiene line scanner (0 findings).
- Repository checks on incoming HEAD: public-claims passed; hygiene flagged
  matrix operators (fixed in working tree); art could not complete because
  `render-sets.mjs` exited 1. This is not an art-gate pass. No Rust/UI logic changed.

## Honest visual verdict

At **256 px**, the closed helmet, glove, tail and exposed legs are clearer, but
this is still readily distinguishable from the painting. The legs are too thin,
the lower/rear cloth has gaps and incomplete volume, the base is too uniform,
and the raised arm lacks the painting's rounded mail shading. Death still
forms a rigid, tangled cloth pile. Attack and gait expose angular, stretched lower legs after the contact
corrections. Bind-space silhouette changes must be matched by anatomical joint
fitting, not treated as a finished retarget; a successful penetration check does not
make those clips clean.

At **64 px**, the lance, lion heraldry, shield and cream/blue palette identify the
same knight. The lower silhouette and base still differ. **No PASS was written.**
Live AO is present; fresh AO/curvature bakes and cloth/contact refinement remain.
The new Metal pass has not run in this CPU-only sandbox.

## Lead command

```sh
ROUND=2 tools/art/anim3d/units/knight/gpu.sh
```

Run from the repository root with no arguments. This rebuilds the scenes,
renders all stages with Cycles GPU at 512 px/64+ samples, retains 512/256 masters,
creates the trimmed atlas, validates it, and writes all reviews and the round MP4.
It refuses CPU fallback and never creates PASS automatically.
