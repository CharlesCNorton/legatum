# Unit 3D pipeline log: cost and metrics per unit and round

One section per unit. Add a row per round: what it cost (wall-clock, tokens, GPU minutes) and what it bought (metric before → after, verdict). The point is to see whether each unit is getting cheaper and better than the last.

Sources: `~/LegatumRuns/anim-pilot/legatum/.progress/astra.log` (task start/finish, runner local time, UTC−5), `.reviews/astra-<task>.md.log` (tokens), `~/LegatumRuns/anim-pilot/spearman-rounds.log` (merge and GPU pass), `review/3d-v2/spearman-log.md` and the round notes (metrics). Lane times overlap; a round's wall-clock is first start to GPU finish, not the sum.

## What the next unit should cost (estimate, not yet measured)

The Spearman took 13 rounds and about 31 hours of wall-clock (2026-11-22 20:13 to 2026-11-24 03:02 local) to pass both metric targets. Most of that was finding the method. The last 0.05 of IoU and the whole colour target came in the final 5 hours, from four moves that are now steps in the skill and code in the kit.

For a second infantry unit starting from the kit, with two builders split by aspect and previews in Eevee:

- Form builder: body, unit kit geometry, guard pose and outline fitted by measured spans. The unit-specific modelling is the long pole; allow 60–90 minutes.
- Look builder: registration fit (20 s), ID pass, per-part textures and ramps (15 s per rebuild), look tuning on previews (55 s per full set). 30–45 minutes, mostly waiting for form.
- Motion: idle and walk retargeted from the pinned donors with the 8.5 cm offset and walk shaping (kit); attack, hit and death keyed or from KayKit, authored on the one-minute quick-look loop. 45–60 minutes.
- One merge and one GPU pass: about 20 + 38 minutes.

That is roughly 3 hours of wall-clock per unit and two GPU launches if a gate fails, against 31 hours for the first. The bottleneck is the single Blender slot: a full GPU pass holds it for 38 minutes and starves every preview, so thirty units in parallel are limited by about 30 × 1 hour of Blender time, not by agents. Run GPU passes back to back when builders are between previews, or move final passes to a second machine. Record the real numbers here when the second unit runs; delete this estimate then.

## Spearman (first unit; metric targets passed in round 13, art PASS pending)

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
| 11 | 11-23 | lanes 19 m + merge 17 m + GPU 31 m | – | 0.9219 CPU, 0.9275 GPU | blurred 4.59 GPU (R10 6.47) | – | 188,730 q80 CPU, 185,380 q80 GPU | Greave fit (a), lining pigment (b), wider walk and shield damping (c); Fable A's Eevee look, Fable B's cloak flare, shaft 1.8× thicker; registration and reduction fixes | Not PASS; colour passes, feet 13.4, silhouette 0.93 |
| 12 | 11-23/24 | lanes 40 m + merge 25 m + GPU 38 m (after a failed 2 m launch) | – | 0.9394 CPU proxy, 0.9384 GPU | blurred 4.55 CPU proxy, 4.72 GPU | – | 190,952 q80 CPU, 186,556 q80 GPU | Fable B's form, guard, cloak, disc and keyed death; KayKit donor hit and 8.5 cm walk offset (c); width-only foot fit (a); revealed-surface pigment (b); soles seated on the stone | Not PASS; best on every aspect; feet 12.9; base lip regressed |
| 13 | 11-24 | lanes 19 m + merge 19 m + GPU 38 m (after a failed 25 m launch) | – | 0.9513 CPU proxy, **0.9537 GPU** | blurred 3.39 CPU proxy, **3.51 GPU** | – | 192,866 q80 CPU, 187,254 q80 GPU | Fable C's guard replanted on the painted feet, registered disc, ankle-anchored ground shadow, base band; lane c's lower swing and calmer collapse; one render function for look and delivery | Both metric targets pass; visual review pending |
| 14 | 11-24 | lanes 29 m + merge 16 m + GPU 42 m | – | 0.9513 CPU proxy, 0.9537 GPU (rest unchanged) | blurred 3.39 CPU proxy, 3.51 GPU | – | 192,682 q80 CPU, 187,316 q80 GPU | Polish: cloak damping in move and attack (b); cloth loop closure, walk sample rotation, evaluated support surface, early parity gate (c) | Rest targets pass on GPU; clip review pending |

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

