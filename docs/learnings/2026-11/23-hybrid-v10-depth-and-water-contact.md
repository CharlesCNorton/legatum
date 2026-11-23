## 2026-11-23: Hybrid ship clearance does not establish depth or water contact

- The user's v9 render review rejected a large galley at the horizon despite a
  passing clearance check. Screen separation alone cannot validate perspective.
- The relief depth is artistic disparity. In v10, interpolate measured nearby
  painted hull sizes by sampled depth and log the size ratio on every frame;
  keep the much larger merchant galley as a separate size comparison.
- Check the original water mask too. The first middle-harbour candidate cleared
  every ship but crossed a foreground cypress; the final x=528→517, y=550 lane
  keeps the full contact strip and reflection centre on water in all 144 frames.
- Position the immersed contact on the sampled water ray, then lift the CG model
  for visibility. Share placement/scale with contact shading and reflection.
- Preparation passes; Blender and rendered visibility remain the lead's checks.
