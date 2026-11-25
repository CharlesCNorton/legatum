# Spearman PBR — round 3 handoff

Branch: `astra/unit-anim-3d-spearman-0ad-pbr`; continues round-2 `ba93c3dc`
after its master merge. Main asset: `tools/art/anim3d/units/spearman-0ad/spearman.glb`.
SHA-256: `6dd1c8b15456b6a97d6341fa6532cf860a331fc1a23e8430ede23178f5bf8622`.

**Verdict: technical gates PASS; premium visual gate FAIL.** This is a review
candidate, not art approval. The construction is cleaner than round 2, but the
helmet, garment tailoring and material finish still fall short of the painting.
Actual three.js pixels and playing-speed approval remain the lead's host step.

## Changes

- Read the 02:03Z premium brief, items 10–13, both painting references, the
  previous lane note, and both lanes' round-2 comparisons. Retained the PBR
  shield identity and the painted lane's useful linen/leather/crimson separation.
- Retained the CC0 MPFB muscular anatomy and native nearest-face-interpolated
  Data Transfer weights; normalized and limited to four influences. Fuller
  upper arms, forearms and hands; original skeleton and all five clips untouched.
- Rebuilt the tunic as a continuous pleated linen chiton, with a light thigh
  blend below the hip; corrected left/right thigh assignments. Broader sculpted
  cuirass, incised pectoral borders, leather belt, shaped knee cups and sandals.
- Closed wraparound Corinthian helmet with real eye/breathing apertures, curved
  cheeks/nape, brow and nasal ridges. One rounded, scalloped crest mass replaces
  the decimated locks that made triangular spikes. Its fine hair detail is still weak.
- Replaced global decimation with explicit part budgets; retained the round
  aspis, rolled rim, raised sunburst, leaf blade and butt spike. All carried
  props remain rigid on their original socket bones.
- Cloak/lining share topology and paired floor corrections. Independent contact
  projection had flattened their layers onto each other; the attack preview
  exposed this as dark patches. Pairing removed that visible breakthrough.
- Worst-pose joint crops caught an open upper arm caused by a spatial torso
  cull. The final model retains the complete body; only the enclosed upper head
  is culled. The raised-arm opening is closed in the final joint crops. Spine-weighted torso volume is fitted inside the cuirass without cutting connected arm surfaces.
- Cycles CPU bakes from **236,568 dense triangles**, with high-only chased bronze
  border/shin grooves, patina, hair striations, hammered relief, cloth weave and AO. Bronze is
  metallic, linen matte, leather semi-matte, wool crimson. Pigment contains gentle
  gradients and material variation; directional lighting/AO stay out of it.
- **9,855 LOD0 / 2,848 LOD1 triangles; 30 joints; one shared material and skin.**
  Both named LODs keep COLOR_0.r, UV0 ORM and the exact +Z-facing skeleton.
- **1,836,304 bytes (1.836 MB decimal)**. Three embedded **1024×1024 WebP** maps,
  authored as **2048×2048 PNGs**. Base/normal/ORM payloads: 214,834 / 180,050 / 336,312 bytes, quality 85/90/88. Normal strength .45. Encoding remains lossy;
  measured mean RGB channel errors are 2.91/1.45/2.89, 3.41/2.23/3.42, 6.33/3.84/6.93 on a 0–255 scale. Do not treat CPU texture-header checks as
  browser decoding or pixel proof.
- Retained the pinned CC0 Poly Haven HDRI, warm key, cool rim, soft shadows,
  SSAO and ACES viewer. Recorder now uses the requested `-vs-panel-viewer.png`
  suffix. The Cycles turntable is separately labelled `-cycles-turntable.mp4`.
  The 48 px examples render **LOD1**, while 160 px sprites render LOD0.

## Exact checks on the delivered hash

- `validate_glb.py`: **valid=true**, errors=[]; includes the new under-2,000,000-byte
  cap, two named meshes, one material, rigid props, team masks and 1024 maps.
- Khronos 2.0.0-dev.3.10: **0 errors, 0 warnings, 0 infos, 0 hints**.
- Validator regression suite: **14/14 PASS**. PBR contract suite: **9/9 PASS**,
  including the added oversized-GLB rejection.
- `check_pbr.py`: all five animation input/output buffers **byte-identical** to
  approved round 6; hierarchy/transforms and inverse binds identical. Both LODs
  sampled at 120 fps; worst floor penetration **1.483 mm**, within 2 mm.
