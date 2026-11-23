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

## Infantry / two-handed pikes — barbarian pikeman round 1

This unit lives entirely in `units/barbarian-pikeman/`; its external assets and
masters live under `ANIM_ROOT/assets/barbarian-pikeman` and
`ANIM_ROOT/masters/barbarian-pikeman`. It uses MPFB 2.0.18's anatomical body and
53-bone game_engine skeleton with original quilted gambeson, trousers, boots,
kettle helmet, straps, buckle, rivets and red arm tie. It has no shield. Keep the
painting's unusually long diagonal shaft and small figure within the same camera.
All Blender commands use plain `blender -b --disable-autoexec` on PATH, so they
participate in the shared gate. Do not pass a private thread count or bypass it.

The four standing quality levers are the standard method: (1) register the full
painting to the token, match the rest pose, then freeze camera UVs on real geometry;
(2) finish geometry with thick cloth, quilt displacement, rounded hard edges and
real fittings; (3) warm upper-left product key, soft fill, cool rim and contact AO;
(4) derive one monotonic foreground histogram grade from the rest render and apply
that same grade to every frame, avoiding temporal color pumping. Facing and alpha
masks fade projected color into the existing generated linen fill on hidden cloth.
The fill reuses the mounted family's recorded imagegen asset; unpainted leather,
metal and skin retain procedural materials. These still need richer unseen-side
painting. Projection carries painted lighting and cannot repair misaligned anatomy.

The common stone material targets displayed sRGB **#E9CFA0** (linear pigment
approximately `.815, .624, .352`) on one low disc. Use a darker bevel/side through
lighting, fine grain and contact shadows. Judge the displayed material after
lighting and the fixed grade; linear pigment alone is not color calibration.

```sh
source tools/art/anim3d/env.sh
UNIT_DIR=tools/art/anim3d/units/barbarian-pikeman
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/prepare.py"
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT_DIR/anatomy.py"
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT_DIR/build.py"
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT_DIR/bake.py"
SAMPLES=8 "$UNIT_DIR/render.sh"
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT_DIR/animate.py"
STAGES=c-details,d-rig-poses,e-idle,e-move,e-attack,e-hit,e-death SAMPLES=8 "$UNIT_DIR/render.sh"
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/deliver.py" --resolution 256
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/validate.py"
```

`anatomy.py` creates the isolated anatomy master and bone inventory. Only the
`body` vertex group may contribute to fitted shells: disabling MPFB's helper mask
for UV projection must not copy its hidden skirt/fit helpers into clothes.
`bake.py` writes six real 256 px Cycles AO/Pointiness maps for the coat and
helmet, then uses cavity AO in pigment and curvature in roughness. Solidify is
disabled during baking to avoid shared inside/outside UV contamination.
Projection UVs evaluate the rest armature but temporarily disable topology-changing
modifiers so loop indices remain valid. Preserve the separate unprojected master.

Idle/move have an extra unshipped closure key; output remains 8/8/10/4/10. Both
hands solve against the same pike control during guard, walk, thrust and recoil.
Death releases it, tips it into depth, collapses the skeleton and holds the final
two output frames. These are authored keys, not motion capture or cloth simulation.
The ribbons follow the arm rig. Inspect grip, knee deformation and contact visually;
the validator is not a complete collision solver.

The executable **`units/barbarian-pikeman/gpu.sh`** is the no-argument host handoff.
It renders all stages with Cycles Metal and denoising at 512 px, keeps raw masters,
creates graded 512 and downsampled 256 masters, all review PNG/WebP images, the
required `barbarian-pikeman-f-restpose-compare.png`, validates the atlas and writes
`barbarian-pikeman-round${ROUND}.mp4`. It refuses a missing Metal device rather than
silently falling back to CPU. The MP4 reconstructs trims before placing all five
clips side by side at 2x scale for eight seconds in H.264/yuv420p. CPU preview
manifests explicitly say CPU/256; they are not 512 masters or GPU approval.

### Pikeman trimmed atlas contract (version 2)

The shipped WebP has 160 px **logical** frames, all 40 original samples, lossless
8-bit alpha and RGB quality chosen from 90/85/80/75 under 200,000 bytes. Physical
packing has one row per clip, in idle/move/attack/hit/death order; rows and columns
are variable size because transparent margins are removed. JSON retains
`frame:{w,h,ax,ay}` and `clips:{name:{row,frames,fps,loop,rects}}`, plus
`version:2, atlas:{w,h}`. Each rect is `{x,y,w,h,ox,oy}`: crop `(x,y,w,h)` from the
atlas and draw at `(ox,oy)` within the logical frame. Apply the shared `ax,ay`
anchor to that reconstructed frame, not to the trimmed rectangle. This branch
adds the candidate asset only and does not change runtime loading.

Packing checks master/clip/render hashes. Validation reconstructs every decoded
frame, compares its exact alpha with the master, checks borders, counts, motion,
held death and the byte/quality caps. Reviews include painting versus render at
256 and 64, details, four attack poses, every clip strip, and a half split plus
50/50 crossfade. No successful validation writes PASS; that requires a separate
visual judgment that the rest pose is hard to distinguish from the painting.

