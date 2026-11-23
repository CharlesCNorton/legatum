# Barbarian crossbowman — driver round 2

Review candidate; **no visual PASS and no runtime activation**.

The prior driver GPU pass succeeded: Cycles GPU64/512 masters, 256 derivatives,
40 frames, Q90 / 157272 bytes, and an eight-second decoded-atlas MP4. Its actual
comparison, five strips, video and source evidence were opened before edits and
archived under `masters/barbarian-crossbowman/driver-r1-gpu/`. Earlier local
iteration headings in the running log do not correspond to driver round numbers.

This round closes the hood crown in one thick continuous mesh, fits the legs,
boots, bolt case and stone closer to the painting, deepens the steel prod curve
and straightens the bowstring. Finished surfaces retain frozen camera projection,
visibility/incidence masks and generated unseen fills. Leather now receives a
warmer generated fill; the physical stone has subtle pigment grain and contact
shading. Real AO/curvature maps were rebaked, and one automatic rest histogram
grade is applied to all clips. No live image warp or billboard geometry is used.

Idle, move, hit and death now use the existing pinned CC0 Quaternius library,
retargeted with full reference/rest rotations including bone roll. The attack is
crossbow-specific authored motion. The carrying layer raises the weapon; hit
returns to guard and death releases the crossbow. Source endpoint drift was
caught by the audit and fixed at the extra unsampled loop key. Foot rotations
are not patched after retarget; floor and stance adaptation are translations.
The trouser extraction excludes the neutral-pose hands. Sources and licences
are in `SOURCES.md`, with source bytes checked by `retarget.py` and `inputs.json`.

At 256 px the face, hood, stance, weapon and stone are closer, but the quilted
cloth is too rigid, boot surfaces stretch in motion, the bolt case remains
simpler, and newly revealed surfaces lack the painting's craft. Plain side views
expose unfinished sleeve/garment construction. At 64 px it reads as the same
hooded crossbowman, but its foot and clothing silhouette is distinguishable.
Alpha-mask IoU (threshold 128) improved from **0.808463** on the prior GPU rest
image to **0.855167** on the current CPU preview; differing render settings and
this silhouette-only metric do not establish visual parity.

All five strips and decoded MP4 contact frames were inspected. The captured walk
and backward collapse improve on the earlier authored motion, but boot rollover,
cloth rigidity and revealed surfaces prevent a clean-motion verdict. No cloth
simulation or full body/cloth collision guarantee is claimed. No PASS file exists.

Verified current CPU candidate:

- Cycles CPU8, native 256 px, all b/c/d/e reviews and 16 front/top foot views.
  The rest comparison, detail image, five strips, looping WebPs and round2 MP4
  are in `review/3d-v2/`.
- Trimmed 160 px atlas: **165030 bytes, WebP Q90**, 40 samples, full alpha and
  per-frame offsets. Source/model/grade/frame/atlas/metadata hashes, bounds,
  motion, exact trim-alpha reconstruction and decoded terminal death hold pass.
- Source audit: all five 53-bone clips pass. Maximum wrist/stock error is
  **0.000362 mm**; idle/move closure is exactly zero; hit recovery matrix error
  is below **4e-18**. Base remains stationary; scales remain safe and nonzero.
- Foot evidence: **2.6446 degrees** maximum support yaw and **0.000588 mm**
  maximum toe-stance residual over five measured intervals against a single
  virtual ground speed. This measures toe joints, not full heel/sole contact.
- MP4: **H.264/yuv420p, 1600x348, 240 frames, 8.000 seconds**, reconstructed
  from the trimmed atlas at 2x on cream.
- Two delivery regression tests pass, all 15 Python files compile, both shell
  scripts pass syntax checking, and diff whitespace checks pass.
- The independent final-master check correctly rejects this CPU evidence.
  Revised GPU512 masters remain pending; prior GPU masters are archived.

Run the complete executable, no-argument host handoff from this checkout:

```sh
ROUND=2 tools/art/anim3d/units/barbarian-crossbowman/gpu.sh
```

It checks Metal, rebuilds/bakes/retargets/audits, renders real front/top feet plus
all b/c/d/e stages at GPU64/512, retains 512/256 masters, validates their provenance,
packs/validates the trimmed atlas and writes/probes the round MP4. Foot evidence
is now also required by the independent GPU gate. Technical success never writes
PASS. Review the fresh GPU output before approval.

`origin/master` is already contained in this branch. Git staging was denied at
`.git/worktrees/lane-19/index.lock`; the runner must commit the changes. No push,
PR, cloud upload or deployment was attempted. Only this unit's playbook chapter
was changed; no Rust/UI/runtime code was touched.
