# Round 1 review — CPU candidate, not PASS

All nine review stages and all forty clip frames were rendered natively at
512px in Cycles CPU, eight samples with denoising. Every stage retains original
raw frames and a 256px derivative set. Plain/model, textured/light, details,
rig poses, all five strips/WebPs, rest comparison, top/front motion check,
decoded-atlas sheet and the round-1 movie exist in the external review folder.

Final candidate: **163,388 bytes**, WebP **Q90**, 1529x621 atlas, 160px logical
cells with per-frame trim offsets. Counts are **8/8/10/4/10**. The last death
samples share a rectangle, so decoded RGBA is exactly identical.

Checks completed:

- Five delivery regression tests passed.
- Eight Python files parsed; both shell entry points passed `bash -n`.
- Geometry audit passed for all clips: 23 mesh objects, manifold principal
  aircraft meshes, real volume, finished camera UVs, local control pivots,
  stationary stone, idle/move loop closure and physical wreck contact.
- Atlas validation passed source/grade/frame hashes, every reconstructed alpha,
  offsets, transparent gutters, frame margins, motion and decoded death hold.
- All nine current raw manifests and both native-512/derived-256 sets verified.
- Movie verified as H.264, yuv420p, 1600x348, 240 frames, exactly 8 seconds;
  representative decoded frames visually inspected with the clip strips.
- `git diff --check` passed. No Rust, rules or app runtime was changed.

Rest alpha IoU versus painting is **0.972768**, opaque-overlap RGB MAE **5.69469**.
These are correspondence measurements, not art acceptance. At 64px this reads
as the same unit. At 256px the painting still has sharper canopy/panel craft
and richer limestone. Off-axis geometry exposes coarse engine/fuselage joins;
projected lighting follows the surfaces. Attack is understated and the crash
needs more convincing impact. No PASS marker is written.

Host GPU execution remains unverified in the sandbox. Run from repo root:

```sh
ROUND=1 tools/art/anim3d/units/stealth-fighter/gpu.sh
```

The entry point performs every GPU render, master export, review, pack, audit,
validation and movie step, then writes a GPU receipt. CPU output cannot satisfy
its GPU provenance check. The driver can start round 2 after that review.

Non-obvious fixes: force a dependency update before reading a newly placed
pivot's matrix during parenting; otherwise the hinge silently remains at the
origin. Reuse identical atlas rectangles for held frames; separate lossy WebP
blocks can change RGB even when their input PNGs are identical. Repeated crops
must use straight-alpha paste, not cumulative alpha compositing.

Git staging was attempted but the sandbox denied creating
`.git/worktrees/lane-19/index.lock`. Changes remain uncommitted for the runner.
Suggested commit title: `Add round-one 3D stealth fighter animation candidate`.
Required trailer:

```text
Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>
```
