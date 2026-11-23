# MPFB spearman pipeline

This work is a spearman-only art candidate. The body is MPFB anatomy, with its face, hands, toes, topology and skin weights. No primitive body, painted relief planes or commercial character service is used. The armour and equipment are original code-built surfaces fitted around that body. Review status and measurements are recorded in `REVIEW.md`; a successful bake or small atlas does not establish art approval.

## Isolated installation

Blender 5.3.0 (build `02f0899d78e3`) was already installed. MPFB 2.0.18 is installed from the official GitHub release tag under `~/LegatumRuns/anim-pilot/blender-user/extensions/user_default/mpfb`. Its software licence is GPL-3.0-or-later; the body, morphs, weights and MakeHuman system asset pack are CC0. MPFB's standard `game_engine` rig has 53 bones. Rigify and Rokoko are unnecessary for this implementation.

All downloads go to `~/LegatumRuns/anim-pilot/assets/`; `SOURCES.md`, `materials-manifest.json` and `install-sha256.json` there record URLs, versions, licences and hashes. See also the repository's central art provenance table. Python/Pillow 13.0.0 lives in `~/LegatumRuns/anim-pilot/venv`, not the repository or system Python. Masters, bakes, texture maps and rendered frames live in `~/LegatumRuns/anim-pilot/masters/spearman-3d-v2/`. Nothing uploads them.

```sh
python3 tools/art/anim3d/setup.py
```

The system pack is about 268 MiB and its official server can be slow. Interrupted downloads resume; ZIP validation precedes extraction. `env.sh` sets Blender resource/config/script/data/cache paths. Blender's thumbnail writer nevertheless tries `~/.thumbnails`; the sandbox denies that nonessential write. `nice -n 10` is always invoked; this sandbox denies its priority adjustment. The four-thread cap remains in force. Temporary files also use `ANIM_ROOT/tmp`. The runner may additionally queue Blender through its machine-wide `blender-slot` shim; do not bypass it. Every heavy entry point takes one shared atomic lock at `~/LegatumRuns/anim-pilot/blender-heavy.lock`; never delete a live lock.

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

`materials.py` uses ambientCG Metal034, Fabric030 and Travertine001 plus Poly Haven brown_leather and fine_grained_wood, all CC0. Pigment grading, multiscale hammering and visible edge materials supplement the scans. `bake.py` unwraps code geometry and bakes 512 px ambient occlusion and Cycles Pointiness curvature for cuirass, helmet, shield and skin. These are actual scene bakes, not fabricated maps. AO darkens cavities with a power curve; curvature drives bright metal edge wear and lower roughness. Solidify is disabled only while baking: its generated inner faces share UVs with the outer surface and otherwise overwrite the visible AO with darkness. The restored master retains its physical thickness. Maps are packed into the master and saved separately in `textures/baked/`. `paint.py` adds our original painting's shield brushwork with a calibrated UV map on the convex 3D aspis, blended with the PBR material; it is ordinary texture mapping, not a relief plane. This texture retains some painted lighting, so multi-view reuse needs review. `finish.py` adds crest fibre highlights, a riveted leather waist belt and variation in bronze roughness. These stages are repeatable. The `paint-clips` and `finish-clips` helpers remain useful for diagnosis; regenerate all clips from the final master before delivery so the source hash remains valid.

`b` emits front, three-quarter and side views beside the painting. `c` emits a three-quarter comparison at native 256 and 64 px. Review files are written immediately to `~/LegatumRuns/anim-pilot/review/3d-v2/`; inspect and critique them before more expensive renders. The first `b` sheet is deliberately retained as first-stage evidence.

## Motion and cloth

CMU 77_02 is standing and 02_01 is walking. The BVHs are Bruce Hahne's 2010 MotionBuilder conversion, retrieved from the una-dinosauria mirror. The accompanying licence permits research and commercial use and adds no restrictions on the conversion. Raw motion stays outside git. The data used in this project was obtained from mocap.cs.cmu.edu; the database was created with funding from NSF EIA-0196217.

`mocap.py` parses BVH channel order and computes forward kinematics, removes travel/yaw, and supplies real captured motion to `animate.py`. Idle uses standing torso deltas; march retargets sagittal leg motion and adds a shield-bearing guard. The weapon arm intentionally does not copy free-walking arm swing. Attack, hit and death are authored keys on the same MPFB rig. The attack raises an overhand grip outside the right shoulder, shifts weight over the bent front knee, and extends above the shield rim; the shaft slides through the grip during the raise to retain both ends inside the fixed cell. This is a reusable retargeting starting point, not a universal full-body motion solver.

