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

## Mounted / knight — round 1

The knight-specific implementation is isolated in `units/knight/`. It reuses the
mounted family's CC0 Quaternius Horse, original horse actions, MPFB CC0 anatomy,
geometry helpers, reference-pose fitting and finished-surface projection. It adds
fitted mail, greathelm, curved thick heater shield, upright striped lance,
scalloped caparison and blue mantle. These are real curved 3D surfaces with
physical thickness, not cards. Unseen surfaces use the mounted family's recorded
original generated fills. Source hashes and licences are in `sources.lock.json`
and `SOURCES.md`; assets, blends, textures and masters stay under `ANIM_ROOT`.

All six Blender skills were used: modeling (bevel/thickness/subdivision),
materials (paint, metal and cloth variation), lighting (warm key/cool rim/fill),
cameras (orthographic painting registration), animation (source action sampling,
reference pose and bone rolls) and rendering (serial Cycles, alpha, retained
sequences and checked encoding). Always invoke plain `blender -b` through PATH;
the machine gate owns thread counts and shared slots. Never run the app binary,
start another heavy process of your own, or use zero scales to hide geometry.

The four standing quality levers are the standard for this unit: first register
full-depth geometry to the painting, then freeze its camera projection into UVs;
finish edges/straps/cloth before projection; use product lighting with physical
contact shading; fit one histogram grade from rest and reuse it for every frame.
The cream stone target is sRGB **#E9CFA0**, converted to linear shader values.
Camera-only painted illumination avoids lighting the painting twice, while the
physical shader still casts shadows. Generated linen/metal/hair fills cover
unseen surfaces. Current cavity shading uses live AO;
round 1 does not claim fresh baked AO/curvature maps. The native 256/64 rest
comparison, split and crossfade are the judge, not script completion.

### Open motion and walk inspection standard

Use licensed open motion by default: CC0 Quaternius or free-use CMU for humans;
CC0 animated quadrupeds for horses and other animals. Match reference pose and
bone rolls before retargeting. Never hand-rotate feet afterward to repair an
axis mismatch. Only weapon-specific attacks are hand-keyed. Every round renders
front and top views across the full move cycle to `<slug>-g-feet-check.png`;
check travel direction, planted-foot contact and sliding before approval.

The knight samples the horse's Idle, Walk, Gallop, Idle_HitReact_Left and Death.
Its human torso uses Quaternius UAL Sitting_Idle_Loop, Hit_Chest and Death01,
retargeted relative to each initial pose with bone-roll alignment. The seated
pelvis, legs and equipment grip remain constrained; this is not full-body
walking retargeting. The horse retains original foot rotations. A whole-horse
floor correction and trajectory audit are present, but are not a proof of
foot-slide-free gait. Caparison and cloak are bone-driven, not simulated cloth.

```sh
# Run serially from the repository root. CPU checks use small Cycles renders.
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/knight/preflight.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/knight/prepare.py
for stage in build kit paint motion animate; do
  tools/art/anim3d/units/knight/run.sh "$stage"
done
CYCLES_DEVICE=CPU RESOLUTION=256 SAMPLES=8 \
  STAGES=b,c,d,e-idle,e-move,e-attack,e-hit,e-death,g \
  tools/art/anim3d/units/knight/run.sh render
tools/art/anim3d/units/knight/run.sh audit
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/knight/delivery.py all --resolution 256

# Complete lead-side GPU pass, no arguments; fails if Metal is unavailable.
ROUND=1 tools/art/anim3d/units/knight/gpu.sh
```

The GPU entry point verifies sources and Metal first, rebuilds, renders all
stages at 512 px with at least 64 Cycles GPU samples and denoising, retains raw
and graded 512/256 masters, writes every review image, packs/validates the atlas,
and writes `knight-round${ROUND}.mp4`. The movie decodes trimmed rectangles onto
160 px canvases before 2x display: five clips side by side on cream, 240 frames,
eight seconds, H.264 yuv420p. It never writes PASS. Failure/completion status and
full logs are in `masters/knight/`; completion leaves `art_approved:false`.

