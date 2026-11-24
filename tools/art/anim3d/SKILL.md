---
name: legatum-unit-3d
description: Build and refine Legatum's painted 3D miniature units in Blender from an existing unit painting, using MPFB bodies, Rigify or the existing deform rig, frozen multi-view paint, open motion retargeting, and five sprite-atlas clips. Use for unit look development, deformation, motion, and render QA.
---

# Painted miniature units

The painting is the art target. A good rest render must survive animation, and a passing mesh or atlas audit is not art approval. Work on copies of the body, rig and master; retain the painting in the game pending lead approval. Use free/open software and freely available, appropriately licensed assets. The numerical settings below are **starting presets**, except the established atlas contract. The verification section distinguishes tested mechanisms from proposed production work.

Read the unit's current playbook, sources and feedback, then inspect its latest rest comparison, details, attack/death strips and top/front feet sheet. In Legatum, resolve `tools/art/anim3d/PLAYBOOK.md` in the active pipeline checkout; the study baseline was `astra/unit-anim-3d-v2`. Do not copy historical round recipes over newer fixes. Load the relevant installed `blender-*` skills for general operations, but adapt their photographic/glTF presets to this sprite target: Shader-to-RGB is appropriate, depth of field is usually off, and Standard can be preferable to AgX.

Run **every** Blender command through `blender` on PATH with `-b --disable-autoexec --python-exit-code 1`; keep previews short and CPU. Do not bypass the gate, replace its locks or supply thread overrides. The gate's current concurrency policy is authoritative. Preserve downloaded-file script restrictions; inspect rig UI scripts before explicitly running any required code. Store masters and review renders outside git, normally under `~/LegatumRuns/anim-pilot/`. This skill does not install itself, publish art, or enable the game's animation renderer.

## Checklist

### 1. Lock the painting, camera and silhouette before adding texture

- [ ] Record painting/master hashes, Blender build, camera matrix and orthographic scale, key direction, view transform, source actions and output settings in a per-iteration receipt. Keep identical settings in A/B comparisons.
- [ ] Match base ellipse, overall height, helmet, knuckles, shield boss, knees and sole contacts. Start orthographic; use perspective only if the painting demands it. Keep a fixed camera and scale through all five clips. Fit all clip bounds with the same camera rather than zooming each frame.
- [ ] Use clay and opaque silhouettes first. For Spearman, prioritize shoulder/hand shape, helmet cheek/crest, shield contour, stance and footwear over microtexture. The R9 comparisons still show these mismatches. Retain anatomical depth and articulation: no camera-facing relief body, foot widening or camera-ray foot displacement.
- [ ] Review landmarks and crossfades at native 256, 160 and 64 px. A suggested registration target is important landmarks within 2 px at 256; this is a diagnostic, not a substitute for art review. Inspect figure and base separately; a large matching base can inflate silhouette IoU.
- [ ] Finish rigid kit's silhouette, thickness, bevels and relief before projection. At a 1.7 m body scale, try 1–3 mm bevels on metal/straps with 2–3 segments; exaggerate only when a necessary edge disappears at 160. Keep organic joint topology stable. Check evaluated faces as well as vertices for shield relief sinking through its convex shell.

### 2. Separate painted illumination from relightable pigment

- [ ] Choose and record the material contract **per region**. Existing projected paint already includes highlights/shadows: preserve it as a mostly unlit illustration layer. New back/underside paint can be authored as pigment and lit with the NPR shader in step 3. A single painting does not uniquely determine albedo, lighting or unseen surfaces.
- [ ] Keep the established source-painted 96% / physical 4% blend as the Spearman A/B baseline, not a universal material recipe. Test 0%, 4% and 10% live response on that region. Do not multiply the painted image by a second full diffuse/AO pass. Also avoid treating a complete lit painting as the colour input to a lighting ramp.
- [ ] In Cycles, route camera rays to painted Emission (strength 1) mixed with the restrained BSDF; route other rays to the physical BSDF using Light Path → Is Camera Ray → Mix Shader. This prevents painted highlights lighting neighbouring skin/base. Use a separate plain-emission material during texture baking: a camera-ray switch is not a valid pigment bake source.
- [ ] Keep the base independent: cream top **#E9CFA0**, darker side **#B68A51**, roughness **0.86**, low-contrast grain. Never project painted feet or cast shadows onto it. Tune its real contact shadows against the painting, not the colour field alone.

