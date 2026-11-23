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

## Infantry family: composite archer, round 1

This isolated unit uses `units/composite-archer/` and external
`$ANIM_ROOT/masters/composite-archer/`. It reuses the infantry MPFB anatomy/rig fitting
method, not the spearman kit. The 53-bone CC0 rig wears a red embroidered tunic,
patterned trousers, felt cap, leather boots and quiver. The recurved composite bow,
string, nocked arrow and spare arrows are real geometry. No billboard, relief-plane
figure, account or paid model service is used. Original scripts are MIT; rendered
art and the project painting are CC BY 4.0. Source URLs, generated-fill prompt and
input hashes are recorded in the unit README and external input manifest.

The six installed Blender skills informed thick clothing shells, bevelled hard
edges, fully metallic gilding versus dielectric cloth/skin, a warm upper-left key
with cool rim and soft fill, an orthographic painting camera, editable quaternion
pose keys, and verified PNG sequences. Entry points invoke only plain `blender -b`
on PATH, with `--disable-autoexec`, so the shared machine gate remains authoritative.
The default is Cycles CPU at eight samples. Do not bypass that gate or scale hidden
objects to zero; the arrow uses keyed render visibility.

### Painting and surface standard

The four quality levers from standing feedback apply to this foot-soldier lane:

1. Align the real rest pose/camera, then project the full painting onto frozen mesh
   UVs. An incidence/alpha mask fades to generated painted fills on unseen surfaces.
   Alpha never replaces geometry. Landmark registration is approximate and carries
   painted lighting; inspect the face, hands and seams in motion.
2. Finish geometry: fitted MPFB clothing weights, physical cloth thickness and fold
   displacement, gold piping, leather belt/baldric/buckle/stitches, layered horn bow
   and binding geometry. Eight actual 256px AO/Pointiness maps on four main surfaces
   darken cavities and vary roughness. Inner Solidify faces are disabled only for
   baking to prevent overlapping-UV contamination. No simulated cloth is claimed:
   these fitted cloth shells use skeletal deformation.
3. Light as a painted miniature product shot, with contact shadows on one cream
   disc. The shared visual target is sRGB **#E9CFA0**, with a darker warm rim. Here the
   AgX shader uses linear pigment `(.82,.61,.32)`, roughness `.9`, emission `.12` to
   retain warmth in shade; that is not an sRGB conversion or an exact pixel match.
4. Derive one bounded RGB-quantile LUT from the rest render and painting, then freeze
   it for all frames. Raw images remain unchanged. The grade is recorded by hash.

`composite-archer-f-restpose-compare.png` contains painting, render, half split and
50/50 crossfade at 256 and 64 px. It exposes mismatch rather than proving parity.
Round 1 remains a review candidate: anatomy/pose, hands, face registration and
motion-revealed projection seams need further work. GPU renders and the lead's art
review decide adoption; no runtime registration changes in this lane.

### Rebuild, interim reviews and GPU handoff

Run sequentially from the repository root:

```sh
UNIT=composite-archer tools/art/anim3d/render.sh prepare
UNIT=composite-archer tools/art/anim3d/render.sh build
UNIT=composite-archer tools/art/anim3d/render.sh refine
UNIT=composite-archer tools/art/anim3d/render.sh paint
UNIT=composite-archer tools/art/anim3d/render.sh round
UNIT=composite-archer tools/art/anim3d/render.sh audit
```

`prepare` requires the two original external images in `assets/composite-archer/`;
`inputs.json` pins them. Build/paint invalidate the source hashes of old clips.
`round` renders rest, authors all five clip masters and renders each sequentially.
It posts b-plain, c-textured-lit, c-details, d-rig-poses and each e-clip strip/WebP
under `review/3d-v2/composite-archer-*` as each stage exists. The running log and any
unit-specific feedback live there too. Idle breathes; move is a guarded crouching
advance; attack draws/releases/recovers; hit recoils; death folds and settles with a
released bow and a two-frame terminal hold. These are original keys, not CMU motion.

The lead rerenders the **saved** masters, without rebuilding materials or poses:

```sh
UNIT=composite-archer RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64 \
  RESOLUTION=512 tools/art/anim3d/render.sh final
```

This explicitly requires Metal and fails instead of silently falling back to CPU.
`final` renders rest first, all clips, audits saved geometry and repacks/validates.
For targeted review use `c`, `d`, `e-idle`, `e-move`, `e-attack`, `e-hit`, `e-death`;
`pack` and `validate` do not launch Blender. After a changed rest grade rerender all
clips. Keep the 512px raw/graded frames and 256px gallery set outside git.

### Trimmed 160px atlas extension (formatVersion 2)

