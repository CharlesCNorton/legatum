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

## Infantry chapter: barbarian spearman, round 1

This unit owns `units/barbarian-spearman/`; it reuses the infantry lead's MPFB and
posing helpers without changing those shared scripts. Its separate external root
is `masters/barbarian-spearman/`. The kit is a folded linen tunic, thick fur mantle
and solid tapered hair locks, leather wraps and belt/buckle, a low ash spear with
iron head, and a convex oval rawhide shield with rim lacing and iron boss. The
full MPFB body and 53-bone skeleton remain editable. The original painting is the
reference, not a claim of equivalence: the face, fur silhouette and draping need
more sculpting and registration in later rounds.

The standard quality method for infantry follows feedback 18–21:

1. Match the painting camera and rest-pose landmarks before projecting its full
   master into frozen UV coordinates on real 3D surfaces. Never project from the
   animated camera every frame. Blend the painting by alpha and surface incidence
   into the project's generated linen/hair fill textures on unseen surfaces.
   Inspect occluded parts and cloth/skin boundaries: source lighting and imperfect
   registration can produce projection spill; texture cannot repair anatomy.
   Mask the source spear out of non-weapon UVs so it does not become a second
   painted weapon when the real spear moves; fill the excluded strip with the
   underlying surface material.
2. Finish geometry: subdivided MPFB anatomy, physical cloth thickness and folds,
   beveled hard edges, thick straps, buckle and lacing, shaped metal edges. Actual
   AO and Cycles Pointiness maps are baked at 256 for skin, linen, shield and boss;
   AO darkens cavities and curvature modulates iron roughness.
3. Use a warm upper-left product key, soft fill, cool rim, AO/contact shading and
   denoising. The one stationary low stone disc uses the shared cream target
   **sRGB #E9CFA0**, entered as linear pigment `(0.815, 0.624, 0.352)` before lighting.
4. Sample the painting's foreground RGB quantiles and derive one restrained,
   monotonic LUT from the rest render. Reuse that exact LUT for every frame; never
   independently grade frames. Keep raw renders. Judge the native 256 and 64 px
   evidence and `barbarian-spearman-f-restpose-compare.png` (painting, render, half
   split, 50/50 crossfade) honestly.

Run from repository root, sequentially. Every Blender invocation is plain
`blender -b --disable-autoexec --python-exit-code 1 ...` through the PATH gate;
no direct application path, thread override, zero-scale hiding or second heavy
process. Local previews default to Cycles CPU. Rebuild downstream files after
changing geometry or materials:

```sh
source tools/art/anim3d/env.sh
TASK=tools/art/anim3d/units/barbarian-spearman
"$ANIM_ROOT/venv/bin/python" "$TASK/prepare.py"
"$TASK/render.sh" build
"$TASK/render.sh" refine
"$TASK/render.sh" b
"$ANIM_ROOT/venv/bin/python" "$TASK/review.py" b
"$TASK/render.sh" paint
"$TASK/render.sh" bake
"$TASK/render.sh" animate
# Host-only, no arguments: all GPU reviews, 512/256 masters, atlas and checks.
"$TASK/gpu.sh"
```

The GPU handoff requires the external masters and packed inputs produced above.
It explicitly selects Cycles Metal GPU at 512 px / 64 samples and refuses a CPU
fallback. It renders every stage and all 40 clip frames, writes all named review
images and animated WebPs, packs and validates delivery, and audits saved rigs.
No upload, push, runtime integration or art approval is implied.

### Trimmed atlas v2 (160 px infantry delivery)

`app/src/assets/units/anim/barbarian-spearman.{webp,json}` uses five ordered
packed rows (idle/move/attack/hit/death), with **8/8/10/4/10** samples. Every source
is reduced to a logical 160px cell with premultiplied bicubic filtering and full
8-bit alpha. Transparent margins are trimmed; rows are packed with two-pixel
outer padding and four-pixel gutters. Identical samples reuse one rectangle,
so the last two death samples remain byte-identical after lossy WebP decoding.

JSON retains `frame:{w:160,h:160,ax:80,ay:137}` and each clip's timing/row, adds
`version:2`, `atlas:{w,h}` and per-clip `rects:[{x,y,w,h,ox,oy},...]`. The source
rectangle is explicit; never derive it from a fixed grid or the row index. Draw
at `anchor + (ox-ax, oy-ay)` scaled to display size. This art lane does not change
the runtime consumer or switch the game away from the painting.

Packing tries Q90/85/80/75, refuses >200,000 bytes, and preserves all samples.
Source/clip/rest/grade hashes, matching render settings, decoded alpha, padding,
clipping, offsets, visible motion and terminal hold are independently checked.
Final delivery retains real 512px masters and 256px copies. `pack.py --preview`
accepts CPU256 evidence without fabricating 512px output; its report explicitly
marks the delivery as a preview. Older masters belong in the archived round.

