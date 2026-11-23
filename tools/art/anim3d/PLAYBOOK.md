# Painted 3D unit families

The painting is the quality bar. Sam's verdict on the first family leads was that
"the quality still looks like something a high school student would make."
Finished meshes, a passing audit and a small atlas do not establish art approval.
At rest, the target is a figure barely distinguishable from its painting at both
256 and 64 px. Keep the existing painting in the game until the lead approves.

## Standard method for every family

Load the installed `blender-modeling`, `blender-materials`, `blender-lighting`,
`blender-cameras`, `blender-animation` and `blender-rendering` skills. Their recipes
are starting points; inspect the installed Blender API and the actual output.

1. **Camera projection.** Match the painting's viewpoint, base ellipse, figure
   extent and landmarks before adding detail. Project the full-resolution source
   onto the actual mesh in that rest pose. Freeze UVs before animation so paint
   moves with the surface. Use visibility and facing masks to exclude occluded
   backsides, and feather the seam into image-generated fills in the same style.
   Check hidden areas during motion. A camera-facing cutout or relief plane is
   not a replacement for the articulated model. Painted illumination must not
   receive a second full lighting pass: separate its pigment/illumination layer
   from the physical surface response and report that choice.
2. **Geometry finish.** Bevel hard edges; retain real thickness on straps, cloth,
   armour and shield rims; model buckles, stitched borders and rivets. Subdivide
   organic anatomy and cloth, with actual folds and displacement where useful.
   Match the MPFB face, hands and silhouette to the source. Keep original skin
   weights. Surface noise cannot repair a wrong pose or contour.
3. **Product lighting.** Warm upper-left area key, soft fill, restrained cool rim,
   contact shadow and AO. Start near 5:1 key/fill and tune by the rendered image.
   Use Cycles GPU with denoising for final frames if Eevee looks flat. Preserve
   broad warm highlights and deep recesses without blowing out the base or skin.
4. **Automatic grade.** Fit the painting's opaque-pixel RGB histograms at rest,
   then use that same monotone grade for every clip. Never fit each frame
   separately: it causes colour pumping. Preserve raw renders and alpha, and
   record the calibration source and master hashes. Refit after camera, material,
   light or engine changes, then rerender all dependent clips.

Every iteration emits `<slug>-f-restpose-compare.png`: painting left, render
right, 50/50 crossfade and a split-screen, each at 256 and 64 px. Review motion
strips and playback too: fixed UVs can stretch or expose fill seams away from rest.
A histogram match measures tone distribution, not geometric or artistic fidelity.

### Shared cream base

Every family uses one stationary round cream stone disc: **#E9CFA0 sRGB top**,
**#B68A51 sRGB darker rim**, fine low-contrast grain, roughness about 0.86. Convert
sRGB to linear before setting Blender shader values:

```python
def linear(c):
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
cream = tuple(linear(v / 255) for v in (233, 207, 160)) + (1,)
rim = tuple(linear(v / 255) for v in (182, 138, 81)) + (1,)
```

Never project the full figure painting onto the static base: its painted feet
and shadows would remain when the real feet move. Keep the shared physical
material and render contact shadows.

Lighting and the display transform change its appearance: verify the rendered
base against the painting, not just its shader's colour field. Do not use grey
scan albedo or add an era-metal ring.

## Execution and ownership

All Blender calls use **`blender` on PATH**, always `-b --disable-autoexec`.
The machine-wide gate queues one Blender process, caps it at three threads and
retries crashes. Do not call `/Applications/Blender.app`, pass `-t`, bypass or
remove a live lock, or add a competing lane lock. Run dependent stages sequentially.
Never hide effects with zero or near-zero object scale; use keyed visibility.

`ANIM_ROOT` defaults to `~/LegatumRuns/anim-pilot`. `env.sh` isolates Blender's
resources, config, scripts, data and caches. The installed Blender is 5.3.0
(`02f0899d78e3`). External masters, textures, cloth caches, source paintings and
rendered frames remain under `ANIM_ROOT`; no upload is part of this workflow.
Pillow lives in `$ANIM_ROOT/venv`. The sandbox denies `nice` priority changes and
some thumbnail writes; the PATH gate still controls concurrency and threads.

