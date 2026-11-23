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

## Infantry: barbarian-crossbowman round 1

Unit-specific entry points are under `units/barbarian-crossbowman/`. This chapter
extends the spearman infantry method without changing its scripts. The brigand
uses CC0 MPFB anatomy and the 53-bone `game_engine` skeleton, with original hood,
quilted gambeson, olive trousers, boots, belt buckle, bolt case and a rigid
crossbow. The bow has separate steel prod, walnut tiller, string, trigger hardware,
loaded bolt and foot stirrup. The five clips use authored skeletal keys, with a
weapon control and arm IK during the raise/fire; no motion-capture or simulated
cloth claim is made. The last two death samples hold the same settled pose.

Standing feedback 12–21 is the quality bar, including Sam's “still pretty rough”
and “high school student” criticism and the later “huge improvement” verdict.
The four standard quality levers are applied here:

1. Register the rest camera and pose to the painting, then assign fixed camera
   UVs to actual mesh vertices. Painting alpha and surface incidence blend the
   projected brushwork into unseen-side fills; neither image alpha nor camera
   projection changes the geometry silhouette. Generated linen from the mounted
   family's CC BY 4.0 fill sheet supplements unseen wool/linen. Projection cannot
   correct the wrong anatomy, hood opening or pose.
2. Finish the geometry: bevel hard edges, keep real thickness on cloth and straps,
   model the buckle opening and tongue, stitch channels, hood seams and weapon
   hardware, and subdivide the anatomy. `bake.py` creates actual 256px AO and
   curvature maps for skin, gambeson, hood and stock, then uses those maps for
   cavity shading and roughness. Procedural weave and grain remain at finer scale.
3. Light the miniature with an upper-left warm area key, soft fill and cool rim.
   CPU previews use denoised Cycles. Finals explicitly select Metal Cycles GPU
   and fail if it is unavailable. Every invocation is plain `blender -b` through
   the shared PATH gate, with automatic script execution disabled.
4. Fit one monotonic RGB grade from the rest image and painting's foreground
   quantiles and apply that same grade to every clip. Keep raw renders. The
   common stone material target is **#E9CFA0** sRGB; its linear pigment is
   `(0.815, 0.624, 0.352)`, with grain and darker contact shading. Judge displayed
   color after lighting and grade, not merely the shader constants.

`post.py review c` writes the painting/render/50-percent crossfade at native 256
and 64 pixels to `barbarian-crossbowman-f-restpose-compare.png`. It also emits
hood/face, quilt/belt and crossbow close-ups. All stage images and looping WebPs
land immediately in the external review directory, and each stage appends to
the unit log. The first plain review is retained separately. Do not write a PASS
marker until the rest pose is difficult to distinguish and the five clips are
visually clean; the validator's technical PASS does not establish that verdict.

From the repository root, for CPU iterations:

```sh
unit=tools/art/anim3d/units/barbarian-crossbowman
"$unit/render.sh" build
"$unit/render.sh" bake
"$unit/render.sh" animate
STAGE=c "$unit/render.sh" render
~/LegatumRuns/anim-pilot/venv/bin/python "$unit/post.py" review c
```

The complete GPU handoff is the executable, no-argument `gpu.sh` in that unit
directory. `ROUND` is supplied by the overnight driver. It rebuilds, bakes,
animates and renders b/c/d/all five e stages at 512px, creates 256px derivatives,
packs and validates the atlas, audits the editable scenes and creates the
8-second H.264 yuv420p video with all five reconstructed clips at 2x on cream.
Masters stay under `masters/barbarian-crossbowman/`, outside git.

### This unit's trimmed atlas extension

The delivery retains `{frame:{w:160,h:160,ax:80,ay:140}, clips:{...}}`. Each clip
has `row`, `frames`, `fps`, `loop`, and `rects`, one rectangle per frame:
`{x,y,w,h,ox,oy}`. `x/y/w/h` address its packed atlas crop; `ox/oy` restore it to
the original 160px logical frame. Draw at `(anchorX-ax+ox, anchorY-ay+oy)`.
Rows are idle/move/attack/hit/death, with 8/8/10/4/10 frames; physical row heights
vary because empty margins are removed. Readers must use rectangles, not assume
fixed 160px strides. This candidate does not alter or enable the app runtime.
WebP is encoded at quality 90, 85, 80 or 75, refusing delivery above 200,000 bytes.
Model hashes, clip hashes, grade hashes and raw frame hashes reject stale packing.
The validator checks bounds, transparency, motion, all 40 samples and held death;
`video` reconstructs frames using the exact same trim offsets.


### Barbarian crossbowman round 2: registered surfaces and honest delivery

Read the actual prior comparison before rebuilding; the supplied round-one
images and manifests were CPU8/256, not verified GPU output. Prior evidence is
preserved externally under `masters/barbarian-crossbowman/round1-cpu`.

