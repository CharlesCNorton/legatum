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

## Infantry chapter: pikeman rounds 1–2

Pikeman is isolated in `tools/art/anim3d/units/pikeman/`; it reuses the MPFB
installation and reviewed newer infantry helpers, with an original steel harness
instead of hoplite or barbarian kit. Full-depth breastplate, limb plates, fluted
tassets, kettle helmet, leather belts and two-handed pike retain real thickness,
bevelled edges and the MPFB 53-bone skeleton. External assets and editable masters
live in `ANIM_ROOT/assets/pikeman` and `ANIM_ROOT/masters/pikeman`.

This chapter supersedes the older fixed-grid/authored-motion instructions above
for this unit. All Blender calls are plain `blender -b --disable-autoexec` on PATH;
the shared gate owns slots and threads. Never call an application binary directly,
create another heavy-process lock, or hide an object with near-zero scale.

The four quality levers are mandatory: align physical geometry and camera before
freezing painting UVs; finish surfaces with thickness, bevels, folds and detail;
use warm upper-left product lighting with soft fill/cool rim/contact AO; fit one
automatic foreground histogram grade at rest and reuse it for every frame. The
projected painting's illumination is camera-only, at 96% pigment/4% physical
response where visible; unseen surfaces retain physical materials and generated
linen/steel brushwork (the generated bronze fill is desaturated in the shader). Standard/None preserves the source pigment here, rather than double-toning
it with AgX. Projection uses ray visibility and facing masks and never changes
geometry opacity or updates UVs per animation frame. Actual AO and Cycles
Pointiness maps supply metal cavity/roughness variation. The stationary stone
uses #E9CFA0 sRGB top pigment with a darker rim and fine grain; no painted feet or
static foot shadows are projected onto it.

At every round compare painting/render/half-split/50% crossfade, at 256 and 64 px,
in `pikeman-f-restpose-compare.png`. It is a visual judgment, not a claim that
matching a histogram or passing an audit establishes art approval.

### Open motion and foot check standard

Humans use CMU free-use mocap or Quaternius CC0 motion for idle, move, hit and
death. Pikeman uses Quaternius Standard `Idle_Loop`, `Walk_Loop`, `Hit_Chest` and
`Death01`, with Blender world-space COPY_ROTATION constraints calibrated using
reference/rest matrices and bone rolls. Locomotion leg axes are matched in the
calibration pose. Never hand-correct foot rotations after retargeting. Two-hand
weapon carrying uses IK constraints over the captured body motion; only the pike
thrust is authored. A source-derived root correction stabilizes planted walking
feet against virtual travel; vertical contact moves the root, not foot rotation.
Animals in other chapters must use CC0 animated quadruped motion as their default.

Every round renders top-down and front views across all eight move samples into
`pikeman-g-feet-check.png`. Check that feet point along the rig's -Y travel axis,
roll naturally, and keep a constant stance speed relative to virtual ground.
An in-place walk has rearward stance travel in the token's coordinate system.
The diagnostic records ankle/toe coordinates and forward-axis dot products.
Licences and pinned external hashes are unit-local and in `assets/SOURCES.md`.

### Rebuild, preview and complete GPU handoff

```sh
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/pikeman
"$ANIM_ROOT/venv/bin/python" "$unit/prepare.py"
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/anatomy.py"
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/build.py"
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/bake.py"
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/animate.py"
STAGES=b-plain,c-textured-lit,c-details,d-rig-poses,e-idle,e-move,e-attack,e-hit,e-death \
  CYCLES_DEVICE=CPU RESOLUTION=256 SAMPLES=8 "$unit/render.sh"
CYCLES_DEVICE=CPU blender -b --disable-autoexec --python-exit-code 1 --python "$unit/feet.py"
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" --resolution 256
"$ANIM_ROOT/venv/bin/python" "$unit/validate.py"
```

The host/overnight driver runs exactly `ROUND=2 tools/art/anim3d/units/pikeman/gpu.sh`
from the repository root. It checks Metal explicitly, rebuilds all five clips,
audits them, renders all stages and 40 transparent frames in Cycles GPU at 512,
renders the feet diagnostic, exports native 512/downsampled 256 masters under
`graded/`, packs/validates 160 px delivery, and writes an eight-second five-column
H.264 yuv420p `pikeman-round${ROUND}.mp4`. It records status, log and a GPU-only
receipt, and fails rather than pretending a CPU render was a GPU pass. It never
writes PASS automatically; that needs visual confirmation against the painting.

### Trimmed atlas format

`pikeman.webp` uses logical 160 × 160 cells, WebP quality >=75 and <=200,000 bytes.
JSON version 2 keeps `frame:{w,h,ax,ay}` and clips in idle/move/attack/hit/death row
order, with counts 8/8/10/4/10. Each clip has `row,frames,fps,loop,rects`; each rect
is `{x,y,w,h,ox,oy}`. Crop that atlas rect, place at `(ox,oy)` in the logical cell,
then anchor by `(ax,ay)`. Duplicate terminal death frames share one rect to ensure
identical decoded pixels. Source/master/render hashes reject stale or mixed
outputs. The existing runtime is unchanged; this is an animation candidate.

### Pikeman round 2: GPU critique and surface correction

The round-one GPU pass succeeded at 177646 bytes / quality 90. The images exposed
helmet/forearm silhouette overhangs, a disconnected raised grip, a smooth thick
stone rim, and simple gray/skin patches revealed by the death clip. The original
GPU sheets and movie are retained externally in `review/3d-v2/pikeman-round1-gpu`.

Round two uses all six Blender skills. A swept helmet brim, raised carrying grip,
fitted breastplate and bounded upper-body contour field align the finished volume
before freezing UVs. Camera depth and anatomical weights are preserved; no alpha
cutout or per-frame reprojection is used. The contour field excludes leg garments
and rejects unstable inverse skin transforms. Cloth has normal-displaced folds;
garment weights are restricted to the garment's anatomical region. Applied
Bevel/Subsurf produced negative deform weights (observed -0.949), so every
finished skinned mesh clamps and normalizes weights before pose evaluation.
The scene audit rejects negative or unnormalized weights; this removed a
metre-long trouser spike that the atlas margin check correctly rejected. The continuous underlying body uses
clothing, gloves and boots on the appropriate regions instead of skin everywhere.

Unseen surfaces use the recorded generated Tagmatic steel/leather and Medjay skin
fills, with box mapping and physical product lighting. Six Cycles AO/Pointiness
bakes remain part of the rebuild. A new generated clean stone top removes boots
and their shadows; it textures the real thinner bevelled disc with frozen
`CleanStoneCamera` UVs. The original unobstructed lower rim is retained, and live
AO supplies moving contact shadows. Texture alpha never cuts the geometry. The
one rest-fitted histogram grade is still reused across every clip.

After the final bake and CPU review, run the virtual-environment Python on
`units/pikeman/provenance.py --seal`. The no-argument `gpu.sh` checks that exact
master/script/texture seal before its full GPU pass. The seal uses portable keys
so a different checkout of the same scripts can render the reviewed master.
The GPU receipt and PASS remain distinct: a valid 40-frame atlas is not a visual
approval of glove contact, plate seams or the rest-pose match.
