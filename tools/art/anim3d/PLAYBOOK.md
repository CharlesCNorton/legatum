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

## Infantry / arquebusier round 1

This unit uses `tools/art/anim3d/units/arquebusier/` and external
`$ANIM_ROOT/masters/arquebusier/`. It retains MPFB 2.0.18 anatomy and its 53-bone
`game_engine` rig, with original slashed doublet, puffed breeches, stockings,
latchet shoes, a swept-brim morion, ten brass-collared powder flasks and a matchlock.
The cloth is modeled with longitudinal folds and thickness; hard kit has rounded
edges, separate brass fittings and a real raised helmet comb. No relief planes
or primitive replacement anatomy are used. The five clips are authored rig keys.

The standard quality method is (1) frozen rest-camera projection of the original
painting onto actual mesh UVs, blended with facing and source alpha, with generated
painted fills for hidden surfaces; (2) real thickness, folds, bevels and fittings;
(3) warm upper-left product key, soft fill, cooler rim and contact shadows; and
(4) a bounded grade measured from source/render opaque-pixel statistics. The grade
is fixed from the rest frame for every clip, avoiding per-frame colour pumping.
Projection contains painted illumination and cannot repair a mismatched silhouette.
Compare painting/render/50-percent crossfade at 256 and 64 px in
`arquebusier-f-restpose-compare.png`; the target remains near-indistinguishability.

The base target is lit sRGB **#E9CFA0**, with a darker warm rim. The unit's shared
stone material is `MAT-cream limestone E9CFA0` (linear pigment `.95,.70,.32` under
its AgX setup); compare the rendered pixels, not the shader triplet. `bake.py`
produces six actual 256 px Cycles AO/Pointiness maps for doublet, helmet and stock,
retaining the maps in the master and external textures folder. The six installed
Blender skills govern anatomy/geometry, Principled materials, lighting, camera,
editable keys and render verification. No optional absent calibration skill is needed.

Run sequentially from the repository root:

```sh
tools/art/anim3d/units/arquebusier/render.sh build
tools/art/anim3d/units/arquebusier/render.sh bake
tools/art/anim3d/units/arquebusier/render.sh c
tools/art/anim3d/units/arquebusier/render.sh animate
tools/art/anim3d/units/arquebusier/render.sh preview
tools/art/anim3d/units/arquebusier/render.sh pack
```

Every Blender invocation is plain `blender -b --disable-autoexec`, using the PATH
machine gate. CPU previews use Cycles; never bypass the gate or invoke an app binary.
No effect is scaled to zero: muzzle flash and smoke have actual geometry and keyed
render visibility. The single lead-side GPU command is:

```sh
ROUND=1 tools/art/anim3d/units/arquebusier/gpu.sh
```

It requires a Metal Cycles device, renders all stages at 512 px, retains graded
512 and 256 sets, regenerates reviews/strips/WebPs and the rest comparison, packs
and validates the atlas, then writes `arquebusier-round${ROUND}.mp4`: five clips,
2x scale on cream, eight seconds, H.264 yuv420p. GPU device absence fails explicitly.
CPU renders are labeled in manifests; a technical validation is not art approval.

### Arquebusier trimmed atlas format (version 2)

The atlas has five logical rows in idle/move/attack/hit/death order. Cells before
trimming are 160 x 160; all 8/8/10/4/10 frames remain. `frame` records `w,h,ax,ay`.
Each clip retains `row,frames,fps,loop` and adds `rects`, one per frame:
`{x,y,w,h,ox,oy}`. `x,y,w,h` address the stored trimmed rectangle; `ox,oy` place it
back in its original 160 px cell. Draw its destination at
`anchor - (ax,ay) + (ox,oy)` times the display scale. Rows have variable physical
heights, so consumers must use rectangles, never infer pixels from `row*160`.
The existing game runtime is unchanged; it must support version 2 before activation.
Packing keeps lossless 8-bit alpha, chooses RGB quality 90/85/80/75 and refuses
anything over 200,000 bytes. No frame removal or lower quality fallback is allowed.
Validation checks source hashes, counts, offsets, alpha, cell margins, motion,
terminal death hold and size/quality. Masters are never committed. Only write a
PASS marker after visual comparison and clean motion establish the full art bar.


