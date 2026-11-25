# Spearman painted lane — premium round 4

Branch: `astra/unit-anim-3d-spearman-0ad-painted`, continued from the round-three
commit and the existing master merge. Main GLB stays at
`tools/art/anim3d/units/spearman-0ad/spearman.glb`.
SHA-256: `366f770517d06e23499c0adb221e7243f07095e9396b206159ba167f5dc977d3`.

## What changed

Read the full premium feedback through the newest lead entry choosing painted
as the main lane, including 14a–f and the ranked a–g list. Reviewed the reference
panel/token and both lanes' round-three three.js comparisons before changing
forms. Read the Legatum unit skill, Blender modeling/materials/lighting/rendering
skills, project instructions, source scripts, provenance and prior lane note.

- Borrowed the PBR branch's convex aspis, bronze rolled lip, inset team band,
  broad raised rays and rounded boss. The recipe/palette source is
  `pbr_build.py` at `2f60247986ffad8cba305d79e2005a6d17b57def`.
  Rebuilt it in Blender for this lane's atlas; no PBR animation or texture buffers
  were copied. Protected rays, outer registers and boss against decimation.
- Tapered the muscle cuirass around the shoulders; added finished bronze hems,
  an oxhide belt and pectoral chase following the actual shell. Added folded
  ivory sleeves/cuffs and linen over the shoulders. The chiton has wider pleats
  and stronger thigh following at the hem. Clean leather strips replace collapsed
  bevel remnants. A part-ID render identified exposed pelvis skin: it is now
  fitted inside the chiton with the garment's hip/thigh blend, without cutting
  anatomical holes. Selection uses bone weights as well as spatial bounds so
  nearby hand vertices stay untouched.
- Kept the CC0 MPFB anatomy, with fuller arms, larger palms/fingers and restrained
  calf/thigh expansion. Replaced separate spherical knees with continuous shaped
  patella-to-ankle greaves, rolled ends and a shin keel.
- Jaw-length Corinthian cheeks, a true dark T aperture, curved brow and lifted,
  flared nape. Restored skin on the exposed neck instead of the previous dark liner
  pigment. Retained full crest volume with finer painted streaks, irregular tips
  and darker roots.
- Rebuilt a full folded cloak from both shoulders to the knees, with integrated
  team trim, shoulder drapes and brooches. Uses the approved cape bones.
- Adapted the PBR bronze palette and roughness separation, retaining stronger
  painted pigment shading and lower metallic response. This is **procedural
  Blender painted-style authoring**, not manual brushwork. Main bronze is
  roughness/metallic .57/.55; bright edges .34/.75; recesses .75/.38 before grain.

No paid tools, new downloads, new donors, stance offsets, joint edits or clip
changes. No zero scales. All Blender calls used the gated `blender` on PATH.
High-poly source: **38,042 authoring triangles / 611,840 subdivided triangles**.
Cycles CPU selected-to-active normal/AO bakes use those preserved source parts.
The inherited opposing-shell tangent repair and 25-degree relief limit remain;
the normal map is not an untouched bake. Masters and editable .blend remain in
`$ANIM_ROOT/lanes/spearman-0ad-painted-r4/`, outside git.

## Exact checks on this GLB

- Contract **PASS**, errors `[]`: **9,968 / 2,763 triangles**,
  **30 joints**, two named skinned LODs, one skeleton, one material, UV0 packed ORM,
  rigid prop weights, red COLOR_0 mask, +Z forward and exact embedded credit.
  **1,787,164 bytes**, below 2 MB. Existing strict premium validator retained;
  its documentation now describes the current layout.
- Four actual **2048×2048** PNG masters checked by PNG headers. Three actual
  **1024×1024** embedded WebPs, quality **88 base colour / 92 normal / 90 ORM**.
  Normal and ORM are lossy. Encoded channel RMSE (8-bit) is
  3.858 / 4.546 / 10.562;
  this is compression error, not an art-quality score.
- Khronos **0 errors / 0 warnings / 0 infos / 0 hints**.
- Exact approved round-six animation and skeleton comparison **PASS**:
  `639ad201654bf2a08b90c9b7b35c8f047ac1f5cf3531e7b7224f80e0e1d58f79`.
- Three.js 170 CPU loader/mixer, shared LOD skeleton/material, team shader and
  framing checks **PASS**. This is not browser decoding or a rendered-pixel check.
- Ground audit at **120 Hz**, both LODs **PASS**; minimum **-0.500462 mm**.
  Initial bind-space contact adjustment reached **46.9243 mm**; the later LOD1
  fit reached **5.3819 mm**. Motion was not changed. This is ground clearance,
  not a certificate of clothing or body intersections.
