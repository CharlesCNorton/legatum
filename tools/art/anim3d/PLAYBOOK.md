# MPFB spearman pipeline

This work is a spearman-only art candidate. The body is MPFB anatomy, with its face, hands, toes, topology and skin weights. No primitive body, painted relief planes or commercial character service is used. The armour and equipment are original code-built surfaces fitted around that body. Review status and measurements are recorded in `REVIEW.md`; a successful bake or small atlas does not establish art approval.

## Isolated installation

Blender 5.3.0 (build `02f0899d78e3`) was already installed. MPFB 2.0.18 is installed from the official GitHub release tag under `~/LegatumRuns/anim-pilot/blender-user/extensions/user_default/mpfb`. Its software licence is GPL-3.0-or-later; the body, morphs, weights and MakeHuman system asset pack are CC0. MPFB's standard `game_engine` rig has 53 bones. Rigify and Rokoko are unnecessary for this implementation.

All downloads go to `~/LegatumRuns/anim-pilot/assets/`; `SOURCES.md`, `materials-manifest.json` and `install-sha256.json` there record URLs, versions, licences and hashes. See also the repository's central art provenance table. Python/Pillow 13.0.0 lives in `~/LegatumRuns/anim-pilot/venv`, not the repository or system Python. Masters, bakes, texture maps and rendered frames live in `~/LegatumRuns/anim-pilot/masters/spearman-3d-v2/`. Nothing uploads them.

```sh
python3 tools/art/anim3d/setup.py
```

The system pack is about 268 MiB and its official server can be slow. Interrupted downloads resume; ZIP validation precedes extraction. `env.sh` sets Blender resource/config/script/data/cache paths. Blender's thumbnail writer nevertheless tries `~/.thumbnails`; the sandbox denies that nonessential write. `nice -n 10` is always invoked; this sandbox denies its priority adjustment. The four-thread cap remains in force. Every heavy entry point takes one shared atomic lock at `~/LegatumRuns/anim-pilot/blender-heavy.lock`; never delete a live lock.

## Build and review

Run these in order from the repository root. Rebuilding the model invalidates downstream material bakes and clip masters; regenerate them.

```sh
tools/art/anim3d/render.sh build
RENDER_ENGINE=CYCLES SAMPLES=12 tools/art/anim3d/render.sh b
tools/art/anim3d/render.sh materials
tools/art/anim3d/render.sh bake
tools/art/anim3d/render.sh paint
tools/art/anim3d/render.sh finish
RENDER_ENGINE=CYCLES SAMPLES=32 tools/art/anim3d/render.sh c
```

`scene.py` creates a muscular male with MakeHuman macro and arm-muscle targets, fits the game-engine skeleton, models a forged muscle cuirass, Corinthian helmet (the build stage runs `helmet.py` for its curved faceplate and real eye/mouth apertures), horsehair crest, convex sunburst aspis, iron-tipped ash spear, greaves, linen pteruges and leather sandals. The base is one stationary cream stone disc. The red cape is a subdivided cloth mesh with shoulder pins, self-collision and character/base colliders.

`materials.py` uses ambientCG Metal034, Fabric030 and Travertine001 plus Poly Haven brown_leather and fine_grained_wood, all CC0. Pigment grading, multiscale hammering and visible edge materials supplement the scans. `bake.py` unwraps code geometry and bakes 512 px ambient occlusion and Cycles Pointiness curvature for cuirass, helmet, shield and skin. These are actual scene bakes, not fabricated maps. AO darkens cavities and curvature drives restrained metal edge wear. Maps are packed into the master and saved separately in `textures/baked/`. `paint.py` adds our original painting's shield brushwork with a calibrated UV map on the convex 3D aspis, blended with the PBR material; it is ordinary texture mapping, not a relief plane. This texture retains some painted lighting, so multi-view reuse needs review. `finish.py` adds crest fibre highlights and adjusts bronze colour. Both stages are repeatable; the `paint-clips` and `finish-clips` stages can update already baked clips after a material-only revision.

`b` emits front, three-quarter and side views beside the painting. `c` emits a three-quarter comparison at native 256 and 64 px. Review files are written immediately to `~/LegatumRuns/anim-pilot/review/3d-v2/`; inspect and critique them before more expensive renders. The first `b` sheet is deliberately retained as first-stage evidence.

## Motion and cloth

CMU 77_02 is standing and 02_01 is walking. The BVHs are Bruce Hahne's 2010 MotionBuilder conversion, retrieved from the una-dinosauria mirror. The accompanying licence permits research and commercial use and adds no restrictions on the conversion. Raw motion stays outside git. The data used in this project was obtained from mocap.cs.cmu.edu; the database was created with funding from NSF EIA-0196217.

