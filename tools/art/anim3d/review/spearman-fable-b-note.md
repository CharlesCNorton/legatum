# Spearman fable-b: form and motion

Branch `fable/unit-anim-3d-spearman-b` (worktree `~/LegatumRuns/anim-pilot/fable-b`), cut from the round-9 candidate.
Masters: `~/LegatumRuns/anim-pilot/fable-b-masters` (copy of the round-9 merge masters; lane root `fable-b-root`).
All evidence is Cycles CPU, 256 px, 16 samples, the round-9 grade. Materials and lighting are untouched (Fable A owns the look).
Not a PASS claim: these are form and motion candidates for the merge.

## What changed

1. **Legs, feet, cloak, shaft (rest form).** `units/spearman/stance.py`, called in `project.py` after the 9a silhouette pass and before the UV freeze.
   - Rest-geometry radial scale about each leg bone's rest axis, weighted by the vertex's own skin weight: thigh 1.16, knee/greave 1.46 easing to 1.26 at the ankle, feet 1.50 x 1.38 x 1.22 about the point under the ankle on the sole plane. No bone, weight or pose change, so every clip inherits it.
   - The calf grows toward the midline, front and back only. The inner contours already registered with the painting; a symmetric scale left pale unpainted lobes outside both greaves (ray-cast confirmed they were greave surface beyond the painted leg).
   - Spear-side cloak edge flared 6 px at hip height and the centre hem lowered 4 px (screen-space fit through inverse skin transforms, the 9a method).
   - Spear-side ankle 5 cm nearer the midline (the art director measured the painted shin as nearly vertical).
   - Shaft, ferrules and butt radius x1.75. Greave spiral ornaments hidden by visibility: they floated beside the fuller greave as rings.
   - Rest silhouette IoU against the painting, same threshold: **0.894 (round 9) to 0.918**.
2. **Death.** `units/spearman/collapse.py`: a keyed collapse replaces the retargeted Death01. Recoil, knees give with the feet planted, drop to the knees with the toes dragged back, topple onto the spear side, settle lying across the stone behind the shield. The aspis stays parented to the forearm for the whole clip; the spear is released and lands on the ground in front of the base. Why keyed: Death01 flips onto its back along the camera's depth axis with both arms up and ends off the base (top/side quick-looks confirmed it), and blending it (round 10c) kept the squat-then-pop.
3. **Hit.** Same module, `HIT_KEYS`: chest and head snap back over planted feet, the shield is driven up into the body, the spear rocks, then a low catch and back to the exact guard. Entry and exit equal idle.
4. **Walk.** Still the CC0 Quaternius Walk_Loop retarget with the heel/toe contact locks. Added on top, all phase-locked to the clip's own measured stance intervals:
   - pelvis dip at double support (2.2 cm), sway over the stance foot (2 cm), shoulder counter-rotation (about 5 degrees) with the head counter-turned, a small forward lean, spear sway;
   - step width: a constant 8.5 cm lateral ankle offset per foot, so the feet no longer land on one line;
   - both ankles re-solved by IK to the retarget's world positions after the shift, so contact is unchanged;
   - sole height per foot: the root follows the planted foot that needs the lowest pelvis; a second support or a dipping swing toe is raised by leg IK (no rigid ankle translation).

## What failed or was dropped

- Symmetric leg scale: pale lobes outside the greaves (see above). Fixed with the inward-only field.
- Scaling the skin calf as far as the greave made no visible difference; the lobes were the greave itself.
- First collapse rest pose (rolled 38 degrees onto the back): the shield stood on him like a hat and the body was lifted 23 cm by the lower elbow. A side-lying rest with the pelvis-to-shoulder line tilted about 9 degrees puts hip and shoulder on the stone together.
- Foot pitch relative to the shin drove the toes into the stone when the shin tilted (body lifted up to 32 cm by the floor solver). Foot pitch is now absolute from the flat neutral sole.
- Walk_Formal_Loop: nearly the same legs as Walk_Loop; not adopted.
- The old disc-footprint sole pass pulled an overhanging planted toe 6 mm below the stone top once the steps were wider; planted soles now skip it.

## Tools

- `units/spearman/quicklook.py` + `quicksheet.py`: render chosen frames of a diagnostic (no cloth) or baked clip from the painting camera plus top/front/side, tile to one sheet. About one minute a loop; this is what made the collapse authorable.
- `units/spearman/fable_review.py`: the `spearman-fable-b-*` sheets (rest triptych with a silhouette difference panel, strips at 256 and 160, GIFs, 160 px contact sheet).
