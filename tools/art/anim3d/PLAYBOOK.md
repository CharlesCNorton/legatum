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

## Infantry chapter: kneeling barbarian scout (round 1)

The unit-scoped implementation is `units/barbarian-scout/`. This chapter supplements
only this infantry variant; the older spearman commands and atlas contract above
remain historical. Reuse MPFB's CC0 anatomical mesh and 53-bone game-engine rig,
bake its morphs before changing the bind pose, and keep the kneeling lookout pose
from the painting. The wolf pelt, folded tunic, hair/beard locks, scarf, boot and
bracer wraps, belt buckle, hollow horn and beveled belt axe are actual geometry.
The unit scripts do not replace another lane's scripts or editable masters.

All six Blender skills were applied: organic subdivisions and thick kit surfaces;
painted material variation; warm upper-left key, cool rim and soft fill; fixed
orthographic painting camera; editable skeletal clips; and CPU preview / explicit
Metal Cycles final rendering with denoising. Every invocation is plain `blender -b`
through the PATH gate, with automatic script execution disabled. Never bypass the
gate or start concurrent heavy jobs. The optional reference-calibration skill is
not installed; foreground quantiles, native-size comparisons and the crossfade
provide direct calibration evidence.

### Painting-first finish

1. Align geometry, crouched skeleton, camera and silhouette to the committed token.
   Fit the full source painting into the token's alpha extent at 1024 px. Freeze
   camera-projected UVs into the real rest mesh; the UVs deform with the character.
   Blend camera-facing coverage into material backfill rather than making a card.
   Generated painted wolf fur fills unseen cloak surfaces. Assets and provenance
   stay under `assets/barbarian-scout/`, including source hashes and the prompt.
2. Bake real Cycles AO and Pointiness at 256 px for anatomy, pelt cowl and axe.
   Apply cavity darkening to base colour and curvature-driven roughness to iron.
   Disable shell Solidify only during baking to prevent inside/outside UV overlap.
   Keep actual cloth folds/thickness, tapered fur tufts and hair locks, thick leather
   wraps, metal buckle and beveled axe edge. Projected paint supplies brushwork;
   it cannot repair a misaligned silhouette or an incorrect hand pose.
3. Use product lighting with contact shadows, Cycles denoising and stable sampling.
   The base pigment is sRGB `#E9CFA0` converted to linear RGB, nonmetallic with
   roughness .85, fine-grain bump and a rounded darker rim from real lighting.
   Compare rendered pixels: sharing shader numbers alone does not match a painting.
4. Measure 17 opaque-foreground quantiles in each RGB channel and apply a bounded
   monotonic transfer blended at 30%. Freeze that rest-derived LUT for all frames
   to avoid temporal colour pumping. Preserve raw renders separately.

Each stage publishes immediately: `barbarian-scout-b-plain.png`,
`-c-textured-lit.png`, `-c-details.png`, `-d-rig-poses.png`, all five
`-e-<clip>-strip.png` and animated WebPs, and `-f-restpose-compare.png` (painting,
render, half split and 50/50 crossfade), plus a native 64 px comparison. CPU and GPU
render metadata are retained. A generated review sheet is not an art pass.

### Rebuild and lead handoff

From the repo root, with the existing shared MPFB install and downloaded source:

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/barbarian-scout/prepare.py
tools/art/anim3d/units/barbarian-scout/render.sh build
blender -b --disable-autoexec --python-exit-code 1 --python tools/art/anim3d/units/barbarian-scout/texture.py
blender -b --disable-autoexec --python-exit-code 1 --python tools/art/anim3d/units/barbarian-scout/bake.py
blender -b --disable-autoexec --python-exit-code 1 --python tools/art/anim3d/units/barbarian-scout/animate.py
RESOLUTION=512 SAMPLES=8 tools/art/anim3d/units/barbarian-scout/render.sh all
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/barbarian-scout/post.py pack
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/barbarian-scout/post.py video
```

The complete GPU handoff, no arguments, is:

```sh
tools/art/anim3d/units/barbarian-scout/gpu.sh
```

It renders every stage serially using Metal Cycles at 512 px, keeps 512/256 masters,
rebuilds reviews, packs and validates, and writes
`review/3d-v2/barbarian-scout-round${ROUND}.mp4`: all five clips side by side,
8 seconds, 2x scale on cream, H.264 yuv420p. It rejects missing GPU devices rather
than silently falling back. `ROUND` defaults to 1 for a manual run. Source/grade
hashes prevent a mixed-generation atlas. The GPU path rerenders saved models;
rebuilding geometry or textures requires regenerating clips first.

### Trimmed 160 px atlas contract, version 2

Ship `app/src/assets/units/anim/barbarian-scout.{webp,json}` as a candidate without
changing the runtime. `frame:{w:160,h:160,ax:80,ay:140}` defines the original cell
and its shared base anchor. `clips` retains rows idle/move/attack/hit/death,
counts 8/8/10/4/10, fps and loop flags. Each clip additionally has ordered `rects`:
`{x,y,w,h,ox,oy}`. Crop `(x,y,w,h)` from the packed atlas; place it at `(ox,oy)` in
the logical 160-square cell, then subtract `(ax,ay)` for world anchoring. Packed
rows have variable heights and widths; consumers must use rectangles, not grid
multiplication. Two transparent pixels separate packed rectangles/rows. Trimming
must never recenter individual frames. `atlas:{w,h}` stores actual packed size.

Keep all 40 frames and 512/256 masters outside git. Alpha is quantized to 16 levels;
RGB is not posterized. The packer searches WebP quality 90/85/80/75 and refuses
anything over 200,000 bytes at quality 75. Validation checks the format, actual
alpha, margins, rectangle bounds, counts, source/grade freshness, clip motion and
held terminal death. This is a technical contract, not painting parity. Only write
`barbarian-scout-PASS` after visual review finds the rest pose hard to distinguish
from the painting and all five clips clean. Round 1 is explicitly not a PASS.
