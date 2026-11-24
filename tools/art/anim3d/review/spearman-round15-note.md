FOCUS a: (Sam/reviewer) RIGID PARTS: make shield, spear, helmet and greave plates rigid (Child Of / single-bone parenting or 100% weight to one bone: shield to the left forearm via a shield-grip bone, spear to the right hand); bake their painting projection to UVs so nothing swims; add the rigid-part check to critique.py (per-frame edge lengths and volume vs rest, >0.5% fails) and run it on every clip. Do not touch the rest pose or the look.
FOCUS b: (Sam/reviewer) ATTACK: rebuild the overhand doru thrust against real reference (hoplite reenactment / stage-combat, or a CC0 thrust mocap clip; note source and licence), 16-20 frames, with anticipation, ease and follow-through; the shield stays up and forward covering the body and turns/moves with the torso and left arm through the lunge; the spear rotates from upright to level over several frames, never a 1-2 frame snap. Judge it from a 160 px looping MP4 at game fps.
FOCUS c: (Sam/reviewer) SMOOTHNESS AND REVIEW TOOLING: raise frame counts (hit 8, move 12-16, idle 12, death 14-16) with rigid shield in hit and death; re-budget the atlas to <= ~350 KB; add a pop check (max per-frame screen displacement of any part at 160 px under a limit except the strike frame); make gpu.sh write a 160 px MP4 per clip looping 3x at game fps (spearman-roundN-<clip>-160.mp4) and a full-frame-rate attack strip (spearman-roundN-attack-fullrate.png).

# Spearman round 15 — combined candidate, GPU rendered / visual review pending

Not a PASS. The GPU pass, pixel-parity gate and decoded atlas validation completed; final visual approval is pending. The CPU evidence below remains labelled separately from the appended GPU receipt.
No PASS issued. The cloud reviewer calls round 14 the first full candidate for
Sam and asks for a hold after this round; no further automatic art changes are
requested here. GPU handoff remains ready for the lead.

## Selection and provenance

Baseline: `9c35ac22` (round 14 GPU). Read FEEDBACK.md and spearman-FEEDBACK.md,
including the art director's 09:59Z lane verdict and 10:13Z final merge review. Compared the supplied
Fable A/B notes, native-size rest comparisons and five-clip contact sheets.

- Skill branch `53773742`: imported updated SKILL, LOG, kit README and unit
  status. Its code matches the evolved kit already on this branch. Critique
  branch `afa9a90f` is the older standalone implementation, already superseded
  by the shared `kit/critique.py` and stable CLI: no downgrade imported.
- Astra a `ba1dc841`: took recovered source pigment across the combined
  skin/leather footprint. Its matched CPU feet ΔE improves 5.45 → 4.72 and
  global 3.39 → 3.30, with silhouette 0.9513 unchanged. The preliminary lane review saw no clear gain; the final 10:13Z review of
  this merge now sees strap bands and separate right toes. Some contrast polish
  remains (reviewer requests straps 15% darker, skin unchanged). Dropped its cloak trial: idle cloth
  correction rose 71 → 99 mm without a convincing visible silhouette gain.
- Astra b `798cca9d`: took move-only tilt shading of the lifted instep/straps
  and compact moving shadow pools following evaluated sole centers. The
  reviewer accepts the removed pale dot; lane masked luminance 80.2 → 51.0
  and 74.5 → 52.1. Preserved donor foot rotations and all choreography.
  **Did not default to its rest pools:** the 09:59Z art director prefers them,
  but the explicit no-regression instruction from the cloud reviewer conflicts
  with that choice: matched CPU feet ΔE 5.45 → 10.94, global 3.33 → 3.98.
  The GPU script renders the alternative alongside the selected look so this
  remains reviewable. Existing rest shadow remains a visible open defect.
- Astra c `c1c016fc`: retained R14's walk and death and added its eight-frame,
  integer/uniform-cadence assertions. Dropped its phase trial: entry 14.41 →
  13.37 px but exit 9.44 → 10.34 px and cloth step 11.89 → 12.53 px at 160.
  The early-fall spear timing and shield-readable face-down ending stay.
