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

## Siege family — artillery (mechanical gun, round 1)

This unit's painting has **no crew**. Its true 3D model is a shielded olive field gun with pneumatic
tires, split trails, ground spades, hollow tapered bore, breech, recuperator cylinders, and wheel
hardware. It uses an editable mechanical parent rig; do not add the field-cannon's Napoleonic gunner.
All artillery scripts live in `tools/art/anim3d/units/artillery/`, to avoid family-lane collisions.
The six Blender skills guide bevels and physical thickness, Principled materials, aimed product
lighting, fixed camera calibration, mechanical keyframes, and actual rendered review.

The standard quality method is the coordinator's four levers: (1) frozen rest-camera painting UVs
on **real geometry**, with a facing/source-alpha mask blending into an original generated olive
fill on unseen surfaces; (2) real edge bevels, recessed hubs, raised bolts, tire tread, hollow muzzle,
and shaped thick shield; (3) warm upper-left key, weaker soft fill, cool rim and contact AO;
(4) source-measured, bounded contrast/channel gains, held constant over all clips. Projection retains
painted lighting and needs review in motion. It never supplies the geometry's alpha or replaces a
mesh with a billboard. Shield and barrel also have actual 256px AO and Cycles Pointiness bakes.

The one stationary stone disc targets a lit top around **sRGB #E9CFA0**, with a darker warm rim and
fine grain. Round 2 uses physical limestone plus camera-only warm top/rim pigment and live contact AO;
the render, not the input triplet, is the colour evidence. The review background is exactly #E9CFA0.

```sh
# CPU previews, one gate-managed Blender process; never bypass the plain blender command.
RESOLUTION=256 SAMPLES=8 tools/art/anim3d/units/artillery/render.sh stills
RESOLUTION=256 SAMPLES=8 tools/art/anim3d/units/artillery/render.sh preview
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/artillery/deliver.py

# Complete host GPU pass, no arguments, from repository root:
ROUND=1 tools/art/anim3d/units/artillery/gpu.sh
```

`gpu.sh` explicitly selects Cycles Metal GPU, fails if no Metal device exists, builds and rerenders
plain/textured/detail/pose stages and all clips, retains `masters/artillery/512/` and `256/`, then
packs, validates, and writes `artillery-round${ROUND}.mp4`. It respects the machine-wide `blender`
gate and never launches two heavy processes. The MP4 is eight seconds, 30 fps, H.264 yuv420p, all five
clips side by side at 2x logical scale on cream; it is reconstructed from the decoded trimmed atlas.
No master enters git. Original input hashes, bakes, packed textures, editable `.blend` files, render
hashes, and grade evidence remain under `masters/artillery/` or `assets/artillery/`.

Every render stage publishes immediately to `review/3d-v2/artillery-*.png`/`.webp`. Rest review includes
painting left, render right and a 50/50 crossfade at **256 and 64 px**, in
`artillery-f-restpose-compare.png`. Idle is a small elevation adjustment; move rolls the wheels in
place and lifts the trails (the runtime supplies travel); attack recoils the barrel and recovers;
hit jolts the carriage; death slumps the gun and cants a damaged wheel, ending in two identical held
samples. Effects use keyed visibility, never zero scale. The base stays fixed.

### Artillery trimmed atlas v2

The atlas preserves **8/8/10/4/10** frames and five clip rows in idle/move/attack/hit/death order.
`frame: {w:160,h:160,ax:80,ay:124}` describes the untrimmed logical cell and its invariant anchor.
Each clip keeps `row`, numeric `frames`, `fps`, `loop`, and adds `sprites`, one rectangle per frame:
`{x,y,w,h,ox,oy}`. Read `(x,y,w,h)` from the atlas and place it at `(ox,oy)` inside the logical cell;
the frame's cropped anchor is `(ax-ox, ay-oy)`. Rows have variable heights and packed widths; **never
infer UVs by multiplying row/frame numbers by 160**. `version:2, layout:"trimmed-rows"` identifies the
extension. This candidate does not change runtime rendering. WebP searches quality 90 down to 75,
never lower, enforcing 200,000 bytes. All 40 alpha masks must reconstruct exactly from decoded trims;
validation also checks margins, source hashes, motion, held death, video codec/duration/frame count.
An atlas contract PASS is separate from art approval; only write `artillery-PASS` when the rest pose
is hard to distinguish from the painting and all five clips are clean.


### Artillery resumed round 2: finished surfaces and mechanical contact

Prior WIP masters/reviews are preserved in `masters/artillery/round1-wip/` and
`review/3d-v2/artillery-round1-wip/`. A prior atlas is not proof of a completed WIP rebuild:
the resumed WIP had no current render manifest. No GPU execution is inferred from those CPU images.

`refine.py` registers complete circular tires, hubs and tread with uniform size and physical mounting
yaw; both wheels keep their own local rolling axis. It fits the thick shield's polygon outlines on
its actual transverse plane, seats solid fastenings, and applies bevels/converts curves before UVs.
This is local geometry registration against source landmarks, not a claim of an exact whole-camera
fit. The original orthographic camera remains. `projection.py` ray-tests the finished surfaces and
freezes their camera UVs, blending into the recorded generated olive fill on occluded/back surfaces.
A camera-only Principled pigment branch retains 96% of painted illumination; other rays retain the
physical shader, bakes and product lights. Standard/None avoids a second tone-map of that pigment.
A source-color exclusion prevents cream stone from being painted onto trails/axle. No source alpha
controls geometry visibility; there is no billboard or per-frame reprojection. No crew/fabric is added.

The stone uses separate warm top/rim pigment with live AO and physical contact shadows. One automatic
rest grade is frozen across all clips. Move lifts each trail in its correct hinge direction. Every
sample seats both complete tires on the .13m contact plane and refits the axle, including the damaged
carriage in death; a lower-bound audit alone had allowed visibly floating wheels. Final death PNGs
remain exactly identical. These checks are contact/ground checks, not a general collision solver.

`ROUND=2 tools/art/anim3d/units/artillery/gpu.sh` is the executable, no-argument host handoff (default
round 2). It resolves its checkout, retains `artillery-gpu-pass-r${ROUND}.log`, writes stage/failure
status, and issues a round-specific receipt only after current GPU512 masters, 256 gallery images,
trimmed atlas and the eight-second decoded MP4 validate. `check.py --require-gpu` rejects CPU previews,
stale pipeline/input/model/clip/grade/gallery hashes and floating tires. A missing-input preflight
verifies the failure transcript without invoking Blender. The script never writes an art PASS.

CPU iteration stays at 256px / Cycles12; fresh 512px finals remain the host GPU pass. Compare the rest
sheet and all five strips after rebuilding: registration, hub/tread richness, trail construction and
revealed surfaces can still fall short despite technical validation. Current measured results and
honest 256/64 verdict are in the external artillery log and unit README.

Artillery packing reuses identical frame rectangles within each clip. This preserves all forty playback
samples and makes the decoded final death hold pixel-identical too; separately encoded duplicates
had different lossy RGB despite equal source PNGs. The unit transcript name avoids the driver log.
