# Driver round 2 — CPU candidate; no visual PASS

The host round-one GPU pass crashed after attack frame 9. Its macOS crash report records
SIGTRAP and allocator free-block corruption while copying mesh attributes in dependency-graph
evaluation. The older death strip and round-one movie were not products of a completed GPU pass.
Mixed evidence is preserved in external `masters/barbarian-musketman/driver-r1-gpu/`.

The GPU handoff now renders each final frame in a fresh gated Blender process with persistent data
disabled. Content-bound checkpoints support interrupted rendering; a bounded retry handles SIGTRAP.
The entire frame-isolation path passed on CPU. The host GPU mitigation remains unverified.

This pass broadens the feather, warms and grains the physical stone, weights the finished shirt and
waistcoat across the spine, and fades grazing projected paint toward the existing generated fills
when surfaces turn. The original frozen camera projection, beveled straps, clothing folds,
AO/curvature maps, product lights and fixed automatic histogram grade remain. Source-derived death
arms blend out of the aiming pose; two-segment contact lowers the terminal hands toward the disc
while preserving lengths and source elbow poles. The released gun retains its world transform.

At 256 px the painting match is close in pigment and silhouette, but the face edge, feather shape,
base finish and exposed clothing still differ. The death hands are improved, but sleeves and coat
undersides still look stretched and terminal contact is imperfect. At 64 px the kneeling marksman
reads as the same unit, with visible feather/base differences. Move remains an extremely restrained
kneeling shuffle, not a standing gait; attack smoke is smaller than the painting. **No PASS.**

Verified delivery: Cycles CPU **512 px / 4 samples**, 62 genuine 512 PNGs and 62 matching 256 PNGs,
including front/top foot cycles. All 40 clip frames remain 8/8/10/4/10. The trimmed 160 px atlas is
**179,112 bytes at WebP quality 80**. The reconstructed five-clip movie is H.264/yuv420p,
1600 x 348, 240 frames, exactly 8 seconds. All strips, rest comparison, details, decoded atlas and
movie contact frames were opened for review. Low-sample CPU previews are not GPU final renders.

Checks passed: six isolated delivery regressions plus three interruption/recovery regressions;
master/clip/frame/metadata/grade hashes, trim reconstruction, exact alpha, padding/clipping,
motion and held death; 53-bone rig, stationary base, safe scales, arm/leg lengths, support-foot
planting and support-hand grip (maximum error 0.00000024 m). All 172 finished projected surfaces
have zero measured sampled rest-UV error. Python compilation, shell syntax and whitespace checks
pass. These checks do not establish complete collision freedom or artistic equivalence.

From this isolated checkout, the lead runs:

```sh
ROUND=2 tools/art/anim3d/units/barbarian-musketman/gpu.sh
```

The executable no-argument handoff preflights Metal, rebuilds/bakes, creates clips, renders every
stage at GPU512/48 or higher, exports 512/256 masters, packs/validates, runs nine regressions and
writes the round MP4 and GPU receipt. It never falls back to CPU or creates PASS. No Rust, rules,
AI or runtime UI behavior changed. No push, PR, merge or upload is part of this handoff.

Commit attempt was blocked by sandbox permission on the worktree index.lock; changes remain for
the runner to commit with the requested co-author trailer. origin/master is already an ancestor.
Commit-based repository/art gates remain runner/lead work; no check of the old HEAD is represented
as verification of these uncommitted changes.