### 3. Build a palette-controlled Eevee NPR material

- [ ] For relightable fills, use **white Diffuse BSDF → Shader to RGB → RGB to BW → ColorRamp → Emission → Output**. White diffuse avoids mixing pigment colour into the lighting measurement. Use 3–5 sampled material colours, with warm highlights and chromatic shadows; start with EASE interpolation and transitions spread over 0.05–0.12 of the ramp. CONSTANT bands are a diagnostic/toon variant, not the default painted finish.
- [ ] Example bronze ramp: positions **0.12 / 0.42 / 0.70 / 0.94**, sRGB **#432518 / #895121 / #CA9741 / #F4D893**. These are study colours; replace them with medians sampled inside the actual bronze, excluding alpha fringes and specular outliers. Tune illumination/ramp input so the whole sculpture does not collapse into one band.
- [ ] Add elongated UV-space noise or a painted stroke-height map **before** the Diffuse normal input. Start Bump strength **0.15**, distance **0.003 m** for a metre-scale body; reduce if it looks hammered everywhere. Use Non-Color for height/normal/mask images, sRGB for paint. A tangent normal image uses Normal Map with the intended UV name; do not treat RGB normals as height.
- [ ] Align strokes to form: cloth along folds, bronze around the shield/breastplate, short skin patches along muscles. Use UV → Mapping scale such as **(6, 36, 1)** → Noise scale **2**, detail **2** as a cheap prototype. Set stroke width to roughly **1–3 final pixels**, length **3–8**, then inspect motion. Subpixel weave mostly produces shimmer or disappears. Brushwork needs directional patches and designed edges; isotropic noise alone does not make painting.
- [ ] Fix stroke seeds and UVs. Do not sample animated world coordinates, regenerate random strokes per frame, or use changing generated bounds on deforming anatomy. Bake the colour/stroke layer into PaintUV when stable. For stronger strokes, study Blender Studio's surface-associated curve/mesh-strip workflow (step 8); keep geometry sparse at this resolution.

```python
# New task-owned material only; linear() converts sampled sRGB to shader values.
import bpy

def linear(c):
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4

mat = bpy.data.materials.new('NPR-bronze-fill')
mat.use_nodes = True
n, links = mat.node_tree.nodes, mat.node_tree.links
n.clear()
diff = n.new('ShaderNodeBsdfDiffuse')
diff.inputs['Color'].default_value = (1, 1, 1, 1)
rgb = n.new('ShaderNodeShaderToRGB')
bw = n.new('ShaderNodeRGBToBW')
ramp = n.new('ShaderNodeValToRGB')
ramp.color_ramp.interpolation = 'EASE'
colors = [(0.12, (67, 37, 24)), (0.42, (137, 81, 33)),
          (0.70, (202, 151, 65)), (0.94, (244, 216, 147))]
for i, (position, color) in enumerate(colors):
    el = ramp.color_ramp.elements[i] if i < 2 else ramp.color_ramp.elements.new(position)
    el.position = position
    el.color = tuple(linear(c / 255) for c in color) + (1,)
emit = n.new('ShaderNodeEmission')
out = n.new('ShaderNodeOutputMaterial')
links.new(diff.outputs[0], rgb.inputs[0])
links.new(rgb.outputs['Color'], bw.inputs[0])
links.new(bw.outputs[0], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], emit.inputs['Color'])
links.new(emit.outputs[0], out.inputs['Surface'])
```

**Check:** Shader-to-RGB is Eevee-only; changing this material's engine to Cycles is not a quality upgrade. Its lighting/pass limitations also mean AO, shadow and transparency combinations need rendered checks. On CPU, use a separate preview material with `dot(normal, normalized_key_direction)`, remapped from [-1,1] to [0,1], feeding the same ramp. That analytic version was rendered in the probe; it has no scene-light shadow response and does not verify the Eevee appearance.

### 4. Match light direction; add only a soft, selective rim

