# Peltast — round 1 candidate

The source painting remains the art bar. This is true 3D built from MPFB anatomy,
not a layered image or billboard: the side-view plain review shows body depth,
full clothing, shield dish, cap, boots and equipment. Editable masters are in
`~/LegatumRuns/anim-pilot/masters/peltast/`. The original painting is unchanged;
the atlas is a candidate and has not been wired into the game.

The first plain and textured sheets are retained with `-first` suffixes. Current
b/c/d/e reviews, 256/64 comparisons, detail crops and the rest-pose 50% crossfade
are in `~/LegatumRuns/anim-pilot/review/3d-v2/peltast-*`. The running log records
interim corrections and distinguishes CPU previews from GPU output.

At 64 px the cap, overhead javelin, blue cloak, red chiton and crescent shield read
as the original unit. At 256 px it is still below the painting: the face and fox
hide are softer and less natural, the torso is narrow, cloak folds are too regular,
and some boot laces stand away from the leather. The rest silhouettes are close
but not indistinguishable. No PASS marker is warranted.

The animation is authored on the 53-bone MPFB rig, with 8/8/10/4/10 samples.
Move is a stepping guard, not captured walking. The throw hides its released
javelin before it exits the cell and returns to a rearmed guard. A later round
should improve the spare-to-hand rearm and follow-through. Cloth uses a weighted
mesh and an authored flutter shape key, not a physics simulation. The terminal
death is held. Technical validation does not establish collision-free animation
or art approval.

The no-argument host GPU handoff is:

```sh
tools/art/anim3d/units/peltast/gpu.sh
```

Run from this repository root. It explicitly selects Cycles Metal GPU with
48 samples/denoising, rerenders all stages and clips, writes 512/256 masters,
creates the trimmed 160 px atlas and metadata, runs validation and audit, then
writes the eight-second `peltast-round${ROUND:-1}.mp4`. It fails without Metal;
this sandbox cannot verify that GPU execution path. `PLAYBOOK.md` documents
rebuilding, source licences, grade behaviour, atlas offsets and anchor semantics.

Git staging/commit and merging the available `origin/master` both hit sandbox
lock-file denials (`index.lock` / `ORIG_HEAD.lock`). Leave the changes for the
runner; do not claim a commit or merge. No push, PR or hosted publication occurred.

Final local checks (CPU Cycles, 512 px / 8 samples):

- All 40 transparent clip frames exist at 512 and 256 px, with every required
  review stage and animated WebP. The final two death outputs explicitly sample
  the same settled frame, avoiding render noise in the hold.
- Atlas: **170,184 bytes**, 1409×731 encoded pixels, 160×160 logical cells,
  WebP RGB quality **75**, 32 alpha levels, maximum measured/allowed alpha error
  **4/255**. Full-alpha masters are retained. Before alpha quantization, quality
  75 was 255,286 bytes; 64 alpha levels were 213,264 bytes. No frames removed.
- `validate.py`: PASS — frame counts, source/grade binding, trim reconstruction,
  alpha error bound, clipping margins, motion, terminal hold, master presence,
  nonoverlapping rectangles and review presence.
- `audit.py`: PASS — 53-bone real anatomy, thick 3D kit, finite/nonzero transforms,
  stationary base, terminal skeletal hold, and idle/move loop matrix error **0.0**.
- Python AST parsing: **13 scripts passed**; `bash -n`: both shell scripts passed;
  `git diff --check`: passed.
- `ffprobe`: H.264, yuv420p, 1600×348, 30 fps, **240 frames / 8.000 seconds**.
  The decoded shipped-size comparison and an extracted video frame were visually
  inspected. The video and delivery are round-1 candidates, not art approval.
- GPU execution and post-merge repository gates remain for the lead/runner:
  Metal is unavailable here, and Git lock denial prevented committing/merging
  the available newer `origin/master`. No Rust/UI/runtime changes were made.

Additional rig finding: a garment with an Armature modifier still needs to
inherit the rig object's transform for a whole-body fall. The animator now
parents unparented skinned garments before keying the root. Omitting that step
left the tunic upright while the anatomy fell, a defect caught by the death strip
and corrected before delivery.
