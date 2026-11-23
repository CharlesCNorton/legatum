# Peltast — driver round 2

The incoming round1 GPU pass succeeded: Cycles Metal 512 px / 64 samples, 40 frames, 196,858
bytes at WebP quality 80 and an eight-second H.264 video. Its images were opened
before edits. The original GPU evidence is retained externally under
`masters/peltast/driver-r1-gpu/`. Driver round numbers are distinct from earlier
local iteration numbers in the running log.

## Changes

- Raised/rearward fox-hide crown, shorter anatomical beard shell, fuller thighs,
  finer iron tips and a tapered/beveled limestone disc. These are full-depth
  mesh edits before frozen rest-camera UVs; no image plane supplies the figure.
- Original ImageGen clean-stone fill, live contact AO, preserved generated
  cloth/wicker/leather unseen fills, real AO/curvature bakes and the automatic
  frozen histogram grade. Input hashes and licences are recorded in SOURCES.md
  and assets.lock.json. Existing cloth folds, straps/buckle and product lights remain.
- CC0 Quaternius idle/walk/hit/death retargeted through Blender constraints with
  rest/reference and bone-roll calibration. Native equal foot sizes are set
  before retargeting. The carrying arms layer open idle; the throw is authored.
- Root translation preserves virtual-ground stance contacts without editing foot
  rotations. Full-anatomy death grounding and keyed cloth plane-contact corrections
  prevent the preview's torso/cloth sinking. This is not a cloth simulation.
- Front/top views of all eight walk samples, including actual boot geometry.
  The unsaved diagnostic scene removes equipment to prevent animated visibility
  keys from restoring weapons across the feet. GPU handoff validates
  the diagnostic source and image hashes as well as the existing masters.

## Visual verdict

**Not PASS.** At256px the clean cream stone, cap contour and fine iron tips are
closer to the painting, and original red linen/wicker brushwork remains strong.
The face/beard/neck transition, nape hide and cloak contour still look different;
the shield is slightly too deep/large along its lower rim. At64px it reads as the
same red/blue crescent-shield peltast, but it is not indistinguishable at rest.

The open walk has real knee/ankle motion instead of the old spread-leg shuffle.
The fall now stays above the stone, but exposed undersides and the equipment
settle remain less convincing than the painting. Rearming the javelin is still
abrupt. Technical contact/loop checks are not a full collision solver or visual
approval of all five clips. No PASS marker is written.

## GPU handoff

From the repository root, run:

```sh
tools/art/anim3d/units/peltast/gpu.sh
```

No arguments; the overnight driver supplies ROUND. The script defaults to round 2,
rebuilds all clips, audits, renders all stages using Cycles Metal 512 px / 64 samples, retains
512/256 masters, generates every review including rest/crossfade and feet views,
packs and validates the trimmed160px atlas, and writes the eight-second five-clip
`peltast-round${ROUND}.mp4`. It preserves failure-stage logs and a receipt that
leaves art approval false. This round's Metal pass remains for the lead.

Full reproduction before that handoff: prepare inputs, then unit render.sh stages
`build`, `refine`, `paint`, `bake`, `c`, `animate`, `audit`, followed by b/d/e/feet.
Never run refine twice on one unpainted master. All six Blender skills were used.

## Checks

Final measured delivery evidence is appended after packing below. No Rust, rules,
UI or runtime code changed; broad Rust/WASM/app suites are not applicable.

- Actual CPU Cycles 512 px / 16 samples renders for b/c/d and all 40 clip frames, with 256 px derivatives; all strips and decoded video contact frames inspected. GPU64 remains pending.
- Trimmed 160 px atlas: **188,106 bytes, quality 75, 1384x747**, lossless 8-bit alpha (zero error),39 unique rectangles /40 playback frames. Q80 was209744 bytes, so Q75 is the highest full-alpha setting under 200000.
- Validation PASS: source/clip/grade/audit/feet hashes, dimensions, counts, trim reconstruction, alpha, margins, motion and byte-identical decoded terminal death.
- Skeletal/geometry audit PASS:53 bones, stationary base, safe transforms, finished-rigid UV error 0 px, both skeleton/equipment loop closures, attack guard endpoints, held death. Walk baked-foot rotation error0; planted forward dot0.999391; virtual-ground toe slip1.86e-09m. Hand/equipment translation error <=3.03e-7m on idle/move/hit. Intentional attack/death releases are excluded from that grip check.
- Video: h264/yuv420p,1600x348,240frames,8.000s.
- 19 Python syntax checks, 2 shell syntax checks, 9 source input hashes, executable GPU entry, missing-master preflight failure, CPU-master rejection and whitespace checks PASS.
- Full silhouette alpha IoU (threshold32): incoming GPU0.82382 -> CPU round 20.83636; figure above row200:0.80406 -> 0.80976. These are framing measurements, not an art-quality score.

Git staging/commit was attempted with the requested co-author trailer, but the
sandbox denied `.git/worktrees/lane-21/index.lock`. Changes remain uncommitted
for the runner. Available origin/master is already an ancestor; no merge was
needed. No push or PR.