Start with a short CPU Cycles preview in the sandbox. Host Eevee uses Metal via
`--gpu-backend metal`. Cycles GPU is an explicit separate path:

```sh
RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU CYCLES_BACKEND=METAL SAMPLES=64 tools/art/anim3d/render.sh c
```

Use `CYCLES_BACKEND=OPTIX`, `CUDA` or `HIP` on an appropriate host. GPU selection
is verified; an unavailable GPU raises an error instead of silently using CPU.
`CYCLES_DEVICE=CPU SAMPLES=12` is an explicitly labelled preview. No Cycles GPU
claim is made from a CPU render or an Eevee render.

## Infantry chapter: spearman family lead

The body is MPFB 2.0.18 anatomy: 19,158 base vertices, original face/hands/toes and
skin weights, plus its 53-bone `game_engine` skeleton. No primitive body or
commercial character service is used. Hoplite kit is original code-built 3D
geometry. Software is GPL-3.0-or-later; MPFB/MakeHuman body and system assets are
CC0. PBR scans are CC0 ambientCG Metal034/Fabric030/Travertine001 and Poly Haven
brown_leather/fine_grained_wood. Downloads and licences are pinned in
`assets.lock.json` and `ANIM_ROOT/assets/`. `setup.py` installs the isolated assets.

`scene.py` builds the muscular hoplite, cuirass, open Corinthian helmet bowl,
horsehair crest, convex sunburst aspis, iron leaf blade/butt, ash shaft, greaves,
pteruges, sandals and cloth cape. `helmet.py` adds a curved faceplate with genuine
eye/mouth apertures. `materials.py` applies PBR; `bake.py` bakes real 512 px AO and
Pointiness curvature. Solidify must be disabled for those bakes because generated
inside faces share UVs and otherwise overwrite the visible surface with darkness.
Correct winding before baking. `paint.py` is the earlier shield detail pass;
`finish.py` adds crest fibres and a riveted waist belt.

Round 3's `project.py` applies camera/pose alignment, wider braced ankles, raised
fist, broader leaf blade, head view, flared folded wool, subdivided linen and a
thick beveled leather ribbon. It preserves `projection-input.blend` before edits
and restarts there on repeat runs, so changes do not accumulate. It writes named
rest-camera UVs and a ray-visibility/facing mask to genuine deforming surfaces.
The painted illumination layer blends with physical PBR; backs and undersides
use generated bronze, wool, linen and leather fills. Prompt and hashes are in
`fills.prompt.txt` / `fills.lock.json`; the original grid and quadrant PNGs live
in `masters/spearman-3d-v2/textures/generated/` and are packed into the master.
The source's own painted illumination is intentionally retained, so oblique
poses still require review. The projection is not a general inverse-rendering
solution and does not make imperfect geometry equal to the source.

### Build from sources

```sh
python3 tools/art/anim3d/setup.py
tools/art/anim3d/render.sh build
RENDER_ENGINE=CYCLES CYCLES_DEVICE=CPU SAMPLES=12 GRADE=0 tools/art/anim3d/render.sh b
tools/art/anim3d/render.sh materials
tools/art/anim3d/render.sh bake
tools/art/anim3d/render.sh paint
tools/art/anim3d/render.sh finish
tools/art/anim3d/render.sh project
RENDER_ENGINE=CYCLES CYCLES_DEVICE=CPU SAMPLES=16 tools/art/anim3d/render.sh c
```

Full rebuilds need the external generated fills named above. Rebuilding the
master invalidates all clips and grades. New review images use `spearman-`;
previous round images are retained for comparison. The current round's status
and exact measured results live in `REVIEW.md`, not in this method document.

### Motion, cloth and review

CMU 77_02 standing and 02_01 walking use Bruce Hahne's 2010 MotionBuilder BVH
conversion (research/commercial use permitted). Data came from mocap.cs.cmu.edu;
the database was funded by NSF EIA-0196217. `mocap.py` preserves channel order and
computes forward kinematics; `animate.py` retargets standing torso deltas and
walking legs with an authored shield-bearing guard. Attack, hit and death are
keyed on that same rig. Attack raises outside the right shoulder and slides the
grip on the shaft to retain framing. Death opens the fingers, releases the spear
across the front of the base, folds the legs and settles the shield.

