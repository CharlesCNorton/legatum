# Spearman round 15 — combined candidate, CPU review / GPU pending

Delivery status: CPU verification in progress; GPU pass and final visual review pending.
No PASS issued. The cloud reviewer calls round 14 the first full candidate for
Sam and asks for a hold after this round; no further automatic art changes are
requested here. GPU handoff remains ready for the lead.

## Selection and provenance

Baseline: `9c35ac22` (round 14 GPU). Read FEEDBACK.md and spearman-FEEDBACK.md,
including the art director's final 09:59Z round-15 verdict. Compared the supplied
Fable A/B notes, native-size rest comparisons and five-clip contact sheets.

- Skill branch `53773742`: imported updated SKILL, LOG, kit README and unit
  status. Its code matches the evolved kit already on this branch. Critique
  branch `afa9a90f` is the older standalone implementation, already superseded
  by the shared `kit/critique.py` and stable CLI: no downgrade imported.
- Astra a `ba1dc841`: took recovered source pigment across the combined
  skin/leather footprint. Its matched CPU feet ΔE improves 5.45 → 4.72 and
  global 3.39 → 3.30, with silhouette 0.9513 unchanged. The art director sees
  no clear gain at native size: this is a modest pigment recovery, **not** a
  claim that the straps/toes are fixed. Dropped its cloak trial: idle cloth
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

## Ranked visible gaps (to be checked against the merged preview)

1. **256 px: sandal contrast/toes** (x 88–115 and 144–169, y 204–222).
   Source recovery improves metric/detail slightly; the painting's three dark
   strap bands against warm lighter skin and separate toes remain clearer.
   At 160 this is small; at 64 it is not a useful improvement claim.
2. **256 px: rest shadow band** (x 105–172, y 214–219). It is still too broad
   and hard compared with the painting's soft local foot shadows. Move uses
   tracking pools; rest awaits the documented visual/metric decision.
3. **256 px: rest cloak** (x 98–112, y 120–175): narrower at hip height than
   the painting; reviewer requests roughly 4 px flare. Behind the right leg
   (x 140–165, y 175–195), the hem remains a diagonal instead of shallow
   scallops. The cloth change was rejected for motion regression.
4. **160 px motion:** the guard/walk hard cut retains measurable 14.41/9.44 px
   sole displacement, even though R14's phase is visibly better than R13.
   Rephasing alone cannot match a wide guard at both ends. Death retains a
   quick kneel-to-prone step and three repeated held frames; do not trade the
   readable shield/crest ending for containment alone.
5. **256 px small tells:** pale sliver beneath spear hand around (106,123),
   bronze cavities slightly shallow (reviewer: helmet p10 33 vs 26, cuirass
   38 vs 31). These were not addressed by a passing lane and remain open.

At 64 px the shield, crest, spear and stance preserve the painting's identity;
no claim that this round materially improves the 64 px token. At 256 the render
remains a close but visibly simpler painted miniature. Final GPU judgment pending.

## Lead handoff

Run from the repo root: `ROUND=15 tools/art/anim3d/units/spearman/gpu.sh`.
The executable no-argument script rebuilds, checks, renders all stages and five
clips; writes native 512/256 masters; packs/validates 160 px trimmed Q≥75 WebP
≤200,000 bytes; produces the eight-second 1600×352 H.264 yuv420p five-clip movie,
painting/render/crossfade comparison, dense top/front feet sheet, decoded 160
contact sheet, shared critique metrics, and appends numbers above these FOCUS
lines. The optional rest-pool A/B remains a review alternative, not delivery.

FOCUS a: After Sam's review, strengthen strap/skin contrast and toes; cloak flare/scalloped hem only if motion and silhouette do not regress.
FOCUS b: Resolve soft rest pools versus regional error on matched GPU evidence; retain the accepted dark moving-foot pigment and test the hand sliver/cavity depth.
FOCUS c: Hold R14 donor walk/readable death; only revisit dedicated guard transitions and fall frame allocation after Sam has seen the candidate.
