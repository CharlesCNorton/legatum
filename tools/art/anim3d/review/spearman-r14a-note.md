# Spearman round 14a — Fable D death integrated on round 13

Lane files: tools/art/anim3d/PLAYBOOK.md; tools/art/anim3d/animate.py;
tools/art/anim3d/units/spearman/collapse.py; tools/art/anim3d/units/spearman/death_review.py.
The complete baseline synchronization file list and exact source commits are in
spearman-r14a-files.json. Git refused ORIG_HEAD.lock and index.lock; no recorded
merge or commit. Round-13 d7798046 was applied as a source diff to the initially
clean branch. Runner: use spearman-r14a-lane-only.patch against round 13; its
application check passes. Commit text: lanes/spearman-r14a/commit-message.txt.

## Change

Imported only Fable D c6e55c3b collapse plus its shield-after-floor-lift hook.
No walk layer or look edits. At build time register_guard reads the new master's
calf/lowerarm tails and knee/elbow positions, rebases the entry and recoil, and
blends full bone matrices through the first interval to preserve entry roll.
The recoil retains planted ankles. The fall's late pelvis shifts inward while
the ankles tuck toward the hip along the fallen body axis. Geometry, camera,
materials, idle, move, attack and hit source are unchanged from round 13.

## Matched CPU evidence

All new comparisons use Cycles CPU, 256 px, 8 samples, seed 17, no denoising,
fixed painting camera, analytic sun painted-look proxy (no cast-shadow term).
Both round-13 and final-death comparisons use baked cloth. The intermediate
Fable import used diagnostic unbaked cloth; its evaluated crest/foot measurements
are unaffected by cloth. Main sheets: spearman-r14a-after-{256,160,64}.png and
spearman-r14a-death-strip-{256,160,64}.png. Animated A/B: spearman-r14a-death.webp.
Five-clip decoded preview: spearman-r14a.mp4. Rest: spearman-r14a-restpose-compare.png.

Held pose horizontal margins inside the evaluated visible base at 256 px:

| Candidate | Crest left margin | Feet right margin |
| --- | ---: | ---: |
| Round 13 | -28.09 px | -13.71 px |
| Fable D on round-13 guard, before tuck | -9.96 px | -10.88 px |
| R14a, both delivered held samples | +3.34 px | +5.00 px |

Positive means inside. These are camera-projected horizontal edge margins, not
a claim every elevated point lies within the base's projected ellipse or a new
physical support-footprint implementation. Lane c owns the base-radius bug.
The held PNG is rendered once and copied, byte-identical. All ten samples remain.
Spear vertical endpoint difference from sample 3 onward is below 0.002 mm.
Death entry ankle/hand/elbow/head max difference from idle: 0.000522 mm.
Direct collapse.apply(0) all-joint error: 0.000776 mm; phase 0.000001:
0.000738 mm. This checks the solver, not only the animator's t=0 reset shortcut.

## Verification

- Complete CPU death build and 79-frame cloth bake succeeded; no spear crossing.
- All 40 delivered poses audited: zero findings (existing round-13 audit).
- 33-sample top/front feet render and all eight contact limits pass: slip
  0.004234 mm, floor error 0.000106 mm, planted heading 5.142 degrees,
  readable heading 9.175 degrees, loop seam 0. Walk was not changed.
- 27 kit + 9 critique/pipeline/look tests pass (36 total). The first module-style
  test invocation lacked PYTHONPATH; rerun with the repository's script paths passed.
- Import checker: zero unresolved local imports. Python AST and gpu.sh shell
  syntax pass. Lane diff whitespace and lane-only patch application checks pass.
- Isolated 160 px trimmed CPU preview atlas: 191440 bytes, Q80, 40 decoded
  records validated. No newly generated atlas written to app assets.
- Rest CPU critique: IoU 0.951254, blurred delta-E 3.330594, raw 7.220911.
  Every region below 6; feet 5.4. Rest source is unchanged from the copied
  round-13 GPU master. Historical round-13 GPU metrics (.9537 / 3.51) use a
  different engine and are not an improvement claim for this death-only lane.

## Verdict and remaining limits

Recommend integrating this death: the held body and face are visible in front
of the shield, and both requested extremities fit inside the rim. At 160 and 64
it reads as the same spearman. At 256 the exposed skirt folds look mechanically
regular and the landing still has a propped-on-forearm quality. Intermediate
sample 6's feet remain 12.19 px beyond the rim and sample 7's 2.92 px; they come
inside for both held frames. All remain in the sprite cell. This lane does not
claim those transitional poses or premium materials are final art approval.
The rest remains close to the painting at 256 and reads as the same unit at 64;
the known sandal-detail and shadow polish remains outside this lane.
No PASS marker written. CPU proxy has no live cast shadows; the lead must judge
the merged GPU MP4 and re-audit after lane c's floor-footprint change.

GPU handoff is unchanged, executable and syntax checked. From repo root:
`ROUND=14 tools/art/anim3d/units/spearman/gpu.sh`
It rebuilds all clips, renders all stages and 512/256 masters, packs/validates
160 px cells, makes the top/front feet sheet, critique and five-clip MP4.

## Learned

1. A transplanted GUARD needs the actual IK endpoints (calf/lowerarm tails) and
   elbow/knee planes, plus an entry rotation blend; matching foot/hand points
   alone can still introduce an abrupt bone-roll change.
2. A released shield must be re-placed after body floor correction or it rides
   upward with the lifted arm even though its authored rest is world-space.
3. Compact a side-lying figure by tucking ankle targets toward the hip in the
   fallen body's axis and moving the torso inward; a translation alone trades
   crest overhang for foot overhang. Measure evaluated geometry at fixed camera.


### Automated critique: spearman-round14 (R14a Cycles CPU proxy, 256px 8 samples, baked death, decoded 160 atlas; GPU pending)

- Silhouette IoU: **0.9513** (target ≥ 0.95; PASS). Best of ±3 px offsets: render x=+0, y=+0.
- Tone/colour ΔE on blurred images (sigma 2 px, CIE76): **3.33** (target ≤ 6; PASS), at zero offset over 11572 overlapping pixels including base. Information only: raw per-pixel ΔE 7.22; at the IoU offset blurred 3.33, raw 7.22.
- Regions (blurred ΔE): head_crest 3.7, torso 2.6, cloak_spear_side 4.3, shield 2.2, legs 2.6, feet 5.4, base 3.2.
- Painting mask: alpha; frames: idle 8, move 8, attack 10, hit 4, death 10.
- Rest: `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r14a/preview/rest/00.png`. Contact sheet uses `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r14a/review/3d-v2/spearman-decoded-160`.

