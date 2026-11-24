---
name: legatum-unit-3d
description: Build and refine Legatum's painted 3D miniature units in Blender from an existing unit painting, using the anim3d kit (MPFB body and rig, registered painting projection, Eevee painted look, open-mocap walk with foot locking, keyed or donor reactions, five sprite-atlas clips, critique). Use for unit look development, form fitting, motion, render QA and round reviews.
---

# Painted miniature units

> **The bar is game feel (Sam, 2026-11-24).** A unit should "feel like a unit in those games" (Age of Empires, Civ 6), and the painting is inspiration, not a pixel target. Pass means clear, weighty, readable motion at 160 px; rigid props; no pops or foot sliding; and recognisably the painting's unit (colours, crest, shield device, bronze) without matching it pixel for pixel. Silhouette IoU and ΔE against the painting are info only, not pass criteria. Method: motion first, on a proven CC0 rig and animation library (Quaternius base character and Universal Animation Library; see PRIOR-ART.md), with props rigidly bone-parented; the painted look goes on top afterwards. No hand-building or hand-posing of bodies, and nothing paid or needing an account. Where a rule below conflicts with this, this wins.

The painting is the art target. The goal at rest: a viewer cannot tell the render from the painting at 256, 160 and 64 px. A passing audit, atlas or metric is never art approval; only the lead writes PASS.

Tags: **[proven]** kept on a Spearman round, with the evidence. **[rejected]** tried and measured worse; do not retry without a new reason. **[untested]** not yet proven on a unit.

Numbers are the Spearman's. Its current status, open items and settings are in `references/spearman-status.md`; per-round cost and metrics in `LOG.md`; reusable code in `kit/` (`kit/README.md`). Sample each new painting before copying a colour, camera or light.

## Ground rules

- [ ] Run Blender as `blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python <script>` through the `blender` on PATH (machine-wide gate: one process, 3 threads). Never call the app directly, pass `-t` or touch the gate's locks. Source `tools/art/anim3d/env.sh` first.
- [ ] Never hide an object by scaling it to 0; key `hide_render`. **[proven]** zero-scaled meshes crashed Cycles (OpenVDB, SIGABRT).
- [ ] Heavy files (`.blend`, textures, caches, frames) stay under `ANIM_ROOT` (`~/LegatumRuns/anim-pilot`). Git holds code and small presets.
- [ ] Licences (public repo): CC0 or CMU free-use motion only; no Mixamo, nothing paid. Record URL, version, hash, action and licence in `units/<slug>/SOURCES.md` and `assets/SOURCES.md`.
- [ ] Work on copies; rebuild from a preserved input file so repeat runs do not accumulate edits. Keep the painting in the game until the lead approves.
- [ ] The installed `blender-*` skills cover general operations; this skill overrides them (Standard view transform, no depth of field, unlit painted pigment).

## Start a new unit (skateboard first)

Get a crude unit through all five clips and the atlas before polishing any stage. Copy `kit/presets/spearman.json` to `<slug>.json`. Each increment ends with a render the lead can look at.

1. Clay figure on the cream base, camera matched, outline measured against the painting (steps 1–2).
2. Registration fit, frozen projection, Eevee painted look with per-part paint (steps 3–4).
3. Open mocap for idle and walk with locked feet; blocked-in attack, hit and death; pose checks (steps 5–7).
4. Preview atlas, movie and `critique.py` numbers (steps 8–10).
5. Then iterate on the worst visible gap, one variable at a time. Split builders by aspect (look; form and motion), not three lanes on one candidate.

## Checklist

### 1. Camera, base and silhouette