### Pikeman round 2: finished geometry, garment weights and handoff receipts

Resume from `.worktrees/barbarian-pikeman-round2` on the pikeman branch. The
runner reassigned lane-17 to artillery during this round after preserving WIP
`57e4b781`; do not switch that active artillery checkout back. No shared family
scripts were changed.

`surface.py` freezes static MPFB macro shapes and applies geometry modifiers
before `projection.py` records UVs, retaining the native armature and skin weights.
Fitted sleeves/trousers/boots select original anatomical bone regions and inherit
**exact source vertex weights**. Height-only shell selection copied hands into
trousers, while nearest-point weights after inflation attached sleeve edges to
finger bones and produced spikes. Correct source membership before adding detail.
The forward elbow pole, wrists, knees, feet and rear clavicle now fit the source
more closely; the animation solver uses those same rest targets. A small solid
brim contour correction preserves camera depth and bone parenting.

Projection uses finished geometry, a BVH visibility test, facing/source alpha,
and frozen rest UVs. Camera rays receive 96% painted illumination; other rays
retain physical materials so the source paint does not become a lamp. Standard/
None preserves this painted illumination, instead of compressing it through AgX
again. Existing generated linen fills, thick cloth, straps, buttons, beard,
product lights and six real AO/Pointiness bakes remain. The slender pike shaft
uses continuous ash pigment because a subpixel source-axis mismatch made its
projected colour broken and pale. This exception is not an exact axis-match claim.

The stone is a real stationary disc with a five-segment bevel, low bump and a
normal-dependent cream/rim pigment, live AO and physical shading. It no longer
projects the full figure painting; static boot marks must never remain on a base
when animated feet leave it. The normal-dependent camera pigment opens the stone
without illuminating the figure. Its front edge still needs visual refinement.

The automatic 17-quantile grade remains fixed across all clips and now records
rest/reference/master hashes. Final packing refuses mixed render settings and
stale clip masters; interim review skips stale stages. The 160px reduction uses
bicubic with lossless alpha, avoiding Lanczos perimeter ringing. Exact duplicate
frames share a rectangle within their clip row without changing frame counts;
the validator now requires identical decoded RGB as well as source pixels for
the final death hold. The split/crossfade sheet includes native 256 and 64px views.

The executable no-argument `units/barbarian-pikeman/gpu.sh` resolves its checkout,
defaults to round 2 / Cycles Metal64 / 512px, verifies scene/device, rebuilds clips,
audits, renders all stages, packs, validates and writes the trim-aware eight-second
round MP4. A retained transcript, failed-stage status and fresh success receipt
make interrupted passes distinguishable from completion. `check_delivery.py`
requires actual GPU512 manifests, matching blend hashes, every 512/256 master and
the probed H.264/yuv420p movie. CPU previews cannot produce that receipt. The host
GPU pass remains required; technical success never writes the art PASS marker.


### Pikeman driver round 2 after the successful round-one GPU pass

The actual round-one GPU pass succeeded (175552 bytes, Q90); preserved review
images, receipt and movie are in `masters/barbarian-pikeman/driver-r1-gpu/`.
The log distinguishes that driver round from the earlier CPU refinement rounds.

The current standard for humans is open motion first: CC0 Quaternius Universal
Animation Library Standard supplies Idle_Loop, Walk_Loop, Hit_Chest and Death01.
These are authored library actions, not mocap. `retarget.py` calibrates native
Blender rotation constraints in reference/rest space including bone roll. The
weapon-specific thrust remains original; both wrists follow one rigid pike
control. Move uses source leg rotations without post-retarget foot rotation
patches, with small root translations to stabilize sampled toe stance. Death
blends out of the painted guard, releases the pike and holds the last two frames.
Source, licence and derived image hashes are pinned in `assets.lock.json` and
verified before a GPU pass. Full attribution is in unit-local `SOURCES.md`.

Always render the complete move cycle from front and top, saved as
`barbarian-pikeman-g-feet-check.png`. The top view clips above the knees so the
actual boots remain visible. Audit sampled forward foot direction and stance
translation numerically; inspect heel/toe contact and loop seams visually too.
This is the standard walking review, not a substitute for animation judgment.

Hidden garment faces use the existing image-generated linen via blended box
mapping, cavity pigment and raised diagonal quilting. Source-colored stone on
boot edges is masked rather than carried onto the rolling toes. The cream disc
is shallower, has a tighter bevel and brighter fine-grained rim. Only its clean
front region below token y225 receives painting UV color, fading in over three
pixels; all vertices above that cutoff or with upward normal z > .35 have zero projection mask, so the top
retains live contact shading without fixed painted boots.

The same fixed 17-quantile grade applies to every frame. GPU handoff now includes
the front/top feet stage and requires its 512/256 masters in the receipt. All
Blender invocations still run sequentially through plain `blender` on PATH.
Technical success never creates PASS; rest and all five clips still require
visual parity with the painting.
