# Spearman fable-c: rest stance on the painted feet, ground shadow, side band

Branch `fable/unit-anim-3d-spearman-c` (worktree `~/LegatumRuns/anim-pilot/fable-c`), cut from round 12 on `astra/unit-anim-3d-v2`.
Masters: `~/LegatumRuns/anim-pilot/fable-c-root` (a copy of `lanes/spearman-r12-merge`; nothing else was written).
Not a PASS claim. Death and walk code are untouched (Fable D).

## Numbers (rest, 256 px, critique.py definitions, zero offset)

| | IoU | blurred dE | feet | base | legs | cloak spear side | shield | torso | head |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Round 12, CPU proxy | 0.9394 | 4.55 | 13.35 | 4.75 | 2.87 | 4.37 | 2.22 | 2.71 | 3.73 |
| fable-c, CPU proxy | 0.9513 | 3.31 | 5.27 | 3.23 | 2.61 | 4.49 | 2.23 | 2.63 | 3.73 |
| fable-c, Eevee GPU (1280 reduced) | **0.9534** | **3.33** | 5.16 | 3.26 | 3.02 | 4.82 | 2.03 | 2.48 | 3.42 |

Both candidate bars pass (IoU >= 0.94, blurred dE <= 6), and so does the 0.95 silhouette target. Lower-body IoU (y > 172) 0.9565 to 0.9652.
Compare: `spearman-fable-c-rest-compare.png` (painting | render | crossfade | silhouette difference, 256 and 160). Feet at 8x: `spearman-fable-c-feet-zoom.png`. Clips: `spearman-fable-c-clips-160.png`.

## What the leg problem was

Measured on an 8x gridded crop, not by eye: the modelled soles lay **3.3 px (spear side) and 2.7 px (shield side) below the painted ones**, and only about 1 px off sideways. The ankle joints were 4 px low, so the knee-to-ankle line was 36 px long where the painting's is about 30: that is the "A-frame". The painted sandal paint was landing on the greave bottoms and the stone, which is why the feet region scored 13 and the sandals read pale.

An orthographic camera cannot see depth, so the fix is to stand the feet deeper on the disc (which raises them on screen) and take up the leg length in the knees, toward the camera, where it does not show:

- `stance.py: plant_guard` (called from `project.py` after `brace_feet`, before the UV freeze). The pelvis moves 5 cm back along the view ray in the guard pose (its picture does not change), both ankles go to their painted screen positions at their own height above the stone, and each leg is re-solved at its own bone lengths with the knee at the painted knee column (112.5 and 146.6). Guard pose only: no bone scale, bind, weight or rest-mesh change. The spear keeps its foot on the stone and its picture; its head follows the hand along the view ray (3 degrees of lean in depth).
- This is a pose edit, not the rest-geometry edit the brief suggested. A rest-mesh shear big enough to lift the feet 3 px would put the foot mesh about 15 cm off its ankle bone, and the walk's heel-toe roll would swing it through the stone.

Also registered while measuring rows (each a few tenths of a percent of IoU):

- Disc: 1.6 px left, 0.2 px down, 3% shallower along the view (`BASE_SHIFT`, `BASE_DEPTH`). The far rim was a row high and the whole disc a pixel right. The band keeps B's 163 mm depth (the scene check pins it).
- Cloak spear-side flare 4.5 to 3.2 px (it stood 1-2 px outside the painted edge on rows 99-147). Hem line: 187 either side of a centre lobe at 191, as measured.
- Spear tip 5 to 6.2 px right of its foot: the shaft was 1 px left along its whole length.

B's shield and helmet spans are untouched.

## Look (look.py)

- **Ground shadow** (new): the painting has one soft warm shadow on the stone top behind the heels and across the gap between the feet (x 114-144, y 208-218; luminance 164 against 225 on the front of the top). It is not a cast shadow of the key, and AO does not make it (tried: a 0.4-2 m ambient term darkens under the shield in front instead, base dE 2.7 to 5.4). It is drawn in the stone shader from two world-aligned empties that follow the ankle bones at render time: one blob per foot, offset back and inward, fading as the foot lifts. Same result in Cycles and Eevee, and it travels with the feet in the clips. Feet region 10.8 to 5.3, global 3.96 to 3.31. Top between the feet now 160 (painting 164).
- **Side band**: `side_drop` 0.06 from lip to foot plus `side_foot` 0.18 on the lowest tenth. Base 2.99 to 2.69. The painted band is nearly flat at the centre column; the gain is on the flanks and the ground line.
- **Sandals**: see the last section; set from the Eevee measurement.
- **Shield rim**: measured by radius on the right half of the shield, Eevee: rim (r 0.9-1.03) 54-65 against the painting's 64-70, face within 2. The rim is already darker than the painting, so it was not darkened further.

## Checks

- `check_scene.py` passes unchanged.
- Feet check passes with round 12's walk numbers to the digit (slip 0.0016 mm, floor 0.0004 mm, planted heading 5.14, readable 9.18, root 48.96 mm, IK 19.94 mm, sole 39.95 mm): the walk is not moved.
- `check_frozen.py` fails on idle and attack, as it must after a guard change: the donor idle and the attack keys are the same, rebuilt on the new guard. The merge has to re-pin `frozen-actions.json` after its own review; I did not.
- Attack: its arm keys are rig-space constants about the old pelvis, which left the arms 2.5-5 cm (along the view ray) off the guard at entry and exit; the audit caught it. `animate.py` now adds the guard's pelvis shift (`rig['guard_shift']`, zero on other masters) to those arm targets and poles. Attack leg targets are unchanged.

## For the merge

- The walk inherits the guard's pelvis location (the retarget copies rotations only), so the hip drop of 1.2 cm shows up as a walk height correction of 3.7 cm against the 4 cm assertion in `animate.py` (round 12: 2.5 cm). That is why `DEEPEN` is 0.05 and not the 0.075 that I measured first (same picture, same IoU; more knee bend). If Fable D's walk needs headroom, lower `DEEPEN`; below about 0.03 the shield-side leg can no longer reach its painted ankle.
- Attack frame 0 still places the feet at the attack's own rig-space targets, about 3 px lower on screen than the planted guard (round 12 had a 2-4 px sideways step at the same place). Making those targets relative to the guard ankles is the clean fix; it changes the frozen attack, so I left it.
- Idle to move: the walker's feet are the round-12 walk's feet, now about 2 px below the guard's.
- After any master rebuild run `prepare-look.sh` (ID pass, textures, Eevee light pass, ramps): the paint must be re-registered to the moved legs. Feet dE drops again with it.

## What failed or was dropped

- Ankle targets alone, without the knee columns: IoU fell to 0.936 (shield-side shin 2-3 px right near the knee). The knee column is the second half of the fit.
- Moving the rig object instead of the pelvis pose: same picture, but every rig-space constant in the clips moves with it and the attack's feet sink 1.2 cm into the stone.
- `BAND = 0` with a larger disc shift scored 0.9522, but it breaks the pinned band depth; the 3% depth squash recovers 0.9513 inside the check.
- A walk-side offset to absorb the hip drop: not mine to change, and it would only have hidden the cost from the assertion.
