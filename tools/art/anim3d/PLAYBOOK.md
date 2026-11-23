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

## Siege chapter — howitzer, round 2

The howitzer painting depicts a gun with no crew. Use a rigid mechanical hierarchy
instead of adding people absent from its composition. This unit's isolated scripts
are in `tools/art/anim3d/units/howitzer/`; newer siege and vehicle chapters and the
artillery lane supplied reusable projection/bake/review/delivery code. Shared
spearman entry points are unchanged.

Build a genuinely hollow, short elevated barrel, recuperators, thick bevelled
shield plates, dished twelve-spoke steel wheels, stepped hubs, thick carriage
cheeks, handwheel, bolted trails and a single stationary stone disc. The hierarchy
has carriage, elevation, recoil, wheel and trail controls. Preserve full depth
when matching the painting, and render clay side/front views as well as the hero
view. Key effect visibility, never zero or near-zero scale. Every Blender command
uses plain `blender -b --disable-autoexec` through the PATH gate, sequentially.

Apply all four quality levers: (1) finish bevels and geometry before freezing one
rest-camera projection from the full painting; ray-test visibility and blend
occluded/back faces into the recorded generated painted-metal fill; (2) use real
thickness, bright edges, bolts, hollow muzzle and actual AO/curvature bakes;
(3) warm upper-left product key, soft fill, cool rim and live contact AO;
(4) measure the painting/rest opaque-subject RGB mean and spread, then freeze one
bounded grade for all frames. Standard/None preserves painted pigment already
containing light; this is not the photographic default. Non-camera rays retain the
physical shader. Round 2 fits the solid beveled spokes to source endpoints by intersecting camera
rays with their physical dish planes and constraining their radial extent.
All rotating wheel parts use continuous source-metal swatch paint: the source
wheel occlusions otherwise rotate into visible patchwork. Fixed gun surfaces
keep the frozen painting UVs. Hidden faces use the generated paint fill. Ray tests must
exclude hide_render geometry, or invisible braces incorrectly erase source pigment.
Camera/geometry registration remains approximate, especially around hubs.

The common stone target is warm cream **#E9CFA0**, with a darker warm rim and fine
grain. Convert sRGB pigment to linear shader values (approximately .815/.624/.352)
before lighting; do not pass those byte-normalized sRGB values as linear. Review
actual rendered colour after grade. A separate warm-pigment source mask can texture the disc, excluding gun pixels
and dark stationary wheel shadows; contact shading must follow the gun. Grain
must feed the camera-visible pigment branch as well as the physical shader, or
the emitted stone will remain flat despite having a noise node. At every round write
`howitzer-f-restpose-compare.png`: painting, rest render and 50/50 crossfade at
256 and 64px. The target remains hard-to-distinguish painting parity, not merely a
technically valid atlas. No automatic PASS marker.

Idle/move/attack/hit/death have 8/8/10/4/10 frames at 10/12/14/12/10fps. Idle and move
loop; combat clips are one-shot with an exact final death hold. The move is an
in-place tow cycle: runtime world travel must match wheel radius times angular
speed. Ground checks keep both rims on z=.13 while the carriage reacts; the base
never moves. Read the contact sheet and animation, not just the numerical audit.

**Open-motion standard for crew/animals:** humans use CMU free-use or Quaternius
CC0 idle/walk/hit/death, with matching rest poses and bone rolls during retargeting;
only weapon-specific attacks are authored on top. Quadrupeds use a licensed CC0
animated animal source. Never repair foot direction after retargeting; fix the
forward/rest-axis mapping. Record URLs/licences locally and in external SOURCES.
Every round includes top/front views across the move cycle, `<slug>-g-feet-check.png`,
checking planted contact and forward-facing feet. The uncrewed howitzer has no gait
asset; its actual top/front move renders document wheel contact instead.

Complete host handoff (executable, no arguments, from repo root):

```sh
ROUND=2 tools/art/anim3d/units/howitzer/gpu.sh
```