- Merge task 22:40–22:57 (17 minutes). Same-settings CPU A/B against round 10 (256 px, 16 samples, seed 17, fixed round-10 grade): IoU 0.9035 → **0.9219**; blurred ΔE at zero offset 6.63 → 6.42; raw 10.55 → 10.29. Production-style preview with a refitted grade: blurred 5.98 (7.23 on the previous shifted definition), feet region 15.7. Kept: lane a's greave fit, lane b's lining for the Cycles fallback, lane c's walk and shield, Fable A's look as the final path, Fable B's cloak flare and a shaft 1.8× thicker in the master. Not taken: lane a's sleeve folds, Fable B's leg and foot scaling (no matched contact A/B yet) and its keyed death and hit (the merge's instruction allows only a keyed attack). 40-pose audit zero findings; feet slip 0.0023 mm, floor error 0.00002 mm, root correction 48.88 mm of 50; idle and attack action hashes equal round 10; CPU preview atlas 188,730 bytes at q80; 32 tests pass (23 kit, 4 critique, 2 pipeline, 3 look). GPU pass 22:57:52–23:28:57 (31 m), pushed as `01a69951`, the first with the Eevee painted look and display-space reduction: IoU **0.9275**, blurred ΔE **4.59** (passes), raw 7.30; regions head/crest 3.8, torso 2.9, cloak 3.3, shield 2.4, legs 3.3, feet 13.4, base 3.9; atlas 185,380 bytes at q80, 40 frames, decoded validation passes; feet slip 0.0023 mm, floor error 0.000 mm, heading 2.618°. Round wall-clock from lanes to pushed GPU result: 68 m. No PASS.
- Art director on the round-11 GPU final (04:31Z): rest pose "best yet"; at 160 and 64 not distinguishable from the painting above the ankles; shaft, linen, cloak width, greaves, base lip fixed and the foot puddles gone. Feet are the last rest tell. Clips: the donor death, hit and walk kept by the merge are the three worst things on screen; take Fable B's walk, death and hit in round 12.

- Reviewer's decision after the merge (about 04:00Z): death, hit and attack may be hand-keyed or donor-based, whichever reviews better; idle and walk stay on open mocap. Round 12 adopts Fable B's death and hit.

### Round 12 (2026-11-23 local, in progress)

Lanes started about 23:31 on the round-11 GPU candidate `01a69951`, with the restructured skill installed.

