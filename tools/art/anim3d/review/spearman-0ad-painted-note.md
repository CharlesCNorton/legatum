# Spearman painted lane — premium round 2

Branch: `astra/unit-anim-3d-spearman-0ad-painted`.
Main GLB: `tools/art/anim3d/units/spearman-0ad/spearman.glb`.
SHA-256: `9f860b78aa85c0a292fa3a02e5ebd1c6bef0a61b1bc1214360ad2655259651b1`.

## Changes

Continued from round 1; read both lanes' round-one comparisons and feedback
through the cloud review at 2026-11-25 02:36Z. Replaced the native mannequin
with a muscular CC0 MPFB 2.0.18 body fitted to the existing rest pose; transferred
0 A.D. weights using nearest-face interpolation, normalized and limited to four.
Real hands and feet, sandal straps, fuller cuirass, pleated linen, shaped knee
greaves, larger helmet, full sagittal crest with 105 tufts, and a wider lined
cloak with folds. The temporary fitting rig is removed. No new animation donor.

Retained the convex 64-segment shield and raised sunburst; compared the other
lane's shield contrast without copying its buffers. Increased pigment contrast
and roughness variation. High-to-low Cycles CPU normal/AO bakes use part/pigment
groups; 70,332 pre-decimation triangles, 1,131,232 subdivided reference triangles.
The base colour is procedurally authored painted shading, not manual brushwork.

Master and logs: `~/LegatumRuns/anim-pilot/lanes/spearman-0ad-painted-r2/`.
Actual lossless 2048 base colour/normal/AO/ORM masters remain outside git.
Three 1024-square WebPs ship inside/beside the GLB: base colour 243,366 bytes,
normal 202,402 bytes, ORM 293,048 bytes (quality 84/85/84). Data-map compression
is lossy; final browser inspection remains necessary. Packed ORM uses UV0.
Quantized normal/tangent/UV/weights plus shared identical animation buffer views
reduce the GLB to **1,985,664 bytes**. Required extensions: EXT_texture_webp and
KHR_mesh_quantization. Positions and approved animation samples remain floats.

The existing HDRI/warm key/cool rim/ACES viewer is retained. `record.mjs` now
adds a 512 px three.js still and a same-size vs-panel comparison to its five
clip movies and 12-second 360-degree idle turntable.

## Exact checks

- Contract: **PASS**, errors `[]`; **9,981 triangles LOD0 / 2,634 LOD1**.
  Two named skinned meshes, one shared material, one skeleton, **30 joints**,
  red COLOR_0 mask on both LODs, rigid single-bone props. One draw per active LOD.
- Khronos: **0 errors, 0 warnings, 0 infos, 0 hints**.
- Motion/skeleton identity: **PASS**, fingerprint
  `639ad201654bf2a08b90c9b7b35c8f047ac1f5cf3531e7b7224f80e0e1d58f79`.
  All channels, times, samples, transforms, hierarchy and inverse binds match
  approved round 6; all five original clip durations are unchanged.
- Three.js 170 CPU load/mix/LOD sharing/team material/framing: **PASS**.
  The image shim checks dimensions; it does not prove browser decoding/GPU pixels.
- Ground check at 120 Hz, both LODs: **PASS**, minimum **-0.50015 mm**, inside
  the 2 mm tolerance. Bind-geometry fitting leaves motion untouched. This is
  not a general collision or joint-deformation certificate.
- Validator regression tests: **25/25 pass** (8.219 s).
- Import checker: **0 unresolved local imports**. Python compilation,
  `node --check` on both changed JS files, `git diff --check`: **PASS**.
- Five 160×160 H.264/yuv420p movies: ffprobe and full ffmpeg decode **PASS**,
  three loops each. Encoded frames/fps: attack 51/14, death 18/4, hit 30/12,
  idle 24/4, walk 24/6. Whole-frame game sampling rounds the short nonintegral
  cycles; the GLB and native browser movies retain exact timing.
- `origin/master` is already an ancestor of HEAD. No fetch or merge needed.
  No Rust or production UI changes; broad unrelated suites were not rerun.

## Evidence and handoff

All required CPU artifacts are in `~/LegatumRuns/anim-pilot/review/3d-v2/`,
prefix **spearman-0ad-painted-r2-**: five `<clip>-160.mp4`, `readability-48.png`
(actual LOD1), `vs-panel.png`, `closeups.png`, `motion-sheet.png`, and `rear.png`.
JSON receipts cover contract, motion identity, Khronos, contact, runtime and
video validation. CPU evidence was regenerated from the final hashed GLB and
uses Cycles/AgX. The readability, motion and close-up sheets were inspected.

Lead command from this worktree, outside the sandbox:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs --prefix spearman-0ad-painted-r2 --out "$HOME/LegatumRuns/anim-pilot/review/3d-v2"
```

Expected browser outputs: `spearman-0ad-painted-r2-turntable.mp4`, five
`<clip>-viewer.mp4`, `viewer-idle.png`, `vs-panel-viewer.png`, and the asset-hash
receipt. **Host browser capture has not run here**, as instructed. Actual
MeshStandardMaterial/ACES tuning and playing-speed/360 review remain pending.

## Honest verdict

**Technical contract passes; premium art gate is NOT met.** Anatomy, folds and
silhouette have changed, but the final body still lacks the painting's heroic
mass. Shield-rim faceting is visible close up. The crest reads as a comb, the
neckline looks stiff, the helmet's face coverage is still too open, and bronze,
skin and cloth lack the painting's richness. The close-ups do not justify
calling this excellent or approved. Further art work and actual browser review
are necessary. Sampled five-clip sheets do not certify every joint deformation.

Non-obvious lessons: keep untouched high-resolution parts before decimation;
bake by part/pigment to avoid cross-surface rays; use a fresh Blender image when
saving resized textures to avoid stale 2048 payloads; merge LOD1 simplification
regions so per-tuft minimums do not exhaust the budget; zero quantized-weight
joint indices; deduplicate identical animation storage without changing samples.

## Git handoff

The sandbox denied creation of `.git/worktrees/lane-7/index.lock`; changes are
uncommitted. The runner can use `lanes/spearman-0ad-painted-r2/commit-message.txt`
(with the required co-author line). A scoped binary patch including new files
is at `lanes/spearman-0ad-painted-r2/lane-7.patch`. No push or merge into master
was performed.
