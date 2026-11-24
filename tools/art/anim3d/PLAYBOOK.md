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

## Vehicles / aircraft — bomber

Unit scripts are isolated under `tools/art/anim3d/units/bomber/`. This aircraft uses original closed fuselage lofts, thick airfoil lofts, twin fins, recessed radial engines, rolled cowls, three-bladed propellers, convex glazing with real frame tubes, and the painting's curved stone support. There are no subject image cards. Actual 512 px Cycles AO and Pointiness bakes on the fuselage and both wings drive restrained cavity grime and edge wear; those maps retain their own UV layer beside the rest projection. Mechanical pivots control the airframe and two propellers; released bombs have independent keyed transforms and visibility. The disc stays fixed. Death banks, drops, impacts and buckles the near wing and nose into a held wreck, collapsing the damaged support as solid geometry, never a zero scale.

The standard four finish levers are: (1) align camera and real geometry to the painting, then freeze camera-projected UV colour onto meshes, blending generated painted fills into unseen surfaces; (2) finish geometry with rounded airfoil sections, bevelled lips, real thickness and relief; (3) warm upper-left product key, cool rim and soft fill, with Cycles denoising; (4) measure RGB 10/50/90 percentiles and reuse one bounded rest-pose grade across every frame. Projection retains painted lighting and needs moving-view review. Colour agreement alone never proves silhouette parity. All six installed Blender skills informed geometry, material separation, camera registration, lighting, animation interpolation and rendered QA.

Warm stone standard: target visible top near **#E9CFA0**, darker cream rim. Convert pigment from sRGB to linear before assigning BSDF colour; the bomber's starting value is `(0.815, 0.624, 0.352)`, roughness `.86`, fine noise bump. The stationary disc uses physical limestone with masked source rim pigment and a clean support footprint; live AO provides changing contact shadows. Recheck rendered pixels after the light/grade changes; a shared shader does not guarantee the same output colour.

```sh
# CPU geometry build and review (all Blender calls use the gated plain PATH command)
tools/art/anim3d/units/bomber/render.sh build
RESOLUTION=512 SAMPLES=8 tools/art/anim3d/units/bomber/render.sh all
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/bomber/deliver.py all
# Complete host GPU pass, saved masters, no arguments:
ROUND=1 tools/art/anim3d/units/bomber/gpu.sh
```

The GPU handoff renders each stage serially using Cycles Metal at 512 px, writes 512/256 masters, stage review images and animated WebPs, the painting/render/crossfade `bomber-f-restpose-compare.png`, trimmed atlas, validation and an 8-second H.264/yuv420p `bomber-round${ROUND}.mp4`. It explicitly fails if Metal is unavailable. The driver supplies ROUND. `audit.py` checks true 3D principal meshes, stationary base, motion, loop closure and held terminal pose. A successful audit is not painting parity; no PASS file is written automatically.

### Bomber trimmed atlas contract (version 2)

`app/src/assets/units/anim/bomber.{webp,json}` uses logical 160 × 160 cells and anchor `(80,132)`. Rows remain idle/move/attack/hit/death with 8/8/10/4/10 frames at 10/12/14/12/10 fps; only idle/move loop. Empty margins are removed **per frame**; sprites are packed left-to-right with 2 px gutters within each variable-height row. `clips[name].sprites[i] = {x,y,w,h,ox,oy}` specifies atlas rectangle and offset into its original logical cell. Draw at `(anchorX-ax+ox, anchorY-ay+oy)`; do not recenter crops. `frame.w/h` describe logical cells, not atlas stride. `atlas.w/h/quality` describe the actual image. Legacy fixed-grid consumers need this explicit format support before adoption; no runtime is changed here.

Packing retains all 40 frames and selects quality 80/75, refusing anything above 200,000 bytes. Validation reconstructs logical cells, checks alpha, frame counts, offsets, atlas bounds, visible margin, motion and identical visible held death frames (ignoring RGB under zero alpha). Master and raw-frame hashes prevent interrupted/stale renders from entering review. Masters remain in `$ANIM_ROOT/masters/bomber/`; provenance and generated fill stay under `$ANIM_ROOT/assets/bomber/`. Early CPU review is evidence of progress, not a GPU or art sign-off.

### Bomber round 2: finished surfaces and mechanical motion

