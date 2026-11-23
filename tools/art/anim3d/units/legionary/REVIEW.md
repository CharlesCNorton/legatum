# Legionary driver round 2

Improved candidate; **not art-approved, no PASS marker**. The existing painting
remains in the game. No runtime rendering or game mechanics changed.

The lead's round-1 GPU pass succeeded through atlas/video validation. Its actual
rest, details, five strips and movie frames were inspected before edits, and its
masters/reviews are retained in external `masters/legionary/driver-r1-gpu/`.

At **256 px**, the narrower rounded scutum and smaller cream base better match the
painting. The pilum wrist/thumb and shaft visibility improved. Multiplying the
skin mask by source alpha removes projected black background; a pinned original
generated skin fill covers newly exposed areas. Sleeves now use evaluated anatomy
weights, and fitted sandal leather follows the calf, foot and toe bones. Painted
armour and shield remain rich, but face/helmet contour, shoulder fit, hand shape
and newly revealed surfaces remain distinguishable. At **64 px**, this reads as
the same Roman unit, with a still-different stance and outline. No parity claim.

Silhouette IoU increased from the GPU baseline **0.7449 to 0.7908 at 256**, and
**0.7588 to 0.8017 at 64** in the latest CPU preview. Foreground colour error is
similar; these metrics are supplementary evidence, not acceptance thresholds.
The camera is calibrated approximately, not claimed to be an exact reconstruction.

Idle, walk, hit and death now use pinned **CC0 Quaternius** actions retargeted with
reference/rest and bone-roll compensation. The walking carrying arms use the
open idle; the shield attack, equipment release and tunic follow-through remain
explicit original adaptations. Source-designated stance gets a small root
translation correction. There is no post-retarget foot rotation patch. The death
no longer uses the original rigid authored fold, but source-painted skin and
released-equipment contact still need close GPU review. This is not a general
cloth/skin/sole collision solver.

Verified Cycles CPU / 8-sample delivery:

- All 40 clip samples plus 24 diagnostic/foot views at native 512 px, with 256 px
  gallery copies and current model/clip/grade/raw-image hashes.
- Geometry audit: 40 samples pass, no failures or warnings; terminal body minimum
  0.10674 m above scene origin over the 0.085 m stone.
- Stance audit: maximum heading 0.02051 degrees; ankle XY residual 0.00000052 m
  against implied travel; maximum root correction 0.01814 m.
- Trimmed 160 px atlas: **180,914 bytes, WebP Q80, 1046 x 754**; all 8/8/10/4/10
  samples retained. Reconstruction, alpha, source margins, hashes and death hold pass.
- MP4: **1600 x 348, H.264/yuv420p, 240 frames, eight seconds**, ffprobe verified.
- Python syntax (15 scripts), Bash syntax (2 scripts), executable handoff and
  `git diff --check` pass.

The full CPU check results are recorded in the external `legionary-log.md`,
`legionary-audit.json`, `legionary-feet-audit.json`, `legionary-validation.json`,
`legionary-video-validation.json` and `legionary-comparison.json`.
The foot sheet shows all eight move samples from the front and top.

External editable masters, raw/graded 512 px frames and 256 px copies are under
`~/LegatumRuns/anim-pilot/masters/legionary/`. Interim comparisons, details,
strips, animated WebPs, decoded atlas and movie are under `review/3d-v2/`.
Provenance and the repeatable pipeline are in `SOURCES.md` and the legionary
chapter of `../../PLAYBOOK.md`.

The lead runs from this branch's repository root:

```sh
ROUND=2 tools/art/anim3d/units/legionary/gpu.sh
```

This executable needs no arguments. It regenerates clips, renders every stage
and the foot review on Cycles GPU at native 512 px, retains 512/256 px
masters, checks geometry and provenance, packs/validates all 40 trimmed 160 px samples
at quality >=75 and <=200,000 bytes, and writes the eight-second H.264/yuv420p
`legionary-round${ROUND}.mp4`. It fails on missing Metal or stale/CPU provenance,
records status/transcript, and never writes a PASS marker automatically.

Working-file hygiene passed across all 18 changed/new text files; the GPU-only
provenance check correctly rejects CPU masters. `origin/master` is already
contained. The working-tree art distinctness render was blocked by Chromium's
macOS MachPortRendezvous permission error (1100); no browser/art approval is
claimed. Git staging/commit was blocked by the sandbox's denial of
`.git/worktrees/lane-5/index.lock`. Changes remain uncommitted for the runner;
the required co-author commit message is retained externally in
`tmp/legionary/commit.txt`. Nothing was pushed and no PR was created.
