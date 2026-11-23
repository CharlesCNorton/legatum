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

## Infantry: legionary, round 1

The legionary lane lives entirely in `units/legionary/`. `UNIT=legionary` dispatches
through the shared `render.sh` without changing the spearman entry points. Its
external master directory is `~/LegatumRuns/anim-pilot/masters/legionary/`, inputs
are in `assets/legionary/`, and reviews use the `legionary-` prefix. All Blender
commands are plain `blender -b --disable-autoexec ...`; the executable on PATH
owns CPU/GPU scheduling and the three-thread cap. Do not bypass it or add another
Blender process. The six Blender skills informed geometry, materials, lighting,
camera calibration, skeletal animation and render inspection.

The model uses MPFB 2.0.18 CC0 anatomy (19,158 source vertices), CC0 system eyes and
its 53-bone game-engine skeleton. Original equipment includes overlapping iron
lorica plates, articulated shoulder lames, thick linen scarf, open bronze helmet
with cheek and neck guards, folded red tunic, studded leather apron, sandals,
curved thick scutum with metal rim and boss, and a pilum with an iron shank.
No human anatomy is assembled from primitives. The generated four-material fill
atlas and painting have pinned hashes in external `inputs.json`; the generation
prompt is committed beside the scripts. Source/licence records are in the shared
external `assets/SOURCES.md` and repository `app/src/assets/PROVENANCE.md`.

### Painting-first finish and review standard

Use these four quality levers together, following standing feedback 12–21:

1. **Camera projection is the standard method.** Match the painting's rest pose,
   orthographic camera, height and silhouette first. `prepare.py` aligns the full
   painting to its committed token. `paint.py` freezes camera UVs onto actual
   weighted meshes, blending by surface incidence and source alpha into original
   generated cloth/leather/iron/bronze fills on unseen surfaces. UVs travel with
   geometry; there are no billboards or screen-space animation warps. A skin mask
   prevents the scutum from painting red onto the body. Registration is approximate
   and painted lighting remains partly baked into the colour: motion needs review.
2. **Finish geometry.** Real thickness, bevels, curved plates, rolled borders,
   buckles/studs, anatomical subdivision and folded cloth matter at token size.
   The shield's gilded motif gets shallow source-aligned relief. `paint.py` bakes
   eight actual 512 px AO/curvature maps for helmet, shield, an iron band and skin;
   these drive cavity shading and roughness. This is not a claim of a full-body
   sculpt or a complete collision solver.
3. **Product lighting.** Warm upper-left key, cool rim, soft fill, real contact
   shadows, Cycles and denoising. CPU previews are explicitly labelled. GPU Cycles
   requires a Metal device and fails rather than silently falling back. The base
   is one stationary cream disc with fine grain. Common displayed target:
   **sRGB #E9CFA0**, with a darker warm side; linear shader values must be calibrated
   under lighting instead of treating sRGB values as linear inputs.
4. **Measured grade.** The rest render and painting supply 17 foreground quantiles
   per RGB channel. `review.py` blends a bounded 35% transfer into one monotonic LUT
   and reuses that same grade for every frame, preserving raw images. A new rest
   render changes the grade hash and requires a full clip refresh before packing.

Every `c` render publishes native 256/64 px comparison, close-ups and
`legionary-f-restpose-compare.png` (painting, render, half-split, 50% crossfade).
The target remains near-indistinguishability at rest. Current round 1 is a review
candidate: face, cylindrical torso, shoulder fit and motion-revealed projection
seams still fall short of the painting. Technical validation is not art approval.

### Rebuild and host GPU review

```sh
UNIT=legionary tools/art/anim3d/render.sh prepare
# Serial build/plain review/paint/rest review/animation/pose review/all clips/audit.
UNIT=legionary RENDER_ENGINE=CYCLES CYCLES_DEVICE=CPU SAMPLES=8 tools/art/anim3d/render.sh round
UNIT=legionary tools/art/anim3d/render.sh pack
UNIT=legionary tools/art/anim3d/render.sh validate
```

`STAGES=...` selects a comma-separated serial subset for `round`. Individual
`build`, `b`, `paint`, `c`, `c-details`, `animate`, `d`, `e-idle`, `e-move`,
`e-attack`, `e-hit`, `e-death`, `audit`, `pack`, and `validate` stages also work.
`animate` creates all five actions (`CLIP=death` selects one for a correction). Idle breathes; move is an authored planted
march; attack anticipates and drives a shield bash while retaining the pilum;
hit recoils; death releases the pilum/scutum and folds the body onto the base.
The tunic hem has authored shape-key follow-through, **not simulated cloth**.
Death resolves evaluated worn geometry onto the stone while keeping released equipment in world space, then holds identical final geometry and final source pixels. Clips keep
8/8/10/4/10 samples at 10/12/14/12/10 fps. Idle and move loop.

