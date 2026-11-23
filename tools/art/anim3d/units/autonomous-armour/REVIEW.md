# Autonomous armour — round 1 candidate

The external master is `~/LegatumRuns/anim-pilot/masters/autonomous-armour/`.
`model.blend` retains the authored materials and geometry before baking/projection;
`plain.blend` is neutral-clay evidence; `finished.blend` has packed textures, real
AO/curvature bakes and rest-camera projection. `clips/` contains five independently
editable mechanical animation files. Inputs and sources are recorded externally
in `inputs.json` and `assets/SOURCES.md`; the generated fill prompt is committed.

The first plain, first projected and first move comparisons are retained in the master folder.
The latest required review sheets and clips use the `autonomous-armour-` prefix
in `~/LegatumRuns/anim-pilot/review/3d-v2/`. The log records each stage honestly.
CPU previews use Cycles, 256 px, eight samples, denoising. They are preview evidence,
not GPU approval or purported 512 px renders.

At 256 px the projection recovers much of the original brushwork and the turret,
sensors and gun are substantially aligned. The hull remains narrower than the
painting; front/side panel geometry and some projected seams do not yet match.
The base is warm cream but its lighting and contact shadow remain less convincing.
Reducing projected colour on the running gear avoids the most obvious moving
texture distortion, but exposes wheels that are too small/dark and a track profile
that needs closer modeling against the painting.
At 64 px it reads as the same compact olive tracked unmanned vehicle with twin
aerials, but its width and front mass are still weaker than the painting.
No PASS marker should be written for this round.

The five clips use independent turret/sensor idle, cycling track links and wheels
for move (two shoe pitches and a six-stud wheel period per loop), aim/recoil/flash/recovery for attack, a mechanical jolt for hit, and a
settled damaged turret/gun/sensor for death. Death holds its final two samples.
This first wreck motion is restrained; it needs review for stronger damage/readability.
The first move review exposed warped projected wheel details; running gear now
uses 28% painting colour and 20% painted-light emission, while the stationary
armour retains 94%/64%. This preserves physical wheel/tread forms in motion.
Projection is designed for this fixed camera, and is not suitable as-is for a
free-orbit viewer. The generated hidden-surface paint provides a fallback, not a
complete unseen-side painted asset.

Run the complete host pass from the repository root with no positional arguments:

```sh
ROUND=1 tools/art/anim3d/units/autonomous-armour/gpu.sh
```

This requests Cycles Metal GPU explicitly, renders all stages at 512 px, keeps the
512 and 256 masters, freezes one grade, creates review images and animated WebPs,
checks the saved rig, packs/validates the trimmed 160 px atlas, then makes the
8-second H.264/yuv420p five-clip MP4 by decoding that atlas. It fails if GPU is
unavailable, a render is stale, or quality >=75 cannot fit 200,000 bytes.
The current atlas is a candidate; no runtime loader has been changed.

The unit's `-validation.json`, `-audit.json`, `-pack.json` and
`-video-validation.json` under the external review folder are the exact technical
results. These are separate from the human art verdict. No game rules or Rust/UI
logic changed; only the art pipeline and candidate assets are in scope.

Final CPU check results: saved-scene audit PASS; all 40 frames and exact alpha/trim
reconstruction PASS; atlas 196,720 bytes at WebP quality 80; held death and loop
boundary checks PASS. MP4 verified: 240 frames, 8 seconds, 1600x348, H.264
yuv420p. All 16 required review images/animations/video exist. Python syntax
(8 files), Bash syntax (2 entry points), and git diff --check pass. GPU rendering
and the 512 px master set are pending the lead command above. Staging/commit
was blocked by sandbox denial of `.git/worktrees/lane-23/index.lock`; the runner
must commit the work. The current origin/master is already included in HEAD.