- [ ] Define lights in **camera space**. Let `R`, `U`, `B` be camera-local +X, +Y, +Z transformed to world space; +Z points back toward the viewer. For a figure of height H centred at C, start key at `C - 1.5H*R + 2H*U + 2H*B`; aim -Z toward C. This is screen upper-left regardless of world orientation.
- [ ] At H≈1.7 m, start an area key at **500 W, size 2H**, fill at **100 W, size 3H**, rim at **50 W, size 1.5H** behind/right. These are starting energies, not measured image ratios; distance, source size and shader all matter. Key colour `(1,.95,.85)`, fill `(.90,.94,1)`, rim `(.85,.92,1)` are restrained linear tints. Test key only, then fill, then rim. Match painted shadow direction first.
- [ ] Use a large area rim, not a hard spotlight or a full Fresnel halo. If using a shader rim, mask `(1-max(N·V,0))^4` by `max(N·Lrim,0)` and mix at **0.03–0.08**, strongest on the lit silhouette only. Keep it out of source-painted highlights unless it improves an A/B. Avoid a new white outline on every edge.
- [ ] Bake cavity AO/curvature as **editable masks**; keep the long-scale light shape independent. Start cavity influence 0.1–0.2, radius 0.01–0.03 m. Reserve brighter wear for authored exposed edges. Disable Solidify during a bake when its inside and outside share UVs, or give them separate islands. Do not bake the character's cast shadows into its pigment or the base.

### 5. Project multiple views, then bake to ordinary surface UVs

- [ ] Preserve `PaintUV`: a non-overlapping, well-packed surface unwrap, including backs/undersides. Keep source projections in separate named layers (`ProjectFront`, `ProjectSide`, `ProjectBack`). Applying a UV Project modifier freezes coordinates; it **does not bake an image**.
- [ ] The hero painting supplies only the hero view. Make additional side/back/underarm **paintovers** in free Krita, GIMP or Blender Texture Paint: render neutral guide views from fitted geometry, paint broad sampled colour masses, continue cloth folds/edges and add deliberate warm/cool strokes. Do not project the same hero painting from several directions or mirror its face/insignia onto the back. CC0 surface swatches are underpaint, not finished illustration.
- [ ] Use one projector/UV/image per view. Blender's multi-projector modifier selects a projector per face; it does not blend different paintings or solve visibility. Match each guide camera and aspect ratio; keep all source views registered to the **same neutral pose**.
- [ ] For each surface sample, use `w_i = visible_i * inside_image_i * alpha_i * smoothstep(.25,.65,N·V_i)^4`. Perspective `V_i` points toward the camera; for orthographic use its fixed +Z direction. Determine visibility with a ray from that camera's ray origin to the evaluated surface: reject earlier occluders and mismatched objects/material regions. Use a scale-aware epsilon (~0.0001–0.001 m), not a large offset that jumps through a shield. Evaluate masks per texel or sufficiently tessellated face corners, not a few coarse vertices.
- [ ] Preserve the best view in high-confidence regions. Blend low-frequency colour over **8–16 texels at 1024**, with normalized weights in overlaps; hand-author the seam around high-frequency eyes, sunburst rays and belt edges so two motifs are not ghosted together. Fill zero-coverage regions explicitly. Put seams under arms, inside thighs and beneath shield rims; still inspect them in attack and death.
- [ ] Freeze projection at the **evaluated fitted rest pose**. On rigid kit, finish static geometry first. On skin, use a temporary evaluated copy with unchanged topology to calculate loop UVs/masks, then transfer them to matching original loops. If modifiers change topology, bake from the evaluated duplicate to the original surface unwrap with an explicit cage/distance instead; never zip unrelated vertex arrays. Keep the live armature on the production mesh.

```python
# Rigid, task-owned neutral mesh obj, fitted projector camera cam.
# For skin use the evaluated-copy procedure above, not a live modifier after Armature.
uv = obj.data.uv_layers.get('ProjectFront') or obj.data.uv_layers.new(name='ProjectFront')
project = obj.modifiers.new('Freeze front projection', 'UV_PROJECT')
project.uv_layer = uv.name
project.projector_count = 1
project.projectors[0].object = cam
project.aspect_x, project.aspect_y = 1.0, 1.0  # square source; otherwise set width/height ratio
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.context.view_layer.update()
bpy.ops.object.modifier_apply(modifier=project.name)
```

