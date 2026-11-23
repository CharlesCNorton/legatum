# True-3D comparison — pass 1

## Verdict

Useful evidence for volumetric animation, **not replacement-ready art**. The 3D
spearman has real thickness, changing occlusion, articulated knees/elbows, a domed
aspis and a body that folds onto the stationary stone. Relief still wins clearly
on paint fidelity, anatomical finish, helmet detail and the richness of the bronze.
The procedural model reads as a simplified miniature beside the original painting.
It has the same identifiable kit and pigment family, but is not an exact visual
match. Do not replace the game's painting with this asset yet. The smaller atlas
is not evidence of a 3D size advantage at equal quality: this model contains less
painted detail. These judgments come from rendered pose sheets; browser playback
and cadence remain unverified.

| Clip | 3D versus pass-2 relief | Remaining limitation |
| --- | --- | --- |
| Idle, 8 frames | Modest gain: chest rise, lateral weight shift and shield perspective change; no exposed flat-card seams | At 64 px the breath remains subtle. Relief is much more convincing as a painting. |
| Move, 8 frames | Clear gain: alternating lifted feet, bent knees, body bob, arm/shield counter-motion | In-place march still has some foot sliding; it needs animation polish, not just more samples. |
| Attack, 10 frames | Clearer whole-body action: lowered pelvis, bent front knee, forward lean, shield drawn in, spear thrust and recovery | The long horizontal spear uses most of the cell; weapon acceleration and the grip silhouette remain mechanical. |
| Hit, 4 frames | Strong gain in legibility: torso/head recoil and shield turn are visible at 256 and 64 px | The snap is deliberately broad; the four-frame recovery is abrupt. |
| Death, 10 frames | Strongest structural gain: knees fold, torso reclines in depth, head curls and kit settles with three identical final poses | A staged collapse, not a physical simulation. The final body/kit pile still needs better anatomical staging. |

Horseman was inspected in the supplied pass-2 sheet: its relief death still reads
as a card tipping over. No horseman-3d was attempted; there is no rendered 3D horse
comparison and no claim that a gait or buckling fall has been solved.

## Build and visual iterations

All work is under `tools/art/anim3d/`, the two requested spearman-3d delivery assets,
this note, and a six-line comparison addition to the existing gallery. No relief
Python/build/pass scripts, app runtime, rules, pins or learnings files changed.

1. Built closed mesh body/limbs, bronze cuirass/greaves, Corinthian-style helmet,
   curved red crest, convex sunburst aspis, spear, thickened red cloak and cream
   stone. A parented armature carries all held kit. Analytic two-bone targets bend
   knees and elbows; all forty poses are baked into the editable `.blend`.
2. First eight-pose CPU preview: rejected the face-on shield, squat framing,
   uniform bronze and seated death. Images retained in `masters/spearman-3d/iteration-1/`.
3. Second preview: narrowed the shield, strengthened painted glazes and lowered the
   collapse. Inspected every selected PNG, including attack, hit and death.
   Images retained in `iteration-2/`. The model still looked too much like a toy.
4. Tried source-paint projection; rejected blotchy armour caused by crop edges and
   overly strong baked shading. Replaced those crops with clean, blended pigment
   patches, lowered/inset the shield, adjusted camera elevation/base framing and
   restored the spear height. Inspected the revised PNGs against the painting.
5. Full-frame checks caught the spear butt leaving the cell and knees/helmet/shoulder
   passing below the stone. Changed the lowering path, knee/elbow bend directions,
   head curl and sandal height. The final build rejects those geometric failures.
   Reviewed decoded delivery frames alongside relief at native 256 and 64 px.

Paint maps are script-painted strokes and sampled/projected colour from the
checked-in painting; the shield sunburst is script-drawn. Diffuse, rough shading
with a small emission fill and texture bump avoids shiny plastic. It does **not**
reproduce the original's detailed hand-painted light, anatomy or metalwork.
The stone receives real soft contact shadow. It has no animated transform.

## Delivery and checks

- **spearman-3d.webp: 159,036 bytes**, quality **80**, all **40** frames.
- **spearman-3d.json: 308 bytes**. Exact existing format/anchor `(127,221)`.
- Atlas **2560 × 1280**, 256 px cells, 8/8/10/4/10 frames; fps 10/12/14/12/10.
  Only idle and move loop. No frame decimation or quality below 60.