- [ ] Camera: orthographic, fixed for all five clips, no per-frame fitting, depth of field off (`kit/studio.py: match_camera`). Give the figure the painting's frame height so 64 px tokens compare 1:1.
- [ ] Base: one stationary cream stone disc for every unit, top **#E9CFA0**, side **#B68A51**, top at **z = 0.105 m** (`kit/base.py`, `kit/audit.py: check_base`). Never project the figure painting onto it: painted feet and shadows would stay behind. Shade it from colours measured on the painted disc, with a thin light lip where top meets side and a lighter, sandier wall. **[proven]** R11 base region ΔE 6.6 → 3.9; R12 dropped the lip and regressed to 4.8.
- [ ] Ground shadow: study what the painting actually draws before simulating one. The Spearman's is one soft warm shadow behind the heels and between the feet, not a cast shadow of the key and not AO (**[rejected]** an ambient term: it darkened under the shield in front instead, base ΔE 2.7 → 5.4). **[proven]** Fable C draws it in the stone shader as two blobs anchored to the ankle bones, offset back and inward and fading as a foot lifts, so it travels with the feet in every clip: feet region 10.8 → 5.3, whole image 3.96 → 3.31. Check that in the walk at 160 px: on the R13 GPU movie the band stayed put while the feet moved (art director); it must follow the feet or drop out during move. Any contact shadow stays within the sole plus 2 px; a plate wider than the foot is a defect. Soles sit within 2 mm of the stone at rest (`kit/contact.py: seat_rest_guard`); never hide a gap with a darker patch.
- [ ] Match the silhouette before any texture. **[proven]** every IoU gain came from geometry or pose (R4 shield and crest 0.839 → 0.851; R9a 0.880 → 0.898; R11 greave, cloak and shaft 0.904 → 0.922; Fable B legs and feet 0.894 → 0.932). Surface detail never moved it.
- [ ] Tune form by **measuring opaque row and column spans at 256 px against the painting**, not by eye: `python -m kit.regions --painting P --after R --rows y0,y1[,x0,x1] --columns x0,x1[,y0,y1]`. **[proven]** Fable B's first leg bulking "looked right but measured wrong" (shins 13–15 px against the painted 9–10); retuned by spans, IoU 0.918 → 0.932. Measurement also overruled review notes: a "5% small" shield matched within 1 px, and two reviews that disagreed on the base wall were both within 1 px of the painting.
- [ ] Feet first, on a gridded 8× crop of painting and render (`python -m kit.regions --painting P --after R --grid x0,y0,x1,y1 --sheet out.png`), before touching the legs. **[proven]** Fable C: the soles lay 3.3 and 2.7 px **below** the painted ones and only 1 px off sideways; the ankles were 4 px low, so the shin line was 36 px long against the painted 30. That was the "A-frame" four reviews had described as leg width or foot size.
- [ ] An orthographic camera hides depth: feet that sit too low on screen are too near the camera. Stand them deeper on the disc (which raises them on screen) and take up the leg length in the knees, toward the camera, where it does not show. Do it as a **guard-pose** edit (pelvis back along the view ray, ankles at their painted screen positions, each leg re-solved at its own bone lengths with the knee on its painted column), not a rest-mesh shear, which would pull the foot off its ankle bone and swing it through the stone in the walk. **[proven]** Fable C: IoU 0.9394 → 0.9513 on the CPU proxy, 0.9534 in Eevee; the first Spearman to pass 0.95. **[rejected]**: ankle targets without the knee columns (IoU fell to 0.936); moving the rig object instead of the pelvis pose (every rig-space constant in the clips moves with it).
- [ ] Thin props: measure them in painting pixels and match in the master, so the paint has something to land on. The painting draws them thicker than life; anything under about 2 px at 160 renders dark and jagged. **[proven]** the Spearman's 2 px black shaft was the art director's first tell for two rounds; 1.8× thicker in the master fixed it.
- [ ] Legs and feet: change **rest geometry** that every clip inherits (scale about the bone axis or the sole point under the ankle, bones, weights and pose untouched; sandal volume built around the anatomical foot, straps laid on its surface). **[rejected]**: splaying or widening in camera space, camera-ray shifts, yawing a foot mesh, rotating toes after the retarget, including yaw fixes on an airborne foot (Sam: "duck feet"); scaling a leg symmetrically (pale lobes outside the greaves); a larger distal greave flare; a more outward knee pole.
- [ ] Choose foot fitting on contact, not rest appearance. **[proven]** width × 1.50 and height × 1.15–1.18 at original length pass every walk limit; **[rejected]** length × 1.35 and × 1.42 (58.7 mm and 42.6 mm of sole correction against the 40 mm limit).
- [ ] Protect the human foot, ball and sole vertices by hash; do not protect armour just because it carries foot weights. **[proven]** R11a freed the distal greave shell: lower-leg overlap 78.3% → 83.0%.
- [ ] Body under rigid armour stays inside the armour's outline (tighten the calf, seat the shin, hold the skin at half the armour's scale). Hide ornament that ends up floating beside a refitted shell.
- [ ] Keep guard fitting and geometry fitting separate. When moving an ankle in the guard, translate the complete foot and ball and preserve the foot head's offset from the calf end; solving the calf straight to the foot head bent the knees 6–7 cm for a small move (R13a).
- [ ] Guard pose before fit: rotate the whole foot+ball pair in the authored guard and solve the leg to the planted ankle at fixed bone lengths, before projection and donor mapping. Pose first, then fit the armour contour, then freeze UVs.
- [ ] Rigid kit: finish thickness, bevels and relief before projection, and check relief clearance on the **evaluated** shell. **[proven]** R5/R6: shield rays sat 8.4 mm inside the Solidify surface until checked on evaluated faces.

### 2. Body and rig

- [ ] MPFB 2 body with macro overrides, `game_engine` skeleton, original MPFB weights (`kit/human.py: create_body`, `add_rig`): 19,158 vertices, 53 bones. Do not re-weight the skin automatically.
- [ ] Before fitting vertices on the working copy, bake the active macro shape keys (`kit/human.py: freeze_macro_mix`). **[proven]** R6: 25 active keys silently overrode direct vertex edits. Keep the morphable original.
- [ ] Skin sandals and soles to foot **and** ball bones. Bind rigid kit to one bone, preserving `matrix_world`.
- [ ] MPFB's `Armature` + `Armature PV` pair is intended; do not delete it.
- [ ] **[untested]** Rigify (`add_rig(..., rigify=True)`) and hinge correctives (`add_hinge_corrective`, authored rest-space deltas only). The Spearman's angular shoulder in hit and death is the open case; **[rejected]** as a cure: sleeve smoothing and shallow folds (R11a), a 32 mm sleeve shortening (R12a).

### 3. Registration and frozen projection

