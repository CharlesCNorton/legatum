# Rifleman round 2 candidate

Not visually approved; do not write `rifleman-PASS` from a technical receipt.
Incoming GPU round 1 completed successfully and is archived externally under
`masters/rifleman/driver-r1-gpu/`, including review images and movie samples.
The running critique and check results are in `review/3d-v2/rifleman-log.md`.

Round 2 fits full-depth coat, trousers, cap, pouches, boots and weighted hand
surfaces to the painting, fixes inward normals on the stock, and freezes finished
geometry before projection. The original painting remains the main pigment source.
Generated clean stone and cloth plates fill occluded areas; the coat no longer
retains the painted hand and rifle after those objects move. Hidden anatomy uses
skin, blue wool, blue trousers or leather according to deform-bone weights.
Aimed warm key, soft fill, reduced cool rim, baked AO/Pointiness, and one bounded
histogram grade remain in place. No alpha card substitutes for geometry.

Quaternius CC0 idle/walk/hit/death remain the motion source; sparse donor channels
are reset before evaluation. Hit recovers into the guard; death blends out of it.
The original rifle attack raises the gun toward the shoulder with a small depth
turn. No foot rotations are patched after retargeting. Surface fit and fingers
still require visual judgment; wrist metrics do not establish full contact.

All source assets, blend files, bakes, 512/256 masters and raw renders are external.
Only scripts, prompts/provenance, and the trimmed candidate atlas/JSON are in git.
The existing painting remains runtime art pending lead review.

From the repository root, the complete GPU handoff is:

```sh
ROUND=2 tools/art/anim3d/units/rifleman/gpu.sh
```

This rebuilds b/c/details/d/e stages using Cycles Metal with no CPU fallback,
keeps genuine 512/256 masters, writes top/front feet and split/crossfade rest
comparison, runs the finished-surface/rig audit, packs and decodes the 40-frame
160px trimmed atlas at quality >=75 and <=200,000 bytes, and makes the eight-second
1600x348 H.264/yuv420p movie. Logs now go both to the driver and master log.
CPU iteration uses `render.sh build`, `animate`, `preview`, `feet`, `audit`, `pack`,
and `validate`. Packing rejects clipped frames rather than cropping visible art.

Round-2 CPU result: 165,824 bytes at quality 90; all 40 frames and decoded trims/alpha pass. Audit: 63 finished projected meshes, zero sampled rest UV error, max wrist attachment error 0.000000784 m. Movie: H.264/yuv420p, 1600x348, 240 frames, 8 seconds. Static syntax/hygiene checks pass. At 64 px the identity is clear; at 256 px cap shape, supporting cuff/grip, shoulder contact and stiff death remain visibly below the painting. No PASS; next lead GPU review is required.
