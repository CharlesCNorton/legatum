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

## Infantry: Byzantine heir (round 1)

The crowned heir uses the infantry MPFB anatomy/rig helpers with new lamellar kit,
boots, folded purple mantle and banner. All unit-specific entry points are in
`tools/art/anim3d/units/byzantine-heir/`; masters are outside Git under
`$ANIM_ROOT/masters/byzantine-heir/`. Every Blender invocation is plain `blender -b`
and obeys the shared gate. CPU previews use Cycles; the strict GPU path configures
Metal Cycles and refuses to fall back silently.

The standard quality method follows feedback 18–21: align the rest camera and
silhouette to the committed painting, project the full source onto **real 3D
surfaces** using frozen rest-pose UVs, and blend generated painted fills onto
unseen surfaces through facing/alpha masks. Beveled lamellae, jewel bezels, crown,
thick folded cloth, MPFB face/hands, skinning and boot volumes carry real form.
AO and Pointiness curvature are baked on the torso, skirt, shoulder mantle and
anatomy. Warm upper-left product lighting, soft fill and a cool rim preserve depth.
The base uses linearized `#E9CFA0` (approximately `.815,.624,.352`), fine bump and
one beveled stone disc. A bounded histogram grade is measured from the rest frame
against the painting and applied unchanged to all clips; no per-frame pumping.

```sh
tools/art/anim3d/units/byzantine-heir/run.sh build
source tools/art/anim3d/env.sh
blender -b --disable-autoexec --python tools/art/anim3d/units/byzantine-heir/bake.py
tools/art/anim3d/units/byzantine-heir/run.sh animate
# CPU review: b, c, e-idle, e-move, e-attack, e-hit, e-death
# Lead's entire final GPU pass, no arguments:
ROUND=1 tools/art/anim3d/units/byzantine-heir/gpu.sh
```

`gpu.sh` produces all stages at 512 px, retained 512/256 masters, native 256/64
comparisons, detail crops, four attack poses, five strips and animated WebPs,
`byzantine-heir-f-restpose-compare.png` (painting/render/50% crossfade), the trimmed
atlas, validation, and `byzantine-heir-round${ROUND}.mp4`. The MP4 reconstructs
trimmed frames, shows all five clips side by side at 2x on cream for eight seconds,
and uses H.264 yuv420p. Cloth follow-through is authored with deformation keys;
it is not a claimed physics simulation. The final death pose holds. A clean
pack/validation is not art approval; write no PASS marker until rest and motion
actually meet the painting.

### Heir trimmed atlas format, version 2

The logical frame remains `frame: {w:160,h:160,ax:76,ay:144}`. Rows are idle,
move, attack, hit, death with 8/8/10/4/10 frames. Each clip keeps `row`, `frames`,
`fps`, `loop` and adds `rects`, one entry per sample:
`{x,y,w,h,ox,oy}`. The first four fields locate the trimmed rectangle in the atlas;
`ox,oy` locate it inside its original transparent 160 px cell. Reconstruct at
`(ox,oy)`, then place the logical frame using `ax,ay`; never center each crop.
Rows occupy 160 px, with explicit rectangles including two-pixel gutters; columns have variable widths. Identical logical samples may share a rectangle. Quality is selected
from 90/85/80/75, never lower, with a strict 200,000 byte ceiling. No frame counts
are reduced. Model/clip/render hashes reject stale output. This candidate is not
wired into the game; a consumer needs trim-offset support before activation.

### Heir resumed round 2: finished surfaces and stable delivery

`units/byzantine-heir/refine.py` restarts from `projection-input.blend`, a copy
of the successfully baked master. `bake.py` refreshes that checkpoint after a
source rebuild. Freeze MPFB macro shape keys before fitting weighted vertices;
invert their blended bone transforms to fit anatomical feet inside the boots.
Finish rigid bevel/solidify geometry and body subdivision before freezing the
rest-camera UVs. Dense cloth retains its authored shape keys and thickness.
Crown/hair, boot contact and the train are fitted in real geometry. This is still
an approximate silhouette match, not a claim of exact registration.

