---
name: legatum-unit-3d
description: Build and refine Legatum's painted 3D miniature units in Blender from an existing unit painting, using the anim3d kit (MPFB body and rig, frozen painting projection, camera-only pigment, open motion retargeting with foot locking, five sprite-atlas clips, critique). Use for unit look development, deformation, motion, render QA and round reviews.
---

# Painted miniature units

The painting is the art target. The goal at rest: a viewer can barely tell the render from the painting at 256, 160 and 64 px. A passing audit, atlas or metric is never art approval; only the lead writes PASS.

Every rule below is tagged:

- **[proven]** used on a shipped Spearman round, with the evidence that kept it.
- **[rejected]** tried and measured worse. Do not retry without a new reason.
- **[untested]** from the technique study or a probe only. Prove it with a same-settings A/B on one unit before relying on it.

Settings are the Spearman's working values. Sample each new painting before copying a colour, camera or light.

## Ground rules

- [ ] Run every Blender command as `blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python <script>` through the `blender` on PATH (machine-wide gate: one process, 3 threads, retries crashes). Never call the app directly, pass `-t`, or touch the gate's locks. Source `tools/art/anim3d/env.sh` first (isolated Blender resources, `ANIM_ROOT`, `TMPDIR`).
- [ ] Never hide an object by scaling it to 0 or near 0; key `hide_render` instead. **[proven]** zero-scaled smoke meshes crashed Cycles (OpenVDB ScaleMap, SIGABRT).
- [ ] Heavy files (`.blend`, textures, caches, frames, `.glb`) stay under `ANIM_ROOT` (`~/LegatumRuns/anim-pilot`). Git holds code and small presets only.
- [ ] Licences for this public repo: CC0 or CMU free-use motion only; no Mixamo, nothing paid. Record URL, version, hash, action and licence in `units/<slug>/SOURCES.md` and `assets/SOURCES.md`.
- [ ] Work on copies. `project.py` keeps `projection-input.blend` and restarts from it, so repeat runs do not accumulate edits. Keep the painting in the game until the lead approves.
- [ ] Load the installed `blender-*` skills for general operations; this skill overrides them where they differ (Standard view transform, no depth of field, unlit pigment).

## Start a new unit (skateboard first)

Get a crude unit through all five clips and the atlas before polishing any stage. Read `tools/art/anim3d/kit/README.md`, copy `kit/presets/spearman.json` to `<slug>.json`, and build in this order. Each increment ends with a render the lead can look at.

1. Clay figure on the cream base, camera matched, compared with the painting (steps 1–2).
2. Frozen projection plus flat fills for unseen surfaces (steps 3–5).
3. Open motion on all four donor clips, plus a blocked attack; feet check (steps 7–8).
4. CPU preview atlas, movie and `critique.py` numbers (steps 9–11).
5. Only then iterate on the worst visible gap, one variable at a time.

## Checklist

### 1. Lock painting, camera, base and silhouette in clay