```sh
for clip in idle move attack hit death; do
  tools/art/anim3d/render.sh "animate-$clip"
  RENDER_ENGINE=CYCLES SAMPLES=16 tools/art/anim3d/render.sh "e-$clip"
done
RENDER_ENGINE=CYCLES tools/art/anim3d/render.sh d
```

Each clip first checks the sampled spear path against the rigid equipment before baking. A failed rebuild invalidates its old clip metadata so it cannot be packed accidentally. Every clip has a one-second cloth pre-roll, followed by actual cloth simulation baked to its separate `.blend`. The five output lengths are 8/8/10/4/10 at 10/12/14/12/10 fps; idle and move loop. Death opens the right hand and releases the spear onto the front edge of the stone before the body rolls onto it; the shield settles farther back. Its last two output samples use the same settled frame. `d` shows four attack poses. Each `e-*` writes a PNG strip with native 256 px cells and 64 px versions, plus animated WebP. Review animations loop for inspection even when the runtime clip is non-looping.

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

Packing preserves all 40 frames, creates a 2560 × 1280 transparent WebP grid, quantizes alpha to 32 levels, and selects quality 85–60 while enforcing **200,000 bytes**. It refuses to overwrite delivery with an oversized atlas. The JSON format is exactly `{frame:{w,h,ax,ay}, clips:{name:{row,frames,fps,loop}}}`, anchor `(127,221)`. `pack.json` binds the atlas to each raw frame by SHA256 and records the actual engine/resolution/sample manifest for each clip. Packing refuses stale renders or clips whose source master hash differs from the current master; an interrupted rebuild cannot silently reuse old clips. Rendering invalidates its old manifest before writing frames, so an interrupted rerender also blocks packing. `validate.py` checks decoded size, metadata, all clips, alpha, padding, clipping margins, actual motion and held death. `audit.py` checks saved geometry, cloth, source topology and stationary base across all samples, plus hand-to-shaft distance before an intentional death release and spear centerline intersections with cuirass, shield and helmet bowl. It is not a full skin/cloth collision solver. `AUDIT_CLIP=attack tools/art/anim3d/render.sh audit` checks only an iteration of the attack.

The review bar is the original painting: equally rich at 256 px, same identity and scale at 64 px, convincing anatomy and equipment, no plastic, blurred or toy-like finish. Compare source and render side by side; inspect chest, helmet and shield close-ups. Check planted feet, grip, spear clipping, cloth intersections, terminal death and the loop seam in motion. No technical check substitutes for the lead's art verdict. Keep the existing painting in the game until that bar is met. No app runtime is changed by this pipeline.

For the next unit, start new external master and review directories; calibrate the painting's camera, proportions and anchor first. Adjust the MPFB macro targets, fit new kit to the same skeletal segments, select and license suitable captured motion, then author the combat keys. Repeat the plain, textured, pose and per-clip reviews before packing. Reuse the download, bake, retarget and validation approach; do not treat a copied spearman mesh, texture or motion as finished art for another unit.

## Round 2 findings and handoff

The original GPU sheets are retained in `review/3d-v2/round1-gpu/`. Round 2 checks the actual c/d/e frames at 256 and 64 px; CPU output is labelled by its render manifest and is not a GPU sign-off.

- Correct normals and bake topology before increasing AO. The aspis had inward winding, and Solidify's shared inside/outside UVs contaminated the original helmet/cuirass bakes. More contrast on that defect only produced black metal.
- Small-form identity needs geometry. The sunburst now has raised facet keels and side walls, a bright turned rim, and a less edge-on pose. The tall red crest is a front-to-back fan above a bronze bowl. Neither is supplied by a flat detail texture.
- A bright metal palette, cavity contrast, curvature polish, hammer-scale bump/roughness and stronger key/rim lights work together. Scanned roughness or fine grain alone disappears at 64 px. The painting still has richer authored engraving and cloth folds; a technically valid atlas is not art approval.
- Projected spear length matters as well as physical clearance. The first non-intersecting overhand pose was foreshortened; the revised direction shows the tip, while grip sliding keeps the butt inside the frame. Measure equipment intersections in world space rather than judging overlaps in a single picture.
- A runner checked lane-2 out to the siege branch during a rebuild. Its WIP commit preserved the work, but the mixed build used old geometry. Continue this branch from `legatum/.worktrees/spearman-round2/`; do not switch the active siege checkout. Model/clip/render hashes now guard packing. Finish a full rebuild before trusting any interim output after a checkout interruption.