- [ ] Fit where the full-size painting sits on the 256 px canvas by image comparison: `python -m kit.registration <slug>-source.png <slug>-256.png` (one isotropic scale and an offset). Never take separate x and y scales from alpha bounding boxes. **[proven]** the Spearman's bounding-box calibration was 0.9% narrow and 0.3% short, up to 0.45 px off at 256, and cost about 3 ΔE; the kit fit and the look lane's independent fit agree at 5.342 source px per canvas px.
- [ ] Fix registration before colour. Paint that lands on the wrong surface reads as a colour fault. **[proven]** Fable C: the Spearman's "pale sandals" (luminance 162–169 against 141 over four reviews) were sandal paint landing on greave bottoms and stone; with the feet under their own paint the region fell from 13.4 to 5.3 blurred ΔE before any tone change, and a leather multiplier afterwards cost more than it gained.
- [ ] Correct registration in **one** place. On a unit whose UVs are frozen, resample the texture and leave the UVs; changing both double-corrects.
- [ ] Freeze the projection at the fitted rest pose on original topology (`kit/projection.py: freeze_projection`: a `Painting camera rest` UV layer and a `Painting visibility` corner attribute). Never reproject per frame.
- [ ] Visibility by **ray distance from the camera**, not normal direction (Spearman tolerance 18 mm; 140 mm for relief on a painted shell). **[proven]** R4: a normal test blanked the shield. Facing weight `clamp((|N·V| − 0.02) / 0.18)`.
- [ ] Register raised ornament on its curved support before projecting, or it doubles and smears (R3 shield).
- [ ] Changing the master invalidates every clip, texture set and atlas. Rebuild; never relabel hashes. After a form change rebuild the look's part textures and ramps (about 15 s) before judging colour.

### 4. The look: Eevee, emission only, applied at render time

The standard look (reviewer and art director, 2026-11-24). Worked example: `units/spearman/look.py`, `look_textures.py`, `look.sh`; helpers `kit/look.py`, `kit/part_paint.py`, `kit/continuity.py`. **[proven]** against Cycles plus denoise plus a histogram grade: blurred ΔE 6.47 → 4.59, raw 9.9 → 7.3, "colours and values finally read as the painting"; rest plus 40 frames render in about 55 s.

- [ ] Keep it a render-time layer: open the master or clip read-only, replace materials and lights, save nothing. Geometry, weights, UVs, cloth caches, actions and camera stay untouched, so look, form and motion can be built and judged separately.
- [ ] Eevee, Standard view, emission only, no denoiser, no grade. The projected painting already contains its lighting: never multiply it by a second diffuse or AO pass.
- [ ] One paint texture **per kit part**, trusting the painting over mesh names: the part keeps the painting only inside its own rest outline (from a flat ID render) and the rest is inpainted from its own pixels (`kit/part_paint.py: part_texture`). Otherwise a part carries its neighbour's paint wherever outline and painting differ by a few pixels. Rigid and free-swinging parts also reject another colour family's paint; torso layers keep all of it. A curve with no UVs reads the painting through the same projection in object coordinates.
- [ ] Before modelling missing fine detail, check the source, the part-ID ownership and the derived texture: per-part erosion can delete detail the painting already has. **[proven]** R15a: sharing the original pigment across the registered foot's leather and skin footprint brought the sandal straps back with no geometry or contact change (feet 5.45 → 4.72, whole image 3.39 → 3.30 on the CPU proxy).
- [ ] Unseen surfaces: white Diffuse → Shader to RGB → ColorRamp of the part's own painted colours (`kit/part_paint.py: palette`, nine luminance quantiles), each stop at the lighting quantile of that material's surface.
- [ ] One camera-space upper-left sun, strength **π**, angle 24°. Shadows travel without relighting painted form through a cast-shadow-only term.

```python
# kit/look.py (Eevee only): form light, cast-only shadow, the part's painted ramp.
g = Graph(material)                       # clears the node tree
form = g.lit()                            # white diffuse -> Shader to RGB -> value
cast = g.lit(constant_normal=key_dir)     # 1 in light, drops only in cast shadow
fill = g.ramp(form, ramp_stops(palette))  # kit.part_paint.palette output
g.emit(g.mix(g.math('MULTIPLY', g.math('SUBTRACT', 1, cast), .45), fill, shadow_tint, 'MULTIPLY'))
```