- Fable A `ee83409f` and B `28da82cb`: their winning painted emission look,
  registration, part paint, fitted form and authored collapse are already
  incorporated and refined by R14. Their earlier combined rest scored about
  0.938 IoU / 4.56 blurred ΔE, versus R14 GPU 0.9537 / 3.51. Definitions and
  rendering settings changed across those historical reports; this is not a
  new matched A/B. The art director's 09:32Z verdict names R14 best on every
  aspect, with no Fable build ahead. No old whole-branch state was reapplied.

Git merge metadata is blocked by `ORIG_HEAD.lock` in this sandbox. Changes are
ported by scoped paths, with a lane-only patch and co-authored commit message
for the runner. No push, PR or master merge. origin/master is already an
ancestor of this branch at this session's fetched state.

## Reusable kit and rebuild

Added `kit/foot_finish.py`: paired frozen pigment masks, tilt-driven node values
and evaluated-sole marker updates. Spearman supplies only mappings, tint and
clip policy. Both the CLI and delivered frame use the same post-frame update.
Added the shared module and sandal pigment source to look receipts. The existing
MPFB/Rigify/corrective helpers, painterly graph, projection/seam fill, camera/light
presets, Quaternius/KayKit retarget and foot locking, critique remain reused.
Rigify/correctives are optional mechanisms; this unit keeps its verified MPFB
rig. A CMU skeleton map is not implemented or claimed.

Rebuilt in `lanes/spearman-r15-merge` from the preserved projection input,
recalibrated part paint, and rebuilt every clip. CPU uses Cycles analytic painted
proxy at 256 px / 8 samples / seed 17, without Eevee cast shadows. Production
512/256 masters and shipped atlas remain R14 until the host GPU pass.

## Ranked visible gaps (merged CPU preview and final 10:13Z review)

1. **256 px: spear-side rest cloak** (x 98–112, y 120–175): still narrower at
   hip height than the painting; reviewer requests 4 px flare and lit folds
   8–12% darker (their proxy p90 185 vs painting 158). This is now the leading
   rest-pose gap. Do not reintroduce the rejected idle-cloth correction.
2. **256 px: cloak hem** behind the right leg (x 140–165, y 175–195): the
   diagonal edge should level near y 190 with three shallow scallops.
3. **Motion:** one of the three held death frames could go to the quick
   kneel-to-prone step. Guard/walk retains measured 14.41/9.44 px sole boundary
   displacement, although all five clips read naturally at 160 to the director.
   Rephasing alone cannot match a wide guard at both ends. Retain the readable
   shield/crest ending and early-fall spear timing.
4. **256 px small surface tells:** pale sliver beneath the spear hand around
   (106,123), bronze cavities a little shallow (earlier reviewer helmet p10
   33 vs 26, cuirass 38 vs 31), left greave about 2 px off its painted lean.
5. **Feet and base polish, now accepted at game size:** the 10:13Z director
   can see the recovered strap bands and separate right toes (x 152–166,
   y 208–220). Feet are a little light by their measure (150 vs 141); darken
   only straps 15%, leaving skin. They accept the weaker shadow band at 160
   and 64 and clarify the pool preference was for the **base**, not changed
   feet. If revisited after GPU review, preserve feet exactly and fade only
   the inter-foot band (x 115–145, y 214–219). The stone side remains smoother
   than the painted grain at 256.

At 64 px the shield, crest, spear and stance preserve the painting's identity;
no claim of a material 64 px improvement. At 256 there are visible contour and
surface differences. At 160 the director considers none of the remaining items
noticeable in game. Their final ranking makes R15 the best CPU candidate on every
aspect; **R14 GPU remains the best verified final build until R15 GPU exists**.

## Lead handoff

