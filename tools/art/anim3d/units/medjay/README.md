# Medjay, round 1

True 3D MPFB anatomy (19,158 source vertices, 53 bones), original linen kilt,
convex hide shield, bronze spear and feather. Fixed-camera painting UVs ride the
actual meshes; unseen surfaces blend into generated skin/linen/hide/wood fills.
Six actual AO/curvature bake pairs are retained outside git. The kilt is modeled
with folds and thickness; covered body faces use a nondestructive mask. No
billboard, relief-plane character, downloaded commercial model or mocap claim.

From the repository root:

```sh
tools/art/anim3d/units/medjay/render.sh build
tools/art/anim3d/units/medjay/render.sh finish
tools/art/anim3d/units/medjay/render.sh animate
ROUND=1 tools/art/anim3d/units/medjay/gpu.sh
```

`gpu.sh` is the no-argument host handoff. It selects Cycles Metal, serially renders
every stage and all 40 frames at 512 px, retains 512/256 masters, grades from the
rest reference, emits all review sheets/animated WebPs and the split-screen,
packs the trimmed 160 px atlas, validates it, audits the saved rig and encodes
the eight-second five-clip H.264 video. It fails if no Metal device is available;
there is no silent CPU fallback. CPU previews use `render.sh <stage>` with
`RESOLUTION=256 SAMPLES=8` (or 512 px for retained preview masters).

External root: `~/LegatumRuns/anim-pilot`. Sources: `assets/medjay`; editable
master and five actions, packed textures and bake maps: `masters/medjay`;
review sheets, strips, WebPs, log and round video: `review/3d-v2/medjay-*`.
`assets.lock.json` pins the original master and generated fill. The central art
provenance table and external `assets/SOURCES.md` record licences.

The candidate atlas is `app/src/assets/units/anim/medjay.{webp,json}`. Version 2
metadata has logical `frame:{w:160,h:160,ax:84,ay:141}` and clip `rects` containing
`{x,y,w,h,ox,oy}`. Crop the atlas rectangle and paste at `(ox,oy)` before applying
the anchor. `row` is an ordering index; rows have variable pixel heights. No
runtime integration is included. Quality never falls below 75; packing refuses
more than 200,000 WebP bytes, clipped cells or stale renders.

Round-one visual verdict: recognizable as Medjay at 64 px; still below the
painting at 256 px. The head/headband and feather registration, facial shape,
upper-body proportions and more convincing attack/death timing need another
round. The stationary base is warm cream, the shield retains the painted hide
pattern, and the corrected kilt reads as ivory cloth. No PASS marker is written.
CPU low-sample frames are previews, not GPU sign-off. Full skin/cloth/equipment
collision freedom is not established by the structural audit.

Implementation lessons: inspect outward normals before diagnosing projection
masks; visible anatomy under close-fitting clothes can masquerade as a texture
error; use evaluated mesh vertices for landing clearance rather than rotated
object bounding boxes. Do not edit a shell entry point while a live shell is
reading it; an earlier local wrapper invocation hit a transient parse error
when its file changed during execution, while the saved script passed `bash -n`.

Recorded round-one CPU checks: all 40 frames retained at both 512 and 256 px;
trimmed 160 px atlas **168,184 bytes at WebP quality 90**; atlas bounds, transparency,
clip lengths, motion, held death and source/grade hashes passed. Python compilation,
Bash syntax and `git diff --check` passed. The structural Blender audit passed.
Final death holds deliberately reuse the settled rendered image: independent
Cycles renders of the identical pose differed by one channel level in a few
pixels, which correctly failed strict byte-identity validation before this fix.
The repository gate on the existing HEAD passed hygiene/public-claims but its
browser art renderer failed; it did not validate this uncommitted worktree.
Metal rendering and the lead's art sign-off remain outstanding.