The script explicitly requires Metal Cycles, rebuilds/bakes and renders every
stage at actual 512px/64 samples, preserves 512 masters and graded 256 derivatives
under `ANIM_ROOT/masters/howitzer/`, publishes all interim reviews, validates
pipeline/model/clip/input/grade/frame hashes and wheel contact, then packs and
checks the atlas and encodes `howitzer-round${ROUND}.mp4`. The movie reconstructs
the decoded trimmed atlas: all five clips, 2x logical scale on cream, 8 seconds,
240 frames, 1600x348, H.264/yuv420p. GPU receipts require actual GPU512 provenance;
CPU512 previews cannot pass that gate. Technical success still requires visual review.

### Howitzer trimmed atlas contract (v2)

`app/src/assets/units/anim/howitzer.webp` uses logical 160px cells, quality >=75,
and <=200,000 bytes. All forty frames remain. Master files never enter git.
The JSON has `version:2`, `layout:"trimmed-rows"`,
`frame:{w:160,h:160,ax:79.375,ay:138.125}`, and five `clips` in
idle/move/attack/hit/death order. Each clip has `row`, `frames`, `fps`, `loop`, and
`rects`: one `{x,y,w,h,ox,oy}` per frame. Rectangles locate cropped atlas pixels;
offsets reconstruct the original logical cell. At display scale s and anchor
(X,Y), draw at `(X+(ox-ax)*s,Y+(oy-ay)*s)`. `row` is ordering, not a fixed cell grid.
Identical held frames share a rectangle. Packing checks exact decoded alpha
reconstruction, every count/offset, motion, quality/size, non-clipping and held death.
This is an unwired art candidate; a v1 fixed-grid runtime cannot read this schema.

Howitzer round-one delivery uses 32-level alpha on the 160px candidate only, with
full alpha retained in 512/256 masters. This matches the existing shared packing
approach and reduces size without dropping any frame or RGB quality below the floor.
The final CPU candidate is 188,042 bytes at Q80; all forty quantized alpha masks
reconstruct exactly. No PASS: moving wheels retain simpler worn-metal surfaces,
carriage/trail and stone still differ from the painting. Never infer GPU success
from the actual CPU512 preview set. Rendering-script hashes protect frames;
postprocessing versions have separate delivery/check receipts so a packing change
does not falsely invalidate or claim a new render of otherwise unchanged masters.

### Howitzer round-two GPU review follow-up

The supplied round-one GPU pass succeeded (187,034 bytes, Q75), but failed the
visual bar: smooth narrow rims/wire spokes, a flat ochre disc and mismatched
lower carriage. Evidence is retained in `masters/howitzer/driver-r1-gpu/`.
Round two adds deeper broad rolled rims, 96 solid rim rivets, beveled rectangular
spokes and sockets, local wheel-plane landmark fitting, generated hidden paint,
masked source stone pigment, and grain in the actual camera-visible shader.
The trail moves toward its painted footprint and the solid flash is less saturated.
No cloth or human/animal motion is applicable to this uncrewed painting.

`prepare.py` checks the source/fill SHA256 pins before build. The GPU entry point
now tees its transcript to the driver's log as well as its own log; round one's
redirect had left the supplied driver log empty despite a successful receipt.
The GPU handoff still rebuilds every stage and refuses CPU evidence. Geometry,
40 frames, trimmed delivery, video and fresh visual comparison must be rechecked;
these improvements do not authorize a PASS marker by themselves.

Source landmarks must also obey the mechanism: a spoke endpoint inferred by
camera-ray/plane intersection may sit outside the real circular rim, because the
painted outline includes tread thickness and perspective. Round two's move audit
caught exactly that (rim z=.243 instead of .13). Clamp the radial extent to the
physical rim and test all angles, including the non-exported loop closure.
Build-time and independent saved-clip audits now check each spoke/socket envelope;
this is necessary even when the rest-pose comparison looks closer.

Do not judge wheel projection only at rest. Even with correct geometry, the
painting's occluded regions become revolving patches. The final round-two wheels
retain object-space source-metal swatch paint and physical lighting; source projection stays
on the fixed gun. A later wheel texture needs completed, occlusion-free painted
surfaces before reintroducing projection. This is still a painting-parity gap.

Round-two CPU512/8 delivery: **174,700 bytes at Q80**, all 40 frames, independent
geometry/provenance/trim checks and 240-frame eight-second movie validated.
Wheel pigment still looks pale/flat and tread banding remains: NOT PASS.
