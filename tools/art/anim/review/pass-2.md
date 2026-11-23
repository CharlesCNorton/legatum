# Pass 2 — full evidence review; fixes proposed for pass 3

**Verdict: not approved.** The paint, identity, figure scale and returned stone
are good. The horse death, cannon fragmentation, visible mask scraps, and draw
cost fail. Changes below are code/rig fixes awaiting the lead's next render;
there are no pass-3 renders or post-fix browser timings in this review.

## Evidence inspected

Opened all four full per-unit sheets; all 20 native 256 px and 20 map captures;
all frames decoded from all 20 animated WebP previews; mirrored parchment,
300/600-token stress captures and `gallery-1000.png`. This is 68 visual files.
Read `metrics.json` and all four packing reports. Preview frames were inspected
as sequences at native size, not played in a browser: smooth playback remains
unverified. The 1000 px screenshot incorrectly showed the bottom stress panel;
capture now scrolls to the top before taking it.

For every clip the checklist included joint seams/gaps/stretching, unseen paint
behind moving parts, solid weight versus flat sliding, stationary planted stone,
source scale, alpha on grey and parchment, map silhouette, pops and loop wrap.
The following judgments describe pass 2, not the unrendered revisions.

## Per-unit and per-clip critique

| Unit / clip | Native-size finding, hidden paint and weight | Map/continuity judgment |
| --- | --- | --- |
| Spearman idle | Identity, bronze, crest and scale match; mild softening, small rectangular discontinuity below shield; no obvious large shoulder split. Small breathing reads as a layered painting. | Readable, base stable; sampled cycle closes without a large jump. |
| Spearman move | Cream blocks travel with feet; hip/hem sections slide, no articulated knee bend. The shield edge exposes missing torso/cloth. | March is distinguishable but sliding feet weaken weight; scraps flicker across samples. |
| Spearman attack | Spear swing is clear, but a cloak strip travels with it; hand pivots while upper arm scarcely follows. Square gap under shield; needs hidden cloth paint or less reveal. | Strong silhouette change; continuous anticipation/strike/recovery samples, not a volumetric thrust. |
| Spearman hit | Readable restrained recoil; shield/body boundary still a cut edge. | Clear at 256, subtle on map; sampled return to neutral is clean. |
| Spearman death | Foot/kit crosses the front rim: this is genuine occlusion, not stone movement. Figure looks folded into a sitting cut-out, rather than lying with convincing contact. | Low death silhouette reads; held ending stable, volume/contact fail. |
| Horseman idle | Rider/horse identity and scale retained. Four-frame breath is restrained; no large isolated seam in this capture, but rider/saddle surface is only the visible painting. | Recognizable horse; four samples cannot certify smooth breath. |
| Horseman move | Cream hoof fragments, cut hip/hock edges and straight swinging leg sections. Rider follows the horse but weight transfer remains mechanical. | Trot is legible; eight samples retain cadence, foot scraps visibly pop. |
| Horseman attack | Rider's spear arm pivots as a piece; exposed strips remain near original hand/shaft. Saddle and shoulder reveal missing paint when rider leans. | Mounted attack distinguishable; recovery samples coherent, no convincing torso turn. |
| Horseman hit | Small recoil preserves outline; rider and horse react as coupled layers. No large new gap evident in the selected capture. | Subtle but readable; neutral return coherent. |
| Horseman death | **Worst horse clip:** horse and rider tip together, legs rise, torso stays suspended over disc. Rider ends sideways/upended instead of pitching off a collapsing horse. Hidden saddle/neck surfaces cannot support this turn. | Reads as card flip, not collapse. Held ending does not make it plausible. |
| Field cannon idle | Uniform, barrel and wheels match source scale; slight softening. Neutral configuration conceals incorrect ownership around arm, wheels and carriage. | Excellent unit silhouette; quiet four-frame breath. |
| Field cannon move | **Blocker:** wheel arcs/spokes disappear and reappear; rotated partial wheel textures expose their original barrel occlusion. Leg/ramrod scraps and cream foot fragments float. | Defects survive at map size; large popping, not a solid rolling gun. |
| Field cannon attack | Recoil small; muzzle smoke faint and outlined rather than dense. Barrel movement exposes incomplete underlying carriage paint; sleeve/contact needs scrutiny. | Firing barely reads on terrain. Six packed frames weaken recoil timing; not approved. |
| Field cannon hit | Wheel/body layers separate, with a disconnected wheel arc near crew hand. | Visible broken silhouette; three-frame timing is coarse. |
| Field cannon death | **Blocker:** sleeve/cloth/leg shards stay suspended where crew stood. Falling crew is a cut-out, gun remains recognizable. | Clearly broken even on terrain; held shards persist. |
| Spartan hoplite idle | Lambda shield, red cape, helmet and height match. Neutral edges mostly coherent; subtle flat breath. | Readable, stable base; sampled loop closes. |
| Spartan hoplite move | Cream foot chips and hip/skirt/cape cut lines; leg swing slides under torso rather than carrying weight. | March visible but mechanical; chips pop against stone. |
| Spartan hoplite attack | Thin spear stays readable; arm pivots around the hand and shield reveals a small notch/hidden cloth. No convincing depth turn. | Good attack silhouette, coherent sampled recovery. |
| Spartan hoplite hit | Cleanest limited-motion clip; subtle cut edges at shield/hip, no major open joint at selected frame. | Readable but understated; return to neutral coherent. |
| Spartan hoplite death | Whole torso inclines as a flattened card, one leg remains below it; final figure hovers rather than resting on its side. Missing backside prevents a convincing roll. | Death silhouette discernible, hold stable, weight/contact fail. |

