# Spearman fable-d: death end pose and walk

Branch `fable/unit-anim-3d-spearman-d` (worktree `~/LegatumRuns/anim-pilot/fable-d`), cut from round 12 on `astra/unit-anim-3d-v2` (ef6631e9).
Masters: `~/LegatumRuns/anim-pilot/fable-d-root` (a copy of `lanes/spearman-r12-merge`; nobody else's masters were written).
Rest pose, materials and proportions are untouched (Fable C owns those). Idle, attack and hit are round 12's clips, re-rendered only.
All review frames are Eevee with the painted look (`look.py`, round 12's look folder), 640 px, reduced in display space.
Not a PASS claim: two motion candidates for the round-13 merge.

## Outputs (in `review/3d-v2/`)

- `spearman-fable-d-death-strip.png`, `spearman-fable-d-move-strip.png`: 256 px row over 160 px row.
- `spearman-fable-d-death-160.gif`, `spearman-fable-d-move-160.gif`: at game rate (death holds its last frame).
- `spearman-fable-d-feet-check.png`: top and front views of the feet, all 33 frames of the cycle.
- `spearman-fable-d.mp4`: all five clips side by side, 160 px at 2x, 8 s.

## What changed

### 1. Death (`units/spearman/collapse.py`, small hooks in `animate.py`)

The collapse is kept through the drop to the knees (recoil, knees give with the feet planted, on the knees). From there:

- **End pose.** He lies on his spear side facing the camera, rolled 0.70 rad toward his back, knees drawn up, head and crest on the stone and turned out toward the viewer, spear arm lying out in front. Pelvis rests at x = +0.22 m (it was -0.04), with a 0.2 rad turn about the vertical: head top at x = -0.59, toes at +0.59 on a stone of radius about 0.58, so the crest tip is at the left rim instead of 30 px past it and the feet are at the right rim.
- **Shield.** The round-12 pose kept the aspis strapped to the forearm, and wherever that arm lay the shield covered him. Now the shield arm goes limp across his flank as his shoulder hits the stone, and the aspis slides off the forearm band: it tips face-up across his side (frames 5-6, lying on him like a lid, never above him), then goes down onto its rim behind him and leans on his back with the face to the camera (frame 7 on). The whole body is in front of it; the upper part of the sunburst shows above his waist. It is never hidden or scaled: `place_shield` blends the control from the arm to a world rest (`SHIELD_REST`) by a keyed weight, turning through face-up at the half-way point, and is re-applied after the floor fit so the rest stays put.
- **Arms** come to rest on things in the world (new `arm_w`, `hand_*_w`, `elbow_*_w` channels), not at a place in the chest's frame. The shield arm ends behind his back, toward the shield.
- **Spear** (art director 06:16Z, item 6): tips and drops over a shorter span (`release/.56`, `/.58`), so it is level on the ground by frame 3 and no longer lies across the kneeling body; frame 2 still crosses the thighs mid-fall. Landing place unchanged.
- **Timing.** Keys at 0, .09, .21, .32 (as before), topple .47, strike .72, settle .88, rest .97. Delivered frames: 0 guard, 1 recoil, 2 knees give, 3 on the knees, 4 sagging over the spear-side knee, 5 mid-fall, 6 down with the shield across his flank, 7 settling with the shield going onto its rim, 8 = 9 held. The knees stay planted until the topple key (letting go earlier made him rise 5-9 cm before falling).
- **Floor fit.** Pelvis 0.34 m and fall 1.49 rad put the hip (on its pteruges) and the shoulder on the stone together; the solver's lift at rest is 18 mm. The 40-pose audit has 0 findings (a first try that left the pteruges out of the fit put them 5 cm into the stone; that was reverted).
- **Art director's two reviews of earlier versions (06:40Z, 06:51Z)** are answered by the above: no raised shield (it tips over him), knees drawn up with the feet at the rim, one more frame in the drop and only the required two-frame hold at the end.

### 2. Walk (`units/spearman/motion.py: WalkLayer`, hooks in `animate.py`, optional `rotations` in `kit/retarget.contact_ik`)

Still the CC0 Quaternius `Walk_Loop` retarget with round 12's contact locks. A layer on top, phase-locked to the clip's own stance intervals:

- **Swing clearance x0.35.** After the planted foot sets the pelvis height, each swing sole keeps 35% of its donor clearance above the stone. Peak sole clearance 9.5 cm to about 3.5 cm; swing ankle peak 0.42 to 0.36 m (left), 0.39 to 0.35 m (right). Scaling the ankle's height instead (first try) drove the toes-down foot into the stone.
- **Swing foot levelled** by up to 50% at mid-swing (zero at toe-off and heel strike), heading kept. This is what stops the sole flashing at the camera in frames 5-6.
- **Swing toe-out clamped to 6 degrees.** The donor swings the toes out up to 24 degrees; once the foot is level that became a readable heading and failed the 10-degree gate (10.1). Raw yaw is now 7.9 degrees at most.
- **Hip sway.** Pelvis shifted 1.2 cm more toward the stance foot (pelvis travel 6.8 to 9.1 cm peak to peak) and the swing hip dropped 4.5 degrees. The lower spine leans 3.5 degrees the other way and the chest is turned upright again, so shoulders, shield, cloak and spear travel no further than in round 12 (shield 6.5 cm vs 7.8 cm; cloak edge 87-96 px, same as round 12; spear stays upright).
- Both legs are re-solved by IK to the ankles' world positions and source rotations after the layer, so contact is unchanged.

Feet check on the baked clip (all limits pass, none relaxed): compensated slip 0.30 mm (limit 1), floor error 0.000 mm, planted heading 5.14 degrees, readable heading 7.94 degrees (round 12: 9.18), seam 0, sole translation 26 mm (limit 40; round 12: 28 mm), root correction 49 mm, foot IK 20 mm. The layer's own numbers are in `clip.json` under `walk_layer` (max swing lowering 8 cm; this is the intended edit, not a contact correction).

## What failed or was dropped

- Shield staying on the arm, leaning on his knees in front: it covered hips and torso, the same complaint as round 12 moved right.
- `WALK_INFLUENCE` 0.78 for a shorter stride: the contact classifier found two stance intervals for one foot. Left at 0.90.
- 2.8 cm of added sway with the whole chest leaning back 4 degrees: the spear rocked 10 px at the tip and the cloak edge flared 2 px more. Replaced by the lean-and-straighten spine above.
- Cloak (art director item 5, "damp the spear-side flare to 3-4 px"): air damping 2.5 and stiffer pins made no measurable difference to the edge (still 87-96 px over the cycle, 6 px of which is the body's own travel). Not solved here; it needs a cloth pass.

## For the merge

- `collapse.py` key 0 (`GUARD`) holds the round-12 guard's ankle and hand positions. Fable C's `plant_guard` change moves the guard: re-read the ankle and hand values from the new master before baking, or frame 0 will not match idle.
- `animate.py` gets three things: `MOTION_FRAMES` (diagnostic only), the `WalkLayer` calls, and `collapse.place_shield` after the death floor fit.
- Death is 2 min of pose solving plus the cloth bake per run; `MOTION_DIAGNOSTIC=1 MOTION_FRAMES=79` poses one frame in 9 s (`units/spearman/pose_report.py` prints joint, shield and floor numbers for it).
- GPU renders: the Eevee look for one clip takes about 10 s once the machine-wide lock is free; another lane's full GPU pass held it for several minutes, so iterate on `kit/quicklook.py` and `cpu_review.py` and use Eevee for the keepers.

## Open

- Only the top 40% of the shield shows behind him in the held frame (frame 7 shows most of it). A rest rolled 1.0 rad onto his back fanned the crest fully but raised the knees over the shield; legs dropped toward the camera hung off the front rim. The art director still ranks round 12's face-down ending first on calmness at 64 px; this is offered as the alternative that shows the man.
- Death frame 2: the falling spear still crosses the thighs for one frame.
- The base mesh's widest vertices are at 0.77 m while the stone top is about 0.58 m, so the death floor fit treats a ring of air around the stone as stone. Nothing rests there in this pose; worth fixing in the kit.
