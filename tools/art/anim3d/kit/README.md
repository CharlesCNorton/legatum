# Painted-miniature kit

Reusable code and small presets for turning a unit painting into a 3D model with five animated clips. Everything here was pulled out of the Spearman scripts, the first unit through the pipeline. The method, settings and evidence are in `../SKILL.md`; per-round cost and metrics are in `../LOG.md`.

Code and presets only. Scene, rig, texture and render masters stay under `ANIM_ROOT` (`~/LegatumRuns/anim-pilot`).

## Start a new unit

Work in `tools/art/anim3d/units/<slug>/`. Get a crude version through every stage before polishing any of them.

1. **Preset.** Copy `presets/spearman.json` to `presets/<slug>.json`. Fit the camera and lights to the new painting (shadow direction with the key alone first); set `delivery.anchor`, the A/B `regions` and the `critique_regions` boxes (head, torso, cloak, shield or weapon, legs, feet, base) at 256 px.
2. **Body and rig** (Blender). `human.create_body(macro_overrides, name)` then `human.add_rig(body, name)` gives the MPFB body with its 53-bone `game_engine` rig and original weights. On the disposable projection copy call `human.freeze_macro_mix(body)` before fitting any vertices.
3. **Camera, light, base** (Blender). `studio.match_camera(scene, '<slug>')`, `studio.match_lighting(scene, '<slug>')`. Build the shared cream disc with `base.build(scene)` (top #E9CFA0, side #B68A51, top at z = 0.105 m) and verify it with `audit.check_base`.
4. **Clay check** (Blender). `ab.clay_override(scene)`, render, and compare the silhouette with the painting before any texture work.
5. **Projection and fills** (Blender). `projection.freeze_projection(...)` at the fitted rest pose; `seams.underpaint(...)` for narrow unpainted wedges; `materials.painted_fill(...)` for unseen surfaces. If a pale patch shows up in a motion pose, run `ab.material_id_render(...)` on that pose first.
6. **Motion** (Blender). `retarget.prepare(rig, root, clip, phases, motion)` for idle, move, hit and death from the pinned Quaternius actions; it locks the walk's feet. The unit supplies a `motion` module (walk influence, time remap, hit envelope, death blends: copy `units/spearman/motion.py`) and hand-keys only the attack. Each sole object needs `toe_vertex` and `heel_vertex` custom properties for `contact.landmarks`.
7. **Checks** (Blender). `audit.check_bounds_and_contact`, `audit.check_shaft`, `audit.check_transition` on every delivered pose; `feet.sample_dense` then `feet.measure`, `feet.failures`, `feet.step_width` on the walk; `motion_metrics.sample` and `summarise` on death and hit.
8. **Grade and deliver** (venv Python). Fit one grade on the rest render with `grade.fit_file`, then:

   ```sh
   cd tools/art/anim3d
   $ANIM_ROOT/venv/bin/python -m kit.deliver --slug <slug> --frames <raw frames dir> \
     --grade <grade.json> --master <unit.blend> --anchor <ax,ay> \
     --out <lane atlas dir> --review $ANIM_ROOT/review/3d-v2 --label 'CPU preview' --round <N>
   ```

9. **Critique** (venv Python). `../critique.py` for whole-image IoU and ΔE, the triptych and the contact sheet; `python -m kit.regions` for before/after numbers on named regions (`--region`, `--pale`, `--stats`) and for wasted or jumping frames (`--clips <decoded-160 dir>`).

## Modules

"Verified" says how the kit copy itself was checked, not whether the art is good.

| Module | What it does | Verified |
| --- | --- | --- |
| `human.py` | MPFB body, `game_engine` rig (or opt-in Rigify), `freeze_macro_mix`, `add_hinge_corrective` (authored rest-space deltas with a hinge driver). | `probe_human.py` in Blender (round 10): 19,158 vertices, 53 bones, 930-bone Rigify. `freeze_macro_mix` is the Spearman `refine.py` code; not yet run from the kit. |
| `studio.py`, `presets/<slug>.json` | Fixed orthographic camera and disk area lights from a preset; Standard view transform. | Used by Spearman `project.py` and `refine.py` since round 10. |
| `projection.py` | Frozen hero-camera UVs and a ray-distance visibility mask on original topology. | Used by Spearman `project.py`. Tolerances (18 mm, 140 mm relief) are Spearman's. |
| `seams.py` | Geodesic continuation of trusted paint (75 mm reach) into a corner attribute. | Used by Spearman `surface_finish.py`. |
| `materials.py` | Camera-only pigment over a physical BSDF, shared cavity-pigment node group. | Used by Spearman `paint_finish.py`. Cycles only. |
| `retarget.py`, `retarget_presets.py`, `contact.py` | Quaternius Standard → MPFB `game_engine`: full-rotation retarget with rest-roll calibration, cyclic heel/toe locking with one fitted speed, IK contact correction. | Used by Spearman `infantry/retarget.py`. Assumes −Y travel, 24 fps sampling, `Leather sandal sole <side>` objects. No CMU or Rigify map. |
| `base.py` | The shared cream stone disc: two materials, fine grain, physical shading plus camera-only pigment, cloth collision. | Rebuilt from the Spearman base code; **not yet run from the kit in Blender**. |
| `ab.py` | A/B preview settings (CPU, 256 px, 16 samples, seed 17), scene invariant hashes, clay override, material-ID render. | Copied from round-10 lane scripts that ran; **not yet run from the kit in Blender**. |
| `audit.py` | Base contract, camera bounds, disc-footprint and ground contact, shaft crossings and grip, arm continuity with idle. | Generalised from Spearman `audit.py`; **not yet run from the kit in Blender**. |
| `motion_metrics.py` | Head step, ankle height, equipment grip range and rotation step, late cloth travel on delivered samples. | Generalised from Spearman `motion_metrics.py`; **not yet run from the kit in Blender**. |
| `feet.py` | Dense walk-cycle sampling of the real soles (Blender), then contact slip, floor error, heading, step width and swing lift with the enforced limits (plain Python). | Tests; `measure` reproduces the stored round-10 Spearman checks from its sampled rows (slip 0.0018 mm, floor 1.133 mm, heading 2.618°). `sample_dense` not yet run from the kit in Blender. |
| `grade.py` | One monotone histogram grade fitted at rest (strength 0.80), bound to the master hash. | Tests, and reproduces the Spearman round-10 LUT and graded rest render exactly. |
| `images.py` | Linear-light, premultiplied-alpha Lanczos resize. | Tests; used by Spearman `delivery.py`. |
| `atlas.py`, `deliver.py` | Trimmed atlas v2 pack, decode, validate, five-clip movie; CLI over a frames folder. | Tests, and reproduces the Spearman round-10 preview atlas and JSON byte for byte (183,016 bytes, q80). |
| `regions.py` | Region IoU, region RGB error, pale-pixel count, reviewer stats per box (pixels, mean RGB, luminance mean and p90), prop width on a row, wasted and jumping frames in a clip, native-size comparison sheet. CLI: `python -m kit.regions`. | Tests, and reproduces round-9/10 numbers from the real renders (whole IoU 0.8983 → 0.8989, lower legs 71.96% → 72.86%) and the art director's round-10 findings (feet luminance 187 vs 146; death frames 6–8 barely change). |
| `critique.py`, `report.py` | Whole-image IoU (±3 px); colour as CIE76 ΔE on blurred images (2 px Gaussian at 256) with per-region values from `--preset` or `--region`, raw per-pixel ΔE for information; triptych, crossfade, heatmaps, 160 px contact sheet; inserts evidence above the FOCUS lines of a round note. | `../test_critique.py` (4 tests); run every round through `../critique.py`. Blurred and regional values added 2026-11-24 and measured on the round-9 and round-10 renders. |

## Tests

```sh
$ANIM_ROOT/venv/bin/python tools/art/anim3d/kit/test_kit.py   # 17 tests, about 20 s, no Blender
(cd tools/art/anim3d && $ANIM_ROOT/venv/bin/python test_critique.py)   # 4 tests
```

`probe_human.py` runs in Blender through the gate with the pipeline's isolated MPFB resources.

## Rules for changing the kit

- The Spearman scripts import `human`, `studio`, `projection`, `seams`, `materials`, `retarget`, `retarget_presets`, `contact`, `images`, `critique` and `report`. Changes to those must keep the Spearman's output identical; add a parameter with the current value as its default rather than changing behaviour.
- Unit-specific choices (object names, colours, tolerances, timing curves) go in the unit's folder or its preset, not here.
- A module copied out of a unit script is "not yet run from the kit" until a round runs it in Blender. Update the table when one does.
- When a second unit needs something the kit assumes away (travel axis, sole object names, another donor skeleton), add the parameter then, with that unit as the test.
- The kit does not make art decisions. Rigify, corrective helpers and the node group are mechanisms; a passing probe or test is not a unit PASS.

## Round 11 painted-look reuse

`look.Graph` is Fable A's Blender node builder (ordered palette ramps,
Eevee diffuse-to-value conversion, emission, texture and mix nodes).
`part_paint.push_pull` and `low_frequency` continue each part's trusted painting
through unseen texels without importing another part's colour. Spearman imports
these directly; object classification and palette settings stay unit-local.
`images.resize_rgba(..., space="display")` matches a reference reduced
in display space; existing callers retain the linear default. The selected
policy must also be used when independently decoding/validating atlas alpha.

MPFB/Rigify/corrective setup, frozen projection, geodesic seam fill, studio
matching, Quaternius retarget and contact locking remain in the modules above.
Rigify and anatomical corrective authoring remain opt-in, not a claimed
Spearman rig migration. No verified CMU-to-Rigify mapping is claimed.

The late skill-branch modules `registration`, `quicklook` and `quicksheet` are also available. Round 11 imported the shared Eevee graph and part-paint implementation rather than keeping parallel copies; the Blender graph was constructed against the rest and all five merged clips without changing geometry, camera or action hashes. GPU pixel validation remains a separate handoff.
