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

## Settler: infantry/civilian round-1 lane

The settler implementation is isolated in `units/settler/`. It reuses the spearman
MPFB 2.0.18 installation, 53-bone game-engine anatomy/weights and `env.sh`, but
builds a female traveller and original civilian kit: linen hood and robes, olive
wrap, rust shawl/fringe, strapped pack, spiral blanket roll, sandals and staff.
There is no copied hoplite equipment, image plane, or displaced painting relief.
The skirt has complete circumference and physical thickness. A non-destructive
body mask culls upper legs fully covered by that opaque garment, preventing stride
poke-through while retaining the source anatomy. Cloth folds and hem
follow-through are authored; this lane does **not** claim a cloth simulation or
motion-capture retarget. The five editable clips retain 8/8/10/4/10 samples.

All six installed Blender skills informed modeling, materials, cameras, lighting,
animation and rendering. In particular: bevels and real strap thickness; fully
metallic brass versus dielectric textiles; a warm upper-left key, soft fill and
cool rim; frozen orthographic rest camera; clamped Bezier rig keys and exact loop
closing keys; low-sample CPU previews with visual inspection before GPU delivery.
Every invocation is plain `blender -b --disable-autoexec` through the PATH gate,
with no private executable, extra lock, thread override on the command line, or
near-zero-scaled hidden effect. One owned process runs a complete serial round.

### Painting and surface standard

Follow feedback 18's four levers: (1) align geometry to the painting and project
its brushwork through frozen evaluated-rest-camera UVs onto the real deforming
mesh, with facing and material-region masks; (2) finish the geometry with thick
folded textiles, rounded straps, stitches, fringe, a relief clasp and real blanket
spiral; (3) light as a painted miniature with contact shade and AO; (4) derive a
bounded monotonic RGB transfer from the rest render and reuse the **same** grade
for every frame. A single alpha-bounds-derived orthographic framing transform,
frozen from the rest pose, also matches painting height/centre; raw renders stay
untouched. Never fit individual animation poses or match histograms independently
per frame. Unseen areas
use generated ivory/olive/rust/leather fills, blended beneath the projection.
Ten actual 256 px AO/Pointiness curvature maps for skirt, olive wrap, hood, shawl
and clasp are retained in `masters/settler/textures/baked/`; they drive cavity
shade and roughness. Painted light is deliberately retained in the projected
colour with a small Principled emission contribution, so this is fixed-view art,
not a neutral PBR asset suitable for arbitrary lighting without another review.

The shared stone target is displayed sRGB **#E9CFA0**, with a darker rounded rim.
The settler uses linear warm pigment `(.92,.66,.36)`, roughness `.87`, fine grain,
and a small warm emission contribution. These shader values are not sRGB values;
judge actual rendered pixels under the scene's lighting and AgX transform. The
base is one stationary low disc, never an animated part of the rig.

`settler-f-restpose-compare.png` shows painting, render, half-split and 50/50
crossfade at 256 and 64 px. The near-indistinguishable target is a judging bar,
not a claim made by writing a file. The current round remains a review candidate.

### Reproduction and host handoff

All downloads, generated fills and masters stay under `~/LegatumRuns/anim-pilot/`.
`assets/SOURCES.md` records origins/licences and the fill prompt is checked in.
`prepare.py` registers the source painting and crops the generated fill sheet.
The saved `.blend` files pack their images. No account or paid service is needed.

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/settler/prepare.py
UNIT=settler SAMPLES=8 tools/art/anim3d/render.sh rebuild
UNIT=settler tools/art/anim3d/render.sh pack
UNIT=settler tools/art/anim3d/render.sh validate
```

`rebuild` runs build/plain review, materials/bakes, rest/detail review, all five
animation masters, rig poses, all strips/WebPs, then the saved-geometry audit.
Stage images publish immediately under `review/3d-v2/settler-*`. `build`,
`materials`, `animate`, `b`, `c`, `c-details`, `d`, `e-<clip>` and `audit` can also
run separately. Rebuilding invalidates downstream hashes; regenerate all stages.
Read `review/3d-v2/settler-FEEDBACK.md` if present before another iteration.

For the lead's GPU rerender, preserve the saved geometry/material/animation work:

```sh
UNIT=settler RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64 tools/art/anim3d/render.sh final
UNIT=settler tools/art/anim3d/render.sh pack
UNIT=settler tools/art/anim3d/render.sh validate
```

`final` renders rest first to establish the grade, then details, rig poses and all
five clips, and audits. GPU Cycles explicitly selects Metal with denoising and
fails if absent. `RENDER_ENGINE=BLENDER_EEVEE` supports a host comparison; CPU
Cycles is the sandbox default. Masters render at 512 px; graded 512 and 256 sets
remain in `masters/settler/frames-{512,256}/`. Review the new GPU pixels before
adopting the candidate. Successful packing does not mean art approval.

### 160 px atlas extension (version 2)

The existing `frame:{w,h,ax,ay}` and `clips:{name:{row,frames,fps,loop}}` remain.
For this unit the logical cell is 160×160, anchor `(79,138)`, grid 10 columns × 5
rows. Each clip adds `trim`, one record per sample:

```json
{"x":160,"y":0,"w":82,"h":145,"dx":40,"dy":8}
```

`x,y,w,h` is the rectangle in the atlas. `dx,dy` restores its origin in the logical
160 px cell. A renderer draws it at `(dx-ax,dy-ay)` relative to the token anchor.
The crop is stored at its grid-cell top-left; the rest of the cell is transparent.
This preserves row/clip indexing while requiring a trim-aware consumer. The lane
adds **no runtime wiring**, so the existing static painting stays in use until
art approval and atlas-consumer integration. The example values above illustrate
the schema; actual offsets are measured from every frame's alpha.

The packer keeps all 40 frames and searches WebP quality 90/85/80/75, with 16 alpha
levels, refusing output over 200,000 bytes at quality 75. It records blend, grade,
raw-frame, 512/256-frame and delivery hashes. The validator checks clip lengths,
trim bounds/restoration, transparent margins and padding, decoded motion, held
death, size/quality and 40 masters at both sizes. The decoded-atlas sheet is also
published for visual review. The 3D audit checks 53 bones, stationary base, actual
motion, exact loop closure/terminal death and ten bakes; it records ground and
camera bounds, but is not an exhaustive skin/cloth collision solver.
