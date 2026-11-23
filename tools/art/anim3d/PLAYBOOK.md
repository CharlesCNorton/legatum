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

## Vehicles — Panzer unit lane

Panzer-specific code is isolated in `tools/art/anim3d/units/panzer/`. This chapter
supplements the spearman workflow; it does not replace other family chapters.
The vehicle family scripts were read from `astra/unit-anim-3d-vehicles` and adapted
locally. No human body or motion library is appropriate for this uncrewed miniature.
All six Blender skills are used: closed beveled armour and skirt thickness,
physical pigments/grain, three-point product lighting, painting-camera alignment,
rigid mechanical animation, and inspected sequential renders.

Build from the repository root:

```sh
U=tools/art/anim3d/units/panzer
"$U/run.sh" build
"$U/run.sh" b
"$U/run.sh" bake
"$U/run.sh" paint
"$U/run.sh" c
"$U/run.sh" details
"$U/run.sh" animate
"$U/run.sh" d
for clip in idle move attack hit death; do "$U/run.sh" "e-$clip"; done
"$U/run.sh" g
"$U/run.sh" audit
"$U/run.sh" pack
```

Every Blender call is plain `blender -b --disable-autoexec`, through the installed
PATH gate. Never call the application directly, pass a private thread override,
or start a second heavy process in this lane. CPU previews use Cycles, 3 threads,
4–8 samples at 256px. Smoke has real thickness and keyed visibility; no zero scale.

The model has full-depth closed hull armour, a polygonal turret, open-front turret
skirts, ten separate hull skirts on hangers, sixteen road wheels in eight paired
bogies, 144 individual moving track shoes, and an actually ported two-chamber
muzzle brake. The rig is a rigid parent hierarchy: suspension root, turret
traverse, recoil group, wheel pivots and link pivots. The stone disc stays fixed.
Idle/move are loop candidates; attack recoils the gun; hit jolts the hull; death
settles the hull and gun, darkens the vehicle pigment and emits a small smoke
plume. Its last two output samples are identical. Frame counts/fps are
8/10, 8/12, 10/14, 4/12, 10/10 for idle/move/attack/hit/death respectively.

### Quality method and judging

The four standing quality levers are standard: (1) align real geometry to the
painting camera and freeze projected UVs from the full-resolution source;
(2) bevel edges, model real thickness and hardware, and bake AO/curvature;
(3) use a warm upper-left key, soft fill and cool rim with Cycles denoising;
(4) measure painting/rest RGB quantiles and apply one bounded grade to all frames.
The rest-pose sheet always includes painting/render/50-50 crossfade at native
256px and 64px. A valid atlas is not a painting-parity verdict.

The base target is warm cream **#E9CFA0**, with a darker rim and fine grain,
never neutral grey. Shader inputs are linear values rather than sRGB hex values:
judge the rendered pixels. The projected rest-camera painting preserves the
painting's own warm stone and contact shadow. Hidden-surface fill reuses original
generated olive brushwork with sand pigment; CC0 steel and travertine scans add
grain. Full source hashes and licences are in the unit's `assets.lock.json` and
`SOURCES.md`, plus external `assets/SOURCES.md`.

Projection is frozen to real meshes; the camera and topology must be registered
before baking. Moving shoes/grousers/pins and every rotating wheel descendant retain their own
physical pigment so painted wheel fragments do not circulate around the belt or
smear around a wheel axle. The round-one video exposed this defect; projection
was removed from wheel surfaces before final packing. Hidden surfaces and
larger viewpoint changes remain approximate; round one's cupola, gun angle and
front running gear do not yet match perfectly. More geometric registration and
occlusion-aware projection are needed before approval. Do not claim that camera
projection alone solves three-dimensional texture layout.

### Motion and running-gear checks

The standard for human lanes is CMU free-use or Quaternius CC0 captured motion,
retargeted with matched rest poses/bone rolls and checked forward feet. Animal
lanes use a CC0 animated quadruped. Do not repair foot direction after a flawed
retarget. Record source and licence in both source ledgers. Only the weapon attack
is hand-keyed on top of captured human motion.

Vehicles use mechanical kinematics instead: panzer travels along +X; shoes follow
a closed circle-envelope route at constant arc length; road-wheel rotation is
travel/radius. The anchored token preview uses a treadmill convention (the app
would translate the token). `panzer-g-feet-check.png` renders all eight move frames
from top and front with a clay override to inspect tread direction and contact,
not camouflage. The numerical audit checks the closed route, contact direction,
stationary base, frame counts, retained volume, nonzero scale and actual vertex
bounds. It does not certify no projection distortion or a perfectly invisible
wheel loop seam. Both remain visual checks.