### Barbarian spearman round 2: registered surfaces and driver movie

Start from `plain.blend`; `refine.py` always writes a separate `registered.blend`.
Freeze the MPFB macro shape keys before changing vertices or they override the
fit. Preserve the 19,158-vertex body, native weights and all 53 bones. A smooth
rest-view fitting field broadens shoulders and stance; inverse blended skin
matrices transfer those changes into the original mesh. The feet move along
camera rays back onto their contact height. The swept hair, complete convex
shield, iron boss and spear reach are fitted in geometry. Neither image warps
nor silhouette transparency substitutes for volume. Apply rigid Solidify/Bevel
before recording frozen UVs so the paint describes the rendered surface.

The painted front uses camera-only Principled emission to preserve its authored
illumination; other rays and uncovered surfaces retain physical materials,
generated linen/hair fills, real AO/curvature and product lights. A finished-scene
ray test excludes surfaces hidden behind the shield from source projection. Standard/None
is intentional for this already-painted pigment, not a photographic preset.
One automatic rest histogram LUT remains frozen across all clips. Repeating the
grade reads retained raw PNGs, rather than grading an already graded image.
The independently moving spear's excluded source band samples adjacent frozen
paint pigment with a feathered edge, reducing the old bright procedural seam.
This does not modify the source painting or mesh alpha; inspect reveal seams.

Move solves each ankle from the finished shoe sole, preserving the authored
swing lift and planted contact. The audit checks those heights within 6mm.
Death folds the elbows after release to reduce the old arm-supported floating
pose. Attack extends visibly before recovery. The last death frame is copied
from the identical settled sample; it is not rendered twice. The saved-scene
floor/grip audit is still not a comprehensive collision or motion-quality check.

`ROUND=2 tools/art/anim3d/units/barbarian-spearman/gpu.sh` is the single host
handoff. It resolves this checkout, retains a transcript and status receipt,
rejects unavailable GPU devices before rebuilding, regenerates registration,
paint, bakes and clips, renders all stages at GPU512/64, grades/reviews, exports
512/256, packs, validates and writes `barbarian-spearman-round${ROUND}.mp4`.
`video.py` reconstructs the decoded trimmed atlas using offsets, shows all five
clips at 2x on cream, and verifies H.264/yuv420p, 1600x348, 240 frames/eight seconds.
CPU previews cannot pass the final GPU provenance gate. Neither script writes
an art PASS marker; that requires visual approval of the final GPU output.

### Barbarian spearman driver round 2 after the GPU receipt

The driver round-one GPU pass succeeded (191422 bytes, Q80); earlier log entries
use development-round numbers. Preserve that actual GPU evidence separately
before producing CPU previews. Never infer GPU failure from those older notes.

Registration must fit the skeleton as well as the visible surface. A camera-ray
foot fit moved the shoe behind its original ankle; during a fall the offset
rotated below the body and propped it up. Freeze the fitted evaluated anatomy,
move the 53 joints through the same fitting field, rebind with original weights,
and restore bone-attached kit world matrices. This preserves the rest view while
bringing articulation back inside the fitted volumes. No bone count or skin
vertex count changes. Inspect both the standing view and all clips after rebinding.

This pass adds a continuous thick pelt mantle underneath the individual locks,
a slanted oval shield, narrower spear exclusion that preserves the gripping
hand, generated fur/leather fills, and front-lip-only stone projection. Never
project feet onto the base: they remain as ghosts when the real foot moves.
Death contact folds are keyed geometric deformation, not a cloth simulation.

The human motion standard is now CC0 Quaternius (or permissive CMU) idle, walk,
hit and death. Only the weapon attack is authored. This unit uses Idle_Loop,
Walk_Loop, Hit_Chest and Death01, full rest/roll-calibrated Blender constraints,
and the idle arm layer for carrying spear/shield. Calibrate footwear soles in
the reference pose; never patch foot rotations after retargeting. A 65mm hip-lowering knee solve fits the upright source walk inside the fixed
painting canvas while keeping captured ankles. Translation contact corrections
retain source foot rotations and a single virtual-ground stance speed. `audit.py` checks the planted sole and horizontal stance displacement.

Every round renders **all eight move samples from both top and front**, including
actual footwear, to `barbarian-spearman-g-feet-check.png`. `gpu.sh` includes this
stage in the same sequential pass as b/c/details/d/e, 512/256 masters, trimmed
Q75+ atlas validation and the decoded-atlas H.264 movie. `--preview` packing
remains explicitly CPU256 evidence; it is never final GPU provenance or art PASS.