The existing generated silk/linen/leather/metal fills and real AO/curvature stay
in the physical material. A camera-ray-only Principled pigment branch carries
96% of the source's already-painted illumination on facing surfaces; non-camera
rays keep the physical shader. Standard/None avoids a second AgX compression of
that pigment. The warm key, soft fill and cool rim remain; the round stone has
fine grain and a camera-only cream contribution to open its physical shading.
Boot masks reject the separate painting's cream stone. No geometry is hidden
using source alpha, and no static painted feet enter the base.

Move uses ankle IK and actual sole clearance for the lifted return and planted
stance. Death includes authored distal-cloth settling, not a claimed cloth sim.
After equality of evaluated terminal geometry, copy the final held PNG instead
of rerendering it with different noise. All 8/8/10/4/10 samples remain.

The executable no-argument `gpu.sh` defaults to ROUND=2, resolves its checkout,
retains a round transcript and failed-stage status, checks Metal before editing,
runs refinement/animation/all render stages, verifies GPU512/48 and 256 gallery
provenance, then packs, validates and writes the required eight-second decoded
atlas MP4. Grade provenance binds the current master, reference and rest PNG;
packing rejects mixed render settings or stale calibration. CPU preview results
are not GPU evidence. No PASS file is created by the technical pipeline.

Heir delivery now uses bicubic reduction with full lossless alpha, two-pixel
gutters and identical-frame rectangle reuse. Validation compares every decoded
alpha byte and requires identical terminal death pixels. The reference remains
the untrimmed logical 160 px cell; use each rectangle offset, never recenter it.

### Heir motion update: common feedback 23

Use proven open motion by default: CMU free-use or Quaternius CC0 for humans,
CC0 animated quadrupeds for animals, with only weapon-specific attacks authored
on top. Match source/target rest poses, coordinate axes and bone rolls. Do not
repair a faulty retarget by overwriting foot orientations each frame. Record each
recording URL/licence/hash in the unit's SOURCES.md and assets/SOURCES.md. Render
a top-down and front foot cycle every round as `<slug>-g-feet-check.png`; inspect
travel direction, contact and sliding. This is a motion-quality gate, separate
from successful encoding.

The heir now uses `motion.py`: CMU 77_02 standing, CMU 02_01 walking (one 132-frame
capture cycle), and CMU 90_18 rug-pull fall for death plus an early balance-loss
excerpt for hit. The source hit excerpt is retimed forward/back to recover. It
is not described as a recorded weapon strike. Global rotations use fixed Y-up /
Z-up and forward-axis calibration with measured rest/bone-roll offsets. Foot
rotations come from the capture; grounding translates the whole rig. Root motion
and exact source samples are recorded in clip metadata. Cloth and banner release
remain authored secondary motion. `g-feet` renders all eight move samples from
each diagnostic viewpoint, and `gpu.sh` includes that stage at final resolution.
The earlier authored-march delivery numbers are superseded by the external log's
final CMU candidate results.

The heir retarget also uses the capture's ankle positions to solve target limb
lengths/rest spread, while retaining the captured foot orientation target. This
is positional IK retargeting, not a constant angle pasted over the feet. The
root trajectory is recorded in metres in the move clip/atlas metadata; in-place
stance motion must be judged with that removed travel in mind. The rigid ankle
cuffs still require visual review at strong foot pitch. The backward captured
fall receives ground-plane framing translation after cloth settling; released
banner world keys are preserved. Never fix a clipped fall by lowering atlas
quality or masking the figure.

For stance-slip checks, compensate the retained in-place frames with their
recorded root travel. The heir's source/target proportion differences initially
left about 11 cm of measured stance residual. Translation-only contact locking
now pins the actual sole patch during support, using captured ankle targets and
preserving the capture's orientation. Inspect and record the measured residual
and direction from `audit.json`; bone provenance alone does not prove clean
motion. Never label a technical atlas pass as an animation/art PASS.

### Heir driver round 2: continuous costume and captured fall arms

