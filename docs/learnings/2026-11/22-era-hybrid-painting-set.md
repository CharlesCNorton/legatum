## 2026-11-22: Preserve the era painting as the cinematic set

- User review of the v3 comparison/contact sheet rejected primitive city geometry
  plus a strong oil filter: box houses, muddy textures, a striped ground plane,
  flat cyan water, pink fire glow and two white wake blobs did not match the painting.
- The v4 direction uses the existing edge-aware depth painting and inpainted
  backplate as the set, with local 3D motion: projected water, a harbour-scale
  vessel, smoke/fire, cloth displacement and gulls. Filter only CG surfaces.
- `tools/art/era-video/hybrid/` contains the implementation and commands. Python
  preparation and projection checks ran; Blender, bake timing and visual quality
  remain unverified for the lead's machine-wide lock run. This is an authored
  hybrid candidate, not a validated replacement render.
