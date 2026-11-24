# Spearman round 10b — shoulder/back coverage

Files changed in this lane (relative to the round-9 candidate):
- `tools/art/anim3d/PLAYBOOK.md`
- `tools/art/anim3d/project.py`
- `tools/art/anim3d/units/spearman/SOURCES.md`
- `tools/art/anim3d/units/spearman/check_scene.py`
- `tools/art/anim3d/units/spearman/coverage.py`
- `tools/art/anim3d/units/spearman/coverage_preview.py`
- `tools/art/anim3d/units/spearman/coverage_review.py`

Round-9 baseline files also brought into this worktree because Git could not create ORIG_HEAD.lock:
- `app/src/assets/units/anim/spearman.json`
- `app/src/assets/units/anim/spearman.webp`
- `tools/art/anim3d/animate.py`
- `tools/art/anim3d/infantry/retarget.py`
- `tools/art/anim3d/units/spearman/gpu.sh`
- `tools/art/anim3d/units/spearman/compare_motion.py`
- `tools/art/anim3d/units/spearman/motion.py`
- `tools/art/anim3d/units/spearman/silhouette.py`
- `tools/art/anim3d/units/spearman/silhouette_review.py`

External shared append-only records: `assets/SOURCES.md`, `review/3d-v2/spearman-log.md`. Every lane artifact and review output is enumerated in `spearman-r10b-files.json`.

## Verdict

**Retain as a focused surface improvement; not PASS.** The broad pale shoulder/back patch reads more coherently as a cinnabar rear shoulder facing, warm linen and painted skin in hit and death. The silhouette, retargeting, cloth settings, camera, lights, base and armour finish are unchanged. At 256 and 160 px the shoulder facing and darker cloak folds are useful; the sleeve shell still has an angular, oversized contour and the overall painting is richer. At 64 px it remains recognizably the same unit; the surface gain is subtle, and the narrower lower-body stance and stylized fall remain. No new microtexture.

## Evidence

- `spearman-r10b-rest-compare.png`, `spearman-r10b-hit-{0,1,2,3}-compare.png`, `spearman-r10b-death-{1,2,3,8}-compare.png`: painting / round-9 CPU / candidate CPU at native 256, 160 and 64 px. Corresponding `*-raw.png` files retain ungraded comparisons.
- All nine A/B poses: Cycles CPU, 256px, 16 samples, seed 17, denoising off, identical camera and lighting. The same frozen round-9 LUT grades both sides and every pose. Reduced previews use linear-light premultiplied RGBA resampling.
- Fixed peak-hit shoulder ROI: pale low-chroma pixels **102 → 24 at 256px** (76.5% fewer), **39 → 7 at 160px** (82.1% fewer). Definition and coordinates are in `spearman-r10b-metrics.json`; this is an exposure diagnostic, not an artistic score.
- Rest shoulder RGB error against painting: **12.0555 → 12.2049 / 255**. Rest is essentially preserved, not an improved pixel match. All nine pairs have byte-identical alpha.
- `spearman-r10b-surface-id.png` identifies the problem surface: red wool, blue sleeve, green skin. The main pale upper patch belongs to the sleeve, not the cape.

## Exact checks

- Direct material pass: exact geometry, faces, weights (including cloth pins), original UVs, transforms, pose, actions, camera and light invariants passed in all nine A/B poses.
- Clean project rebuild and scene checks passed: 314 painted materials, 280 camera-only unseen fills, 19,158 body vertices, 53 bones, both round-9 hooks and the new coverage marker.
- Rebuilt all five clips from the new master; every clip has its current master hash and coverage marker. Full **40-pose audit: zero findings**. The first audit correctly rejected copied old clips as stale; those were rebuilt, not relabelled.
- Rebuilt master geometry/actions match round 9 exactly. Frozen painting UVs match exactly. The existing clean-project pipeline regenerated 80 underlying cuirass UVMap loop values by one float unit (maximum 5.9604645e-8); the material-only pass itself changes no original UV.
- Fresh top/front feet cycle rendered as `spearman-r10b-feet-check.png`. 33 dense/planted samples, maximum planted heading **2.54395°**, readable heading **3.46707°**, sole contact slip **0.002156mm**, floor error **1.080395mm**, loop seam **0**; no findings.
- Two pipeline regression tests passed; Python syntax **41/41**, Bash syntax, executable GPU handoff and `git diff --check` passed. No Rust/UI changes, so no Rust/WASM/UI build was run. `tools/art/anim3d/critique.py` is absent and could not be run.

## Learnings

1. Use a material-ID render before guessing at a pale motion patch: this one was largely the fitted linen sleeve. Repainting only the cape would miss it.
2. Preserve trusted source pigment and author low-confidence coverage by garment region. Broad frozen colour masses and a coherent shoulder facing matter more at 160px than more weave. The trial grazing-projection gate worsened rest without improving the patch and was discarded.
3. Verify image buffer encoding. This byte-backed sRGB image exposes encoded byte values through bpy; FLOAT_COLOR requires one linearization. Cache rest normals before writing colour attributes to avoid repeatedly invalidating/recomputing mesh normals.

## Handoff

Run `ROUND=10 tools/art/anim3d/units/spearman/gpu.sh` from the repo root. The existing executable script is unchanged relative to round 9; its project stage now calls the coverage pass. It rebuilds every clip/stage, 512/256 masters, trimmed 160px atlas/JSON, validation, feet sheet, rest comparison and round-numbered five-clip MP4. Final GPU appearance and candidate atlas size are unverified; the imported app atlas is round 9, not a new delivery. No PASS file was written.

Git merge and staging are blocked by ORIG_HEAD.lock/index.lock permissions. The scoped round-9 art baseline was applied as a working-tree patch; unrelated newer master files were retained. `origin/master` is already an ancestor of HEAD. No push, PR or master merge. The runner can commit the worktree with `lanes/spearman-r10b/commit-message.txt`; `round10b-only.patch` contains only the seven lane-B files relative to the round-9 candidate for a clean lead merge.