Across all four: the stone footprint stays planted and the neutral figure scale
matches the painting. No broad matte halo is obvious on either grey or parchment;
there are soft/lossy thin edges, plus explicit cream fragments on moving feet
that must not be mistaken for clean alpha. Map-size reductions hide some seams,
but cannot excuse failures at 256 px. The stress screenshots are densely crowded
and are performance evidence, not evidence that individual animation is good.

## Pass-2 measured numbers

| Unit | Atlas bytes | Quality | Packed frames |
| --- | ---: | ---: | ---: |
| Spearman | 179,524 | 70 | 40 |
| Horseman | 198,592 | 60 | 34 |
| Field cannon | 190,716 | 60 | 27 |
| Spartan hoplite | 199,128 | 70 | 40 |

All are below 200,000 B; horseman has only 1,408 B spare, hoplite 872 B.
These are measurements of the old pass-2 atlas, not predictions for pass 3.
The quality floor remains 60 and the hard byte ceiling remains 200,000.

Chromium 153.0.8010.12, DPR 1, 180 draws after 15 warmups:

| Tokens | Mean | p95 | Result |
| ---: | ---: | ---: | --- |
| 300 | 5.6739 ms | 7.3 ms | FAIL: mean must be below 4 ms |
| 600 | 15.585 ms | 19.3 ms | Recorded; no separate gate |

Browser errors: none. Validator failed with
`('spearman', 'death', 5, 'stone pigment/position changed', 41.4)`.

## What changed and why

1. **Stone occlusion, not a moving base.** The sheets show the fallen leg crossing
   the rim, and the base mesh has neither animation nor modifiers. Instead of
   weakening a color threshold, render only foreground into `foreground/` and
   composite the immutable `base.png` in the packer. Store the actual selected
   foreground alpha as a separate mask, bound to base and atlas by SHA-256.
   Validation excludes only rendered occlusion plus one edge pixel, requires a
   useful exposed rim, and still fails missing/moved/recolored stone. It cannot
   silently call a color mismatch an occluding figure. Pass archives preserve
   these masks and reference base. Old pass-2 frames cannot supply this evidence.
2. **Mask ownership.** Narrow contact polygons remove excess cream around feet.
   Anatomical torso regions and deterministic nearest-part assignment transfer
   stray limb/kit pixels out of the body layer. Replace global six-pixel paint
   dilation (which left duplicate detached strips behind) with small three-pixel
   joint overlaps. Revisit crew/sleeve, ramrod/hand, and rider/boot ownership.
   This is not full hidden-surface inpainting; unseen cloth, saddle and limb backs
   remain a limitation, not a solved problem.
3. **Infantry.** Add spear-arm pivots; distribute attack between upper arm and
   carried spear. Keep shields rigid relative to the torso, rather than expose
   unpainted areas by independently rotating them. Fold the falling left leg
   inward to avoid the extended-foot pose and keep the revised masks in frame.
   Expected: cleaner kit/foot edges and more connected arm movement for both
   spearman and hoplite. A real body turn/contact still needs pass-3 judgment.
