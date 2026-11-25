# Spearman PBR — round 2 lane handoff

Branch: `astra/unit-anim-3d-spearman-0ad-pbr`; continues round-1 commit `beeb648e`.
Main asset: `tools/art/anim3d/units/spearman-0ad/spearman.glb`.
SHA-256: `dd0070b9fbc87cca685e24f7707df0b93e2a3d884fa18c27f9ad21ae74283acf`.

**Verdict: FAIL the premium visual gate; technical gates PASS.** This is a
round-2 review candidate. The silhouette and material responses improve, but
the shipped close-ups still expose coarse crest tips, clothing intersections
and simplified armour. It does not yet belong beside the premium painting.
No browser or playing-speed art approval is claimed.

## Changes against round 1

- Read both round-1 lane comparisons and close-ups, the lead's ranked critique,
  and the 02:36Z cloud additions. Retained the PBR lane's crisp round shield;
  borrowed the painted lane's longer pteruges and clearer material/value bands.
- Replaced exposed source anatomy with a muscular MPFB 2.0.18 CC0 body, fitted
  to the original rest pose. Native weights transfer with Blender Data Transfer
  nearest face interpolation, normalized and limited to four influences. The
  temporary fitting rig is discarded. The original skeleton remains unchanged.
- New muscle cuirass with pec/ab relief, fuller calf/knee shells and fitted
  sandal straps; larger headgear; a volumetric front-to-back crest arc with
  layered locks; a broad folded crimson cloak and darker lining on the same
  three cape bones. A continuous shoulder mantle replaces the old scarf.
- Preserved the 64-segment convex aspis, rolled lip, raised sunburst, leaf spear
  and butt spike. Protected the shield and helmet round silhouettes before
  simplifying the other geometry. Rigid props retain original single-bone sockets.
- Cycles CPU high-to-low normal/AO bake from 228,144 dense triangles. Warm bronze
  with roughness variation and smoother edges; matte off-white linen, semi-matte
  leather and crimson wool. Pigment has gentle gradients and variation, without
  baked directional lighting or AO. Normal-map strength is .45.
- **9,504 triangles LOD0 / 2,847 LOD1; 30 joints; one shared material and skin.**
  Two named skinned meshes in one GLB; one draw call when selecting one LOD.
  Both LODs carry COLOR_0.r team masks. ORM is UV0, R AO / G roughness / B metallic.
- **1,895,720-byte GLB (1.896 MB decimal)**. Three embedded **1024×1024 WebP**
  maps, from **2048×2048 PNG masters** outside git. Base/normal/ORM payloads are
  225,642 / 204,224 / 341,798 bytes. Quality 85/90/85, EXT_texture_webp, compact
  normals/tangents/UVs/weights via KHR_mesh_quantization. Positions and animation
  stay float32. Compression is lossy: mean channel errors, on a 0–255 scale,
  are base 2.87/1.41/2.72, normal 4.05/2.57/4.14, ORM 8.52/4.65/7.00.
  Inspect the browser before accepting that compression tradeoff.
- Kept the pinned Poly Haven Studio Small 09 CC0 HDRI, warm key, cool rim,
  soft shadows, SSAO and ACES viewer. Recorder now adds an actual three.js
  512 px still and side-by-side painting comparison, in addition to the
  five viewer clips and twelve-second idle 360-degree turntable.

## Exact checks on the delivered hash

- `validate_glb.py`: **valid=true**, errors=[]; 9,504/2,847 tris, 30 joints,
  two named meshes, one material, all three maps 1024 and declared master 2048.
- Khronos validator 2.0.0-dev.3.10: **0 errors, 0 warnings, 0 infos, 0 hints**.
- `test_validate_glb.py`: **14/14 PASS**. `test_pbr_contract.py`: **8/8 PASS**,
  including missing maps, separate AO/UV, LOD names/mask, master size and shared
  material negative cases. Corruption tests handle normalized integer attributes.
- `check_pbr.py`: all five animation input/output buffers **byte-identical** to
  approved round 6; original hierarchy/transforms and inverse-bind bytes identical.
  Both LODs sampled at 120 fps: worst floor penetration **1.494 mm**, within the
  existing 2 mm tolerance. This is floor contact only, not a general collision test.
  Rest shape fitting does not change animation, root yaw or the +Z asset axis.