Run from the repo root: `ROUND=15 tools/art/anim3d/units/spearman/gpu.sh`.
The executable no-argument script rebuilds, checks, renders all stages and five
clips; writes native 512/256 masters; packs/validates 160 px trimmed Q≥75 WebP
≤200,000 bytes; produces the eight-second 1600×352 H.264 yuv420p five-clip movie,
painting/render/crossfade comparison, dense top/front feet sheet, decoded 160
contact sheet, shared critique metrics, and appends numbers above these FOCUS
lines. The optional rest-pool A/B remains a review alternative, not delivery.

## Fresh combined verification — 2026-11-24

- **36/36 tests pass:** kit 27, look 3, pipeline 2, critique 4. All 120 Python
  files parse; zero unresolved local imports; gpu.sh syntax/executable checks
  and git diff whitespace checks pass.
- Fresh project/calibration and all five clips rebuilt. Scene check, evaluated
  support regression and transition checks pass; **40-pose audit: zero findings**.
  Frozen idle/attack hashes match. Independently compared R14/R15 CPU receipts:
  **all actions match and all 41 alpha images are pixel-identical**, including
  rest. No silhouette or choreography regression is hidden by the merge.
- **33 dense foot samples pass every limit:** compensated slip 0.004234 mm,
  floor error 0.000106 mm, planted heading 5.1424°, readable heading 9.1751°,
  loop seam 0 mm. Top/front sheet visually inspected. This sheet uses geometry
  diagnostic materials; inspect the final-look move strip for pigment.
- Shared critique: **IoU 0.9512536 unchanged; blurred ΔE 3.3865986 → 3.2979887;
  feet 5.4466455 → 4.7170817**. Both targets pass. Raw ΔE is 7.1487 (diagnostic,
  not the colour gate). All regions remain below 6. The tiny legs-box increase
  of 0.0016 is disclosed below: source recovery changes the blurred foot/leg
  boundary. There is no visible leg change; this is not an assertion that
  every floating-point metric improved.

| Region | R14 CPU ΔE | R15 CPU ΔE |
| --- | ---: | ---: |
| head_crest | 3.7378 | 3.7378 |
| torso | 2.6347 | 2.6347 |
| cloak_spear_side | 5.0336 | 5.0336 |
| shield | 2.2224 | 2.2224 |
| legs | 2.7262 | 2.7278 |
| feet | 5.4466 | 4.7171 |
| base | 3.2322 | 3.2160 |

- Decoded preview atlas validates: **40 frames, 160 px trimmed, 192,774 bytes,
  Q80** (7,226 bytes below the decimal 200 KB limit). It lives in the isolated
  lane atlas directory. The shipped atlas remains the R14 GPU artifact until
  the host produces final masters.
- Movie independently probed: H.264, yuv420p, 1600×352, 192 frames, exactly
  8.000 seconds. Native 256/160/64 comparisons, decoded contact sheet and all
  clip poses inspected. Dark lifted-foot dot suppressed, no altered silhouette;
  rest sandal bands still softer than the painting. Shield/crest readable at
  64 px through the retained ending. Rest stone side is smoother/less mottled
  than the painted disc, especially at 256; at 160 the residual shadow stripe
  is more noticeable than stone grain.
- Fresh same-master foot-finish A/B with the recovered pigment confirms the
  extracted kit leaves geometry, UVs, weights, rig poses and actions untouched.
  Masked move foot luminance **91.87 → 59.12** and **79.15 → 55.22**; these are
  the combined candidate's values, not the lane-b values quoted earlier.
  Marker error to evaluated sole centers is exactly zero. Compact **rest**
  pools remain worse numerically: global **3.298 → 3.957**, feet **4.717 →
  10.279**, versus the visually cleaner pools. Their rejection still stands.
- Setup correction: the first isolated project launch lacked spearman.blend;
  copied the baseline master beside its preserved projection input and rebuilt
  successfully. A later control-metric lookup used a nonexistent R14 JSON;
  rescored the preserved R14 image with the same critique instead. Neither
  failure was a render/contact defect or a relaxed gate.

