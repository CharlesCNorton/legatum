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

## Mounted family — Cavalry round 1

Cavalry's isolated pipeline is `tools/art/anim3d/units/cavalry/`. It reuses the
mounted branch's licensed Quaternius horse and MPFB 2.0.18 anatomical rider, with
original navy uniform, kepi, curved steel sabre, crossbelts, boots and saddle gear.
The horse's weighted skeleton and the rider's separate 53-bone rig remain editable;
the rider follows the horse's torso. All silhouettes are real geometry. The
painting is a colour texture on those surfaces, never a cutout or relief plane.

The six Blender skills inform the geometry, materials, lights, camera, animation
and render setup. The standing four quality levers are the standard here:

1. Align the rest camera and anatomy before projecting the archived source with
   fixed UVs. Surface incidence and conservative coat/cloth/skin masks blend into
   generated painted fills on unseen surfaces. Cavalry reuses the mounted family's
   CC BY 4.0 generated fill sheet; its original prompt is retained alongside the
   unit scripts. The cloth fill is tinted navy in the shader. Projection cannot
   repair silhouette or anatomical mismatches.
2. Use physical strap and cloth thickness, bevelled hardware, fitted MPFB garments,
   buttons, buckles, piping and horse subdivision. Bake real AO and Pointiness;
   retain the native UV channel for bakes when adding the projection UV channel.
3. Use a warm upper-left key, soft fill, cool rim, contact shading and denoising.
   Metal is metallic=1; cloth, skin and leather are dielectric. The single fixed
   cream stone base targets sRGB **#E9CFA0**, with fine grain and darker rim shading.
4. Fit one monotonic RGB quantile grade to the rest painting and use the identical
   LUT for every clip. Preserve raw renders. Never grade frames independently.

Run from the repository root with the existing external installation:

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/cavalry/prepare.py
for stage in build b materials bake paint c c-details animate d; do
  RENDER_ENGINE=CYCLES CYCLES_DEVICE=CPU SAMPLES=8 \
    tools/art/anim3d/units/cavalry/render.sh "$stage"
done
for clip in idle move attack hit death; do
  RENDER_ENGINE=CYCLES CYCLES_DEVICE=CPU SAMPLES=4 \
    tools/art/anim3d/units/cavalry/render.sh "e-$clip"