Each clip has one second of cloth pre-roll and a persistent simulation bake.
Light edge pinning keeps the cloak's broad rest silhouette while its middle
moves. Lengths are 8/8/10/4/10 frames at 10/12/14/12/10 fps. Idle and move loop.
Death's terminal sample is rendered **once and copied**, including identical PNG
bytes. Never weaken the pixel-equality check to hide stochastic render noise.

```sh
for clip in idle move attack hit death; do
  tools/art/anim3d/render.sh "animate-$clip"
done
```

### Round 4 registration and lead GPU handoff

`infantry/refine.py` runs before frozen UV calibration. It turns the actual feet
outward, narrows the volumetric crest, registers the raised shield boss/rays to
the painted ornament, and adds fine limestone pigment grain. Relief vertices are seated on the actual convex shell with ray intersections
and explicit keel/boss depth; lateral camera registration alone can bury them.
The old second shield-paint blend is disabled; it was competing with the camera projection.
The visible shell under the relief receives continuous paint instead of PBR
wedges caused by ray occlusion at individual vertices. Painted illumination is
now 96% at fully covered vertices, with 4% physical response; hidden surfaces
retain the existing generated fills. This is still an articulated 3D mesh. Death reduces lower-cape pin weights to
15% while retaining shoulder pins; shield release preserves its original scale.

The one complete **host-only** command, from the repository root, is:

```sh
ROUND=4 tools/art/anim3d/units/spearman/gpu.sh
```

It regenerates all five saved clips and their cloth caches; runs Cycles GPU
(default Metal, 64 samples) at 512 px for plain geometry, rest, details, rig
poses and all 40 frames; fits one rest histogram grade; runs the rig audit and
pipeline tests; exports 512/256 masters; packs and independently validates the
trimmed atlas; and encodes all five decoded clips side by side for eight seconds.
`ROUND` comes from the overnight driver. Unavailable GPU devices fail explicitly.
All Blender calls still use the PATH gate. Final outputs go under
`masters/spearman/{512,256}/` and `review/3d-v2/spearman-*`; editable source,
raw renders, generated fills and cloth caches remain in `masters/spearman-3d-v2/`.
The script never writes PASS: that requires visual review of the GPU output.

For CPU iteration use `RENDER_ENGINE=CYCLES CYCLES_DEVICE=CPU RESOLUTION=256
SAMPLES=12 tools/art/anim3d/render.sh <stage>`, then
`units/spearman/delivery.py pack --preview` with the isolated Pillow Python.
This marks the delivery report as a preview and does not manufacture 512px
masters by upscaling. Rest and clips must share engine, device, resolution and
sample settings. The old root `pack.py`/`validate.py` retain their fixed-grid
contract for older callers; they are **not** the spearman delivery entry points.

### Round 5 fitting and painted color

`infantry/refine.py` now registers the whole volumetric shield outline before
seating its ornament. Relief intersection uses the **evaluated** shell including
Solidify; the raw mesh lies inside the rendered surface at oblique angles and
still buried several rays despite the round-4 depth correction. Review clay
again after any support-surface or modifier change. A smooth rest-view fitting field seats the spear-side
shoulder and shin, and broadens the other sandal's actual toe/sole together.
For weighted anatomy and clothing it inverts each vertex's blended bone matrix
after fitting, preserving MPFB topology, original weights and live articulation.
Rigid footwear uses its bone-parent matrix. These are mesh-coordinate edits,
not a silhouette cutout, alpha mask, or per-frame reprojection.

The source already contains painted illumination. In this specific pipeline,
AgX was compressing that pigment a second time. Standard/None now preserves its
display colors, with the existing 96% pigment / 4% physical mix and one frozen
rest histogram grade. This choice is specific to projected painted illumination,
not a general photographic rendering preset. The warm key is less orange,
the cool fill remains soft, and a low stone-pigment emission contribution opens
the physical rim. No figure/foot paint or static cast shadows enter the base.
Generated bronze/wool/linen/leather fills and beveled straps/folds remain intact.

