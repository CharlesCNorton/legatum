# Biplane — driver round 3

**Candidate; no PASS marker.** At 256 px the new stone pigment, rudder seam,
engine highlights and retained crash support improve the result. Cockpit/coaming,
dark wheel edges, propeller orientation, lower-wing attachment marks and smooth
hidden crash surfaces still distinguish it from the painting. At 64 px it clearly
reads as the same unit, but remains distinguishable. CPU256 previews are softer
than the prior GPU512 downsampling; a fresh GPU pass remains required.

## Evidence and changes

Opened incoming GPU c/f, all five motion strips and round2 movie frames. The lead's
round-two pass succeeded: Cycles GPU512/64, 194,118 bytes Q80, 40 frames and an
8-second H.264 movie. Its inputs, masters and reviews are preserved externally
under `masters/biplane/driver-r2-gpu` and `review/3d-v2/biplane-driver-r2-gpu`.
No GPU failure needed repair. Common feedback 1–23 and every local playbook chapter
were read; biplane-FEEDBACK.md was absent at the start and end of this round.

A built-in ImageGen clean stone plate fills the support's previously occluded
footprint. It is registered to the source painting and blended into the original
lower rim, projected onto the real closed disc, with live contact AO. A pigment
margin prevents a dark bevel fringe. The disc's ground-plane position and diameter
are closer to the painting. Exact generation, prompt and source hash are recorded
in SOURCES.md, stone-fill.prompt.txt and stone-fill.json; assets stay external.

The rudder seam follows the same registration as the fin, removing the stray spike.
Visible engine cylinders and fins now receive the painting's frozen camera pigment;
unseen surfaces retain physical steel. Product lighting, generated hidden fills,
finished bevels, linen ribs and eight actual AO/curvature bakes are retained. One
rest-derived automatic histogram grade is frozen across all clips.

Three capped full-depth stone sections preserve the curved support at rest and
separate during impact, settling into a compact pile. This replaces its abrupt
disappearance. A first intact support fall was rejected because its long silhouette
looked like a horn. The final audit checks closed positive-volume sections and
visibility at all samples, alongside bounds, floor, wheel alignment and held wreck.
It is not a complete mesh/mesh collision solver.

## Exact checks

- Cycles **CPU256, 8 samples**: b/c/d/g and all 40 animation frames rendered.
- Geometry audit: passed; three closed visible stone sections, finished projection,
  four struts, bounded above-ground poses, aligned wheels, stationary base, held wreck.
- Atlas: **1341 × 710, 182,556 bytes at Q80**, trimmed 160 px cells, 8/8/10/4/10
  frames. All 40 alpha offsets reconstruct exactly; final two death frames identical.
- Movie: **1600 × 348, H.264/yuv420p, 240 frames, 8.000 seconds**, ffprobe verified.
  Eight decoded samples and all strips/rest/details/gear sheets opened and reviewed.
- Six provenance regression tests passed; current asset/build preflight passed.
- Twelve Python scripts and both Bash scripts parse; diff whitespace passed.

Current CPU evidence is retained in `masters/biplane/driver-r3-cpu`. Stale active
512 files were removed after archiving the actual round-two GPU masters. This
round does not yet have native GPU512 masters. No Rust/rules/UI code changed;
full Rust/WASM/application suites are not applicable to this isolated art pipeline.

## Lead GPU pass

From this checkout, no script arguments:

```sh
ROUND=3 tools/art/anim3d/units/biplane/gpu.sh
```

The executable defaults to round 3. It verifies inputs, regenerates clips, audits,
requires Cycles Metal GPU, renders every stage at native 512/64, retains 512/256
masters, regenerates reviews, packs/validates the trimmed atlas and produces the
8-second movie. Its receipt now includes asset hashes and the build manifest.
It never writes PASS automatically. GPU size and visual quality require fresh review.

The atlas is an unwired art candidate; its offsets require a trimmed-atlas reader.
