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

## Vehicles / aircraft — biplane (`biplane`)

This aircraft chapter is unit-isolated in `tools/art/anim3d/units/biplane/`; it reuses
`env.sh`, the Vehicles frozen-camera UV / partial-emission method, and the installed
Blender/Pillow environment. Read the Vehicles family chapter on
`astra/unit-anim-3d-vehicles` for the tank-specific build. Biplane uses no MPFB body:
its model, cockpit, hollow cowling, rotary engine, cambered wings, rib seams, struts,
landing gear, propeller and cream support are original volumetric geometry. The
painting's airborne display composition stays intact at rest. Only the base is
stationary through every clip; the support is hidden during the crash.

### Required finish method

1. Match the painting's camera and rest silhouette first. Freeze camera UVs on real
   mesh surfaces and project the archived full painting as base colour. Normal and
   ray-cast visibility masks retain hidden-surface fills. Biplane uses generated
   painted linen, olive, wood and rubber fills, recorded in the external SOURCES.md.
   Projection follows articulated geometry; it is not a painted subject plane.
2. Finish the geometry: cambered closed wing volumes, beveled metal/wood edges,
   open cockpit and cowling, real seams/rivets, padded seat, distinct tyre/disc/hub.
   Four major meshes carry actual 256 px Cycles AO and Pointiness emission bakes.
   AO modulates cavities and curvature modulates roughness; exposed metal parts
   provide edge glints separately from dielectric paint and doped fabric.
3. Use a warm upper-left area key, soft fill, cool rim, contact shadows and GPU
   Cycles denoising for finals. The stone pigment is sRGB **#E9CFA0 converted to
   linear**, roughness .86, with a bevel and fine grain. Judge rendered pixels;
   sharing a shader value alone does not establish source matching.
4. Derive one bounded per-channel 10/50/90-percentile grade from the rest image
   against the painting. Freeze it for every clip, preserve alpha and raw renders.
   Compare painting / render / 50–50 crossfade in
   `biplane-f-restpose-compare.png`, at native 256 and 64 px. This round remains a
   candidate until silhouettes, surfaces and all clips meet the painting.

### Rebuild and previews

Run from the repository root; source and generated fills are external in
`$ANIM_ROOT/assets/biplane/`, with input hashes in `masters/biplane/inputs.json`.

```sh
source tools/art/anim3d/env.sh
PY="$ANIM_ROOT/venv/bin/python"
UNIT=tools/art/anim3d/units/biplane
"$PY" "$UNIT/prepare.py"
"$UNIT/render.sh" build
"$UNIT/render.sh" register
SAMPLES=8 "$UNIT/render.sh" b
"$PY" "$UNIT/review.py" b
"$UNIT/render.sh" paint
SAMPLES=12 "$UNIT/render.sh" c
"$PY" "$UNIT/review.py" c
"$UNIT/render.sh" animate
for stage in d g e-idle e-move e-attack e-hit e-death; do
  RESOLUTION=512 SAMPLES=8 "$UNIT/render.sh" "$stage"
  "$PY" "$UNIT/review.py" "$stage"
done
"$PY" "$UNIT/deliver.py"
"$PY" "$UNIT/check.py"
blender -b --disable-autoexec --python "$UNIT/audit.py"
```

Every Blender call is plain `blender -b --disable-autoexec`; PATH supplies the shared
machine gate. Never bypass it, add a competing heavy process, or zero-scale effects.
CPU previews default to Cycles CPU. The five rigid authored clips are idle hover/bank
8, move 8, attack run 10, hit 4, crash 10. Propeller keys are linear; looping clips
include a hidden closure sample. Combat clips are one-shot; the crash holds its final
two frames. Rebuild/paint invalidates animation hashes; reanimate and rerender before
packing. `deliver.py` rejects stale `.blend` hashes and clipped frames.

### Complete GPU handoff and trimmed atlas format

```sh
ROUND=2 tools/art/anim3d/units/biplane/gpu.sh
```

No arguments. This selects Cycles **GPU / Metal**, fails when no Metal device is
available, renders b/c/d, sixteen top/front gear diagnostic views, and all 40 animation frames at 512 px, retains actual 512
and downsampled 256 masters, writes all review sheets and animated WebPs, packs and
validates the delivery and writes `biplane-round${ROUND}.mp4`: five clips side by
side, 2x scale on cream, 240 frames / 8 seconds, H.264 yuv420p. Masters remain under
`$ANIM_ROOT/masters/biplane/`, outside git. CPU 256 previews are never upscaled and
misrepresented as 512 masters. The handoff verifies current build/asset hashes, preserves the finished model and baked materials, regenerates the five clips, audits them, and records a round log/status/receipt. It fails on missing inputs, mixed settings, stale hashes, or CPU-labelled output. The receipt explicitly leaves visual approval false.

The biplane atlas extends the old grid format with `schema: legatum-trimmed-atlas-v1`.
`frame:{w:160,h:160,ax:73,ay:140}` is the **untrimmed logical cell and anchor**.
`clips` retains idle/move/attack/hit/death order and `{row,frames,fps,loop}`, adding a
`rects` array of `{x,y,w,h,ox,oy}` per frame. `x,y,w,h` locate the trimmed rectangle
in the atlas. Reconstruct it at `(ox,oy)` in a transparent 160×160 cell; draw directly
at `(anchorX-ax+ox, anchorY-ay+oy)` to preserve placement. `row` is the logical clip
row; physical Y and width vary. Do not multiply row/frame indices by 160 to sample
this atlas. Round 2 adds `version:2` and uses premultiplied bicubic reduction with full lossless 8-bit alpha. Native masters retain full alpha. Invisible RGB is discarded by WebP. One transparent pixel separates rectangles. Identical held frames may reuse a
rectangle without dropping any timeline samples. The renderer verifies the terminal
pose transforms and reuses its PNG; this avoids stochastic noise in a held wreck.
The encoder retains all
40 frames and tries quality 90/85/80/75, refusing anything above **200,000 bytes**.
Validation decodes the actual WebP and checks exact alpha reconstruction, motion,
held death, metadata, review completeness and (on the GPU path) both master sizes.
No runtime loader is changed or candidate adoption implied by this art-only lane.

