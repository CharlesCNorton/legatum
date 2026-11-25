# Spearman painted lane — premium round 1

Branch: `astra/unit-anim-3d-spearman-0ad-painted`.
Main GLB: `tools/art/anim3d/units/spearman-0ad/spearman.glb`.
SHA-256: `c15f8a6ef4d1b12079d51bac87b4b2ce28adcf1e3d31e17eed5294fb7fabc250`.

## What changed

- Rebuilt a 64-segment convex aspis, thick rolled rim, raised twelve-ray sunburst,
  boss, concentric registers and rivets. Rebuilt the Corinthian dome, cheek/nose
  guards, dark eye recesses, seated crest support and full fluted horsehair mass.
- New leaf spearhead and butt spike, greaves, shaped bronze cuirass with palmette
  and pectoral ornament, leather pteruges, and folds in the native weighted cloak.
  Corrected the collar to crimson and the hands to skin. Welded coincident source
  seam vertices for smoother shading. Subdivision/bevel followed by decimation.
- A high-poly copy with extra subdivision and geometric noise displacement was
  baked to tangent normals and AO in Cycles CPU. Authored painted pigment graphs
  carry stronger directional form shading, grain and some AO in albedo. Bronze
  is deliberately rough and partly metallic; linen/wool/leather are dielectrics.
  This is procedural painted pigment, not a manual brush-painted texture.
- Actual 2048-square base colour, normal, AO and ORM masters retained under
  `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-0ad-painted-r1`. Three 1024-square base colour/normal/ORM maps are shipped and embedded.
  ORM is R AO, G roughness, B metallic on UV0. Editable master: `painted-master.blend`.
- Viewer: local CC0 Poly Haven studio HDRI (exact licence/hash in SOURCES.md),
  warm key, cool rim, filtered shadows, material AO, ACES, LOD selector and an
  exact-frame 12-second 360-degree idle turntable. No asset yaw was added.

## Contract and checks

- LOD0: **9783 triangles**; LOD1:
  **2846 triangles**. Exactly two named
  skinned meshes, one skeleton, **30 joints**, one shared material and one draw
  per active LOD. Both carry COLOR_0 red team masks and rigid prop weights.
- `validate_glb.py`: **PASS**, zero errors. GLB: 6,145,012 bytes.
- Khronos: **0 errors, 0 warnings, 0 infos, 0 hints**.
- Exact animation/skeleton comparison: **PASS**. Every channel, key time/value,
  bone transform, hierarchy and inverse bind equals approved round 6. Fingerprint:
  `639ad201654bf2a08b90c9b7b35c8f047ac1f5cf3531e7b7224f80e0e1d58f79`.
- Three.js 170 CPU loader/mixer/team material/LOD sharing/framing check: **PASS**.
- Ground check, both LODs at 120 Hz: **PASS**, worst -0.5000 mm against
  the 2 mm tolerance. New geometry was fitted in bind space; motion was not changed.
  This is a ground check, not a mesh-intersection certificate.
- Contract regression suite: **8/8 passed**. Import checker: **0 unresolved imports**.
  Python compilation, JS syntax and `git diff --check`: passed.
- All five 160 px H.264/yuv420p movies were decoded/probed: three loops each.
  Encoded frames/rates: attack 51/14 fps, death 18/4, hit 30/12, idle 24/4,
  walk 24/6. Whole-frame game-rate sampling rounds attack/hit/death cycle lengths;
  the GLB and lead's 30 fps viewer recording retain the exact approved timings.
- Broad repository static gates were also attempted on the existing branch HEAD:
  public claims passed; hygiene flagged four pre-existing matrix-multiplication
  expressions as email addresses in `units/spearman/donor_motion.py` and
  `round12c_review.py`; the unrelated art-set renderer exited 1. Those files were
  not changed here. This is not a claim of an all-green repository gate.

## Delivered evidence

`spearman-0ad-painted-r1-<clip>-160.mp4` for idle, walk, attack, hit, death;
`spearman-0ad-painted-r1-readability-48.png`; `spearman-0ad-painted-r1-vs-panel.png`;
`spearman-0ad-painted-r1-closeups.png`; `spearman-0ad-painted-r1-motion-sheet.png`.
JSON receipts cover contract, Khronos, motion identity, contact, runtime and video.
All were refreshed from the final GLB; packaging rejects stale frames by mtime.
The still/sprite evidence is **Cycles CPU / AgX**, not browser ACES output.

The lead records the browser videos outside the sandbox, from the lane worktree:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs --prefix spearman-0ad-painted-r1 --out "$HOME/LegatumRuns/anim-pilot/review/3d-v2"
```

Expected turntable: `spearman-0ad-painted-r1-turntable.mp4`. Browser videos and
turntable have **not** been recorded here, as requested. The native browser
playing-speed look, shadows and the full 360-degree view still need lead review.

## Honest verdict

**Technical contract passes; premium art gate is NOT met yet.** The shield,
helmet and crest are much rounder and the sunburst has genuine relief. At 48 px (the actual LOD1, not a downscaled LOD0)
it reads as a spear/shield unit. Beside the panel painting, however, the bronze
still looks too uniform/matte, cloth and skin remain plain, and the crest reads
as a sculpted fluted fan rather than convincing horsehair. Some neckline/skirt
faceting and attachment transitions remain visible in the close-ups. This is a
usable round-one comparison candidate, not something I would call excellent or
approved. The lead should compare both lanes before choosing the next look pass.

Non-obvious implementation lessons: manually packaged Blender UVs need V flipped
and tangent handedness reversed together; exported seam duplicates must be welded
before smoothing; preserve animation bytes outside Blender export; round props
need a protected simplification budget; fitting geometry to the original motion's
ground envelope prevents a larger crest/rim from invalidating approved death keys.

FOCUS a: refine crest strands and neckline/skirt transitions without new motion.
FOCUS b: richer bronze edge wear, engraved contrast and more convincing cloth/leather detail.
FOCUS c: keep all motion frozen; inspect browser clips and turntable at playing speed.

## Git handoff

The sandbox denied creation of `.git/worktrees/lane-7/index.lock`; nothing was
committed or pushed. All task changes remain in this worktree. The runner can
use `lanes/spearman-0ad-painted-r1/commit-message.txt` (with the required
Co-Authored-By line). A scoped binary patch is at
`lanes/spearman-0ad-painted-r1/lane-7.patch`. `origin/master` is already an
ancestor of HEAD; no fetch, merge into master or push was performed.
