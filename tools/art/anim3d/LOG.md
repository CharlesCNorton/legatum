# Unit 3D pipeline log: cost and metrics per unit and round

One section per unit. Add a row per round: what it cost (wall-clock, tokens, GPU minutes) and what it bought (metric before → after, verdict). The point is to see whether each unit is getting cheaper and better than the last.

Sources: `~/LegatumRuns/anim-pilot/legatum/.progress/astra.log` (task start/finish, runner local time, UTC−5), `.reviews/astra-<task>.md.log` (tokens), `~/LegatumRuns/anim-pilot/spearman-rounds.log` (merge and GPU pass), `review/3d-v2/spearman-log.md` and the round notes (metrics). Lane times overlap; a round's wall-clock is first start to GPU finish, not the sum.

## Spearman (first unit; no PASS yet)

### Summary

IoU-old is the original CPU diagnostic (unshifted, alpha threshold 32). IoU and ΔE are `critique.py` (best of ±3 px, alpha > 8, CIE76, base included; targets ≥ 0.95 and ≤ 6). RGB error is the mean absolute R/G/B error over the silhouette union, /255. Atlas is the CPU preview unless marked GPU.

| Round | Date (local) | Codex wall-clock | IoU-old | IoU | ΔE | RGB error | Atlas bytes | What changed | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 11-22 | 46 m | – | – | – | – | – | MPFB hoplite, PBR kit, hand-built motion | Sam: "still pretty rough, but good progress" |
| 2 | 11-22 | 50 m | – | – | – | – | – | Brighter bronze, shield relief, tall crest, cream base | Sam: "huge improvement from round 1 to round 2" |
| 3 | 11-22 | 59 m | 0.8394 | – | – | 35.6/41.3/42.7 | – | Camera projection of the painting, generated back fills, one histogram grade | Shield ornament doubled; feet carry base paint |
| 4 | 11-22 | 26 m | 0.8511 | – | – | 33.3/38.2/39.6 | 198,130 q85 | Shield and crest registered before projection; ray-distance visibility; trimmed atlas, 5-clip movie | Not PASS |
| 5 | 11-22 | 23 m | 0.8644 | – | – | 30.3/35.6/35.5 | 196,706 q85 | Relief cleared above the evaluated shell | Not PASS |
| 6 | 11-23 | 40 m | 0.8767 | – | – | 24.9/29.5/30.4 | 198,474 q85 | Camera refit, real disc at 0.105 m with camera-only cream; macro shape keys baked before fitting; stricter disc-footprint audit | Not PASS |
| 7 | 11-23 | 22 m | 0.8839 | – | – | 22.3/27.3/28.6 | 184,028 q80 | Continuous arm, hand, neckline; elbow poles share the guard | Not PASS |
| 8 | 11-23 | 14 m | 0.8862 | – | – | 21.6/26.8/27.9 | 181,968 q80 | Physical stone calibrated; grade kept | Not PASS; Sam on the walk: "looks like duck feet" |
| 9 | 11-23 | 65 m + lanes 21 m + merge 15 m | 0.8983 | 0.9035 | 13.74 | – | 196,738 q85 | Quaternius CC0 retarget with heel/toe locking; lanes: shield top and cloak tails (a), seam underpaint and fills (b), 92% walk and attack timing (c) | Not PASS; reviewer: stance, values, ragdoll death, pale shoulder |
| 10 | 11-23 | lanes 23 m + merge 14 m + GPU 29 m | 0.8989 | 0.9022 CPU, 0.9039 GPU | 13.81 CPU, 14.05 GPU | – | 183,016 q80 CPU, 197,114 q85 GPU | Calf/greave mass and guard turn (a), shoulder/back coverage (b), source-pose death blend and shield hinge (c); kit extracted | Not PASS; gaps: shoulder shell, lower-leg mass, shield hinge, value structure |

Round-to-task mapping for rounds 1–3 is inferred from task order in `astra.log`. The round-9 ΔE and IoU on the `critique.py` scale are the same-settings baseline measured during round 10 (8 samples, fixed round-9 grade).

### Cost