- [ ] Write a receipt per iteration: painting and master hashes, Blender build, camera matrix and ortho scale, lights, view transform, source actions, samples, seed. A/B pairs must share all of it.
- [ ] Camera: orthographic, fixed for all five clips, no per-frame fitting, depth of field off. Spearman: location `(2.5, -7, 3.0)`, target `(0, 0, 1.2)`, `ortho_scale 2.9` (`kit/studio.py: match_camera`). Give the figure the same frame height as the painting so 64 px tokens compare 1:1.
- [ ] Base: one stationary cream stone disc for every unit, top **#E9CFA0**, side **#B68A51**, roughness **0.86**, fine low-contrast grain, top at **z = 0.105 m**. Convert sRGB to linear before setting shader values. Never project the figure painting onto the base (painted feet and shadows would stay when the real feet move); give it camera-only cream pigment with live physical contact shadows. **[proven]** R6 with this base and a re-fitted camera: IoU 0.8644 → 0.8772, RGB error 30.3 → 25.4.
- [ ] Match the silhouette in clay before any texture: base ellipse, height, helmet and crest, shield contour and boss, hands, knees, stance, footwear. Surface detail cannot repair a wrong pose or contour. **[proven]** every IoU gain so far came from geometry or pose (R4 0.8394 → 0.8511 shield and crest; R9a 0.880 → 0.898 shield top, cloak tails, shoulder).
- [ ] Fix a narrow or thin lower body with **pose and surrounding anatomy first**: rotate the whole foot+ball pair about the vertical in the authored guard (Spearman: left 55°, right −12°), solve the leg chain to the real planted ankle at fixed bone lengths, and grow calf and greave mass radially in rest coordinates, excluding foot-weighted vertices. **[proven]** R10a: lower-leg IoU 71.96% → 73.21%, sole span 68.98 → 77.03 px, foot geometry, weights and bind hash-identical.
- [ ] Never widen, splay, yaw or camera-ray-shift a foot mesh to imitate the painted footprint. **[rejected]** R1–R8 "duck feet" (Sam). Larger distal greave flare and a more outward knee pole are also **[rejected]** (R10a: both lowered overlap).
- [ ] Rigid kit: finish silhouette, thickness, bevels (1–3 mm, 2–3 segments at 1.7 m body scale) and relief before projection. Check relief on the **evaluated** shell: every raised element needs positive face-centre clearance above its Solidify surface (Spearman minimum 6.59 mm over 12 shield rays). **[proven]** R5/R6: rays were buried 8.4 mm inside the shell until checked on evaluated faces.
- [ ] Review at native 256, 160 and 64 px with split and 50/50 crossfade. Judge figure and base separately: the matching base inflates whole-image IoU.

### 2. Body and rig