Inspect current images before rebuilding and archive their actual provenance. The supplied round-one
images were Cycles CPU512/4; they did not prove a GPU pass. Prior masters/reviews remain in
`masters/bomber/round1-cpu`. No PASS follows from technical success.

The fuselage crown now reaches the dorsal turret's mounting surface. Finish bevels/subdivision and
convert capped frame tubes into solid meshes before freezing UVs. Camera-only pigment avoids
lighting the stone with the painting's baked highlights; non-camera rays retain the physical BSDF.
Standard/None preserves already painted illumination, while product lights still shade the true
geometry. Source visibility/facing masks feather into the existing generated olive fill. A separate
source-object mask removes rotating blades from underlying body/cowl paint. The plain stationary
stone disc has physical grain, a cream top/rim, contact shading and no projected figure/support.
One bounded rest histogram grade is frozen across all clips. Baked AO/curvature remain real maps.

Propellers rotate around local Z under fixed shaft mounts. Adding to a tilted mount's Euler Z had
changed the shaft direction instead. Two painted blade vectors define a projected circular plane;
SVD reconstructs its orthonormal 3D basis and radius. Blades retain real thickness and bevels.
The loop audit checks axis stability as well as three-blade periodicity. Held death is rendered once
and copied byte-for-byte. All five clips retain 8/8/10/4/10 samples.

Motion standard: humans use licensed CMU or Quaternius CC0 motion and correctly matched rest poses,
bone rolls and forward axes; animals use a licensed animated CC0 quadruped. Check top/front feet
through the complete move cycle without hand-correcting orientation after retargeting. For this
crewless aircraft, feet and mocap are inapplicable: `bomber-g-feet-check.png` explicitly says so and
shows actual top/front move renders to inspect shaft direction, bank and the fixed pedestal.
Asset URLs, versions and licences live in unit `SOURCES.md` and external `assets/SOURCES.md`.

`ROUND=2 tools/art/anim3d/units/bomber/gpu.sh` is the one executable host entry point. It runs all
stages serially in Cycles Metal at 512 px, saves genuine 512/256 masters, refits the rest grade,
authors/saves the clips, runs the geometry audit, packs/validates the trimmed atlas, and encodes
all five decoded clips side by side at 2x scale for eight seconds. A retained transcript, status
and round-specific receipt distinguish missing input/device failures from successful GPU output.
The receipt requires actual GPU settings, current blend/raw/grade/frame hashes, and verified video
codec, pixel format, dimensions, duration and frame count. It never writes art PASS.

Atlas validation independently reconstructs all 40 alpha planes at their offsets and checks gutters,
bounds, timing, motion, held death, current source hashes, quality >=75 and <=200,000 bytes. Packing
tries quality 95/90/85/80/75 without dropping frames. `test_delivery.py` covers bounded monotone grade,
stale-master rejection, CPU rejection by the GPU gate, missing-input shell failure receipts, and
incorrect movie frame count. CPU preview checks do not claim that Metal ran inside the sandbox.

Round-two CPU evidence: 40 samples, Q80 **192,266 bytes**, exact reconstructed alpha and held death; geometry and five delivery regression checks pass. Movie: H.264/yuv420p, 1600x348, 240 frames/eight seconds. Silhouette IoU .878 at256/.883 at64 (prior .847/.858). Canopy/nacelles, propeller finish, stone rim and wreck character still fall short; no PASS. GPU512 rendering and visual acceptance remain outstanding.

### Bomber driver round 2: GPU findings and occluded paint

The actual driver round-one pass succeeded at GPU512/96: all 40 clip frames, Q80
191,852-byte atlas, and the verified eight-second movie. Its full evidence is preserved
in `masters/bomber/driver-r1-gpu/`. The outer driver log was empty because gpu.sh redirected
all output; the script now reports the transcript path and completion/failure to the driver.
It uses a saved output descriptor because sandboxed Bash rejected /dev/fd process substitution.

At 256 px the largest gaps were the flat tan disc, white/blue fallback patches behind
rotating blades, an overly round nose lens, and the disappearing support during death.
At 64 px identity was already close, but the empty-disc death remained visibly wrong.
The revised disc projects only the exposed stone rim/outer top; its support footprint
uses clean procedural pigment and live AO, so no raised support is baked onto the base.
The nose lens and its solid frame tubes share a tilted elliptical volume. Propeller
blades retain thickness/bevels and receive original painted highlights and tip bands.