- Three.js 170 GLTFLoader/AnimationMixer CPU checks: **PASS** for loading,
  skeleton/material sharing, animation, masks, texture headers and framing.
  Browser access was unavailable; no actual browser-rendered verdict is claimed.
- Joint compression sampled at 60 fps and the worst shoulder/elbow/knee poses
  rendered for every clip. Attack minimum local blend-axis scale is **.354 at
  the shoulder / .253 at the elbow**; this is substantial LBS compression, not
  a clean candy-wrap pass. Other clip minima are .678 or higher. Final crops
  show the arm opening fixed, but do not certify all collision clearance.
- Python compilation (10 changed files), JS syntax checks (2), import check
  (**0 unresolved**) and `git diff --check`: **PASS**.
- No Rust or production app code changed; no unrelated Cargo/app suite run.

## Evidence and remaining gaps

Review directory: `~/LegatumRuns/anim-pilot/review/3d-v2/`, prefix
`spearman-0ad-pbr-r3-`. Deliverables: five `<clip>-160.mp4` sprite movies, three
loops at game rates; `readability-48.png`, `vs-panel.png`, `closeups.png`,
`motion-contact.png`, `joint-check.png`, `cycles-turntable.mp4` and JSON receipts.
Sprites use the existing 4/6/14/12/4 fps rates; these change apparent speed from
the native clips, whose timings remain identical. Judge native motion in the viewer.

1. The figure is still less convincing and less richly crafted than the painted
   hoplite. It has cleaner construction, not the painting's premium finish.
2. The rounded crest has lost the sharp stray tips, but reads as a solid mass
   without enough horsehair texture. Helmet eye/brow and cheek contours remain
   too simple. Some close-up edging still looks angular.
3. The shoulder linen boundary and armour joins need better tailoring. Joint
   crops expose the attack's elbow compression; a complete intersection-free
   result is not established. The wider cloak still moves like a simple surface
   on the approved three cape bones.
4. Bronze and cloth separate, but fine chased detail does not produce the
   reference's deliberate ornamental richness. Compression and the actual
   three.js lighting must be judged before approving these material choices.

FOCUS a: refine shoulder/arm fitting and tailored garment boundaries while preserving motion.
FOCUS b: sculpt helmet eye/cheek construction and convincing horsehair; improve crafted bronze finish.
FOCUS c: judge the exact shipped asset in three.js at native playing speed; keep all clips frozen.

## Lead's host capture

From this worktree, outside the sandbox:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs --prefix spearman-0ad-pbr-r3
```

Writes five `-<clip>-viewer.mp4`, `-turntable.mp4`, `-viewer-still.png`,
`-vs-panel-viewer.png` and a hashed capture receipt. **Pending lead execution.**
No Chromium launch, upload, push or publication performed by this lane.

## Reproducibility and learning

Editable blends, dense source, 2048 masters, frames and logs: `oad/pbr-r3/`.
`final-verified/` preserves the delivered source/maps and GLB. Sources and
CC BY-SA 3.0 credit remain in PROVENANCE/SOURCES/LICENSE-ART and asset.extras.

Cache mesh normals before changing coordinates in a high-poly loop; fetching
normals after every coordinate write triggered an expensive repeated update.
That slow intermediate process has exited; no host stop remains necessary.
Spatial torso culling is unsafe after rest-pose fitting: the inner upper arm
can occupy the same box. Pair thin garment layers during floor fitting, and
budget silhouettes individually before decimation.

Git staging was rejected by the sandbox (`index.lock: Operation not permitted`).
Changes are uncommitted for the runner. `oad/pbr-r3/commit-message.txt` contains
the required co-author trailer; `oad/pbr-r3/lane-only.patch` includes tracked
and new files plus binary diffs. `origin/master` is already an ancestor of HEAD.
No fetch, merge into master, commit or push was performed.

Final delivery verification: all 11 visual review files exist. ffprobe confirms
160-square H.264/yuv420p sprites with 36/48/54/24/48 frames at 4/6/14/12/4 fps
(three repeats), plus a 256-square, 96-frame, 12-second Cycles turntable at 8 fps.
Both video receipts match the delivered hash. Shipping maps, 2048 masters and
the preserved final copy match source-manifest.json. The final comparison,
close-ups, 48 px LOD1 sheet, joint sheet and motion samples were inspected.
