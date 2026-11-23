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

## Infantry / barbarian archer: round 1

This unit owns `units/barbarian-archer/`; other families and the original spearman
entry points are unchanged. Use the six installed Blender skills. The MPFB body,
face, hands, anatomical weights and game-engine skeleton remain real 3D anatomy.
The wolf-head pelt, thick folded mantle and skirt, fitted trousers and boots,
crossbelts, buckles, quiver, curved yew bow and string are original geometry.
The bow remains hand-attached; the string endpoints and nock follow the stave and
drawing hand. Five authored actions retain 8/8/10/4/10 samples. The base is stationary.
The cape's folds are modelled and bone-deformed in this round, not cloth simulation.

### Standard finish and judging method

Standing feedback 12–21 applies: a small valid atlas does not establish painting
parity. First match rest silhouette, camera and figure extent. Use **frozen
rest-camera UV projection of the painting onto actual mesh surfaces** as the
standard visible-colour method. Retain geometry and opacity; never use subject
cards or flatten the figure. The projected UVs deform with the weighted mesh.
Incidence and source alpha fade projection into generated fur, linen and leather
fills on unseen surfaces. The source is registered to the shipped 256 px token,
so full-master padding does not change composition. The generated atlas and
source hashes are external under `assets/barbarian-archer/`, packed into the blend.

Finish geometry before increasing projection: real thickness, rounded hard edges,
folded fabric, layered fur, buckles and distinct small forms. Actual 256 px AO and
Pointiness emission bakes on four principal meshes drive cavity colour and surface
roughness. Match warm upper-left key, restrained cool rim and soft fill to the
painting; Cycles denoising is used for the final pass. Grade from opaque-pixel RGB
quantiles of the rest render and painting, with one bounded LUT reused for every
clip. Preserve raw renders. The shared base target is displayed sRGB **#E9CFA0**:
this unit starts from linear pigment `(.815,.624,.352)` and fine grain, then checks
rendered colour under its own lighting. Never assume a hex shader alone guarantees
that displayed colour. No metallic component is used for stone or cloth.

Publish b/plain, c/textured, c/details, d/poses and each e/clip immediately. The
`barbarian-archer-f-restpose-compare.png` sheet contains painting, render, half-split
and 50/50 crossfade at native 256 and 64 px. Double contours and projection spill
are defects to report, not evidence of parity. The target remains a rest pose
that is barely distinguishable from the painting. This round is a review candidate.

### Commands and complete GPU handoff

