# Round 1 — CPU candidate, not art approval

Built and reviewed 2026-11-23. Blender 5.3.0, Cycles CPU, native 256px, 12 samples with denoising. Final GPU pass has not run in this sandbox. Native 512px masters must be produced by gpu.sh; previews are never upscaled and described as 512px masters.

## What exists

- Original 20-mesh, 7,831-vertex closed-volume aircraft/pedestal scene, projected painting materials, physical silver hidden surfaces, six real 512px AO/Pointiness maps, rigid airframe rig and five saved clip scenes.
- Idle 8, move 8, cannon attack run 10, hit 4, crash 10. Bank/translation use quaternion keys. Crash deforms the near wing, tips the support, solves a base contact correction and holds the final two samples. No zero-scale effects or volumes.
- External editable masters, texture bakes, native 256px frames and hash receipts under `~/LegatumRuns/anim-pilot/masters/jet-fighter/`.
- Immediate b-plain, c-textured-lit, c-details, d-rig-poses, five e-clip strips/animated WebPs, f-restpose-compare and g-feet-check under `~/LegatumRuns/anim-pilot/review/3d-v2/`. First b/c sheets retained as `jet-fighter-first-*`; log records rejected geometry and clipping fixes.
- Candidate `app/src/assets/units/anim/jet-fighter.webp` and JSON: 160px logical frames, trim offsets, shared held-frame rectangle. No runtime changes.
- Eight-second side-by-side decoded-atlas video `jet-fighter-round1.mp4`, plus FFprobe receipt and decoded preview frame.

## Visual verdict

At 64px this reads as the painting's silver jet on its cream curved pedestal, with similar frame occupation. At 256px it is visibly less finished: the intake lip/cavity and canopy silhouette are approximate, the near-wing chord/root and rear fin/fuselage junction do not reproduce the painting exactly, and some source highlights are softened. The far wing has actual depth, but its sweep, dihedral and projected pigment coverage remain weak when viewed from top/front or revealed during the crash. That off-angle geometry is the largest next-round modeling task. Product lighting on unseen silver can still become too bright.

Idle and move loop cleanly but flight is restrained. The cannon run reads subtly. Death is a visible descent/impact/fold with an identical terminal hold; its wing curl and support tip are stylized and need better mechanical damage and contact. Technical collision checking is limited to the sampled base contact correction, not a full collision solver. No PASS file is written. Rest-pose painting parity and clean GPU motion are not yet established.

## Checks

- Input/build preflight: PASS, external source and fill hashes plus scene/prepare/bake source hashes and saved masters.
- Blender geometry/clip audit: PASS, manifold positive-volume main fuselage/wings/fin/intake, nonzero object scales, fixed base, moving clips, closed idle/move loop endpoints and held death root.
- Atlas validation: PASS, 40 frames, **178,178 bytes**, **quality 85**, 160px logical cell, transparent padding, no crop overlap or clipping, exact reconstructed alpha, identical decoded death hold, scene/script/grade/frame hashes current.
- FFprobe: PASS, H.264, yuv420p, 1600x348, 240 frames, 8.000 seconds. Decoded representative frame inspected.
- Python AST: PASS, eight scripts. Shell syntax: PASS, render.sh and gpu.sh. git diff whitespace: PASS.
- No Rust, game rules or app UI changed, so no Cargo/build/test suite was run. GPU execution remains lead-side work.

## Lead command

From this branch's repo root:

```sh
ROUND=1 tools/art/anim3d/units/jet-fighter/gpu.sh
```

This is the sole no-argument handoff: strict Metal preflight; every stage and all 40 samples at 512px Cycles GPU; 512/256 master export; rest comparison/details/top-front sheets; trimmed atlas, validation, audit and `jet-fighter-round${ROUND}.mp4`. Default 96 samples; optional SAMPLES override. The script reports technical completion with visual review pending and never writes PASS.

Commit attempt was blocked by sandbox index.lock permissions; all changes remain uncommitted for the runner. Intended footer: `Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>`. The already-fetched origin/master has no commits ahead of this checkout.
