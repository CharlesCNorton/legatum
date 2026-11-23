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

This family uses original closed hard-surface geometry and authored mechanical motion, not an MPFB body. `tank` is the turreted WWII tank; `main-battle-tank` is later and `landship` is the turretless Early Tank. Match this painting and do not add insignia.

Code is isolated under `tools/art/anim3d/vehicles/`, with the driver entry point at `units/tank/gpu.sh`. It reuses `env.sh`, Blender 5.3.0, the installed Pillow and CC0 Metal034/Travertine001 scans. All Blender invocations are plain `blender -b --disable-autoexec` through the PATH gate, with three render threads and one heavy lane process. Never bypass the gate or call the application directly. Masters, packed textures and renders live outside git at `$ANIM_ROOT/masters/tank/`. The original painting and reused image-generated olive fill are SHA256-pinned in `units/tank/assets.lock.json`; their licences/generation are in `$ANIM_ROOT/assets/SOURCES.md` and the project provenance table.

### Build and registration

Run from the repo root, in order; rebuilding invalidates every downstream bake, material, clip and render:

```sh
tools/art/anim3d/render.sh vehicles-build
tools/art/anim3d/render.sh vehicles-refine
RENDER_ENGINE=CYCLES SAMPLES=8 tools/art/anim3d/render.sh vehicles-b
tools/art/anim3d/render.sh vehicles-bake
tools/art/anim3d/render.sh vehicles-paint
RENDER_ENGINE=CYCLES SAMPLES=16 tools/art/anim3d/render.sh vehicles-c
tools/art/anim3d/render.sh vehicles-animate
RENDER_ENGINE=CYCLES SAMPLES=16 tools/art/anim3d/render.sh vehicles-final
```

`scene.py` creates a sloped hull, rounded transmission nose and cast turret/mantlet, recessed short gun, six road wheels in three VVSS bogies per side, sprockets, 124 separate track shoes, hatches, tools, headlights, hull MG, jerricans, folded solid canvas, thick straps and buckles. The cream disc is stationary. `tank-built.blend` preserves the original construction. `refine.py` starts from that untouched file every time and registers full-depth meshes in the fixed camera's horizontal/vertical axes, preserving camera depth and mechanical parents. Its measured part bounds are saved in `registration.json`. This is mesh editing, not image warping, silhouette clipping or a subject card. Three-view plain renders make the retained volume reviewable.

Round-2 calibration widened/lowered the cast silhouette, reduced/moved the cupola, raised the gun 10 native pixels, lowered the jerricans and moved the rear box onto an extended armour shoulder. Road-wheel centres/radii and bogie supports are also registered; invented radial spoke rods and black plug details were removed. Registration is approximate, not proof of exact painting parity; inspect the native 256/64 comparison and crossfade after every change.

### Paint, light and grade

`bake.py` produces six actual 512px Cycles maps: AO and Geometry Pointiness emission for the upper hull, lower hull and turret. Those drive cavity grime and edge wear. `prepare-paint.py` fits the original full-size alpha master to the same token field. `paint.py` freezes rest-camera UVs on the actual meshes, preserving explicit bake UVs. Moving track shoes, grousers, pins and sprocket teeth retain physical steel so they cannot carry projected wheel/bogie fragments around the belt. End-sprocket centres now fit measured source landmarks; their UVs use the same frozen camera projection as the hull. Facing/alpha confidence blends 98% projected colour on visible surfaces into the generated olive fill, scanned grain, canvas, rubber and stone materials on hidden surfaces. No hidden-view source painting exists; those fills are an approximation. Small-angle motion is intentional. Large viewpoint changes need repainting and a new review.

The projection shader mixes 96% camera-only painted pigment at full confidence with physical BSDF response. Non-camera rays see the physical shader, preventing painted illumination from lighting nearby parts. Standard/None preserves the source display colour; this is specific to a painting with existing lighting, not a photographic preset. Product light energy is 55% of the previous AgX setup. Olive paint is dielectric. Bevels, material grain and the physical component retain three-dimensional relief. Warm upper-left key, soft fill and cool area rim are the product-shot setup. The painting's warm base samples at native 256px are approximately RGB `(244,209,172)` on the front top and `(232,188,140)` on the rim. Procedural fallback uses linear pigment `(.88,.65,.40)` to `(1,.84,.60)`, roughness `.86`, Travertine displacement `.006` and warm emission strength `.20`; these shader values are not sRGB colours. Sample actual pixels after lighting changes.