- Joint audit at **30 Hz**, all five clips and both LODs **PASS** against the
  .20 severe-collapse indicator; minimum axis scale **0.218389**. Significant
  elbow compression remains. This does not certify absence of candy wrapping.
- Validator regression suite **26/26 PASS** (7.274 s). Python parse, JavaScript
  syntax, import checker (**0 unresolved imports**) and `git diff --check` pass.
- No Rust or production UI change; unrelated Cargo/app suites were not run.
  `origin/master` was already an ancestor; no fetch or new merge was needed.

## Evidence and viewer handoff

CPU outputs use the exact final hashed GLB, Cycles/AgX, prefix
`spearman-0ad-painted-r4-`: five `<clip>-160.mp4`, `readability-48.png` with actual
LOD1, `vs-panel.png`, `closeups.png`, plus `motion-sheet.png`, `joints.png` and
`rear.png`. Packaging verifies main/still/joint manifest hashes and frame
freshness before accepting outputs. Video receipts record H.264/yuv420p,
three loops, correct game sampling rates and full decode. Native GLB timings
stay exact; whole sprite-frame sampling rounds nonintegral cycle durations.
Final encoded frame counts/fps: attack 51/14, death 18/4, hit 30/12, idle 24/4,
walk 24/6. The requested turntable is the lead's three.js recording, not a
substitute CPU turntable.

The existing credited CC0 Poly Haven HDRI, warm key, cool rim, soft shadows,
AO and ACES remain in the viewer. `record.mjs` now writes the comparison **first**;
`--stills-only` stops after the quick comparison and hash receipt. Default mode
still records all five clips and `<prefix>-turntable.mp4`.

From this worktree, on the lead's host:

```sh
PLAYWRIGHT_MODULE="$HOME/LegatumRuns/anim-pilot/oad/viewer-runtime/node_modules/playwright/index.mjs" node tools/art/anim3d/viewer/record.mjs --prefix spearman-0ad-painted-r4 --out "$HOME/LegatumRuns/anim-pilot/review/3d-v2"
```

Add `--stills-only` for the quick `spearman-0ad-painted-r4-vs-panel-viewer.png`.
Fresh browser evidence is **pending**: the browser connection returned
“The browser access host is unavailable”; the native fallback returned
“Computer Use was not approved to use Google Chrome”. No fresh three.js pixels
or playing-speed browser approval are claimed. The temporary local review server
was stopped. A Blender thumbnail cache write outside the sandbox failed harmlessly;
master save, export and all actual review renders succeeded.

## Honest verdict

**Technical contract passes. Premium art gate is NOT met.** The shield's broad
rays and rounded boss are cleaner; linen, bronze and leather now read as layers;
continuous greaves remove the old separate-knee look; the rear view shows a full
folded cloak. The body and hands still lack the painting's convincing heroic
weight at the review angle. The helmet is more shaped but still too plain;
its eye opening and cheek need more character. The crest remains a rounded
sculpted volume, not convincing fine horsehair. Bronze is still too uniform and
smooth beside the reference. Small shoulder/yoke overlaps and elbow compression
need further inspection. Do not call this excellent or approved.

FOCUS a: convincing helmet/armour silhouette, human hand mass and clean shoulder
cloth transitions; preserve all round-six motion data.
FOCUS b: richer local bronze recess/edge painting and less uniform surfaces,
judged in the fresh three.js comparison before further Cycles tuning.
FOCUS c: lead playing-speed and 360-degree review of cloth/armour clearance,
hand grip, sleeves and elbow compression; numerical checks alone do not pass art.

Non-obvious lessons: identify a bad patch with a part-ID render before repainting;
fit hidden anatomy using bone influence as well as spatial bounds; protect the
shield boss and rays explicitly when distributing the triangle budget.

## Final visual and runner handoff

Inspected the final same-size panel comparison, close-ups, 48 px LOD1 sheet,
and all five clips' joint samples after packaging. The shield boss is round;
the exposed pelvis patch is gone. Visible remaining defects include angular
shoulder cloth, a small light gap under the crest saddle, and the crest's
scalloped edge at close zoom. These keep the premium gate open. Playing-speed
browser review remains pending rather than inferred from stills.

`git add` failed: sandbox denied
`.git/worktrees/lane-7/index.lock` (Operation not permitted). Changes remain
uncommitted on this branch. No push or master merge was attempted.
Runner files in `$ANIM_ROOT/lanes/spearman-0ad-painted-r4/`:
`lane-7.patch` (includes the new script and binary assets; reverse check PASS)
and `commit-message.txt` (ends with the required gpt-6-astra co-author line).
The prior round-three lane note is preserved as `previous-lane-note.md`.
