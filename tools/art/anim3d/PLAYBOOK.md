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

### Open motion standard — every unit (Sam, feedback 23)

Use proven open motion as the default. Humans use CMU (free use) or the free
Quaternius Universal Animation Library (CC0) for idle, move, hit and death.
Retarget through Rokoko's free add-on or Blender's native constraints and baking.
Match the source T-pose/rest pose to the target anatomy and carry complete bone
rotations, including roll. Positions or a single bone direction do not preserve
roll. Keep only the weapon-specific attack hand-keyed, starting and ending on the
new idle. Holding a weapon may require a constant upper-body reference offset;
record it rather than replacing the source motion with invented keys.

For horses, elephants and other animals, use a CC0 animated quadruped (for
example Quaternius animated animal packs), retargeted or as the weighted base.
Idle, walk/gallop and death come from its open actions. Motion licences for this
public repository are **CC0 or CMU free use only**: no Mixamo or paid animations.
Record exact source URL, version/commit, file hash, action and licence in both
`units/<slug>/SOURCES.md` and external `assets/SOURCES.md`.

Never hand-correct foot orientation after retargeting. Fix the rest-pose/roll
mapping instead. Do not camera-ray-shift, widen or twist foot meshes to imitate
a painted footprint. Small contact translations are allowed; measure their
size. Every round renders actual feet from above and from the front over the
whole move cycle to `<slug>-g-feet-check.png`. Check their heading against the
rig's documented forward axis and check planted-foot slip, including the loop
seam. An in-place walking atlas needs a documented virtual root velocity for
this test: backwards stance travel is expected, lateral drift or variable
planted-foot speed is not. Inspect rendered sole geometry as well as bones.
A source label, a successful bake or a still image alone is not a clean-walk pass.

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

Round 9 replaces the earlier partial CMU direction reconstruction with the
CC0 Quaternius Standard actions `Idle_Loop`, `Walk_Loop`, `Hit_Chest` and
`Death01`. `infantry/retarget.py` imports the glTF with Blender, calibrates full
rest/reference matrices (including roll), then samples native world-space Copy
Rotation constraints. Blender's `Bone.convert_local_to_pose` bakes each visual
matrix with its sampled parent, avoiding stale-parent dependency updates.
Locomotion legs match the source T-pose axes while retaining MPFB roll; a
Blender NLA layer supplies `Idle_Loop` arms over the unarmed walk. The upper
body uses constant reference offsets into the spear/shield guard. The hand-keyed attack
starts and finishes at that idle reference. Equipment release remains authored.
Death blends from the guard into the fully rest-matched open action over its
first 18 percent; it does not carry the guard's arm/leg offsets through the fall.
Hit samples the open recoil then blends back to the same idle over its final
third, so the four-frame reaction does not snap out of a held wounded pose.
Exact provenance, pinned hashes and source actions are in
`units/spearman/SOURCES.md`; each `clip.json` includes the mapping and source hash.

The walk keeps the source cadence. Bounded root translations and Blender
two-bone IK lock evaluated heel/toe contact landmarks to one fitted virtual
travel speed, including heel strike, toe-off and support across the loop seam.
Native world-space rotation constraints retain the source foot roll during IK;
there is no authored foot angle correction. Bone-ankle positions alone cannot prove foot contact: verify the actual
heel/toe landmarks and support height. The source fall is grounded against the
raised stone and armour surfaces; an invisible, thick floor collider supports
cloth outside the disc. The released spear follows its own trajectory.

`infantry/refine.py` no longer splays toes, broadens sandals in screen space or
raises feet along the camera ray. It preserves the anatomical foot/sandal shape
and aligns rest rotations before projection. The finished leather soles and
straps are skinned to foot + ball bones, preserving the fitted neutral surface;
a rigid ankle-parented sandal cannot reproduce an articulated human toe-off. Per-frame foot orientation comes
only from the retarget. `units/spearman/feet.py` renders isolated, evaluated
lower-leg geometry for the top/front review without changing the saved master.

Each clip has one second of cloth pre-roll and a persistent simulation bake.
Light edge pinning keeps the cloak's broad rest silhouette while its middle
moves. Lengths are 8/8/10/4/10 frames at 4/6/14/12/4 fps (walk keeps the source
1.33-second cycle rather than playing at twice its speed). Idle and move loop.
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

### Round 8 stone and contour polish

The unchanged rest camera still owns all projection UVs. `infantry/refine.py`
fits the real knuckles and shoulder more closely and trims the crest's lower
fan while extending its forward tip. The original MPFB body topology, weights,
solid kit, folded cloth and generated unseen fills remain intact.