- Three.js 170 GLTFLoader/AnimationMixer CPU checks: **PASS** for loading, both
  LODs/shared skeleton and material, animation, team mask and framing. Image
  decoding is a header shim: this is explicitly not browser pixel/codec proof.
- Five 160×160 H.264/yuv420p sprite MP4s verified with ffprobe: three repeats
  each; idle 36 frames at 4 fps, walk 48 at 6, attack 54 at 14, hit 24 at 12,
  death 48 at 4. Legacy sprite rates affect apparent playback speed; native
  GLB timings are unchanged and must be judged in the host viewer.
- Final Python compilation (10 files), both JS syntax checks, kit import check
  (0 unresolved) and diff whitespace check **PASS**; results are recorded in `oad/pbr-r2/final-static-checks.log`.
- No Rust or production app code changed; no unrelated Cargo/app suite run.

## Review evidence and remaining gaps

All new review files use `spearman-0ad-pbr-r2-`: five `<clip>-160.mp4`,
`readability-48.png`, `vs-panel.png`, `closeups.png`, `motion-contact.png`, and
contract/Khronos/motion/runtime/build/texture/video JSON receipts. The main
comparison, closeups and representative frames from all five clips were
visually inspected. These renders import the actual shipped GLB in Cycles/AgX.

1. The reference still has a much stronger heroic stance, sculpted anatomy and
   ornate, tailored construction. More muscular source anatomy alone has not
   solved the visual proportion gap in the frozen pose.
2. The crest is fuller, but its locks retain coarse triangular tips. Helmet
   cheek plates and armour relief remain too simple. The shield rim is round,
   but the no-visible-faceting gate is not passed.
3. Shoulder skin still pokes through the mantle in the close-up; linen and
   pteruges have small intersecting/sliver edges. Sampled motion sheets cannot
   establish clean shoulders/elbows/knees or complete collision clearance at speed.
4. Bronze reads as metal, but it and the cloth lack the painting's deliberate
   recess contrast, rich trim, linen folds and believable leather detail. Lossy
   ORM/normal compression also needs the actual browser judgement.
5. At 48 px the shield/crest identify the unit, but fine detail collapses. The
   idle silhouette remains less broad and grounded than the painted reference.

FOCUS a: clean garment boundaries and anatomically convincing shoulder/arm proportions.
FOCUS b: refine crest tips, helmet face construction and crafted bronze/cloth surface detail.
FOCUS c: review the exact shipped asset in three.js at playing speed; keep all motion frozen.

## Lead's host capture

Run from this worktree, outside the sandbox:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs --prefix spearman-0ad-pbr-r2
```

Writes `spearman-0ad-pbr-r2-turntable.mp4`, five `-<clip>-viewer.mp4`,
`-viewer-still.png`, `-viewer-vs-panel.png` and hashed capture receipts.
**Pending lead execution**: these browser outputs and playing-speed review are
not completed by this lane. No Chromium launch, upload or publication performed.

## Sources, reproducibility and learning

Editable Blender, high mesh, 2048 masters, 1024 intermediate PNGs, frames and
logs: `~/LegatumRuns/anim-pilot/oad/pbr-r2/`. MPFB input hashes and CC0 license
are recorded in SOURCES/PROVENANCE; the combined derivative remains CC BY-SA 3.0
and retains credit in asset.extras. No paid services or new motion sources used.

Apply MPFB helper masks before removing modifiers or its fitting surfaces can
escape into the render. Reserve round silhouettes before decimation. Keep the
cuirass on continuous torso weights: nearest transfer can pick arm weights for
a wide breastplate. Tangent handedness must match the exported UV orientation.

Git staging was blocked: `index.lock: Operation not permitted`. Changes remain
uncommitted for the runner. `oad/pbr-r2/commit-message.txt` contains the requested
co-author trailer; `oad/pbr-r2/lane-only.patch` includes tracked and new binary
files. `origin/master` is already an ancestor of HEAD. No fetch, master merge
or push performed.