- Rounds 1–8 (single Astra task each, CPU previews only): 4 h 40 m of Codex wall-clock in total, 2026-11-22 20:13 to 2026-11-23 01:37. Tokens were not kept per round.
- Round 9: first pass 65 m (07:30–08:35); three focus lanes in parallel 10–21 m (20:02–20:24); merge 15 m (20:25–20:40); GPU pass 29 m (20:40–21:10). Round wall-clock from lanes to pushed GPU result: 68 m.
- Round 10: lanes 18–23 m in parallel (21:12–21:34); merge 14 m (21:35–21:49); GPU pass 29 m (21:49–22:19). Round wall-clock from lanes to pushed GPU result: 67 m. Tokens: lane a 199,406, lane b 179,812, lane c 160,558, merge 158,814; **698,590 in total**.
- GPU pass: about 30 m per round at 512 px / 64 samples on the M3 Max (round 8 build: 16:07–16:38; round 9: 20:40–21:10). It rebuilds projection, all five clips with cloth, every stage render, masters, atlas, feet sheet and movie. The pass labelled r8 ran revision `fa87664e`, the first Quaternius build.
- Bottleneck: one Blender process machine-wide. Three lanes plus a merge queue on the same gate, so lane CPU previews must stay short (256 px, 16 samples).

### What moved the numbers

- Geometry and pose registration drove every IoU step (rounds 4, 5, 6, 9a). Surface texture never did.
- The physical base and camera refit were the largest single colour gain (round 6: RGB error −5.4).
- Open motion (round 9) fixed the walk at a stroke after eight rounds of hand-built motion; contact checks have passed since (slip ≤ 0.0022 mm, floor error ≤ 1.14 mm, heading ≤ 2.62°).
- Rounds 9 and 10 improved motion and revealed-surface coverage more than rest metrics: IoU has been flat at 0.90 for two rounds. The remaining rest gap is form (shoulder, lower legs) and value structure.

### Round 11 (2026-11-23 local, in progress)

Lanes started 22:21:19–22:21:25 on the round-10 GPU candidate `aeacff7d`.

- Lane a (sleeve and greave shell), note at 22:32: keep the lower-leg correction. Same-settings CPU A/B (256 px, 16 samples, seed 17, no denoising, fixed round-10 LUT): lower-leg overlap 78.31% → 83.02%; lower-leg RGB error 30.79 → 23.56/255; figure above base 88.98% → 89.87%; whole-image IoU 0.9035 → 0.9103; raw ΔE 13.75 → 13.61. Sleeve smoothing: shoulder overlap 88.75% → 88.64%, optional. Uniform calf-and-greave widening rejected (77.87% → 76.62%). Feet checks unchanged (slip 0.0018 mm, floor 1.133 mm, heading 2.618°; root correction 48.97 mm).

- Lane b (folds and recessed values), note at 22:39: small, bounded surface gain. Inner cloak lining luminance 55.6 → 50.6 (painting 49.0), region blurred ΔE 6.31 → 5.41; death skirt-lining luminance 133 → 99; hit sleeve 109 → 104. Whole image unchanged (IoU 0.9035, raw ΔE 13.76 → 13.75). Rejected: palette replacement with rim darkening (13.76 → 14.00), a global red/green gate, forcing coverage alpha to 1. The lane itself defers to Fable A's look.
- Lane c (motion), note at 22:36: death shield rotation step 83.0° → 34.4°, head step 0.655 → 0.420 m, peak ankle 0.355 → 0.423 m (worse), late cape travel 0.119 → 0.145 m; walk mean ankle spacing 0.246 → 0.344 m (42% → 58% of the rest stance), planted floor error 1.133 mm → under 0.0001 mm, slip 0.0023 mm, root correction 48.88 mm; idle, attack and hit byte-identical to round 10. Not judged against Fable B's keyed death.
- Lanes done 22:40:22 (19 minutes for all three in parallel); merge task queued 22:40.

### Colour on the blurred scale (added 2026-11-24)

`critique.py` now scores colour on blurred images (2 px Gaussian at 256) at zero offset, with per-region values; the ±3 px search is for IoU only. Each round's own graded rest render, re-measured:

