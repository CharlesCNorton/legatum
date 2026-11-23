# Spearman MPFB review — round 3

This remains an **art candidate, not production art approval**. The app still uses
its existing painting. All 19 shared feedback items, the previous running log,
the spearman-specific feedback, and all six installed Blender skills were read.
Sam's family-lead quality verdict is the bar; technical validity does not replace
comparison against the painting.

## What changed

The full source painting now supplies frozen rest-camera UVs on actual rigged
surfaces, with ray-visibility and facing feather masks. Generated bronze, wool,
linen and leather fills cover surfaces the painting never shows. Their original
PNG and crops are saved under the external master's `textures/generated/`;
`fills.prompt.txt` and `fills.lock.json` record the built-in imagegen prompt and
five file hashes. The static base is exempt from projection so painted feet and
shadows cannot remain on it during motion. It uses the shared #E9CFA0 cream top
and #B68A51 rim, correctly converted from sRGB to linear, with physical contact
shadows.

The camera now matches the painted base ellipse more closely. The guard uses a
calibrated planted spear and a stored hand target; ankle spacing is wider, the
cape has modeled folds and controlled flare, the leaf blade is larger and
beveled, and the crest has the source's swept profile. Linen is subdivided,
the baldric is a thick beveled leather ribbon, and the belt has a real buckle
frame and tongue. MPFB's original 19,158-vertex body and 53-bone rig are retained.

Lighting uses a warm upper-left key, softer fill and restrained cool rim.
A single alpha-masked histogram grade is fitted at rest and reused across all
clips; raw PNGs are retained. The projected painting includes painted lighting,
so its illumination layer is blended with physical PBR instead of receiving a
second full lighting pass. This is a deliberate reference-matching choice,
not a general relightable albedo reconstruction.

Every Blender invocation goes through `blender` on PATH, with `-b` and automatic
Python execution disabled. The obsolete lane lock and four-thread overrides are
removed. Cycles GPU/Metal selection and denoising are supported explicitly;
unavailable GPU selection fails rather than silently falling back to CPU.
Repeated animation samples are rendered once and copied byte-for-byte. Death's
last two PNGs therefore cannot differ because of stochastic GPU noise.

## Visual verdict

At **256 px**, chest engraving, linen folds, shield wear, warm skin and the cream
base are materially closer to the painting. The swept crest also matches better.
The hand, helmet profile and foot orientation still differ visibly. Source paint
stretches with the mesh in large motions, and transitions to physical/generated
fills need a host GPU review. This is **not nearly indistinguishable** from the
painting and does not meet the final premium-art bar yet.

At **64 px**, the source's gold/red/cream hierarchy, sunburst, crest and braced
silhouette are much more recognizable. Rest matching has improved substantially,
but the grip and foot placement still prevent a one-for-one match. Motion reads
as a genuine articulated 3D figure, not a moving cutout.

Evidence is under `ANIM_ROOT/review/3d-v2/`: `spearman-f-restpose-compare.png`
(painting/render/crossfade/split, both sizes), `spearman-c-details.png`, all five
`spearman-e-*-strip.png` / WebPs, and `spearman-round3.mp4`. Diagnostic silhouette
IoU and RGB error live in `spearman-look-metrics.json`; those are not quality
approval metrics. Earlier GPU evidence and the received atlas are preserved in
`round2-gpu/`; the pre-projection editable master is preserved separately.

## Checks and handoff

The measured results below use CPU Cycles; no host GPU approval is implied. No Rust, rules, app runtime,
WASM or public deployment changes are part of this work.

The lead runs the exact **host GPU handoff** in `PLAYBOOK.md`: Cycles GPU/Metal,
64 samples, c first to refit the grade, then detail/d/all five clips, pack,
validate and audit. Eevee/Metal remains supported. Inspect the new GPU rest
comparison and motion, then run the browser/art gate and Claude art review before
integration. This branch is not pushed or merged by this task.

Non-obvious implementation findings: MPFB's masks remove helper vertices from
evaluated geometry, so projection must recover original vertex indices without
putting helpers into the visibility BVH. Camera-space silhouette edits under a
rotated bone belong in local mesh data; object TRS decomposition can lose shear.
The static base must not inherit the figure painting's feet or shadows. Grade
once at rest and freeze the LUT across motion; never refit each frame.

## Final round-3 results

- Atlas: **195,870 bytes**, WebP **quality 70**, all **40 frames**, transparent
  **2560 × 1280**, unchanged frame/clip JSON and `(127,221)` anchor. SHA256
  `3ad42b11c8a76555a3a8cbdaa66f74d7d36fb8cd9ebe035e670536c5f39ed23e`.
- Source renders: CPU Cycles, **384 px / 24 samples** for c/d/all five clips;
  **512 px / 32 samples** for details. Every packed frame uses the same current
  source master and histogram-grade hashes. Raw renders are preserved.
- Saved-rig audit: **40 samples, zero findings**. Original body/rig, baked cloth,
  fixed physical cream base, floor/camera bounds, held-weapon grip and spear
  centerline clearance pass. This is not a full skin/cloth intersection solver.
- Decoded validation: **PASS** dimensions, metadata, all frames, alpha, transparent
  padding, motion, clipping margins, byte cap and held death. Terminal PNGs are
  identical **bytes and pixels**, including after grading.
- Regression tests: **2 PASS**. Syntax: **21 Python / 2 Bash / 2 JSON PASS**.
  Working-tree hygiene: **30 text files, zero findings**. Diff whitespace passes.
  The video encoder's final two-thread cap also passed syntax and real encoding.
- Video: H.264, **544 × 380**, **240 frames**, **24 fps**, **10.000 seconds**, checked
  with ffprobe. Native-size strips and decoded-atlas representative frames were
  visually inspected; final host GPU playback/art approval remains with the lead.
- Review data: `spearman-final-report.json`, `spearman-g-decoded-atlas.png`,
  `spearman-f-restpose-compare.png`, `spearman-c-details.png`, per-clip strips and
  `spearman-round3.mp4` under the external review directory.

The base correction was material-only: it removed projection shaders and unused
base UV/mask data from the saved master/clips, preserved and asserted existing
cloth caches, and rebound clip source hashes. `project.py` makes the same
exemption during a full rebuild. All dependent frames were rerendered afterward.

## Runner handoff limitations

Git staging failed because the sandbox denied this worktree's `index.lock`;
round 3 remains uncommitted. The runner must commit it with the requested
co-author trailer, merge the two newer `origin/master` browser-test/CI commits,
and run the post-merge determinism/pin checks. No fetch or push was attempted.
The browser distinctness check reached Chromium using the main checkout's
Playwright dependency, but launch failed with `bootstrap_check_in ... Permission
denied (1100)`. It did not evaluate the images. Run the committed-tip gates and
final art review on the host; source/atlas validation above is not art approval.
