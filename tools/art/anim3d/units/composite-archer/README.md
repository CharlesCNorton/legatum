# Composite archer — 3D round 2 candidate

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
UNIT=composite-archer tools/art/anim3d/render.sh refine
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
ROUND=2 tools/art/anim3d/units/composite-archer/gpu.sh
```

`gpu.sh` rebuilds clip keys, renders plain views and rest, renders every clip,
audits geometry, packs/validates, verifies GPU provenance and encodes the round MP4.
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

## Round 2 method and handoff

The actual mesh is now fitted to source landmarks through inverse skin transforms;
the painting is projected through one frozen camera without local UV warping.
Rigid kit is finished before projection, and occluded/head surfaces are masked to
avoid retaining the source drawing hand after release. Camera-only painted pigment
preserves source illumination while backs and non-camera rays retain the existing
physical materials and generated fills. The cream rim has a separate calibrated
pigment contribution with physical contact shadows retained.

`gpu.sh` is executable and accepts no arguments. It defaults to round 2, accepts the
driver's ROUND, and retains a transcript under `ANIM_ROOT`. Its receipt requires
GPU64/512 provenance, matching master/frame/grade hashes, valid trimmed delivery,
and an eight-second H.264/yuv420p MP4 of all five decoded clips. Missing-input
preflight and CPU-master rejection are checked locally; actual Metal rendering
must run on the lead host. A technical receipt is never an art PASS marker.

The trimmed anchor is now the exact scaled `(79.375, 138.125)`. The terminal death
hold reuses a single rectangle, and validation compares decoded alpha byte-for-byte
with source alpha at every offset. Native 256px previews cannot manufacture 512px
masters. All 40 samples and the Q75/200,000-byte limits remain unchanged.

## Round-2 verification and verdict

CPU Cycles, eight samples: all 40 native 512px frames and 40 gallery 256px frames.
The 160px trimmed atlas is **178,220 bytes at Q80**, with lossless 8-bit alpha and
premultiplied bicubic reduction. Q85 was 201,936 bytes and exceeded the cap. Full
atlas validation and the geometry/contact audit pass. Worst measured boot/stone
penetration is 2.83mm within the unchanged 12mm tolerance. The MP4 is verified
H.264/yuv420p, 1600x348, 240 frames/eight seconds, and decoded contact frames were
visually inspected. CPU evidence is retained under `round2-cpu`.

The sleeve silhouette, painted detail and cream pigment improve the rest image;
alpha silhouette overlap increases from .7370 to .7934. At 256px the face, hand/bow
contact, skirt and base perspective remain distinguishable from the painting.
At 64px the correct red/gold archer identity reads more strongly, but does not
match the source silhouette. Move/death expose simpler face/boot shapes and paint
seams; the five clips are not artistically cleared. **No PASS marker.** The lead
must run `gpu.sh` and inspect the GPU output before any final acceptance.

Final local checks: 17 Python files parse, both shell scripts pass `bash -n`,
21 text files pass working-tree hygiene, public-claims and `git diff --check` pass.
The browser art-set check is blocked: shared Playwright resolves, but Chromium's
MachPortRendezvous bootstrap is denied by the sandbox. Git add/commit is also
blocked creating this worktree's `index.lock`; the runner must commit these files.
No push or PR was attempted. The commit trailer is
`Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>`.

## Driver round 2 after GPU round 1

The supplied GPU job succeeded: 177,986 bytes at Q80, all native512/64 samples and
valid eight-second MP4. That evidence is archived under `driver-round2-before`.
This revision calibrates the circular-disc camera to16 degrees, preserves the
figure's screen registration through inverse skinning, projects real bow/binding
surfaces, and adds an image-generated cheek/beard/collar fill for the face revealed
by the drawing hand. Source prompt and full attribution are in `SOURCES.md` and
`face-fill.prompt.txt`; the generated asset is external `assets/composite-archer/face-fill-source.png`.

Idle/move/hit now derive from the local CC0 Quaternius library. Its crouch reference
is mapped onto the kneeling pose with complete rest/roll matrices, carrying-arm
layer and reduced stride. Death combines its torso/head reaction with floor support
and bow release. The unrestricted retarget was rejected after visual review; this
is constrained adaptation, not unmodified full-body capture. Foot rotations are
never manually patched. Full boot-shell support fixes penetration and keeps a
support foot down throughout the kneeling shuffle. `feet` renders actual front/top
move samples with only boots, trousers and stone visible, so the torso cannot hide
foot direction. The top/front images and measured ankle/toe positions remain
review evidence, not a claim of no sliding.

`gpu.sh` includes this diagnostic and rejects stale or CPU-labelled foot renders.
Packing now verifies every original painting/fill hash, including the new face
fill. The final quality verdict and current checks are in the external running log.
No PASS marker is written by any script.

Current driver-round2 CPU verification: **198,456 bytes at Q79**, all40 native512
and gallery256 clip frames. Source/grade/trim/alpha/hold validation and the saved
geometry audit pass; move boot clearance is2mm across all eight samples. Source
crouch influence was reduced to8% after the larger transfer hopped. The diagnostic
still does not prove natural knee support or no sliding. Video is H.264/yuv420p,
1600x348,240 frames/eight seconds, explicitly labelled CPU8. Python AST20 files,
Bash syntax and working-tree hygiene27 text files pass. CPU provenance is correctly
rejected by the GPU receipt checker. Rest silhouette overlap improves.793→.823;
face/hand alignment, stone shading and cramped fall remain below the painting.
No art PASS. Lead command remains `ROUND=2 tools/art/anim3d/units/composite-archer/gpu.sh`.

Final delivery limits: the working-tree browser art gate was attempted and blocked
by Chromium MachPortRendezvous bootstrap permission denial. Public-claims passes.
Git add/commit is denied at this worktree's index.lock; the runner must commit the
changes with the requested coauthor trailer. No push, PR or merge was attempted.