`grade.py` measures opaque rest-pose RGB 10th/50th/90th percentiles against the painting, creates a bounded monotonic LUT (maximum 32 levels/channel), and applies that one frozen grade to details, poses and every clip. Alpha is untouched. Original ungraded renders remain in `renders/ungraded/`; reports bind frames to the grade and saved scene hashes. Render `vehicles-c` before all other painted stages whenever lighting or engine changes. A histogram match never establishes silhouette or craft parity.

All six Blender skills informed the work: modeling for rounded joins and solid folded stowage; materials for dielectric paint, generated fill and worn surfaces; cameras for measured registration; lighting for key/fill/rim; animation for layered-action linear mechanical curves; rendering for safe CPU previews and explicit Metal Cycles finals. The optional reference-look-calibration skill is absent; native-size images, landmark bounds and quantile measurements supply the comparison.

### Five mechanical clips

Idle uses restrained engine shake, turret scan and exhaust. Move cycles separate links around a closed circle-envelope route and turns wheels by matching travel/radius. Attack traverses and recoils the gun, with mesh flash and smoke at the registered muzzle. Hit jolts the hull with short sparks. Death settles into a planted wreck, with masked soot confined to the vehicle and a subdued smoke plume; the stone base keeps its material. Output lengths/fps are idle 8/10, move 8/12, attack 10/14, hit 4/12, death 10/10. Only idle/move loop in the runtime metadata. The last two death output samples are identical.

Never hide effects by setting scale to zero or nearly zero. Key `hide_render` and keep real mesh thickness. The earlier volume approach caused OpenVDB ScaleMap crashes and cost roughly 11 CPU seconds per frame; noise/facing-faded translucent 3D shells avoid that conversion. The former solid orange death spikes were removed after review. Flash, sparks and smoke still need visual review; a successful audit does not make them painterly. Linear interpolation is applied through Blender 5 layered actions, stepped interpolation to visibility.

### Complete host GPU handoff

The executable, no-argument driver entry point is:

```sh
ROUND=4 tools/art/anim3d/units/tank/gpu.sh
```

It renders every review stage and all 40 clip frames serially in Metal Cycles at 512px, 256 samples with denoising (override `SAMPLES` explicitly if needed). It uses the saved built/baked/projected/animated masters and never rebuilds them. It creates the actual 512px and downsampled 256px master sets, packs and validates the 160px trimmed atlas, audits saved geometry, and makes the eight-second H.264/yuv420p `tank-round${ROUND}.mp4`. All five clips appear side by side at 2x on cream; one-shot clips replay every two seconds with a terminal hold. FFprobe verifies 240 frames, eight seconds and 1600x348 dimensions; representative video frames are decoded for inspection. Missing Metal devices fail explicitly; sandbox CPU previews do not establish GPU success.

Every stage immediately writes `tank-b-plain.png`, `tank-c-textured-lit.png`, `tank-c-details.png`, `tank-d-rig-poses.png` or `tank-e-<clip>-strip.png` and animated WebP into `review/3d-v2/`. `tank-f-restpose-compare.png` is painting/render/50-50 crossfade at 256/64px. `tank-g-delivery.png` also shows the decoded 160px atlas enlarged for comparison. Check feedback during work and log actual observations. `tank-PASS` is manual evidence of painting parity, clean clips and contract success; scripts never write it automatically.

### Trimmed atlas contract (version 2)

The old 2560x1280, quality-54 tank candidate is superseded. Delivery preserves all 40 frames, resizes to logical 160x160 cells, removes alpha below 3/255, trims transparent margins, and packs each clip into its own horizontal strip with transparent gutters. Identical held frames reuse one rectangle, preserving decoded RGB as well as alpha. WebP uses full-quality alpha and the highest tested quality in 95/90/85/80/75 that fits **200,000 bytes**. Failure at 75 stops without lowering quality. Masters are retained; delivery never upscales previews to masquerade as 512px originals.