4. **Horseman.** Add two foreleg knee joints. Sequence knee buckle, torso lowering,
   head lowering and independent rider pitch, with a separate far boot attached
   to the rider. The horse root only inclines 8 degrees, with no whole-body scale
   squash or 69-degree flip. Torso drops 43 px; rider spills separately; the last
   two poses settle identically. Expected: a low collapsed horse with a separate
   fallen rider, not an airborne inverted card. CPU bounds put final torso down
   to y=222.52 on the stone; this is geometry evidence, not visual approval of a
   horse lying convincingly on its side. Watch saddle reveal and knee seams.
5. **Cannon.** Stop rotating incomplete painted wheels; remove the axle
   decompression rig. Wheels, carriage and barrel move rigidly together. Recoil
   moves the whole gun 3 px, so it does not uncover an unpainted breech. Neutral
   gun stays stationary while crew breathes/reacts. Expected: intact wheels,
   fewer floating crew fragments, coherent recoil. This sacrifices convincing
   rolling wheels; it is an honest limit until full wheel surfaces exist.
6. **Gallery hot path.** Pre-scale cells once to 64/80 px, pre-mirror each atlas,
   and use one integer-positioned 1:1 blit per token. Reuse original pixels for
   native 256 inspection. Terrain was already cached; there were no token
   shadows/filters. Skip unchanged inspection canvases. Pause other gallery
   draws during benchmarks. Capture both original and cached paths with separate
   terrain/sprite times; README documents game reuse, DPR/zoom and memory costs.
   Expected speedup is unmeasured until the lead runs capture. No runtime game
   files or atlas JSON contract changed; no `app/node_modules` dependency added.

## Limits and next comparison

The cut-out risk is inherent to this single-facing relief approach. A subdivided
projected painting is still missing actual side/back surfaces. Small breathing,
recoil and restrained arm motions can work, but substantial turns and falls
cannot be made convincingly solid by tuning planar transforms alone. I do not
believe the solid-figure bar for every clip can be met within this approach.
Proceed with the planned **true-3D spearman comparison after pass 3**. Do not label
the current relief study production-ready or approve it on byte/perf checks.

## Checks and handoff

- `venv/bin/python tools/art/anim/test_pipeline.py`: **7 tests passed** (30.487 s),
  including all four synthetic atlas contracts, independent occlusion vs missing,
  shifted/recolored stone, insufficient visibility, source coverage/ownership,
  timing/hold and byte-budget preservation.
- `node tools/art/anim/test_sprites.cjs`: **PASS**, three sizes, both facings,
  populated cells, mirror anchors, native reuse and a single 1:1 draw hot path.
- CPU-only model builds/audits: **all four passed, 160 poses** after fixing bounds
  found during iteration. No Eevee image render or Chromium launch performed.
- Final syntax/static and strengthened horse audit results are recorded below.
- Full Rust/app builds are not applicable: no engine or app runtime changes.

Lead: run **`tools/art/anim/pass.sh 3`** from this worktree with the existing
external Playwright `NODE_PATH` and browser cache environment. All four units
must rerender: packer input changed from old composite `frames/` to figure-only
`foreground/`. Do not repack the old frames or use `--contract-only` as the gate.
Keep the original pass-2 images/metrics as evidence. Inspect new `*-pack.json`
profiles, all clips, foreground/base validation and both timing paths. The
current delivered atlases are untouched; final sizes and visual results await
this render. No push or merge is authorized or attempted.

### Final verification and commit status

Final CPU-only builds/audits passed for **all four / 160 poses**, including the
horse no-flip, bent foreleg, separate rider and low torso checks. Final Python
compilation, JavaScript syntax (gallery, sprite helper and capture), shell syntax,
and `git diff --check` passed. Blender emitted nonfatal thumbnail-write and
`nice` permission warnings; models saved, audit exits were zero.

`tools/gates/check.py HEAD --base origin/master --checks-only --skip art` exited
1: `public-claims` passed, hygiene mistook an unspaced matrix multiplication
quoted in the **historical pass-1 note** for an email. Spaced that quotation in
the working file. The gate reads committed objects, so the runner must rerun it
after committing; this is not a full gate pass. Direct hygiene line checks on
all 19 animation/skill text files passed with 0 findings after the correction.
No browser art gate ran.

`origin/master` is already an ancestor of HEAD (**6 ahead / 0 behind**); no fetch
or merge was needed. `git add tools/art/anim .claude/skills/legatum-art/SKILL.md`
failed with exit 128 because the sandbox denied creating the worktree index lock.
Changes are therefore **uncommitted for the runner**, with no permission or index
workaround. Stage only those paths; the delivered atlases were not modified.

Suggested commit:

```text
Repair animation masks and collapse, cache gallery sprites after pass 2

Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>
```