Do not fill a blade-removal mask with one flat material colour. The generated
`occlusion-fill-source.png` reconstructs the surfaces behind the six blades, using the
original registration and only the excluded pixels. The original painting still supplies
all other visible colour, and real geometry supplies all silhouette/alpha. Convex glazing
and small attached mechanical parts skip the coarse vertex-visibility mask: a frame
intersecting a few vertices otherwise spreads blue/white fallback across whole polygons.
The normal-facing mask still blends unseen surfaces to material fills. New artwork is
recorded in unit SOURCES.md and external assets/SOURCES.md; no masters enter git.

Death compresses the solid stone support into a remnant, buckles the near wing and
settles the belly on the disc. The propeller decelerates into a held angle, with an audit
for the last three angular deltas. A scalar ground-contact check alone did not establish
a convincing grounded silhouette; inspect the strip and decoded movie as well.

The no-argument `gpu.sh` verifies hashes for builder scripts, textures and saved masters
before rendering; run `render.sh build` after changing them. Its final GPU512/256 stages,
trimmed atlas, validation and decoded H.264 movie are unchanged as deliverables. The
`build-inputs.json` keys are logical paths so identical source in another checkout works.
No automatic art PASS is written.

Driver-round-two CPU checks: 64 stage/master PNGs at each of 512/256, all 40 clip samples,
73-mesh audits across five clips, exact decoded alpha/offset/gutter checks and held death
pass. Atlas: **197,232 bytes at Q80**. Six delivery regression tests pass. Movie: H.264
yuv420p, 1600x348, 240 frames/eight seconds. The native 256/64 comparison improves, but
wingtip shape, propeller hubs and the too-intact wreck still differ; no PASS. Run
`ROUND=2 tools/art/anim3d/units/bomber/gpu.sh` for the final Metal pass and visual review.

### Bomber driver round 3: stone fill and surface contact

The incoming GPU round-two pass completed all stages at Cycles GPU512/96, with
all 40 frames and an eight-second decoded movie. Preserve its masters, receipt
and review images under `masters/bomber/driver-r2-gpu/` before CPU iteration.
At256 the outstanding gaps were stone grain/support edges, angular wing tips,
simplified hubs and a too-intact, weakly grounded death; identity already matched
at64. Metrics and successful rendering are not art acceptance.

The generated clean stone disc is registered by its opaque bounds to the original
painting's disc. Its top supplies hidden mineral grain; the original lower rim
remains, and Blender AO supplies moving contact. Source SHA256 is verified before
preparation; the exact prompt and generation are recorded with the unit. Finish
support bevels and planar cap normals before projection, and do not interpolate
coarse occluder masks over the support's visible cap. Both wing tips have more
rounded span stations; the far wing root extends beneath the nacelle.

Death now folds the outer wing at a span break and retains a solid crushed
support. The original horizontal flight path keeps the entire tail inside the cell. `contact.py` samples evaluated aircraft
vertices, triangle interiors and edge midpoints against a BVH of the actual disc
and deformed support. This replaces the old nominal-disc-height vertex test,
which ignored the remnant and could pass an unconvincing pose. It is a sampled
contact check, not a full continuous collision solver. Review the complete strip
and decoded movie as well. The GPU receipt includes the measured contact record.

Run `ROUND=3 tools/art/anim3d/units/bomber/gpu.sh` from the repository root after
the CPU build. The executable does every GPU stage, 512/256 masters, grade,
trimmed 160px atlas, alpha/offset checks, geometry audit, reviews and H.264 movie.
It checks current input hashes, fails rather than using CPU when Metal is absent,
and never writes art PASS automatically.

Driver-round-three CPU evidence: all 40 frames, **197,588 bytes at Q80**, trimmed
160px cells; exact alpha/offset/gutter/clipping/held-death checks pass. All five
73-mesh audits pass; sampled terminal stone contact gap zero over 21,240 samples.
Six delivery regressions, nine Python parses and both Bash syntax checks pass.
64 masters at each of512/256; movie H.264/yuv420p1600x348,240frames,8.000s.
A farther-left wreck path failed clipping and was restored before final delivery.
At64 identity matches; at256 the hubs, glazing edge and support still differ,
and broad rotations reveal pigment seams. No PASS; GPU round3 review is pending.
