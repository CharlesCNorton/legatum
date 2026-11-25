# Spearman painted lane — premium round 3

Branch: `astra/unit-anim-3d-spearman-0ad-painted`, continued from round two.
Main GLB: `tools/art/anim3d/units/spearman-0ad/spearman.glb`.
SHA-256: `692320d217f41db9f65b791c7a5c71009a35451efd126d1bafda2989746aa175`.

## Changes

Read feedback through the cloud reviewer at 2026-11-25 03:18Z, both reference
paintings, the installed Legatum/Blender skills, the prior lane note, source
provenance and both lanes' round-two Cycles and three.js comparisons.

Retained the CC0 MPFB 2.0.18 body pipeline and native nearest-face interpolated
weight transfer, normalized and limited to four influences. Fuller limbs;
continuous shoulders, thighs, knees and torso. Initial idle-only face culling
was rejected when the overhead-attack joint view exposed a missing shoulder.
Covered central torso vertices now fit inside the cuirass and match its
spine/chest blend, including vertices previously controlled by hip/spine.
Concealed facial geometry is replaced by a dark rigid liner inside the helmet.
No temporary MPFB rig ships.

Closed the helmet around the temples/nape with actual eye and mouth openings,
nasal bridge and cheek borders. Replaced the 105 spike-like tufts with a rounded
fluted horsehair mass and painted radial streaks. Rebuilt pectoral/abdominal
cuirass relief, lowered the shoulder drape, retained the wide folded cloak,
and integrated its team trim into the cloth surface. The convex aspis retains
its 64-segment outline, 96-segment rolled rim, continuous inner register and
protected raised sunburst rays. Greaves, pleated linen, pteruges, leaf spear,
butt spike and rigid prop sockets remain.

Simplify outer shells before adding thickness, including LOD1; triangulate
before UV packing/baking. Preserve high-resolution parts before decimation.
Cycles CPU normal/AO transfer uses a **639,712-triangle** subdivided reference
from **39,624** authoring triangles. Opposing-shell normal rays caused black
patches: baked tangent vectors are hemisphere-corrected and limited to a
25-degree relief cone. This bounds the transfer; it is not an untouched bake.
Paint is procedural Blender shading, not manual brushwork. Main bronze is
roughness .60 / metallic .32 before grain. No paid tools or new external assets.

The later reviewer stance-offset suggestion was not used because the task
explicitly locks round-six motion. The skeleton, timings and clips are unchanged.

## Final exact checks

- Contract **PASS**, errors `[]`: **9,911 / 2,819 triangles**,
  **30 joints**, two named skinned LODs sharing one skeleton/material,
  single-bone rigid props, red COLOR_0 mask, UV0 packed ORM, +Z, no baked yaw,
  exact embedded credit. **1,610,900 bytes**, below the new strict 2 MB gate.
- Actual **2048×2048** base colour/normal/AO/ORM masters verified outside git;
  three actual **1024×1024** delivered WebPs, quality 84/85/84. Data maps are lossy.
- Khronos **0 errors / 0 warnings / 0 infos / 0 hints**.
- Exact animation/skeleton comparison **PASS**; fingerprint unchanged:
  `639ad201654bf2a08b90c9b7b35c8f047ac1f5cf3531e7b7224f80e0e1d58f79`.
- Three.js 170 CPU loader/mixer, LOD sharing, team material and framing **PASS**.
  This checks texture dimensions, not browser decoding or GPU pixels.
- Ground audit at **120 Hz**, both LODs: **PASS**, minimum
  **-0.50048 mm**.
  Rest-geometry projection initially moved some vertices by up to **107.23 mm**;
  this is disclosed and does not alter motion. It is not an intersection certificate.
- Joint audit at **30 Hz**, all five clips and both LODs: no axis scale below
  the .20 severe-collapse indicator; minimum **0.222591**.
  This is substantial elbow compression, not a blanket candy-wrap pass. The
  final joint sheet was inspected; shoulder continuity is restored. Clothes,
  joint transitions and intersections still need playing-speed review.