The lead can rerender all saved masters under one GPU gate acquisition:

```sh
UNIT=legionary RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=64 \
  STAGES=c,d,e-idle,e-move,e-attack,e-hit,e-death,audit tools/art/anim3d/render.sh round
UNIT=legionary tools/art/anim3d/render.sh pack
UNIT=legionary tools/art/anim3d/render.sh validate
```

The lead must inspect GPU rest, details and motion again; CPU output is not GPU
sign-off. Each stage publishes its review immediately. Every colour frame retains
512 px raw and graded PNG masters plus graded 256 px images under
`masters/legionary/renders/<stage>/`. The plain diagnostic defaults to 256 px.
Hashes bind model, clip, raw frame, grade and atlas; stale stages refuse packing.

### Trimmed 160 px atlas format

This lane implements feedback 20, superseding the older 256 px grid for this unit.
The delivery retains `{frame:{w,h,ax,ay},clips:{name:{row,frames,fps,loop}}}` and
adds `format: "trimmed-rows-v1"`, `atlas:{w,h}`, and a `rects` array to each clip.
The canonical frame is transparent **160 × 160**; anchor `(79.375,138.125)` is the
existing `(127,221)` anchor scaled by 160/256. Clips occupy five packed rows in
idle/move/attack/hit/death order. Each frame rectangle is:

```json
{"x":0,"y":0,"w":84,"h":147,"ox":38,"oy":8}
```

`x/y/w/h` describe its atlas crop. `ox/oy` place that crop in the original 160 px
cell. To draw at an anchor, use destination `(ox - ax, oy - ay)`, multiplied by
the display scale. Do not derive an atlas crop from `row * frame.h`: row height
and frame width are trimmed. No runtime loader is changed by this candidate.

Packing keeps all 40 frames and tries WebP quality 90, 85, 80, then 75. It refuses
anything over **200,000 bytes** at quality 75; it never drops frames or lowers the
quality floor. Validation reconstructs every cell, checks source margins, alpha,
padding, motion, held death, and all source hashes. The geometry audit checks
stationary base, nondegenerate scales, base penetration and pilum centreline
intersections with rigid armour/helmet/shield. Skin/cloth intersections and grip
appearance still require visual review.


### Legionary round 2: shoulder fit, finished surfaces and complete handoff

The old shoulder caps were attached to the upper-arm bones in the A-pose. Lowering
those arms rotated the caps upright. They now hang from the cuirass/spine segment,
with the crown lowered 11 cm; the body-derived upper cuirass stops below the neck.
This is a rigid shoulder yoke, not a simulated articulated shoulder mechanism.

Before freezing projection UVs, `paint.py` freezes MPFB macro shape keys on its
working copy and applies static thickness/bevel/subdivision on rigid equipment.
The original 19,158 anatomy vertices, weights and 53 bones remain; deforming skin
and tunic retain their modifiers. Curved straps/rims become real closed meshes;
the pilum remains a curve for the existing centreline collision audit. The clean
morphable input remains `legionary-plain.blend`. Repaint always reloads that input.

Camera-visible source pigment now preserves painted illumination, with 4% physical
response at fully covered, front-facing samples. Non-camera rays and uncovered
surfaces retain the original physical materials, generated fills and actual
AO/curvature bakes. Standard/None avoids compressing source paint a second time;
the three product lights retain their ratios at 55% energy. This display-transform
choice is specific to painted illumination, not a photographic rendering preset.
One automatic rest histogram LUT is still frozen for all clips. Geometry and
source-object registration remain approximate; face/hand and motion seams need
visual review. The camera is unchanged, not claimed to match the painting exactly.

The stone uses camera-only top/rim pigment over physical shading and grain; no
painted feet or static source shadows are projected onto it. Sampled 512/CPU8
preview top is RGB 248.8/210.5/163.1 versus painting 250.6/211.4/163.6. Its rim
is 235.2/183.8/128.3 versus 236.2/188.8/130.7. These local samples do not prove
whole-image parity. Current silhouette overlap improved from .713 to .745.

The required executable, no-argument host entry point is now:

```sh
ROUND=2 tools/art/anim3d/units/legionary/gpu.sh
```

