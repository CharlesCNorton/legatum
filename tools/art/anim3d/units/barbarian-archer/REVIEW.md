# Barbarian archer, driver round 2

**Review candidate, not art-approved. No PASS marker.**

Opened the actual round-one GPU c/f sheets, all five strips and sampled decoded
MP4 frames before editing. The pass succeeded: GPU512/64, 40 frames, quality90,
192166 bytes and a verified eight-second movie. Those originals are preserved in
`masters/barbarian-archer/driver-r1-gpu/`, including the review images/movie.

The new pass replaces near-static authored walking and the rigid authored fall
with CC0 Quaternius Idle_Loop, Walk_Loop, Hit_Chest and Death01. Blender constraints
compensate reference/rest poses and bone roll; walk uses open idle carrying arms
and a lower carrying pose to keep the bow inside the fixed cell. No post-retarget
foot-angle correction. The attack remains authored. The fall is turned toward the
camera to fit the cell; the back pelt receives thick geometric contact folds.
These are shape keys, not cloth simulation. Actual evaluated final death meshes
are checked for a held pose, not only rig transforms.

Toe geometry/UV calibration reduces cream-base spill, quiver curves are converted
to meshes for frozen projection, fletchings have ivory pigment on both sides,
and the physical stone has a tighter bevel, warmer pigment and stronger product
key/fill. Eight actual AO/curvature maps and original generated unseen-surface
fills remain; the automatically sampled rest grade is fixed across the clips.

At 256 px, the rest is still distinguishable from the painting: bow hand/fingers,
left boot shape, coarse pelt boundary, upper-arm width and sparse quiver differ.
Stone is warmer but lacks the painting's fine authored surface. At 64 px it reads
as the same wolf-pelt archer, with visible silhouette differences. The walk now
clearly steps; the fall no longer leaves an upright pelt, but exposes simpler fills
and a stiff front mantle. It is not five art-approved clips. Root stance correction
uses a virtual in-place ground speed; the foot sheet is not a full no-slip solver.

## Verification and handoff

Current CPU previews use Cycles256/8 with denoising. All c/d/e sheets, details,
rest split/crossfade, front/top eight-frame feet review and animated WebPs are
published under `review/3d-v2/`. The complete delivery results are appended below.
Current GPU512/64 renders remain pending; preserved round-one renders are not
claimed as the new geometry's output.

From the repository root, run the executable without arguments:

```sh
ROUND=2 tools/art/anim3d/units/barbarian-archer/gpu.sh
```

This probes Metal, rebuilds all clips from the saved finished master, audits them,
renders every stage and all40 frames at512/64, renders the new front/top feet
check, exports current512/256 masters, packs/validates trimmed160, and encodes
`barbarian-archer-round${ROUND}.mp4` from the decoded atlas (H.264/yuv420p,
1600x348,240 frames,eight seconds,2x on cream). Failure stage/status and logs remain
external. Technical success never creates an art PASS marker.

Source URLs/licences/hashes are in unit `SOURCES.md`, `inputs.json`, the checked
retarget inputs and external `assets/SOURCES.md`. No new downloads, image service,
accounts or paid services. No Rust, runtime/UI, gameplay, deployment or PR changes.

Non-obvious findings: straightening the gait raises the bow out of a camera fitted
only to the braced rest; calibrate the carrying pose too. Camera-projected meshes
need material masks at toes so the painting's plinth does not become boot pigment.
Quiver curves need mesh conversion to participate in the frozen projection. A held
skeletal death can still have moving shape-key cloth; check evaluated geometry.

Final CPU delivery: **186,236 bytes, quality 85**,40 frames with160px
trimmed cells. Atlas/source/grade/decoded-alpha validation and all four delivery
tests pass. Scene audit covers40 weapon/base/scale samples and actual evaluated
terminal death geometry. Eight bakes pass. The decoded round2 MP4 passes
H.264/yuv420p,1600x348,240 frames,eight seconds. All Python and Bash syntax checks
and `git diff --check` pass. No Rust/app code changed, so no unrelated build ran.

Commit attempt was blocked by sandbox index.lock permission; changes remain
uncommitted for the runner. HEAD includes origin/master (zero incoming commits).
No push or PR. Final decoded movie contact frames and corrected foot cutaway were
visually inspected. No PASS marker.
