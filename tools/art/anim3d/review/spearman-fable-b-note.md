# Spearman fable-b: form and motion

Branch `fable/unit-anim-3d-spearman-b` (worktree `~/LegatumRuns/anim-pilot/fable-b`), cut from the round-9 candidate.
Masters: `~/LegatumRuns/anim-pilot/fable-b-masters` (copy of the round-9 merge masters; lane root `fable-b-root`).
All evidence is Cycles CPU, 256 px, 16 samples, the round-9 grade. Materials and lighting are untouched (Fable A owns the look).
Not a PASS claim: these are form and motion candidates for the merge.

**With Fable A's look on these masters** (`look.sh` from `fable/unit-anim-3d-spearman-a` at ee83409f, unchanged): rest IoU **0.938**, delta-E 7.06 (4.56 blurred, zero offset), 160 px atlas about 186 KB at quality 80, validation PASS. A's look on my first form scored 0.920 / 6.80 (4.41): the silhouette gained, colour lost a little where the feet turned out and the legs moved under A's projected paint. See `spearman-fable-b-look-rest-compare.png`, `-look-clips-160.png`, `-look.mp4`.

## What changed

1. **Legs, feet, cloak, shaft, base (rest form).** `units/spearman/stance.py`, called in `project.py` after the 9a silhouette pass and before the UV freeze. Tuned by measuring opaque row spans at 256 px against `spearman-256.png` (script `fable-b-root/legs.py`), not by eye.
   - Rest-geometry radial scale about each leg bone's rest axis, weighted by the vertex's own skin weight (thigh 1.12, knee cap 1.18, shin 1.0, ankle 1.20; feet 1.32 x 1.30 x 1.18 about the point under the ankle on the sole plane). No bone, weight or pose change, so every clip inherits it.
   - The first pass (knee 1.46, feet 1.5) looked right but measured wrong: the painted shins are 9-10 px wide, the bulked ones 13-15. What made the stance read narrow was the knee cap, ankle and foot mass, the cloak, and both shins sitting 1.5 px too far toward the shield. The shield-facing side of both shins is trimmed; the skin calf is held at half the greave's scale so it stays inside the bronze.
   - Shield-side ankle 2.5 cm and spear-side ankle 4.5 cm nearer the midline, shield-side knee pole inward (the "A-frame" note); guard pose only.
   - Cloak: spear-side edge flared 4.5 px at hip height down to the knee; hem behind the legs levelled to y 189-193 with three shallow scallops (it sloped down past the shield-side greave and was being read as leg width).
   - Shaft, ferrules and butt radius x1.75 (3-4 px at 256, as painted); spear 1 px longer. Greave spiral ornaments hidden by visibility (they floated beside the greave as rings).
   - Stone disc radius x0.965 and the side band 8 mm deeper: rows 210-242 now match the painted disc within 1 px.
   - Greave profile fitted row by row (14 px knee cap, 9 px shin, 11 px over the ankle); sandal straps laid on the foot surface (they were free arches up to 5 cm above the instep and read as hoops at the ankle); spear-side foot turned out 24 degrees and shield-side 45 degrees, where the painted sandals lie.
   - Rest silhouette IoU against the painting (Cycles, alpha > 128, zero offset): **0.894 (round 9) to 0.932**; lower body (y > 172) 0.935.
   - Checked and left alone, with numbers: shield (column spans equal within 1 px at x 150-177), helmet and crest (row spans equal within 1-2 px at y 60-90), spear x position (95-98 vs 96-99). A lower spear hand (grip y 120) lost IoU; the hand is at 116.