### Arquebusier resumed round 2: finished surfaces and painted light

`units/arquebusier/refine.py` starts from the preserved external
`refinement-input.blend` (seeded from round one's plain checkpoint). Repeat runs
never accumulate fitting. It freezes MPFB macro shape keys while retaining the
19,158 native vertices and skin weights, converts solid curve details to meshes,
and applies rigid bevel/thickness before camera projection. Long kit edges get
interior samples for visibility tests: endpoint-only samples on a barrel can
reject its whole visible middle when one endpoint is behind a hand.

The rest fit edits actual mesh coordinates at measured screen landmarks, keeping
depth and articulation. Native anatomy uses inverse blended skin transforms;
rigid kit uses its parent/object matrix. Footwear moves along camera rays back
onto the ground after fitting. The camera remains fixed; this is a local geometry
fit with recorded controls, not a claim of an exact viewpoint. The rounded stone
is moved back on the ground to fit the source ellipse and remains stationary.

Projection now combines frozen UVs with source alpha, facing and ray visibility.
Camera rays receive 98 percent of the painting's existing illumination; other
rays and unseen areas keep physical materials and the original generated fills.
Standard/None is intentional for this painted pigment, avoiding a second AgX
compression. Physical product lights retain their ratios at reduced energy.
The stone has its own warm camera pigment, real grain and live contact AO; the
figure painting is never projected onto it. Actual AO/Pointiness maps are rebaked.
One bounded monotone RGB quantile grade is fitted at rest and frozen for all clips.

The attack uses a rigid gun transform and solves both arms toward the trigger and
fore-end while raising/regripping. Death folds the legs, turns the fall within the
cell and settles the evaluated figure against the actual offset stone footprint.
Smoke is a bounded volume with radial density, not an opaque sphere. These changes
still require visual review; the matrix audit is not a full collision solver.

CPU iteration, sequentially:

```sh
for stage in refine project bake b c animate preview pack; do
  tools/art/anim3d/units/arquebusier/render.sh "$stage"
done
```

The executable `ROUND=2 tools/art/anim3d/units/arquebusier/gpu.sh` regenerates clips,
audits geometry, renders all stages at GPU512/64 samples, retains 512/256 masters,
checks actual blend hashes and device provenance, packs/validates and writes the
8-second five-clip MP4. It retains a transcript, failed-stage status and a success
receipt; none means visual PASS. Missing-input and CPU-provenance rejection are
checked locally; the sandbox cannot verify Metal rendering.

Packing now downsamples premultiplied RGBA with bicubic filtering, retaining all
8-bit alpha values. Identical frames within a row share one rectangle, including
the final death hold. Independent validation reconstructs alpha from every source
frame, verifies the atlas/grade hashes and exact decoded death hold. The 160 px
logical frame, per-frame offsets, five logical rows, frame counts, Q75 floor and
200,000-byte cap are unchanged. Three delivery tests cover monotone grades, alpha
preservation, premultiplied edge colour and WebP trim reconstruction.


### Arquebusier driver round 2: bind depth and open motion

The actual round-one GPU pass succeeded at 512 px, 64 samples, 191,478 bytes/Q90.
Its evidence is preserved externally in `masters/arquebusier/driver-round1-gpu/`.
The technical pass did not meet painting parity. Stock faces had inward normals,
rejecting their projected paint. Recalculate winding before projection and after
fitting; the real bevels then retain the painting's wood grain and highlights.

Camera registration must fit depth as well as screen landmarks. Prior footwear
had been displaced behind the skeletal ankles along camera rays; small authored
keys hid that error. Open motion exposed detached shoes. `bind_fit.py` preserves
the native anatomy and painted rest view, relocates disc and shoes together along
camera rays, connects stocking surfaces in depth, bakes the fitted rest pose and
calibrates ankle/toe bind joints before retargeting. Flush the dependency graph
before reading matrix_world after location/scale fitting, or the old matrix can
silently undo the stone placement. Thick folded knee panels
blend thigh/calf weights across the joint. Closed leg clothing masks its
covered anatomical mesh while retaining all 19,158 original vertices and weights.

The human motion default is now open motion: Quaternius Universal Animation
Library Standard (CC0), with pinned input hashes and provenance in the unit's
`SOURCES.md` and external `assets/SOURCES.md`. Idle_Loop, Walk_Loop, Hit_Chest and
Death01 are retargeted with Blender world rotation constraints, calibrated rest
matrices and bone rolls. The carry arms use the source idle through NLA; only the
weapon attack remains authored. No post-retarget foot orientation edits are made.
Small root translations match the sampled stance toes to one virtual ground speed.

Every round renders actual top/front footwear over all eight move samples to
`arquebusier-g-feet-check.png`. The supporting evidence records foot yaw, virtual
stance error, source clip hash and CPU/GPU provenance. Bone-only metrics can pass
with badly bound footwear; the geometry audit now also measures each ankle
against the actual shoe surface in every clip. Inspect the rendered shoe/stocking
connection too.
The GPU handoff includes this stage and rejects stale or CPU-only foot evidence.
The fixed rest histogram grade, image-generated hidden fills, genuine bevels and
cloth folds, product lighting and 160 px/Q75/200,000-byte delivery contract remain.

### Arquebusier driver round 3: moving seams and clean stone

The actual round-two GPU pass completed at 512 px/64 samples with all 40 frames,
182,788 bytes at Q85. It was technically valid but still showed a pointed bright
morion brim, broad footwear, dark exposed fills and open sleeve seams in action.
Original evidence is preserved under `masters/arquebusier/driver-r2-gpu/`.

`round3.py` finishes the calibrated rest geometry before projection. Small measured
screen corrections retain the helmet/stocking/shoe depth. The existing sleeves
become skin-weighted across elbows and shoulders; thick folded elbow linings
bridge their interiors. Their rest surfaces remain in place, while joint weights
blend through motion. Generated hidden cloth/leather fills receive a restrained
camera pigment layer with live contact AO, retaining physical BSDFs and weave.
Do not compensate a black unprojected seam by grading the entire painted figure.

The clean stone occlusion plate is original ImageGen output in the external asset
folder. Alpha bounds register its pigment onto the actual rounded disc. It never
provides opacity or geometry, and fresh AO supplies moving contact shadows. The
source painting, original generated fabric fills and clean stone are SHA256-pinned
in `inputs.json`; `prepare.py` checks them before preparing maps. The fixed rest
histogram grade remains shared by all frames. Camera registration remains measured
and approximate; the matched pigment is not evidence of an exact camera solve.

Clear imported pose transforms before assigning sparse glTF actions; otherwise
channels absent from an action can retain an unrelated imported pose. The open
Quaternius motion, rest/roll mapping and foot rotations remain intact. Inspect
actual top/front shoes and cloth as well as the numerical stance check.

Run the sequential CPU stages documented above, then the lead runs:

```sh
ROUND=3 tools/art/anim3d/units/arquebusier/gpu.sh
```

The same 512/256 masters, 160px trimmed atlas, Q75 floor, 200,000-byte cap,
provenance/geometry/alpha validation and eight-second five-clip movie are required.
Successful checks still do not establish painting parity or authorize a PASS file.

The round-three top view exposed a gap in the earlier foot check: a forward bone
axis did not prove that its fitted shoe pointed forward. Bind calibration now
measures heel/toe vertex landmarks on the actual shoe and aligns the ankle/toe
bind axis before retargeting, preserving the painted rest silhouette. The foot
review and GPU gate also check the actual shoe direction (20-degree limit).
No sampled foot rotation is edited. Thin rounded leather soles and flattened
undersides replace point-contact ellipsoids; ground placement includes the soles.
Generated stone edge alpha blends pigment over cream and never cuts opacity.