- [ ] Wire each source Image Texture through its **explicit** projection UV node. Mix with saved masks and fills into an Emission shader. Create a new 1024²/2048² image, sRGB, for the destination. Set **PaintUV active and active_render**; select an unconnected Image Texture node holding the destination in **every participating material**. Never read from the bake destination while writing it.
- [ ] Bake pigment with Cycles CPU, `bpy.ops.object.bake(type='EMIT')`, 1–8 samples, **16 px margin at 1024** / 32 at 2048, `margin_type='EXTEND'`; leave ≥2× margin separation between islands. Use `use_selected_to_active=False` for a same-mesh UV transfer. For a high→low duplicate, select source then active target, enable selected-to-active and calibrate a cage to avoid the next body part.
- [ ] Save/pack the bake. Replace the projection network with PaintUV → baked image. Reproject neither on camera movement nor per animation frame. Check rest before/after, ±30° turn, raised arms, bent knees and death; inspect checker stretch and the actual painting. Bake preserves registration, not missing detail or correct deformation.

### 6. Use Rigify through MPFB, with audited deformation weights

- [ ] Keep a copy of the existing 53-bone Spearman rig and motion. Rigify is an optional **control/deformation upgrade** when needed, not a reason to discard working R9 retargeting. Prove it on one copy before converting every unit; changed bone counts require intentional audit/mapping changes, not relaxed checks.
- [ ] Finish MPFB macro proportions first. For the projection/animation copy, freeze the chosen macro mix once if geometry fitting requires it; retain the original morphable body. New pose correctives come **after** that freeze. Do not subsequently erase all shape keys or edit base vertices underneath active macro keys.
- [ ] Enable Rigify, add MPFB's fitted Rigify metarig with **import weights enabled**, and generate with **MPFB's own generation helper/operator**. It updates equipped assets, parenting and deformation groups. Generic automatic weights on the already skinned body can lose MPFB's shoulder/hand work. Retain the metarig and keep regeneration separate from skin edits.

```python
# Installed MPFB extension namespace on the tested machine; inspect it on another host.
# body is a clean, fitted MPFB body copy without a second live skeleton attached.
bpy.ops.preferences.addon_enable(module='rigify')
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.rigservice import RigService
meta = HumanService.add_builtin_rig(body, 'rigify.human', import_weights=True)
bpy.context.view_layer.update()
rig = RigService.generate_rigify_rig(meta, name='Unit-rig', meta_rig_action='hide')
assert rig is not None
mods = [m for m in body.modifiers if m.type == 'ARMATURE']
assert mods and all(m.object == rig for m in mods)
```

- [ ] **Do not require exactly one Armature modifier.** MPFB can intentionally create `Armature` plus `Armature PV`, the latter using Multi Modifier and `mhmask-preserve-volume` to blend preserved-volume deformation. Verify targets, masks, order and flags; do not delete it as a supposed double-transform bug.
- [ ] Audit only groups corresponding to `use_deform` bones: every **rendered skin** vertex must have nonzero deform weight; sum should be 1 within 1e-4. Report unmapped/missing groups, negative/non-finite weights, left/right leakage, disconnected weight islands and unexpected distant influences. Exclude documented helpers and masks from both the sum and the visible-skin count. Do not normalize `mhmask-*`, cloth pins or material masks together with bone weights. Do not impose a four-influence game-engine limit on an offline sprite rig.
- [ ] Bind rigid helmet/shield/weapon kit to the intended bone preserving `matrix_world`. Skin sandals to foot **and toe/ball**; ankle parenting alone prevents toe-off. Transfer garment weights only between corresponding nearby surfaces, then inspect skirt/cape independence. Avoid heat weighting armour onto the whole body.
- [ ] Render clay and checker tests at shoulder elevation **0/45/90/120°**, shoulder twist **±45°**, elbow **0/45/90/130°**, knee **0/45/90/120°** and ankle/toe roll. Check shoulder cap volume, armpit collapse, elbow/knee crease, armour intersection, sole contact and texture stretch. A clean weight sum does not certify anatomy.

### 7. Add pose-space correctives and preserve full motion rotations

