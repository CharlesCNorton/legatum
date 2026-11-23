# Tank candidate — resumed round 2

The painting remains the production asset. This is a true-3D animation candidate with no runtime wiring and **no tank-PASS marker**. The image is substantially closer, but it is still distinguishable from the painting at 256px.

The resumed WIP now has tested full-depth geometry registration, source-camera painting projection, the recorded image-generated olive hidden-surface fill, six actual AO/curvature bakes, bevelled cast parts, solid folded canvas and straps, product lighting and one automatic histogram grade for every frame. The gun was raised 10 native pixels, the cast turret widened/lowered, the cupola reduced/moved, jerricans shortened, and rear stowage supported by the extended hull shoulder. Rotating road wheels/bogies were registered to painted centres. Track shoes retain physical steel rather than carrying whole projected bogie fragments around the belt. Source sprocket textures are centred on their real axles. Death is now a soot-darkened smoking wreck; orange polygon spikes were removed and the stone is excluded from soot.

At **256px**, gun/turret registration, hull brushwork and cream stone are much improved. Remaining differences include end-sprocket placement/track profile, the rear shoulder and fender silhouette, somewhat uniform wheel finish, and painted lighting that travels with rotating wheels. Smoke needs higher-sample GPU review. At **64px**, it clearly reads as the same WWII tank, but the running gear is still more regular and the rear silhouette differs. The five strips were inspected; no frame-edge clipping was seen. This is not a claim that all five clips meet the final craft bar.

Descriptive measurements versus the retained round-1 rest render: 256px alpha-mask IoU increased from 0.8635 to 0.9263; mean absolute RGB error over opaque overlapping pixels fell from 33.034 to 12.336. At 64px those measurements are 0.9304 and 10.627. These are not approval thresholds. Evidence is in `masters/tank/comparison-metrics.json` and the native-size `tank-f-restpose-compare.png`.

The final **CPU preview** contract passes: **198,480 bytes, WebP quality 81, 40 frames, logical 160px cells, trimmed 1503x564 atlas**. JSON version 2 carries per-frame atlas rectangles and logical offsets; the exact drawing rule is in the Vehicles chapter of `PLAYBOOK.md`. Validation checks source/master/grade hashes, all counts, bounds, offsets, nonoverlap, transparent padding, motion and identical final death samples. Saved-scene audit passes for 124 moving links, 16 wheel pivots, recoil, planted samples, stationary base and six bakes. Thirteen Python scripts parse; the three shell entry points pass `bash -n`; `git diff --check` passes. No Rust or application logic changed.

All five clip masters, 256px CPU renders and review strips/WebPs are retained outside git under `~/LegatumRuns/anim-pilot/masters/tank/` and `review/3d-v2/`. The eight-second CPU video is `tank-round2-cpu.mp4`; the GPU script writes the driver's exact `tank-round${ROUND}.mp4` name. A real 512px GPU frame set remains **pending**; none was fabricated by upscaling these previews.

The executable no-argument host handoff, from the repository root, is:

```sh
ROUND=2 tools/art/anim3d/units/tank/gpu.sh
```

It uses the saved current masters, explicitly selects Metal Cycles/512px/256 samples with denoising, renders every stage and all clips, retains actual 512 and downsampled 256 masters, packs/validates, audits geometry and creates/probes/decodes the five-up H.264/yuv420p video. Metal is unavailable in this sandbox, so host execution and visual approval are outstanding. Do not rebuild just to rerender.

For a clean rebuild, run `vehicles-build`, `vehicles-refine`, `vehicles-b`, `vehicles-bake`, `vehicles-paint`, `vehicles-c`, and `vehicles-animate` in that order before the final rendering pass. `tank-built.blend` preserves construction geometry and makes refinement repeatable. Original round-1 masters remain in `round1-backup`.

Non-obvious findings: projecting whole rest-camera wheel/bogie fragments onto moving track links looks convincing at rest and tears during travel. Register individual wheel centres and keep travelling shoes on their own material. A source-landmark-fitted track route can also break real fender clearance and base contact; the rejected experiment failed the hit contact audit and was removed. Keep the planted belt until the entire chassis/fender/axle system can be calibrated together. Never hide smoke by zero scaling; use visibility keys and real thickness. Avoid editing a shell wrapper while a process is running it.