- Lane a (sandals and shin), note at 23:48: foot width × 1.50 and height × 1.15, ankle 35 mm inward, guard turned 15°. Same-settings CPU A/B: IoU 0.9219 → 0.9229; blurred ΔE 6.42 → 6.29; lower-leg overlap 86.1% → 87.8%; lower-leg RGB error 21.1 → 19.2; feet RGB error 34.8 → 31.9; shin lean 8.7 → 4.2 px. Walk limits pass (slip 0.0020 mm, heading 3.38°, root 48.88 mm, sole translation 35.6 mm). Rejected: foot length × 1.35 (58.7 mm sole correction), 25° guard turn, 32 mm sleeve shortening. Preset feet region still 13.8.
- Lane b (material continuity), note at 23:53: render-time paint for soles, skirt lining and rear shoulder on a CPU proxy of the Eevee look. Rest unchanged (IoU 0.9219, blurred 4.509 → 4.514); death frame 4 skirt luminance 101 → 83, sandals 88 → 70. Found a 3 mm gap between the rest soles and the stone.
- Lane c (motion), note at 00:09: new CC0 donors KayKit `Hit_B` and `Death_B`, plus the 85 mm ankle offset. Walk minimum ankle separation 9.0 → 15.0 px at 256, shield turn 5.7° → 2.5°; hit head range 81 → 12 mm; death head step 420 → 319 mm, late cape travel 157 → 81 mm, peak ankle 423 → 419 mm. Walk limits pass (slip 0.0019 mm, root 48.97 mm, sole translation 26.3 mm); 40-pose audit zero findings; idle and attack byte-identical; CPU preview atlas 184,282 bytes at q80. Art director (04:47Z): donor hit wins outright, walk ties Fable B, death is the best donor death so far.
- Art director, 05:02Z: Fable B's form and clips under A's look are the best complete Spearman, rest IoU 0.935.
- Lanes done 00:11:31 (about 40 minutes); merge 00:11–00:36 (25 minutes). Same-settings CPU proxy (256 px, 8 samples, display-space reduction), round 11 → 12: IoU 0.9244 → **0.9394**; blurred ΔE 4.49 → 4.55; feet 13.96 → 13.35; cloak 3.05 → 4.37; base 3.88 → 4.75. Kept: Fable B's form, guard, straps, cloak, disc and keyed death; lane a's width-only foot rule; lane b's revealed-surface pigment (now `kit/continuity.py`); lane c's KayKit hit and widened walk. Dropped: lane c's donor death, lane a's competing shin fit, Fable B's 1.42× foot length (42.6 mm sole correction). Rest sole clearance 3.0 → 1.0 mm. Walk: slip 0.0018 mm, heading 5.14° (readable 9.18°, limit 10°), root 48.96 mm. CPU preview atlas 190,952 bytes at q80. 33 tests pass.
- GPU pass 00:36: **failed after 2 minutes** at the painted-look stage, `ModuleNotFoundError: No module named 'continuity'` (a unit-folder import under `blender --python`). The lead fixed it in `ef6631e9`. Cost: one wasted launch; the static check that would have caught it is now `kit/check_imports.py`.
- GPU rerun 00:38:24–01:16:07 (38 m), pushed as `07643cd4`: IoU **0.9384**, blurred ΔE **4.72** (passes), raw 7.52; regions head/crest 3.7, torso 2.9, cloak 4.8, shield 2.4, legs 3.4, feet 12.9, base 4.8; atlas 186,556 bytes at q80; walk slip 0.0018 mm, floor error 0.000 mm, heading 5.142°. Round wall-clock from lanes to GPU result: about 105 m including the failed launch. No PASS.
- Art director on the merge (CPU proxy, before the GPU frames): best Astra candidate on every aspect; feet are the only failing region; the base lost the lip round 11 had; walk lifts the trailing foot too high; hit frames 1 and 2 too alike; death's final frame reads at 64 px.

### Round 13 (2026-11-24 local, in progress)

Lanes about 01:20–01:39 on the round-12 GPU candidate `07643cd4`, with the consolidated skill installed. Same-settings CPU proxy A/Bs against round 12:

