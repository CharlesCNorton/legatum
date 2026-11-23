# Spartan hoplite — driver round 3

**No art PASS.** At 256 px, the leg/foot registration, visible cape painting,
layered linen and spear silhouette are closer to the painting. Helmet/gaze,
neck/shoulder drape, skin and sandal shapes still differ; the stone is still less
rich than the painted disc. At 64 px the same hoplite identity reads, but the
contour and finish remain distinguishable. Source projection stretches in motion.
The terminal death legs are visibly too raised after the lower-body fitting,
a regression from the flatter round-2 landing. The next pass must reconcile the
fitted lower-limb bind geometry with anatomical retargeting. Five technically
valid clips are **not** five visually approved clips.

Incoming round-2 GPU pass succeeded: 172,022 bytes at Q85, GPU512/64 masters and
an eight-second validated movie. All c/f/e sheets and movie frames were opened
before editing. Common FEEDBACK through item 23 was read; unit-specific FEEDBACK
was absent at both opening and final checks. All six Sam Blender skills were used.

This round:

- Fits full-depth lower limbs, greaves and sandals through inverse skin matrices,
  preserving original MPFB topology and weights. Adds a continuous folded linen
  tunic under shortened armour tabs, with real thickness and a beveled hem.
- Fixes reversed cape winding: its projection weights had all been zero. Restores
  source-painted folds and an asymmetric hem before frozen-camera UV generation.
- Registers the complete straight solid spear to the source, with independent
  hand-depth and grounded-butt constraints. Reuses recorded generated skin,
  crimson cloth and leather fills on unseen surfaces; adds stone pigment grain
  and live AO. Existing bevels, straps, buckles, product lights and the automatic
  rest-derived histogram grade remain.
- Transfers anatomical foot/toe weights to finished sandals so toe roll does not
  pass through rigid shoes. Open-action walk contact targets evaluated sandals
  using root translation; foot rotations remain source-driven. Authored attack
  and carried spear support use evaluated geometry.
- Adds cape-projection and rest-grip regression checks, actual-sandal yaw/slip
  measurements, and fresh GPU master checks. GPU handoff defaults to round 3 and
  the new checkpoint. No runtime loader or game rules changed.

Final CPU evidence (Cycles, 256 px, 12 samples):

- All **40 RGBA clip frames**, counts **8/8/10/4/10**; 48 total stage frames,
  plus 16 actual top/front feet renders. All b/c/details/d/e/f/g sheets refreshed.
- Full forty-sample rig/equipment/cloth audit: **0 findings**. Scene/input checks:
  **174 projected meshes, 19,158 anatomical vertices, 53 bones**, nonzero scales,
  pinned asset hashes, cape projection mean **0.215054**, rest grip **0.037509 m**.
- Four planted intervals: maximum evaluated-sandal ground error
  **0.0000000537 m**, maximum sole yaw **2.074345 degrees**. Ankle displacement
  **0.037312 m** is diagnostic, not the contact target. Solver root correction is
  bounded to one quarter of measured sandal length; independent output limits
  remain **25 mm** slip and **20 degrees** yaw.
- Trimmed **160 px**, **172,172-byte WebP at quality 85**, per-frame offsets and
  anchors. Counts, alpha/RGB reconstruction, motion, margins, hashes and held death
  all pass.
- Decoded atlas movie: **H.264/yuv420p, 1600×348, 240 frames, 8 seconds**.
  All five strips, feet sheet, rest/details/poses and 16 decoded movie frames opened.
- Rest silhouette IoU **0.787116 → 0.846854** versus round-2 GPU evidence.
  This is contour evidence only, not exact viewpoint or art parity.
- **20 Python files** parse; shell syntax/executable and whitespace checks pass.
  Current-file hygiene: **27 files, 0 findings**. Public-claims passes.
  `origin/master` has **0** commits outside HEAD. No Rust/UI build was needed.
- GPU provenance gate correctly rejects the CPU set as missing fresh 512 masters.
  GPU rendering and lead art review remain outstanding.

External editable masters, clips/caches, raw renders, 256 derivatives and reports:
`~/LegatumRuns/anim-pilot/masters/spartan-hoplite/round4-3d/`.
The unpainted checkpoint is the repeatable input. Prior GPU512/256 masters remain
in `round3-3d/`; incoming review evidence is in
`review/3d-v2/spartan-hoplite-round2-gpu-preserved/`. Current review sheets,
`spartan-hoplite-round3.mp4`, decoded video sheet and running log are in
`~/LegatumRuns/anim-pilot/review/3d-v2/`.

Lead-side complete handoff, executable and requiring no arguments:

```sh
ROUND=3 tools/art/anim3d/units/spartan-hoplite/gpu.sh
```

It rebuilds, checks/bakes/audits, renders every stage at Cycles GPU512/64, retains
512/256 masters, renders feet views, verifies provenance, packs/validates the
trimmed atlas and encodes/verifies the movie. It refuses CPU fallback and never
writes PASS automatically. The current candidate is for continued review.

Git staging was denied creating `.git/worktrees/lane-12/index.lock`; changes are
left uncommitted for the runner. The requested commit message and co-author line
are saved in `~/LegatumRuns/anim-pilot/tmp/spartan-driver-round3-commit.txt`.
No push or PR was attempted.
