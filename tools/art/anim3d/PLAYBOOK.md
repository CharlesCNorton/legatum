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

## Infantry / Spartan hoplite round 1

The unit entry point is `UNIT=spartan-hoplite tools/art/anim3d/render.sh STAGE`.
Unit-specific code is in `units/spartan-hoplite/`. The shared MPFB builder,
Corinthian helmet, scan materials, AO/curvature baking and animation accept an
optional `ANIM_MASTER` directory; the spearman default is unchanged. This lane
uses `masters/spartan-hoplite/round1-3d/`, preserving the earlier hoplite experiment.
Its internal `spearman.blend` filename is the shared pipeline's working convention;
the scene's `unit` property identifies the actual Spartan hoplite.

The painting has linen armour, red-edged pteruges, a red shoulder mantle, bronze
greaves, a Corinthian crest and an ivory-faced lambda aspis. The body is the real
MPFB CC0 weighted human, with a 53-bone armature. Kit meshes have thickness,
rounded edges, stitched bindings, buckles and layered cloth folds. The cape uses
actual per-clip cloth caches. The plain sheet is retained as first-stage evidence.

The standard finish follows all four standing quality levers: (1) frozen-camera
projection of our original painting onto actual meshes, blended by surface
incidence and pigment masks into scanned/generated fills; (2) physical bevels,
cloth thickness/folds and small kit geometry; (3) warm upper-left product key,
soft fill, cool rim and Cycles contact shadows; (4) one painting-derived monotonic
RGB histogram grade, reused unchanged across clips. The projection records its
per-part registration in external `projection.json`. It is approximate and carries
painted lighting; it is not proof of rest-pose parity. Unseen linen uses the mounted
lane's original generated fill, with CC0 scans on remaining unseen materials.

Stone uses the common sRGB **#E9CFA0** target, converted to linear pigment before
lighting, with a darker rim and low-contrast scanned grain. Judge its *rendered*
colour against the painting. `spartan-hoplite-f-restpose-compare.png` contains the
painting, render, half split and 50% crossfade, plus native 64 px views. Review the
helmet, chest and shield crops in `spartan-hoplite-c-details.png`; no file existence
or atlas size check constitutes art acceptance.

```sh
UNIT=spartan-hoplite tools/art/anim3d/render.sh prepare
UNIT=spartan-hoplite tools/art/anim3d/render.sh build
UNIT=spartan-hoplite SAMPLES=8 tools/art/anim3d/render.sh b
UNIT=spartan-hoplite tools/art/anim3d/render.sh materials
UNIT=spartan-hoplite tools/art/anim3d/render.sh c
UNIT=spartan-hoplite tools/art/anim3d/render.sh all-clips
UNIT=spartan-hoplite tools/art/anim3d/render.sh all-renders
UNIT=spartan-hoplite tools/art/anim3d/render.sh pack
UNIT=spartan-hoplite tools/art/anim3d/render.sh validate
UNIT=spartan-hoplite tools/art/anim3d/render.sh audit
```

All Blender calls are plain `blender -b --disable-autoexec` through PATH's shared
gate, with three render threads; this lane starts no concurrent heavy process.
CPU Cycles is the sandbox default. The lead's GPU refresh is:

```sh
UNIT=spartan-hoplite RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=64 tools/art/anim3d/render.sh all-renders
UNIT=spartan-hoplite tools/art/anim3d/render.sh pack
UNIT=spartan-hoplite tools/art/anim3d/render.sh validate
UNIT=spartan-hoplite tools/art/anim3d/render.sh audit
```

GPU mode explicitly selects Metal and refuses silent fallback. Rendered 512 px
masters and downsampled 256 px gallery frames are preserved externally. A 256 px
CPU preview is never upscaled and labelled as a 512 px master. Rebuilding the
model invalidates clips; regrading rest invalidates all rendered clip grades.
The packer binds each clip/render/master and grade by SHA256 and refuses staleness.

### Hoplite trimmed atlas extension

The candidate ships 160×160 logical cells, 10 columns and five rows, all
8/8/10/4/10 frames, WebP quality **at least 75**, at most **200,000 bytes**.
The legacy `frame:{w,h,ax,ay}` and clip `row,frames,fps,loop` fields remain.
`format:"trimmed-grid-v1"` adds `clips[clip].rects[i]`:
`{x,y,w,h,ox,oy}`. `x,y,w,h` selects the cropped sprite in the atlas; `ox,oy`
restores its position in the 160 px logical frame. Draw at
`anchorX - frame.ax + ox, anchorY - frame.ay + oy`. Each crop is packed at the
upper-left of its existing 160 px grid slot. Empty slot padding remains transparent.
Consumers **must use rects and offsets**; treating this as the old full-cell atlas
would jitter. This art candidate does not change or enable the runtime loader.
An over-budget pack fails instead of dropping frames or quality. Alpha alone is
quantized to 16 levels. Pack and validation reports remain outside git.