`mocap.py` parses BVH channel order and computes forward kinematics, removes travel/yaw, and supplies real captured motion to `animate.py`. Idle uses standing torso deltas; march retargets sagittal leg motion and adds a shield-bearing guard. The weapon arm intentionally does not copy free-walking arm swing. Attack, hit and death are authored keys on the same MPFB rig. This is a reusable retargeting starting point, not a universal full-body motion solver.

```sh
for clip in idle move attack hit death; do
  tools/art/anim3d/render.sh "animate-$clip"
  RENDER_ENGINE=CYCLES SAMPLES=16 tools/art/anim3d/render.sh "e-$clip"
done
RENDER_ENGINE=CYCLES tools/art/anim3d/render.sh d
```

Every clip has a one-second cloth pre-roll, followed by actual cloth simulation baked to its separate `.blend`. The five output lengths are 8/8/10/4/10 at 10/12/14/12/10 fps; idle and move loop. The death's last two output samples use the same settled frame. `d` shows four attack poses. Each `e-*` writes a PNG strip with native 256 px cells and 64 px versions, plus animated WebP. Review animations loop for inspection even when the runtime clip is non-looping.

## Host GPU render

The sandbox has no Metal or Chromium. CPU previews use Cycles at low samples. On the host, the default engine is Eevee, using Blender's macOS GPU backend. Eevee does not use the Cycles `compute_device_type` switch. The host path explicitly passes `--gpu-backend metal`. The script does not silently fall back if Eevee fails.

```sh
tools/art/anim3d/render.sh c
tools/art/anim3d/render.sh d
for clip in idle move attack hit death; do
  tools/art/anim3d/render.sh "e-$clip"
done
```

Use the same `ANIM_ROOT` (default above), resources and saved masters. `RESOLUTION=512 RENDER_ENGINE=CYCLES tools/art/anim3d/render.sh detail` followed by `"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/details.py` produces a chest/helmet/shield comparison. `RESOLUTION=512` can produce a closer inspection render; review and pack scripts downsample to 256. GPU images need fresh visual review because Eevee and Cycles differ. Hunyuan3D mini was skipped because the sandbox cannot use Metal/MPS and a CPU generation does not fit the requested light local workload. TRELLIS was not installed.

## Pack and verify

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/pack.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/validate.py
tools/art/anim3d/render.sh audit
```

Packing preserves all 40 frames, creates a 2560 × 1280 transparent WebP grid, quantizes alpha to 32 levels, and selects quality 85–60 while enforcing **200,000 bytes**. It refuses to overwrite delivery with an oversized atlas. The JSON format is exactly `{frame:{w,h,ax,ay}, clips:{name:{row,frames,fps,loop}}}`, anchor `(127,221)`. `pack.json` binds the atlas to each raw frame by SHA256. `validate.py` checks decoded size, metadata, all clips, alpha, padding, clipping margins, actual motion and held death. `audit.py` checks saved geometry, cloth, source topology and stationary base across all samples.

The review bar is the original painting: equally rich at 256 px, same identity and scale at 64 px, convincing anatomy and equipment, no plastic, blurred or toy-like finish. Compare source and render side by side; inspect chest, helmet and shield close-ups. Check planted feet, grip, spear clipping, cloth intersections, terminal death and the loop seam in motion. No technical check substitutes for the lead's art verdict. Keep the existing painting in the game until that bar is met. No app runtime is changed by this pipeline.

For the next unit, start new external master and review directories; calibrate the painting's camera, proportions and anchor first. Adjust the MPFB macro targets, fit new kit to the same skeletal segments, select and license suitable captured motion, then author the combat keys. Repeat the plain, textured, pose and per-clip reviews before packing. Reuse the download, bake, retarget and validation approach; do not treat a copied spearman mesh, texture or motion as finished art for another unit.

## Vehicles — WWII Tank (`tank`)

This family uses original hard-surface geometry and authored mechanical motion, not an MPFB body. `tank` is the earlier **turreted** tank; `main-battle-tank` is later. `landship` is the separate turretless WWI Early Tank, so it cannot supply the requested turret-traverse clips. The reference has no insignia: do not add stars, numbers or invented markings.

The Vehicles code is isolated under `tools/art/anim3d/vehicles/`. It reuses `env.sh`, the installed Blender and Pillow, the existing CC0 Travertine001 and Metal034 displacement, the review-sheet layout and exact atlas contract. Masters, packed textures, six 512 px AO/curvature maps, five animated `.blend` files and raw frame PNGs are under `$ANIM_ROOT/masters/tank/`. Source/licence records are in `$ANIM_ROOT/assets/SOURCES.md` and the repository art provenance table. No model or master belongs in git.

### Build, bake and mechanical clips

```sh
RENDER_ENGINE=CYCLES tools/art/anim3d/render.sh vehicles-build
RENDER_ENGINE=CYCLES SAMPLES=6 tools/art/anim3d/render.sh vehicles-b
RENDER_ENGINE=CYCLES tools/art/anim3d/render.sh vehicles-bake
RENDER_ENGINE=CYCLES tools/art/anim3d/render.sh vehicles-paint
RENDER_ENGINE=CYCLES SAMPLES=12 tools/art/anim3d/render.sh vehicles-c
RENDER_ENGINE=CYCLES SAMPLES=12 tools/art/anim3d/render.sh vehicles-details
RENDER_ENGINE=CYCLES tools/art/anim3d/render.sh vehicles-animate
RENDER_ENGINE=CYCLES SAMPLES=8 tools/art/anim3d/render.sh vehicles-d
for clip in idle move attack hit death; do
  RENDER_ENGINE=CYCLES SAMPLES=8 tools/art/anim3d/render.sh "vehicles-e-$clip"
