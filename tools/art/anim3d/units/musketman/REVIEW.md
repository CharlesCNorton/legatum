# Musketman round-two review

Candidate only; no PASS. The painting remains the visual target. No game rules
or runtime UI changed.

Inspected the lead's actual GPU c/rest/idle/move images, all available strips and
round1 movie frames before editing. The round-one GPU log ended in SIGTRAP while
rendering attack frame 8, with no complete GPU receipt. Later strips and movie
were previous CPU evidence. Those mixed outputs are preserved outside git in
`masters/musketman/driver-r1-gpu/` and `review/3d-v2/musketman-round1-preserved/`.
The log does not identify the underlying Metal failure.

Changes: fuller red/ivory plume, asymmetric thick brim, inverse-skinned support
finger fit, complete solid gunstock butt, corrected barrel/ramrod/socket/blade,
warmer and thicker stone with grain, and an 8-degree orthographic camera.
The existing frozen painting projection, generated hidden-surface fills,
beveled straps/buckles, geometric cloth folds, AO/curvature bakes, warm key,
soft fill, cool rim and automatically sampled histogram grade remain in use.
Captured hit motion now returns to guard in its fourth sample.

At native 256 px, the rest is closer in hat silhouette, gun shape and stone
color. Coat/face/bandolier brushwork remains rich. It is still distinguishable:
the brim and feather are more regular, the support grip is small, the steel
looks simpler, and the stone lacks the painting's subtle edge variation. At
native 64 px it clearly reads as the same buff/red musketman, with a closer
base and plume; that is identity matching, not indistinguishability.

All five clips exist and were inspected in strips, decoded atlas and extracted
movie frames. The walk has a stiff carried weapon and needs ground-speed/entry
review despite passing heading/contact checks. Hit recovery is better. Death
still exposes abrupt sleeve/wrist transitions, patchy undersides and suspended
legs; it does not meet the clean-clips bar. Cloth remains thick folded geometry
with contact shape keys rather than a cloth simulation. No PASS was written.

Verified CPU output (Blender 5.3 Cycles, 512 px, 8 samples, denoising):

- All 62 stage frames completed through isolated processes, with verified
  per-frame checkpoints. Genuine 512 and downsampled 256 masters are retained
  externally; there are 40 clip frames in the required 8/8/10/4/10 counts.
- Scene audit passed: 53-bone rig, frozen camera UV agreement, source hashes,
  positive scales, stationary base, bone lengths, boot heading/contact,
  support-hand bone constraint and held terminal death. These are limited
  geometry checks, not a collision-free animation certificate.
- Trimmed 160 px atlas: **185,124 bytes at WebP quality 85**. Quality 90 was
  218,866 bytes. All 40 frames, alpha/offset reconstruction, clip settings,
  motion, held death and source/grade/delivery hashes passed validation.
- Seven regression tests passed, including stale output rejection, corrupt
  trim detection, refusal of a CPU GPU-receipt, and interrupted-stage handling:
  a valid earlier frame is reused, SIGTRAP retries once, and no completion
  manifest survives failure.
- H.264/yuv420p movie probe passed: 1600×348, 240 frames, 8 seconds, five
  reconstructed clips at 2× on cream. `musketman-round2.mp4` and an extracted
  contact sheet are in external `review/3d-v2/`.
- Python syntax, Bash syntax and `git diff --check` passed. No Rust/WASM/app
  build is applicable to these asset-generation-only changes.

The revised GPU handoff isolates every frame in a fresh plain `blender` process,
disables persistent Cycles data, binds checkpoints to source/settings/renderer
and PNG hashes, and refuses incomplete or stale manifests. This mitigation
passed CPU rendering and failure-path tests; Metal recovery remains unverified.
Run from repository root, without script arguments:

```sh
ROUND=2 tools/art/anim3d/units/musketman/gpu.sh
```

It rebuilds, bakes, retargets, GPU-renders every stage at 512 px/48 samples,
keeps 512/256 masters, packs and validates, writes the round movie and then a
hash-bound GPU receipt. Review the resulting images before any art approval.

Git staging was blocked by sandbox permission on `.git/worktrees/lane-9/index.lock`.
The runner must commit; the requested co-authored message is saved externally
as `review/3d-v2/musketman-commit-message.txt`. HEAD already contains the fetched
`origin/master`, so no integration merge was needed.
