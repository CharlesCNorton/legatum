# Spearman review — round 6

**Not PASS.** At 256 px the shield paint is cleaner, the shoulder protrusion is
reduced and the base is less blown out, but shoulder contour, sandals, crest and
stone surface still differ from the painting. Raised-arm paint stretches and
oblique/death surfaces remain uneven. At 64 px it reads as the same spearman;
the stance and base still prevent an indistinguishable rest match. No
`spearman-PASS` was written. All output is explicitly labelled CPU preview.

Round 5's requested GPU log was absent. Its supplied images and movie were CPU
previews; no GPU success or failure was inferred. They are preserved under
`review/3d-v2/spearman-round5-preserved/`. All six Blender skills, full playbook,
shared/unit feedback, source licences and prior log were read before the revision.

## Changes

Rigid thickness and bevels are applied before frozen camera UV projection,
removing displaced/doubled paint on the shield and improving other kit surfaces.
Long shield-ray triangles were still cutting through the convex shell between
clear endpoints: actual subdivision, interpolated keel heights and surface
seating now keep all twelve finished rays clear. Minimum tested face-center
clearance is 6.59mm. The geometry retains volume and live bone parenting.

MPFB's active macro shape keys were overriding earlier body vertex edits. The
current mixed morph is now baked on the working copy before inverse-skin fitting.
The clean checkpoint retains the original morphable human; the fitted master
keeps 19,158 vertices, original weights and the 53-bone rig. Shoulder and foot
corrections now affect the rendered anatomy. Foot skin fits inside the sandals;
small foot/calf contact corrections prevent the detected standing/death
penetrations. The stricter audit measures the actual disc footprint and top,
with a 10mm tolerance, plus world ground. It is not a full collision solver.

The lower camera better matches the disc ellipse. Painted pigment is camera-only
so it does not light nearby surfaces. Product-light ratios remain, at 55% of
prior energy; the cream base keeps physical contact shadows and fine grain with
camera-only pigment. Existing generated fills, AO/curvature, bevels, straps and
cloth folds remain. One automatic histogram grade is frozen across every clip.

## Verified outputs and checks

- CPU Cycles rest and all 40 frames: 256 px, 12 samples; 512 px detail preview.
  Five clips retain 8/8/10/4/10 frames. Final GPU master export has not run.
- Trimmed 160 px atlas: **198,474 bytes at quality 85**.
  SHA256 `692c0e5a28e0d924b4068a445e93b1a62913ab05fadfdd578418d62bf55acd2f`.
- Independent decoded validation passes current source/grade/frame hashes,
  timing, crop offsets, exact alpha, gutters, camera bounds, visible motion,
  byte cap and quality; held death PNGs are byte-identical.
- Full saved-rig audit: **40 samples, zero findings** under the stricter test.
  Saved-scene checks pass: 314 camera-gated paint materials, frozen MPFB morph,
  finished rigid surfaces, positive ray clearance and original body/rig counts.
- **2 regression tests pass**. Syntax: **25 Python, 3 Bash, 2 JSON**. Hygiene:
  **33 text files, zero findings**. Diff whitespace passes.
- Movie: five decoded clips simultaneously on cream, H.264 yuv420p,
  **1600 × 352, 192 frames, 24 fps, exactly 8 seconds**.
- Rest silhouette IoU **0.8767** versus round 5 **0.8644**; RGB union errors
  **24.90 / 29.49 / 30.44** versus **30.30 / 35.57 / 35.50**. Diagnostics only.
- Opened final clay, details, rest split/crossfade at 256/64, rig poses, all five
  strips, decoded atlas and freshly decoded round-6 movie contact frames.

No Rust, rules, WASM or UI runtime changed. The game still displays its painting.

## GPU handoff

From the repository root on the GPU host:

```sh
ROUND=6 tools/art/anim3d/units/spearman/gpu.sh
```

The executable resolves its own checkout, verifies Cycles GPU/Metal availability,
rebuilds projection and every clip, runs scene/rig checks, renders every stage at
512 px / 64 samples, exports real 512/256 masters to `masters/spearman/`, packs
and validates the atlas, and writes `spearman-round6.mp4` plus the comparisons.
It retains `gpu-logs-spearman-r6.log` and writes a running/failed/complete status
receipt with failed stage/exit code. It never writes PASS automatically.

Running log and exact report: `review/3d-v2/spearman-log.md` and
`spearman-final-report.json`. Masters remain outside git. Available origin/master
is already contained; no fetch, merge, push or PR is part of this round.

Git staging was blocked by `Operation not permitted` creating
`.git/worktrees/spearman-round2/index.lock`; changes remain uncommitted for
the runner. The branch already contains the available `origin/master`.
