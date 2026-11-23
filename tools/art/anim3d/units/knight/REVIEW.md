# Knight round 1 — candidate, not PASS

Built the MPFB rider and Quaternius horse with knight-specific greathelm, mail,
shield, lance, caparison and mantle. Frozen camera UVs carry the painting on real
3D geometry; unseen sides retain physical materials and licensed/generated fills.
All five clips and required review stages exist. The feet sheet isolates actual
skinned lower legs so cloth cannot hide their orientation in the top view.

## Evidence and exact checks

- CPU Cycles previews: all nine stages at 512 px, 8 samples, denoised; separately
  retained 256 px derivatives. Metal/GPU execution has not been tested here.
- Source preflight: all 8 pinned external source hashes passed.
- Scene audit: five licensed horse actions, clip lengths, stationary stone and
  nonzero scales passed. Recorded foot targets/floors are in external `audit.json`.
- Atlas: **197,194 bytes**, **quality 85**, **40 frames**, trimmed 160 px canvases.
  Counts/timing, hashes, alpha reconstruction (max 5/255 quantization error),
  rectangle bounds/non-overlap, margins, motion and exact held death passed.
  The last two death entries share one rectangle to avoid WebP block variation.
- Movie: **240 frames, 8 seconds, 1600x348, H.264, yuv420p** verified by ffprobe.
- All 16 Python scripts parse; both shell entry points pass `bash -n`;
  `git diff --check` passes.
- Repository gate on the existing HEAD: hygiene/public-claims passed; art failed
  while `render-sets.mjs` exited 1. It did not validate these uncommitted changes.
  The wrapper returned no more specific cause. No Rust or runtime/UI logic changed.
- Git staging failed with `index.lock: Operation not permitted`; the runner must
  commit the working tree. No push or PR was attempted.

## Visual verdict

At 64 px the palette, lance and lion heraldry identify the knight. The lower
silhouette is still too ragged and broad. At 256 px it is plainly distinguishable
from the painting: caparison folds are slab-like, the rear mantle is incomplete,
helmet shape is too cylindrical, the cream base lacks the painted rim's depth,
and projection masks show on off-camera surfaces. The pale tail is improved,
but still simpler than the painting.

The isolated feet check exposes several hoof positions beyond the small stone
footprint; contact/stride still needs correction. Source foot axes were retained,
but this is **not** a no-slide sign-off. Cloth is bone-driven and not a collision
simulation. Live AO/grain are present; fresh AO/curvature bakes remain outstanding.
No PASS marker was written. Next round should solve full-depth horse/hoof/base
registration and cloth shape before adding further texture detail.

## Lead command

```sh
ROUND=1 tools/art/anim3d/units/knight/gpu.sh
```

From the repository root, without arguments. It checks Metal and source hashes,
rebuilds all scenes, renders every review stage with Cycles GPU at 512 px/64+
samples, creates 512/256 masters, packs/validates the atlas, writes all review
images (including the rest split/crossfade and feet), and writes the round MP4.
It fails instead of silently falling back to CPU and never writes PASS.
