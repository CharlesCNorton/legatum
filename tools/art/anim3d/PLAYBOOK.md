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

## Infantry / peltast — round 1

This chapter owns only `units/peltast/`. It follows the MPFB infantry method above,
with an original throwing stance and kit fitted to the peltast painting, rather
than a recoloured hoplite. All six installed Blender skills informed the build:
anatomical subdivision and rounded/thick kit; layered cloth/skin/reed materials;
warm upper-left product key, soft fill and cool rim; calibrated orthographic
camera; joint keys and delayed cloak deformation; transparent Cycles previews,
retained image sequences, and an explicit Metal GPU final pass.

**The four quality levers are the standard method.** Match the painting's camera
and rest pose, then freeze the original painting as UV base colour on genuine 3D
surfaces. Blend by incidence and source alpha into generated painted fills on
unseen faces. Finish actual geometry (cloth folds and thickness, boot laces,
cap fur/ears, rawhide binding, dished wicker, beveled iron tips); use a product
lighting setup; freeze a bounded histogram grade measured against the original.
A reference projection cannot repair a mismatched silhouette or anatomy. Judge
painting/render/50% crossfade at rest, at native 256 and 64 px; successful checks
are not art approval. Do not write a PASS marker while the likeness falls short.

The shared stone target is sRGB **#E9CFA0**: convert sRGB to scene-linear before
setting Principled Base Color, keep a rough fine-grained surface and one low
beveled disc, and check the *displayed* result. Peltast records a separate,
reference-measured limestone colour correction so the figure histogram does not
turn the base grey. That correction is frozen across clips, not independently
fitted per frame.

External dependencies reuse MPFB 2.0.18, MakeHuman eyes, Blender and Pillow from
`env.sh`. `assets/peltast/painting-source.png` is our original CC BY 4.0 master;
`painted-fills.png` is original generated red linen, blue wool, wicker and leather.
The prompt and prepared-file SHA256 inventory are in the unit directory. Fetch
only into `ANIM_ROOT/assets/peltast/`; all blend files, 512/256 images and baked
maps stay under `ANIM_ROOT/masters/peltast/`. The repository contains only scripts,
provenance and the small delivery atlas. Source downloads/licences are recorded
in `ANIM_ROOT/assets/SOURCES.md`.

From the repository root, rebuild sequentially:

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/peltast/prepare.py
tools/art/anim3d/units/peltast/render.sh bootstrap
tools/art/anim3d/units/peltast/render.sh build
tools/art/anim3d/units/peltast/render.sh b
tools/art/anim3d/units/peltast/render.sh paint
tools/art/anim3d/units/peltast/render.sh bake
RESOLUTION=512 tools/art/anim3d/units/peltast/render.sh c
tools/art/anim3d/units/peltast/render.sh animate
tools/art/anim3d/units/peltast/render.sh d
for clip in idle move attack hit death; do
  RESOLUTION=512 tools/art/anim3d/units/peltast/render.sh "e-$clip"
done
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/peltast/pack.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/peltast/validate.py
tools/art/anim3d/units/peltast/render.sh audit
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/peltast/mp4.py
```

Every invocation is plain `blender -b --disable-autoexec ...` through the PATH
gate. No independent lock, executable bypass, thread override, or overlapping
heavy processes. The unit defaults to Cycles CPU. GPU finals use Cycles/Metal
with denoising, fail if Metal is missing, and never silently fall back:

```sh
tools/art/anim3d/units/peltast/gpu.sh
```

This no-argument entry point rerenders b/c/d and all five clips at 512 px,
regenerates 256 px masters, all reviews (including `peltast-f-restpose-compare.png`),
the trimmed atlas, validation and geometry/animation audit, and
`peltast-round${ROUND:-1}.mp4`. The video is eight seconds, five clips side by side
at 2x the shipped size on cream, H.264 yuv420p. Raw renders, manifests, prepared
textures and packed blend images make the pass reproducible without new downloads.

Animation uses the 53-bone MPFB rig with authored keys (no new mocap): idle
breathing, a stepping guard move, overarm throw/recovery, a hit recoil and a fall
with independent equipment release and a held final pose. Cloak follow-through
is an authored shape key, **not a claimed cloth simulation**. Visibility keys hide
the released javelin; no geometry is scaled to zero. Source/clip/render/grade
hashes prevent packing stale or mixed passes. The audit checks mesh volume,
transforms, base stability, loop closure and the terminal hold. It does not claim
a complete skin/cloth/equipment collision solver.

### Peltast atlas contract (trimmed version 2)

Compatible with the siege family's `version:2` rectangle convention; the logical
frame is 160×160. Five physical shelves preserve idle/move/attack/hit/death row
order, with 8/8/10/4/10 entries. `frame:{w,h,ax,ay}` defines the untrimmed logical
canvas and its ground anchor. `atlas:{w,h}` records encoded dimensions. Each
`clips[name]` keeps `row`, numeric `frames`, `fps`, `loop` and ordered
`rects:[{x,y,w,h,ox,oy}, ...]`. `x/y/w/h` selects the tightly cropped atlas region;
`ox/oy` restores it in the logical frame. Draw at
`(anchorX + ox - ax, anchorY + oy - ay)` with the desired scale. Atlas rectangles
have a transparent one-pixel gutter. RGB quality remains 75. The packer tries
256, 64, then 32 alpha levels (maximum opacity error 0, 2, or 4/255 as
conservatively bounded in the report; actual quantizer errors are checked).
WebP stores the chosen alpha losslessly. This follows the original infantry
pipeline's bounded alpha quantization; full-alpha 512/256 masters are retained.
The packer refuses >200,000 bytes at 32 levels rather than removing frames or
lowering RGB quality. The measured report records the chosen alpha levels. Existing fixed-grid consumers must use the rects to display this
candidate; this lane does not change runtime wiring.

Peltast attachment finding: a posed/scaled bone can have shear. Parenting and
then assigning `child.matrix_world = old_world` decomposes the inverse into TRS,
which distorted the shield and shifted its UV registration. The unit helper first
measures the bone parent's full world matrix with identity child transforms, then
stores its inverse in `matrix_parent_inverse` and the original transform in
`matrix_basis`. This retains the authored geometry without approximating shear.