`build.py` freezes the MPFB macro mix; `refine.py` finishes solid/beveled/subdivided
garment and kit surfaces before projection, and fits the hood and boot volumes without
flattening their depth. Boot corrections invert each vertex's blended skin
matrix, preserving native anatomy, weights and the 53-bone rig. The lower camera
and arm poles bring the stance closer to the painting; the stock is lengthened
and the bowstring has a shallower draw triangle. Projection cannot repair a
wrong silhouette, and the pose still needs further art review.

`project.py` records frozen UVs on these finished surfaces. A combined evaluated
scene BVH checks camera visibility; facing and source alpha feather into the
existing image-generated linen and procedural unseen pigments. Cloth behind the
hands excludes their source pixels so fingers are not left painted on the tunic
when the hands move. A camera-ray-only Principled pigment branch retains 97%
of the source's painted illumination where covered; non-camera rays retain the
physical material. Standard/None avoids compressing that illumination again.
This is a view-specific painted surface, not general inverse rendering. Stone
uses its own cream top/rim pigment, live AO and physical response, never painted
feet or static shadows. One rest-derived histogram grade remains fixed for all
five clips; actual AO and curvature are rebaked after geometry changes.

Attack interpolates from the saved wrist and elbow locations, and solves the
weapon grip after recoil moves the torso. The audit limits wrist/stock error
to 2 mm in idle/move/attack. Death settles evaluated body geometry against the
disc footprint and ground rather than only lifting penetrations; its final
samples remain held. This does not constitute a full cloth/body collision solver.

`ROUND=2 tools/art/anim3d/units/barbarian-crossbowman/gpu.sh` is the complete
no-argument host handoff. It resolves this checkout, records the revision and
Blender gate, retains a round transcript and stage/status file, checks Metal
before rebuilding, then builds/bakes/animates/audits and renders every b/c/d/e
stage at GPU64/512. The independent delivery gate verifies all actual 512 masters
and 256 derivatives, source hashes and grade hashes before packing. It validates
the trimmed atlas and probes the decoded-atlas MP4 (H.264/yuv420p, 1600x348,
240 frames/eight seconds). CPU previews cannot satisfy the final-master gate.
Missing GPU logs or CPU-labelled review sheets never establish a successful GPU
pass. Technical completion explicitly leaves visual acceptance pending.

Packing now uses bicubic reduction with full 8-bit alpha and checks exact alpha
reconstruction at each trim offset. Identical logical frames share a rectangle
within their clip row, retaining all 40 playback samples and a pixel-identical
decoded terminal death hold. Atlas/metadata/source/frame/grade hashes are checked
independently. Quality remains at least 75 and size at most 200,000 bytes; no
frame count is reduced. Two regression tests cover semitransparent trim offsets
and stable monotonic grading with unchanged alpha. The runtime is still unwired.

## Infantry chapter: Tagmatic Soldier (round 1)

The unit-owned implementation is `units/tagmatic-soldier/`; run from the repository
root. It uses the installed MPFB 2.0.18 CC0 male anatomy and game_engine skeleton,
with a conical spangenhelm, interlocked mail, fitted gathered sleeves, overlapping
lamellae, leather boots, a genuinely convex thick kite shield and a forged spear.
These are full 3D meshes. No billboard, depth-card animation or source-image warp
is used. This chapter changes no other family's entry points.

Four quality levers are the standard method for this infantry unit:

1. Calibrate the orthographic camera and rest silhouette to the committed token;
   align the original full source by alpha bounds, then freeze its camera-space
   UVs on the actual meshes. UVs travel with the geometry. Ray visibility, facing and source-alpha
   masks blend the painting into generated crimson wool, steel, leather and brass
   fills on back/edge surfaces. The source has baked lighting; this remains a
   view-specific texture and must be checked in motion.
2. Model material thickness, bevel hard edges, retain real MPFB face/fingers,
   gather sleeves and pleat the tunic, add raised shield decoration, armour
   overlaps, mail rings, helmet ribs/rivets, boot seams and a belt buckle.
   `bake.py` creates actual 256 px Cycles AO and Pointiness maps on shield, helmet
   and lamellae. AO controls mild recess darkening and Pointiness controls edge
   roughness. Generated fills supplement, rather than replace, this geometry.
3. Use a warm upper-left area key, soft fill, cool rear rim, contact shadows and
   denoised Cycles final frames. The cream stone is exactly sRGB **#E9CFA0**
   converted to linear BSDF values `(0.81485, 0.62396, 0.35153)`; it is one low
   beveled disc. Colour management and lighting still affect its rendered colour.
4. Fit one foreground histogram grade from the rest comparison and use the same
   17-quantile LUT for every frame. Never fit per-frame grades. Raw renders remain
   alongside the LUT and graded masters. Review painting/render/50% crossfade at
   256 and 64 px in `tagmatic-soldier-f-restpose-compare.png`.

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/tagmatic-soldier/prepare.py
tools/art/anim3d/units/tagmatic-soldier/render.sh build
tools/art/anim3d/units/tagmatic-soldier/render.sh b
tools/art/anim3d/units/tagmatic-soldier/render.sh bake
tools/art/anim3d/units/tagmatic-soldier/render.sh c
tools/art/anim3d/units/tagmatic-soldier/render.sh animate
tools/art/anim3d/units/tagmatic-soldier/render.sh d
for clip in idle move attack hit death; do
  tools/art/anim3d/units/tagmatic-soldier/render.sh "e-$clip"
