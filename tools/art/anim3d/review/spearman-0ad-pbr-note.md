# Spearman PBR — round 1 lane handoff

Branch: `astra/unit-anim-3d-spearman-0ad-pbr`. Main asset remains
`tools/art/anim3d/units/spearman-0ad/spearman.glb`.
Final SHA-256: `6d1a6fc8b320f61d3632606dac8c6c7f3442164ff195f447b120d7879825503f`.

**Verdict: FAIL the premium visual gate; technical gates PASS.** This is a
reviewable round-1 look candidate, not art approval or a replacement for the
approved painting. The forms and material responses improve on round 6, and the
48 px unit is legible, but the side-by-side still falls visibly short of the
reference's craftsmanship and richer surface treatment.

## What changed

- New 64-segment convex aspis with rolled rim, raised twelve-ray sunburst,
  rounded boss, beads and rivets; new round Corinthian dome, separate nasal,
  cheek guards and eye opening; full sculpted crest with tapered strand ridges.
- New leaf spear blade/socket/butt spike, tapered greave shells with real
  thickness and rolled lips, leather pteruges, garment-following cuirass trim,
  embossed scrollwork, and rest-space cloak folds. Native anatomy and weights
  are refined with subdivision; props remain on the original rigid sockets.
- Cycles CPU normal and AO bakes from a 232,752-triangle dense source. Base colour
  has only pigment variation and a gentle vertical value gradient; AO is not
  multiplied into it. Bronze uses metallic response/roughness variation and
  smoother edge pigment; linen, leather and crimson cloth use distinct roughness.
- 2048-square masters on disk; three 1024-square shipping PNGs (base colour,
  tangent normal and ORM). ORM uses UV0, R AO / G roughness / B metallic.
- Both LODs in the same GLB, named `spearman_LOD0` and `spearman_LOD1`:
  **9,686 / 2,838 triangles**, one shared material, one shared 30-joint skin,
  one primitive per LOD. Select one mesh at runtime; no MSFT_lod. Both carry
  COLOR_0.r masks for crest, shield rim and cloak trim.
- Viewer has the pinned Poly Haven Studio Small 09 CC0 HDRI, warm key, cool rim,
  soft shadow filtering, SSAO and ACES. It hides LOD1 by default. `record.mjs`
  accepts `--prefix` and records a twelve-second 360-degree idle orbit.

## Motion preservation and validation

All five original clip input/output buffers are **byte-identical** to approved
round 6, including timings and the round-5/6 fixes. Original skeleton node
transforms and inverse-bind bytes also match exactly. No baked display yaw;
GLB forward remains +Z. Rest geometry is fitted against frozen poses for contact.

- `validate_glb.py`: **valid=true**, no errors. Enforces named LOD layout,
  budgets, shared skin/material, three maps, ORM UV0, rigid weights, team coverage
  separately on both LODs, axes, credit and the five clips.
- Khronos: **0 errors, 0 warnings, 0 infos, 0 hints**.
- `test_pbr_contract.py`: **5/5 passed**, including negative LOD-name, normal-map,
  separate-AO and LOD1-team-mask probes.
- `check_pbr.py`: exact rig/clip equality passed; both LODs evaluated at **120 fps**,
  worst floor penetration **1.493 mm**, inside the existing 2 mm tolerance.
  This checks floor contact, not all mesh-to-mesh intersections. LOD1's final
  body surface is a few millimetres above LOD0 after simplification; the report
  retains that measurement rather than claiming identical body contacts.
- Three.js GLTFLoader/AnimationMixer CPU runtime, shared LOD skeleton/material,
  textures/team shader and framing checks: **passed**.
- JS syntax checks, Python compilation, `kit/check_imports.py` (0 unresolved),
  `git diff --check`: **passed**. No Rust or app production code changed.
- All five encoded sprite MP4s: ffprobe confirms 160×160, H.264 yuv420p,
  exact frame counts and three repeats at game fps (4/6/14/12/4).
- Repository static gates on committed HEAD: public-claims passed; hygiene
  flagged existing matrix-multiplication expressions as email addresses in
  untouched `spearman/donor_motion.py` (131, 132, 189) and
  `spearman/round12c_review.py` (52). These are not lane modifications.
- Repository-wide `tools/gates/art.py` attempt failed inside `render-sets.mjs`;
  no broad distinctness pass is claimed. That gate archives committed HEAD,
  so it cannot certify the uncommitted lane changes in this sandbox.
- Browser rendering, playing-speed review and viewer turntable capture remain
  with the lead. CPU render sheets are Cycles/AgX, not browser/ACES screenshots.

## Review files

All files are under this review directory, prefixed `spearman-0ad-pbr-r1-`:
five `<clip>-160.mp4`, `readability-48.png`, `vs-panel.png`, `closeups.png`,
`motion-contact.png`, and JSON build/contract/Khronos/motion/runtime/video receipts.
Masters, dense source, texture masters, frame sequences and logs are under
`~/LegatumRuns/anim-pilot/oad/pbr-r1/`.

Run from this worktree outside the sandbox:

```sh
node tools/art/anim3d/viewer/record.mjs --prefix spearman-0ad-pbr-r1
```

This writes `spearman-0ad-pbr-r1-turntable.mp4` and the five `-viewer.mp4` files,
with the GLB hash and decoded stream receipts. It does not publish or upload.

## Remaining visible gaps, ranked

1. Torso/armour boundaries and ornament still read as simple procedural forms;
   the reference has much stronger sculpted anatomy, layered fabric, tailored
   edges and crafted decoration. The body and hands are still recognisably the
   inherited low-detail source, despite subdivision and corrected hand pigment.
2. Helmet reflections retain a broad, uneven highlight, and the crest remains
   too clean and regular. The outer shield is round, but small relief edges and
   strand ends still need the close-up quality pass. Do not call the no-faceting
   gate passed merely because there are more triangles.
3. Surface richness remains too restrained: linen weave, leather stitching,
   local bronze wear/recess contrast and foot dirt need a more deliberate atlas
   pass. The current gentle procedural variation is not the painting's finish.
4. The square sprite camera keeps the full death/spear extent, so death's figure
   fills less of its 160 px frame than idle; the 960×640 viewer fit passes the
   existing 65–70% figure-height check. No clip motion was changed to improve framing.

FOCUS a: fitted torso/armour construction and refined helmet/crest forms.
FOCUS b: deliberately authored material detail, especially linen/leather/bronze recesses.
FOCUS c: keep every approved animation byte frozen; inspect new geometry collisions at speed.

## Reproducibility and handoff

`pbr_build.py` asserts the approved source hash. The 512 bake flag is iteration
only; the final build has 2048 masters. `pbr_render.py` imports the actual shipped
GLB. Nonplanar faces must be triangulated before duplicating the high bake mesh:
otherwise selected-to-active projection creates false cheek-plate normal seams.
Metal pigment must bake through emission; a diffuse-only pass makes metallic
areas black. These are pipeline findings, not changes to the approved motion.

The commit attempt was blocked by `index.lock: Operation not permitted`.
Changes remain uncommitted for the runner; the commit message (with requested
co-author trailer) is `oad/pbr-r1/commit-message.txt`; the complete lane-only
binary patch is `oad/pbr-r1/lane-only.patch`. No push or merge was attempted.
`origin/master` is already an ancestor of HEAD; no fetch or merge was needed.
