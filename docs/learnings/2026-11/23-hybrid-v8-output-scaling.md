# Hybrid v8: output size is independent of the fluid cache

The hybrid scene stores an entire baked `.blend`, including its render and
compositor settings. Adding a build-only resolution flag would silently render
960x540 when a 1920x1080 request reuses that cached scene. V8 reapplies output
settings immediately after loading the cache and recomputes projection readbacks.
Both sizes share one simulation; resolution is deliberately outside its signature.

The shore polygons, masks and all placements were already authored in 1920x1080
source coordinates and project through UVs/world space. They must not be doubled
again for full output. Raster measurements and thresholds scale with output size;
Kuwahara radius doubles and canvas tooth uses a 2x resample of the same pattern.

The owner's v7 baseline is smoke density gain 0.3 and flame flicker gain 5.
V8 keeps both, the stable 0.15 vorticity and 0.1 flame vorticity, and the reduced
scholar spill. Larger smoke uses 128 base voxels and 2x wavelet noise, a wider
domain and gentle rightward wind. These are implementation choices awaiting the
lead's bake/render, not verified visual results or measured v8 timings.

Editing-agent validation is Python-only. No Blender invocation or commit is
authorized for this pass. The lead retains the machine-wide Blender lock.