`ROUND=5 tools/art/anim3d/units/spearman/gpu.sh` is the same complete host
handoff. It first checks for the requested Cycles GPU, then reruns projection
from the preserved clean input, all cloth/animation builds and all render stages.
It retains `ANIM_ROOT/gpu-logs-spearman-r${ROUND}.log` itself unless the driver
already redirects there, and logs the failed stage on error. No prior GPU pass
is inferred from old review files. The round-4 files supplied for round 5 were
CPU-labelled, and the requested round-4 GPU log was absent.

### Round 6 finished-surface projection

MPFB's active macro shape keys override direct `data.vertices` edits. Bake the
current mixed morph on the working projection copy before inverse-skin fitting;
otherwise body corrections can appear in the script without changing a single
rendered foot vertex. Keep the original morphable human in the clean
`projection-input.blend` checkpoint. This retains the 19,158-vertex topology,
original weights and 53-bone rig, and the scene check rejects unfrozen shape keys.

Apply static Solidify/Bevel/Subsurf modifiers on rigid kit **before** frozen UV
calibration. The prior raw-mesh UVs moved when modifiers generated the rendered
surface, visibly doubling the shield's painted rays despite correctly seated
relief. The finished shell, rays, rim, helmet and straps keep their real volume
and bone parenting. Deforming body and cloth keep their original topology and
skin weights. The original AO/curvature and generated unseen-surface fills remain.

Seating only the endpoints of the shield rays was insufficient: their long flat
triangles cut through the convex support between endpoints. Subdivide the actual
rays and intersect every vertex with the evaluated shell, interpolating the
original keel height. Check the finished face centers for penetration as well
as inspecting clay. Painted registration can conceal buried geometry.

The camera now sits at `(2.5, -7, 3.25)`, looking at `(0, 0, 1.20)`, with the
same orthographic scale of 2.90. The lower elevation better matches the source
disc ellipse. The stationary round disc's top is at the `.105m` contact plane
already used by the spear. Shoulder and spear-side toe fitting happens in the
rest view before frozen UVs; no per-frame reprojection or alpha cutout is used.
Foot geometry also moves along the camera ray onto the stone without changing
its painted screen position. Animation uses the actual finished sole underside
to apply small foot-bone contact corrections; airborne feet keep their pose.
The floor audit now derives its threshold from the actual disc top (10mm
penetration tolerance), replacing the old fixed `.07m` limit that missed buried
soles. Check only the disc's actual flat footprint against its top; a released
spearhead outside that footprint does not intersect the stone. The world-ground
check still applies everywhere. Fit the anatomical foot underside inside the
sandal, and correct the folded calf/greave contact in death before baking cloth.
It still is not a full skin/cloth collision solver.

Camera-only painted pigment avoids using the source's illumination as a physical
lamp. Non-camera rays see the original physical material; this retains real
shadows and avoids orange emission spill. Product lights retain their ratios at
55% of the prior energy because Standard has no highlight rolloff. Cream stone
retains physical shading and low-contrast grain, with camera-only pigment to
open its top/rim. Refit one automatic rest histogram grade after these changes.
Inspect the expanded detail sheet's sandals and base as well as head/chest/shield.

`units/spearman/check_scene.py` checks the saved camera-only pigment wiring,
finished rigid surfaces, contact plane, nonzero scales and original body/rig
counts before clip rebuilds. `ROUND=6 units/spearman/gpu.sh` (with the full
`tools/art/anim3d/` prefix) remains the complete GPU handoff. It resolves its own
checkout, defaults ROUND to 6, and writes `spearman-gpu-status.txt` with running,
failed-stage/exit, or complete/pending-visual-review status, alongside the round
log. Missing logs and CPU-labelled images are not evidence of a GPU pass.

### Round 7 arm, neckline and unseen-surface finish

The real spear-side knuckles now have a taller stack, and the whole bent arm
is fitted through inverse skin transforms. The sleeve cap alone cannot fill a
missing upper-arm silhouette. Lower the rear folded collar and weighted cape
neckline behind the helmet instead of hiding its squared outline with alpha.
The near helmet cheek is wider; all these edits retain camera depth and the
original body topology, weights and articulation.