Hoplite-specific corrections: the inherited aspis triangle fan and outer quad
rings had opposite winding. `shield_normals.py` reverses the outer rings while
preserving UVs; otherwise the incidence mask projects almost no painting onto
the face and Solidify hides the emblem. The lambda is paint on the convex shield,
not a second raised letter. `ANIM_ATTACK_SLIDE=.43` (spearman default remains .25)
keeps the shorter hoplite spear's rear end inside the tighter fixed camera.

The front mantle likewise needs outward winding for its painted colour mask.
A targeted rest-camera probe caught fingertips protruding through the aspis;
its surfaces now sit 75 mm farther forward. The hoplite-only
`ANIM_SHIELD_SETTLE=1` grounds the fully released shield after that clearance
change. These switches leave the spearman defaults unchanged.

### Hoplite round 2: finished surfaces and driver handoff

The resumed master lives in `masters/spartan-hoplite/round2-3d/`; round-one masters
and review images remain preserved. `refine` always starts from this directory's
`unpainted.blend`, so repeated driver runs do not accumulate fitting or shader
layers. To reconstruct that checkpoint, run the unit's build/materials stages;
`materials` preserves the unprojected, baked input before its older paint pass.
Then run `refine`. All changed code remains in `units/spartan-hoplite/`.

`refine.py` freezes the mixed MPFB shape keys while retaining its 19,158 vertices,
original skin weights and 53 bones. The spear hand rises 24 cm while the weapon's
world transform stays fixed; the unit-owned animation uses that same guard and
interpolates combat elbow poles from it. Camera framing raises the figure, the
crest and complete shield narrow, shoulder cloth corners lower, and the actual
helmet/head geometry moves upward. Weighted fitting inverts the blended skin
matrix. These are depth-preserving edits to articulated surfaces, not cutouts.
The recorded camera and contour fit are approximate, not an exact source match.

Static bevel, thickness and subdivision finish before projection. A single
frozen rest-camera UV map replaces the old per-part rectangle stretching. Surface
facing, ray visibility and source pigment masks blend into existing physical
materials and generated linen fills. A camera-only Principled pigment branch
preserves the source's painted illumination; other rays see the original PBR
surface. Standard/None avoids grading already painted light through AgX again.
This is specific to painted projection. Product lights and the physical cream
disc remain; the disc receives no painted feet or stationary figure shadows.
The rest-derived histogram LUT is shared unchanged by every clip.

The complete, executable, no-argument host handoff is now:

```sh
ROUND=2 tools/art/anim3d/units/spartan-hoplite/gpu.sh
```

It resolves this checkout, records revision/dirty inputs and the Blender gate,
then sequentially refines, checks the scene/input hashes, rebuilds all five cloth
clips, audits the rig, renders plain/rest/details/poses/all clips with **Cycles
GPU, 512 px, 64 samples**, checks GPU provenance and actual 512/256 dimensions,
packs and validates the 160 px trimmed atlas, and encodes
`review/3d-v2/spartan-hoplite-round${ROUND}.mp4`. The movie reconstructs decoded
crops with their offsets, displays all five clips at 2x on cream, and verifies
H.264/yuv420p, 1600×348, 240 frames/eight seconds with ffprobe. Nonlooping clips
hold and replay every two seconds. The script retains its own transcript and a
running/failed-stage/complete status file; technical completion never writes PASS.

CPU iteration uses `SAMPLES=12 RESOLUTION=256 UNIT=spartan-hoplite
 tools/art/anim3d/render.sh STAGE`. The scene check covers original anatomy,
nonzero scales, fixed camera, frozen UV topology, camera-only pigment wiring and
source hashes. Existing equipment/cloth audits and trim/motion validation remain.
Repeated death samples copy the already-rendered PNG instead of trusting denoiser
noise to match. Packing and validation reject changed masters, clips, grades and
frames. A CPU rerender cannot relabel an old 512 px master as fresh output.

At this round's first calibrated rest preview, alpha-threshold silhouette overlap
improved from .644822 to .770323. That measures the contour only: crest curvature,
helmet/gaze, shoulder drape, stone shading and animation still need visual review.
No art PASS is implied by the measurement or by a valid atlas.

The raised guard exposed a framing regression during the full audit: six attack
samples put the butt outside the fixed cell. `animate.py` adds another .29m shaft
slide only after the raise passes .4, reaching the full correction by .8. Keeping
the early diagonal pose unchanged avoids pushing its spearhead above the canvas.
`attack-clearance` applies the same rigid-only correction to an existing attack
cache; it asserts the weapon is not a cloth collider and preserves the cloth bake.
The subsequent full forty-sample audit reports zero findings.

### Hoplite resumed driver round 2: source contour and open motion

The driver calls the previous completed GPU run `round1`; its source checkout
already contained the earlier round-two work. Preserve that evidence under
`review/3d-v2/spartan-hoplite-round1-gpu-preserved/`. This pass uses a new
`masters/spartan-hoplite/round3-3d/` checkpoint; `unpainted.blend` is copied from
the prior master directory and is always the repeatable input to `refine`.