```json
{
  "version": 2,
  "trimmed": true,
  "frame": {"w": 160, "h": 160, "ax": 79.375, "ay": 138.125},
  "clips": {
    "idle": {
      "row": 0, "frames": 8, "fps": 10, "loop": true,
      "rects": [{"x": 2, "y": 2, "w": 145, "h": 101, "ox": 8, "oy": 29}]
    }
  }
}
```

The example shows one illustrative rectangle; actual JSON has one rectangle per frame and all five clips in idle/move/attack/hit/death row order. `x/y/w/h` are atlas source pixels. `ox/oy` place that crop into its logical 160px frame. To draw at logical anchor `(X,Y)`, draw the cropped image at `(X - ax + ox, Y - ay + oy)`, applying the same display scale to all coordinates. `row` is clip ordering metadata; it is **not** a constant-height grid coordinate. This is an extended candidate format with no app runtime wiring in this lane.

`deliver.py --validate-only` checks current clip-scene/source hashes, grade consistency, quality/bytes, all clip counts and offsets, nonoverlapping rectangles, transparent padding, motion and held death. `vehicles-audit` checks actual meshes and parents, 124 links, 16 wheel pivots, recoil, planted samples, stationary base and six bake files. `archive.py --require-512` rejects non-GPU or sub-512 source reports. Contract and geometry checks do not replace art review.

Keep the painting in the game until the lead approves the GPU output. At the resumed round-2 checkpoint the rest image is substantially closer, but rear/fender outlines, end-sprocket placement, cast surface shading and motion remain review items; do not infer PASS from a small atlas.

### Round 3 chassis and GPU receipts

`runninggear.py` constructs each belt as the convex envelope of the end-sprocket
and lower contact circles, then samples it by arc length. `refine.py` registers
both end sprockets separately on each side before freezing paint, retains their
circular geometry and real thickness, and seats the full-depth fenders above the
new route. The transmission casting is extended to meet the nose; the rear armour
shoulder is broader and the stowage box lower. These local mechanical fittings
are an approximation to the painting, not a calibrated physical camera solution.
Copying the near-side fit blindly to the far side exposed the upper belt beyond
the hull; inspect both ends and contact before keeping a new fit. The low road-wheel
run remains planted. Three numerical tests check route length, closure, constant
speed and shoe tangent orientation. Moving track steel uses camera-only dusty
pigment over its physical surface instead of carrying source bogie fragments.

The executable `units/tank/gpu.sh` defaults to ROUND=3 and retains a direct log at
`ANIM_ROOT/gpu-logs-tank-r${ROUND}.log`, recording the actual checkout revision and
modified inputs. Its input and Metal preflights precede rendering; errors write
the failing stage to `review/3d-v2/tank-gpu-status.txt`. Completion records technical
success with visual review still pending. The master exporter now checks scene
and grade hashes; the atlas validator checks exact reconstructed alpha and an
identical decoded death hold. The scaled anchor preserves fractional pixels.

### Round 3 after the lead GPU receipt

The lane is `astra/unit-anim-3d-vehicles` in `.worktrees/tank-round3`; run its
GPU script from that checkout. The lead's `gpu-logs-tank-r2.log` and saved reports
confirm Cycles GPU512 at 256 samples completed: 190,044 bytes at Q80 and an
8-second H.264/yuv420p video. Earlier missing-GPU notes were historical. That
receipt, the old rendered frames/clip masters and actual 512px exports are
preserved under `masters/tank/round2-gpu-receipt/`.

The round base's lower rim gives a better camera constraint than the hull alone:
its approximately 227 x 42px projected ellipse implies a lower elevation. The
saved camera is now `(5.6,-10,3.32)` looking at `(0,0,1.14)`, orthographic scale
4.95. The base remains a real round horizontal cylinder. Armour vertices are
registered in the camera plane, retaining depth; wheel pivots and track routes
are fitted separately while preserving physical ground contact. The first
camera trial exposed misplaced fixtures: keep real lamp housings at the source
landmarks, rather than accepting painted duplicate fixtures on the glacis.
Rear stowage is wider/lower, shoes are 15% narrower, the muzzle is slimmer and
invented black sprocket plugs are removed. These are local painting fits, not
proof of a unique physically recovered camera or a reusable multi-view model.

