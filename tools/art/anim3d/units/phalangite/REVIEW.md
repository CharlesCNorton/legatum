# Phalangite: driver round 2

Candidate only. No `phalangite-PASS`: the rest pose and five clips do not yet
meet the painting parity / clean motion bar.

## What changed

The round-one GPU receipt confirms Cycles Metal 512/64, all 40 clip samples,
181,270 bytes at Q90, and the eight-second H.264 movie. Its original review
images, movie and scene checkpoints are preserved outside git. The outer driver
log was empty because `gpu.sh` redirects to its own unit transcript.

This iteration keeps the MPFB anatomy, original 19,158 vertices and 53 bones,
full-depth inverse-skinned fitting, painting-projected pigment, generated bronze
and linen fills, six AO/curvature bakes, physical straps/folds/bevels, product
lights and automatic frozen histogram grade. Calves and the right sandal are
broader. The stone has a revised ellipse/rim and a new image-generated clean
plate with no painted feet; real geometry supplies silhouette and contact shade.
Transparent plate texels blend into the underlying stone pigment, never black
or mesh transparency. Shield source-view visibility limits projection onto its
hidden reverse side. Whole-body occlusion remains unresolved around overlapping
armour, so that broader experimental mask was not retained.

Idle, move, hit and death now derive from the pinned CC0 Quaternius Standard
library. The Medjay retargeter is adapted locally; full rotations are calibrated
against source/target rest or reference poses, including bone roll. Source foot
rotations remain unchanged after retargeting. Carrying arms and a continuous
sarissa are layered on source motion. Attack is authored, with a stronger thrust
and compensating weight transfer. Death releases the sarissa at the first
falling sample. The stationary base never follows the character.

## Visual verdict

At 256 px the torso brushwork and material identity are close, but face/cheek,
fingers, shoulder contour, greave geometry and stone contour still differ.
At 64 px it reads as the same phalangite; it is still distinguishable at rest.
The unchanged camera is an approximate calibration, not a solved exact camera.
The new walk transfers through alternating stance/swing instead of shuffling.
Source foot rotations and the eight front/top diagnostic frames are checked;
sandal/greave silhouette and contact still need visual refinement. The captured
death articulates better but exposes simplified hidden surfaces and equipment
fit. No comprehensive skin/cloth/shield collision proof is claimed.

## Lead handoff

Run from this checkout's root:

```sh
ROUND=2 tools/art/anim3d/units/phalangite/gpu.sh
```

This executable needs no arguments. It verifies external inputs, rebuilds clips,
audits, renders all stages with Cycles Metal at 512 px, retains 512/256 masters,
renders all 16 front/top foot views, packs/validates the trimmed 160 px atlas,
and writes `phalangite-round${ROUND}.mp4` from the decoded trimmed atlas.
It verifies source/frame/grade hashes, alpha reconstruction, counts, padding,
size, Q75 minimum, loop/hold and movie format. GPU evidence checks reject CPU
masters and stale foot diagnostics. The completion receipt explicitly leaves
visual approval false. Inspect the fresh GPU comparison, strips and movie before
considering PASS. Source and generated-fill licences are in `SOURCES.md`.

## Verification

CPU previews are not GPU acceptance. Prior GPU results remain in `gpu-r1-preserved` under the
master directory and `phalangite-gpu-r1-preserved` under the review directory.
No game rules or UI implementation changed.

- All 48 stage/clip masters at 512 px and matching 256 px copies: Cycles CPU,
  8 samples. All five strips, animated WebPs, rest split/crossfade and details exist.
- Trimmed 160 px atlas: **194,762 bytes at Q90**, all 40 samples (8/8/10/4/10).
  Decoded alpha reconstruction, offsets, padding, source/frame/grade hashes,
  motion and identical final death rectangle passed.
- Saved-scene audit passed: original topology, 53 bones, six real bakes, frozen
  UVs, source motion, unchanged source foot rotations, stationary base, exact
  loop endpoints and held death. Largest wrist/palm proxy error is 7.58 cm in
  attack; this is not proof of clean fitted finger contact.
- All 16 foot views are current. Python/Bash syntax, input SHA256 and whitespace
  checks passed. GPU evidence validation correctly rejected CPU512 masters.
- Movie verified by ffprobe: H.264/yuv420p, 1600x360, 192 frames, eight seconds.
  Four decoded movie frames and all motion strips inspected.
- Rest silhouette IoU at alpha128: 0.805602; a registration measurement, not approval.
- Remaining prominent motion defect: the reverse shield/kit looks like a broad,
  stretched fan during death; hidden-side finish and contact need another round.
  Face, fingers, base perspective and footwear still miss the painting. No PASS.

Commit attempt was blocked by sandbox denial of the worktree index.lock. The
runner must commit the working changes with the requested co-author trailer.
The existing-HEAD repository gate passed public-claims but failed hygiene on
unspaced matrix operators and failed art in render-sets.mjs. Matrix spacing is
fixed in this working tree and direct unit Python/Bash hygiene line checks pass;
the commit-based gate cannot cover these uncommitted changes. Art-set rendering
and the new GPU pass remain unverified.