- [ ] Eevee traps, each cost a round: a sun of strength 1 returns 1/π on white diffuse; an unlinked Normal socket ignores `default_value` (link a Combine XYZ); ColorRamp elements re-sort when positions are assigned in place (remove all but one, add in order); Shader to RGB needs a GPU context (`--gpu-backend metal`).
- [ ] Paint what motion reveals, from rest-space masks (`kit/continuity.py`): sole undersides leather brown (not the vertical sidewall), inward skirt faces shadowed linen, unseen rear shoulder in the cloak's colour. **[proven]** R12b: death skirt luminance 101 → 83, lifted soles no longer flash white, rest unchanged.
- [ ] Before repainting a pale patch seen in motion, render a material-ID image of that pose (`kit/ab.py: material_id_render`). **[proven]** twice: the "cape" patch was the sleeve (R10b); the "inner patch" was cloak, the death underside was skirt (R11b).
- [ ] Keep trusted source pigment and coverage alpha; correct locally with feathered patches. **[rejected]**: replacement palettes, forcing alpha to 1, global colour gates (R11b); assigning pixels to parts by colour distance; retargeting painted sandals box-to-box onto small feet; projecting the painted disc onto the stone (look lane); more weave or micro-bump on a plain surface (R9b; invisible at 64 px).
- [ ] Values: compare luminance per region, mean and 90th percentile (`python -m kit.regions --stats name=x0,y0,x1,y1`), and correct the end that is off. Put darkness where the painting has it; never raise global saturation. Check every cavity for stray bright pixels.
- [ ] Check clips where the body turns or lies down: baked highlights travel with it. If they read wrong, blend a little live form shading on that clip only (`paint_form`). No problem seen on the Spearman so far.
- [ ] No GPU in a sandbox: `kit/cpu_look.py: graph_for_sun` substitutes a sun cosine for Shader to RGB on Cycles. Label it a proxy; it has no cast shadows, so contact and shadow depth need the Eevee pass.
- [ ] Fallback only: the Cycles camera-pigment hybrid (`kit/materials.py: painted_fill`, `kit/studio.py: match_lighting`, one rest-fitted grade `kit/grade.py`). If used: fit the grade once at rest, never per frame; bake AO with Solidify disabled.

### 5. Motion

- [ ] **The rule (reviewer, 2026-11-24).** Idle and walk come from open mocap with proper retargeting; do not reinvent solved motion. Attack, death and hit may be hand-keyed or donor clips with layered corrections, whichever the art director and reviewer rank better.
- [ ] Retarget with `kit/retarget.py: prepare`: per-bone reference offsets **including roll**, world-space Copy Rotation, sample the whole evaluated pose, bake parent-first with `Bone.convert_local_to_pose`. Joint directions alone lose roll; assigning `pose_bone.matrix` in a loop reads stale parents.

```python
for p in rig.pose.bones:  # parent-first; kit/retarget.py: apply_matrices
    args = {'parent_matrix': matrices[p.parent.name],
            'parent_matrix_local': p.parent.bone.matrix_local} if p.parent else {}
    p.matrix_basis = p.bone.convert_local_to_pose(
        matrices[p.name], p.bone.matrix_local, invert=True, **args)
```

