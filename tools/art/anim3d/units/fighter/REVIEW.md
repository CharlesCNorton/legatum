# Fighter — round 1 candidate

Original full-volume aircraft, mechanical rig, five authored clips, frozen painting
UVs, generated hidden-surface painted fill, six actual AO/curvature maps, and serial
CPU/GPU rendering/packing tools are implemented. External editable masters, 512/256
frames and render evidence live in `~/LegatumRuns/anim-pilot/masters/fighter/`.
All review stages and the eight-second MP4 live in `review/3d-v2/fighter-*` under the
same external root. Provenance and input hashes accompany the scripts.

The rest silhouette, olive/silver scheme, elevated composition and cream pedestal
read as the same fighter at 64 px. At 256 px the canopy/fuselage join, propeller
profile, warmer base shading, subtle surface lighting and broken-support crash
presentation still need work. The final crash is currently an intact nose-down
settled aircraft; the support switches off at impact. No smoke volume or zero-scaled
mesh is used. Projection is a fixed-view technique: larger rotations reveal areas
filled from generated brushwork, not independent multi-view source paintings.

No art PASS is claimed. Technical closure/atlas checks do not establish painting
parity. CPU renders use 8 samples; the lead must inspect the GPU rendition.

```sh
ROUND=1 tools/art/anim3d/units/fighter/gpu.sh
```

This executable takes no positional arguments. It renders all stages with Cycles
Metal, keeps actual 512/256 masters, rebuilds the 160 px trimmed atlas, validates it,
audits the geometry, and verifies the five-clip H.264 review video. All five strips,
animated WebPs, detail/rig sheets and the rest-pose crossfade are regenerated.

Non-obvious findings: outward-facing wing normals are essential for projection
confidence; otherwise the procedural underside replaces the painting. Foreground
propeller paint must be excluded from the wing underneath to avoid a static second
propeller when the real blades turn. Preserve independent bake and frozen-camera UV
layers. Pillow's RGBA `getbbox()` defaults to alpha-only: exact held-frame comparison
must explicitly use `alpha_only=False`.
