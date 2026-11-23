# Horseman — driver round 3, 23 November 2026

**Not art-approved; no PASS marker.** At 256 px the rest is still clearly different
from the painting; at 64 px it reads as the same class but is thinner and stiffer.

The lead's round-2 GPU pass succeeded: forty frames, 175,668 bytes at Q85, actual
512/256 masters and a verified eight-second movie. That evidence is preserved in
`masters/horseman/driver-r2-gpu`, including freshly decoded MP4 frames.

## What changed

The bent rear cannon was partly a rig bug. Sparse glTF Idle channels retained
Walk's IK translations while changing the leg rotations. All source action
switches now reset bone bases first. The Blender regression reproduces the old
contamination and verifies clean Idle after four different preceding actions.

Full-depth limb/poll fitting, a bridle fitted to the actual muzzle, trailing solid
crest fibres and varied generated-hair pigment improve geometry and surfaces.
Frozen camera UVs follow geometry finishing; the broader horse ownership mask
preserves white socks. Existing image-generated unseen-surface fills, bevels,
cloth folds, physical lighting and the shared automatic histogram grade remain.
No painting cards or per-frame image warps are used.

The new top/front feet review exposed front hooves hovering throughout the old
walk despite its one-hoof support test. Positional retargeting now transfers
actual original Quaternius sole trajectories with constant horizontal rest
corrections and original stance/swing heights. Translations taper into upper
limbs; source foot rotations remain unchanged. The original horse action supplies
motion; the seated rider response and weapon attack remain authored, not mocap.

## Verified CPU delivery

- Cycles CPU12 for nine review stages and all forty frames; actual 512 px detail,
  256 px stage/clip images, editable blends and textures retained outside git.
- Trimmed 160 px atlas: **178,850 bytes at quality 85**, 1091 × 758; all five
  clips retain 8/8/10/4/10 frames and per-frame offsets. Q90 was 208,154 bytes.
- Atlas validator: **zero findings**, including reconstructed alpha, source
  hashes, frame bounds, motion and held terminal death. Alpha uses 32 levels,
  maximum 4/255 source error; RGB is not posterized.
- Geometry audit: **five clips, zero errors**. All 32 walk sole heights match
  source targets within 15 mm; every foot supports weight during the cycle.
- Idle and move close exactly at the unsampled ninth-frame endpoint. Maximum
  sole-position transfer error is **0.000000302 m**, foot-rotation error **0 rad**.
- Sixteen actual lower-limb diagnostic renders show top/front views on a 25 cm
  grid, with four distinct limb colours and support labels.
- MP4 decoded and inspected: **240 frames, eight seconds, 1600 × 348, H.264
  yuv420p**. All five clips reconstruct the trimmed atlas on cream at 2x.
- Four master-gate tests pass; sparse-action regression passes four transitions.
  Python syntax, shell syntax and whitespace checks pass.

Silhouette IoU is .7753 at 256 and .7808 at 64, up from the prior CPU .7378/.7445.
These are geometric measurements, not art approval. Review strips, native
painting/render/split/crossfade and decoded atlas/movie images were inspected.

## Remaining gaps

The horse still lacks the painting's muscular chest, refined hocks and flowing
hair; the rider's face, crest, posture, skirt and far leg remain mismatched.
The tail is a coarse dark bundle, and projected anatomical shading does not
always follow the moving geometry naturally. Falling rider/tack intersections
still need work. The corrected feet improve motion but do not establish five
artistically clean clips or exhaustive freedom from sliding/collisions.

Current evidence is a **CPU preview**, not a new GPU pass. The earlier GPU512
masters remain historical until the lead runs, from this checkout:

```sh
ROUND=3 tools/art/anim3d/units/horseman/gpu.sh
```

That executable rebuilds paint/animation, runs geometry/action/loop checks,
produces all nine Cycles Metal GPU512 stages and 512/256 masters, renders the
feet review, packs/validates, and encodes/verifies the movie. Current hashes guard
the completion receipt. No script writes PASS; the game keeps its painting.

Non-obvious lessons: reset sparse actions before sampling; validate every foot's
support sequence, not just one grounded hoof; use clay to reject corrective
sculpture that merely hides a rig bug; preserve source rotations during contact
retargeting. No changes to game rules, Rust or UI were made.

Commit handoff: this sandbox denied `.git/worktrees/lane-13/index.lock`, so the
changes remain uncommitted for the runner. The exact message and requested
co-author footer are saved in the external `horseman-commit-message.txt`.
