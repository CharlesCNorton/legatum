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

## Infantry chapter: Medjay

This unit's scripts are isolated under `tools/art/anim3d/units/medjay/`. The
existing spearman chapter supplies MPFB installation and environment setup;
Medjay uses its own 53-bone MPFB body and original kit, not hoplite armour.
The reference has a bare torso, pleated ivory kilt, feathered headband, long
bronze-tipped spear and round-topped oxhide shield. All are true 3D surfaces.
Masters, source painting, generated fill textures and bakes remain outside git
under `ANIM_ROOT/assets/medjay` and `ANIM_ROOT/masters/medjay`.

### Standard finish and review method

Apply all four quality levers together: align the rest camera and geometry to
the painting, project the original painting as fixed UV colour on the actual
skinned surfaces, finish geometry with physical thickness/rounded edges/folds,
and light as a painted miniature with a warm upper-left key, cool rim and soft
fill. Camera projection is the standard method, not a flat subject card.
Normal-incidence and source-alpha masks blend into the existing generated painted
skin, linen, hide and wood fills on unseen sides. Eight actual geometry AO and
Pointiness bake pairs supply cavity shading and roughness variation, including
the solid headband and anatomical eyes. The camera-only painted pigment retains the source's
illumination at 96% confidence; non-camera rays use the physical material.
Standard/None prevents a second display rolloff of that already painted light.
This is specific to projected illustration, not a general photographic preset.
The orthographic view is calibrated approximately; silhouette differences remain.

The single stationary cream stone disc targets **sRGB #E9CFA0** with a darker
rim and fine grain. The physical shader is tuned against rendered pixels, not
only an albedo swatch. Its top remains at .085 m while the thinner underside and
slightly smaller radius better fit the painting. No painted figure or feet are
projected onto the base. A 17-quantile foreground RGB transfer is calibrated at
rest, bounded to 24 levels/channel and frozen for all clips; alpha is retained.
Raw frames remain ungraded. Never histogram-fit each frame independently.
`medjay-f-restpose-compare.png` includes the painting, 3D, a half split and
50/50 crossfade at 256 px with 64 px checks. File creation is not art approval.

All six installed Blender skills inform the pipeline: organic subdivision and
bevels; dielectric cloth/skin versus bronze; aimed key/fill/rim; orthographic
reference framing; clamped skeletal keys; Cycles previews and image-sequence
verification. All Blender calls are plain `blender -b --disable-autoexec` through
the machine-wide gate. Never bypass PATH or launch concurrent heavy processes.

```sh
tools/art/anim3d/units/medjay/render.sh build
SAMPLES=8 tools/art/anim3d/units/medjay/render.sh b
tools/art/anim3d/units/medjay/render.sh finish
SAMPLES=8 tools/art/anim3d/units/medjay/render.sh c
tools/art/anim3d/units/medjay/render.sh animate
for stage in c-details d e-idle e-move e-attack e-hit e-death; do
  SAMPLES=8 tools/art/anim3d/units/medjay/render.sh "$stage"
done
```

The five authored actions are idle 8, move 8, attack 10, hit 4 and death 10.
Idle/move have an extra keyed seam pose beyond the exported range. Death releases the spear and shield, curls the legs with world-space IK and ends
with a held pose. Motion is authored on the MPFB skeleton; it is not represented
as motion capture. Kit follows hands, forearm, head and pelvis. The kilt has
modeled folds and thickness; it is not a cloth simulation.

### GPU handoff and atlas extension

Run from the repo root, no arguments:

```sh
ROUND=1 tools/art/anim3d/units/medjay/gpu.sh
```

This serial script selects Cycles Metal explicitly, refuses CPU fallback, renders
every stage and all five clips at 512 px, retains 512/256 masters, writes all
review images/WebPs, packs and validates the candidate, audits the rig and writes
`medjay-round${ROUND}.mp4`. The video reconstructs trimmed frames, shows all five
clips side by side at 2x on cream, and verifies 240 frames of H.264 yuv420p (8 s).
GPU results still need visual review. The script never writes a PASS marker.

Medjay uses the **version 2 trimmed-rows format**. `frame:{w:160,h:160,ax:84,ay:141}`
defines the original logical frame and stationary anchor. `clips` retains
`row,frames,fps,loop`; each clip also has `rects`, one entry per frame with
`{x,y,w,h,ox,oy}`. `(x,y,w,h)` locates a cropped rectangle in the WebP; paste it
at `(ox,oy)` in a transparent 160px logical frame before drawing at `(ax,ay)`.
Physical atlas rows have variable heights and widths; never derive pixel
coordinates from `row*160` or frame index. Two-pixel gutters separate crops.
Quality tries 90/85/80/75, never below 75, and refuses >200,000 bytes. No frames
are dropped. Blend hashes, source-frame hashes and the frozen grade bind the
pack report to its source renders. The candidate is not wired into the runtime.

### Medjay round-two findings

Read the actual prior provenance: the supplied round-one output was CPU512/6,
not verified GPU output. The original masters, all frames and reviews are
preserved in `masters/medjay/round1-cpu/`. The unit-specific feedback file was
absent; common feedback 1-22 was read in full.

`register.py` fits the actual cranial vault, calves and toes in the fixed rest
view through inverse skin transforms, retaining depth and the native weights.
The tilted head is upright, the feather narrower, and the three headband tubes
are replaced by a solid woven ribbon. The taller kilt closes a real waist gap;
its matching anatomical coverage mask prevents skin showing through opaque cloth.
The original 19,158-vertex MPFB cage is retained in the plain master. Registration freezes macro morphs; `finish.py` applies smoothing/thickness/bevels
before UV calibration;
the finished body's subdivision interpolates the native weights. It does not
retain the original vertex count. The old coverage-only `refine.py` was removed
because it could not safely transfer indices between these two topologies.

Camera-only paint avoids double illumination and emission spill. Hidden surfaces
retain the recorded image-generated fills, real AO/curvature and product lights.
The audit verifies the finished UVs within .05 token pixels and exact rest entry
for attack/hit/death, as well as the rig, stationary base and nonzero scales.
Move compensates planted targets for root bob. These checks are not a full
collision solver or an art PASS.

The trimmed atlas now uses bicubic reduction with full 8-bit alpha, verified
byte-for-byte after reconstruction. Identical samples reuse a rectangle, keeping
the final death hold identical after lossy RGB encoding. Validation rejects
stale retained 512/256 masters and mixed rest/clip render settings. A CPU preview
is labelled explicitly; GPU delivery requires all nine stages at GPU512/64+.

The executable `gpu.sh` defaults to ROUND=2, keeps a direct round log and failure
status, removes its stale receipt before work, then renders every stage, verifies
GPU provenance and retained masters, audits, packs, validates and encodes the
five-clip MP4. Only successful completion writes a technical receipt with
`art_approved:false`. Missing inputs and CPU-labelled renders are tested rejection
paths. The sandbox has no Metal, so the host's GPU run remains required.

Round-two CPU verification: all 40 frames retained at 512 and 256 px, Cycles
CPU8; trimmed 160 px WebP **157,968 bytes at quality 90**, full lossless alpha.
Atlas reconstruction, identical decoded death hold, current render/grade/master
hashes, rig/finished-UV/combat-entry audit, Python/Bash syntax and whitespace
checks pass. MP4 verified H.264/yuv420p, 1600 x 348, 30 fps, 240 frames, 8 seconds.
Silhouette alpha IoU improves from .776736 to .802003. The painting remains
visibly different; **no art PASS and no verified GPU render**.
