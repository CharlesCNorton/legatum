# Spearman round 14 — combined candidate, CPU review / GPU pending

Delivery status: build in progress; no round-14 GPU result is claimed.

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

Combined build and CPU image measurements will be appended after completion. No PASS marker: the merged GPU movie still needs the lead's visual review.

FOCUS a: Sandal straps/toe separation and the cloak's rest flare/scalloped hem, measured against the painting; preserve registered feet and base.
FOCUS b: Remove the moving pale-sole flash; soften the base shadow and anchor it to evaluated animated feet, with same-path GPU A/B evidence.
FOCUS c: Reduce guard/walk boundary jumps without changing donor foot rotation, contact or frame count; review combined cloth through the loop and preserve shield-readable death.
