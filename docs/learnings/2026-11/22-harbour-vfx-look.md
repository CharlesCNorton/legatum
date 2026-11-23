## 2026-11-22: Harbour VFX requires look checks as well as simulation checks

- The lead's v1 render proved motion but exposed broad pale foam, an untextured Shader-to-RGB/emission finish, a sail occlusion and a temple close-up. Nonzero simulation grids and moving vertices alone do not verify appearance.
- Replace the broad foam colour ramp with a clamped crest mask; retain coloured illumination through Principled pigment materials. CPU previews can inspect this material path without Metal, but they cannot certify Eevee reflections or volumetric appearance.
- The installed Blender 5.3 sky API uses `MULTIPLE_SCATTERING` / `aerosol_density`, not the older `NISHITA` / `dust_density`. Inspect installed RNA properties when adapting skill recipes.
- Keep each review generation in a separate masters directory. Record actual bake timings, cached-grid readbacks and projected framing alongside the render critique in `tools/art/era-video/review/vfx-v1-critique.md`.
