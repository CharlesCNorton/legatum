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

### Colour on the blurred scale (added 2026-11-24)

`critique.py` now judges colour on blurred images (2 px Gaussian at 256) and per region. Each round's own graded rest render, re-measured:

| Render | IoU | Raw ΔE | Blurred ΔE | head/crest | torso | cloak (spear side) | shield | legs | feet | base |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Round 9 CPU | 0.9053 | 13.71 | 7.62 | 4.5 | 4.3 | 8.6 | 3.7 | 7.9 | 17.4 | 6.6 |
| Round 10 CPU | 0.9022 | 13.81 | 7.36 | 4.4 | 4.1 | 8.9 | 3.3 | 7.6 | 17.4 | 6.0 |
| Round 10 GPU | 0.9039 | 14.05 | 6.98 | 3.8 | 3.6 | 8.7 | 2.8 | 7.0 | 17.2 | 6.1 |

Feet, the spear-side cloak and the legs carry the colour error; shield, torso and head are within target. The raw number moved the wrong way across the same three renders.

### Fable builders (2026-11-24, in progress)

- Fable A (look), `fable/unit-anim-3d-spearman-a`: commits `267b2c59` 22:02 and `2127e5ef` 22:22 local; first rest preview 22:23. Art director 03:24Z: better materials than Astra round 10 (shaft colour, cloak cavities, greave and shield highlights, base lip), linen too dark, form unchanged (IoU 0.900 vs 0.903). No clips yet.
- Fable B (form and motion), `fable/unit-anim-3d-spearman-b`: commit `c74a6c2d` 22:16 local, an authored keyed death collapse plus quick-look tools. No preview or note yet.

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