- [ ] Donors (CC0): Quaternius Universal Animation Library Standard `Idle_Loop`, `Walk_Loop`; KayKit Character Animations Free 1.1 `Hit_B`, `Death_B` (`kit/retarget_presets.py`). Locomotion legs calibrate from anatomical rest, not the weapon guard; the upper body keeps the guard with the donor delta on top; carrying arms come from the idle via an NLA layer, driven by the donor's torso so shield and spear share the walk's weight.
- [ ] Try another donor before layering corrections on a bad one. **[proven]** two rounds of blending Quaternius `Death01` never removed its squat and pop; KayKit's hit and death gave the first donor reactions the art director accepted (hit head bob 81 → 12 mm). A new donor still needs anatomical leg calibration, source ankle heights transferred by IK, and every sandal strap checked against the floor.
- [ ] Walk: both legs must read separately at 160 px in every frame. **[proven]** a constant **8.5 cm lateral ankle offset per foot**, ankles re-solved by IK so contact holds: on-screen ankle separation 9 → 15 px at 256, the first walks to pass. Lower a marching swing foot relative to the measured support sole, before the final floor solve, with translation-only IK that keeps the donor's foot rotation (`kit/walk.py: shape_walk`, which asserts the rotation is unchanged; **[proven]** R13c: swing clearance 114 → 76 mm, slip 0.004 mm); lowering an absolute ankle height is undone by the root correction. Add pelvis dip at double support (about 2 cm), sway over the stance foot, 2–3° of shoulder counter-rotation and spear sway, phase-locked to the measured stance intervals; the shield stays the stable mass. **[rejected]** by verdict: widening only through leg spread in the calibration (world spacing 42% → 58% of rest, legs still crossed on screen). Judge the walk on screen, not in world units.
- [ ] Tame a stylised donor in its own rest space before retargeting (NLA influence; Spearman 0.90). **[rejected]** 0.88 and 0.82: contact broke. Contact quality is not monotonic in attenuation.
- [ ] Death: pick by review between a keyed collapse and a donor that stages on the base. **[proven]** the Spearman ships a keyed collapse (recoil, knees give with feet planted, kneel, topple, settle across the stone) over both donor deaths. Author it with `kit/quicklook.py` and `kit/quicksheet.py` (painting camera plus top, front, side; about a minute a loop). Foot pitch absolute from the flat sole. Choose the end pose by what reads at 64 px: crest, shield face and body.
- [ ] Containment does not outweigh identity. R14a compacted a side-lying ending fully inside the rim (crest and feet margins −28 and −14 px → +3.3 and +5.0 px, by tucking the ankles toward the hip and moving the torso inward; a translation alone trades crest overhang for foot overhang) and was still **[rejected]**: it hid the shield and showed a striped skirt underside, and the director kept the ending with the shield face readable. Re-place a released shield after the body's floor correction or it rides up with the lifted arm.
- [ ] Death staging: everything stays in the 160 px cell in every frame, weapon included (never crop it); the body ends on the base; the fallen unit still reads as itself at 64 px (shield face and crest toward camera, shield never flat like a dish); a dropped weapon tips over 2–3 frames, starting in frame 1; cloth lies on the body and never tents; hold only the last 2 frames.
- [ ] Hit: a lean back with the shield drawn in, not a crouch. Cloak pinned at both shoulders, crest attached along the helmet ridge in every frame, shield turn at most about 30° and lift 10 px at 256, and a visible peak: the four frames must differ.
- [ ] Attack: start and end on the idle guard **including elbow poles**, not only hand targets (R7). No weapon jump over about 35° in one frame.
- [ ] Carried equipment stays parented at its grip. For a shield in a fall: an edge-down preference with damping and enough samples through the descent (**[proven]** R11c: rotation step 83° → 34°).
- [ ] Loops: a zero foot seam says nothing about cloth. Measure evaluated cloth vertices at the loop's duplicate endpoint (**[proven]** R14c: the R13 walk had a hidden 12 px cloak jump; a post-bake correction closed it to 0.00003 px, `kit/loop.py: close_cloth_loop`). That correction is authored, not simulated: report its size (273 mm at the worst free vertex on the merged walk) and inspect every intermediate frame. Reduce the idle-to-walk cut by choosing which donor phase the loop starts on, minimising entry and exit together (R14c: sole gap 23.0 → 14.4 px in, 18.7 → 9.4 px out by rotating the eight samples; **[rejected]** optimising entry alone, which worsened the exit to 20 px). Report entry, exit and the largest cloth step together when choosing the phase: on R15c an exhaustive check of all 32 phases left R14's as the only one that regressed none of them. A toe-out guard cannot equal a walking pose; a clean entry needs its own transition samples.
- [ ] Cloth: one second of pre-roll, a persistent bake per clip, full shoulder pins; for a fall, softer lower pins and about two seconds of post-roll (R12c: late cape travel 157 → 81 mm). **[rejected]** loosened hit pins (R9). Even a 1–2 px edit to rest cloth changes every simulation: rebuild and compare each clip, and keep the previous version of any clip that regresses (R15a kept R14's cloak). Damping is not monotonic either: judge a cloak by its visible sweep at 160 px **and** its worst-vertex return (`kit/cloth.py: configure`; **[proven]** R14b, walk: lower pins × 1.8, air damping 6, bending 2.0 took the cloak's edge sweep 22.1 → 15.5 px; a 1.35× trial lowered sweep but left a hem vertex 246 mm from its loop start). Secondary motion (crest, shield) is a capped damped spring, not a second performance.
- [ ] Clips: idle/move/attack/hit/death = **8/8/10/4/10** frames at **4/6/14/12/4 fps**; idle and move loop. Render the final death frame once and copy it byte for byte. Spend the frame budget on motion: `python -m kit.regions --clips <decoded-160 dir>` flags frames that barely change before the held tail and poses that jump.
- [ ] A guard-pose change leaks into every clip through rig-space constants (attack arm targets and poles keyed about the old pelvis, the walk's height correction, clip entry poses). Right after one, re-run the pose audit, the feet check and the frozen-action check, and expect the frozen check to fail until the merge re-pins it. **[proven]** Fable C: the audit caught attack arms 2.5–5 cm off the guard at entry and exit; the walk's height correction rose to 3.7 cm of its 4 cm limit. Transplanting a guard needs its real IK endpoints (calf and forearm tails), elbow and knee planes and an entry rotation blend; matching hand and foot points alone leaves a bone-roll jump (R14a). Key clip targets relative to the guard, not as rig-space constants (R13: attack leg targets from the neutral calf tails, entry and exit sole error under 0.001 mm). Register an in-place walk to a new guard with one constant translation of the whole donor track; **[rejected]** ankle-only offsets (29.8 mm of planted slip against 0.0042 mm).
- [ ] Freeze a clip once the art director accepts it: pin its action hashes and check them in the unit's `gpu.sh` (`units/spearman/check_frozen.py`, `kit/ab.py: invariant`). A form rebase rebuilds the clip; say so rather than claiming identical hashes.

### 6. Foot locking and the feet check

- [ ] `kit/retarget.py: stabilize_walk` locks heel strike, flat stance and toe-off from evaluated **sole landmarks** (`toe_vertex`, `heel_vertex` properties on each sole object), fits one virtual forward speed over all support intervals, keeps support across the loop seam, and corrects with a shared root offset plus two-bone IK while a world Copy Rotation holds the donor's foot rotation. Converge on the evaluated sole, not the bone.
- [ ] Enforced limits (`kit/feet.py: measure`, `failures`): compensated sole slip ≤ **1 mm**, planted floor error ≤ **2 mm**, planted and readable heading ≤ **10°**, loop seam ≤ **3 mm**, root and foot-IK correction ≤ **50 mm**, sole translation ≤ **40 mm**. Spearman R12: slip 0.0018 mm, floor 0.000 mm, heading 5.1°, root 48.96 mm. Tighten a limit when it misses something; never loosen one to pass.
- [ ] Measure slip on `foot(t) + virtual_displacement(t)`; an in-place walker's planted foot slides back by design.
- [ ] Every round render the real lower legs from top and front over the whole cycle (`<slug>-g-feet-check.png`, ≥ 32 dense samples) and look at it. `kit/feet.py: step_width` and `swing_lift` give numbers for stance width and foot lift.

### 7. Checks on every delivered pose

- [ ] Query the support surface on evaluated faces, bevel and ground included (`kit/base.py: SupportSurface`), and use the same query for fitting, floor correction and audit. **[proven]** R14c: the widest-vertex top approximation claimed support at 0.105 m where a flared test base's rim was at 0.042 m.
- [ ] Pose audit over all 40 poses (`kit/audit.py`): camera bounds, contact against the real disc footprint plus world ground, weapon crossings and grip, arm joints within 2 mm of idle at clip entry and exit; plus every sandal, strap and welt vertex against the stone. Zero findings.
- [ ] Motion numbers on delivered samples (`kit/motion_metrics.py`): largest head step, highest ankle, equipment grip range and rotation step, late cloth travel. They describe; they do not approve.
- [ ] For a change that claims to touch only one aspect, hash everything else before and after (`kit/ab.py: invariant`) and assert equality.

### 8. Render

- [ ] Iterate on previews; a full GPU pass takes 30–38 minutes of the machine's only Blender slot and starves everyone else's 55-second Eevee jobs. **[proven]** R10: the art director's 14 ranked items were identical on preview and GPU final. Do not start a full pass while builders are iterating; batch A/B variants in one Blender session (eight in 13 s).
- [ ] **One render path** (reviewer's decision). The unit's `gpu.sh` and its `look.py` must render through the same code, so the delivered atlas and the review images are what `critique.py` scored. **[proven]** R12: the `gpu.sh` path gave a lighter shield rim (p10 50 against 38) and hotter greave highlights than `look.py` on the same master (27/64/107 against the painting's 28/65/108), and a review chased a fault that was only in one path. Compare numbers from one path only. Both entry points call the same render setup and frame function, resolution percentage included, and the GPU handoff renders the rest through both and compares them before delivery (R13). Give that comparison a tolerance measured from rendering one path twice (the working gate: mean error < 0.01 and under 0.05% of pixels off by more than 2 levels): **[proven]** R13's first gate asserted exact equality and failed a 25-minute pass on GPU sample noise (142 of 262,144 pixels differed, one by more than 2 levels, mean error 0.0002).
- [ ] A/B pairs share everything: engine, size, samples, seed, camera, lights (`kit/ab.py: preview_settings`: Cycles CPU, 256 px, 16 samples, seed 17, no denoising or adaptive sampling). Label proxy, CPU and GPU evidence; never claim one from another.
- [ ] Final masters: 512 px transparent RGBA plus a derived 256 set under `masters/<slug>/{512,256}/`. Never upscale.
- [ ] Reduce every image the way the painted tokens were reduced: **display-space Lanczos with premultiplied alpha** (`kit/images.py: resize_rgba(..., space='display')`, `python -m kit.deliver --reduce display`). **[proven]** the painting's own master reduced that way matches the 256 px painting to 0.7 ΔE; reduced in linear light it scores 3.1. One space for a unit's cells, masters and comparisons. At 64 px compare against the painting's own 64 px token.

### 9. Deliver

- [ ] Atlas v2: 160 px cells, per-frame alpha trim with offsets, shared anchor, 2 px gutters, WebP quality ≥ 75, **≤ 200,000 bytes**, 40 records (`kit/atlas.py`, `python -m kit.deliver`). Spearman: 185–197 KB at q80–q85. If it does not fit, report it; never drop frames or quality silently.
- [ ] Validate the **decoded** atlas (alpha, offsets, gutters, bounds, counts, timing, held death); the unit script adds hash checks. Judge "this clip moves" on lossless source frames: lossy WebP makes identical tiles decode differently.
- [ ] Previews go to a lane folder; only a 512 px final pass writes `app/src/assets/units/anim/`.
- [ ] Movie: five clips side by side on cream at 2×, 1600×352, H.264 yuv420p, 24 fps, 8 s, `review/3d-v2/<slug>-round<N>.mp4`.

### 10. Critique and review

- [ ] Every round: `critique.py --slug <slug> --round <N> --label '<what was rendered>' --painting <256.png> --rest <rest.png> --frames <decoded-160 dir> --feet <feet-check.png> --out $ANIM_ROOT/review/3d-v2`. It reads the unit's `critique_regions` from `kit/presets/<slug>.json` and appends its numbers above the FOCUS lines of the round note.
- [ ] What passing took on the first unit (GPU, same definitions): R10 0.9039 / 6.47 → R11 0.9275 / 4.59 (the Eevee look, registration, greave fit) → R12 0.9384 / 4.72 (measured leg and foot form) → R13 **0.9537 / 3.51** (feet registered on a gridded crop, guard replanted in depth, ankle-anchored ground shadow). Start a new unit with those four moves, in that order, before anything else.
- [ ] Targets: silhouette IoU ≥ **0.95** (best of ±3 px offsets) and **blurred ΔE ≤ 6 at zero offset** (CIE76, 2 px Gaussian at 256, linear light). The offset search is for IoU only. Raw per-pixel ΔE is information: it is dominated by fine-texture misregistration. Reviewer's bar for showing Sam: IoU ≥ 0.94, blurred ΔE ≤ 6, good clips. Do not round up to a threshold.
- [ ] A region's average tells you where, not what. Before changing colour in a failing box, look at what fills it: the Spearman's feet box included pale stone showing where the foot was narrower and lower than the painting, so darkening foot pixels made it worse (**[rejected]** R13b: 13.33 → 13.90; the sole silhouette persisted with contact AO off). Compare zero-offset IoU as well as the searched value: a ±3 px search can hide a real loss (R13a: 0.9369 searched hid a fall at zero offset).
- [ ] Read the per-region values first and treat any region over 6 as open. **[proven]** on R10 the boxes alone reproduced the art director's ranking (feet 16.5, cloak 8.2, base 6.6, legs 6.4).
- [ ] Use the shared tool's numbers. A lane's own variant of a metric is not comparable, and when a definition changes, give old and new values for the same render side by side.
- [ ] Report regional and global numbers together, wins, losses and secondary regressions (`python -m kit.regions --region ... --pale ...`). One variable per A/B.
- [ ] Write reviews the way the art director does: rank what the eye catches first at 160 px; give each item a pixel box at 256, the measured value on both sides and the change wanted. "Feet region luminance 169 vs 141" survives a round; "feet too pale" does not.
- [ ] Check a review observation against the source before acting on it. R14: a review called the rest cloak wider after a lane that had not touched rest geometry; the merge proved the rest pixels identical.
- [ ] Review clips with the final look applied. **[proven]** a "cloak fin" flagged in three reviews of a hybrid preview was the helmet crest once the look was on.
- [ ] Once a unit is a candidate for the owner, polish without disturbing what passes: if any metric or clip regresses against the candidate, keep the candidate's version of that part and say so in the note; then stop iterating until the owner has seen it (reviewer on Spearman R14).
- [ ] Keep a regression list of items earlier rounds closed and tick them on every new render. **[proven]** R12 lost the base lip R11 had fixed, and the merge note showed only a regional ΔE.
- [ ] With several builders: judge per aspect (silhouette, materials and values, each clip) and merge the best of each. Do not stack two fixes for the same region; pick one and re-measure. **[proven]** two builders split by aspect took the Spearman from IoU 0.905 to 0.920 with colour inside target in about 50 minutes; three lanes plus a merge on one candidate had moved it 0.9035 → 0.9039 in 67.
- [ ] Each round note ends with ranked visible gaps and three FOCUS lines (a: form, b: surface, c: motion), and adds a row to `LOG.md` (time, tokens, metric before → after).

### 11. Lane hygiene

- [ ] Before every handoff: `python3 tools/art/anim3d/kit/check_imports.py`. `blender --python` does not put the script's folder on `sys.path`. **[proven]** R12's GPU pass died two minutes in on a sibling import that 33 sandbox tests had passed.
- [ ] A new gate in `gpu.sh` goes before the expensive stages, and is calibrated against its own noise before it is allowed to fail the pass. Two of three GPU launches on 2026-11-24 died on a gate or import the sandbox could not exercise (R12: 2 minutes lost; R13: 25).
- [ ] Codex sandboxes cannot take `index.lock` or `ORIG_HEAD.lock`: leave changes uncommitted with a `commit-message.txt` and a lane-only patch; the runner commits.
- [ ] Lane masters and preview atlases live in `lanes/<slug>-r<N><lane>/`. Port lane changes by scoped diff.
- [ ] Record rejected experiments with their numbers; they are as reusable as the wins.
- [ ] Per-object shader variants need distinct material cache keys; a cache keyed by part alone lets the first object's settings silently override the rest (R13b).
- [ ] Do not name a script after a standard-library module (`inspect.py` broke numpy). `bpy.data.libraries.load` replaces the assigned name list; pass a copy if you need the names.
- [ ] A byte-backed sRGB image read through bpy gives encoded values: linearise once before writing a `FLOAT_COLOR` attribute, and cache normals before adding a colour attribute.

## Not yet proven on a unit

Try one at a time with a same-settings A/B; move it into the checklist with its evidence or delete it.

- Multi-view paintovers (side, back) baked to a packed surface unwrap, for units seen from more than the hero angle.
- Pose-space correctives (Blender Studio's Pose Shape Keys extension, GPL) for shoulders, elbows and knees.
- CMU mocap (free-use, **not CC0**; credit CMU/NSF EIA-0196217) for a less stylised walk; no retarget map exists yet.
- Stroke texture on unseen fills (Bump from stretched noise, strokes 1–3 final pixels wide).
- `scripts/technique_probe.py` and `kit/probe_human.py` check mechanisms on synthetic scenes (frozen UVs, Standard view round trip, roll-preserving retarget, MPFB and Rigify generation); they certify no art. Details in `references/verification.md`.

## Sources and licences

Recheck the licence file of anything downloaded.

- Blender (GPL); manual (CC-BY-SA 4.0): [Shader to RGB](https://docs.blender.org/manual/en/4.5/render/shader_nodes/converter/shader_to_rgb.html), [colour management](https://docs.blender.org/manual/en/4.5/render/color_management.html), [Bone.convert_local_to_pose](https://docs.blender.org/api/current/bpy.types.Bone.html#bpy.types.Bone.convert_local_to_pose).
- [MPFB](https://github.com/makehumancommunity/mpfb2): code GPL-3.0-or-later; bundled body and assets CC0.
- [Quaternius Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html): CC0, free Standard subset only. KayKit Character Animations Free 1.1: CC0 (URL and hashes in `units/spearman/SOURCES.md`).
- [CMU Graphics Lab mocap](http://mocap.cs.cmu.edu/): free-use, no resale of the data, **not CC0**.
- [ambientCG](https://docs.ambientcg.com/license/) and [Poly Haven](https://polyhaven.com/license): CC0 textures (pinned in `assets.lock.json`).

## Learned

One line per finding, newest first; the rule lives in the step in brackets. Round agents: add a dated line, edit the step it changes, and delete any rule it contradicts rather than leaving both. Unit-specific open items go in `references/<slug>-status.md`, not here.

- 2026-11-24 Fable C (IoU 0.9534, blurred ΔE 3.35, feet 5.4; first to pass every target): measure feet on a gridded crop first; an orthographic camera hides depth; registration before colour; the painted ground shadow is two ankle-anchored blobs; a guard change leaks into every clip. One render path for delivery and review. [1, 3, 5, 8]
- 2026-11-24 R15 lanes (polish, nothing regressed): sandal straps recovered from the source pigment (feet 5.45 → 4.72); a cloak edit and a walk rephase rejected for regressing other clips. [4, 5]
- 2026-11-24 reviewer: round 14 is the first full candidate to show Sam (rest matches the painting, all five clips read at 160 px); round 15 polishes four items without regressing anything, then the loop holds. [10]
- 2026-11-24 R14 (polish on a passing unit; rest pixels unchanged): cloth loop seams measured and closed; walk rephased to soften the idle cut; cloak sweep damped by measurement; a fully contained side-lying death rejected for losing the shield face; support queried on evaluated faces; parity gate moved early, and the GPU pass ran clean on its first launch (IoU 0.9537, blurred ΔE 3.51 held). [5, 7, 10]
- 2026-11-24 R13 GPU: **IoU 0.9537, blurred ΔE 3.51, every region under 6 (feet 5.3)**: the first round to pass both targets, thirteen rounds and about 30 hours after the first render. Its first launch failed at an exact pixel-parity gate on sample noise: calibrate gates, and put them first. [8, 10, 11]
- 2026-11-24 R13 merge (Fable C's guard, feet, base and look; R13c's walk and collapse): CPU proxy IoU 0.9394 → 0.9513, blurred ΔE 4.55 → 3.39, feet 13.35 → 5.45; whole-track walk registration; look and delivery share one render function with a pixel-equality gate. [5, 8]
- 2026-11-24 R13 lanes: small gains beside Fable C (IoU 0.9358 → 0.9367; base 4.77 → 4.00; swing clearance 114 → 76 mm); a failing region's average says where, not what; check zero-offset IoU too. [1, 5, 10]
- 2026-11-24 R12 GPU (IoU 0.9384, blurred ΔE 4.72): best on every aspect, feet the only failing region; a fix from R11 regressed, hence the regression list; a Blender-only import broke the first launch, hence `check_imports`. [10, 11]
- 2026-11-24 R12 lanes: foot length cannot grow inside the contact limits, width can; a better CC0 donor beat correcting a bad one; revealed surfaces painted from rest-space masks; soles must touch the stone. [1, 4, 5]
- 2026-11-24 Fable B: tune form by measured row spans, not by eye (IoU 0.894 → 0.932); keyed collapse authored with a one-minute quick-look loop; 8.5 cm ankle offset for a readable walk. [1, 5]
- 2026-11-24 Fable A: Eevee emission-only look with per-part paint and painting-fitted ramps; registration fitted by image (0.9% error cost 3 ΔE); reduce like the painting. [3, 4, 8]
- 2026-11-24 reviewer: colour is scored blurred at zero offset and per region; idle and walk from open mocap, reactions by review; split builders by aspect. [5, 10]
- 2026-11-24 art director: reviews carry pixel boxes and measured values; first tells at 160 px were thin dark props, pale small feet and calves outside the greaves; never crop the weapon; review clips with the look on. [1, 5, 10]
- 2026-11-23 R11: free armour that carries foot weights; sleeve smoothing does not fix a shoulder; keep source pigment and coverage alpha. [1, 2, 4]
- 2026-11-23 R10: material-ID render before repainting; attenuation limits on a donor walk; previews and GPU finals rank the same. [4, 5, 8]
- 2026-11-23 R9: full-rotation retarget with heel/toe locking replaced hand-built motion ("duck feet"). [5, 6]
- 2026-11-23 R6–R8: bake MPFB macro shape keys before fitting; audit against the real disc; elbow poles share the guard. [2, 5, 7]
- 2026-11-22 R4–R5: visibility by ray distance; relief clearance on evaluated faces; register ornament before projecting. [1, 3]
- 2026-11-22 R1–R3 (Sam): "looks like something a high school student would make" → camera projection of the painting and real geometry finish; R2 "huge improvement". [1, 3]
