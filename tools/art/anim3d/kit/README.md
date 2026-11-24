# Painted-miniature kit

Reusable code and small presets for turning a unit painting into a 3D model with five animated clips. Everything here was pulled out of the Spearman scripts, the first unit through the pipeline. The method, settings and evidence are in `../SKILL.md`; per-round cost and metrics are in `../LOG.md`.

Code and presets only. Scene, rig, texture and render masters stay under `ANIM_ROOT` (`~/LegatumRuns/anim-pilot`).

## Start a new unit

Work in `tools/art/anim3d/units/<slug>/`. Get a crude version through every stage before polishing any of them.

1. **Preset.** Copy `presets/spearman.json` to `presets/<slug>.json`. Fit the camera and lights to the new painting (shadow direction with the key alone first); set `delivery.anchor`, the A/B `regions` and the `critique_regions` boxes (head, torso, cloak, shield or weapon, legs, feet, base) at 256 px.
2. **Body and rig** (Blender). `human.create_body(macro_overrides, name)` then `human.add_rig(body, name)` gives the MPFB body with its 53-bone `game_engine` rig and original weights. On the disposable projection copy call `human.freeze_macro_mix(body)` before fitting any vertices.
3. **Camera, light, base** (Blender). `studio.match_camera(scene, '<slug>')`, `studio.match_lighting(scene, '<slug>')`. Build the shared cream disc with `base.build(scene)` (top #E9CFA0, side #B68A51, top at z = 0.105 m) and verify it with `audit.check_base`.
4. **Clay check** (Blender). `ab.clay_override(scene)`, render, and compare the silhouette with the painting before any texture work.
5. **Projection and fills.** First fit the registration (venv Python): `python -m kit.registration <slug>-source.png <slug>-256.png`, and pass its `registration` to the projection. Then in Blender: `projection.freeze_projection(...)` at the fitted rest pose; `seams.underpaint(...)` for narrow unpainted wedges; `materials.painted_fill(...)` for unseen surfaces. If a pale patch shows up in a motion pose, run `ab.material_id_render(...)` on that pose first. For the Eevee painted look (SKILL.md step 5, method B) build per-part textures and ramps with `part_paint` and the materials with `look.Graph`; the Spearman's `look.py` and `look_textures.py` on `fable/unit-anim-3d-spearman-a` are the worked example.
6. **Motion** (Blender). `retarget.prepare(rig, root, clip, phases, motion)` for idle and move from the pinned Quaternius actions; it locks the walk's feet. The unit supplies a `motion` module (walk influence, time remap, hit envelope, death blends: copy `units/spearman/motion.py`) and keys the attack. Key death and hit too when the donor does not stage on the base (the Spearman's `collapse.py` on `fable/unit-anim-3d-spearman-b` is the worked example), iterating with `quicklook.py` and `quicksheet.py`. Each sole object needs `toe_vertex` and `heel_vertex` custom properties for `contact.landmarks`.
7. **Checks** (Blender). `audit.check_bounds_and_contact`, `audit.check_shaft`, `audit.check_transition` on every delivered pose; `feet.sample_dense` then `feet.measure`, `feet.failures`, `feet.step_width` on the walk; `motion_metrics.sample` and `summarise` on death and hit.
8. **Grade and deliver** (venv Python). Fit one grade on the rest render with `grade.fit_file`, then:

   ```sh
   cd tools/art/anim3d
   $ANIM_ROOT/venv/bin/python -m kit.deliver --slug <slug> --frames <raw frames dir> \
     --grade <grade.json> --master <unit.blend> --anchor <ax,ay> \
     --out <lane atlas dir> --review $ANIM_ROOT/review/3d-v2 --label 'CPU preview' --round <N> --reduce display
   ```

9. **Critique** (venv Python). `../critique.py` for whole-image IoU and ΔE, the triptych and the contact sheet; `python -m kit.regions` for before/after numbers on named regions (`--region`, `--pale`, `--stats`) and for wasted or jumping frames (`--clips <decoded-160 dir>`).

## Modules

"Verified" says how the kit copy itself was checked, not whether the art is good.