done
tools/art/anim3d/units/cavalry/render.sh audit
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/cavalry/pack.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/cavalry/validate.py
ROUND=1 "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/cavalry/mp4.py
```

Every Blender invocation is plain background `blender` on PATH, with automatic
Python execution disabled. The machine gate owns slots/threads; do not bypass it
or launch concurrent heavy work. No zero-scale hiding is used. No external master
is committed. The unit uses `assets/cavalry/`, `masters/cavalry/` and the required
`review/3d-v2/cavalry-*` names below `~/LegatumRuns/anim-pilot/`.

Idle/move/attack/hit/death have 8/8/10/4/10 samples. Horse actions are sampled from
the CC0 source; move retimes its gallop trajectories into a three-beat canter.
Rider motion, sabre slash/recoil/release and death contact correction are authored.
The last death image is reused exactly. Tack is bone-attached, not a leather
simulation, and needs intersection review in extreme poses. Inspect at 256 and
64 px, and inspect the strips/video for hoof contact, grip and loop seams.
`cavalry-f-restpose-compare.png` shows painting, rest render, half split and 50/50
crossfade. A successful structural audit is not visual approval.

### Cavalry trimmed delivery and GPU handoff

```sh
ROUND=1 tools/art/anim3d/units/cavalry/gpu.sh
```

This no-argument script renders **all** b/c/details/d/e stages with Cycles Metal
GPU (64 samples by default), or Eevee with `RENDER_ENGINE=BLENDER_EEVEE` and explicit
`--gpu-backend metal`. It refuses a silent Cycles CPU fallback. It retains real
512 px frames and downsampled 256 px masters, generates every review sheet and
animated WebP, packs and validates the atlas, and writes the eight-second
`cavalry-round${ROUND}.mp4`: all five clips at 2x on cream, H.264/yuv420p.

The new atlas contract is version 2. `frame:{w:160,h:160,ax:87,ay:141}` describes
the **logical untrimmed cell** and its shared ground anchor. `clips` retains named
rows idle/move/attack/hit/death, `frames`, `fps`, and `loop`. Each clip adds
`rects:[{x,y,w,h,ox,oy}, ...]`, in frame order. `(x,y,w,h)` is the packed source
rectangle; `(ox,oy)` restores its top-left within the 160 px logical cell. To draw
at a world anchor `(X,Y)`, place that crop at `(X-ax+ox,Y-ay+oy)`. Packed rows have
variable heights and two transparent pixels between crops; never infer rectangle
coordinates by multiplying row or frame number by 160.

Packing keeps all 40 frames, alpha and offsets and chooses WebP quality 90/85/80/75
under **200,000 bytes**. It fails rather than dropping frames or quality below 75.
Source, blend, grade and delivery hashes reject stale inputs. Validation reconstructs
all logical frames from the decoded WebP and checks clip counts, alpha, bounds,
motion, byte budget and held source death. This is an isolated candidate; the
runtime must understand version-2 rectangles before using it. The painting stays
in the game. Write a `cavalry-PASS` only after visual parity and clean motion are
actually established, not because the packer passes.

### Cavalry round 2: surface fitting and reliable delivery

The runner reassigned lane-20 during work; its cavalry WIP was recovered in
`legatum/.worktrees/cavalry-round2` on the original cavalry branch. Never switch
an active lane back from another unit; use the isolated checkout. The clean
external `cavalry-unpainted.blend` is the repeatable input to `paint`.

`refine.py` freezes MPFB macro shape keys on that working copy, cuts accidental
jacket-covered hands using native hand/finger skin weights, and fits full-depth
anatomy through inverse skin matrices. The horse is subdivided in bind space
before fitting. Bounded local horse corrections replace an oscillating global
landmark fit that produced a visibly distorted hindquarter; the rejected trial
was caught in the immediate rest comparison. The rider uses a smooth landmark
field; the sabre uses a shape-preserving rest-view similarity transform.
Depth, skin weights and both editable skeletons remain. These are approximate
landmark corrections, **not** a claim of an exact camera or anatomical match.

Rigid bevels/solid thickness are applied before UV sampling. Frozen source paint
is camera-ray-only, mixed with the physical material; non-camera rays retain
real shading and shadows. Standard/None avoids compressing painted illumination
a second time. Existing generated coat/navy/hair fills, scanned materials,
AO/curvature, cloth folds, mane locks and metal detail remain. Warm key/fill/rim
energies are 340/68/110. The independent stone pigment has a warm top and darker
rim; it never contains painted hooves or static figure shadows. One automatic
rest histogram LUT stays fixed for all clips; repeated grading uses preserved
raw files and is idempotent. The source/master hashes are recorded with it.

`tack.py` attaches both real rein curves to the animated bit and the evaluated
rein hand, retaining slack. Animation keys the curve points in all forty poses.
This fixes disconnected endpoints, not full leather simulation. Stirrups are
fitted closer to the boots; source gait, boot/stirrup contact, tail shape and
horse/rider anatomy still require visual review. A structural pass cannot certify
clean motion or painting parity.

`ROUND=2 tools/art/anim3d/units/cavalry/gpu.sh` remains the complete no-argument
host handoff. It resolves its checkout, records revision/dirty inputs and the
Blender gate in `cavalry-gpu-round${ROUND}.log`, and writes a status file naming
any failed stage. Cycles Metal preflight precedes changing masters. Every pass
rebuilds paint and all five clips, then renders all stages at GPU512, exports
native stage masters and gallery256, audits, packs, validates and makes the
8-second decoded-atlas MP4. GPU512 provenance is required before final packing;
CPU previews cannot satisfy that gate. No automatic PASS marker is written.

Atlas v2 keeps the existing per-clip `rects` contract and all 8/8/10/4/10 samples.
Premultiplied bicubic reduction retains **lossless 8-bit alpha**; identical logical
frames share a rectangle so held death is identical even after lossy WebP colour
encoding. Validation checks source hashes, reconstructed alpha byte-for-byte,
trim offsets, bounds, motion, decoded held death, Q75 minimum and the 200,000-byte
cap. FFprobe checks the 192-frame H.264/yuv420p, 1600x352, eight-second movie.
Masters and reviews remain external; the shipped game still uses its painting.

The frame-bounds check caught the hit sabre above the camera and the settled
horse beyond the right edge in death. Hit and early death now rotate the actual wrist/grip
until the blade clears the top margin; death settles 0.20m left in the camera's
ground-plane direction and folds the released sword arm across the body. The
camera and cell size stay fixed. Rebuild and review those clips after changing
any rest fit; source trajectories alone do not guarantee safe framing.

### Cavalry driver round 2: silhouette and source motion

Round-one GPU evidence is preserved under `masters/cavalry/driver-r1-gpu/`.
The outer driver log was empty because the handoff redirected stdout; `gpu.sh`
now tees its detailed transcript to the caller too. Its completed round-one
receipt was 188,260 bytes at Q80, not an art approval.

`finish.py` refines the horse in bind space through inverse skin matrices,
retaining depth, weights and both editable rigs. It lowers/rounds the croup,
adjusts muzzle landmarks, fits thinner bridle/stirrup geometry and builds
thirteen tapered, solid, weighted tail locks. `refine.py` broadens the actual
sabre diamond section before bevel and frozen projection. Source ivory material
patches are removed: the painting supplies its own narrow blaze and fetlocks.
A warm-colour mask had discarded those details and the grey muzzle; full source
pigment now uses rest-view visibility/incidence on the actual horse mesh.
No pigment mask clips rendered alpha. Existing generated fills, real cloth
folds, scans/bakes and product-shot lights remain; stone gets fine colour grain.
One rest histogram LUT is applied unchanged to all clips.

Use open motion as the default: the horse uses synchronized native Quaternius
Idle/Gallop/Hit/Death trajectories, not independently retimed legs. The rider
uses the CC0 Universal Animation Library Sitting_Idle_Loop, Hit_Chest and Death01
with reference/roll compensation. Pelvis/legs stay saddle-constrained; sabre
attack/release and framing/contact adaptations are original. Full URLs,
licences and SHA256 pins are in the unit `SOURCES.md` and `rider_motion.py`.
No post-retarget foot rotation correction is applied.

The mounted review standard includes actual top/front renders of the evaluated
lower legs for every move sample, `cavalry-g-feet-check.png`, plus sole positions
in `masters/cavalry/feet/manifest.json`. This cutaway is a diagnostic copy only;
the master remains complete. Inspect travel direction, planted intervals and
sliding in addition to the five hero-view clips. A structural audit and a
readable feet sheet do not certify clean contact.

`ROUND=2 tools/art/anim3d/units/cavalry/gpu.sh` still performs the complete
sequential GPU512 pass, gallery256, trimmed Q75+ atlas, validation, feet sheet
and eight-second five-clip MP4. It now regenerates/pins derived painting inputs
before paint and retains the driver's transcript. CPU previews remain labelled
CPU; no PASS is generated automatically. Horse anatomy, silhouette and extreme
motion must be reviewed against the painting after the fresh GPU pass.

The full-cycle CPU review rejected lower-leg silhouette fitting: both local
warps and a continuous section trial pulled anatomy away from its source joints
and stretched it during gallop. The final fitter masks out native leg/shoulder
weights, preserving source leg volumes. `contacts.py` adds vertical support
correctives over native foot lift, retaining horizontal gait and foot rotations
and the raised idle foreleg. Attack/hit blend back to rest; death blends into its
source action. Tail motion keeps source timing at reduced amplitude for the
longer hair sculpture. These are mounted contact adaptations, not a foot-slip
proof. The remaining source-pose silhouette mismatch must not be hidden by a
static-only fit or an art-PASS claim.

Added tail locks must copy both the native horse object parent hierarchy and
its skin weights. An armature modifier alone looked attached at rest but left
the hair behind during root-level death translation; the structural audit now
checks that shared hierarchy, and the death strip is reviewed after rebuild.

### Cavalry driver round 3: joint registration instead of skin displacement

The round2 GPU handoff completed at 184,594 bytes/Q80, but its successful audit
hid visibly stretched hind tendons and a different rest stance. Prior GPU
masters, clips and reviews are retained under `masters/cavalry/driver-r2-gpu/`.

`stance.py` fits the actual leg joints and independent imported hoof controls to
measured painting coordinates before frozen UV projection. The imported rear
hoof controls are separate roots; verify their pairing from shared skin weights,
not apparent proximity in the projected pose. A screen-proximity trial paired
them incorrectly and was rejected after inspecting the lowest vertices. Control
origins can also differ from visible skin joints: the final fitter measures
shared-weight boundary centroids on the evaluated rest mesh, then fits those
anchors. Bone-origin-only fitting was rejected for lower-leg distortion. Mild radial changes
broaden the existing weighted anatomy around its axes. The pose fit keeps depth,
then adjusts support along the camera depth axis so planted soles touch the
stone without changing their image coordinates. `contacts.py`'s mesh-only support
warps were removed. Idle retains the registered stance; move uses synchronized
native gallop; attack/hit/death blend out of the registered pose into source
motion. This is rest-pose adaptation, not a claim of full contact/slip solving.

Reset all source pose bases before evaluating each action sample. Imported glTF
actions may be sparse: a channel absent from the action otherwise retains a
registered rest translation/scale or the previously sampled action. This applies
to both the horse and the CC0 seated rider source. Do not patch foot yaw after
retargeting.

`blade.py` fits a real beveled diamond-section sabre to the painting's curved
profile before UV sampling; broader tapered solid tail locks keep their copied
horse parent hierarchy and source weights. Existing thickness, straps, buckles,
uniform folds, scanned materials, generated unseen-surface fills, product lights
and the single automatic rest-histogram LUT remain. `stone.py` uses a new generated
clean occlusion plate as pigment on the actual beveled disc, with live AO for
moving hoof shadows. Generated alpha never clips geometry. Exact prompt and
SHA256 pins are in the unit directory and both source ledgers.

`ROUND=3 tools/art/anim3d/units/cavalry/gpu.sh` verifies immutable source inputs
before regenerating derived maps, then rebuilds the complete sequential GPU512
pass, gallery256, top/front feet diagnostics, rig audit, 160px trimmed Q75+ atlas,
validation and eight-second H.264/yuv420p movie. Review sheets now label device,
native resolution and samples. CPU previews remain CPU evidence; no PASS is
created by the script. Inspect all five clips and both token sizes after GPU
rendering, including first-frame continuity, support, tail and released sabre.

The movie helper also extracts eight frames from the encoded MP4 into
`cavalry-round${ROUND}-video-check.png`; that sheet is decoded movie evidence,
not a reconstruction from the original frame files.
