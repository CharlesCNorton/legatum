# Autonomous armour — driver round 3 candidate

**No art PASS.** The round-2 GPU pass succeeded and is preserved in
`masters/autonomous-armour/driver-round2-gpu/`. Current evidence is a complete
Cycles CPU8/256 pass; new GPU512/256 output remains the host handoff.

The closed belt now wraps raised end sprockets and grounded road wheels, with two
beveled pads per link. One shared path controls all construction and animation.
Full-depth front armour registration brings the headlights closer to the painting.
Generated wheel pigment follows the solid wheel geometry; twelve-angle averaging
removes directional shading and makes its detail periodic at the move seam.
Tread-only painting masks restore source wear without copying wheel hubs or stone.
The existing generated olive fill, actual AO/curvature bakes, product lights and
frozen histogram grade remain. Source originals are checked against immutable pins.

At **256 px**, the tread silhouette and front armour are closer, but the road
wheels still have overly uniform size and flatter dishes than the painting, and
some fender edges and masked stone shading remain distinguishable. The CPU antenna
edges are noisy. At **64 px**, the same unit reads clearly with the right twin-aerial
identity, but the running gear still differs. The orthographic camera is a close
upper-body fit, not an exact solution to the painting's stylized perspective.

Inspected the rest/crossfade at both sizes, detail crops, every clip strip, exposed
running-gear top/front views and decoded movie frames. No obvious frame-edge clipping,
base movement or terminal-death jump; motion is restrained. The tread pigment is
not exactly periodic, so fresh GPU move/seam inspection remains necessary. These
checks are not a complete interpenetration solver or art approval.

Final CPU checks:

- Forty transparent 256 px clip samples, counts **8/8/10/4/10**.
- Trimmed160 atlas **197,852 bytes, WebP quality 90**; exact decoded alpha,
  offsets, bounds, source/scene/render hashes and all five moving clips pass.
- Idle/move seam ratios **0.997025 / 1.060665**; terminal death is pixel-identical.
- Saved-scene audit passes 128 links, 16 wheel/sprocket controls, six separated
  road tyres per side, rolling distances/direction, closed track loop, safe scales,
  stationary base and frozen source UVs. Contact z **0.236888–0.240000 m** against
  the 0.24m stone top; maximum contact radius **2.342375m < 2.36m** stone radius.
- Movie: **1600x348, 240 frames, 8 seconds, H.264/yuv420p**, all clips side by side
  at 2x on cream, reconstructed from trimmed atlas rectangles.
- Eight Python AST parses, two Bash syntax checks, executable GPU script and diff
  whitespace pass. Missing scenes fail the default-round3 preflight with status/no
  receipt; stale generator and CPU-as-GPU evidence are independently rejected.

Comparison measurements: silhouette IoU **0.938916 -> 0.948480**, opaque RGB MAE
**15.0481 -> 13.3438**, running-gear MAE **19.6063 -> 16.3347**. These compare old
GPU96/512-downsampled output with new CPU8/256, not identical render conditions.

From this checkout, run the complete no-argument GPU handoff:

```sh
ROUND=3 tools/art/anim3d/units/autonomous-armour/gpu.sh
```

It makes every review stage, fresh 512/256 masters, the trimmed atlas/JSON,
validation, round3 MP4 and independently checked GPU receipt. No script writes
PASS. Existing top-level 512 files are from round 2 until this handoff replaces
them; CPU manifests never count them as current evidence. The painting remains
the game's art; this candidate does not change the runtime loader.

New built-in-generated asset:
`~/LegatumRuns/anim-pilot/assets/autonomous-armour/wheel-fill-source.png`;
exact prompt `wheel-fill.prompt.txt`, provenance `SOURCES.md`, hashes
`assets.lock.json`. Original images stay external and are never committed.

Commit is pending the runner: sandbox denied creation of
`.git/worktrees/lane-17/index.lock`. No push or PR was attempted; `origin/master`
is already an ancestor of this branch.