The saved masters already contain the revised geometry, materials, rig and cloth caches. From the spearman branch checkout, the lead should render the GPU review and then repack:

```sh
tools/art/anim3d/render.sh c
RESOLUTION=512 tools/art/anim3d/render.sh detail
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/details.py
tools/art/anim3d/render.sh d
for clip in idle move attack hit death; do
  tools/art/anim3d/render.sh "e-$clip"
done
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/pack.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/validate.py
tools/art/anim3d/render.sh audit
```

Run each heavy stage sequentially. Other unit lanes share the same lock; if one owns it, let its job finish. Then review both sizes and motion, including the attack's grip/clearance, cloth, feet and held death, and run the project's browser/art gate against the committed branch. Keep the painting in the game until the lead approves the candidate.

## Vehicles — hunter-killer mechanical walker

`units/hunter-killer/` is an isolated vehicle-family lane. The painting shows a planted four-legged armoured **machine**, not an aircraft or robot dog. Match the low broad hull, short autocannon, small turret with paired sensors, thick near leg and broad flat feet. All six Blender skills are applied. No changes to game rules or runtime are required.

Build and review from the repo root:

```sh
tools/art/anim3d/units/hunter-killer/render.sh build
SAMPLES=4 tools/art/anim3d/units/hunter-killer/render.sh b
tools/art/anim3d/units/hunter-killer/render.sh finish
SAMPLES=8 tools/art/anim3d/units/hunter-killer/render.sh final
```

The scripts reuse `env.sh`, plain gated `blender -b --disable-autoexec`, and existing Pillow/FFmpeg. One heavy process runs at a time. `model.blend`, `plain.blend`, `finished.blend`, five keyed clip scenes and six actual AO/Pointiness bakes live under `$ANIM_ROOT/masters/hunter-killer/`. Never hide a mesh by shrinking it: the finite muzzle flash uses visibility keys. The six-face hull and full-depth leg armour are closed geometry, with machined bevels and surface-fitted deck fittings; plain side/front images reveal the volume. Camera-space landmark construction is an approximate registration, not a reconstructed physical camera solution.

### Four quality levers and judgement

1. Standard method: uniformly register the original full painting to the token field and freeze camera UVs on the real rest mesh. Blend by facing/alpha confidence into the existing generated olive brushwork on hidden surfaces. Projection never cuts the mesh's alpha. The static stone is independent, so moving legs leave no painted feet behind.
2. Finish physical geometry: bevel edges, closed armour thickness, separate joint caps, hydraulic rods, broad feet, fitted hatches, recessed optical lenses and barrel. Six real AO/Pointiness maps drive cavity grime and edge wear; grain modulates normals. No mesh is merely a painting card.
3. Warm upper-left key, cool rim, soft fill and contact AO. Final Cycles/Metal output is denoised. Camera-only pigment avoids double-lighting the source; Standard/None is intentional for painted colour, not a photographic preset. Base fallback pigment is sRGB **#E9CFA0**, converted to linear, with physical contact shadow and warm camera pigment so the rim does not go grey.
4. One bounded monotonic RGB grade comes from rest-pose opaque 10/50/90 percentiles and is frozen across the entire set. The painting/render/50-50 crossfade at native 256 and 64 px is `hunter-killer-f-restpose-compare.png`. A favourable metric is not art approval.

Publish every stage immediately: `b-plain`, `c-textured-lit`, `c-details`, `d-rig-poses`, each `e-<clip>-strip` and animated WebP; maintain the unit log and check arriving unit feedback. The per-clip images are CPU previews until an explicit GPU receipt says otherwise.

### Motion and planted-foot check

