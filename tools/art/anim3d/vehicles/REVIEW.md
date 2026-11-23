# Tank candidate — round 3 after GPU review

**Not visually passed.** The painting remains the production asset; this lane has no runtime wiring or `tank-PASS` marker. The lead's round-2 receipt confirms Cycles GPU512/256 samples, all 40 frames, a Q80/190,044-byte atlas and an eight-second video. Those renders and masters are preserved under `masters/tank/round2-gpu-receipt/`.

This revision calibrates the camera from the round stone's lower-rim ellipse, keeps the saved camera through rendering, re-fits rear armour/stowage and real headlamps, narrows the shoes and muzzle, and removes invented black sprocket plugs. Existing generated hidden-surface fill, bevels, thick straps/folded canvas, product lighting, six fresh AO/curvature bakes, frozen camera projection and automatic histogram grading remain. Effects now follow the measured muzzle. Detail comparison uses matching framing. The GPU script also produces top/front geometry views of the complete eight-frame move cycle; this is the mechanical equivalent of the feet check.

At **256px**, the base and rear outline are closer, with rich painted surfaces; the far fender, circular wheel finish and some fixture contours still differ. At **64px**, it reads as the same WWII tank, but is not indistinguishable. The five strips and decoded video frames were inspected: no frame-edge clipping, clean recoil/hit/held wreck, but painted wheel lighting travels during rotation and low-sample smoke is grainy. Top/front views show parallel running gear; physical contact and travel/radius checks pass. Off-angle views expose the locally fitted geometry, so this is not a general-purpose vehicle model.

Descriptive source comparisons: native 256px alpha IoU **.927584 → .949746**, opaque-overlap RGB MAE **6.595 → 7.489**. At native 64px, IoU **.896830 → .912717**, RGB MAE **15.993 → 16.127**. The prior frame is GPU512/256 samples and the new frame CPU256/12 samples; these are not like-for-like quality results or approval thresholds. Exact evidence is in `review/3d-v2/tank-round3-metrics.json`.

Current CPU delivery passes: **180,602 bytes at Q80**, all 40 frames, 160px trimmed cells. Validation checks source/scene/grade hashes, rest/clip camera agreement, counts/timing, bounds, offsets, nonoverlap, exact reconstructed alpha and identical decoded terminal death. Geometry audit passes 124 links, 16 wheel pivots, travel/radius, recoil, contact, six bakes and stationary base. Three numerical belt tests pass; 16 Python files parse; three shell entry points pass syntax checks. No Rust/UI code changed.

Current 256px masters, all interim sheets/WebPs, `tank-g-feet-check.png`, and `tank-round3-cpu.mp4` exist outside git. The video probe confirms H.264/yuv420p, 1600x348, 240 frames/eight seconds. Previous 512px masters are explicitly filed with the old GPU receipt; fresh 512px masters for this revision remain pending the lead's GPU pass.

From this checkout run:

```sh
ROUND=3 tools/art/anim3d/units/tank/gpu.sh
```

The executable no-argument script renders every stage and clip serially with Metal Cycles at 512px/256 samples, archives actual 512/256 masters, packs and validates the atlas, audits geometry, makes the crossfade and top/front review, and probes/decodes `tank-round3.mp4`. It leaves visual approval to the reviewer and never writes PASS automatically.

Non-obvious findings: a renderer that restores a construction camera silently breaks frozen projection when camera calibration changes. Match the detail comparison's source crop to the rendered camera too. A lower base ellipse can improve the rest silhouette while exposing fixture occlusion and lighting errors; inspect actual meshes and animation after each fit. Projecting wheel/bogie fragments onto moving shoes tears during motion, so travelling shoes retain their own pigment. Small atlas size and a successful GPU job do not establish art parity.