After opening the actual round-1 GPU sheets and MP4 frames, preserve that evidence
under `masters/byzantine-heir/driver-r1-gpu/`. `finish_geometry.py` runs inside
`refine.py` before projection and binds finished costume vertices through the
inverse blended pose matrices. The calf-to-foot boot skin keeps its lower cuff
inside the closed shoe while preserving the original captured foot rotations.
The skirt and hem blend into the thighs; the individual lamellae use constant
per-plate weights. Dark woven breeches cover the leg anatomy revealed by a fall.
These are real geometry/material changes, with no alpha cutout or hidden feet.

Lower the rear neckline in every cloth shape key, fit the hair-cap top to the
painting contour while retaining depth, and add limestone mineral variation.
Existing generated silk/linen/leather/metal fills and AO/curvature remain in the
shader. Projection is frozen after fitting; the fixed rest-derived histogram
grade remains shared by all clips. `finish_version=3` guards the new checkpoint.

The CMU fall now supplies arm rotations and released-hand position targets;
keeping a weapon-carrying elbow offset through a fall made the earlier pose rigid.
Idle uses a quieter 96-source-frame standing excerpt. Cloth settling remains
an authored deformation with support folds, not a physics simulation. Audit the
actual evaluated cuff vertices inside each shoe BVH for both legs in every pose,
in addition to travel-compensated stance drift and foot direction.

The required no-argument `gpu.sh` still renders GPU512/48 and gallery256, all
review stages, the trimmed atlas, validation and the round MP4. It now checks for
the baked projection checkpoint and tees its transcript to the driver as well as
the retained per-round log. Run `ROUND=2 tools/art/anim3d/units/byzantine-heir/gpu.sh`.
Fresh CPU previews are technical and visual iteration evidence, not GPU approval.

Source projection also freezes camera-ray visibility so occluded boot tops and
underlayers use their generated material fills instead of borrowing purple cloak
pixels. Measure raw indexed UV positions first, then restore MPFB's helper mask
before ray casting. Leaving that mask disabled turns non-rendered face helpers
into false occluders and creates blotches in the visible painted face.

The final fall samples CMU 90_18 through frame 360 of 395, holding that later
settled pose twice; frame 200 was still mid-fall. The source list is recorded in
clip metadata. Extending the capture does not by itself solve the skirt lining
and cloth-shape limitations exposed in the fallen pose.


### Heir driver round 3: lined tunic and attached ornament

The round-2 GPU pass succeeded (170110 bytes, Q85); its complete review and
512/256 masters are retained under `masters/byzantine-heir/driver-r2-gpu/`.
The visual failure was a hollow skirt and depth-detached jewels exposed by the
captured fall. Rest-camera projection can conceal those construction defects.

`finish_geometry.py` now fits low leather lasts, densifies the hem/skirt before
skinning, adds a thick sewn lining with two leg openings, and covers the pelvis
as well as the thighs with the existing generated woven fill. The lining uses
that same licensed image-generated linen, dyed plum-brown. `garment.py` adds a
pose-space gravity fold with evaluated anatomical clearance; it is authored
cloth deformation, not a simulation. Keep the shoulder wrap attached to the
chest rather than applying the long train's ground-settling deformation to it.
Seat each bezel and garnet on its actual backing in depth. Camera-ray fitting
preserves projected positions where possible; the overhanging shoulder clasp
uses the nearest sewn edge. Audit backing clearance in every output pose.

Hair/crown geometry is constrained to the reference contour while retaining
depth. Only the unobstructed source rim below camera y=230/256 is projected onto
the stone; the upper base remains physical with moving contact shadows. Never
copy source boots or their shadows onto the stationary disc. The original four
generated fills, bevels, bakes, warm key/fill/rim and fixed histogram grade remain.
`finish_version=4` identifies this construction. Review now rejects stale grade
provenance as well as packing. Source UVs include the dense lined garments.

Run `ROUND=3 tools/art/anim3d/units/byzantine-heir/gpu.sh` from the repository root.
It rebuilds this finish and every clip, renders all stages on Metal Cycles at
512/48, retains 512/256 masters, packs and validates the trimmed 160 px atlas,
and writes the eight-second round MP4. It does not grant visual PASS.
