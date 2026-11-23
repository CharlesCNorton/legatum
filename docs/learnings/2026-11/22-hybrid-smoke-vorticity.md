## 2026-11-22: Hybrid smoke collapsed after sufficient pre-roll

- The v5 bake completed in 38.78 seconds but its frame-1 noise plume spanned only
  2.89 units in picture-up Y. Python gzip/NumPy readback reproduced that value:
  UNI base XYZ is 33×72×22, noise XYZ is 66×144×44, and X runs fastest. The ZYX
  reshape and reduction over (0,2) were correct.
- Direct SDNA inspection of the saved pre-bake scene confirmed enabled -Y scene
  gravity, zero domain/emitter rotation and applied unit scales. The domain's
  default -Z fallback was not the active scene gravity. Picture up is +Y here.
- More pre-roll would not address the failure: noise height was already 36.11
  at frame -24. Velocity components grew from 3.26 at -47 to 1,022 at -24 and
  1,527 at frame 0, while heat stayed near 3. The evidence points to excessive
  smoke/flame vorticity (2.5/2.0) reinforcing curl beyond the three-substep budget,
  with open boundaries flushing the plume. Frame-1 base height was still 12.28.
- Reduced vorticity to 0.15/0.1 and noise strength to 0.5; allowed six adaptive
  substeps at CFL 2. Kept buoyancy, inflow, the 48-frame pre-roll, thick domain,
  fixed transforms and height thresholds. Added explicit gravity/axis checks and
  XYZ span diagnostics. The existing cache is retained as evidence until rebake.
- No Blender execution was authorized for this fix. Offline axis/failure checks,
  preparation and syntax are the available validation; corrected plume behavior
  and the eight-minute bake target still require the lead's locked Blender run.
- Mechanism reference: Blender's [smoke integration](https://github.com/blender/blender/blob/main/intern/mantaflow/intern/strings/smoke_script.h)
  adds fuel-dependent flame confinement to smoke confinement and applies density
  and heat buoyancy against effective gravity. The upstream source supports the
  diagnosis but is not a rerun of the installed build.