### Lead GPU handoff and masters

```sh
ROUND=2 tools/art/anim3d/units/panzer/gpu.sh
```

This executable takes no arguments, runs from the repo root, and performs the
entire pass sequentially: every review stage, all 40 clip frames and the top/front
check in Metal Cycles (`CYCLES_DEVICE=GPU`, default 128 samples), real 512px masters
plus downsampled 256px masters, geometry audit, trimmed packing/validation and an
eight-second H.264/yuv420p `panzer-round${ROUND}.mp4`. The five clips play side by
side at 2x on cream; non-looping clips replay with a held terminal pose. Missing
Metal fails explicitly. CPU previews are never upscaled and called 512px masters.
All masters remain in `$ANIM_ROOT/masters/panzer/`, outside git. Review sheets and
logs appear immediately under `$ANIM_ROOT/review/3d-v2/`.

### Trimmed atlas contract (version 2)

The shipped candidate is `app/src/assets/units/anim/panzer.webp` plus `.json`.
Logical frames are 160x160; each clip is its own atlas row, with per-frame trimmed
rectangles and two-pixel transparent gutters. Quality tries 95/90/85/80/75 and
fails if none fits **200,000 bytes**, retaining all 40 samples. Identical held
frames share one source rectangle. Masters retain full alpha and resolution.

```json
{"version":2,"trimmed":true,
 "frame":{"w":160,"h":160,"ax":79.375,"ay":138.125},
 "clips":{"idle":{"row":0,"frames":8,"fps":10,"loop":true,
 "rects":[{"x":2,"y":2,"w":145,"h":106,"ox":8,"oy":26}]}}}
```

This illustrative snippet shows one of eight idle rectangles. Real metadata has
all five clips and one rectangle per sample. `x/y/w/h` crop the atlas; `ox/oy`
place the crop in its logical cell. Draw at `(X-ax+ox,Y-ay+oy)` for anchor `(X,Y)`
and scale every coordinate consistently. `row` is ordering, not a fixed cell
height. This lane does not wire the extended format into the game runtime.
Validation checks bytes/quality, source and scene hashes, grade identity, clip
counts, rectangle overlap/padding, exact reconstructed alpha, motion and held
death. Video is decoded with ffprobe/ffmpeg and must have 240 frames, 8 seconds,
1600x348 pixels, H.264/yuv420p. `panzer-PASS` is written only after actual visual
parity and clean clips; scripts never manufacture that verdict.

### Panzer round 2: registration and wheel finish

The driver's round-one GPU pass succeeded (188,914 bytes at quality 75); it was
not painting parity. Preserve its evidence before replacing stage images. Match
near-side road wheels and end sprockets separately: the original wheelbase was
long and low, while the painting's end sprockets sit much higher than its road
wheels. The near/far registered track envelopes have separate arc-length routes,
but use the same travel distance and wheel angle = distance/radius. Do not shift
the far track out from beneath the front glacis to correct the visible near row.

Wheel faces now have full-depth dishes, raised chipped rings, hubs, six recessed
apertures and eight bolts. A generated ochre material swatch follows the wheels;
its exact prompt and source/hash are in this unit's files. Do not freeze painted
screen lighting onto a rotating axle. Original olive fill remains on hidden hull
surfaces. The extra wheel close-up in `c-details` exposes smooth, featureless or
over-dark running gear that can hide in a turret-only comparison.

Projection uses a conservative rest-camera visibility test. Reject a polygon
only when both its centre and all its vertices are occluded; centre-only masking
incorrectly erased the broad base top and the hull deck because their centres
were hidden while their edges remained visible. This is a conservative mask,
not a per-texel visibility bake; partially occluded faces remain a limitation.
Never compensate for bad masking by grading up the whole frame.

Keep cream stone fixed while the vehicle moves. Smoke uses irregular closed
meshes, staggered centres, keyed visibility and normal/view alpha falloff to
avoid the old hard oval outlines. These are surface-shell effects, not a fluid
simulation. All dimensions/scales stay positive. The GPU script now audits the
saved clips before rendering and verifies every stage actually used GPU/512px;
it writes a round-specific technical report but never writes the visual PASS.