- [ ] Weight repair comes before corrective shapes. For shoulders, restore the deltoid/armpit at raised/twisted poses; elbows preserve olecranon volume and inner crease; knees preserve patella volume and front silhouette. Make separate left/right and bend/twist/combo shapes, with smooth regional falloff. Start activating elbow/knee correction at **45°**, full near **100–110°**; validate intermediate and combined poses.
- [ ] Shape keys are evaluated **before** Armature. Do not copy a sculpted posed mesh directly into a rest-space key: it double-deforms. Use Blender Studio's free Pose Shape Keys workflow to transfer the posed sculpt into correctives, or invert the *actual* skin-deformation mapping. A simple inverse weighted bone matrix applies to linear blend skinning only; MPFB's preserved-volume/Multi Modifier stack and B-Bones require a matching solver or the add-on. Corrective Smooth after Armature (factor **0.2**, **5** iterations, masked to joints) is an optional cleanup, not a substitute for sculpted volume.
- [ ] Drive a hinge corrective from a verified local rotation axis on an isolated bend mechanism bone, in radians. An illustrative driver is `min(1,max(0,(bend-0.785398)/1.047198))`. Check sign on each side. Shoulders need separate elevation/twist measurements or pose-space interpolation; a single Euler channel is insufficient for arbitrary swing. Review drivers; do not enable arbitrary downloaded scripts globally.
- [ ] Use **Quaternius's free Standard subset (CC0)** or **CMU free-use** for idle, move, hit and death. CMU is **not CC0**: record its terms and the converter's terms. Import clips at their recorded fps/units; remove an added calibration T-pose from playback. Map pelvis, spine, clavicles, arms, hands, thighs, calves, feet and toes; record unsupported fingers rather than inventing captured motion.
- [ ] Establish a common forward/up axis, unit scale and T/A reference pose. Preserve full 3×3 rotations including twist/roll. Head/tail direction alone loses one rotational degree of freedom. For matching skeleton motion in a shared world frame, calibrate `C = inverse(S_ref) @ T_ref`; use rotation of `S(t) @ C` on target helpers. Handle root translation and limb lengths separately rather than copying source joint positions into different proportions.
- [ ] Native route: source pose → reference-offset helpers → world-space Copy Rotation on a target FK/retarget rig; Rigify controls/IK follow the solved targets. Do not key constrained DEF bones and expect them to override Rigify mechanisms. Optional Rokoko route: use the free LGPL add-on's retarget panel, inspect its bone map/rest pose, pin a compatible version, and bake locally. A login/service dependency or Blender-version break is a reason to use native constraints, not to buy Studio features.
- [ ] Sample the **entire evaluated target pose** before modifying it. Bake visual transforms parent-first to a separate action/clean rig; include root, location, rotation and scale. Use quaternions with hemisphere continuity. For constrained Rigify controls, bake the controls or a clean deform duplicate; preserve the editable control rig.

```python
# P maps bone names to sampled matrices in TARGET ARMATURE space.
# Work on a clean bake rig with the source constraints muted/removed.
for pb in parent_first_bones:
    kwargs = {}
    if pb.parent:
        kwargs = dict(parent_matrix=P[pb.parent.name],
                      parent_matrix_local=pb.parent.bone.matrix_local)
    pb.rotation_mode = 'QUATERNION'
    pb.matrix_basis = pb.bone.convert_local_to_pose(
        P[pb.name], pb.bone.matrix_local, invert=True, **kwargs)
    # Flip quaternion sign if dot(previous_q, current_q) < 0 before keying.
    for channel in ('location', 'rotation_quaternion', 'scale'):
        pb.keyframe_insert(channel, frame=frame)
```

- [ ] Keep only the weapon-specific attack authored; start/end at the same guard as idle, including **elbow poles**, not just hands. Use constant documented guard offsets/upper-body layers where necessary. Preserve the source death body motion, separately author equipment release and ground contact. Retain the R9 complete-rotation/visual-bake fixes; do not revert to direction-only CMU reconstruction.
- [ ] **Foot locking:** detect heel/toe support from evaluated sole landmarks and velocity, inspect labels, and use hysteresis (starting thresholds: enter below **10 mm** and **0.04 m/s**, leave above **20 mm** or **0.08 m/s**). Calibrate to body scale and the actual disc contact plane. Correct global height first so detection is not fooled by bad grounding. Lock the stance landmark in world space with leg IK, stable knee pole and bounded pelvis adjustment; retain source foot/ball roll through heel strike/toe-off. Do not yaw foot meshes to hide mapping errors.
- [ ] For in-place sprites, define virtual displacement `d(t)`. A stance foot should follow `p(t)=anchor-d(t)` in the sprite, so measure slip on `p(t)+d(t)`, **not** raw foot motion against the stationary disc. Fit one speed over supporting intervals; do not fit independent speeds per foot/frame. Blend IK over **2–4 source frames**, with cyclic contacts joined across the loop. Start a diagnostic limit of **2 mm** compensated sole slip/floor error and **5°** heading discrepancy from the donor; retain stricter existing checks. Flag root/IK corrections above **3 cm**, reject above the existing **5 cm** bound rather than silently stretching legs.
- [ ] Inspect top/front **rendered feet**, support over ≥32 dense samples and the loop seam. Verify planted toe and heel geometry, not just ankle bones. Include transition into/out of idle and attack; a motion-source label is not a clean-walk pass.

