# Pikeman round 1 review

Status: complete CPU round-one candidate, **not art approved**. PASS intentionally absent.

## What exists
- True 3D MPFB anatomy and 53-bone rig; original steel breastplate, articulated limb armour, fluted tassets, kettle helmet, leather fittings, long slender pike and stationary cream disc.
- Frozen visibility-masked painting UVs on finished weighted surfaces; generated hidden linen/steel brushwork; six actual AO/Pointiness bakes. Geometry fitting preserves full depth and inverse skin transforms.
- Quaternius CC0 idle/walk/hit/death with source/rest/bone-roll compensation; two-hand constraints; original pike thrust. Hit recovery reuses the captured reference sample. Death anatomical retarget fixes the braced-leg collapse artifact.
- All b/c/d/e review sheets and five animated WebPs, rest split/crossfade and top/front feet check, plus labelled CPU round1 MP4.
- 40-frame 160px trimmed atlas: **174736 bytes, quality 90**. External editable .blend sources and native 256px CPU masters. Final 512/GPU masters await the host command.

## Visual judgment
At 64px the silver armour, wide guard, diagonal long pike and cream disc read as the same unit. At 256px the render is still visibly softer and less crafted than the painting: grip/shoulder registration remains imperfect, the helmet/armour contours and painted edges are not exact, the stone rim is too uniform, and newly exposed areas in movement/death show stretched paint and simpler surfaces. No claim of indistinguishability or final clean-motion approval. The attack is now a visible depth thrust; death settles with identical final frames. Visual review used the actual CPU comparisons, pose and motion strips, and top/front feet sequence; no live GPU output was available.

## Exact checks
- Python AST parsing: 18 unit scripts passed. Both shell entry points passed `bash -n`; `git diff --check` passed.
- Scene check passed: finished meshes, 53 bones, frozen camera-only pigment, no painted feet on static base, no near-zero scales.
- All five rig audits passed: finite transforms, stationary base, wrist-axis bound, held terminal death. Wrist-axis distance is not a finger-contact/collision guarantee.
- Trimmed atlas validation passed all five frame counts 8/8/10/4/10, exact alpha reconstruction, transparent margins, visible motion, current hashes and pixel-identical held death. 174736 <= 200000 bytes, quality 90 >= 75.
- Feet: minimum planted forward-axis dot 0.99999994; maximum **sampled ankle** stance residual 0.000001103m at virtual travel 2.167422m/s. This is a sampled stance check, not a continuous sole/cloth/armour collision solver.
- MP4 verified: H.264 yuv420p, 1600x348, 240 frames, 8.0 seconds; five clips at 2x on cream, CPU-preview label.
- Repository gate against existing HEAD (pending files could not be committed): hygiene PASS and public-claims PASS; art gate FAIL because its Node `render-sets.mjs` browser rendering subprocess exited 1. No art-gate pass claimed.
- No Rust, game rules or runtime UI changed. No full engine build needed. `origin/master` had no commits ahead of this checkout; no fetch/merge performed.

## Lead command
```sh
ROUND=1 tools/art/anim3d/units/pikeman/gpu.sh
```
Run from repository root, no arguments. The executable checks Metal, regenerates clips, audits and renders every stage on Cycles GPU, exports true 512/256 masters, reruns pack/validation, renders feet, and writes the round MP4 plus GPU-only receipt. Missing GPU fails explicitly. Keep PASS absent until the actual GPU rest comparison and all motion meet the painting.

## Useful implementation findings
- Death cannot retain a braced guard-leg reference: retarget the anatomical pose and blend the entry from the guard.
- A backward planar toe vector during airborne toe-off is not duck-footed stance; compare planted phases against travel and inspect the source motion.
- Apply geometry modifiers before UV projection. Fit weighted surfaces through inverse skin transforms; preserve camera depth and original articulation.

## Commit handoff
`git add` was denied creating `.git/worktrees/lane-3/index.lock`. Changes are uncommitted for the runner; no push or PR was attempted.