| Module | What it does | Verified |
| --- | --- | --- |
| `human.py` | MPFB body, `game_engine` rig (or opt-in Rigify), `freeze_macro_mix`, `add_hinge_corrective` (authored rest-space deltas with a hinge driver). | `probe_human.py` in Blender (round 10): 19,158 vertices, 53 bones, 930-bone Rigify. `freeze_macro_mix` is the Spearman `refine.py` code; not yet run from the kit. |
| `studio.py`, `presets/<slug>.json` | Fixed orthographic camera and disk area lights from a preset; Standard view transform. | Used by Spearman `project.py` and `refine.py` since round 10. |
| `registration.py` | Fits where the full-size painting sits on the 256 px canvas (isotropic scale and offset, by image comparison); returns the tuple `freeze_projection` takes. CLI: `python -m kit.registration`. | Test, and on the Spearman gives 5.3421 source px per canvas px, matching the look lane's independent 5.3425 (the bounding-box calibration in use was 0.9% off). |
| `projection.py` | Frozen hero-camera UVs and a ray-distance visibility mask on original topology. | Used by Spearman `project.py`. Tolerances (18 mm, 140 mm relief) are Spearman's. |
| `seams.py` | Geodesic continuation of trusted paint (75 mm reach) into a corner attribute. | Used by Spearman `surface_finish.py`. |
| `materials.py` | Camera-only pigment over a physical BSDF, shared cavity-pigment node group. | Used by Spearman `paint_finish.py`. Cycles only. |
| `retarget.py`, `retarget_presets.py`, `contact.py` | Quaternius Standard → MPFB `game_engine`: full-rotation retarget with rest-roll calibration, cyclic heel/toe locking with one fitted speed, IK contact correction. Optional hooks on the unit's `motion` module since round 11: `walk_calibration_axis` (keep some leg spread in the walk's reference pose) and `blend_walk_source` (donor torso drives the carrying arms). | Used by Spearman `infantry/retarget.py`. Assumes −Y travel, 24 fps sampling, `Leather sandal sole <side>` objects. No CMU or Rigify map. |
| `base.py` | The shared cream stone disc: two materials, fine grain, physical shading plus camera-only pigment, cloth collision. | Rebuilt from the Spearman base code; **not yet run from the kit in Blender**. |
| `part_paint.py` | Per-part paint: keep a part's own painted pixels and inpaint the rest (push-pull), low-frequency local colour, value ramps from the part's painted pixels. | Tests. Copied from the Fable look lane (`239540b5`), where it produced the art director's preferred materials; the Spearman imports it from the kit since round 11. |
| `look.py` | Eevee node helpers for the render-time painted look: `Graph` (emission-only graphs, form and cast-only light terms, ordered ColorRamp), `ramp_stops`, `key_sun` (strength π). | `Graph` copied from the Fable look lane, where it ran in Blender 5.3 Eevee. Round 11: the Spearman imports it from the kit and the graph was constructed on the merged rest and all five clips with geometry, camera and action invariants passing. `key_sun` not yet run. |
| `quicklook.py`, `quicksheet.py` | Render chosen frames of a clip from the painting camera plus top, front, side and back, optionally in clay, with unbaked cloth switched off; tile them into one sheet. The authoring loop for keyed clips. | Copied from the Fable form-and-motion lane (`91e3031c`), where they ran in Blender 5.3; behaviour unchanged. |
| `ab.py` | A/B preview settings (CPU, 256 px, 16 samples, seed 17), scene invariant hashes, clay override, material-ID render. | Copied from round-10 lane scripts that ran; **not yet run from the kit in Blender**. |
| `audit.py` | Base contract, camera bounds, disc-footprint and ground contact, shaft crossings and grip, arm continuity with idle. | Generalised from Spearman `audit.py`; **not yet run from the kit in Blender**. |
| `motion_metrics.py` | Head step, ankle height, equipment grip range and rotation step, late cloth travel on delivered samples. | Generalised from Spearman `motion_metrics.py`; **not yet run from the kit in Blender**. |
| `feet.py` | Dense walk-cycle sampling of the real soles (Blender), then contact slip, floor error, heading, step width and swing lift with the enforced limits (plain Python). | Tests; the Spearman uses the shared limits since round 11; `measure` reproduces the stored round-10 Spearman checks from its sampled rows (slip 0.0018 mm, floor 1.133 mm, heading 2.618°). `sample_dense` not yet run from the kit in Blender. |
| `grade.py` | One monotone histogram grade fitted at rest (strength 0.80), bound to the master hash. | Tests, and reproduces the Spearman round-10 LUT and graded rest render exactly. |
| `images.py` | Premultiplied-alpha Lanczos resize, in linear light (default, the Spearman delivery through round 10) or display space (`space='display'`, how the painted tokens were reduced; adopted 2026-11-24). | Tests; used by Spearman `delivery.py`. |
| `atlas.py`, `deliver.py` | Trimmed atlas v2 pack, decode, validate, five-clip movie; CLI over a frames folder, `--reduce linear|display`. | Tests, and reproduces the Spearman round-10 preview atlas and JSON byte for byte (183,016 bytes, q80, linear). The same frames in display space: 198,944 bytes at q85. |
| `regions.py` | Region IoU, region RGB error, pale-pixel count, reviewer stats per box (pixels, mean RGB, luminance mean and p90), prop width on a row, row and column outline spans against the painting (`--rows`, `--columns`), wasted and jumping frames in a clip, native-size comparison sheet. CLI: `python -m kit.regions`. | Tests, and reproduces round-9/10 numbers from the real renders (whole IoU 0.8983 → 0.8989, lower legs 71.96% → 72.86%) and the art director's round-10 findings (feet luminance 187 vs 146; death frames 6–8 barely change). |
| `critique.py`, `report.py` | Whole-image IoU (±3 px); colour as CIE76 ΔE on blurred images (2 px Gaussian at 256) at zero offset with per-region values from `--preset` or `--region`, raw per-pixel ΔE for information; triptych, crossfade, heatmaps, 160 px contact sheet; inserts evidence above the FOCUS lines of a round note. | `../test_critique.py` (4 tests); run every round through `../critique.py`. Blurred and regional values added 2026-11-24 and measured on the round-9 and round-10 renders. |

