# Tank candidate — round 4 after GPU review

**Not visually passed.** The painting remains the production asset; no runtime wiring or `tank-PASS` marker. The lead's round-3 GPU pass succeeded: Cycles GPU512/256 samples, all 40 frames, Q80/197,260-byte atlas, eight-second video. Its renders, clips, actual 512/256 masters and review evidence are preserved under `masters/tank/round3-gpu-receipt/`.

This revision fixes fender-side classification for converted curves, seats the far rolled edge, tapers mudguard tips, narrows track shoes and raises/shortens the rear armour shoulder. Wheel shaders separate a bounded broad-light estimate from rotating pigment; the illumination frame follows suspension but never wheel spin. This preserves rest projection and reduces broad painted-shadow rotation. Fine painted aperture shadows still rotate: it is an approximate decomposition, not recovered physical albedo. Existing generated olive fill, bevels, solid straps/folded canvas, product lighting, six regenerated AO/curvature bakes and automatic frozen histogram grade remain.

At **256px**, the outline is closer and the stray bar behind the far headlamp is gone. Track finish and circular wheel detail are still too regular, and effects remain simplified. At **64px**, it reads as the same WWII tank, but heavier front running gear remains distinguishable. All five strips and decoded video frames were inspected: no frame-edge clipping, restrained recoil/hit, identical held wreck; low-sample smoke remains grainy. The eight-frame top/front geometry review shows parallel running gear, with contact and wheel/track speed confirmed by audit. This fixed-view fitted model is not a general-purpose multi-view vehicle.

Descriptive source comparisons: 256px alpha IoU **.949667 → .952378**, opaque-overlap RGB MAE **6.594 → 7.598**; 64px IoU **.911663 → .913194**, MAE **16.104 → 15.880**. These compare GPU512/256-sample round3 against CPU256/12-sample round4, not a controlled quality comparison or approval threshold. Exact image hashes are in `review/3d-v2/tank-round4-metrics.json`.

CPU delivery passes: **181,292 bytes at Q80**, 40 frames, 160px trimmed logical cells, 1381x556 atlas. Validation checks source/scene/grade hashes, rest/clip camera agreement, counts/timing, offsets, nonoverlap, exact reconstructed alpha and identical decoded death hold. Geometry audit passes 124 links, 16 wheel pivots, travel/radius, recoil, contact, stationary base, six bakes, rest wheel-light coordinate agreement and nonspinning light coordinates across every sample. Three route tests pass; 16 Python files parse; three shell entry points pass syntax checks. No Rust/UI code changed.

Current actual 256px masters, all interim PNG/WebP reviews, top/front geometry views and `tank-round4-cpu.mp4` exist outside git. FFprobe confirms H.264/yuv420p, 1600x348, 240 frames/eight seconds. Current-round 512px masters await GPU rendering; previous actual 512px output is preserved with the prior receipt.

From this checkout run:

```sh
ROUND=4 tools/art/anim3d/units/tank/gpu.sh
```

This executable no-argument script renders every stage and clip serially using Metal Cycles at 512px/256 samples, archives actual 512/256 masters, packs and validates the atlas, audits geometry, creates the crossfade/top-front reviews, and probes/decodes `tank-round4.mp4`. It never writes PASS automatically. GPU rendering was not attempted from the Metal-less sandbox this round.

Non-obvious findings: converted-curve object origins cannot identify a vehicle side; use mesh positions. Broad painted lighting needs a nonspinning coordinate field independent of wheel pigment. Blender evaluates an unchanged child-local matrix with sub-micro-unit roundoff under suspension movement, so verify with a small numerical tolerance rather than exact matrix equality.