### 8. Study open production assets selectively

- [ ] **Rain v3 / Snow:** free Blender Studio CC-BY 4.0 rigs. Study IK/FK snapping, parent switching, limb stretch controls and pose correctives. They use Studio rig systems (CloudRig lineage); they are not drop-in MPFB Rigify templates. Keep their stylized proportions out of Spearman unless the painting calls for them.
- [ ] **Brushstroke Tools**, Simon Thommes's free quick-start and the extension's bundled node assets: study stroke shape/opacity, layering and coherent colour masses. The lesson shows the CC-BY **Painterly Fishing Hut**, but its scene download currently requires a subscription; use the free lesson and extension, not that download. The GPL-3.0-or-later Brushstroke Tools extension creates textured strips from curves associated with surfaces; its deforming-surface workflow requires a rest-position attribute. Try a small cloak patch before covering an entire character. Dense transparent strokes can cost more than their 160 px contribution justifies; Cycles may need more transparent bounces.
- [ ] **Einar v1** from Charge: free Blender Studio CC-BY 4.0 rig. Study the skin, layered worn clothing and material separation as a physical-material reference; simplify them toward the painting instead of copying photographic noise. Credit reused material/rig data as `Einar Rig (CC-BY) Blender Foundation | studio.blender.org`.
- [ ] **Pose Shape Keys** (GPL-3.0-or-later extension): study the reversible posed-sculpt → rest-key workflow before writing a deformation inverse. Keep shape controls simple and independently testable.
- [ ] Use only items actually marked free. Some Blender Studio production files and Quaternius Source/Pro tiers require payment even when the artwork licence is permissive; neither is required here. Record exact download, creator, licence/version, hash and modifications for anything reused. Credit a reused Rain asset as `Rain Rig (CC) Blender Foundation | studio.blender.org`, with its source/licence link; likewise Snow and Einar. Keep the asset's CC-BY notice, not just the repository's general licence. This study incorporates no Studio asset.

### 9. Render and downscale for the sprite, not the viewport

- [ ] Choose the renderer **with the shader**. Eevee suits the ramp/light-response path; Cycles suits the existing camera-only projection/physical hybrid, emit baking and richer physical contact. Compare the same three poses before switching. More samples cannot correct a wrong silhouette, stretched UVs or pale fill.
- [ ] Eevee requires a graphics context even in background mode; `scene.cycles.device='CPU'` does not make Eevee a CPU renderer. On an authorized compatible host, use the gate's GPU route and label it accurately. Blender 5.3 accepts `BLENDER_EEVEE`; 4.x builds can use `BLENDER_EEVEE_NEXT`. Try the identifiers against the installed API rather than trusting a static enum listing.
- [ ] Start Eevee final at **128 render samples**, previews **32**; shadows on, ray tracing off unless demonstrated necessary, motion blur/DOF/bloom off. Configure `scene.eevee.taa_render_samples` only if present; report missing settings. Do not silently pretend removed `use_gtao`/SSR switches work. Inspect band-edge and alpha shimmer across frames, not just a still.
- [ ] Cycles CPU test: **160/256 px, 8–16 samples**, fixed seed, denoising off for comparisons. Final candidate: **512 px, 64–128 samples**, adaptive threshold **0.01**, minimum **16**, max bounces **6**, diffuse **2**, glossy **2**, transparent **8** (raise for actual layered strokes). Compare OIDN on/off at 160: denoising can smear painted strokes or flicker. `use_persistent_data` is a performance option, not temporal denoising.
- [ ] For an already painted source: **sRGB display, Standard, Look None, exposure 0, gamma 1**. Decode sRGB images once; convert hexadecimal swatches to linear for node values. AgX is useful for newly lit HDR/PBR surfaces, but compresses/desaturates the source-painted palette; Filmic is the older alternative, not an automatic upgrade. Never use Raw as a display-ready export. Save linear EXR when preserving radiance; PNG export receives the chosen display transform once.
- [ ] Render transparent **512²** RGBA masters and keep them; derive 256 and 160 from those masters, not a 256 preview upscaled to 512. Save 16-bit PNG masters when grading; use 8-bit RGBA for WebP. Disable DOF and motion blur so spear edges remain legible. Dither 0 for colour tests; optionally test very low dithering for final banding, frozen across the pipeline.
- [ ] Downsample **linear-light, premultiplied RGBA**: decode sRGB RGB → linear; multiply RGB by alpha; resample RGB×alpha and alpha together (area or Lanczos); clamp ringing/alpha; divide only where alpha > epsilon; encode RGB to sRGB, store straight alpha. Never gamma-transform alpha. Verify on cream, black and saturated backgrounds for fringes. A direct straight-RGBA or gamma-space resize is not equivalent.
- [ ] Keep one rest-calibrated monotone grade for every frame. Measure face/bronze/cloth/base separately; global histogram matching can improve statistics while shifting the wrong region. Preserve raw output and source hashes. Refit once after a camera/material/light/engine change, then rerender dependent clips.