For people the standing standard is CMU free-use or Quaternius CC0 captured motion retargeted in matching rest pose and bone roll, with only the weapon-specific attack authored. For horses/elephants use an open animated quadruped; never repair foot direction by rotating feet after retargeting. Record licences in both unit and external source ledgers. This machine instead uses the vehicle family's authored mechanical motion: a rigid chassis/turret/recoil rig and four analytic two-link limbs. Each quarter-cycle begins a foot swing lasting three eighths of a cycle; its ground position and forward orientation stay fixed while planted. Move is a deliberate on-the-spot stepping cycle, not locomotion with simulated world displacement. Idle scans, attack aims/recoils, hit jolts, and death collapses the chassis into folded legs and holds its final two samples. No squashed segment lengths or zero scale.

Every round renders all eight move samples from top and front to `hunter-killer-g-feet-check.png`. The audit independently reads saved foot transforms and records planted-position error, segment-length error, stationary base, closed mesh topology, nonzero scales and terminal hold. Visual review must still catch silhouette faults, collisions and timing.

### Trimmed 160 px contract and GPU handoff

All 40 frames remain: idle 8, move 8, attack 10, hit 4, death 10. Actual final renders are 512 px; 256 px gallery masters are downsampled and retained alongside them. CPU256 previews are never upscaled into 512 masters. Delivery uses premultiplied reduction to a logical 160x160 cell, transparent-margin trimming, lossless full alpha and WebP quality 95/90/85/80/75, stopping at the highest quality below **200,000 bytes**. Failure at Q75 stops rather than reducing frames/quality.

JSON has `version:2`, `trimmed:true`, `frame:{w:160,h:160,ax:80,ay:139}`, `atlas:{w,h}` and `clips`. Each clip has ordered `row`, `frames`, `fps`, `loop`, and one `rects` record per frame: `{x,y,w,h,ox,oy}`. Draw the atlas crop at `(anchorX-ax+ox, anchorY-ay+oy)`, scaling all coordinates equally. `row` is clip ordering, not a fixed atlas grid. Identical held frames reuse one rectangle. No runtime consumer is changed here.

```sh
ROUND=2 tools/art/anim3d/units/hunter-killer/gpu.sh
```

The no-argument executable renders every stage and every clip serially in Cycles GPU512 (96 samples default), publishes 512/256 masters, packs and validates the trimmed atlas, writes the geometry audit, and creates `hunter-killer-round${ROUND}.mp4`: all five decoded clips side by side at 2x on cream, exactly 8 seconds/240 frames, H.264 yuv420p. Missing Metal fails explicitly. Final independent verification checks scene/render/grade/atlas hashes, GPU device, resolution, complete frame sets, video format and duration. Progress/failure lives in `hunter-killer-gpu-status.txt`; transcript is `gpu-logs-hunter-killer-r${ROUND}.log`. Only a manual painting-parity judgement plus clean clips and a passing size contract may create `hunter-killer-PASS`; the scripts never write it automatically.

### Driver round 2 refinements

The lead's first GPU pass succeeded: 187,526 bytes at Q90, 40 GPU512 frames, independent GPU receipt and eight-second MP4. Preserve that evidence before overwriting previews (`masters/hunter-killer/driver-r1-gpu/`). Round 2 fits the outer upper plates and three shin silhouettes as closed extruded armour, brings the far-left foot inward, rounds the stone edge and adds recoil anticipation/recovery plus chassis weight shift. Longer overlapping foot swings reduce one-frame foot pops; forward reach is limited because the rear leg is close to full extension. Planted foot positions and segment lengths still come from the IK audit. This remains in-place mechanical stepping, not captured advancing locomotion.

A new generated clean stone fill removes the walker and its contact shadows from the reference. Fit that texture to the disc landmarks, feather back to the original unobscured rim below y184/256, then freeze UVs on the physical disc. Its alpha blends pigments only, never cuts geometry. Camera-visible mineral grain and real AO retain surface detail without leaving painted feet when legs lift. The prompt, generation identity and input hash live in the unit files; the bitmap stays under `assets/hunter-killer/`. Existing generated olive still fills unseen armour. Cloth and straps do not apply to this machine.

`render.sh build` starts a recipe/input seal; `finish` seals the complete eight-scene set only after all clips succeed. Final rendering and `gpu.sh` reject incomplete builds, changed recipes, changed derived textures and stale scene hashes. Rebuild then finish after any geometry/material/motion recipe change. GPU defaults to ROUND=2; the driver may override it. Every stage is published as soon as rendered. CPU checks use 256 px Cycles at 16 samples; GPU final remains a separate host pass at 512 px/96 samples. No automatic PASS marker.
