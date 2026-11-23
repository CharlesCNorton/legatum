# Panzer, driver round 2

**Candidate; no visual PASS.** Read the original GPU c/f comparisons, five strips
and decoded round-one MP4 before editing. That GPU pass completed successfully:
188,914 bytes at quality 75. Original review images and 512/256 masters are
preserved under `masters/panzer/driver-r1-gpu/`, outside git.

This round raises/enlarges the cupola, extends the ported brake, registers the
near running gear to painting landmarks while retaining the far track beneath
the glacis, and adds recessed wheel dishes, chipped raised rims, hubs, apertures
and bolts. New generated ochre brushwork is mapped to the rotating wheel
surfaces, with a fixed-height studio wash so painted lighting does not rotate.
The exact built-in ImageGen prompt is `painted-ochre.prompt.txt`; its external
asset is `assets/panzer/painted-ochre.png`, with provenance and hash in this unit's
source/lock files. Existing generated olive fill remains on hidden hull faces.

Conservative rest-camera occlusion masking rejects wholly hidden polygons.
Testing only polygon centres erased visible parts of broad hull/base faces;
centre-plus-corner visibility fixed that defect. Partly hidden faces can still
carry projected detail into motion; this is not a per-texel visibility bake.
Warm key/cool rim, a lower soft wheel fill and one automatic RGB-quantile grade
are used. Irregular closed smoke shells with normal/view alpha falloff replace
the stack of hard oval outlines. Visibility is keyed; no near-zero scale or
OpenVDB volume is used.

At **256px**, the upper armour brushwork, cupola and barrel are closer to the
painting, but the wheel faces still look too uniform and shallow; wheel/track
silhouettes and highlights are distinguishable. The smoke is less geometric but
grainy at 12 CPU samples. At **64px**, this is recognizably the same sand/olive
skirted Panzer, though the running gear still reads as a simpler band. No source
wheel-paint smearing was observed in the revised move strip/video samples.
A perfectly invisible wheel loop seam and final smoke quality remain GPU-review
items. No `panzer-PASS` was written.

Actual CPU checks:

- Every stage rendered in Cycles: 256px, 4 samples for plain, 12 for final c/details,
  poses, all five clips and top/front track checks. Current 256px masters include
  a renderer/source manifest. Current-round 512px masters require the GPU pass.
- Four numerical track tests passed, covering both registered envelopes:
  closure, constant speed, tangents and lower-run direction.
- Saved-scene audit passed all five clips: 8/8/10/4/10 samples, source hashes,
  fixed base, positive scales, full mesh geometry and a 2% frame margin. The
  stricter margin was added after packing caught an antialias tail at the right
  edge of hit; keyed hit/death gun retractions and shorter flash corrected it.
- Trimmed atlas: **1413×583, 199,414 bytes, WebP quality 85**, 40 logical 160px
  frames. Exact reconstructed alpha, row order, offsets, gutters, source/render/
  grade hashes, motion and held death passed.
- Actual encoded video: H.264, yuv420p, 1600×348, 240 frames, 8.000 seconds.
  Decoded 0/0.3/0.6/1.5-second frames inspected, alongside all five native strips.
  `video.py` now validates the current atlas before encoding, rejecting stale
  delivery after a failed pack. CPU video is `panzer-round2-cpu.mp4`.
- All 15 Python files parse; both shell entrypoints pass `bash -n`; diff whitespace
  check passed. No Rust, rules or app runtime changes; no repository-wide CI claim.

From the repository root the lead runs this executable with no arguments:

```sh
ROUND=2 tools/art/anim3d/units/panzer/gpu.sh
```

It audits saved clips, runs the track tests, renders every stage sequentially in
Metal Cycles at 512px (128 samples by default), retains true 512/256 masters,
rebuilds/validates the atlas, produces all comparisons including rest/crossfade,
and writes `panzer-round${ROUND}.mp4`. A per-round report verifies GPU/512px
provenance for every stage. It never writes the visual PASS automatically.

Git staging is sandbox-blocked at `.git/worktrees/lane-4/index.lock`; the runner
must commit these changes with the requested co-author. No push or PR was made.
