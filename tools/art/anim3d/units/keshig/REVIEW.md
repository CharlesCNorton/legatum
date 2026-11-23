# Round 1: candidate, not approved

Built an editable MPFB rider and native CC0 Quaternius horse rig, original Mongol
archery kit, frozen camera projection, generated unseen-surface fills and actual
helmet AO/Pointiness bakes. All five clips, staged PNG/WebP reviews, split-screen
comparison and top/front move-cycle views exist outside git under
`~/LegatumRuns/anim-pilot/review/3d-v2/keshig-*`.

CPU evidence: 512 px, eight Cycles samples with denoising. There are 46 actual
512 masters and 46 corresponding 256 images (plain, rest, four rig poses and
40 clip frames), plus editable master and five clip blends in `masters/keshig/`.
These are not GPU approvals.

Checks passed: geometry/source-hash audit; all 40 frame rectangles, margins and
transparent gutters; source locks; lossless alpha reconstruction; exact decoded
held death; nonzero motion; 160 logical cells; atlas **186,820 bytes at Q80**;
H.264 yuv420p movie **1600x348, 240 frames, 8.000 seconds**. Python syntax,
Bash syntax and diff whitespace checks passed. Repository baseline HEAD hygiene/public-claims
checks passed; the art gate's `render-sets.mjs` subprocess failed, producing no
distinctness verdict. No Rust or UI code changed. Git staging was denied when creating
`.git/worktrees/lane-12/index.lock`; changes remain uncommitted for the runner.

At 256 px the coat/saddle retain painted detail, but the horse is too slim and
stylized, the head/neck and leg proportions differ, the cap is too pointed, the
bow is angular, the tail is too simple, and projection seams/unpainted areas
remain obvious. At 64 px this reads as a mounted archer, but lacks the painting's
broad galloping silhouette. The attack needs clearer draw/release timing and the
death needs closer equipment/collision review. Foot direction uses the original
horse rig; ground-height checks are not a claim of zero sliding.

A rest-fitting experiment was rejected because it stretched the hocks during
native gallop. Its images remain in `masters/keshig/rejected-rest-fit/`. Future
shape work should fit anatomy and rest bones together, then revalidate the whole
source motion before projection. Do not revive the rejected screen-space leg
sculpt simply because its rest silhouette is closer.

GPU handoff, from this checkout's root:

```sh
ROUND=1 tools/art/anim3d/units/keshig/gpu.sh
```

The script validates Metal, makes fresh clips, renders all stages, retains
512/256 masters, packs and independently validates the atlas and MP4. It does
not write PASS. Keep `keshig-PASS` absent: round one does not meet painting parity.