`biplane-PASS` is a human/agent visual verdict, never written merely because contract
checks pass. Round-1 shortcomings and exact check results belong in the unit
`REVIEW.md` and the external `biplane-log.md`.

### Resumed round 2: registration, pigment and evidence

`refine.py` runs after build and before paint. It converts curved seam details to
solid meshes, applies the finished bevels, corrects normals, and fits the actual
wing/cowl/tail surfaces in the fixed source camera while retaining camera depth.
Registration bounds and residual changes are recorded in `registration.json`;
this is a local full-depth fit, not proof of an exact global camera match.
Four interplane struts replace eight accidentally coincident struts. Their solid
end fittings follow measured source attachment points. The propeller is physically
shorter about its spindle. A curved, beveled, full-depth stone support replaces the
broad straight support; the horizontal circular disc moves on its ground plane.

Before projection, shape-preserving subdivision supplies visibility samples along
long faces. A single frozen world-space BVH avoids rebuilding the dependency graph
on every UV/colour-attribute write. Projecting the original source on the finished
surface prevents bevels moving its brushwork. A 96% camera-only pigment branch
retains painted illumination; non-camera rays and unseen surfaces keep the physical
material and existing generated linen/olive/wood/rubber fills. Standard/None avoids
compressing the painted pigment twice, with lower product-light energies. This is
specific to painted illumination, not a general photographic preset. The base
uses physical cream plus a camera-only top/rim pigment; it never retains a painted
shadow or image of the moving support. Eight actual AO/curvature bakes remain.

One automatically fitted rest grade is frozen for every clip. Its source painting,
raw rest and render-manifest hashes are recorded. Packing rejects mixed rest/clip
render settings, stale masters, raw images, processed frames or grades. Round-two
CPU256 previews are labelled as such; old native CPU512 masters stay archived under
`masters/biplane/round1-cpu`, never relabelled as this round's GPU output.

`gpu.sh` resolves its own checkout, defaults to round 2, retains
`gpu-logs-biplane-r${ROUND}.log`, writes `biplane-gpu-status.txt`, and writes a
round-specific JSON receipt only after every stage, current GPU512/256 master,
trimmed atlas and eight-second decoded-atlas MP4 passes. It never creates PASS.
`--python-exit-code 1` makes Blender Python exceptions fail the shell stage.
Six unit regressions cover changed scripts/paintings/masters, CPU falsely presented
as GPU, and stale GPU source hashes. A missing-input invocation tests the actual
shell logger/error trap without starting Blender.

### Motion standard and aircraft diagnostic

The cross-family standard is proven CMU free-use or Quaternius CC0 motion for
humans, and a CC0 animated base/retarget for quadrupeds; match rest poses, bone rolls
and travel axes before retargeting, without a later foot-orientation patch. Every
round requires top/front move-cycle foot review and checks for sliding. Record
source URL, version and licence in unit and external `SOURCES.md`.

Biplane has no human or animal. Its rigid flight and propeller motion is mechanical;
retargeted walking is inapplicable. `g` writes `biplane-g-feet-check.png` with top
and front landing-gear views over all eight move samples, explicitly labelled
**airborne, no grounded walk**. The audit checks wheel planes follow the flight
axis throughout all forty poses. Clear excluded meshes' keyed visibility only in the unsaved diagnostic scene: rendering reevaluates animation even after `frame_set` and otherwise turns the hidden support back on. Wing ribs
follow the actual upper-wing pivot in death; the final wreck pose and decoded
last two frames are identical. Review the source-painted surfaces exposed in banking
and crash poses; geometric/encoding checks do not establish clean art or motion.

### Driver round 2 after a verified GPU pass

Preserve round-one GPU evidence before rebuilding: this lane keeps it under
`masters/biplane/driver-r1-gpu/` and `review/3d-v2/biplane-driver-r1-gpu/`.
The round-one receipt verifies Cycles GPU512/64, 191,950 bytes at Q80 and the
8-second MP4; its visual approval remains false. New CPU256 previews must not
inherit old files in the active `512/` directory.

Thicken the closed strut cross sections before fitting their attachment endpoints.
Small wheel hubs use dull steel, while the rotating propeller uses a separate
amber-tinted generated wood material. A shared dark wood fill made its silhouette
much heavier than the painting even with the right blade length.

The cream disc blends fine object-space grain with frozen source UV pigment only
below the support/contact region (feathered from source y=212 to 218 at 256 px).
This preserves the painted lower rim without leaving an image of the support in
the wreck. Its centre remains physical/procedural stone. Retain the automatic
rest-derived histogram grade, fixed for every clip.

Attack effects must be attached to the **finished, registered** gun endpoints.
Using original construction coordinates buried them in the cowling. The revised
short solid amber bursts use keyed visibility and keep nonzero thickness.
`gpu.sh` invalidates any old PASS when a new run starts; a successful GPU receipt
still does not approve the art.