2. **Death.** `units/spearman/collapse.py`: a keyed collapse replaces the retargeted Death01. Recoil, knees give with the feet planted, drop to the knees with the toes dragged back, topple onto the spear side, settle lying across the stone behind the shield. The aspis stays parented to the forearm for the whole clip; the spear is released over frames 2-4 and lies level in front of the base, inside the frame. Why keyed: Death01 flips onto its back along the camera's depth axis with both arms up and ends off the base (top/side quick-looks confirmed it), and blending it (round 10c) kept the squat-then-pop. The 40-pose audit has zero findings.
3. **Hit.** Same module, `HIT_KEYS`: chest and head snap back over planted feet, the shield is driven up into the body (turn capped near 30 degrees), the spear rocks, then a low catch and back to the exact guard. Entry and exit equal idle.
4. **Walk.** Still the CC0 Quaternius Walk_Loop retarget with the heel/toe contact locks. Added on top, all phase-locked to the clip's own measured stance intervals:
   - pelvis dip at double support (2.2 cm), sway over the stance foot (2 cm), shoulder counter-rotation (about 2.6 degrees, halved after review so the shield stays the stable mass) with the head counter-turned, a small forward lean, 2.6 degrees of spear sway;
   - step width: a constant 8.5 cm lateral ankle offset per foot (15 px between the feet at 256), so the legs read separately at 160 px; the walker is centred 7 cm nearer the disc centre;
   - both ankles re-solved by IK to the retarget's world positions after the shift, so contact is unchanged;
   - sole height per foot: the root follows the planted foot that needs the lowest pelvis; a second support or a dipping swing toe is raised by leg IK (no rigid ankle translation).
   - Feet check: planted heading 1.9 degrees, compensated slip 0.002 mm, contact error 0.000 mm (`spearman-fable-b-feet-check.png`).

## What failed or was dropped

- Symmetric leg scale: pale lobes outside the greaves (see above). Fixed with the inward-only field.
- Scaling the skin calf as far as the greave made no visible difference; the lobes were the greave itself.
- First collapse rest pose (rolled 38 degrees onto the back): the shield stood on him like a hat and the body was lifted 23 cm by the lower elbow. A side-lying rest with the pelvis-to-shoulder line tilted about 9 degrees puts hip and shoulder on the stone together.
- Foot pitch relative to the shin drove the toes into the stone when the shin tilted (body lifted up to 32 cm by the floor solver). Foot pitch is now absolute from the flat neutral sole.
- Spear landing: a diagonal landing (to shorten its screen width) puts the tip below the frame; any lie beside the base leaves the frame left or right. A 2.3 m spear only fits level in front of the base, so it cannot also stay within 20 px of the rims.
- Shin position by eye: moving the spear-side ankle a further 4 cm in lost IoU (0.918 to 0.911); the row measurements showed the error was width, not position.
- A's look waited on the machine-wide GPU lock for over ten minutes while another lane's pass held it; I withdrew the queued job twice and ran it once the lock was free (about 90 s).
- Walk_Formal_Loop: nearly the same legs as Walk_Loop; not adopted.
- The old disc-footprint sole pass pulled an overhanging planted toe 6 mm below the stone top once the steps were wider; planted soles now skip it.

## Tools

- `units/spearman/quicklook.py` + `quicksheet.py`: render chosen frames of a diagnostic (no cloth) or baked clip from the painting camera plus top/front/side, tile to one sheet. About one minute a loop; this is what made the collapse authorable.
- `units/spearman/fable_review.py`: the `spearman-fable-b-*` sheets (rest triptych with a silhouette difference panel, strips at 256 and 160, GIFs, 160 px contact sheet).

## Open, for the merge and the next round

- Colour items in the reviews (darker sandals, sole colour on lifted feet, contact shadow and side gradient on the base, shield rim value, cloak highlights, pale thigh in death) live in A's `look.py`; I did not touch materials.
- "Cloak fin" left of the helmet in the death rest: it is the horsehair crest, which lies in that plane once he is on his side. The cloak itself settles under the shoulder by frame 7.
- Requested "shield 5% larger" and "helmet and crest wider" do not show in the measurements against `spearman-256.png` (spans above); they may come from a different form in the round-11 merge.
- The death spear cannot both lie level and stay within 20 px of the base rims: it is 2.3 m long on a 1.15 m disc.
- Fallen feet are large at the painted foot size and read as pale lumps at the right of the death rest; darker sandals in the look would help more than geometry.
- Walk is still the Quaternius donor with a weight-shift layer. A CMU walk would need a new skeleton map and loop cut; not attempted.