- Lane a (stance): IoU 0.9358 → 0.9367 (zero offset 0.9358 → 0.9361); lower-leg IoU 0.9169 → 0.9187; blurred ΔE 4.58 → 4.53; shin lean 10.4/5.3 → 9.3/4.5 px; feet region unchanged at 13.3. Larger inward shifts lost zero-offset IoU.
- Lane b (base and sandals): base 4.77 → 4.00 (side 3.81 → 2.86); feet 13.33 → 13.36 with strap-only darkening; broad foot darkening rejected (13.90).
- Lane c (walk and death staging): swing-sole clearance 114 → 76 mm; pelvis sway 68 → 85 mm; slip 0.0018 → 0.0043 mm; death body over the disc 55% → 76%.
- For scale: Fable C, working on the same round-12 base at the same time, took the rest pose from IoU 0.9394 to 0.9513 and the feet region from 13.35 to 5.3 by measuring the feet on a gridded crop first.
- Lanes done 01:39:25. Merge 01:39–01:58 (19 m): Fable C's guard, feet, base and look with lane c's walk and collapse; lanes a and b dropped as overlapping, Fable D's death dropped on the 06:40Z verdict. CPU proxy against round 12: IoU 0.9394 → **0.9513**, blurred ΔE 4.55 → **3.39**, feet 13.35 → 5.45, base 4.75 → 3.23; walk slip 0.0042 mm on the new guard after a whole-track registration (ankle-only: 29.8 mm). Look and delivery now share one render function.
- GPU pass 01:58:55–02:23:57: **failed after 25 minutes** at the new render-parity gate, which asserted exact pixel equality between two Eevee renders of the rest. They differ by sample noise only (142 of 262,144 pixels, one by more than 2 levels, mean 0.0002). Second GPU launch of the night lost to a gate or import the sandbox could not run. The lead gave the gate a noise tolerance in `10966f8e`.
- GPU rerun 02:25:00–03:02:39 (38 m), pushed as `d7798046`: IoU **0.9537** (passes 0.95), blurred ΔE **3.51** (passes 6), raw 6.36; regions head/crest 3.7, torso 2.9, cloak 4.8, shield 2.4, legs 3.2, feet 5.3, base 3.3; atlas 187,254 bytes at q80; walk slip 0.0042 mm, floor error 0.000 mm, heading 5.142°. **First round to pass both metric targets.** Art director, 08:03Z: best on every aspect, clips hold at 160 px, "ready to show Sam as a PASS candidate"; seven polish items, none blocking. No PASS file (the lead's and Sam's call). Round wall-clock from lanes to GPU result: about 100 m including the failed launch.

### Round 14 (2026-11-24 local, in progress): polish after passing

Lanes about 03:05–03:33 on the round-13 GPU candidate `d7798046`.

- Lane a (death staging): Fable D's collapse compacted onto the base; crest and feet margins against the rim −28.1 / −13.7 px → +3.3 / +5.0 px. Rest on the CPU proxy unchanged in kind: IoU 0.9513, blurred ΔE 3.33.
- Lane b (cloak in move and attack): cloak edge sweep 22.1 → 15.5 px (move) and 10.4 → 8.0 px (attack); cloth endpoint p95 182 → 133 mm. A 1.35× pin trial rejected (worst vertex 246 mm).
- Lane c (loops and transitions): cloak loop gap 12.07 → 0.00003 px (move), 2.62 → 0.00003 px (idle); idle-to-move sole gap 23.0 → 14.4 px, move-to-idle 18.7 → 9.4 px by rotating the walk's eight samples.
- Lanes done 03:33:00 (a 16 m, b 13 m, c 29 m in parallel). Merge 03:33–03:49 (16 m): lane b's cloth and lane c's loop closure, sample rotation, evaluated support surface and early parity gate; lane a's side-lying death dropped (contained, but the shield face is lost). Rest pixels identical to round 13 on the CPU proxy (IoU 0.9513, blurred ΔE 3.39); CPU preview atlas 192,682 bytes at q80; 36 tests, zero audit findings, walk slip 0.0042 mm. Worst free-cloth loop correction 273 mm (authored, not simulated). GPU pass 03:49:31–04:31:40 (42 m), first launch clean with the parity gate early, pushed as `9c35ac22`: rest unchanged at IoU **0.9537**, blurred ΔE **3.51** (regions head/crest 3.7, torso 2.9, cloak 4.8, shield 2.4, legs 3.2, feet 5.3, base 3.3); atlas 187,316 bytes at q80; walk slip 0.0042 mm, heading 5.142°. Round wall-clock from lanes to GPU result: 89 m. Visual review of the new clips pending; no PASS file.

### Fable C and D (2026-11-24, from round 12)