## Tests

```sh
$ANIM_ROOT/venv/bin/python tools/art/anim3d/kit/test_kit.py   # 24 tests, about 35 s, no Blender
(cd tools/art/anim3d && $ANIM_ROOT/venv/bin/python test_critique.py)   # 4 tests
```

`probe_human.py` runs in Blender through the gate with the pipeline's isolated MPFB resources.

## Rules for changing the kit

- The Spearman scripts import `human`, `studio`, `projection`, `seams`, `materials`, `retarget`, `retarget_presets`, `contact`, `images`, `critique` and `report`. Changes to those must keep the Spearman's output identical; add a parameter with the current value as its default rather than changing behaviour.
- Unit-specific choices (object names, colours, tolerances, timing curves) go in the unit's folder or its preset, not here.
- A module copied out of a unit script is "not yet run from the kit" until a round runs it in Blender. Update the table when one does.
- When a second unit needs something the kit assumes away (travel axis, sole object names, another donor skeleton), add the parameter then, with that unit as the test.
- The kit does not make art decisions. Rigify, corrective helpers and the node group are mechanisms; a passing probe or test is not a unit PASS.

Round 12 additions: `continuity.prepare(scene, classify, sole_prefixes=...,
body_prefix=...)` and `continuity.pigment(...)` preserve leather undersides,
shadowed skirt lining and rear shoulder cloth using rest-space masks. The
Spearman wrapper supplies names. `cpu_look.graph_for_sun(direction)` is an
explicit Cycles preview proxy for `look.Graph`, without cast shadows; never
label its output Eevee or use it to approve contact shadow. Existing `human`
MPFB/Rigify/corrective helpers, `materials`, `projection`, `seams`, `studio`,
Quaternius `retarget_presets`/foot locking and `critique` remain the starting kit.
CMU mapping is not implemented or claimed; Quaternius is the verified human
preset. Rigify and authored corrective shapes remain opt-in for new units.

`contact.seat_rest_guard` seats the complete fitted guard on evaluated soles
before neutral capture and projection. Rest contact is checked independently
from walk contact; moving a rest guard never substitutes for retarget locking.
KayKit Free 1.1 bone/action names now join the Quaternius preset in
`retarget_presets.py`; the Spearman reaction adapter uses that shared map.
