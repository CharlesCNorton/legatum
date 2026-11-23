# Barbarian pikeman, round 2

Status: **candidate, not an art pass**. No PASS marker. True articulated MPFB
anatomy, original full-depth kit and frozen surface UVs; no billboard or relief
substitute. Prior round evidence is preserved outside git in
`masters/barbarian-pikeman/round1-preserved`.

At 256 px, the coat brushwork is crisper, the forward elbow/fist are much closer
to the reference, the oversized kettle brim is reduced, knees/boots fit better,
and the pike is thin and continuously brown. Fitted garments now inherit exact
anatomical vertex weights; this removes the sleeve spikes caused by copying
hands into clothing and assigning nearby finger weights. Static modifiers and
macro shapes are finished before camera projection. Camera-only painted pigment
avoids double lighting and source illumination spilling onto other surfaces.

The cream stone has a smooth bevel, low grain, live contact shading and no
projected boot marks. It is still too uniformly shaded, with a darker/rounder
front edge than the painting. The rear forearm/shoulder contour, face and boot
shapes still differ. At 64 px the buff/red costume, wide stance and long pike
read as the same unit; it is still distinguishable from the source token.

All five clip strips were inspected. Idle is subtle, move remains stiff, attack
is a short two-handed thrust, and hit recovers. Death releases the pike and holds
its last two frames, but its raised leg and fall remain too posed. Revealed cloth
and skin are simpler than the source-facing paint. The rig audit checks a
stationary base, finite transforms, nonzero scales, 53 bones and wrist/shaft
proximity; it is not a complete grip, cloth or floor collision solver.

Current delivery is explicitly **Cycles CPU12 / 256px preview**:

- Forty samples: idle 8, move 8, attack 10, hit 4, death 10.
- Trimmed 160px logical cells, **158,564 bytes at WebP quality 90**, lossless alpha.
- Decoded alpha/offsets, bounds, motion, source hashes and held-death source/RGB
  equality pass. Duplicate frames share a rectangle without dropping samples.
- Six fresh 256px AO/Pointiness bakes and saved editable master/clip blends.
- Round-2 MP4: H.264, yuv420p, 1600 × 348, 240 frames, eight seconds; all five
  decoded clips side by side on cream, at 2x logical frame size.
- Scene/rig checks, all 15 Python files, both shell scripts and whitespace checks pass.
- The GPU receipt correctly rejects this CPU delivery; the missing-input test
  records the failed preflight and leaves no success receipt.
- The actual GPU entry point reaches device discovery and correctly fails with
  `Metal GPU unavailable; no CPU fallback` in this sandbox. GPU rendering is
  unverified here. Device discovery uses a CPU slot; actual renders use the GPU gate.
- Repository hygiene and public-claims pass on the committed changes. Initial
  hygiene false positives on matrix operators were fixed with spacing. The art
  gate is blocked by Chromium `bootstrap_check_in ... Permission denied (1100)`
  in the sandbox; no distinctness result or browser art approval is claimed.

The runner reassigned lane-17 mid-round after WIP commit `57e4b781`. Continue on
`astra/unit-anim-3d-barbarian-pikeman` in `.worktrees/barbarian-pikeman-round2`, not
in the active artillery checkout. The single executable host handoff is:

```sh
ROUND=2 tools/art/anim3d/units/barbarian-pikeman/gpu.sh
```

It checks the actual Metal device, regenerates all clips, audits, renders every
stage at GPU64/512, retains 512px masters and 256px derivatives, packs/validates,
and writes the round MP4. Its retained log and failed-stage status distinguish
an interrupted run from a completed one. A fresh success receipt requires GPU
provenance, matching master hashes, every 512/256 frame and a probed movie.
Final GPU rendering and visual acceptance remain outstanding; CPU previews do
not manufacture 512px masters or establish GPU success.