Use a five-segment 22mm stone bevel and restrained 1mm-distance scan bump.
The elevated 5m area key softens and shortens the broad diagonal base shadows;
its energy compensates for the increased distance. The shared cream albedo
stays recorded, while a small linear pigment lift makes the rendered stone
paler. Compare actual pixels: the albedo field alone does not establish a
painting match. Raw/graded region comparisons showed that the fixed global
histogram grade helped the figure; retain it rather than correcting each frame.

`check_scene.py` verifies the new stone finish as well as the original rig,
camera-only pigment, finished rigid surfaces and shield clearances. Keep local
contour targets separately named: reusing the shield ornament target in a
crest loop made later objects depend on scene iteration order and was caught
by the existing projection assertion.

`ROUND=8 tools/art/anim3d/units/spearman/gpu.sh` is the complete host handoff;
it defaults to round 8 and records checkout revision, dirty inputs and the
resolved Blender gate in its retained log. The requested round-7 GPU log was
absent and supplied evidence was CPU-labelled. This is an unverified GPU pass,
not evidence of successful final rendering or a diagnosed GPU failure.

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

### Round 9a proportions and silhouette lane

`units/spearman/silhouette.py` is a geometry-only pass after `refine()` and
before frozen painting UVs. It lowers the shield's over-high upper rim while
leaving its boss registered, shortens the cape's side tails, seats the shoulder
cap, fills the upper-arm contour and extends the crest tip. Shell, rim, backing
and ornament receive the same continuous fitting field. Weighted surfaces are
edited in the guard pose through inverse skin transforms. Camera-axis depth,
MPFB topology/weights, material definitions, cloth settings, foot geometry and
open-motion retargeting remain unchanged. The existing camera already registers
the crest height and base ellipse closely; changing it would move every landmark.

Parallel Spearman lanes must use separate external `ANIM_ROOT` working copies.
Lane a uses `ANIM_ROOT=$HOME/LegatumRuns/anim-pilot/lanes/spearman-r9a`, copying
the master, projection checkpoint, source painting and textures, with links to
the existing assets and Blender resources. Do not overwrite the
shared final master or another lane's renders during CPU iteration.

`silhouette_review.py` compares the preserved `round8-render/`, a 256px/16-sample
CPU `baseline-cpu/`, and the current raw `renders/c/` with one
`baseline-grade.json` LUT. It emits `spearman-r9a-restpose-compare.png` with
native 256/64 views, a 50/50 crossfade and split-screen in the shared review
folder. Alpha IoU is diagnostic only; it cannot certify proportions, surface
quality or clean motion. The unchanged `ROUND=9 tools/art/anim3d/units/spearman/gpu.sh`
automatically includes this pass when it rebuilds projection, clips and final
512/256 masters, atlas, foot check and movie after the lead merges lane winners.


### Round 9b material lane: seam underpainting

`infantry/surface_finish.py` is a material-only pass called at the end of
`project.py`, after the frozen camera UVs. It leaves the base, geometry, weights,
pose, actions, lights and camera alone. Trusted opaque source samples seed a
bounded 75mm geodesic colour continuation along the original mesh edges. That
undercoat blends into the existing generated bronze/linen/wool/leather fills;
source alpha and the ray-visibility mask still govern the original projection.
Disconnected surfaces cannot borrow pigment from each other. This is frozen
mesh pigment, not a new image plane or per-frame projection.

The undercoat retains restrained generated-fill grain. Live cavity shading and
10% physical response remain on unseen surfaces, with the original baked
AO/curvature, scan normals and roughness. Additional submillimetre hammer/weave
bump and polished bronze rim roughness add surface variation; oxide remains a
dielectric. Camera-only pigment avoids illuminating the stone. The existing
rest-fitted histogram grade is still fitted once and reused for every clip.

For a material-only A/B on an isolated master, use `units/spearman/surface_preview.py`
with a clean projected master and an output directory as its two arguments after
`--`, through plain `blender -b --disable-autoexec`. `RESOLUTION=512 SAMPLES=32`
produces CPU diagnostic masters. It hashes geometry, weights, original UVs,
transforms, pose, actions, camera and lights before/after, and fails if they
change. `surface_review.py` emits native 256/64 comparisons and enlarged crops;
its optional argument is the isolated work root. Both CPU previews receive the
same candidate-rest LUT, and raw comparisons remain available.

R9b evidence lives under `review/3d-v2/spearman-r9b-*`; the isolated work root is
`masters/spearman-r9b`. The improvement is seam continuity and tone, not a claim
that new weave is individually visible at 64px. Rest checks do not establish
motion quality: inspect unseen areas after the lead's full GPU pass. The existing
`ROUND=9 tools/art/anim3d/units/spearman/gpu.sh` automatically includes this pass
through its project stage; do not replace the other lanes' animation changes.


### Round 9c motion lane