Fit the existing full-depth crest tufts to swept inner/outer curves in the
painting's camera, retaining their depth, thickness and head attachment. Fit the
shoulder mantle and single rounded brooch before freezing UVs. Pigment-only hue
masks were rejecting legitimate painted highlights on skin/cloth; the finished
surface visibility/alpha mask now carries those source pixels. Calibrate the
stone's separate rim material as well as its top; changing only the top left a
dark grey-brown rim. Existing bevels, straps, folds, scanned AO/curvature and
generated unseen linen remain. The projection is still viewpoint-dependent;
contour fitting is not evidence of exact viewpoint or rest parity.

Motion follows common feedback 23: use proven open actions by default, and
calibrate donor and target rest matrices including bone rolls. This unit now
uses Quaternius CC0 `Idle_Loop`, `Walk_Loop`, `Hit_Chest`, `Death01`, with the
unit-local `retarget.py` snapshot read from the trench-infantry lane. Walking
arms use the open idle layer to retain the spear/shield guard. No post-retarget
foot orientation patch is allowed. Root contact corrections preserve the donor
rotations. Only the weapon-specific attack and equipment release are authored.
Per-clip metadata names the action, source hashes, map and contact correction.
Sources and licences live in the unit's `SOURCES.md` and external assets registry.
The 8/8/10/4/10 samples remain; playback uses 4/6/14/8/5 fps for readable actions.

Every round must render the entire move cycle from top and front, with the top
camera clipped above the ankles so the body cannot conceal the feet. The `feet`
stage writes actual Cycles frames and `spartan-hoplite-g-feet-check.png`, plus
ankle/toe positions and yaw in `feet/evidence.json`. Review forward direction,
plant/roll and virtual-ground slip in addition to the normal five strips. The
GPU handoff includes these views and binds their evidence to the current move
master. Full technical validation still does not confer art PASS.

The first open-death retarget exposed a limitation of carrying the neutral
weapon guard into every action: raised limbs propped the corpse up, even though
the original `Death01` lies flat. Death now calibrates all limb chains in the
anatomical reference and crossfades out of the held guard during its opening.
No foot rotation is patched. `Hit_Chest` is sampled forward and back to return
its four output frames to the starting guard. Inspect the original donor when a
retarget looks wrong; a collision-free result can still be the wrong motion.
A finite hidden collision slab catches simulated cloth beyond the base edge;
released equipment stays inside the fixed camera and the spear's planted butt
uses only an along-shaft contact correction. These are unit-specific contact
constraints, not a claim that the original donor animation fits every weapon.

### Hoplite driver round 3: visible cape, linen layers and fitted sandals

Keep the successful round-2 GPU masters in `round3-3d/`; the new repeatable
checkpoint is `masters/spartan-hoplite/round4-3d/unpainted.blend`. Incoming GPU
review files and movie are copied into `spartan-hoplite-round2-gpu-preserved/`.
The driver entry point defaults to `ROUND=3` and the new master directory.

`finish_round3.py` works before UV freezing. It fits the complete lower limbs,
greaves and sandals through the inverse skin matrix while retaining depth,
original topology and weights. Sole fitting preserves the ground plane. Short
armour tabs now overlap a separate folded linen underlayer with a solid hem.
The straight solid spear is registered as a single axis/cross-section assembly,
with a grounded butt. None of these edits changes donor foot rotations.

The cape's camera-visible side had reversed winding: every stored projection
weight was zero. Correcting winding before projection restores painted folds;
more saturation would not have fixed it. Its asymmetric hem and real cloth
simulation remain. Skin, wool and leather revealed in movement now use recorded
image-generated physical fills, blended with live AO. The limestone's camera
pigment also receives fine grain and live contact AO instead of a flat colour.
Original bevels, buckles, straps, product lighting and a single automatically
sampled rest-pose histogram grade remain in use.

Every move review now checks the **evaluated sandal meshes** as well as bones:
sole principal-axis yaw and virtual-ground center displacement are measured in
planted intervals. This catches mesh registration errors that a bone-only foot
check misses. Top/front actual renders remain required; numeric checks do not
establish art quality. The complete lead-side pass is:

```sh
ROUND=3 tools/art/anim3d/units/spartan-hoplite/gpu.sh
```

All stages, genuine GPU512/64 masters and 256 derivatives, feet review, trimmed
160 px atlas, validation and the decoded eight-second movie remain part of this
single no-argument handoff. It never writes PASS; rest parity and five clean clips
still require visual inspection of the final GPU output.

The first full-depth fit exposed why screen matching alone is insufficient:
constrain the weapon to the hand in camera **depth**, not only in screen pixels,
and rerun all equipment/ground audits. Sandal-center drift exceeded the 25 mm
contact gate even while ankle drift was below a micrometre. The unit's open-walk
adapter now stabilizes evaluated sandal centers by root translation; it retains
source rotations and records ankle displacement diagnostically. Delivery gates
use the actual sole centers and their yaw. Attack and carried spear support also
use evaluated geometry rather than assumed rest offsets.

Sandals must share the anatomical foot/toe skinning: rigid parenting to `foot_*`
while MPFB toes bend on `ball_*` lets toes pass through soles on toe-off. This
round transfers nearby anatomical weights to finished soles and straps with
inverse neutral skinning, preserving their rest geometry. Do this before frozen
projection and cloth/clip regeneration, then repeat actual mesh contact views.
