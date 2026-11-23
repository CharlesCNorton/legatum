# Barbarian crossbowman — round 2

Review candidate only; no art PASS and no runtime activation.

The rest pose is closer to the painting at 256 px: the hands and elbows are
registered more naturally, the boots have more volume, the vertical stock and
bowstring better match the source, and the face/cloth retain much more painted
detail. The stone is warm cream. At 64 px the same hooded crossbowman identity
reads, but the silhouette is still distinguishable. Alpha-mask IoU increased
from **0.7300 to 0.8099** (threshold 128); that is not a visual-quality pass.
The hood contour, sleeve tailoring, foot shapes and bolt case remain simpler
than the source. The plain side views expose the unfinished garment construction.

All five actions were rebuilt and inspected as strips, plus contact frames from
the decoded atlas MP4. Attack now starts at the saved rest arm pose and keeps
its stock grip through recoil. The walk is still restrained and stiff. Death
moves the hanging bolt case aside and settles against the actual support
footprint, but the rigid cape/clothing and leg pose still look partly suspended.
It needs a more natural collapse and cloth contact before approval. No cloth
simulation or full body/garment collision guarantee is claimed.

The model retains native MPFB anatomy, weights and 53 bones. Macro shape keys
are frozen before fitting; thick/beveled/subdivided kit surfaces are finished
before recording camera UVs. Ray visibility, facing, source alpha and hand
exclusions blend into the existing image-generated linen/physical unseen fills.
Camera-only painted pigment avoids lighting the source a second time; other
rays retain physical materials. Stone never receives projected feet/shadows.
Real AO/curvature bakes and one frozen automatic rest histogram grade remain.

Verified CPU delivery:

- All 40 frames: idle 8, move 8, attack 10, hit 4, death 10; Cycles CPU8, native
  256 px. Earlier evidence is in `round1-cpu`, current evidence in `round2-cpu`.
- Trimmed 160 px atlas: **138,532 bytes, WebP Q90**, full alpha, per-frame offsets.
  Source/model/frame/grade/atlas/JSON hashes, exact decoded alpha reconstruction,
  bounds, motion, and pixel-identical decoded death hold pass.
- All five source audits pass: 53 bones, stationary stone, safe nonzero scales,
  finished projection and camera-only pigment. Maximum right-wrist/stock error:
  idle **0.298 mm**, move **0.000373 mm**, attack **0.000362 mm** (2 mm limit).
- Two delivery regression tests pass; 12 Python files compile, both shell files
  pass `bash -n`, and whitespace checks pass.
- MP4 probe: **H.264/yuv420p, 1600x348, 240 frames, 8.000 seconds**. Every clip
  is reconstructed from trimmed atlas rectangles at 2x on cream.
- The independent final-master gate rejects the actual CPU preview manifests.
  Running the executable GPU handoff's preflight in this sandbox fails explicitly
  with `Metal GPU required; refusing CPU fallback`, exit 1, and records the
  failed stage in its status file. A queued earlier preflight was interrupted;
  device discovery now uses a CPU slot because it does not render.

GPU64/512 final masters and their 256 derivatives remain pending. From this
checkout's repository root, the lead runs the complete no-argument handoff:

```sh
ROUND=2 tools/art/anim3d/units/barbarian-crossbowman/gpu.sh
```

It checks Metal, rebuilds/bakes/animates/audits, renders every b/c/d/e stage,
checks final-master provenance, packs/validates and writes the eight-second
round MP4. It retains its transcript and stage/status receipt. Technical success
never creates PASS. Masters, bakes, raw frames and reviews stay under
`~/LegatumRuns/anim-pilot/`; no new downloads, services or uploads were used.

Git staging was blocked by the sandbox denying
`.git/worktrees/lane-13/index.lock`; the runner must commit the round. No push or
PR was attempted. `origin/master` is already an ancestor of HEAD. Pre-existing
Tagmatic files and its uncommitted playbook chapter were preserved. Commit-based
repository gates remain deferred; the unit-local checks above cover this round.