- [ ] Default body: MPFB 2 with macro overrides, `game_engine` skeleton, original MPFB weights (`kit/human.py: create_body`, `add_rig`). Spearman: 19,158 vertices, 53 bones. Do not re-weight the skin automatically.
- [ ] Before fitting vertices on the projection copy, **bake the active macro shape-key mix** into that copy (`kit/human.py: freeze_macro_mix`). **[proven]** R6: 25 active macro/muscle keys silently overrode direct `data.vertices` edits, leaving feet below the sole through several "fixes". Keep the morphable original; add new shape keys only after the freeze.
- [ ] Skin sandals and soles to foot **and** ball bones; an ankle-parented sandal cannot toe-off. New footwear geometry needs its own evaluated floor check (R10a welt minimum z 0.1069 m over the 0.105 m stone).
- [ ] Bind rigid helmet, shield and weapon to one bone, preserving `matrix_world`. When rebuilding a released equipment transform from a quaternion, preserve its scale (R4).
- [ ] MPFB may add `Armature` plus `Armature PV` (Multi Modifier, `mhmask-preserve-volume`). That pair is intended; do not delete it or require exactly one armature modifier.
- [ ] **[untested]** Rigify (`add_rig(..., rigify=True)`, 930 bones via MPFB's own generator) is opt-in for a new unit. Never migrate a unit with working motion; no Rigify retarget map exists yet.
- [ ] **[untested]** Correctives: `add_hinge_corrective` drives authored **rest-space** deltas from one local hinge axis (starts 45°, full ~105°). Shape keys evaluate before the armature, so never paste a posed sculpt into a key. No anatomical corrective has been sculpted yet; the Spearman shoulder shell in hit and death is the open case (R10 gap 1).

### 3. Freeze the painting projection at the fitted rest pose

- [ ] Finish static geometry and the rest pose first, then `kit/projection.py: freeze_projection` writes the `Painting camera rest` UV layer and the `Painting visibility` corner attribute on original topology. Evaluated points must keep original vertex indexing. Never reproject per frame or on camera movement.
- [ ] Decide visibility by **ray distance from the camera**, not normal direction: a point is visible when the first hit is within tolerance (Spearman 18 mm; 140 mm for relief sitting on a painted shell). **[proven]** R4: a normal-direction test blanked the shield because the shell winding was reversed.
- [ ] Facing weight: `clamp((|N·V| − 0.02) / 0.18)`; absolute value so double-sided cloth and open armour shells are painted on their camera side only.
- [ ] Register raised ornament laterally **and** on the curved support surface before projecting, or the painting's ornament doubles and smears (R3 shield, fixed R4 by aligning the boss to (163,139) on the 256 px painting).
- [ ] Changing the master invalidates every clip, grade and atlas. Rebuild them; never relabel hashes. **[proven]** R10b's audit correctly rejected stale clips copied from the old master.

### 4. Cover what the painting never shows

- [ ] Before repainting a pale patch that appears in motion, render a **material-ID image** of that pose (`kit/ab.py: material_id_render`) and find which surface it is. **[proven]** R10b: the hit/death shoulder patch was the linen sleeve, not the cape; cape-only paint did nothing.
- [ ] Fill by garment region with broad, coherent colour masses (rear shoulder facing, warm linen folds, skin, darker cloak folds). Keep trusted hero paint where visibility is high. **[proven]** R10b: pale shoulder pixels at peak hit 102 → 24 (256 px), 39 → 7 (160 px); rest shoulder error 12.06 → 12.20/255 (kept: a motion win at near-zero rest cost).
- [ ] More noise, weave or micro-bump does not fix a plain or angular surface, and is not visible at 64 px. **[proven]** R9b: hammer/weave/grain gave a modest gain at 256 only. Spend the effort on shape and broad value first.
- [ ] Seams: `kit/seams.py: underpaint` extends trusted paint up to **75 mm** along mesh edges (geodesic Dijkstra), never across a gap, and stores colour and weight in a corner attribute. It only softens transitions; it does not author missing back or underside art.
- [ ] Generated fills for backs and undersides: record prompt and hashes (`fills.prompt.txt`, `fills.lock.json`), keep source PNGs under `masters/<slug>/textures/generated/`.
- [ ] Image buffers: a byte-backed sRGB image read through bpy gives encoded values; linearise **once** before writing a `FLOAT_COLOR` attribute. **[proven]** R10b: skipping this overbrightened rest pigment. Cache rest normals before writing colour attributes.
- [ ] **[rejected]** gating projection by grazing angle or sleeve area compression: worsened rest without reducing the hit patch (R10b).

### 5. Materials: unlit painted pigment, physical secondary rays

- [ ] The projected painting already contains its lighting. Show it to the camera as Emission and let other rays see the physical BSDF: Light Path → Is Camera Ray → Mix Shader. Spearman baseline: 96% painted, 4% physical on projected regions. Never multiply the painting by a second full diffuse or AO pass.
- [ ] Unseen fills: `kit/materials.py: painted_fill` (camera-only pigment at amount **0.65**, shared `Legatum painterly cavity pigment v1` group, AO distance **0.08**, 8 samples, cavity amount **0.65**). Pigment and cavity amount stay editable per material.
- [ ] Bake AO and curvature with Solidify **disabled** (its inside faces share UVs and overwrite the visible surface with darkness) and winding corrected first.
- [ ] Value structure beats saturation. Reviewer on R9: render flatter and more orange than the painting. Add darkness where the painting has it (cloak folds, under the shield, inner thighs, shield rim) and keep bright metal edges; do not raise global saturation. Open on Spearman (R10 gap 4).
- [ ] **[untested]** Eevee NPR ramp material (white Diffuse → Shader to RGB → ColorRamp → Emission) for relightable fills: graph built in the probe, never rendered on a unit. Recipe in "Options not yet proven".

### 6. Light and grade

- [ ] Light like a product shot of a painted miniature: `kit/studio.py: match_lighting` builds disk area lights from the preset. Spearman: warm key upper-left `(-3,-4,8)` 596.75 W size 5 colour `(1,.97,.93)`; cool fill `(4,-2,3)` 77 W size 3; back rim `(-2,3,4)` 132 W size 2 colour `(.7,.83,1)`; world 0.19 grey. Match the painting's shadow direction with the key alone before adding fill and rim.
- [ ] Colour management for a painted source: **Standard**, Look None, exposure 0, gamma 1. **[proven]** probe: cream `(233,207,160)` round-trips exactly in Standard; AgX gives `(190,177,157)`, Filmic `(198,187,161)`.
- [ ] Grade: fit one monotone per-channel histogram match on the **rest** render against the 256 px painting (opaque pixels, alpha > 240, strength **0.80**), bind it to the master hash, and apply the same LUT to every frame (`kit/grade.py: fit_file`, `load`, `apply`; a grade whose master hash is stale is refused). Never fit per frame: colour pumps. Keep raw renders.
- [ ] Before changing the grade, compare raw and graded figure and base regions separately. **[proven]** R8: the grade already improved the figure; the fix was the physical stone, not the LUT.
- [ ] Refit once after any camera, material, light or engine change, then rerender dependent clips.

### 7. Motion: open donors, full rotations

- [ ] Idle, move, hit and death come from **Quaternius Universal Animation Library Standard (CC0)**: `Idle_Loop`, `Walk_Loop`, `Hit_Chest`, `Death01` (`kit/retarget_presets.py`, hashes pinned in `kit/retarget.py`). Only the weapon-specific attack is hand-keyed. **[proven]** R9 replaced hand-built motion and a direction-only CMU reconstruction; Sam had called the old walk "duck feet".
- [ ] Retarget with `kit/retarget.py: prepare`: calibrate `offset = inverse(source_ref) @ target_ref` per bone in the reference pose, **including roll**, parent a helper to each source bone, world-space Copy Rotation onto the target, sample the whole evaluated pose, then bake with `Bone.convert_local_to_pose` parent-first (`apply_matrices`). Joint directions alone lose roll; assigning `pose_bone.matrix` in a loop reads stale parents.

```python
# kit/retarget.py: bake sampled armature-space matrices without stale parents.
for p in rig.pose.bones:  # parent-first order
    args = {'parent_matrix': matrices[p.parent.name],
            'parent_matrix_local': p.parent.bone.matrix_local} if p.parent else {}
    p.matrix_basis = p.bone.convert_local_to_pose(
        matrices[p.name], p.bone.matrix_local, invert=True, **args)
```

- [ ] Locomotion legs calibrate from anatomical rest with the limb axis swung onto the donor's T-pose axis (target roll kept). Reset the guard's leg transforms to bind before mapping, so guard-only foot turns never leak into the walk. Upper body keeps the weapon guard with the donor delta layered on it.
- [ ] A shield or spear carrier cannot swing both arms: layer the donor's `Idle_Loop` arms over the walk with an NLA strip on a copy of the source rig.
- [ ] Tame a stylised donor by attenuating the **whole source action in its own rest space before retargeting** (NLA strip influence). Spearman walk: **0.90**. **[rejected]** 0.88 (root correction 54.8 mm, over the 50 mm bound) and 0.82 (stance split into two intervals). Contact quality is not monotonic in attenuation; reject a setting rather than loosen a check. Gain is modest (peak ankle 430.6 → 422.6 mm); a less stylised donor is the better fix if the walk still reads as a march.
- [ ] Death: remap donor time to separate knee yield from torso descent (`source_phase`), blend from the guard into the donor over the first **18%**, and blend the donor's **own** settled leg pose and `Idle_Loop` arms (85% shield arm, 65% free arm) in source space during recoil. No new joint keys. **[proven]** R10c: largest head step 1.277 → 0.655 m, peak ankle 0.848 → 0.355 m. Timing alone did not remove the feet-up recoil.
- [ ] Death staging (reviewer): knees give, torso falls, ends lying across the base with the shield still on the arm and the spear dropped beside him. Register the donor's fall toward the disc centre (Spearman 0.40 m).
- [ ] Hit: sample the donor recoil over the first third (`phase*3`), then blend back to idle over the last 70% so four frames do not snap.
- [ ] Attack: start and end on the idle guard, **including elbow IK poles**, not only hand targets (R7).
- [ ] Carried equipment stays parented at its grip; add a geometry-triggered hinge about the grip that rotates only enough to clear the floor. **[proven]** R10c: grip distance range 1.142 m → 0.0000002 m. Still open: the shield turns 83° between two delivered samples; measure equipment rotation per delivered frame (`kit/motion_metrics.py`), not just attachment.
- [ ] Cloth: one second of pre-roll and a persistent bake per clip; full shoulder pins. Death keeps 35% partial pins, bending stiffness 0.8, air damping 4 (R10c: late cape travel 0.419 → 0.119 m). **[rejected]** loosened hit cloth pins: raised a cape corner behind the shoulder at recovery (R9).
- [ ] Secondary motion (crest, shield sway) is a damped spring driven by carrier acceleration, capped (crest 16 mm), not a second keyed performance.
- [ ] Clips: idle/move/attack/hit/death = **8/8/10/4/10** frames at **4/6/14/12/4 fps**; idle and move loop; move keeps the donor's 1.33 s cycle. Render the final death sample once and copy it byte-for-byte.

### 8. Foot locking and the feet check

- [ ] `kit/retarget.py: stabilize_walk` locks heel strike, flat stance and toe-off from evaluated **sole landmarks** (`kit/contact.py`, `toe_vertex` and `heel_vertex` custom properties on each sole object), fits **one** virtual forward speed over all support intervals (search 0.75–1.25× the donor's median stance speed), keeps support across the loop seam, and applies the correction as a shared root offset plus two-bone IK per foot with source foot rotation held by a world Copy Rotation (`contact_ik`). Foot rotation is never edited after the retarget.
- [ ] Contact classification on the donor: ankle within 15 mm or toe within 12 mm of its cycle minimum while moving backward. Exactly one support interval per foot per cycle, or the gait is broken.
- [ ] Enforced limits on the delivered walk (`units/spearman/feet.py`): compensated sole slip ≤ **1 mm**, planted floor error ≤ **2 mm**, planted and readable heading ≤ **10°** from travel, loop seam ≤ **3 mm**, root and foot-IK correction ≤ **50 mm**, sole translation ≤ **40 mm**. Spearman R10: slip 0.0018 mm, floor 1.133 mm, heading 2.618°, seam 0, root 48.97 mm, IK 19.95 mm. Treat heading above 5° or a correction above 30 mm as a warning to investigate.
- [ ] For an in-place sprite, measure slip on `foot(t) + virtual_displacement(t)`, not raw foot motion over the still disc. Heading is ill-conditioned when a raised foot projects under 8 cm on the ground; gate it to planted and readable footprints.
- [ ] Every round: render the real lower legs from the top and front over the whole cycle to `<slug>-g-feet-check.png` (≥ 32 dense samples) and look at it. Bone positions and a passing metric do not prove sole contact.

### 9. Render

- [ ] CPU preview for every A/B: Cycles CPU, **256 px, 16 samples, seed 17**, denoising and adaptive sampling off (`kit/ab.py: preview_settings`), identical camera, lights and **one fixed LUT** on both sides. Stage renders (`render.py`) keep denoising on with adaptive threshold 0.025; never compare across the two. Label CPU and GPU evidence; never claim one from the other.
- [ ] For a change that claims to touch only materials or only motion, hash everything else before and after (`kit/ab.py: invariant`: geometry, weights, UVs, pose, actions, camera, lights) and assert equality. **[proven]** R10a and R10b shipped with these invariants identical to R9.
- [ ] Final: `RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU CYCLES_BACKEND=METAL RESOLUTION=512 SAMPLES=64 GRADE=1`, transparent RGBA. A preflight fails fast if no GPU is exposed rather than falling back to CPU.
- [ ] Keep 512 px masters and a derived 256 px set under `masters/<slug>/{512,256}/`. Derive 256 and 160 from the 512 masters, never by upscaling.
- [ ] Downsample in **linear light with premultiplied alpha**, before trimming (`kit/images.py: resize_rgba`, Lanczos). A straight sRGB RGBA resize fringes edges.
- [ ] Motion blur, depth of field and bloom off; dither 0 for colour tests.

### 10. Deliver and verify the decoded atlas

- [ ] Atlas: 160 px logical cells, per-frame alpha trim with offsets, shared anchor (no per-crop recentring), 2 px gutters, WebP quality ≥ 75, **≤ 200,000 bytes**, all 40 records. Spearman R10 CPU preview: 183,016 bytes at q80. If it does not fit, report it; do not drop frames or quality silently.
- [ ] Pack and validate with `python -m kit.deliver` (`kit/atlas.py`): it rebuilds logical cells from the **decoded** atlas and checks alpha, offsets, gutters, bounds, frame counts, timing, motion and the held death. The unit script adds the hash checks (master, grade, render manifests current). Write CPU previews to a lane folder, never to `app/src/assets/units/anim/`. **[proven]** the kit packer reproduces the Spearman R10 atlas byte for byte.
- [ ] Judge "this clip moves" on the lossless reduced source frames. Lossy WebP makes identical tiles decode differently, so a decoded-pixel difference test passes a static clip (found while testing `kit/atlas.py`).
- [ ] Movie: all five clips side by side on cream at 2×, 1600×352, H.264 yuv420p, 24 fps, 8 s, written to `review/3d-v2/<slug>-round<N>.mp4`.
- [ ] Pose audit over all 40 saved poses (`kit/audit.py`): equipment crossings, camera bounds, contact against the real disc footprint plus world ground (not an infinite plane), arm joints within 2 mm of idle at clip entry and exit. Zero findings required. Tighten a check when it misses something; never loosen one to pass.

### 11. Critique, A/B and stop rules

- [ ] Run `critique.py` every round (it appends its numbers to the round note above the FOCUS lines):

```sh
$ANIM_ROOT/venv/bin/python tools/art/anim3d/critique.py --slug <slug> --round <N> \
  --label 'CPU 256 px / 16 samples' --painting app/src/assets/units/<slug>-256.png \
  --rest <rest.png> --frames <decoded-160-dir> --feet <feet-check.png> --out $ANIM_ROOT/review/3d-v2
```

- [ ] Targets: silhouette IoU ≥ **0.95** (best of ±3 px offsets, alpha > 8), mean CIE76 ΔE ≤ **6** over the overlap. Both include the base. Spearman R10: 0.9022 and 13.81, both fail. These numbers are not comparable with the older unshifted, threshold-32 IoU (R10 on that scale: 0.8989).
- [ ] Report regional and global numbers together, wins and losses (`python -m kit.regions --painting P --before A --after B --region name=x0,y0,x1,y1 --pale name=x0,y0,x1,y1`; the Spearman boxes are in `kit/presets/spearman.json`). **[proven]** R10 kept three regional wins while whole-image IoU fell 0.9035 → 0.9022 and fixed-grade ΔE rose 13.74 → 13.91; that was disclosed, not hidden.
- [ ] One variable per A/B, so a win can be attributed. Port lane changes by scoped diff, not whole-branch merge.
- [ ] Look at the images: rest at 256/160/64, hit and death strips, all 40 decoded cells, feet sheet, movie samples. Reject seam popping, swimming texture, doubled ornament, bright unpainted backs and foot drift even when every number passes.
- [ ] Each round note ends with a ranked list of visible gaps and three FOCUS lines (a: form, b: surface, c: motion). Add the round to `tools/art/anim3d/LOG.md` with time spent and metric before/after.
- [ ] Never write a PASS file because a render or audit completed.

### 12. Lane hygiene (saves a round each time)

- [ ] Codex sandboxes cannot take `index.lock` or `ORIG_HEAD.lock`: leave changes uncommitted with a `commit-message.txt` and a lane-only patch; the runner commits. Do not work around the lock.
- [ ] Keep lane masters and CPU atlases in `lanes/<slug>-r<N><lane>/`; never overwrite the shared master or the checked-in atlas from a lane.
- [ ] `critique.py` must exist in the lane checkout before the task asks for it (R10 lanes could not run it). Merge the skill branch first.
- [ ] Record rejected experiments with their numbers in the lane note; they are as reusable as the wins.

## Options not yet proven on a unit

Try one at a time, on a copy, with a same-settings A/B. Move it into the checklist with its evidence if it wins; delete it if it loses.

- **Eevee NPR fill material.** White Diffuse BSDF → Shader to RGB → RGB to BW → ColorRamp (EASE, 3–5 sampled colours) → Emission. Eevee only, needs a GPU context. Example bronze ramp positions 0.12/0.42/0.70/0.94, sRGB #432518/#895121/#CA9741/#F4D893 (replace with medians sampled from the painting). Stroke noise through Bump (strength 0.15, distance 0.003 m) on UV → Mapping scale (6, 36, 1) → Noise scale 2; strokes 1–3 final pixels wide or they shimmer. Fixed seeds and UVs only.

```python
import bpy
def linear(c): return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
mat = bpy.data.materials.new('NPR-bronze-fill'); mat.use_nodes = True
n, links = mat.node_tree.nodes, mat.node_tree.links; n.clear()
diff = n.new('ShaderNodeBsdfDiffuse'); diff.inputs['Color'].default_value = (1, 1, 1, 1)
rgb = n.new('ShaderNodeShaderToRGB'); bw = n.new('ShaderNodeRGBToBW')
ramp = n.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation = 'EASE'
stops = [(.12, (67, 37, 24)), (.42, (137, 81, 33)), (.70, (202, 151, 65)), (.94, (244, 216, 147))]
for i, (pos, col) in enumerate(stops):
    el = ramp.color_ramp.elements[i] if i < 2 else ramp.color_ramp.elements.new(pos)
    el.position = pos; el.color = tuple(linear(c / 255) for c in col) + (1,)
emit = n.new('ShaderNodeEmission'); out = n.new('ShaderNodeOutputMaterial')
links.new(diff.outputs[0], rgb.inputs[0]); links.new(rgb.outputs['Color'], bw.inputs[0])
links.new(bw.outputs[0], ramp.inputs['Fac']); links.new(ramp.outputs['Color'], emit.inputs['Color'])
links.new(emit.outputs[0], out.inputs['Surface'])
```

- **Multi-view paintovers baked to a surface unwrap.** Keep a packed `PaintUV`; one projector, UV layer and image per view (`ProjectFront`, `ProjectSide`, `ProjectBack`), all registered to the same neutral pose; weight `visible * inside * alpha * smoothstep(.25,.65,N·V)^4`; blend low-frequency colour over 8–16 texels at 1024 and hand-author seams through eyes and ornament. Bake with Cycles CPU `bake(type='EMIT')`, 1–8 samples, margin 16 px at 1024, `margin_type='EXTEND'`, a plain-emission source material (a camera-ray switch is not a valid bake source), destination image selected but unconnected in every material. Do not project the hero painting from several directions or mirror insignia onto the back. Probe only: convex checker test, 0.80/255 error; no occlusion or deforming-seam proof.
- **Selective rim.** Large area rim, or shader rim `(1−max(N·V,0))^4 * max(N·L_rim,0)` mixed at 0.03–0.08 on the lit silhouette only; keep it off painted highlights.
- **Pose-space correctives.** Blender Studio's Pose Shape Keys extension (GPL) turns a posed sculpt into a rest-space key; start elbow and knee correction at 45°, full near 100–110°, separate left/right shapes. Corrective Smooth after the armature (factor 0.2, 5 iterations, joint mask) is cleanup, not volume.
- **Other donors and tools.** CMU mocap (free-use, **not CC0**; credit CMU/NSF EIA-0196217, record the converter) for a less stylised walk. Rokoko's LGPL add-on for retargeting only if it runs locally without a login. Brushstroke Tools (GPL) for a small cloak patch. Rain, Snow and Einar rigs (CC-BY 4.0, Blender Studio) as study references only; credit if any data is reused.
- **Cycles final settings to test.** Adaptive threshold 0.01, min 16 samples, bounces 6 (diffuse 2, glossy 2, transparent 8); compare OIDN on and off at 160 px, since denoising can smear painted strokes.

## Probe

`scripts/technique_probe.py` (synthetic sphere and rig, Blender 5.3.0, Cycles CPU) checks mechanisms only: frozen UV Project layers stay byte-identical after camera movement; Standard round-trips cream exactly; reference-offset Copy Rotation plus `convert_local_to_pose` gives 0 rad error with a 0.7 rad rest-roll mismatch; a hinge driver evaluates 0.5 at half range; stock Rigify generates. `kit/probe_human.py` checks MPFB 19,158 vertices, 53-bone game rig and 930-bone Rigify with `Armature PV`. Neither certifies art. Details: `references/verification.md`.

```sh
blender -b --disable-autoexec --factory-startup --python-exit-code 1 \
  --python tools/art/anim3d/scripts/technique_probe.py -- --output /tmp/legatum-unit-3d-probe
```

## Sources and licences

Recheck the licence file of anything downloaded.

- Blender (GPL) and manual (CC-BY-SA 4.0): [Shader to RGB](https://docs.blender.org/manual/en/4.5/render/shader_nodes/converter/shader_to_rgb.html), [UV Project](https://docs.blender.org/manual/en/latest/modeling/modifiers/modify/uv_project.html), [baking](https://docs.blender.org/manual/en/4.5/render/cycles/baking.html), [colour management](https://docs.blender.org/manual/en/4.5/render/color_management.html), [Bone.convert_local_to_pose](https://docs.blender.org/api/current/bpy.types.Bone.html#bpy.types.Bone.convert_local_to_pose).
- [MPFB](https://github.com/makehumancommunity/mpfb2): code GPL-3.0-or-later, bundled body and assets CC0; [Rigify workflow](https://www.makehumancommunity.org/mpfb/docs/rigging_posing/rigify.html).
- [Quaternius Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html): CC0, free Standard subset only.
- [CMU Graphics Lab mocap](http://mocap.cs.cmu.edu/): free-use, no resale of the data, **not CC0**.
- [ambientCG](https://docs.ambientcg.com/license/) and [Poly Haven](https://polyhaven.com/license): CC0 textures. Spearman uses Metal034, Fabric030, Travertine001, brown_leather, fine_grained_wood (pinned in `assets.lock.json`).
- Study references: [Brushstroke Tools](https://extensions.blender.org/add-ons/brushstroke-tools/) and [Pose Shape Keys](https://extensions.blender.org/add-ons/pose-shape-keys/) (GPL-3.0-or-later); [Rain](https://studio.blender.org/characters/rain/v3/), [Snow](https://studio.blender.org/characters/snow/v2/), [Einar](https://studio.blender.org/characters/einar/v1/) (CC-BY 4.0, Blender Foundation); [Rokoko add-on](https://github.com/Rokoko/rokoko-studio-live-blender) (LGPL-3.0, not exercised).

## Learned

One line per finding, newest first; the rule itself lives in the step named in brackets. Full numbers are in `LOG.md` and the round notes. Round agents: add one dated line here, edit the step it changes, and delete any rule it contradicts rather than leaving both.

- 2026-11-24 kit: `grade`, `atlas`/`deliver` and `regions` reproduce the Spearman R10 LUT, atlas and regional numbers exactly; a decoded-pixel motion test passes a static clip under lossy WebP. [10, 11]
- 2026-11-23 R10 (merge): report regional and whole-image metrics together; R10 kept regional wins with a small global regression (IoU 0.9035 → 0.9022). [11]
- 2026-11-23 R10a: a narrow sandal was a guard-orientation and calf-mass problem, not a foot-size problem; flare and outward knees rejected. [1]
- 2026-11-23 R10b: material-ID render first; the pale patch was the sleeve. Linearise byte images once. Grazing-angle gate rejected. [4]
- 2026-11-23 R10c: blend the donor's own settled pose in source space; walk influence 0.90, 0.88 and 0.82 rejected; grip-preserving shield hinge. [7]
- 2026-11-23 R9: full-rotation Quaternius retarget with heel/toe locking replaced hand-built motion; loosened hit cloth pins rejected; microtexture gain modest. [4, 7, 8]
- 2026-11-23 R8: compare raw and graded regions before touching the grade; fix the stone, keep the LUT. [6]
- 2026-11-23 R7: matching hand targets does not match the arm; elbow poles must share the guard. A moved base needs contact tests in its own footprint. [7, 10]
- 2026-11-23 R6: active MPFB macro shape keys override direct vertex fitting; bake the mix on the projection copy. Audit against the real disc footprint. [2, 10]
- 2026-11-22 R5: check relief clearance on evaluated faces, in plain clay as well as painted. [1]
- 2026-11-22 R4: visibility by ray distance, not normals; register ornament before projecting. [3]
- 2026-11-22 R1–R3 (Sam): "looks like something a high school student would make" → projection, geometry finish, product light, one grade; R2 "huge improvement"; walk "duck feet" → open motion. [1, 3, 6, 7]
