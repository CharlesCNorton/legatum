# Spearman round 14 lane c — loops, transitions and real stone support

Files changed relative to round 13 (`d7798046`), under `tools/art/anim3d/`:
- `PLAYBOOK.md`
- `animate.py`
- `audit.py`
- `kit/audit.py`
- `kit/base.py`
- `kit/loop.py`
- `units/spearman/check_support.py`
- `units/spearman/check_transitions.py`
- `units/spearman/donor_motion.py`
- `units/spearman/frozen-actions.json`
- `units/spearman/gpu.sh`
- `units/spearman/round14c_review.py`
- `units/spearman/transitions.py`

## Verdict

Keep the evaluated support surface, cloth loop closure, expanded measurements,
reviewed fingerprints and earlier render-parity gate. The balanced walk sample
rotation improves both cuts but does not make idle/move seamless: NOT a PASS.
No foot yaw correction, rest geometry/material/camera edit, atlas-anchor shift,
or death choreography edit. Lane a owns death, lane b owns walk/cloth styling.
The generic cloth closure runs after either lane's bake.

At 256 px the rest is unchanged and still shows smooth sandal shapes and the
strong shadow band from round 13; CPU noise is visible. At 160/64 it retains the
painting's identity. The loops are visibly calmer; the hard cut from the broad
painted guard to the moving stride remains visible. No claim of GPU approval.

## Matched CPU evidence

Cycles CPU, 256 px, 8 samples, seed 17, Standard, no denoiser; shared
`look.configure_render` / `look.render_frame`, analytical-light proxy without
Eevee cast shadows. Before/after rest pixels are exactly equal. Rest critique:
IoU 0.9512536, blurred delta-E 3.33059, feet 5.44725, base 3.23225. This is not a
colour improvement over R13: the matched before is the identical image.
R13's production GPU result remains separately 0.9537 / 3.51.

All following distances are maximum corresponding geometry vertex distances
at 160 px, not inferred from a movie or a sole centroid:

| Check | R13 | R14c |
| --- | ---: | ---: |
| Idle cloak duplicate-endpoint gap | 2.62442 px | 0.000031 px |
| Move cloak duplicate-endpoint gap | 12.07360 px | 0.000015 px |
| Idle frame 0 to move entry sole gap | 23.00415 px | 14.41120 px |
| Last delivered move to idle frame 0 sole gap | 18.663 px | 9.44206 px |
| Attack entry/exit sole gap | <0.00004 px | <0.00004 px |
| Move foot duplicate-endpoint gap | 0 | 0 |

The reviewer-described attack-frame-0 jump was not reproduced on the merged
R13 master. Full sole geometry already matches to <0.001 mm, including toe and
heel; all idle exit phases move by at most about 0.15 px. Do not disturb that
performance to fix an obsolete observation.

Walk samples rotate from [25,29,33,37,41,45,49,53] to
[41,45,49,53,25,29,33,37]. Every original sample and the 4-frame interval survive.
Entry-only phase 37 was rejected: it improved entry to 9.44 px but worsened the
exit to 19.95 px. Dense phase 40 gave a marginally better balanced 13.37 px but
would replace the original eight delivered samples; kept the simpler exact
permutation. A true entry/exit performance needs separate transition samples;
forcing the toe-out guard into each locomotion loop would violate donor foot
rotation and walking-contact constraints.

Cloth correction: capture the baked pre-thickness endpoint residual, store
825 point offsets, and apply a zero-slope envelope after Cloth and before
thickness/subdivision. Maximum free-cloth correction is 71 mm idle / 230 mm
move. All 53 bone matrices remain exactly unchanged at every dense sample.
This is an authored correction of simulation drift; no claim it is a fresh
physical simulation. Reviewed intermediate 256/160/64 sheets, not only the
endpoint numbers. Idle action fingerprint changes to
`75c85c9d912cbc2e8ee41a18902123a2c5e661741972eb16a6b80d2209087cca`;
a fresh full idle rebuild reproduced it exactly. Attack remains
`d78edd5ce23bd3725d76f2e1f7ffad98fb4d43e8f3834982c0872800f0706ab3`.