`units/spearman/motion.py` owns the motion-only refinement. The open Quaternius
walk is blended at 92% **on the source armature in Blender NLA**, before matched
rest/roll constraints are sampled. Enable `use_animated_influence` and key its constant value: setting only
`influence` leaves Blender's automatic strip influence at full strength. The
source cadence and idle carrying-arm layer remain. The source stance detector
allows a 12mm near-floor arc after blending; virtual speed is refitted, and the
actual target sole still must pass 1mm slip and 2mm floor-error limits; no target foot rotation is corrected. Keep the top/front feet-over-cycle
review mandatory for every walk iteration.

The weapon attack now has bounded C1 pose curves instead of rounded pose indices:
small reverse anticipation, a short drive with 14cm more hand extension, then
longer recovery. The CC0 hit
reaches recoil earlier and releases over the remaining samples; death retains
its source poses with faster collapse and more settling time. Equipment release
uses the same remapped death phase. Human hit/death joints are still source-driven.

Crest tips flex with a damped spring driven by head acceleration (roots fixed,
26mm cap); the strapped shield lags its carrier around the grip (3-degree cap).
Attack/hit fade that response into the exact guard. Lower cloak silhouette pins
are loosened for those two clips and air damping increased; shoulders stay pinned
and the real cloth cache is rebaked. The master, materials and proportions are
unchanged. Loop clips keep their previous secondary response to avoid introducing
a new equipment seam.

For independent CPU iteration, copy the current master/grade/assets into an
isolated `ANIM_ROOT` under `ANIM_ROOT/lanes/`. `compare_motion.py` combines preserved
round-8 GPU strips with the actual CPU renders and painting at native 256/64 px,
writing only `spearman-r9c-*.png` to the shared review directory. GPU delivery is
still `ROUND=9 tools/art/anim3d/units/spearman/gpu.sh`, unchanged; it rebuilds all
motion, cloth, feet checks, atlas, 512/256 masters and movie from merged code.

### Round 9 combined candidate

The merge keeps lane a's contour fitting, lane b's frozen seam underpainting,
and lane c's source-space walk attenuation, continuous weapon attack, source
hit/death timing and passive equipment response. It drops lane c's loosened
cloth pins/settings for hit: the combined recovery frame raised a cloak corner
behind the shoulder. Attack retains that cloth response; hit retains its original
pinning and cloth settings. Run silhouette fitting before
freezing projection UVs, then surface underpainting after projection; rebuild
all five clips from that same master. `check_scene.py` requires both round-9
geometry/material markers, in addition to the existing rig and contact checks.

The GPU handoff also saves `spearman-round${ROUND}-restpose-compare.png` from
the fresh calibrated rest render and checks required files before completion.
The movie retains round 8's 1600x352, five-column, 2x-on-cream layout, 24 fps,
192 frames, H.264/yuv420p. CPU merge checks use the isolated external root
`lanes/spearman-r9-merge`; its atlas is preview-only, leaving the last GPU atlas
intact until the lead's pass. Passing these checks is not a visual PASS.

### Painted Eevee look (render-time; look lane, 2026-11-24)

`units/spearman/look.sh MASTER_DIR OUT_DIR` renders the rest pose and all five
clips with emission-only painted materials in Eevee (Standard view, no grade)
and packs a validated preview atlas outside `app/`. It never saves a `.blend`:
geometry, weights, UVs, cloth caches and actions are whatever the master holds,
so it runs unchanged on any form or motion candidate. Rest plus 40 frames takes
about a minute once the GPU lock is free.

- Seen surface (stored rest visibility) shows the painting itself. Unseen
  surface uses white Diffuse → Shader to RGB → a ramp whose stops are the
  material's painted colours placed at the rest lighting quantiles
  (`look_textures.py`, second pass with the `debug=6` ramp-input render).
- `look_textures.py` first resamples the painting onto the frozen UVs.
  `project.py`'s calibration is 0.9% narrow and 0.3% short against the true
  fit (5.3425 source px per 256-canvas px about (627,627) ↔ (127.5,128)); fix
  that constant before the next projection rebuild and drop `register()`.
- Each kit part keeps paint only inside its own rest outline; the rest is
  push-pull inpainted from its own pixels. Rigid and free-swinging parts also
  reject another colour family's paint; torso layers keep everything.
- Eevee facts: a sun of strength π returns 1.0 on white diffuse; an unlinked
  Normal socket means the geometry normal (link a Combine XYZ for a constant);
  a diffuse whose normal is the key direction returns the cast shadow alone;
  ColorRamp elements re-sort when a position is assigned.
- Judge against the game's 256 painting with a display-space Lanczos
  reduction (that is how the painting was reduced); linear-light reduction
  adds about 2.4 CIE76 of pure resampling difference. `look_compare.py`
  reports the critique numbers, the colour error at zero offset and a
  2 px-blurred tone error.
- The spear shaft and ferrules get a render-time bevel (`shaft_radius`,
  `ferrule_radius`); set them to 0 once the master's shaft matches the painting.