Canonical round-15 movie/images/metrics currently show the **CPU proxy**. Copies
with `spearman-round15-cpu-*` preserve this evidence when the GPU driver replaces
the canonical filenames. CPU sources, all 40 frames, atlas, receipts and logs:
`~/LegatumRuns/anim-pilot/lanes/spearman-r15-merge/`. No GPU run or art PASS is
claimed in this sandbox. No new third-party asset or licence was introduced.

## Cost record

`.progress/astra.log`: lane a 20m38s, b 24m51s, c 8m40s; parallel lane wall
24m53s. Merge began 04:59:33 America/New_York; verified through 2026-11-24T05:13:55.461126-05:00
(14.37 minutes). Runner finish and GPU time are still pending; tokens are
not measured. Exact parsed timestamps: `lanes/spearman-r15-merge/timing.json`.

## Git handoff

Final staging also failed on the sandbox's `index.lock`. Source changes remain
uncommitted on `astra/unit-anim-3d-v2`. Runner artifacts:
`lanes/spearman-r15-merge/round15-only.patch`, `changed-files.json`, and
`commit-message.txt` (required gpt-6-astra co-author included). The patch covers
only this round's source changes against `9c35ac22`; no masters are in git.

## Final art-director feedback received during handoff — 10:13Z

The director reviewed this merge's CPU comparison, contact sheet and note:
strap bands and separate right toes now read at 256; the weaker band is acceptable
at 160/64; all five clips read naturally at 160. R15 merge is ranked best for
silhouette, materials/values, move, hit and death; idle/attack remain frozen.
No Fable lane is ahead. Recommendation: if GPU matches this proxy, show Sam R15
as the PASS candidate. No GPU frames have been reviewed and no PASS is issued.

Their independent proxy IoU is 0.949 (also unchanged for R14); shared critique
remains 0.9512536 at zero/best offset. These measurements are not interchangeable;
use the shared tool for the numeric gate. The ranked gaps above were rewritten
for this latest verdict; the earlier lane comments remain historical evidence.

### Automated critique: spearman-round15 (Eevee painted GPU 512 masters / display-space decoded 160 atlas)

- Silhouette IoU: **0.9537** (target ≥ 0.95; PASS). Best of ±3 px offsets: render x=+0, y=+0.
- Tone/colour ΔE on blurred images (sigma 2 px, CIE76): **3.42** (target ≤ 6; PASS), at zero offset over 11570 overlapping pixels including base. Information only: raw per-pixel ΔE 6.19; at the IoU offset blurred 3.42, raw 6.19.
- Regions (blurred ΔE): head_crest 3.7, torso 2.9, cloak_spear_side 4.8, shield 2.4, legs 3.2, feet 4.6, base 3.2.
- Painting mask: alpha; frames: idle 8, move 8, attack 10, hit 4, death 10.
- Rest: `/Users/samcorcos/LegatumRuns/anim-pilot/masters/spearman/256/rest.png`. Contact sheet uses `/Users/samcorcos/LegatumRuns/anim-pilot/review/3d-v2/spearman-decoded-160`.

### Delivery receipt (GPU final render, visual review pending)

- 40 frames; 160 px trimmed atlas: 187440 bytes, quality 80; decoded validation PASS.
- Walk: planted slip 0.0042 mm; floor error 0.000 mm; heading 5.142°.
- Movie: five clips, 1600×352, H.264 yuv420p, 192 frames / 8 seconds. No art PASS issued.

FOCUS a: After Sam's review, refine cloak flare and scalloped hem without worsening motion; the final director now sees recovered straps/toes.
FOCUS b: Inspect GPU first; if revisiting shadow, preserve feet and fade only the inter-foot band; optional straps 15% darker, hand sliver and cavity depth.
FOCUS c: Hold R14 donor walk/readable death; only revisit dedicated guard transitions and fall frame allocation after Sam has seen the candidate.
