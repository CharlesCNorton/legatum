# Spearman: where it stands and what is open

Unit-specific status for the first unit through the pipeline. The rules these items produced are in `../SKILL.md`; numbers per round are in `../LOG.md`. Positions are pixels at 256 in the painting's frame. Latest reviews: `~/LegatumRuns/anim-pilot/review/3d-v2/spearman-FEEDBACK.md`.

## Latest candidate (Fable C, 2026-11-24 about 06:30Z, awaiting merge and review)

- `fable/unit-anim-3d-spearman-c`, cut from round 12: rest **IoU 0.9534, blurred ΔE 3.35** in Eevee through `look.py` (CPU proxy 0.9513 / 3.31); regions feet 5.4, base 3.3, legs 3.0, cloak 4.8, shield 2.0, torso 2.5, head 3.4. Passes the 0.95 and 6 targets and the bar for showing Sam; lower body IoU 0.965.
- How: guard pose replanted on the painted feet (pelvis 5 cm back along the view ray, ankles at their painted positions, knees on columns 112.5 and 146.6), disc registered (1.6 px left, 3% shallower), cloak flare 4.5 → 3.2 px, ground shadow as two ankle-anchored blobs, side-band gradient, sandal tone.
- For the merge: `check_frozen.py` fails on idle and attack until re-pinned (same choreography, new guard); the walk's height correction is 3.7 cm of 4; attack frame 0 places the feet about 3 px lower than the guard (make its targets relative to the guard ankles); run `prepare-look.sh` after any master rebuild.
- The shield rim, cavity and greave-highlight items below are faults of the `gpu.sh` render path, not of `look.py`; deliver through one path.

## Status (round 12 GPU, 2026-11-24 06:16Z)

- IoU 0.9384, blurred ΔE 4.72 (passes), raw 7.52, atlas 186,556 bytes at q80. No PASS.
- Regions (blurred ΔE): shield 2.4, torso 2.9, legs 3.4, head and crest 3.7, cloak 4.8, base 4.8, feet 12.9.
- GPU trend: R10 0.9039 / 6.47, R11 0.9275 / 4.59, R12 0.9384 / 4.72.
- Build: Fable A's Eevee look on Fable B's form and keyed death, R12c's KayKit donor hit and widened Quaternius walk. Idle and attack are frozen.
- Reviewer's bar for showing Sam: IoU ≥ 0.94 and blurred ΔE ≤ 6 with good clips.

## Open at rest, ranked

1. Feet (y 206–224), the only failing region. About 16 px wide against the painting's 20, luminance 169 vs 141, each on a hard dark slab (left x 84–102, right x 147–164, y 217–224). Painting: both feet point toward camera-right, about 20 px wide and 10–12 px tall at the instep, mid-brown with three dark strap bands and a thin dark sole line. Try a foot about 1.25× (length 1.35× and 1.42× both broke the 40 mm sole-correction limit), raise the instep 3–4 px, and cut the slab to a soft contact shadow no wider than the sole plus 2 px, warm brown about (150,105,70) at 40%.
2. Base: R12 lost the 1 px light lip R11 had; top (233,198,156) vs (249,217,176), side target (225,180,124). Add the faint warm shadow behind the feet (x 110–170, y 216–224, 6–8% darker).
3. Bronze cavities a little light: cuirass p10 luminance 40 vs 31, shield rim 50 vs 38, helmet 35 vs 26; deepen only the darkest cavities about 20%. Right greave highlights hot: p90 211 vs 179.
4. Pale sliver under the spear hand at about (106,122); the painting has plain forearm skin.
5. Cloak on the spear side: lit folds dark (p90 140–145 vs 150–158), mean (127,53,32) vs (133,62,36); hem behind the right leg (x 140–165, y 175–195) should be level at y ~190 with three 2–3 px scallops.
6. Legs slightly A-framed against the painting (cloud reviewer): shins more vertical, feet a little closer together.
7. Shoulder shell is still angular in hit and death; no corrective shape has been sculpted.

## Open in the clips

- Move: the trailing foot lifts to mid-shin in frames 5–6 and reads as a parade march at 160; lower the swing peak by a third. Legs read separately in every frame; keep that. Walk heading is 5.1° (readable 9.2°, limit 10°) on the larger feet; root correction 48.96 mm of 50.
- Hit: frames 1 and 2 are nearly the same pose; push frame 1 further (torso 4–5° more back, shield 5 px closer) and make frame 2 the half-way return.
- Death: in frames 2–3 the spear crosses in front of the body and at 64 px cuts the figure in two for one frame; let it fall 10 px further toward the viewer. Final frame is good.

## Closed, keep on the regression list

- Shaft thickness and wood colour (R11, 1.8× in the master).
- Linen value, pale blob between the thighs, shield and cuirass highlights (the look, R11).
- Calf outside the greave and the floating ring ornament (R11a, Fable B).
- Cloak width on the spear side (Fable B flare: 683 px vs 632).
- Pale shoulder patch in hit and death (R10b, then the look and R12b's rear-shoulder pigment).
- Soles seated on the stone: 3.0 mm → 1.0 mm (R12).
- Death ends on the base with shield face and crest readable at 64 px (Fable B's keyed collapse).
- Base lip: fixed in R11, **lost in R12**.

## Spearman settings worth knowing

- Camera: orthographic, location (2.5, −7, 3.0), target (0, 0, 1.2), ortho scale 2.9.
- Registration: 5.3425 source px per 256-canvas px, source (627,627) ↔ canvas (127.5,128). `project.py`'s frozen UV formula is 0.9% narrow and 0.3% short; the correction lives in the look's texture registration. Switch both together at a rebuild.
- Rest form (Fable B, measured by row spans): thigh 1.12, knee cap 1.18, shin 1.0, ankle 1.20; skin calf at half the greave's scale; merged foot width × 1.50, height × 1.18, original length; shaft radius × 1.75–1.8; disc radius × 0.965, band 8 mm deeper.
- Look (`units/spearman/look.py`): sun strength π at 24°; cast-shadow depth 0.22 on projected paint, 0.45 on unseen fill, 0.85 on stone; ramp input fill 0.30, AO 0.55, stroke 0.10; contact shadow at 40%.
- Motion: Quaternius `Idle_Loop`, `Walk_Loop` at 0.90 source influence with an 8.5 cm lateral ankle offset per foot; KayKit `Hit_B`; keyed death (`collapse.py`) and attack. Clips 8/8/10/4/10 frames at 4/6/14/12/4 fps.
- Cycles hybrid fallback (through R10): key (−3,−4,8) 596.75 W size 5; fill (4,−2,3) 77 W; rim (−2,3,4) 132 W; world 0.19; one histogram grade at strength 0.80.