`render.py` now retains the saved camera instead of resetting the construction
camera after UV projection. The detail view is a parallel dolly and its reference
crop has the same framing/magnification. Delivery checks exact clip/rest camera
metadata, in addition to current scene and grade hashes. Flash/smoke origins are
measured from the actual registered muzzle rather than a fixed pixel offset.

`vehicles-g` renders all eight move samples from top and front with a neutral
material override and produces `tank-g-feet-check.png`. The vehicle has no human
or animal gait; this is its mechanical equivalent of the common feet review.
Use the physical track-speed/contact audit alongside the sheet. GPU handoff
includes these renders and archives them at 512/256. Unit-local provenance now
lives in `units/tank/SOURCES.md` as well as the external source registry.

Current CPU256/12-sample delivery: **180,602 bytes at Q80**, 40 frames, trimmed
160px logical cells. All three belt tests, geometry/contact audit, atlas alpha /
anchor / clip / camera / terminal-hold checks and the 240-frame, 8-second video
probe pass. At256 alpha IoU changes from .927584 (previous GPU) to .949746 (new
CPU); opaque RGB MAE changes from 6.595 to 7.489. These are different render
settings and are descriptive, not an art threshold. At64 the identity survives,
but the running gear and far fender remain distinguishable. Painted illumination
still rotates with wheel texture; CPU smoke is grainy. **No tank-PASS marker.**
The fresh GPU512 pass and visual review are still required for these changed
masters. Run `ROUND=3 tools/art/anim3d/units/tank/gpu.sh`.


### Round 4 after the lead GPU receipt

The round-3 GPU pass succeeded: 40 frames, **197,260 bytes at Q80**, actual
512/256 masters and a verified eight-second H.264/yuv420p video. Its immutable
review copy is under `masters/tank/round3-gpu-receipt/`. Current host entry point
now defaults to ROUND=4; run `ROUND=4 tools/art/anim3d/units/tank/gpu.sh` from this
checkout. No GPU failure needed repair in this round.

Converted fender curves have zero-valued object origins. Side selection now uses
the actual mesh centroid in suspension space, so the near rolled edge follows
the near suspension. The far rolled edge is seated below the lamp, forward
mudguard tips taper, shoes narrow from .85 to .78 of construction width, and
the rear shoulder is raised and shortened. All edits retain closed geometry;
the six AO/curvature maps and rest-camera UVs are regenerated afterwards.

`prepare-paint.py` derives a 16px-radius low-pass field from the 1024px painting.
Wheel materials divide rotating pigment by its rotating broad-light estimate
and multiply by a nonspinning broad-light field, clamping the ratio to .6–1.65.
The illumination frame follows hull suspension, not the axles. At rest its
coordinates agree with the saved camera projection. This is approximate
frequency separation, not a claim of recovered albedo: small painted aperture
shadows can still rotate. The existing generated olive hidden fill, hard-edge
bevels, thick straps, folded canvas, product lights and frozen histogram grade
remain. `audit.py` checks rest-coordinate agreement and all-frame nonspinning
lighting in addition to the mechanical/contact checks. Matrix comparison uses
1e-5 tolerance: Blender evaluation showed harmless 4.8e-7 matrix roundoff.

Current CPU256/12-sample delivery: **181,292 bytes at Q80**, 40 frames, 1381x556
trimmed atlas, 160px logical cells. All three route tests, geometry/contact and
wheel-light audit, exact alpha/offset/camera/grade/held-death checks pass. All
review sheets and actual 256px masters are refreshed; `tank-round4-cpu.mp4` is
H.264/yuv420p, 1600x348, 240 frames/eight seconds, with decoded frames inspected.
Previous 512px masters remain with the GPU receipt; fresh round-4 GPU512 output
is still required. At256 the fender/shoulder outline is closer, but the tread
finish, wheel detail and simplified effects remain distinguishable. At64 the
identity is correct but the heavier front running gear still differs. **No PASS.**
