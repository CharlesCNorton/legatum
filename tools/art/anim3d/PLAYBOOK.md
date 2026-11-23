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

### Tagmatic GPU follow-up: sourced motion and reproducible rebuild

The round-one GPU pass was successful (182,516 bytes, Q75), but consumed an
external master ahead of the checked-in build scripts. The recovered unit-owned
round-two changes now reproduce finished-surface projection and the rest grade.
The stone has a thicker bevelled rim, normal-driven side shading, measured warmer
pigment and live AO; the visible calf has a fuller fitted boot.

Use proven open motion as the default for human units: this lane now uses the
CC0 Quaternius Universal Animation Library Standard's Idle_Loop, Walk_Loop,
Hit_Chest and Death01. `retarget.py` samples Blender world-space rotation
constraints with full reference matrices and bone-roll compensation. Locomotion
legs use the anatomical calibration rather than the painting's braced stance;
boots map their flat neutral soles to the source T-pose. Aligning foot-bone axes
alone pitches the fitted soles down. Never patch foot rotation after retargeting.
The spear-carrying arm has a clearance constraint; only attack and released
props are authored. Death blends out of the guard before following the sourced
fall. Vertical root contact uses evaluated geometry; cloth is still modelled
folds with contact shape keys, not simulation.

Render `render.sh g` each round. `tagmatic-soldier-g-feet-check.png` shows all eight
move samples from top and front; the geometry audit records sole heights and
forward yaw. Inspect travel direction, contact and slide in motion; a bounds or
alpha pass cannot certify foot planting. Source action names, samples, licence
and hashes are stored in clip metadata and the unit's `SOURCES.md` and lockfile.

The no-argument `gpu.sh` now rebuilds from pinned inputs and includes the g stage
in its GPU512/48 master gate (64 review images at both 512 and 256). It creates
the trimmed 160 atlas, validates exact alpha/offset reconstruction and held death,
encodes the trim-aware round MP4, verifies ffprobe output, and writes a receipt
with `art_approved: false`. It never creates PASS automatically. Inspect the
GPU result at 256 and 64 before art approval.


### Tagmatic round 3: grip depth, stone pigment and released equipment

The round-2 GPU pass completed at 187,990 bytes/Q75; its visual critique exposed
plain limestone and a disconnected-looking death. A matched 2D grip had hidden
a roughly 14 cm depth gap. Fit the real wrist along the camera depth axis before
building sleeves or freezing UVs, then audit palm-to-shaft distance in every held
sample. Painting alignment alone cannot certify a physical grip.

The stone now projects a registered generated clean plate on its full-depth
bevelled disc. `stone-fill.prompt.txt` and `assets.lock.json` pin the source edit;
the generated top removes the soldier and shadows, the original unobscured lower
rim retains its exact pigment. Live AO supplies new contacts. This texture never
cuts the silhouette or replaces geometry. One automatic hashed rest grade still
applies to all clips. Standard/None preserves existing painted illumination.

The shield has a leather back material, solid bevelled enarmes, rivets and buckles.
All belong to the same rigid release assembly. Continuous MPFB under-clothing
keeps exposed bent sleeve/trouser joints from reverting to skin. Death carries
props through the initial loss of balance, then releases from their actual held
poses. Interpolate the assembly centre and quaternion separately; interpolating
world transform translations can create an unwanted orbital arc. Use actual
mesh vertices for ground clearance: a rotated bounding box can spuriously lift
a thin shield above the stone. This remains an authored equipment landing and
modelled cloth contact, not a rigid-body or cloth simulation.

`gpu.sh` defaults to ROUND=3 and rebuilds everything from the pinned inputs. It
retains GPU512/48 and 256 masters, all interim sheets, feet diagnostics, trimmed
160 atlas, alpha/offset/motion validation and the eight-second trim-aware MP4.
A technical receipt leaves art_approved false; only visual review can create PASS.