done
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/tagmatic-soldier/deliver.py pack
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/tagmatic-soldier/deliver.py validate
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/tagmatic-soldier/deliver.py video
```

Every Blender process goes through plain `blender -b --disable-autoexec` on PATH;
that is the machine-wide slot gate. Do not use the old direct application path
or add a second gate around the wrapper. No zero-scale hiding. CPU previews
use 256 px / 8 Cycles samples. Only one heavy stage runs at a time.

The complete lead-side command is executable `units/tagmatic-soldier/gpu.sh`
(no arguments). It uses Cycles Metal, 512 px / 48 samples for **every** b/c/d/e
stage, keeps 512 and 256 masters in `masters/tagmatic-soldier/`, packs and validates
the 160 atlas, and writes all review PNGs, animated WebPs, the rest split-screen
and `tagmatic-soldier-round${ROUND}.mp4`. It refuses a requested GPU pass if no
Metal device is available. Round 2 rebuilds the model, bakes and clips from pinned inputs before rendering. It never writes a PASS marker:
visual approval requires an actual review.

Five clips are authored on the MPFB skeleton: idle 8, move 8, attack 10, hit 4,
death 10. Idle/move include a closure key beyond the sampled loop; death holds
its last two samples. The raised hand keeps the spear's broad leaf visible;
combat uses anticipation and recovery, and death releases both shield and spear.
Round-1 cloth has modeled folds following bones and authored 3D contact shape keys
for the death landing, not a simulated cloth cache. Occluded surfaces use painted
fills so the hidden torso never inherits the shield cross.

### Tagmatic trimmed atlas contract (version 2)

The atlas is transparent WebP, quality **at least 75**, **at most 200,000 bytes**.
`frame: {w:160,h:160,ax:74,ay:142}` describes the untrimmed cell and stationary
stone anchor. `clips` retains `row`, numeric `frames`, `fps`, and `loop`. Its added
`rects` array has one `{x,y,w,h,ox,oy}` object per frame: `x/y/w/h` is the source
rectangle in the packed atlas; `ox/oy` is that rectangle's destination offset in
its original 160-square cell. At an anchor `(X,Y)`, draw the cropped image at
`(X-ax+ox, Y-ay+oy)`, with ordinary display scaling applied to all values.
Rows remain idle/move/attack/hit/death, but have independently trimmed heights
and variable-width frame rectangles. Consumers must use `rects`, not multiply
frame indices by 160. No runtime consumer is enabled by this art candidate.

Packing checks model/clip/render hashes, retains all 40 frames and full alpha,
and refuses oversized output at quality 75. Validation reconstructs each cell,
checks bounds, alpha, motion and the held death. The MP4 uses that same trim-aware
reconstruction: five clips side by side, 2x on cream, 8 seconds, H.264 yuv420p.
Technical validation does not establish painting parity or collision-free motion.


### Tagmatic round 2: finished projection and stable clip entry

Apply the rigid kit's solidify/bevel modifiers before computing frozen UVs.
Otherwise the rendered surface shifts away from the source even when cage UVs
are correct. Triangulate/subdivide the raised cross and seat every sample on
the evaluated convex shield; endpoints alone cut through the dome. Keep the
original full-volume shield, rim and ornament, MPFB anatomy and bone parenting.

Painted source illumination is a 97-percent camera-ray-only pigment layer where
source alpha, facing and visibility allow it. Other rays and unseen surfaces
retain physical materials and the recorded generated cloth/steel/leather/brass
fills. Standard/None avoids compressing the source a second time. Real AO and
Pointiness maps remain on the physical branch. Refit one hashed automatic rest
grade after any such change, never one per frame. The stone has its own fine
cream pigment and live contact AO, no projected feet or static source shadows.

A compact anatomical palm and folded thumb fix the stray finger beside the
shaft; equipment is attached after the palm adjustment so the spear keeps its
full dimensions. Attack now extends farther forward and down. Read elbow and
knee poles from the actual neutral rig to avoid a pose pop at clip entry; death
interpolates these toward its landing poles. This remains authored motion and
bone-attached folded cloth, not simulated cloth or a full collision solution.

The sole no-argument GPU entry point remains
`tools/art/anim3d/units/tagmatic-soldier/gpu.sh`, now defaulting to ROUND=2.
It preflights Metal, rebuilds/bakes/animates/audits, renders every stage at
GPU512/48, verifies every 512/256 export against the current scene and grade,
packs/validates the trimmed 160 atlas and probes the eight-second decoded MP4.
It retains a transcript and explicit failure stage. Its round receipt sets
`art_approved: false`; technical success never creates the visual PASS marker.

Identical crops within each Tagmatic clip share a rectangle, retaining all forty
playback entries and their original offsets. The held death must be byte-identical
in both the lossless source frames and decoded atlas cells.