done
```

Every Vehicles invocation goes through `$ANIM_ROOT/bin/blender-slot`, in background mode, with three render threads. The machine-wide gate may impose a stricter single-process limit; wait for it. Run only one command at a time. The inherited infantry commands remain backward compatible. Do not call the Blender application directly or pass your own thread count. A rebuild invalidates downstream bakes, projected materials, clip masters and frames; repeat those steps in order, including `vehicles-paint` after the bake. Projection intentionally refuses to apply twice to the same master.

The model has a sloped upper hull, rounded transmission nose, rounded cast turret and mantlet, closed cupola, recessed muzzle, short gun, six road wheels in three VVSS bogies per side, drive sprockets, 124 individually moving track shoes and grousers, louvres, jerricans, stowage boxes, headlights, hatch and towing details. Separate rigid parents control suspension, traverse and recoil. The cream stone base is stationary. Paint has multiscale pigment variation and cast grain; **actual Cycles AO and Pointiness emission bakes** on the upper/lower hull and turret drive cavity grime and noisy edge wear. Small original oxide chips, rubbed lips and dried mud supplement the bakes. Visible surfaces use frozen rest-camera UV projection from the full-resolution painting onto actual hull/turret meshes, blended at 90% confidence on camera-facing surfaces and fading into procedural scanned steel on hidden surfaces. The original bake UV layer is explicitly retained. No flat subject cards or silhouette replacement is used. Small turret motions carry the painted UVs with the mesh; substantial viewpoint changes would expose baked-lighting and alignment errors and need repainting.

Idle has restrained engine shake, a small turret scan and exhaust wisps. Move advances each track link continuously around a closed capsule by three eighths of a shoe pitch per output sample, turns the wheels by corresponding travel/radius, and pitches the hull. Attack traverses the turret, recoils the barrel, flashes and emits smoke. Hit jolts the hull and throws short sparks. Death settles the hull into a planted wreck with noise-masked soot, mesh flames and translucent 3D smoke shells. The last two output frames deliberately repeat the settled sample, including its effects. Exact lengths and fps: idle 8/10, move 8/12, attack 10/14, hit 4/12, death 10/10; only idle/move loop at runtime.

**Never hide volume meshes with zero or tiny scales.** That produced an OpenVDB `ScaleMap` exception and a desktop crash dialog. Inactive effects retain sane scale and use keyed `hide_render`. Smoke is now noise/facing-faded translucent shading on actual 3D shells (the volume version took about 11 seconds per CPU frame just to process); flames and sparks are emissive geometry. Effects need frame-margin and visual review under both render engines. No smoke simulation cache or paid effect asset is required.

### Review and host GPU rerender

Each completed stage immediately writes `review/3d-v2/tank-b-plain.png`, `tank-c-textured-lit.png`, `tank-c-details.png`, `tank-d-rig-poses.png` or `tank-e-<clip>-strip.png`, plus each `tank-e-<clip>.webp`. Sheets include the painting and native 256/64 px comparisons. `tank-log.md` records actual progress; check `tank-FEEDBACK.md` between rounds. The first plain sheet is early evidence, not the final material verdict.

From this worktree on the host, after CPU build/bake/animate:

```sh
tools/art/anim3d/render.sh vehicles-c
tools/art/anim3d/render.sh vehicles-details
tools/art/anim3d/render.sh vehicles-d
for clip in idle move attack hit death; do
  tools/art/anim3d/render.sh "vehicles-e-$clip"
