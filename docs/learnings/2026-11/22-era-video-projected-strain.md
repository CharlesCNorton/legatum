## 2026-11-22: Living-painting motion must be measured independently of its camera

- The rendered Classical v1 had about 3–4 levels of consecutive RGB difference, but
  camera-compensated samples left water/sky/cloth differences below one level. That
  residual includes resampling; overall frame difference does not establish visible life.
- Only 0.39% of relief vertices were faded, yet projected depth geometry predicted
  large local compression and stretch at the foreground columns and olive leaves.
  Triangle edge-length expansion alone misses compression/shear. Check both singular
  values of the projected triangle transform after removing ordinary zoom.
- V2 halves the push/relief, smooths depth geometry without blurring the painting,
  and validates sampled evaluated cloth geometry and all held frames in a Blender
  dry-run. Camera-only stretch is within about 3.7%, with zero faded vertices.
  Rendered approval is still pending; numerical checks do not replace visual review.
- Evidence and ranked critique: `tools/art/era-video/review/v1-critique.md`.