- Fable C (rest stance, ground shadow, base band), `fable/unit-anim-3d-spearman-c`, note about 01:30 local: rest IoU 0.9394 → **0.9513** on the CPU proxy and **0.9534** in Eevee; blurred ΔE 4.55 → **3.35**; feet 13.35 → 5.4; base 4.75 → 3.3. First candidate to pass both targets. Walk numbers unchanged to the digit (slip 0.0016 mm, heading 5.14°, root 48.96 mm). Dropped: ankle targets without knee columns (0.936), an AO ground shadow (base 2.7 → 5.4), stronger sandal tones.
- Reviewer's decision: one render path. Round 12's `gpu.sh` output differs from `look.py` on the same master (shield rim p10 50 vs 27 against the painting's 28–38).

### Colour on the blurred scale (added 2026-11-24)

`critique.py` now scores colour on blurred images (2 px Gaussian at 256) at zero offset, with per-region values; the ±3 px search is for IoU only. Each round's own graded rest render, re-measured:

| Render | IoU | Blurred ΔE | Raw ΔE (zero offset) | head/crest | torso | cloak (spear side) | shield | legs | feet | base |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Round 9 CPU | 0.9053 | 7.29 | 10.73 | 4.1 | 3.4 | 8.3 | 3.6 | 7.5 | 16.9 | 7.1 |
| Round 10 CPU | 0.9022 | 6.90 | 10.85 | 3.5 | 3.0 | 8.5 | 3.0 | 7.0 | 16.7 | 6.6 |
| Round 10 GPU | 0.9039 | 6.47 | 9.91 | 3.1 | 2.3 | 8.2 | 2.4 | 6.4 | 16.5 | 6.6 |
| Round 11 GPU (Eevee look) | 0.9275 | 4.59 | 7.30 | 3.8 | 2.9 | 3.3 | 2.4 | 3.3 | 13.4 | 3.9 |
| Round 12 GPU (Eevee look, Fable B form) | 0.9384 | 4.72 | 7.52 | 3.7 | 2.9 | 4.8 | 2.4 | 3.4 | 12.9 | 4.8 |
| Round 13 GPU (Fable C guard and look) | 0.9537 | 3.51 | 6.36 | 3.7 | 2.9 | 4.8 | 2.4 | 3.2 | 5.3 | 3.3 |
| Fable C, Eevee via look.py (its note) | 0.9534 | 3.35 | – | 3.4 | 2.5 | 4.8 | 2.0 | 3.0 | 5.4 | 3.3 |
| Fable A look on Fable B form (look lane's own blur, not comparable) | 0.920 | 4.41 | 6.80 | – | – | – | – | – | – | – |

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
- Fable B v3 (note updated 23:42 local): form retuned by measured row spans, rest IoU 0.918 → 0.932 (alpha > 128, zero offset), lower body 0.936; disc radius × 0.965; keyed death with the spear released over frames 2–4, 40-pose audit zero findings; walk feet check heading 1.9°, slip 0.002 mm. Its Eevee previews were starved twice by another lane's GPU pass.
- Verdicts, 03:36Z (cloud reviewer and art director). Look: Fable A, adopt as baseline with its registration fix and display-space reduction. Silhouette: Fable B. Death and hit: Fable B, adopt. Walk: no winner (feet on one line in both). Idle and attack: identical in all three, frozen. Next merge: A's look over B's death, hit and silhouette, the best walk and attack, plus the open shape fixes (shaft width, sandal volume, shield size and rim, base lip, spear arm).

- Verdict, 03:52Z (art director, on A's look over B's form and motion): the best Spearman so far, base of the next merge. Rest IoU 0.918–0.920 against Astra round 10's 0.904. Walk: Fable B v2. Death and hit: Fable B. From Astra round 11, "take nothing over the Fable pair" unless lane a's sandal welts turn out fuller than B's feet.
- Cost comparison for the same evening: Astra round 10 (three lanes, a merge, a GPU pass) took 67 minutes and about 700,000 Codex tokens for IoU 0.9035 → 0.9039 on GPU and a blurred ΔE of 6.47. The two Fable builders, cut from the round-9 candidate and split by aspect (look; form and motion), reached IoU 0.920 and blurred ΔE 4.41 in about 50 minutes of wall-clock from their first commit (22:02 local) to the combined verdict (22:52 local), with previews in Eevee at 55 s per full set. Their token use is not in the Codex log.

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
