# Spearman review — round 7

**Not PASS.** At 256 px the sleeve/upper arm is more continuous, the hand fuller,
the rear neckline cleaner and the stone perspective closer. Crest and cheek
outline, sandals, stance and base shading still differ from the painting.
Raised-arm paint stretching and uneven pale fallen-pose surfaces remain. At
64 px this clearly reads as the same spearman, but the base and stance are still
distinguishable. No `spearman-PASS` was written. All results are CPU previews.

The requested round-6 GPU log and status receipt are both absent. Supplied
images and movie were CPU-labelled; no GPU success or failure was inferred.
They are preserved under `review/3d-v2/spearman-round6-preserved/`. All six Blender
skills, all playbook chapters, complete shared/unit feedback, source licences
and the running log were read before the revision.

## Changes

Depth-preserving inverse-skin fitting now covers the whole bent arm and taller
knuckle stack. The near helmet cheek is wider; real folded collar and weighted
cape vertices lower the squared rear neckline. Original anatomy, topology,
weights, bevels, straps and simulated cloth remain.

The lower camera and repositioned round disc fit the shallower top ellipse;
the stone has a taller edge, fine pigment grain and unchanged .105m contact top.
The death calf solver now uses the actual base-local footprint. Existing generated
unseen fills and tinted MPFB skin receive camera-only pigment, live AO and 35%
physical response. Non-camera rays still see the original physical material.
One automatic rest histogram grade remains fixed across all clips.

Attack previously used a raised elbow pole at zero raise, causing a visible
entry/exit pop despite matching hand targets. Attack and death now interpolate
from the same guard poles as idle. The audit checks those transitions explicitly.

## Verified outputs and checks

- CPU Cycles rest and all 40 frames: 256 px, 12 samples; 512 px detail preview.
  Clips retain 8/8/10/4/10 frames. Final GPU 512/256 master export is pending.
- Trimmed 160 px atlas: **184,028 bytes at quality 80**.
  SHA256 `d7408ecf78042c7770163a28461d1e3d570781ab066cb10605c452a2b02b2a5f`.
- Decoded validation passes current hashes, timing, crop offsets, exact alpha,
  gutters, bounds, visible motion, byte/quality caps and identical held-death PNGs.
- Full saved-rig audit: **40 samples, zero findings**. Attack entry/exit arm
  positions match idle exactly; death entry differs by less than 0.000001m.
- Saved-scene checks pass: 314 camera-gated painting materials, 280 camera-only
  unseen fills, original 19,158 body vertices / 53 bones, .155m stone thickness,
  unchanged contact top and positive face clearance for all 12 shield rays.
  Additional scene ray tests confirm all 12 rays are directly visible.
- **2 regression tests pass**. Syntax: **26 Python, 3 Bash, 2 JSON**. Hygiene:
  **34 text files, zero findings**. Diff whitespace passes.
- Movie: five decoded clips simultaneously on cream, H.264 yuv420p,
  **1600 × 352, 192 frames, 24 fps, exactly 8 seconds**.
- Rest silhouette IoU **0.8839** versus round 6 **0.8767**; RGB union errors
  **22.25 / 27.27 / 28.60** versus **24.90 / 29.49 / 30.44**. Diagnostics only.
- Opened final clay, details, rest split/crossfade at 256/64, rig poses, every
  strip, decoded atlas and freshly decoded round-7 movie contact frames.

No Rust, rules, WASM or UI runtime changed. The game still displays its painting.

## GPU handoff

From the repository root on the GPU host:

```sh
ROUND=7 tools/art/anim3d/units/spearman/gpu.sh
```

The executable defaults to round 7, verifies Cycles GPU/Metal availability,
rebuilds projection and every clip, runs scene/rig checks, renders all stages at
512 px / 64 samples, exports genuine 512/256 masters to `masters/spearman/`,
packs and validates the atlas, and writes `spearman-round7.mp4` plus all review
images. It retains `gpu-logs-spearman-r7.log` and a stage/status receipt. It never
writes PASS automatically. Final GPU rendering and visual review remain pending.

Running log and exact report: `review/3d-v2/spearman-log.md` and
`spearman-final-report.json`. Masters remain outside git.

Git staging was blocked by `Operation not permitted` creating the worktree
`index.lock`; changes remain for the runner to commit with the requested
`Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>` trailer. The branch
already contains available `origin/master`; no fetch, push or PR was performed.
