# Composite archer — 3D round 1 candidate

True MPFB anatomy and 53-bone rig, original fitted costume, recurved composite bow,
hand-following string, arrow visibility and five clips. This is an art candidate;
the game continues to use its painting. See the unit chapter in ../../PLAYBOOK.md.

## Inputs and licences

- Painting: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/composite-archer-source.png
  (project CC BY 4.0), SHA256 `03e04d8a0a5ef29086547d08f86a21a2d5d6ec48ab6f7ffcfc7815944541bb21`.
- MPFB 2.0.18: https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18
  (GPL software, CC0 body/target/rig output). Existing isolated installation.
- MakeHuman system eyes: https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip
  (CC0), reused from the infantry pipeline.
- Original generated unseen-surface fills: `painted-fills.prompt.txt`, built-in imagegen
  output `01a2066f-01e7-74a3-a104-3aa0d38acf0c/exec-02734169-abee-47d0-ad4c-e44dade0c45f.png`,
  SHA256 `e95b9f80df2cd2deff9fef2c9c506cd66e9e923b24048a24aa38cd35bbfb0e58`.
  Project CC BY 4.0; retained externally at `assets/composite-archer/painted-fills.png`.
- Blender 5.3.0 and Pillow 13.0.0, existing open-source installs. No new model,
  commercial asset, account, cloud rendering or motion service.

Scripts are MIT; rendered art is CC BY 4.0. The complete external manifest is
`~/LegatumRuns/anim-pilot/masters/composite-archer/inputs.json`; shared asset sources
are recorded in `~/LegatumRuns/anim-pilot/assets/SOURCES.md`.

## Commands

Run at the repository root, one heavy process at a time:

```sh
UNIT=composite-archer tools/art/anim3d/render.sh prepare
UNIT=composite-archer tools/art/anim3d/render.sh build
UNIT=composite-archer tools/art/anim3d/render.sh paint
UNIT=composite-archer tools/art/anim3d/render.sh round
UNIT=composite-archer tools/art/anim3d/render.sh audit
```

A one-clip motion correction preserves the existing rest grade:

```sh
UNIT=composite-archer CLIP=attack tools/art/anim3d/render.sh refresh
UNIT=composite-archer tools/art/anim3d/render.sh pack
```

For the lead's GPU rerender of existing masters:

```sh
UNIT=composite-archer RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU \
  SAMPLES=64 RESOLUTION=512 tools/art/anim3d/render.sh final
```

`final` renders the rest pose first, refreshes all clips, audits geometry and repacks.
It fails if Metal is unavailable. Plain `blender -b --disable-autoexec` on PATH is the
only Blender launch; the shared gate owns concurrency and CPU limits.

## Outputs and honest review

External masters: `masters/composite-archer/`, including editable `.blend` files,
eight AO/curvature bakes, projection registration, generated fill inputs, all 40 raw
512px clip frames, graded 512/256 sets, render manifests, audit and pack reports.
Review: `review/3d-v2/composite-archer-*`, including the first plain build, textured
comparison, close-ups, rig poses, five PNG strips and five animated WebPs, plus the
rest split/crossfade at 256 and 64px. The log records each stage immediately.

The 160px candidate atlas has per-frame trim rectangles and offsets, quality >=75,
and a 200,000-byte hard limit. It requires a version-2 trim-aware reader. No runtime
wiring is changed. Source, clip, render and grade hashes prevent stale packing.

At 256px, the red/gold cloth, patterned trousers, quiver and composite bow are
recognizable, but the figure is narrower and the sleeve/draw-arm pose, face,
fingers, knee contact and projection registration do not match the painting's
craft. At 64px, it reads as the same archer family and palette; the source has a
broader, more convincing kneeling silhouette. This is not painting parity or GPU
approval. The fitted cloth is skeletally deformed, not simulated. The geometry
audit does not claim comprehensive body/gear collision detection.

## Round-1 verification

- Atlas: **180,418 bytes**, WebP **quality 85**, all **40 frames**, 160px untrimmed
  coordinates with per-frame crop offsets; 40 saved masters at each of 512/256px.
- Pack/validate passed source/render/grade hashes, decoded dimensions and alpha,
  native 2px margins, motion in each clip, terminal hold, trim reconstruction and
  size/quality limits. The actual decoded 160/64px review is `composite-archer-g-atlas-check.png`.
- Geometry audit passed 19,158 MPFB body vertices, 53 bones, stationary base,
  finite/nonzero transforms, current source hashes and held death. Death starts at
  the neutral transform within `5.96e-8`.
- **Contact is not cleared:** the audit reports anatomy minima around z=.052–.057
  during idle/move/attack/hit against a disc top at z=.085; hidden foot/boot geometry
  intersects the disc. Knee contact and footwear need another geometry pass.
- All 14 Python scripts parse; shell syntax and `git diff --check` pass.
- Browser art-set gate did not pass here: its `render-sets.mjs` process exited 1.
  GPU rendering and the lead's art review remain outstanding. No Rust, UI runtime,
  rules or dependency changes were made in this unit lane.

Two reusable implementation findings: import MPFB eyes before creating unattached
materials (the eye import purged them), and transfer fitted-shell weights by exact
source vertex index with subdivision disabled, rather than nearest vertices.

Final working-tree hygiene line checks (21 text files) and public-claims checks
passed using the existing gate functions on the actual files. Commit creation was
blocked by sandbox access to `.git/worktrees/lane-9/index.lock`; the runner must
commit these changes. The browser-dependent art gate remains outstanding.