The camera is `(2.5, -7, 3.0)` aimed at `(0, 0, 1.20)`, scale 2.90. The round
stone disc moves 0.20m away from the camera on the ground, with a deeper underside
and unchanged .105m contact top; its radius is reduced by one percent. This fits
the painting's shallow top ellipse and taller edge without flattening the disc.
The death calf contact solver uses the disc's actual local footprint, as the
audit already did; origin-centered floor assumptions fail when a base moves.

`infantry/paint_finish.py` blends the existing generated unseen bronze, wool,
linen and leather, or original tinted MPFB skin, with live ambient occlusion
and 35% physical surface response. Like the source-painted layer, this pigment
is camera-only; non-camera rays retain the original physical BSDF. This reduces
washed-out newly exposed surfaces under the display transform. Frozen source
UVs still move with geometry; this is not per-frame reprojection. Review raised
arms and the final death pose for remaining stretches and seams.

Attack and death interpolate their IK elbow poles from the same guard poles
as idle. Matching hand targets alone does not match the arm pose: a raised or
fallen pole at phase zero produces a visible clip-entry pop.

`ROUND=7 tools/art/anim3d/units/spearman/gpu.sh` is the complete host pass and
now defaults to round 7. Missing round-6 GPU log plus CPU-labelled supplied
images do not establish that a GPU render ran. The script retains its own round
log and stage/status receipt; final 512/256 export and PASS still require actual
GPU output and visual review. The CPU iteration report records measured results.

### Trimmed atlas v2 and checks

`units/spearman/delivery.py` preserves 8/8/10/4/10 frames, real alpha, and the
five logical rows idle/move/attack/hit/death. Every source frame is resampled to
160 × 160, cropped to its nonzero-alpha rectangle, and placed in its clip row
with two transparent pixels on each side. Width and row height are variable.
Encoding tries quality 95, 90, 85, 80, then 75; exceeding **200,000 bytes** at 75
fails without replacing delivery. No frame counts are reduced.

JSON v2 has `version:2`, `atlas:{w,h}`, `frame:{w:160,h:160,ax:79.375,ay:138.125}`,
unchanged `clips:{name:{row,frames,fps,loop}}`, and
`frames:{name:[{x,y,w,h,ox,oy},...]}`. `x/y/w/h` is the source rectangle in the
packed atlas; `ox/oy` is its offset in the untrimmed 160px frame. Draw the crop at
`anchor + (ox-ax, oy-ay) * scale`. Consumers must use the explicit rectangles,
not infer fixed-cell positions from `row`. The game still displays its painting;
this task does not enable the animation renderer.

Validation checks current master/clip/grade/frame hashes, 40 records, clip timing,
packing bounds and gutters, exact decoded alpha reconstructed at each offset,
transparent padding, camera margin, visible motion, byte cap, quality, and
identical held-death source PNGs. `spearman-delivery.json` records the encoded
quality and hashes, `spearman-validation.json` the result. Decoded atlas pixels
feed both `spearman-g-decoded-atlas.png` and the movie; ffprobe checks H.264,
yuv420p, 1600 × 352, 192 frames and 8 seconds. PNG strips and rest comparisons
show the native 256 and 64 px views, not upscaled visual-quality evidence.

`audit.py` checks all 40 samples for original body/rig topology, persistent cloth, stationary base, floor
and camera bounds, hand/shaft distance and spear centerline intersections against
shield, cuirass and helmet. It is not a full cloth/skin collision solver.
`AUDIT_CLIP=attack tools/art/anim3d/render.sh audit` narrows an iteration check.
Run Python/Bash syntax, whitespace and repository hygiene at completion; no
Rust/WASM/app tests are needed for art-only changes. The lead still runs the
browser/art gate and Claude art review before integration.

Non-obvious findings: preserve outward normals and the authored bake surface;
read projected weapon length as well as world-space clearance; use one camera
through calibration and clips; freeze the grade across animation; duplicate a
held render rather than render the same simulation sample twice. Keep the
spearman checkout on `astra/unit-anim-3d-v2`; the siege lane has a separate tree.