### Knight atlas v2 and validation

`app/src/assets/units/anim/knight.{webp,json}` retains 8/8/10/4/10 frames in
idle/move/attack/hit/death order, with 160 px untrimmed canvases, one-pixel empty
gutters and per-frame alpha trimming. Quality is selected from 90/85/80/75 and
the writer refuses anything over **200,000 bytes**. RGB is not quantized; alpha
uses 32 levels (at most 5/255 rounding error).

JSON has `version:2`, `layout:"trimmed-rows"`, `frame:{w:160,h:160,ax:79,ay:144}`,
`atlas:{w,h}`, and `clips:{name:{row,frames,fps,loop,rects:[{x,y,w,h,ox,oy}]}}`.
A rectangle is cropped from atlas `(x,y,w,h)` and pasted at `(ox,oy)` on its
160 px canvas. Direct placement relative to the unit anchor is
`(ox-ax,oy-ay)`. `row` identifies semantic clip order, not a fixed pixel stride.
No runtime loader is enabled or changed by this candidate. The two terminal
death entries share one identical rectangle to prevent lossy block compression
from creating a false flicker; both frames remain present in the ten-frame clip.

Validation requires current blend/frame/grade/atlas hashes, all forty frames,
matching timing, exact decoded trimmed alpha, non-overlap/bounds, transparent
margins, actual motion, held final death and size/quality limits. It cannot
certify cloth collision freedom or painted parity. Keep `knight-PASS` absent
until the rest pose is hard to distinguish from the painting and all clips are
clean at both review sizes.

### Knight driver round 2

Round-one GPU evidence is preserved externally in `masters/knight/driver-r1-gpu/`.
It exposed two separate failures: visible geometry registration errors and a
terminal-death validation failure. Repeated source frame numbers now reuse the
same rendered PNG within each view, rather than invoking stochastic Cycles and
denoising twice. The packer then aliases the identical death hold rectangle;
validation still requires exact decoded equality. Never weaken the hold check.

`refine.py` fits the actual curved cloth and weighted lower legs before freezing
camera UVs. Static curve trim is finished and registered with its parent surface:
otherwise a fitted helmet can still have a floating original rim, or a fitted
horse can retain black mane wedges. The helmet now has a shallow closed crown;
shorter folded caparison surfaces reveal the actual legs rather than carrying
painted duplicates. Tail locks are full-depth meshes attached to the native tail
bone and receive the same visibility-tested source pigment. Steel and leather
fills reuse the pinned original Tagmatic Soldier generated materials. The stone
has normal-driven top/rim colour, fine grain and live contact AO. No fresh
AO/curvature bake is claimed.

`contacts.py` adapts the inspected cataphract helper: vertical bind-space mesh
correctives preserve native source hoof lift. A translation-only footprint
constraint keeps the fitted soles within the stone disc; every source foot
rotation remains unchanged. Corrections re-evaluate the deformed sole because
a different vertex can become lowest after fitting. The reference's raised foreleg remains raised
in idle. This addresses floating soles introduced by silhouette fitting; it is
not a complete stride/foot-slide solver. Death uses the whole-body floor solver,
with rider hands settling onto the evaluated horse after lance release. Cloth
is still bone-driven, and the collapsed cloth silhouette still needs review.

The plain stage now renders `knight-sculpted.blend` so it shows the same finished
geometry as the painted stage. Each clip stores the painted-master hash, and
rendering refuses a stale clip. GPU status invalidates older validation/movie
receipts before starting. For the next full host pass run:

```sh
ROUND=2 tools/art/anim3d/units/knight/gpu.sh
```

The entry point rebuilds and renders all stages, including the sixteen front/top
feet samples, then grades, packs, validates and encodes the eight-second movie.
Current CPU previews remain review candidates, not a Metal or art sign-off.
