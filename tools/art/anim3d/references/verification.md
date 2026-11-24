# Technique study verification

Recorded 2026-11-23. These results establish small mechanisms, not Spearman art approval.
The entrypoint [../SKILL.md](../SKILL.md) is the practical workflow.

## Inputs actually reviewed

- `git show astra/unit-anim-3d-v2:tools/art/anim3d/PLAYBOOK.md`, branch tip
  `042bb19b5cf3c631b4855808de5a409289f38747` at inspection.
- External `review/3d-v2/log.md`, `FEEDBACK.md`, `spearman-FEEDBACK.md` and the
  later `spearman-log.md` through R9a/R9b/R9c.
- `spearman-r9a-256.png`, `spearman-r9b-details.png`, and
  `spearman-r9c-move-compare.png`: the source painting is present in these sheets.
  Registration is close, but source and render still differ in shoulder/hand,
  helmet, shield edge, stance and feet. The material A/B is subtle at token size.
- All six installed Blender SKILL.md files, plus Legatum's art skill and project
  instructions. Their generic Principled-only and photographic colour presets
  were adapted to the requested sprite/NPR workflow.
- Blender/MPFB official documentation and locally installed MPFB implementation;
  free Blender Studio/Quaternius/Rokoko source pages cited in the skill. No
  third-party rig, scene, add-on or artwork was downloaded for this study.

## Reproduction

From the repository root, with MPFB already installed in the pilot's isolated
resources (omit these environment assignments and `--mpfb` for the stock test):

```sh
ANIM_STUDY_ROOT="$HOME/LegatumRuns/anim-pilot"
BLENDER_USER_RESOURCES="$ANIM_STUDY_ROOT/blender-user" \
BLENDER_USER_CONFIG="$ANIM_STUDY_ROOT/blender-user/config" \
BLENDER_USER_SCRIPTS="$ANIM_STUDY_ROOT/blender-user/scripts" \
BLENDER_USER_DATAFILES="$ANIM_STUDY_ROOT/blender-user/datafiles" \
XDG_CACHE_HOME="$ANIM_STUDY_ROOT/blender-user/cache" \
blender -b --disable-autoexec --factory-startup --python-exit-code 1 \
  --python tools/art/anim3d/scripts/technique_probe.py -- --mpfb \
  --output "$ANIM_STUDY_ROOT/review/3d-v2/technique-study"
```

The script operates on its fresh scene, writes seven CPU PNGs, a baked texture,
editable `.blend` and `results.json`. It removes an old success receipt before
starting, so a failed rerun cannot masquerade as current success. Keep logs
alongside the output. It does not save Blender preferences or alter production
assets. The gate limits concurrency/threads; no gate was bypassed.

## Results

- Blender **5.3.0**, build **02f0899d78e3**; Cycles **CPU**, 160², 8 samples,
  fixed seed 11, no denoising, transparent film. ShaderToRGB graph construction
  passed; Eevee rendering deliberately not run because this was CPU-only.
- CPU analytic normal/ramp/bump sphere rendered. The image has coherent warm
  light/shadow masses; brush normal variation at this strength is subtle. It
  is a plumbing test, not a finished hand-painted shader.
- UV Project applied for two orthographic projectors; saved UVs identical after
  camera movement. Two-view colour blend baked with Emit to 256², margin 8.
  Original and baked rest renders have opaque RGB MAE **0.801227/255**, measured
  on pixels opaque in both; a rotated render demonstrates texture attachment.
  Checker boundaries soften slightly through baking/filtering, as expected.
- Strength-1 cream swatch centre pixel: Standard **(233,207,160)**, AgX
  **(190,177,157)**, Filmic **(198,187,161)**. Dither 0, exposure 0, gamma 1,
  sRGB display, None look. This is evidence for Standard on baked illumination,
  not evidence that AgX is wrong for photographic/PBR assets.
- One-bone native retarget: **0.0 rad** reported quaternion error across three
  rotations, including twist, with **0.7 rad** different target rest roll.
  This checks the calibration/constraint/visual-matrix mechanism, not a full
  humanoid bone map or an imported donor clip.
- Corrective driver: **0.49999994** at 45° on a 0–90° ramp. No anatomical
  corrective sculpt was authored or visually certified.
- Synthetic two-bone IK leg: foot head/tail maximum contact drift
  **8.433879e-8 m** over three 0/3/6 cm lateral root positions. This checks
  native IK plus a foot rotation constraint. It does not test skin soles,
  stance detection, toe-off, an in-place donor or loop transitions.
- Stock Rigify generated **706 bones**. MPFB generated **930 bones** on a
  **19,158-vertex** default human; both Armature modifiers target the generated
  rig. No production Spearman conversion was performed.
- Raw MPFB audit found **16 zero-weight vertices**, all hidden helper cubes
  (`joint-pelvis` and `joint-ground`), **zero** on evaluated visible faces.
  The visible raw weight-sum error is approximately **0.0003753**. The probe
  normalizes only deform-bone weights on its synthetic visible body and checks
  the result at **4.866160e-8** maximum sum error (below **1e-4**), preserving
  helper/material/volume masks. The small
  raw rounding error is not evidence of a visible deformation failure.

The seven images were inspected as a contact sheet on cream. The baked texture
and generated scenes remain external; the script is the reproducible artifact.
Production still needs Eevee host A/B, multi-view visibility/seam paint, joint
sculpts, real clip retargeting, dense sole tests and final sprite review.

## Findings that changed the recipe

1. The first MPFB assertion incorrectly required one Armature modifier. MPFB
   deliberately builds a masked **Multi Modifier** preserved-volume pass.
   Both targets were correct. The check now validates that configuration;
   deleting the second modifier would discard intended deformation behavior.
2. The initial all-vertex report included hidden helper geometry; the subsequent
   visible-only check found small source-weight rounding residuals. Check evaluated visibility and only deform groups;
   demonstrate explicit normalization on the test copy without calling the
   source body broken. A saved-scene inspection confirmed the 16 exclusions.
3. Blender 5.3's static render-engine RNA enum listing returned only Eevee even
   though assigning and rendering with `CYCLES` worked. Do not use that listing
   alone as a capability verdict; test the requested setting and operation.
4. Shader graph creation is not a rendered Eevee test. The CPU normal-dot-light
   fallback is useful for palette experiments but does not replicate the real
   Eevee light/shadow response.
5. Public search snippets describe the Fishing Hut attachment on a free lesson.
   The live attachment link actually points to `/join/` and says subscription
   required. The skill uses the free lesson and GPL extension instead. Rain v3
   and Snow v2 expose free download links and CC-BY **4.0** licence links.
6. CMU's live site was reachable over HTTP with a normal browser user-agent
   after the web fetch timed out. Its actual terms distinguish commercial use
   from direct dataset resale. Do not relabel CMU motion CC0.

The platform's `nice: setpriority: Operation not permitted` and Blender's
Material.use_nodes deprecation warning were nonfatal. No GPU success, complete
Spearman validation, purchased tool, upload or art PASS is claimed.
