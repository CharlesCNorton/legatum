# Round 2: improved candidate, not approved

Opened the supplied round-one GPU c/f comparisons, all five clip strips and four
movie samples before editing. The driver's named log was empty because gpu.sh
redirected output internally; GPU receipts show round one completed at 512px/64
samples, Q80, 187340 bytes. All supplied evidence is archived in external
`masters/keshig/driver-r1-gpu/`. No keshig-specific feedback file was present.

Changes: anatomical horse-joint registration at retained depth; source-action
reference compensation, including resetting omitted static glTF channels; wider
rider head/cap and longer bow arm; smooth solid recurved bow; full-depth belly
sculpture; thick weighted tail locks; head/saddle-weighted reins; camera-visible
stone grain/AO. Frozen painting projection, generated hidden fills, real helmet
AO/Pointiness bakes, cloth folds/thickness, bevelled kit and product lighting are
retained. One rest-fitted histogram grade is applied to every rendered frame.

## Verified CPU result

- All stages rendered with Cycles CPU, 256px, 8 samples: plain/rest/details,
  four attack poses, five clips (8/8/10/4/10), and 16 top/front feet views.
- Geometry audit passed: stationary base, safe scales, source/master hashes,
  no below-support move geometry, and first-move fitted-reference regression.
- Trimmed 160px logical-cell atlas: **196016 bytes, quality 80, 40 frames**,
  1490x700 encoded size. Independent verification passed all rectangles,
  margins/gutters, exact reconstructed alpha, held death and source locks.
- Movie verified: **1600x348, H.264 yuv420p, 240 frames, 8.000 seconds**.
- Python syntax: 15 files passed; Bash syntax and diff whitespace passed.
  Working-tree hygiene line checks: 23 files, zero findings. Compact matrix
  operators were spaced to avoid email false positives, with AST equality checked.
- Repository HEAD public-claims passed. The browser art gate failed in
  render-sets.mjs before a distinctness verdict. This is not an art-gate pass.
- Git staging failed creating lane-12/index.lock (Operation not permitted).
  Changes remain uncommitted for the runner. No Rust or UI runtime changed.

Current masters/256 and editable blends are external. Previous GPU512 output is
archived, not presented as fresh round-two 512 evidence. Fresh GPU512/256 output
is the lead's pending handoff.

## Honest visual verdict

The full alpha-silhouette overlap improved from 0.5695 to 0.6960 at 256px and
0.5727 to 0.6997 at 64px (includes the base; not a visual-quality score). The wide
galloping outline reads much closer at 64px. At 256px the lower coat/seating,
cap profile and muzzle geometry still differ, and projected detail becomes
misregistered as surfaces turn. Tail mass is improved but less natural than the
painting's locks. Death still obscures the rider and needs equipment/contact
polish; the attack release needs stronger articulation.

Over-wide move/attack/death samples are uniformly fitted into the fixed camera
and re-grounded. Per-frame scales are recorded in audit.json, bounded above
0.85; move reaches 0.88. This avoids clipping but produces scale modulation,
which remains a quality defect. Foot direction follows the original rig; the
support audit and front/top images are not proof of zero sliding.

**No PASS marker.** These are five technically validated clips, not five
visually approved clips. Rest is not hard to distinguish from the painting.

## GPU handoff

From the repository root:

```sh
ROUND=2 tools/art/anim3d/units/keshig/gpu.sh
```

The executable no-argument script now rebuilds every model stage from this
checkout, renders all stages on Cycles Metal GPU at 512px/64 samples, keeps
512/256 masters, packs/validates the trimmed atlas, emits the comparison and
five-clip movie, and tees output into both the driver and unit logs. It never
writes PASS. The lead still needs to inspect that new GPU evidence.