- Validator regression suite **26/26 pass** (8.859 s).
- Import checker **0 unresolved imports**; Python compilation, JS syntax,
  `git diff --check`, and reverse-check of the runner patch **PASS**.
- Five 160 px movies: H.264/yuv420p, three loops, full ffmpeg decode **PASS**.
  Encoded frames/fps: attack 51/14, death 18/4, hit 30/12, idle 24/4, walk 24/6.
  Whole-frame sprite sampling rounds short nonintegral cycles; GLB timing is exact.
- Cycles turntable: **256×256, 96 frames, 8 fps, 12 s**, full decode **PASS**.
- `origin/master` is already an ancestor of HEAD; no fetch/merge was needed.
  No Rust or production UI changes; unrelated full suites were not run.

## Delivered evidence

All CPU outputs are in `~/LegatumRuns/anim-pilot/review/3d-v2/`, prefix
**spearman-0ad-painted-r3-**: five `<clip>-160.mp4`, `readability-48.png` (actual
LOD1), `vs-panel.png`, `closeups.png`, `motion-sheet.png`, `joints.png`, `rear.png`,
and `turntable-cycles.mp4`. JSON receipts cover contract, exact motion,
Khronos, runtime, ground, joint deformation, textures, build and video streams.
Final images and movies were regenerated from the final hashed GLB. A stale
intermediate delivery was correctly rejected by the hash/freshness guard.

The final panel comparison, close-ups, 48 px sheet, joint sheet and sampled
turntable angles were inspected. CPU evidence is Cycles/AgX. Browser access
returned **“The browser access host is unavailable.”** No new three.js still,
viewer movie or browser turntable was captured here. The host capture remains
the lead's designated handoff; no renderer parity or premium approval is claimed.

From this worktree, outside the sandbox:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs --prefix spearman-0ad-painted-r3 --out "$HOME/LegatumRuns/anim-pilot/review/3d-v2"
```

This writes `spearman-0ad-painted-r3-vs-panel-viewer.png`,
`spearman-0ad-painted-r3-turntable.mp4`, five viewer movies and an asset-hash
receipt. The existing CC0 HDRI, warm key/cool rim, AO and ACES are retained.

## Honest verdict

**Technical contract passes; premium art gate is NOT met.** Shield contour,
sunburst integrity, crest tips and body continuity improve on round two. The
painting still has much richer bronze, anatomy and cloth. The helmet reads too
smooth and generic, the torso relief is weak in the review view, hands are small,
and greaves/knees remain segmented. A small dark collar overlap remains visible;
there is no claim of collision-free clothing. The crest is cleaner but still a
sculpted mass, without the painting's fine hair edge. Do not call this excellent.

FOCUS a: improve helmet character, torso/limb proportions and knee transitions;
keep the continuous MPFB body and the exact approved skeleton/clips.
FOCUS b: richer painted bronze/linen separation and finer crest root/edge detail,
judged in the actual MeshStandardMaterial/ACES viewer.
FOCUS c: review all five clips and the 360 turntable at speed for remaining
clothing overlaps and elbow compression; do not edit the approved motion.

## Git and runner handoff

`git add` failed: sandbox denied `.git/worktrees/lane-7/index.lock`. Nothing was
pushed or merged. All changes are left on this worktree. Runner files:
`lanes/spearman-0ad-painted-r3/lane-7.patch` (binary patch including new scripts)
and `commit-message.txt` (required gpt-6-astra co-author line). The patch passes
`git apply --check --reverse` against this working tree.

Non-obvious lessons: visible body coverage must be checked through all clips;
outer/inner shell decimation must share topology; tangent bakes can hit opposing
shell faces; preserve shield boundaries and rays explicitly; bind body and armour
with compatible torso weights; reject media whose source hash is stale.