From repo root, after the external source and generated fill are available:

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/barbarian-archer/prepare.py
tools/art/anim3d/units/barbarian-archer/run.sh build
tools/art/anim3d/units/barbarian-archer/run.sh b
tools/art/anim3d/units/barbarian-archer/run.sh finish
tools/art/anim3d/units/barbarian-archer/run.sh c
tools/art/anim3d/units/barbarian-archer/run.sh animate
```

Every Blender invocation is plain `blender -b --disable-autoexec` through the PATH
gate, one heavy process at a time, three threads. No direct application executable,
no zero-scale hiding, no paid asset or service. CPU defaults are Cycles/8 samples.
The complete no-argument lead-side script is:

```sh
tools/art/anim3d/units/barbarian-archer/gpu.sh
```

It requires Metal Cycles, refuses CPU fallback, renders every stage and all 40
frames at 512 px/64 samples, creates 512 and 256 masters, regenerates reviews,
packs and validates the atlas, and checks sources, real bakes and rig audit reports.
The saved plain/master/clip blend files are outside git in `masters/barbarian-archer/`.
The script rerenders saved geometry; it does not overwrite it with a rebuild.

### Version 2 trimmed atlas format

`barbarian-archer.webp` uses a 1600 × 800 grid, 160 px maximum cells. Each frame is
trimmed to its alpha bounds and packed at its cell's top left. `frame` remains
`{w:160,h:160,ax:75,ay:143}` in **untrimmed** coordinates. Each clip keeps `row`,
`frames`, `fps`, and `loop`; `rects[i]` adds `{x,y,w,h,ox,oy}`. `x/y/w/h` select the
trimmed atlas rectangle; `ox/oy` restore its location in the original cell. Draw at
`anchor + (ox-ax, oy-ay)` times display scale. Do not stretch trimmed rectangles
back to 160 px. Idle/move loop; attack/hit/death do not. The final two death frames
hold. Consumers must support this extension before enabling the candidate.

Quality is selected from 90, 85, 80, 75 while enforcing 200,000 bytes. The packer
refuses an oversized atlas at 75 instead of reducing quality or dropping frames.
Master and raw-frame hashes, actual engine/device/samples and grade hash remain in
`masters/barbarian-archer/pack.json`. No masters or source rasters belong in git.


### Barbarian archer round 2: finished projection and GPU movie

Resume from the preserved `plain.blend`; `finish.py` calls unit-local `refine.py`
without accumulating edits. Freeze MPFB macro shape keys before inverse-skin
fitting. Fit actual full-depth knees, head, raised arm and fingers in the rest
camera; retain native weights and the live rig. The bow uses a smooth sampled
curve fitted to the painted stave, with real tubular thickness and the original
hand attachment. Synchronize the rest string/nock/arrow with the animation solver.
The wolf muzzle/nose and ears move as real solid meshes, not texture patches.

Apply static Solidify/Bevel/Subdivision to the working surfaces before freezing
UVs, temporarily disabling the armature while applying garment modifiers. Remove
zero-level subdivision explicitly: Blender rejects applying a disabled modifier.
Actual AO/curvature bakes remain on four principal surfaces. Source projection
uses rest-camera visibility and incidence on the finished geometry; unseen parts
keep the original generated fur/linen/leather fills. Camera-only Principled pigment
preserves the painting's existing illumination without lighting other surfaces.
Standard/None and reduced 5:1 key/fill suit this painted layer; this is not a
photographic preset. One automatic rest grade remains frozen across all clips.
The physical cream disc still receives contact shadows and is never figure-projected.

`refined-plain.blend` is the new plain review input. The original round-one CPU512
frames and masters are preserved in `masters/barbarian-archer/round1-cpu/`.
Current CPU256 previews are never upscaled and labelled as 512 masters. Final
masters require the host pass. Run the executable, argument-free handoff:

```sh
ROUND=2 tools/art/anim3d/units/barbarian-archer/gpu.sh
```

It resolves its checkout, retains `gpu-logs-barbarian-archer-r${ROUND}.log`, records
failure stages, requires Metal, rebuilds all five clip blends from the current
master, renders all stages at GPU512/64 samples, exports 512/256 PNGs, packs and
validates the trimmed atlas, and encodes the decoded five-clip MP4. The movie is
H.264/yuv420p, 1600x348, 240 frames/eight seconds, 2x scale on cream. `ROUND` comes
from the driver. A technical completion receipt never creates the art PASS marker.

The atlas keeps the existing v2 1600x800 layout and per-clip `rects` contract.
Premultiplied bicubic reduction preserves thin contours without Lanczos ringing;
trim uses every nonzero alpha pixel. Validation compares reconstructed decoded
alpha byte-for-byte with all forty reduced source frames, verifies blend/frame
hashes, fixed grade, timing, offsets and held death. Stale master/clip/render or
mixed engine/resolution/sample settings fail instead of packing old images.
Remaining artistic defects and measured delivery results live in the unit log
and `units/barbarian-archer/REVIEW.md`. No gameplay or runtime wiring changes.

### Barbarian archer driver round 2: GPU review and open motion

The driver called the first host pass round 1 even though earlier CPU iterations
were labelled round 2. Preserve that actual GPU evidence under
`masters/barbarian-archer/driver-r1-gpu/` before updating previews. The host pass
succeeded; its technical receipt does not mean painting parity.

Use open motion for this human unit: the existing CC0 Quaternius Universal
Animation Library Standard supplies Idle_Loop, Walk_Loop, Hit_Chest and Death01.
`retarget.py` verifies input hashes, maps full rotations with Blender constraints
and calibrates reference/rest matrices including bone roll. Walk legs use the
matched locomotion rest; upper-body motion layers the library's idle onto a lower
bow-carrying pose. Do not rotate feet after retargeting to hide a wrong mapping.
The attack remains weapon-specific authored motion. Unit `SOURCES.md` records
URLs/licences; external per-clip motion JSON binds the action to the master.

An in-place gait is measured against virtual forward ground speed. Small root
translations stabilize sampled stance toes; actual boot geometry sets floor
height. This is not a full heel/toe contact solver. Render all eight move samples
from front and top every round with `run.sh g-feet`, including upper-body cutaway,
and inspect `barbarian-archer-g-feet-check.png`. The GPU handoff now includes this
stage and checks its source hash. Bow carrying height must be checked after
locomotion straightens the legs: matching the rest-pose bounds alone misses
clipping in the walk.

The back pelt keeps its thickness and receives geometric contact-fold shape keys
through the sourced fall. These are modelled folds, not a simulated cloth cache.
Audit the actual evaluated terminal meshes as well as rig transforms before
holding the last death frame. Source projection must exclude cream base pixels
from boot/skin toe UVs. Quiver vanes use ivory pigment on both sides so unseen
feathers do not become dark sticks. Finish and freeze geometry before projection;
rebuild every clip and render after any master change.

`ROUND=2 tools/art/anim3d/units/barbarian-archer/gpu.sh` remains the complete
argument-free host pass: Metal Cycles512/64, all stage/clip/foot reviews, current
512/256 masters, trimmed160 atlas at quality>=75 and <=200000 bytes, validation,
and decoded five-clip eight-second H.264/yuv420p movie. CPU256 previews do not
replace the archived GPU512 evidence or establish a new GPU result. No art PASS
is created by technical checks.
