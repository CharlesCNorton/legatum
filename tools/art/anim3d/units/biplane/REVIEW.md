# Biplane — driver round 2 after GPU review

**Candidate; no PASS marker.** At 256 px, the aircraft remains distinguishable from
the painting: cockpit/cowling contours, lower-wing attachment marks, smooth stone
and exposed crash surfaces still differ. At 64 px it reads as the same unit, but
its propeller/gear silhouette and plinth remain distinguishable. Death still loses
its display support abruptly. Technical checks are not visual approval.

## Reviewed evidence and changes

Opened the lead's textured/rest comparisons, all five motion strips and eight
sampled frames of round1.mp4 before editing. The GPU pass succeeded: Cycles
GPU512/64, 191,950 bytes at Q80, 40 frames and an eight-second H.264 movie. Original
masters/reviews are preserved in external `masters/biplane/driver-r1-gpu/` and
`review/3d-v2/biplane-driver-r1-gpu/`.

This round widens the four closed strut cross sections 24%, reduces the wheel hub
radii 30% and uses dull steel there. The propeller has separate amber-tinted
generated wood grain. Fine object-space stone grain blends into projected
lower-disc brushwork, excluding the support/contact footprint so death cannot
leave a painted support on the disc. The existing frozen camera UVs, generated
hidden fills, finished bevels, product lighting, eight real AO/curvature bakes and
one automatically fitted histogram grade are retained and regenerated.

Attack flashes now use the finished gun endpoints. Their former construction
coordinates buried them in the cowling after registration. The short solid bursts
are visible in the new 256/64 strip. All five strips, the gear sheet, rest/details
comparisons and decoded movie samples have been opened and reviewed.

`gpu.sh` now invalidates an old PASS when a new run starts. It still creates only
technical receipts, never visual approval. No round-one GPU failure needed repair.

## Exact current checks

- **Cycles CPU256, 8 samples**: all b/c/d/g stages and all 40 animation frames rendered.
- Geometry audit passed: frozen UVs/camera-only pigment, four struts, 40 bounded
  above-ground poses, aligned wheel axes, stationary disc, held final wreck.
- Trimmed atlas: **1341 × 715, 199,758 bytes at Q85**, 160 px logical cells and
  unchanged 8/8/10/4/10 clips. Q90 was 233,336 bytes. All 40 alpha offsets
  reconstruct exactly; the final two death frames decode identically.
- Movie: **1600 × 348, H.264/yuv420p, 240 frames, 8.000 seconds**, ffprobe verified;
  assembled from the decoded trimmed atlas.
- Six provenance regressions passed; current asset/build preflight passed.
- Twelve Python files parse; both shell scripts parse; diff whitespace passed.

Active 256 masters and reviews are CPU previews. Prior real 512 GPU masters remain
archived; the current `512/` set is deliberately absent until the new GPU pass.
No Rust, rules or app UI changed. No full Rust/WASM/app suite is applicable.
Repository art gate and lead visual review remain pending on the committed candidate.

## Lead GPU pass

From this checkout, no script arguments:

```sh
ROUND=2 tools/art/anim3d/units/biplane/gpu.sh
```

It verifies current inputs, regenerates clips, audits, requires Cycles Metal GPU,
renders every stage at native 512/64, retains 512/256 masters, regenerates all
reviews, packs/validates the trimmed 160 px atlas and creates the eight-second MP4.
The log, status and round receipt distinguish success from failure. GPU atlas size
will be checked independently; the CPU Q85 result has only 242 bytes of headroom,
so the normal Q80/Q75 fallback may be needed. Quality never falls below 75.

Masters stay external. The atlas remains an unwired art candidate; its JSON rects
and per-frame offsets require the trimmed-atlas reader, not fixed-cell sampling.