It regenerates all clips from the finished saved master, renders b/c/d and all
five clips with Cycles GPU at native 512 px (64 samples by default), publishes
256 px gallery copies, details and rest crossfade, runs the geometry audit,
rejects mixed/stale/CPU master provenance, packs and validates the trimmed atlas,
and writes `legionary-round${ROUND}.mp4`. `ROUND` is supplied by the driver.
The PATH Blender gate remains mandatory; a missing Metal device fails explicitly.
The unit transcript is `gpu-logs-legionary-r${ROUND}.log`; the status file records
running, failed command/exit, or technical completion pending visual acceptance.
No script creates a PASS marker automatically.

The five-row JSON contract is retained. Reduction now uses premultiplied bicubic
RGBA, preserving all 8-bit alpha instead of thresholding weak pixels. Exact
identical frames share a rectangle within their row without removing a playback
sample. Validation compares every reconstructed alpha byte with the logical
source cell and requires identical decoded held-death frames. The movie uses
those actual decoded rectangles and offsets: five clips side by side at 2x on
cream, 1600x348 H.264/yuv420p, 240 frames, eight seconds, verified by ffprobe.
Prior round evidence is retained outside git in `masters/legionary/round1-cpu/`.

The first richer projection exposed left fingers physically crossing the shield
face. Camera-ray queries identified the anatomy rather than a texture blemish.
The left wrist now sits 8 cm farther behind the shield, consistently in the rest
pose and all authored guards; the scutum keeps its original rest world transform.
The audit now checks actual skin/scutum triangle intersections in held poses as
well as the existing pilum centreline/kit test. It does not claim a general
skin/cloth solver, and the released shield/body contact in death still needs review.

### Legionary driver round 2: source motion, skin alpha and foot review

The driver's round-1 GPU pass completed successfully. Its masters and review
sheets are preserved in external `masters/legionary/driver-r1-gpu/`; subsequent
CPU previews must not be mistaken for that GPU evidence.

The round-3 finish method remains frozen camera projection onto weighted, thick
3D surfaces, image-generated fills for hidden areas, beveled equipment/folded
cloth, product lighting, and one automatic rest-derived histogram grade. This
round narrows/rounds the curved scutum, matches the cream base diameter, moves the
pilum wrist toward its painted landmark, opposes the thumb and brightens the ash
shaft. The skin mask now **multiplies** the painting alpha; replacing alpha had
projected black background into the hand/arm. Hidden skin reuses the original
project-generated Medjay fill with its own pinned hash. Registration is still
approximate, especially the face and hand; these changes do not establish parity.

Per common feedback 23, human idle/walk/hit/death use proven open motion by
default. Legionary retargets Quaternius CC0 `Idle_Loop`, `Walk_Loop`, `Hit_Chest`
and `Death01` through Blender world-rotation constraints. Helpers calibrate
source/target reference poses and bone rolls; anatomical rest aligns locomotion
legs. Walking layers the open idle's carrying arms; only the weapon-specific
shield attack remains fully authored. Hit timing traverses the captured reaction then reverses through it to recover
the guard within four samples. A short guard-to-death source blend,
equipment release and authored tunic follow-through remain explicit adaptations.
No imported mannequin is rendered. Unit `SOURCES.md` and the external source
register record the exact library URL, version, licence and verified hashes.

Never fix a retarget by rotating the feet afterward. A small root XY correction
locks source-designated stance ankles to one virtual map-travel speed, preserving
captured toe/foot rotations. Loop closing poses are keyed explicitly. Root Z
keeps sandals in contact; this is not a general whole-body contact solver. Sandal
straps are fitted to actual posed skin, then inverse-bound to nearby anatomical
calf/foot/toe weights so toe roll no longer leaves rigid straps behind.

Every round now renders **`legionary-g-feet-check.png`**, front and top views of
all eight move samples. `feet_audit.py` checks stance toe heading and ankle XY
slip relative to implied travel; it explicitly does not certify the entire sole.
Inspect strap contact, roll and foot sliding visually as well. `compare.py`
records silhouette IoU and foreground RGB error at 256/64, with no art-pass
threshold. Do not replace a visual judgment with these measurements.

```sh
UNIT=legionary RESOLUTION=512 SAMPLES=8 CYCLES_DEVICE=CPU \
  tools/art/anim3d/render.sh round
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/legionary/check_delivery.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/legionary/feet_audit.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/legionary/compare.py
UNIT=legionary tools/art/anim3d/render.sh pack
UNIT=legionary tools/art/anim3d/render.sh validate
ROUND=2 "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/legionary/video.py
```

The no-argument executable `units/legionary/gpu.sh` includes the foot renders and
checks alongside every previous stage, 512/256 masters, trimmed160 packing,
validation, rest crossfade and eight-second H.264 movie. The driver supplies
`ROUND`; the script never writes an art PASS automatically.
