# Painted-miniature kit

Small code and presets only; all scene/rig/texture masters stay in `ANIM_ROOT`.
Spearman round 10 uses these mechanisms through the existing entry points.

| Module | Used by / contract |
| --- | --- |
| `human.py` | `scene.py`: MPFB macro body and original-weight game_engine skeleton. New units may explicitly request MPFB's Rigify generation. `add_hinge_corrective` accepts authored **rest-space** deltas; never converts a posed sculpt by pretending it is rest geometry. It is a driver utility, not an anatomical sculpture. |
| `materials.py` | `infantry/paint_finish.py`: shared painterly cavity-pigment node group, camera-only Emission and retained physical secondary rays. Colour and cavity amount remain per-material inputs. This is the existing Cycles hybrid, not Eevee Shader-to-RGB. |
| `projection.py` | `project.py`: frozen hero UVs and facing/visibility; caller supplies source registration. Existing relief tolerances are Spearman-specific and still coarse; do not use them blindly for other units. |
| `seams.py` | `infantry/surface_finish.py`: geodesic underpaint into unseen fills, per-corner attribute. It does not author missing back/underside artwork or bake to PaintUV. |
| `studio.py`, `presets/spearman.json` | `project.py` and `infantry/refine.py`: fixed orthographic camera and matched product lights. Sample a new unit's painting before copying the preset. |
| `retarget.py`, `retarget_presets.py`, `contact.py` | `infantry/retarget.py`: pinned Quaternius Standard source, full rotation/rest-roll conversion and cyclic heel/toe locking; unit motion layers injected explicitly. Preset targets MPFB game_engine, -Y travel, 24 fps sampling and authored sandal landmarks. CMU and Rigify mapping remain future presets; no untested support is claimed. |
| `images.py` | `delivery.py`: linear-light premultiplied downsample, decoded trim/alpha verification. `ATLAS_OUTPUT` isolates CPU previews from shipped assets. |
| `critique.py`, `report.py` | Stable public `../critique.py` CLI: IoU, CIE76 ΔE, 256 triptych, crossfade, 160 contact sheet, feet copy, note insertion before focus lines. Include base in interpretation; an IoU target is not art approval. |

Run `venv/bin/python tools/art/anim3d/kit/test_kit.py` for edge/colour/note
regressions. `probe_human.py` runs through the plain `blender` gate with the
pipeline's isolated MPFB resources; never alongside another heavy owned job.
Production Spearman keeps its tested 53-bone rig. Optional Rigify and the driver
probe do not certify shoulder/knee deformation or supply corrective sculptures.
