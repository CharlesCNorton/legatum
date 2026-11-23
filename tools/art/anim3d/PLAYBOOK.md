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

## Infantry / scout — round 1

The scout's isolated scripts are in `units/scout/`. Reuse the MPFB installation and
`env.sh`; the scout adds no external model or motion dependency. Its MPFB body and
53-bone game-engine rig wear original thick folded linen, a shoulder cowl and olive
cloak, stitched leather straps/satchel, real buckles, sandals, curls/beard and a forked
walking staff. The cape uses authored secondary shape keys, **not a claimed cloth
simulation**. All five actions are authored on the anatomical rig. Masters and all
raw render sequences remain under `~/LegatumRuns/anim-pilot/masters/scout/`.

The six Blender skills informed rounded edges and overlapping joins; dielectric
cloth/leather and metallic brass; a warm upper-left key, soft fill and cool rim;
orthographic painting-camera registration; eased skeletal keys and cape follow-through;
and denoised transparent image sequences. Every invocation is plain `blender -b
--disable-autoexec` through the installed PATH gate, with three CPU threads and no
nested Blender process. Do not call the application binary or add another heavy process.

### Scout quality method

The standing four quality levers are the standard: align the real rest geometry and
camera, project the painting as **fixed UV colour on that geometry**, finish its
bevels/straps/folds, light it as a painted miniature, and apply a measured grade.
Projection never provides mesh transparency or a billboard. Material-specific alpha
masks suppress skin/cloth spill, and facing weights blend into generated painted
linen/wool/leather/skin fills on unseen surfaces. Regional registration boxes are
explicit in `paint.py` and recorded in the master directory. Some lighting remains
baked into this colour; inspect motion-revealed seams. AO and curvature are actually
baked from four meshes and drive cavity colour and roughness. They are 256 px maps.

The base is one stationary cream disc, with the common displayed target **#E9CFA0**
and a darker rim. Its linear shader pigment is `(0.86, 0.65, 0.37)` under AgX/product
lighting; this is not a literal sRGB-to-shader conversion. `review.py` samples opaque
RGB quantiles at rest, bounds the grade, and reuses the same LUT for all clips. It
retains raw images. `scout-f-restpose-compare.png` shows painting, render and 50/50
crossfade at 256 and 64 px. Silhouette and surface mismatches remain visible; a valid
atlas is not art approval. The original painting stays the active game asset.

### Scout build, review and GPU handoff

```sh
UNIT=scout tools/art/anim3d/render.sh prepare
UNIT=scout RENDER_ENGINE=CYCLES CYCLES_DEVICE=CPU SAMPLES=8 tools/art/anim3d/render.sh round
UNIT=scout tools/art/anim3d/render.sh pack
UNIT=scout tools/art/anim3d/render.sh validate
```

`round` serially builds, publishes b, bakes/projects, publishes c/details, saves all
five clip masters, and publishes d and each e strip/WebP immediately. The log and
reviews use `review/3d-v2/scout-*`. The source painting and generated fill atlas must
exist under `assets/scout/`; `inputs.json` records their hashes. The generated fill
prompt is `units/scout/painted-fills.prompt.txt`. To rerender **saved masters** on the
lead's host, then repack and validate:

```sh
UNIT=scout RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64 RESOLUTION=512 tools/art/anim3d/render.sh final
UNIT=scout tools/art/anim3d/render.sh pack
UNIT=scout tools/art/anim3d/render.sh validate
```

`final` starts with c to establish the GPU grade, then details/d/all five clips. Metal
is required explicitly; there is no silent CPU fallback. `RENDER_ENGINE=BLENDER_EEVEE`
is also supported for comparison. Each renderer manifest binds frames to the saved
blend and grade. Changing model/materials requires rebuilding clips; changing grade
requires rerendering every clip. Recheck visual quality after the GPU pass.

### Scout atlas v2: 160 px source canvases, per-frame trim offsets

Keep true 512 px rendered masters and derived 256 px gallery frames; pack all
8/8/10/4/10 samples at **160 px**, WebP quality **90, 85, 80 or 75**, at most
**200,000 bytes**. Packing refuses a larger image instead of reducing quality or
frame counts. No full-size masters enter git.

The extended JSON preserves `frame:{w,h,ax,ay}` and numeric
`clips[name]:{row,frames,fps,loop}`, and adds `formatVersion:2` plus
`trims[name][sample]:{x,y,w,h,ox,oy}`. `x,y,w,h` address the cropped rectangle in the
packed atlas; `ox,oy` restore it in the untrimmed 160×160 canvas. Drawing relative
to the anchor uses `(ox-ax, oy-ay)`. Each clip occupies one packed row, in
idle/move/attack/hit/death order; sample widths and row heights vary, with a 2 px
transparent gutter. `row` is logical order, **not** a fixed-cell addressing formula
for v2. A v1 loader must be extended before activating this candidate; this art lane
does not change runtime loading. Validation reconstructs all 40 frames and writes
`scout-atlas-decoded.png`, checks crop bounds/overlap, alpha, clipping, motion, held
death, source hashes, master sizes and the byte/quality limits.

Scout `audit` is also an explicit stage (`UNIT=scout tools/art/anim3d/render.sh audit`).
It checks all sampled base transforms, MPFB topology/53 bones, nonzero object scale,
hand-to-staff distance, loop endpoint transforms and held death transforms. Body
minimum Z must stay between 0.095 and 0.105; detailed cloth/sandal contact still needs review.

The scout packer quantizes **alpha only** to 32 levels, retaining RGB detail and all
40 samples. This follows the infantry packing approach while enforcing the newer
quality floor. Input source/fill hashes are pinned in `units/scout/assets.lock.json`
and checked by `prepare`. The final frame placement uses evaluated anatomy to keep
body minimum Z at 0.100 above the stone top at 0.095; this is not a full cloth-contact solver.

During death, per-sample corrective shape keys settle the real cloak and hem on
Z 0.108 while retaining shell thickness. This prevents the long cape passing through
the base; it is authored contact deformation rather than a cloth-physics bake.
A targeted motion refresh is `UNIT=scout CLIP=hit tools/art/anim3d/render.sh refresh`
(or another clip name); it updates only that clip, its reviews and the full rig audit.