- Comparison relief spearman: **179,524 bytes**; unchanged horseman: **198,592 bytes**.
- Final render: **Cycles CPU, 16 samples, four threads**, one Blender process at a
  time under the shared lock. `nice -n 10` was invoked; the sandbox rejected the
  priority adjustment. Blender's thumbnail-cache write warning was nonfatal.
- End-to-end `RENDER_ENGINE=CYCLES SAMPLES=16 tools/art/anim3d/build.sh spearman`:
  **passed**, including saved-rig audit, rendering, packing and decoded validation.
- Rig audit: **40 poses passed**; max joint gap **2.39e-06** Blender
  units; spear/grip gap **2.53e-07**. All evaluated mesh vertices stay
  inside the camera; no character/kit mesh extends below z=0.135 (stone top=0.14,
  with beveled edge). Base transform stays fixed throughout.
- Decoded validation: **passed** exact metadata, bytes, opaque/transparent coverage,
  all cell bounds, transparent padding, exposed stationary rim, actual motion in
  every clip and byte-identical raw final three death poses. The edge check compares alpha
  on both exposed front rim sections, allowing real contact shadows to move. An
  initial RGB test was corrected because changing shadow colour is not base motion.
- Python compilation, `bash -n`, JavaScript syntax, local script/asset path checks
  and `git diff --check`: **passed**.
- Browser playback, 300/600-token performance, Eevee rendering and Claude art review:
  **not run**. No Chromium/Metal workaround, AWS, bucket upload, PR or push.
- No Rust/app runtime code changed, so no Cargo, WASM or full app build was run.

## Review files and lead handoff

`~/LegatumRuns/anim-pilot/review/spearman-3d-vs-relief.png` is an equal-size comparison
of the **decoded** atlases, with 64 px silhouettes below every 256 px image. Each
row shows the painting followed by two adjacent relief/3D pose pairs. The same
directory contains `spearman-3d-{idle,move,attack,hit,death}.webp` and the pack report.
The `.blend`, embedded paint textures and all raw renders stay outside git at
`~/LegatumRuns/anim-pilot/masters/spearman-3d/`.

To reproduce the delivered CPU result:

```sh
RENDER_ENGINE=CYCLES SAMPLES=16 tools/art/anim3d/build.sh spearman
```

To test the host's Eevee path (automatically falls back to CPU Cycles on failure):

```sh
tools/art/anim3d/build.sh spearman
```

Serve the repository root with `python3 -m http.server 8000 --bind 127.0.0.1` and
open `/tools/art/anim/gallery/`. The new **Relief vs 3D** section plays all five clips
side by side with the painting at 256, 80 and 64 px. Pause/step affects each pair.
Its independent shadow DOM works even if another relief unit is missing. The lead
still needs to inspect browser playback at both viewport sizes, review the Eevee
result if used, and obtain the project's Claude art verdict before any merge.

The useful next investment is a better sculpt/paint pass on this rig, especially
helmet, hands, cuirass and cloak folds. Adding a horse before that would expand the
experiment without resolving its largest weakness: source-art fidelity.

## Final gate and commit handoff

- `git add` failed with exit **128**: the sandbox denied creating the worktree's
  `index.lock`. The chained commit was therefore not attempted. All requested
  changes remain uncommitted for the runner; no alternate index or bypass was used.
- `python3 tools/gates/check.py HEAD --base origin/master --checks-only --skip art`
  returned **1**. `public-claims: PASS`; hygiene flags the **pre-existing**
  `tools/art/anim/review/pass-1.md:91`, where a quoted Python matrix multiplication
  has no spaces around the at-sign and is mistaken for an email address. That
  relief-lane file was left untouched. This command reads committed HEAD and does
  not certify the new uncommitted files.
- Direct hygiene checks over all **12 new/changed text files: 0 findings**.
  Python/Bash/JavaScript syntax and `git diff --check` passed. The runner should
  rerun the committed-tip gate after committing and resolve the inherited false
  positive with the relief lead.
- `HEAD...origin/master`: **6 ahead / 0 behind**. No fetch, merge or push was needed.

Stage only `tools/art/anim3d/`, `tools/art/anim/gallery/index.html`,
`tools/art/anim/review/3d-pass-1.md` and the two `spearman-3d` atlas/JSON files.
Suggested commit:

```text
Add a volumetric spearman animation comparison

Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>
```
