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

### Lead's host GPU handoff

After the saved master and clips are rebuilt, render c first to fit the grade.
Use the same engine/device/resolution for the rest and all clip renders.

```sh
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU CYCLES_BACKEND=METAL SAMPLES=64 RESOLUTION=384
tools/art/anim3d/render.sh c
tools/art/anim3d/render.sh detail
tools/art/anim3d/render.sh d
for clip in idle move attack hit death; do
  tools/art/anim3d/render.sh "e-$clip"
done
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/pack.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/validate.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/test_pipeline.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/details.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/movie.py
tools/art/anim3d/render.sh audit
```

The optional comparison movie requires `ffmpeg` on PATH and encodes with two
threads. For Eevee use `export RENDER_ENGINE=BLENDER_EEVEE RESOLUTION=384` instead. Review
both sizes and playback after each engine change. `grade.py` keeps raw PNGs in
each render directory and binds one frozen RGB LUT to the source/master.

### Delivery contract and checks

`pack.py` preserves all 40 frames in a transparent 2560 × 1280 WebP, alpha
quantized to 32 levels, quality selected from 85–60 with a strict **200,000-byte**
cap. Oversize fails without overwriting delivery. JSON remains exactly
`{frame:{w,h,ax,ay}, clips:{name:{row,frames,fps,loop}}}`, anchor `(127,221)`.
Master, clip, render, grade and individual frame hashes prevent stale packaging.
Interrupted stages invalidate their completion manifests.

`validate.py` checks decoded dimensions, metadata, all clips, padding, alpha,
bounds, actual motion and pixel-identical held death. `audit.py` checks all 40
samples for original body/rig topology, persistent cloth, stationary base, floor
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