## Base and pipeline

Floor fits and audits now query actual evaluated stone faces, including the
bevel, in world coordinates. A synthetic 0.58 m top / 0.77 m lower ring test
finds support at 0.041842 m where the old top-plane test returned 0.105 m;
points beyond the actual rim fall to world ground. Tests also cover a loose
vertex and translated/nonuniformly scaled ellipse. The actual merged R13
base has a widest raw local radius of 0.5839 m, so the reported 0.77 m was not
reproduced on that input. The defect in the general floor approximation is
fixed without changing the painted stone geometry.

`gpu.sh` retains the one-render-path parity check and its measured sample-noise
tolerance; moves it before all five cloth bakes; adds the support regression;
retains 512/256 masters, 40-frame 160px atlas, validation, critique and movie.
GPU parity was not run inside this CPU-only sandbox.

## Verification and files

- Rebuilt all five clips against the evaluated support; corrected idle/move cloth.
- 36 Python tests passed: kit 27, look 3, critique 4, pipeline 2.
- Blender support regression passed; complete sole and cloth-loop gates passed.
- Frozen idle/attack checks passed; fresh idle build reproduced the new pin.
- All 40 poses audited: zero findings after cloth correction.
- All eight feet limits passed: slip 0.004234 mm; planted floor error 0.000106 mm;
  heading 5.1424 deg, readable heading 9.1751 deg; foot loop 0.
- Full 33-pose top/front feet sheet rendered and reviewed. Its foot geometry
  is unchanged by the subsequent cloak-only modifier; final metrics refreshed.
- CPU atlas: 193118 bytes, Q80, 40 decoded frames validated; isolated lane only.
- Movie: H.264/yuv420p, 1600x352, 24 fps, 192 frames, 8.000 seconds.
- Import checker: zero unresolved imports. Python parse, bash syntax, git
  whitespace checks passed. Lane-only patch applied to a clean R13 file tree
  and reproduced all 13 changed files exactly.

Main review files in this directory:
`spearman-r14c-rest-{256,160,64}.png`,
`spearman-r14c-entry-{256,160,64}.png`,
`spearman-r14c-loops-{256,160}.png`,
`spearman-r14c-{idle,attack,death}-{256,160,64}.png`,
`spearman-r14c-feet-check.png`, `spearman-r14c-contact-sheet.png`,
`spearman-r14c.mp4`, and `spearman-r14c-{metrics,transitions,audit,delivery}.json`.

Masters, raw CPU frames, receipts, logs, atlas and helper scripts:
`~/LegatumRuns/anim-pilot/lanes/spearman-r14c/`.
No new downloaded assets; no PASS file, push or PR. CPU delivery stays isolated;
the app atlas only received the requested R13 baseline content port.

Merge and commit could not acquire `ORIG_HEAD.lock` / `index.lock`. R13 content
was ported into the clean worktree. Runner: merge `astra/unit-anim-3d-v2`, then
apply the lane-only `lanes/spearman-r14c/lane-c.patch`; `changed-files.txt`,
`source-branches.json`, and the required co-author `commit-message.txt` accompany
it. Current origin/master is already an ancestor of R13; no fetch performed.
Lead GPU handoff from repository root:
`ROUND=14 tools/art/anim3d/units/spearman/gpu.sh`.

## Learned for the cumulative skill

1. A zero foot-loop seam says nothing about cloth. Measure actual evaluated
   cloth vertices at the duplicate endpoint; the R13 move had a hidden 12 px gap.
2. Post-bake geometry correction can close periodic cloth drift without
   touching donor rotations or UVs. Check the whole clip and re-pin the changed
   idle action; large free-hem corrections are not physically re-simulated.
3. Minimize both entry and exit when rephasing a cycle. Reordering a loop can
   reduce hard-cut jumps, but cannot make a toe-out guard identical to walking.
4. A maximum vertex radius does not describe the support top. Evaluate faces;
   keep fitting and auditing on one surface query, including bevel and ground.
