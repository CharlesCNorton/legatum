# Spearman round 12c — donor reactions and visible walk tracks

Changed repository files relative to the round-11 integration candidate:

- `tools/art/anim3d/PLAYBOOK.md`
- `tools/art/anim3d/animate.py`
- `tools/art/anim3d/infantry/retarget.py`
- `tools/art/anim3d/units/spearman/SOURCES.md`
- `tools/art/anim3d/units/spearman/check_frozen.py`
- `tools/art/anim3d/units/spearman/donor_motion.py`
- `tools/art/anim3d/units/spearman/fetch_reactions.py`
- `tools/art/anim3d/units/spearman/gpu.sh`
- `tools/art/anim3d/units/spearman/motion.py`
- `tools/art/anim3d/units/spearman/round12c_review.py`

External shared edits: `assets/SOURCES.md`, `review/3d-v2/spearman-log.md`. The complete source/baseline/generated-file inventory is `spearman-r12c-files.json` beside this note.

**Verdict: not PASS.** Retain hit and walk as strong motion candidates. The donor death now falls forward with staged knee yield, a level spear landing, a face-up shield and visible helmet at the end. It is a credible alternative for the lead's A/B; early cape flutter remains and the small final pose is still less immediately readable than the standing painting. At 256 px the painted silhouette/material differences remain; at 64 px the bronze shield/red crest identity survives but death is a low, compressed shape. Pale sole undersides during walk are a remaining look issue. Hit's two middle poses could be more distinct. No PASS marker written.

KayKit Character Animations Free 1.1 supplies `Hit_B` and `Death_B` (CC0), using full reference-rotation/bone-roll calibration. Idle/walk still use the pinned Quaternius source; only weapon attack is an authored human performance. Native IK transfers source ankle heights and clears actual sandal straps, retaining donor world foot rotation. A constant 85 mm offset per ankle widens walk tracks; carrying-torso motion is halved. Death lower cloak pins are softened with stronger gravity and two seconds of baked post-roll. The attached shield's floor-driven hinge turns face-up; spear release follows the new donor fall. All sources and hashes are in the unit and shared SOURCES.md.

CPU comparisons use 256 px Cycles, 16 samples, seed 17, fixed round-11 LUT, no denoiser, same master/camera. 160/64 reductions use display-space premultiplied alpha. The 64 px painting column uses the real token. These are hybrid-fallback motion previews, not the final selected Eevee look.

| Matched metric | Round 11 | Round 12c |
|---|---:|---:|
| Walk minimum ankle separation (px at 256) | 9.046 | 14.980 |
| Walk shield turn (degrees) | 5.690 | 2.522 |
| Hit vertical head range (mm) | 81.494 | 11.746 |
| Hit shield turn (degrees) | 29.398 | 24.643 |
| Death head step (mm) | 419.934 | 318.570 |
| Death shield turn (degrees) | 34.414 | 33.120 |
| Death peak ankle height (mm) | 422.611 | 418.852 |
| Death late cape travel (mm) | 157.339 | 80.674 |

Rest is byte-identical: IoU 0.921945; blurred delta-E 6.415022, unchanged in this matched CPU setup. Do not compare these directly with round-11 GPU metrics from the other engine.

Checks:

- 32 relevant unit tests passed (`kit`, critique, pipeline, look); the aggregate invocation needs both `tools/art/anim3d` and its `units/spearman` directory on PYTHONPATH. Initial aggregate invocation missed that path; corrected invocation passes.
- Final 40-pose audit: zero findings (camera bounds, base/ground penetration, spear crossings, grip/entry/exit continuity, cloth cache).
- 33-sample actual-foot walk check: all 8 limits pass; slip 0.001887 mm, floor error below 0.0001 mm, planted heading 2.618 degrees, seam zero. Root correction 48.97 mm; slip IK 19.95 mm; sole translation 26.32 mm. Constant 85 mm stance registration is separate from slip correction.
- 103-frame death sandal/strap sweep: minimum clearance 0.99979 mm, no below-floor vertex.
- Rest master and entire idle/attack blend bytes identical to round 11; action hashes separately pinned by `check_frozen.py`, which is also in gpu.sh. See `frozen-files.json`, `frozen.log`, `masters/spearman-3d-v2/frozen-actions.json` in the lane folder.
- CPU preview atlas: 184,282 bytes, quality 80, 40 transparent trimmed frames, validation PASS. This isolated preview is not the shipped atlas. Final two death source samples are byte-identical and decoded alpha is exact. Lossy WebP tiles differ slightly in RGB (channel RMS at most 1.77/255); this is codec noise, not body/cloth movement.
- Movie: H.264 yuv420p, 1600x352, 24 fps, 192 frames, exactly 8 seconds, all five clips at 2x on cream.
- Python compilation, `bash -n gpu.sh`, executable mode and `git diff --check` pass. No Rust/engine/UI changes.

Evidence: `spearman-r12c-{move,hit,death,rest}-{256,160,64}.png`; `spearman-r12c-feet-check.png`; `spearman-r12c-motion-metrics.json`; final critique `spearman-r12c-round12-metrics.json` and related comparisons; `spearman-r12c-round12.mp4`. Isolated masters, before clips, rejected candidates and render/test logs are under `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r12c`.

Learned: donor choice alone is insufficient. Guard-relative knee mapping caused a bounce; use anatomical leg calibration and transfer source contact height after armour/root lifting. Evaluate every sandal strap, not only sole vertices. Optimize delivered head displacement and shield angle rather than cumulative path length alone, then inspect staging. Cape endpoint settling needs simulated post-roll; a good terminal hold does not prove that the earlier cloak is calm. Preserve frozen performances with action and whole-file checks.

Git: requested merge failed at `ORIG_HEAD.lock` (Operation not permitted). Applied the exact 47-file round-11 source delta instead, then made these 10 lane edits. Staging also failed at `index.lock`; no commit was possible. `origin/master` is already an ancestor of lane HEAD. The runner should merge `astra/unit-anim-3d-v2`, then apply `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r12c/lane-only.patch` (not the baseline patch again). `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r12c/commit-message.txt` contains the required co-author trailer. No push or PR.

Lead GPU pass, from the repository root after integrating selected changes:

```sh
ROUND=12 tools/art/anim3d/units/spearman/gpu.sh
```

The executable still fetches pinned sources, rebuilds all five clips, verifies frozen actions, renders every stage and 512/256 masters, produces and validates the trimmed 160 atlas and eight-second MP4, checks feet/geometry, and writes critique/rest comparisons. GPU execution was not available in this CPU sandbox; selected-look GPU output remains required.
