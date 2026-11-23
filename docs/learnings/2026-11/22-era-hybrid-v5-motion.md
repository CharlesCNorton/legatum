## 2026-11-22: Era hybrid motion must be measured at delivery size

- The supplied v4 contact sheet/crops and owner feedback approve the painted look and camera, but reject the almost invisible ship, smoke, birds and cloth. V4's own scene used a 14-unit hull and only 80 source pixels of travel.
- V5 sizes the hull and path numerically at 960×540; the built scene checks the same bounds before baking. A larger hull in front of a shallow relief needs shoreline occlusion and camera-ray alignment for its water reflection/wake, otherwise those effects separate during the push.
- Nonzero maximum smoke density proves only that the emitter produced smoke. V5 also reads the vertical extent of the density grid. Blender's fluid RNA returns the noise grid when noise is enabled, so reshape with the corresponding resolution.
- Keep the lead's type-aware `setv()` socket selection and the Blender 5.3 compositor node-group interface. No Blender was run in this editing pass; visual quality, runtime compatibility and the eight-minute bake target await the lead's locked run.