### 10. Verify decoded delivery and stop on evidence

- [ ] Maintain the established Spearman clips: **idle/move/attack/hit/death**, **8/8/10/4/10** frames at **4/6/14/12/4 fps** respectively; idle/move loop. Work at donor sampling fps before final sampling. Change timing only with a reviewed motion reason. Render the terminal death sample once and copy it byte-for-byte.
- [ ] Pack 160 px logical cells, per-frame alpha trim/offsets, **2 px gutters**, WebP **quality ≥75**, **≤200,000 bytes**, all 40 records. Keep the shared anchor; do not recenter each crop. Decode the final atlas, reconstruct logical cells and verify alpha, offsets, margins, bounds, frame counts, timing, held death and hashes. Preserve RGB edge padding as needed for filtering while keeping gutter alpha zero.
- [ ] Review painting/raw/graded/decoded images at native 256/160/64, plus split and crossfade. Review motion playback and attack/death extremes. Separate geometry, projection, materials and motion A/B changes so a win can be attributed. Reject visible seam popping, swimming strokes, ghost ornament, bright unpainted backs or foot drift even when numerical checks pass.
- [ ] Run the probe below when changing its mechanisms; run changed Python/Bash syntax, skill validation and repository hygiene/whitespace at completion. No Rust/WASM/UI build is needed for this skill-only change. A production adoption still needs the unit's full scene/rig/atlas tests and the lead's art review. Record unfinished checks; never write PASS solely because a render completed.

## Verified probe and limits

Run the bundled [scripts/technique_probe.py](scripts/technique_probe.py) in a fresh process:

```sh
blender -b --disable-autoexec --factory-startup --python-exit-code 1 \
  --python tools/art/anim3d/scripts/technique_probe.py -- --output /tmp/legatum-unit-3d-probe
```

When installed, resolve the script relative to this skill directory. Optional `--mpfb` tests an already installed MPFB; use the pipeline's isolated `BLENDER_USER_RESOURCES`, `BLENDER_USER_CONFIG`, `BLENDER_USER_SCRIPTS`, `BLENDER_USER_DATAFILES` and `XDG_CACHE_HOME`. It downloads nothing and never saves preferences. Copy `scripts/` with this skill when installing.

Study date **2026-11-23**, Blender **5.3.0 / 02f0899d78e3**, gate-managed Cycles CPU, synthetic sphere/rig, 160 px/8 samples. Evidence remains under `~/LegatumRuns/anim-pilot/review/3d-v2/technique-study/`; the script recreates portable evidence rather than committing renders.

