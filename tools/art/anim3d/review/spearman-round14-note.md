# Spearman round 14 — combined candidate, CPU review / GPU pending

Delivery status: CPU verified; GPU pass and final visual review pending.

## Selected changes and evidence

- **Skill/critique:** attempted the requested git merge; sandbox denied ORIG_HEAD.lock. Ported the skill lane's current SKILL, LOG, kit README, fitted base defaults and status notes. Integrated c's support query without overwriting those defaults. The critique branch contains the older standalone raw/offset colour implementation; its useful work is already superseded by the shared kit critique (zero-offset blurred colour, preset regions, FOCUS-preserving report). Kept that newer implementation rather than reverting it. No fetch, push, master merge or PR.
- **Fable A (paint) + B (form): retain their already integrated foundation.** Inspected both notes and their rendered comparisons. A alone: IoU 0.9091, zero-offset blurred delta-E 4.94; B with A's look: about 0.938 / 4.56, per their notes. Those older masters have visibly poorer feet/base registration than the current Fable C / R13 master. Keep A's emission-painted Eevee graph, part textures and ramps; B's measured form, shaft, cloak and keyed collapse; C's registered feet/guard/disc. R13 GPU remains the production baseline: 0.953676 IoU / 3.512809 blurred delta-E. Different CPU/GPU engines are not a before/after improvement claim.
- **Astra a: dropped side-lying Fable D death.** Its held crest/feet margins improve to +3.34/+5.00 px inside the base. However the inspected 256 sheet shows striped skirt undersides and a shield hidden behind the body; the 08:22/08:33Z director ranks it below the shield-readable R13/c ending. No new a choreography or guard rebase was applied. Its early level spear is already present in the retained candidate by sample 3.
- **Astra b: merged restrained move/attack cloth.** Full shoulder pins, lower-pin factors 1.8/.85, bending 2/1.2 and air damping 6/5. Lane's matched geometric edge sweep: move 22.10 → 15.48 px, attack 10.37 → 7.96 px at 256; endpoint p95 182 → 133 mm and 154 → 114 mm. These are full-mesh geometric measures, not visible-edge measurements. Rest master is unchanged: the director's description of a wider rest cloak is not supported by the source or identical rest comparison. No rest-silhouette win is claimed.
- **Astra c: merged periodic cloth correction, balanced walk sample rotation, evaluated stone support, stronger transition checks, and early GPU parity.** Director 08:33Z says take the entry and retain this death. Lane measurements: idle/move cloth duplicate-endpoint gaps 2.624/12.074 px → <0.00004 px at 160; idle→move full-sole jump 23.00 → 14.41 px and move→idle 18.66 → 9.44 px. Rig rotations and all eight walk samples are preserved. The bone motion of accepted idle/attack remains; idle's fingerprint includes the reviewed cloth-correction action, attack retains its original fingerprint. Hit and death choreography remain R13. Fable D's alternate walk is not imported: the latest director prefers c and D's yaw clamp would modify donor foot rotation.

## Reusable kit and pipeline

New reusable cloth configuration and periodic residual correction live in kit/cloth.py and kit/loop.py. Evaluated stone SupportSurface is shared by the animator, donor floor fitting and audit. Spearman cloak.py supplies only its settings. The already integrated kit supplies MPFB with optional Rigify and authored hinge correctives, painterly graph, frozen projection/seam fill, painting camera/lighting presets, Quaternius/KayKit retarget maps and foot locks, and critique. No CMU/Rigify retarget mapping or production corrective sculpt is falsely claimed. Heavy assets stay outside git.

CPU review now uses the same look.configure_render/render_frame as the GPU handoff, records master/code/calibration hashes and refuses stale packaging. gpu.sh retains all five clips, 512/256 masters, q>=75 / <=200000-byte trimmed 160 atlas, decoded validation, feet sheet, contact sheet, crossfade and eight-second five-clip movie. Parity runs before cloth bakes, with the existing measured GPU noise tolerance.

## Ranked visible gaps to judge on the merged output

1. **Feet detail / sole flash (256: x 90–113 and 152–166, y 205–220).** Rest sandals still read as smooth brown forms rather than the painting's dark straps and separated toes. The rephased walk shows the pale trailing sole at entry. More noticeable in motion at 160 than the rest mismatch; anatomy and headings remain measured separately.
2. **Stone shadow (x 105–172, y 214–219).** R13 GPU review flags a hard tan band that stays put during the walk. CPU analytical lighting cannot certify its Eevee shadow behavior; do not mark this closed. Needs weaker/softer per-foot shadow that follows animated feet.
3. **Guard-to-walk hard cut.** The director sees a much better entry; full sole geometry still differs by about 14 px at 160. Reordering samples reduces a cut, not a new transition performance. Cloth closure must be checked through the whole combined b+c cycle, not just its endpoints.
4. **Cloak at rest (x 98–112, y 120–175; hem x 140–165, y 175–195).** Still short of the painting's flare and level scalloped hem. b changes motion response only. The R13 GPU director measured lit folds p90 163 vs 150 and roughly 50 px missing area; those are historical GPU measurements, not new CPU results.
5. **Death staging and small painted details.** Retained shield-readable ending shows less body than a; the diagonal spear is still visible during the initial fall before lying flat by sample 3. Pale sliver under the spear hand near (106,123), simpler deepest bronze cavities and slight left-greave lean remain 256 px polish. At 64 px the crest, spear and sun shield carry the unit identity.

