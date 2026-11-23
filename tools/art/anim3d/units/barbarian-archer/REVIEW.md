# Barbarian archer, driver round 3

Review candidate. No PASS marker: the rest pose is still distinguishable from the
painting and the motion needs further art review.

Actual round2 GPU evidence was opened before edits: c/f sheets, all five strips,
and movie frames. It succeeded at Metal Cycles512/64,40 frames,Q85,181276 bytes,
and H.264/yuv420p eight seconds. Originals are preserved under
`masters/barbarian-archer/driver-r2-gpu/` and
`review/3d-v2/barbarian-archer-driver-r2-gpu/`.

## Changes

Ray checks found trouser and bracer surfaces around the bow fingers. Height-only
garment selection had included the lowered rest-pose hands. Semantic weight
filtering removes716 misplaced trouser vertices and1381 bracer vertices before
fitting/baking. Native hand geometry is fitted more closely in the rest camera.
Body regions beneath clothing retain cloth/leather pigment when revealed.

Closed full-depth leather toe boxes inherit MPFB weights and the original rig
parent. Motion inspection caught and corrected detached toe boxes in an early
preview; audits now check the parent. Painted stone pixels at the sole fade to
leather without clamping UVs or cutting geometry. Actual footwear sets the gait's
floor height. No foot rotation correction is applied after retargeting.

A built-in ImageGen clean stone plate fills the occluded top. Registered pigment
and the original lower rim color the real beveled disc with live contact AO.
It is not a card or a transparent cutout. Source, prompt and hashes are recorded
in SOURCES.md/inputs.json. Existing thick straps, cloth folds, product lights,
generated hidden-side fills, eight actual bakes and automatic fixed rest grade
remain. Source poses reset before sparse library/NLA actions are sampled.

## Visual judgement

At256 the stone grain, boot silhouettes and bow-hand outline improve, but the
upper-arm cuff, coarse pelt edges, sparse quiver and hand thickness still differ
from the painting. CPU256/8 details are also softer than the painting; GPU512/64
is needed to distinguish sampling loss from material loss. At64 it reads as the
same wolf-pelt archer, but silhouette parity is not achieved.

All five strips, the rest split/crossfade, foot sheet and decoded round3 movie
frames were inspected. Toe boxes stay attached and the settled death is held.
The fall still exposes a stiff front mantle and simple underside materials.
The walk lifts and pitches its feet sharply; some swing-frame heel-to-toe forward
dots are negative. The existing sampled toe/root correction uses a virtual ground
speed and is not proof of no-slip contact. These remain art limitations, not
claims of five clean approved clips.

## Exact checks

- CPU Cycles256/8: all40 frames and all b/c/d/e/front-top-feet reviews regenerated.
- Trimmed160 atlas:184062 bytes,WebP quality85; all40 frames, offsets, source/grade
  hashes, exact reconstructed alpha, clip timing and held death pass.
- Saved-scene audit:53-bone MPFB rig, semantic garment regions, toe-box parents,
  finished projection surfaces,40 string/nock/base/safe-scale samples and evaluated
  terminal death geometry pass. Eight real AO/curvature maps pass.
- All pinned source hashes pass; four delivery rejection tests pass.
- Movie:H.264/yuv420p,1600x348,240 frames,eight seconds,2x scale on cream.
- All18 Python files parse; both shell scripts pass bash -n;gpu.sh is executable;
  git diff --check passes. Missing-master GPU preflight correctly exits1 before
  Blender and records the failed stage.

Updated256 masters and editable blends are external. Previous512 GPU masters
remain preserved and are not claimed as current geometry. No Rust/runtime/UI
code changed, so no unrelated application or Rust build ran.

## Lead GPU command

```sh
ROUND=3 tools/art/anim3d/units/barbarian-archer/gpu.sh
```

The no-argument executable verifies source pins, probes Metal, rebuilds all clips,
audits saved scenes, renders every stage at512/64, publishes512/256 masters and
reviews, packs and validates trimmed160, and writes the decoded five-clip
`barbarian-archer-round${ROUND}.mp4`. It records errors by stage and never writes
an art PASS marker. GPU rendering and judgement of this revision remain pending.

Commit attempt was blocked by sandbox permission on
`.git/worktrees/lane-20/index.lock`; changes remain for the runner to commit.
HEAD includes origin/master (zero incoming commits). No push, PR or merge.