- Constructed the Eevee Diffuse/Shader-to-RGB/ramp graph; **did not render Eevee** on CPU. Rendered the separate analytic normal/ramp/bump preview; the small bump is subtle, not proof of finished painterly style.
- Applied two UV Project layers; UVs stayed byte-identical after camera movement. Baked their blended checker colours to a 256 px surface image with 8 px padding, then rendered at rest and rotated. Opaque RGB mean absolute before/after error: **0.801/255**. This convex test does **not** validate occlusion masks, hidden-area paintovers or deforming-body seams.
- Rendered cream `(233,207,160)` through strength-1 emission: centre pixels **Standard (233,207,160)**, **AgX (190,177,157)**, **Filmic (198,187,161)**. This verifies an unlit swatch round trip, not every lit material.
- Native reference-offset Copy Rotation plus `convert_local_to_pose`: **0 rad** reported error for three test rotations with a **0.7 rad** rest-roll mismatch. One bone only; real hierarchy/retarget action and foot audits remain necessary.
- Corrective driver evaluated to **0.49999994** at 45° for a 0–90° ramp. This checks driver mechanics, not anatomically correct corrective sculpture.
- Stock Rigify human generated **706 bones**. The optional MPFB test and synthetic IK result are described in the companion [verification record](references/verification.md), including the initial assertion error and its cause.

## Sources and licences

Primary sources consulted for the mechanisms; presets and Legatum-specific recommendations above are adaptations, not vendor guarantees. Recheck downloaded artefacts' actual licence files.

- Blender manual: [Shader to RGB](https://docs.blender.org/manual/en/4.5/render/shader_nodes/converter/shader_to_rgb.html), [UV Project](https://docs.blender.org/manual/en/latest/modeling/modifiers/modify/uv_project.html), [baking](https://docs.blender.org/manual/en/4.5/render/cycles/baking.html), [colour management](https://docs.blender.org/manual/en/4.5/render/color_management.html), [Corrective Smooth](https://docs.blender.org/manual/en/4.2/modeling/modifiers/deform/corrective_smooth.html). Manual: CC-BY-SA 4.0; Blender software: GPL. Version-specific API checked locally.
- [Bone.convert_local_to_pose](https://docs.blender.org/api/current/bpy.types.Bone.html#bpy.types.Bone.convert_local_to_pose): official API reference; Blender GPL implementation. See sampled-parent conversion rather than direction-only rotation reconstruction.
- [MPFB Rigify workflow](https://www.makehumancommunity.org/mpfb/docs/rigging_posing/rigify.html), [MPFB source and licences](https://github.com/makehumancommunity/mpfb2): code GPL-3.0-or-later, bundled body/assets CC0; community clothing can have separate terms.
- [Brushstroke Tools](https://extensions.blender.org/add-ons/brushstroke-tools/) and [production documentation](https://studio.blender.org/tools/addons/brushstroke_tools): extension GPL-3.0-or-later. [Free quick-start lesson](https://studio.blender.org/training/stylized-rendering-with-brushstrokes/get-started-using-brushstroke-tools/): Simon Thommes / Blender Studio, CC-BY 4.0; fishing-hut scene download is subscription-gated and excluded.
- [Rain v3](https://studio.blender.org/characters/rain/v3/), [Snow v2](https://studio.blender.org/characters/snow/v2/), [Einar v1](https://studio.blender.org/characters/einar/v1/): free Blender Foundation rigs, CC-BY 4.0, attribution required. Pin the selected version and its licence link.
- [Pose Shape Keys](https://extensions.blender.org/add-ons/pose-shape-keys/) and [workflow](https://studio.blender.org/tools/addons/pose_shape_keys): GPL-3.0-or-later extension; posed corrective authoring with weight iteration.
- [Rokoko Blender add-on](https://github.com/Rokoko/rokoko-studio-live-blender): LGPL-3.0; optional local retargeting code, distinct from Rokoko Studio/service terms. Not installed or exercised in this study.
- [Quaternius Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html): CC0, use the free Standard subset only; the full Source/Pro offerings are unnecessary.
- [CMU Graphics Lab](http://mocap.cs.cmu.edu/), [cgspeed conversion](https://sites.google.com/a/cgspeed.com/cgspeed/motion-capture): CMU custom free-use terms permit commercial products but forbid resale of the data itself, including converted data; **not CC0**. Credit CMU/NSF EIA-0196217 and identify conversion/version. Original capture is ASF/AMC; converted BVH can add an estimated T-pose and noisy toe channels. Retain the conversion README.
- [ambientCG](https://docs.ambientcg.com/license/) and [Poly Haven](https://polyhaven.com/license): CC0 texture/HDRI assets. [Krita](https://krita.org/en/about/license/): GPLv3 software for original paintovers. Software licences do not automatically license unrelated artwork.
