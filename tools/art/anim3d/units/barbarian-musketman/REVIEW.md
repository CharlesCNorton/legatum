# Driver round 3 — CPU candidate; no visual PASS

The complete round2 GPU pass succeeded: 178,740 bytes at Q80, all 40 frames and the GPU receipt.
The isolated frame workers fixed the earlier interrupted pass. Incoming evidence, including actual
MP4 frame extraction, is preserved under external `masters/barbarian-musketman/driver-r2-gpu/`.

Round3 replaces inappropriate horse-fur garment fills with generated buff leather, ivory linen,
flesh and charcoal plates. Exact prompts and source hashes are beside these scripts. The real
stone disc receives a generated clean top with the original lower rim and live contact AO; no
image alpha clips geometry. The feather now has a hooked cambered vane, thickness, quill and barbs.
Finished sleeves share spine/upper-arm/elbow weights while retaining the exact rest fit. Anatomical
underlayers use garment materials under clothing, and projected pigment fades toward generated
fills as surfaces rotate. Existing camera projection, bevels, straps, folds, product lighting,
AO/curvature maps and fixed automatic histogram grade remain.

A final actual-vertex check found the enlarged feather penetrating the disc during death. Its
flexible geometry now bends onto the stone through the cloth contact keys, and the audit checks
all death frames for feather penetration. This does not establish general collision freedom.

At 256 px the rest view is close in pigment and silhouette, with a better stone and feather, but the
feather remains too tidy and the hat/face edge differs. At 64 px it reads as the same kneeling unit;
the feather/base still differ. Death has substantially less scrambled paint, but exposed sleeves,
coat and anatomy look less authored than the painting and the raised-arm transition is awkward.
Move is a restrained kneeling shuffle; smoke remains smaller than the source. **No PASS marker.**

Verified final delivery: Cycles CPU 512 px / 4 samples, 62 genuine 512 PNGs and 62 matching 256 exports; all 40 clip
frames (8/8/10/4/10); trimmed 160 px atlas **183,660 bytes at Q80**. Movie: H.264/yuv420p, 1600x348,
240 frames, 8.000s. Opened rest/details, all five strips, front/top feet, decoded atlas and actual
encoded movie frames. These low-sample CPU previews are not round3 GPU approval.

Checks passed: six delivery regressions and three interrupted-frame/recovery regressions; source,
master/clip/frame/metadata/grade hashes; exact alpha and trim reconstruction; margins; motion and
held death; 53-bone rig, positive scales, fixed base, arm/leg lengths, planted support, grip error
<=0.00000024m, evaluated feather contact. All 168 finished projected surfaces have zero sampled
rest-UV error. Nine Python files parse; Bash syntax and git whitespace checks pass. An auxiliary
image-dimension check initially used system Python without Pillow; rerun in the pipeline venv
passed both 62-image sets. No Rust, rules, AI or app runtime code changed.

From this checkout, the lead runs the executable no-argument handoff:

```sh
ROUND=3 tools/art/anim3d/units/barbarian-musketman/gpu.sh
```

It preflights Metal, verifies source pins, rebuilds/bakes, renders every stage at GPU512/48 or
higher using fresh gated processes, keeps 512/256 masters, packs/validates, runs nine regressions,
and writes the round movie, extracted contact sheet and GPU receipt. No CPU fallback or automatic
PASS. origin/master has zero commits ahead of this branch. No push, PR, merge or upload.

Commit attempted with the requested co-author trailer; sandbox denied creation of the worktree
index.lock. Changes remain uncommitted for the runner. No permission escalation was requested.