## Verification

- Fresh projection and CPU look calibration, all five clip/cloth builds, 19,158-vertex MPFB / 53-bone scene check, evaluated support regression: passed.
- 40-pose audit: **zero findings**. All eight contact limits pass over 33 dense top/front samples: slip **0.004234 mm**, floor **0.000106 mm**, planted/readable headings **5.142/9.175 degrees**, foot loop **0**. Root correction 48.963 mm and sole correction 39.954 mm remain near their 50/40 mm caps, not relaxed.
- Frozen idle and attack fingerprints reproduced exactly. Attack full-sole entry/exit error **0.0000341 px** at 160. Move entry/exit residual **14.4112 / 9.4421 px**. Combined cloth endpoint gaps: idle **0.0000305 px**, move **0.0000153 px** at 160.
- Combined b+c maximum free-cloth correction is **273 mm**, versus c's reported 230 mm; idle remains 71 mm. This is a regression in correction magnitude, not hidden as a universal improvement. Inspected all intermediate 160 px poses against c: less flag-like motion and no obvious new silhouette artifact; retain pending GPU playback review. The correction is authored geometry after simulation, not a physically converged cloth bake.
- Rest RGBA pixels equal the archived R13 CPU proxy **exactly** (mean/max channel difference 0). Rest IoU **0.951254**, zero-offset blurred delta-E **3.386599**, raw **7.274262**. No rest gain or GPU-to-CPU comparison claim. All regional blurred values under 6 (feet 5.447; cloak 5.034).
- CPU atlas: **192,682 bytes, Q80, 160 px cells, 40 records**, decoded alpha/trim/offset/gutter/motion/held-death validation passed. Movie verified H.264/yuv420p, **1600x352, 24 fps, 192 frames, 8.000 s**. Preview atlas lives in `lanes/spearman-r14-merge/atlas`; app assets remain the R13 GPU delivery.
- Python tests **36/36** (kit 27, critique 4, pipeline 2, look 3). Import check: zero unresolved imports; 113 Python files parse; gpu.sh shell syntax and executable bit pass. No Rust/UI source changes or unrelated engine builds.
- Personally inspected 256 rest triptych, 256/160/64 sizes, 160 contact sheet, b+c versus c move/attack strips and all 33 top/front foot samples. At 256 it is close but sandals, hem, small sliver and the low-sample CPU surface noise still distinguish it. At 160/64 it reads as the same painted unit; moving sole and boundary-cut polish remain. No PASS marker: merged GPU output still needs visual review.

GPU lead command from repo root: `ROUND=14 tools/art/anim3d/units/spearman/gpu.sh`. It regenerates every stage and replaces the clearly labelled CPU round-14 review outputs with final GPU evidence. The GPU parity gate and 512/256 delivery are prepared, not claimed as executed inside this sandbox.

### Automated critique: spearman-round14 (Merged R14 Cycles CPU proxy, freshly rebuilt/calibrated, 256 px 8 samples; decoded 160 atlas; GPU pending)

- Silhouette IoU: **0.9513** (target ≥ 0.95; PASS). Best of ±3 px offsets: render x=+0, y=+0.
- Tone/colour ΔE on blurred images (sigma 2 px, CIE76): **3.39** (target ≤ 6; PASS), at zero offset over 11572 overlapping pixels including base. Information only: raw per-pixel ΔE 7.27; at the IoU offset blurred 3.39, raw 7.27.
- Regions (blurred ΔE): head_crest 3.7, torso 2.6, cloak_spear_side 5.0, shield 2.2, legs 2.7, feet 5.4, base 3.2.
- Painting mask: alpha; frames: idle 8, move 8, attack 10, hit 4, death 10.
- Rest: `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r14-merge/preview/rest/00.png`. Contact sheet uses `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r14-merge/review/3d-v2/spearman-decoded-160`.

FOCUS a: Sandal straps/toe separation and the cloak's rest flare/scalloped hem, measured against the painting; preserve registered feet and base.
FOCUS b: Remove the moving pale-sole flash; soften the base shadow and anchor it to evaluated animated feet, with same-path GPU A/B evidence.
FOCUS c: Reduce guard/walk boundary jumps without changing donor foot rotation, contact or frame count; review combined cloth through the loop and preserve shield-readable death.