done
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/vehicles/deliver.py
tools/art/anim3d/render.sh vehicles-audit
```

The default render engine is host Eevee with `--gpu-backend metal`; sandbox previews explicitly request Cycles CPU. For a richer final, use `RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=256` before the same render commands; this explicitly selects Metal Cycles and denoising and fails if no Metal device exists. No silent engine fallback. Do not run `vehicles-build` merely to rerender: it overwrites the material master and requires rebaking/reanimating. `deliver.py` refuses thumbnails below 256 px, retains all 40 frames, checks transparent margins/padding and held terminal death, and writes `app/src/assets/units/anim/tank.{webp,json}` with anchor `(127,221)`, under 200,000 bytes. `tank-pack.json` records raw-frame hashes, engine, samples and master hashes. `vehicles-audit` checks articulated geometry, stationary base, track contact, movement, recoil and bake existence. Use `deliver.py --validate-only` to inspect delivery without repacking.

A contract pass does not establish painting parity. Judge the rounded cast shapes, olive surface depth, warm cream base, wheel/bogie readability, source camera and width/height at 256 and 64 px. Watch the move loop for wheel/track aliasing and the combat effects for artificial-looking lobes or frame-edge clipping. GPU re-render and the lead's art review are required before adopting this candidate in the game. No runtime wiring is changed.

#### Warm stone recipe for family reuse

The source tank base samples at native 256 px are RGB `(244,209,172)` on the front top and `(232,188,140)` on the front rim. The cloud review's shared target is warm cream near `#E9CFA0`, with a darker rim. A neutral white shader under warm light was insufficient. Vehicles uses linear-light pigment noise from `(.88,.65,.40)` to `(1.0,.84,.60)`, roughness `.86`, no metal, fine Travertine001 displacement at `.006`, and warm material emission `(.9,.64,.40)` at strength `.20` to keep the contact shade from turning grey. Keep the lighting and AgX transform in mind: these shader numbers are **not** sRGB hex values. Sample the rendered base against the painting after any lighting change; do not assume sharing shader values guarantees matching pixels.

#### Painting alignment and finish standard

Following the coordinator's quality feedback: align the real geometry and camera first, then project the full painting as rest-camera UV colour, retaining procedural material for back faces and newly revealed surfaces. Keep edge bevels, real inset/raised detail and the AO/curvature bakes; projection supplies brushwork, not geometry. In this tank, the main projected meshes are the upper/lower hull, turret, mantlet and transmission cover, with a lighter projection on actual wheel faces, hubs and bogie castings. Hidden sides use the same original olive pigment/scanned cast grain; no extra image generation was necessary for these small-angle motions. Check projection seams and any painted-lighting mismatch before reusing the asset at other angles.

`grade.py` measures each RGB channel's 10th, 50th and 90th percentiles over opaque rest-pose pixels against `tank-256.png`. A bounded monotonic LUT (maximum change 32 levels/channel) is frozen from `vehicles-c` and reused for details, poses and every clip. Alpha is untouched; raw renders are retained under `renders/ungraded/`. Always render `vehicles-c` first after changing lighting or engine, and then rerender every clip before packing. The grade and render reports retain the evidence; do not substitute a histogram match for a silhouette/lighting review. `tank-f-restpose-compare.png` shows painting, 3D render and 50/50 crossfade at 256 and 64 px.

The final projection pass uses a 45% emission/55% BSDF mix on confidently projected surfaces to avoid lighting the painting's highlights twice; back faces remain fully physical. Wheel/bogie projection uses a gentler 55% colour blend. These are deliberate fixed-view art choices, not physically neutral PBR materials.

For the complete host rerender, repack and audit in one serial command (saved masters only):

```sh
RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=256 tools/art/anim3d/render.sh vehicles-final
```

`vehicles-final` also works with the default Eevee backend or explicit Cycles CPU previews. It renders the rest pose first to establish one grade, then details, rig poses and all five clips, packs/validates, and audits the saved 3D geometry. It never rebuilds the tank or replaces the saved material work.

#### Blender skill review

The newly installed `blender-modeling`, `blender-materials`, `blender-lighting`, `blender-cameras`, `blender-animation` and `blender-rendering` skills were read at the end of this candidate round. They informed a final review of bevels/rounded joins, paint versus exposed steel, key/fill contrast, reference framing, mechanical motion and sequence verification. Concrete additions: every Vehicles invocation now passes `--disable-autoexec` before loading masters, and rendering explicitly rejects an unassigned camera. Existing project object names, orthographic token framing, requested painted lighting and alpha atlas output take priority over generic GEO-prefix, cinematic depth-of-field and glTF presets. The optional `reference-look-calibration` skill is not installed; the source bounding boxes, RGB quantiles, native-size sheets and crossfade provide direct comparison.

The review identified follow-ups rather than establishing art parity: separate dielectric olive paint from truly exposed-metal wear masks instead of treating the present blended metallic values as physical materials; refine cast joins and wheel recess geometry; match gun/camera registration more closely; check subframe linear interpolation for mechanical travel if the masters are reused beyond these integer-frame atlas samples. No material preset was retroactively claimed as tested. Preserve the current candidate when exploring those changes, then regenerate its bake/projection/render/pack chain and compare actual images.
