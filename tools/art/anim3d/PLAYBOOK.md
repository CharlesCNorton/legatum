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

## Vehicles — landship / Early Tank (round 1)

This unit's isolated implementation lives in `tools/art/anim3d/units/landship/`.
It reuses the vehicles family's full-depth camera registration, painted projection,
trimmed delivery and video methods, without changing its shared scripts. All six
Blender skills informed modeling, materials, lighting, camera, mechanical animation
and render inspection. There is no visible human crew in this painting.

```sh
tools/art/anim3d/units/landship/render.sh build
tools/art/anim3d/units/landship/render.sh b
tools/art/anim3d/units/landship/render.sh bake
tools/art/anim3d/units/landship/render.sh animate
SAMPLES=12 tools/art/anim3d/units/landship/render.sh c
# Render d, e-idle, e-move, e-attack, e-hit, e-death and g in that order.
# Complete lead-side pass, no arguments, from repository root:
ROUND=1 tools/art/anim3d/units/landship/gpu.sh
```

Every invocation is plain `blender -b --disable-autoexec` through the PATH gate.
Never bypass it or run two heavy processes in this lane. CPU previews use Cycles;
`gpu.sh` explicitly discovers Metal devices and fails rather than silently falling
back. It renders all stages and forty clip frames at 512px, retains actual 512px
and downsampled 256px masters outside git, creates reviews immediately, packs and
validates the atlas, audits geometry and writes `landship-round${ROUND}.mp4`.
The video decodes the trimmed delivery, shows all five clips side by side at 2x
on #E9CFA0, and verifies H.264/yuv420p, 1600x348, 240 frames and eight seconds.

### Four quality levers and judging

1. Match the painting camera and rest silhouette first. Freeze camera UVs on
   **finished full-depth meshes**, not flat cutouts or a composited painting.
   Landship projects the original CC BY 4.0 full-size source onto hull, cab,
   sponson, base and track parts. Each shoe carries its own paint while moving.
   Facing/alpha confidence blends hidden surfaces into the licensed generated
   metal fill, graded ochre. Newly exposed surfaces remain approximate.
2. Real geometry supplies beveled armour, riveted seams, deep sponsons, hollow
   muzzle, roof hatch, track housings and 128 independent shoes/grousers. Actual
   Cycles AO and Pointiness bakes for three armour parts supply cavity grime and
   roughness wear on the physical fallback. Projected pigment already contains
   the source's painted illumination; camera-only pigment avoids double lighting.
3. Use a warm upper-left key, cool rim and soft fill/contact shadow. The common
   base pigment is sRGB **#E9CFA0**, converted to linear for the physical shader;
   projection preserves the painting's darker rim and warm top. Standard/None is
   deliberate for already painted pigment, not a photographic render preset.
4. Sample opaque rest-pose RGB 10/50/90 percentiles against the painting. Build
   one bounded monotonic grade (18 levels/channel maximum), freeze it and apply
   it to every painted pose and frame; preserve raw renders and alpha. Never
   per-frame grade, because it flickers. Rerender c before all painted stages
   whenever lighting/materials change.

Judge painting/render/50% crossfade in `landship-f-restpose-compare.png`, plus
native 64px in `landship-f-restpose-64.png`; details, three-view plain geometry,
rig poses and each clip have their own immediate review. Never equate a valid
atlas with painting parity. `landship-PASS` is written manually only after visual
parity, clean clips and <=200KB delivery are established. No script grants PASS.

### Motion and contact standard

Humans use proven CMU free-use or Quaternius CC0 motion with native Blender or
Rokoko retargeting, matched rest poses and bone rolls. Only weapon-specific attack
is authored on top. Animals use an appropriately licensed animated quadruped base.
Do not hand-correct foot orientation after retargeting: fix the coordinate map.
Always render top/front move-cycle checks as `<slug>-g-feet-check.png`.

Closed vehicles without visible crew use mechanical rigs: landship's 128 shoes
move around physical closed rhomboid routes by arc length, with the lower run
moving opposite +X travel. The sprite is an in-place loop (runtime supplies world
travel); its g-feet-check is top/front running-gear inspection. Idle is restrained
engine vibration, move cycles the tracks, attack recoils the sponson barrel, hit
jolts the chassis, death opens the hatch and becomes a smoking disabled wreck.
Idle/move loop; the final two death frames hold identically. Effects are real
finite-thickness meshes with keyed visibility, never zero/near-zero scale.

### Landship delivery contract

The candidate uses the vehicles **version 2 trimmed** format. Logical frames are
160x160; row order is idle/move/attack/hit/death, with 8/8/10/4/10 frames and
10/12/14/12/10 fps. `frame.ax/ay` is the anchor in the untrimmed cell. Each clip's
`rects[]` stores `x,y,w,h` in the atlas and `ox,oy` in that logical frame. Draw the
crop at `(anchorX-ax+ox, anchorY-ay+oy)`, scaling all coordinates together. `row`
is ordering metadata, not a fixed cell-height coordinate. Held duplicate frames
share a rectangle. Transparent gutters surround every crop. Quality is the
highest of 95/90/85/80/75 fitting **200,000 bytes**; failure never drops frames or
quality below 75. Decode validation checks exact alpha reconstruction, crop
bounds/gutters, source/scene/grade hashes, all clip counts, motion and held death.
The existing static painting remains the runtime art until the lead approves the
candidate; this lane does not change the runtime renderer.

### Landship driver round 2: inspect hidden projection and pivots

Incoming GPU round1 completed at quality90 / 188748 bytes, but that technical pass
hid art defects. Archive GPU evidence before replacing previews. The cab and far
upper track were overlaid by convincing pigment despite incorrect geometry; a
lower camera elevation, full-depth cab corner registration, fitted near nose,
smaller grousers and a flatter cream disc improve the physical match.

Generate occlusion fills where motion uncovers baked-in objects. The original
stone texture included a second chassis, and the sponson included a second gun.
Round2 uses a generated clean-stone top on the actual disc (original lower rim
retained), plus a small feathered generated gun-port patch on the actual sponson.
All other visible surfaces retain the painting. Both original generated outputs,
exact prompts and hashes are retained. Alpha controls pigment confidence only;
it never cuts the geometry. Real AO supplies changing stone contact shading.

Removing the false painted gun exposed an almost camera-facing geometric barrel.
Its actual axis now reproduces the painting's visible length, with the recoil
pivot at the mantlet. Never use a projection match as proof of mechanical fit.
The flash is a closed tapered gas jet; smoke uses nonzero, closed irregular volume
meshes instead of opaque stacked balls. Death opens the hatch and holds the wreck.
No cloth, straps or human/animal motion is appropriate to this crewless painting.

`animate` seals source scripts, immutable painting/fills, six bakes and all saved
masters in external `build-inputs.json`. `gpu.sh` checks that seal and the geometry
before rendering, then verifies every stage really used GPU512, the retained
512/256 painted masters, the trimmed atlas and decoded eight-second MP4. Changing
build inputs requires build/bake/animate again. Do not edit an executing shell
entrypoint: bash can read its changed tail mid-invocation. No script grants art PASS.