The candidate `app/src/assets/units/anim/composite-archer.{webp,json}` retains the
five clip rows in idle/move/attack/hit/death order and lengths **8/8/10/4/10**.
`frame` is `{w:160,h:160,ax:79.375,ay:138.125}` in the common untrimmed frame coordinates.
`clips[name]` retains `{row,frames,fps,loop}` with numeric frame counts. The new
`frames[name][index]` gives `{x,y,w,h,ox,oy}`: packed atlas rectangle plus its top-left
offset inside the original 160px square. Draw the crop at `(ox-ax, oy-ay)` relative
to the unit anchor. Rectangles have two pixels of transparent padding; row heights
and packed x positions vary. `atlas` stores actual decoded dimensions. Consumers
must honor the rectangles/offsets for version 2; do not interpret this as the old
fixed grid. Runtime support is a separate integration task, not silently supplied
by this art-only candidate.

All 40 frames remain. Alpha remains lossless 8-bit after premultiplied bicubic reduction. WebP quality searches
90/85/80/75 and must stay at least 75 and at most 200,000 bytes; failure is reported,
never hidden by dropping frames or lowering quality. The pack report binds raw
frames, clip/master and grade hashes. Validation checks transparent bounds, original
512/256 sets, native margins, actual motion, held death and trim reconstruction.
The geometry audit checks MPFB topology, finite/nonzero scales, stationary base,
source hashes and held terminal bones. It is not a full body/equipment collision
solver or art approval.

### Round 2: geometry registration and complete GPU delivery

`refine.py` starts from the unchanged `plain.blend` checkpoint. It freezes current
MPFB morphs, fits actual full-depth anatomy and kit in the rest camera, inverts
weighted bone transforms to preserve articulation, and finishes rigid modifiers
before painting. The original body vertex count and 53-bone skeleton remain.
The tunic skirt and its real stitched hem share the same additional flare.
The painting now uses one frozen camera mapping without the prior local UV warp.
Occlusion and head-region masks prevent the drawing hand remaining painted on the
cheek after release. Copy evaluated vertex data before ray queries: refreshing the
dependency graph while holding an evaluated vertex reference invalidates it.

Camera-only pigment preserves the painting's illumination, with physical materials
on non-camera rays and existing generated fills on unseen surfaces. Standard/None
avoids applying AgX compression to that pigment a second time; the existing product
lights are reduced accordingly. The physical stone retains contact shadows and a
calibrated camera pigment for its cream top and warmer rim. The single automatic
rest histogram grade stays frozen across all clips. This is not an exact camera
match or art approval; the base ellipse and contact still need visual scrutiny.

The complete no-argument host entry point is
`ROUND=2 tools/art/anim3d/units/composite-archer/gpu.sh` (the driver supplies ROUND).
It retains its own transcript, rebuilds all clips from the saved current master,
renders plain/rest/details/poses/all clips at Cycles GPU / 64 samples / 512 px, exports native 512 px
and gallery 256 px images, audits geometry, packs and validates, and encodes all five
decoded clips at 2x on cream for eight seconds. Missing inputs and CPU provenance
are rejected; a receipt is written only after the GPU master and video checks pass.
The MP4 is H.264/yuv420p, 1600x348, 240 frames. The script never writes art PASS.

Native 256 px CPU previews no longer manufacture 512 px masters. Trim anchors retain the
fractional scaling of 127/221, and duplicate terminal death images share a rectangle
so lossy encoding cannot introduce hold flicker. Validation compares reconstructed
alpha byte-for-byte against the source, verifies current clip/master/grade
hashes and requires an identical decoded death hold. Original 40 frame counts,
Q75 floor and 200,000-byte cap remain. Round1 evidence is in `round1-backup`.

Low anatomical/boot vertices are seated along their camera rays onto the stone,
retaining the registered silhouette. After authored leg poses, foot bones receive
small corrections from the evaluated sole minimum inside the disc footprint;
airborne feet retain their lift. The audit independently measures boot clearance
against the .085m stone top with a .012m penetration tolerance. It still does not
prove full cloth/body collision freedom or anatomical realism. The shortened
attack recovery avoids the deepest sleeve deformation; revealed jaw surfaces use
a warm, AO-shaded camera pigment instead of retaining the painted drawing hand.

Apply the full floor constraint during death rather than blending it by fall
progress: a partial constraint left an early-frame boot inside the stone. Keep
the original contact tolerance and fix the motion when that audit fails.

Round-2 CPU delivery: all 40 samples at 512px / Cycles CPU8, with 256px gallery
copies; **178,220 bytes at Q80**, lossless 8-bit alpha and premultiplied bicubic
reduction. Q85 was 201,936 bytes. Atlas reconstruction/alpha/hold validation,
geometry/contact audit, Python/Bash syntax and working-tree hygiene pass. MP4:
H.264/yuv420p, 1600x348, 240 frames/eight seconds. CPU evidence is archived in
`round2-cpu`. Silhouette IoU improves from .7370 to .7934, but face/hand anatomy,
base perspective and motion-revealed face/boot surfaces remain visibly different.
No art PASS; the actual GPU512/64 host render and visual acceptance remain pending.