| Render | IoU | Blurred ΔE | Raw ΔE (zero offset) | head/crest | torso | cloak (spear side) | shield | legs | feet | base |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Round 9 CPU | 0.9053 | 7.29 | 10.73 | 4.1 | 3.4 | 8.3 | 3.6 | 7.5 | 16.9 | 7.1 |
| Round 10 CPU | 0.9022 | 6.90 | 10.85 | 3.5 | 3.0 | 8.5 | 3.0 | 7.0 | 16.7 | 6.6 |
| Round 10 GPU | 0.9039 | 6.47 | 9.91 | 3.1 | 2.3 | 8.2 | 2.4 | 6.4 | 16.5 | 6.6 |
| Fable A look on Fable B form (lead's figures) | 0.920 | 4.41 | – | – | – | – | – | – | – | – |

Feet, the spear-side cloak and the legs carry the colour error on the Cycles rounds; shield, torso and head are within target. **Baseline as of 2026-11-24: Fable A's look on Fable B's form.** Colour is inside its target; the remaining gap is silhouette.

### Fable builders (2026-11-24, in progress)

- Fable A (look), `fable/unit-anim-3d-spearman-a`, cut from the round-9 candidate: commits `267b2c59` 22:02, `2127e5ef` 22:22, `239540b5` 22:33 local; note at 22:34. About 35 minutes from first commit to a look the art director prefers (03:24Z: better materials than Astra round 10; linen too dark; form unchanged). Rest ΔE on the round-9 geometry, raw per-pixel:

  | Step | IoU | ΔE at critique offset | ΔE at zero offset |
  | --- | --- | --- | --- |
  | Round 9, Cycles CPU, graded | 0.9053 | 13.71 | 10.73 |
  | First Eevee pass | 0.9053 | 14.45 | 11.06 |
  | + display-space reduction, torso layers keep all paint | 0.9048 | 13.29 | 8.45 |
  | + sun at π, cast-only term, ordered ramps | 0.9048 | 12.62 | 7.10 |
  | + shaded stone (current) | 0.9048 | 12.46 | 7.34 |

  Per part at zero offset: shield 3.0, cuirass 3.2, belt 3.5, skirt 3.9, greaves 4.3–5.2, helmet 5.4, spear 5.8 (round 9: 21.3), skin 9.6, cloak 10.9, stone top 12.6, sandals 18–22. Render cost: rest plus 40 frames in about 55 s in Eevee, against a 30-minute Cycles GPU pass. Preview atlas 195,048 bytes at q85. `critique.py` on this branch reproduces the round-9 zero-offset figure (10.73) and gives round 10 GPU 9.91.
- Fable B (form and motion), `fable/unit-anim-3d-spearman-b`, cut from the round-9 candidate: commits `c74a6c2d` 22:16 and `91e3031c` 22:3x local; note at 22:41. Rest-space leg and foot scaling, cloak flare, shaft ×1.75: rest IoU 0.894 → 0.918 (Cycles CPU, 256 px, 16 samples, round-9 grade). Keyed death and hit, walk weight shift with an 8.5 cm lateral ankle offset.
- Verdicts, 03:36Z (cloud reviewer and art director). Look: Fable A, adopt as baseline with its registration fix and display-space reduction. Silhouette: Fable B. Death and hit: Fable B, adopt. Walk: no winner (feet on one line in both). Idle and attack: identical in all three, frozen. Next merge: A's look over B's death, hit and silhouette, the best walk and attack, plus the open shape fixes (shaft width, sandal volume, shield size and rim, base lip, spear arm).

### Round 10 detail (2026-11-23)

| Task | Start | End | Wall time | Tokens |
| --- | --- | --- | --- | --- |
| unit-anim-3d-spearman-a | 21:12:01 | 21:31:54 | 19 m 53 s | 199,406 |
| unit-anim-3d-spearman-b | 21:12:05 | 21:34:40 | 22 m 35 s | 179,812 |
| unit-anim-3d-spearman-c | 21:12:05 | 21:29:45 | 17 m 40 s | 160,558 |
| unit-anim-3d-v2 (merge) | 21:35:10 | 21:49:24 | 14 m 14 s | 158,814 |

- Lane a kept: lower-leg overlap 71.96% → 73.21%; sole span 68.98 → 77.03 px. Oversized flares and outward knees rejected.
- Lane b kept: hit pale pixels 102 → 24 (256 px), 39 → 7 (160 px); rest shoulder error 12.06 → 12.20/255 (slightly worse). Cape-only paint insufficient; grazing-angle gate rejected.
- Lane c kept: death head step 1.277 → 0.655 m; peak ankle 0.848 → 0.355 m; late cape travel 0.419 → 0.119 m combined (0.146 m in lane). Walk influence 0.88 and 0.82 rejected. Shield still turns 83.03° between two delivered samples.
- Combined CPU rest (8 samples, fixed round-9 grade): IoU 0.903515 → 0.902229; ΔE 13.735 → 13.905; refitted grade 13.814. Both targets fail. Regional and motion gains kept despite the small global regression.
- 40-pose audit: zero findings. Feet: slip 0.0018 mm, floor error 1.133 mm, heading 2.618°, seam 0; root correction 48.97 mm (bound 50). CPU atlas 183,016 bytes at q80, 40 records, decoded checks pass.
- Kit probe: MPFB 19,158 vertices, 53-bone game rig, 930-bone Rigify with Armature PV, synthetic corrective 0.49999994 at half activation. Seven regression tests pass.
- Art director review of the CPU preview (2026-11-24 02:51Z, 14 items in `review/3d-v2/spearman-FEEDBACK.md`): spear shaft too thin and dark, feet pale and small, calves outside the greaves, pale blob between the thighs, cloak short on the spear side, base too yellow; death is the worst clip, hit balloons the cloak, walk stance collapses; attack and idle keep. Kit measurements agree: feet-region luminance 187 vs 146 in the painting; death frames 6–8 barely change (decoded alpha steps 1.2, 0.03, 0.03 against a median of 8.2); figure-above-base IoU 0.8887 → 0.8881 and lower-leg IoU 71.96% → 72.86% for the combined candidate.
- GPU pass 21:49:29–22:18:57 (29 m 28 s), 512 px / 64 samples, pushed as `aeacff7d`: IoU **0.9039**, ΔE **14.05**, atlas **197,114 bytes at q85** (2,886 bytes under the limit), 40 frames, decoded validation passes; feet slip 0.0018 mm, floor error 1.133 mm, heading 2.618°. Kit measurements on the GPU masters: figure-above-base IoU 0.8899, lower-leg IoU 73.19%, feet-region luminance 186 vs 146 in the painting, base top `(236,193,137)` vs `(241,203,156)`; death frames 6–8 still barely change. No PASS.
- Art director on the GPU final (03:21Z): all 14 CPU items stand in the same order; six additions visible only on clean frames (pale patch under both feet, calf flap with a ring artifact on the right greave, base lip and wall height, no cast shadow on the base top, shaft still a 2 px black line, crest spike in death frame 3). Attack and idle frozen. Best candidate on every aspect is still Astra round 10; no Fable previews yet.

## Spearman — round 11 merge (2026-11-23 local)

Timing from `.progress/astra.log` (local):

| Task | Start | End | Wall time |
| --- | --- | --- | --- |
| Astra a / form | 22:21:19 | 22:33:38 | 12 m 19 s |
| Astra b / material | 22:21:23 | 22:40:12 | 18 m 49 s |
| Astra c / motion | 22:21:25 | 22:37:11 | 15 m 46 s |
| Merge / unit-anim-3d-v2 | 22:40:28 | 22:55:35 verification checkpoint | 15 m 7 s through this checkpoint |

The runner writes the merge task's finish only after the final response; this is an elapsed verification checkpoint, not a fabricated finished-event timestamp.

- Matched CPU, 256/16/seed17, no denoise/adaptive, fixed R10 LUT: IoU **0.903509 → 0.921945**, zero-offset blurred ΔE **6.63194 → 6.41502**, raw ΔE **10.54877 → 10.28534**. Refitted production-style CPU preview: blurred **5.98499**, raw **10.22221**; IoU still fails 0.95. Feet regional ΔE **15.7**.
- CPU atlas **188,730 bytes / q80**, 40 frames, decoded validation PASS. Movie 1600×352, 192 frames/8 s, H.264 yuv420p. Scene checks pass, pose audit zero findings, 32 tests pass.
- Walk 33 samples: slip **0.00227 mm**, floor error **0.0000211 mm**, heading **2.6184°**, seam **0**, root correction **48.8804 mm**, sole translation **35.7282 mm**. All eight limits pass; near-limit corrections remain warnings.
- Kept Astra a legs (not sleeve), b local lining in the Cycles fallback, c donor-based walk/death; Fable A v3 selected final materials; Fable B cloak flare. Dropped authored B death/hit under the explicit donor-only user rule, despite their art-director win. Idle/attack action hashes identical to R10.
- Imported latest kit/critique through 2c4c2030, with user-conflicting keyed-body exception excluded. New kit graph/part-paint imports replace duplicate unit implementations. Six scene invariants pass for selected look; GPU pixels, 512 masters and final atlas size pending the host `ROUND=11 units/spearman/gpu.sh`. No PASS.
- Full critique and ranked next focus: `review/3d-v2/spearman-round11-note.md`. Isolated master/checks/CPU atlas: `lanes/spearman-r11-merge/`.

- Combined motion readback: death head step 0.41993 m, shield step 34.4144°, ankle height 0.42261 m, late cape travel 0.15734 m (lane C 0.145 m; broader cloak adds 12 mm of late travel). Kept for the rest silhouette win; remaining motion gap is explicit.
