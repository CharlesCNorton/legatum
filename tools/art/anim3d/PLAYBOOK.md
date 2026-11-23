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

## Vehicles / autonomous armour — round 2

This unit's scripts live in `tools/art/anim3d/units/autonomous-armour/`; they do not
replace the tank lane's family scripts. The unmanned vehicle uses original closed
hull and turret meshes, a genuinely open muzzle, separate optical housings, twin
antennas, thick segmented skirts, six road wheels per side, two sprockets per
side and 128 individually articulated track links. A rigid parent hierarchy owns
chassis, turret traverse, gun recoil, sensor yaw, antennas, wheels and links.
No infantry anatomy or MPFB installation is needed for a machine.

Standard finish follows feedback 18–21: first align the camera and true rest
geometry to the painting, then freeze full-source camera UVs on those meshes.
Finished static surfaces receive shape-preserving subdivision before UV freezing.
A frozen world-space BVH supplies visibility samples and normal-facing confidence;
it avoids rebuilding Blender's dependency graph after every material assignment.
Camera-only pigment preserves 97% of the source illumination on visible static
armour, with physical PBR retained for other rays and revealed surfaces. Standard /
None avoids a second filmic compression of already painted illumination. This is a
source-painting workflow, not a general photographic colour-management preset.
Rotating gear excludes source projection entirely: painted source hubs otherwise
rotate across the independently modeled wheel faces. Neutralized generated olive
fill, ambient cavity shading, bevels and physical response finish the wheel dishes.
Three real Cycles AO/Pointiness bake pairs remain on the main armour surfaces.

The round-two hull and track gauge are 22% broader, the turret is 15% shorter with
a raised mounting, and the camera is `(10,-5.7,4.6)` aimed at `(0,0,1.6)`, scale 5.25.
These are measured local visual improvements, **not an exact viewpoint claim**.
The source/render/50-percent-crossfade sheet at 256 and 64 px remains the art gate;
passing file checks alone is not approval. Remaining running-gear proportions,
paint registration and stone shading are recorded honestly in the unit log.

A warm high area key, soft fill and cool rim light the miniature. A bounded RGB
percentile grade is measured at rest and frozen across every clip. Projected and
stone pigment are camera-only, so they cannot light nearby geometry. Review newly
revealed surfaces and source-object contamination in moving poses.

The base retains the shared dielectric **#E9CFA0** albedo, fine grain, a real
55mm five-segment bevel and .24m contact top. Camera-only top/rim pigment with live
AO opens its shaded edge; no tank image or dark painted contact shadow enters the stone.
The driver-round-two finish also freezes source UVs on the real disc. Only
bright cream source pixels below the vehicle may contribute; olive pixels and
dark painted contact shadows are excluded. Physical/pigment stone remains
underneath the vehicle and on unseen surfaces. Judge actual lit/graded pixels,
not material numeric values alone.

Mechanical motion uses shared constants in `common.py`: five track pitches per
move loop, five twelve-stud wheel periods and three twelve-tooth sprocket periods.
The rolling direction matches the tread, and angular travel times rolling radius
equals track travel. The saved-scene audit checks those distances and maps closure
links to their corresponding starting links. `g` renders all eight move samples
from above and in front as `autonomous-armour-g-feet-check.png`; for this vehicle
it checks track direction/contact instead of human feet. Runtime supplies forward
map travel; the base stays fixed for the in-place animation preview. Idle/move
controls and combat clips start at the same rest transform. Death cants and lowers
the turret, gun, optics and aerials, then reuses the terminal render exactly.

All six Blender skills informed this implementation: modeling (closed beveled
plates and bore), materials (dielectric paint versus exposed metal, real AO and
curvature bakes), lighting (aimed product lights), cameras (orthographic source
registration), animation (authored mechanical keys and visibility toggles), and
rendering (CPU draft inspection, explicit GPU final, PNG sequences then encoding).
Every invocation is plain `blender -b --disable-autoexec` through the PATH gate;
no direct application executable, nested slot lock or zero-scale hiding.

```sh
unit=tools/art/anim3d/units/autonomous-armour
# Source and generated fill must exist under assets/autonomous-armour (SOURCES.md).
"$unit/render.sh" build
"$unit/render.sh" b
"$unit/render.sh" finish
"$unit/render.sh" c
"$unit/render.sh" details
"$unit/render.sh" d
for clip in idle move attack hit death; do "$unit/render.sh" "e-$clip"; done
"$unit/render.sh" audit
"$unit/render.sh" pack
"$unit/render.sh" validate
"$unit/render.sh" movie
# Complete host pass from repository root; no arguments:
ROUND=2 tools/art/anim3d/units/autonomous-armour/gpu.sh
```

`gpu.sh` is executable, resolves its checkout, takes no arguments and defaults
ROUND to 2. It checks all saved scenes, audits, then renders every stage serially
with Cycles Metal GPU (96 samples by default). It retains 512/256 PNG masters,
all review sheets/WebPs and the rest comparison; packs and validates the atlas;
and encodes `autonomous-armour-round${ROUND}.mp4` from decoded trimmed frames:
five clips side by side, 2x on cream, eight seconds, H.264/yuv420p, 1600x348,
240 frames. It independently probes that movie and verifies every stage's GPU,
sample count, resolution, master/blend/raw/graded-image hashes before writing
`autonomous-armour-gpu-round${ROUND}.json`. The receipt leaves art approval false.

The direct transcript is `ANIM_ROOT/gpu-logs-autonomous-armour-r${ROUND}.log`;
`autonomous-armour-gpu-status.txt` records running, failed stage/exit, or complete
pending visual review. Missing inputs and CPU-labelled evidence are tested rejection
paths. Unavailable Metal fails explicitly; no CPU fallback is called a GPU pass.
Do not edit an executing shell script: its open file offset can resume mid-token.
The round-two audit passed but its shell caller failed after an in-place script
edit; the complete final run was repeated from stable scripts.

CPU previews at 256 never masquerade as 512 masters. Prior round-one CPU evidence
is preserved in `masters/autonomous-armour/round1-cpu`. No GPU pass is inferred from
old files, a technical validation or a missing driver log. The script never writes
PASS; only visual acceptance against the painting can authorize that marker.

### Autonomous armour trimmed atlas extension

The new candidate metadata uses `format: "trimmed-v1"`. `frame` is the untrimmed
logical 160x160 canvas with anchor `ax:80, ay:139`. `atlas` records physical packed
width/height. `clips` retains rows in idle/move/attack/hit/death order and exact
8/8/10/4/10 frame counts, fps and loop flags. Each clip has `rects`, one per frame:
`{x,y,w,h,ox,oy}`. Crop the physical atlas at `(x,y,w,h)`, then draw the crop at
`(ox,oy)` on its logical 160 canvas; anchored drawing uses
`(ox-ax, oy-ay)`. Identical held frames can share a rectangle within their clip without reducing
the logical frame count. Each clip occupies one variable-height shelf, so `row` is an
ordinal, not a fixed-cell multiplication. Preserve full alpha, all frames and
quality >=75; reject delivery over 200,000 bytes. Reduce tokens with premultiplied
RGBA bicubic sampling, preserving the exact resulting 8-bit alpha on decode.
Raw and graded hashes are rechecked independently during validation. No runtime loader is changed
by this art candidate, and fixed-grid consumers must not infer new crop positions.

### Driver round 2 after the successful round-1 GPU pass

The driver reused the earlier round-two CPU implementation for its round-one GPU
pass. Its receipt verifies Cycles GPU96 at 512, a 192,900-byte Q85 atlas and an
8-second H.264 movie. That exact evidence is preserved externally at
`masters/autonomous-armour/driver-round1-gpu/`; it is not the current geometry.

A less side-on orthographic camera shortens the excessive projected tread run.
The turret shifts 0.15m toward the visible side, its gun mount shifts 0.13m forward,
and the two antenna tips have independently corrected heights. Six separated
road tyres replace seven overlapping tyres. Their radius is derived from the
same five track pitches using 150 degrees of travel; twelve repeated studs close
at five periods. Curved closed wheel dishes and rolled warm worn rims replace
flat concentric cylinders. The audit now rejects intersecting road tyres as well
as testing contact, travel, closure and frozen UV registration.

`animate.py` records generator, source/fill and saved-scene SHA256 values in
`build-inputs.json` once all five scenes exist. GPU preflight and the final receipt
both verify these inputs, rejecting a script or texture change after the build.
This extends the existing raw/graded/atlas hashes. Never treat an older 512 folder
as current evidence after CPU iteration; only fresh GPU manifests establish that.
The current CPU/GPU difference and remaining silhouette/paint gaps belong in the
unit log, and only actual visual acceptance can write PASS.

### Autonomous armour driver round 3

Preserve each incoming GPU receipt, master, review and decoded movie frame before
CPU iteration (`masters/autonomous-armour/driver-round2-gpu/` for this round).
The round-2 handoff succeeded: Cycles GPU96/512, all stages, Q85/192,282-byte atlas
and verified eight-second H.264 movie. Its technical success did not meet the art
bar: the uniform low running gear remained visibly different from the painting.

The belt now follows a closed convex path around raised end sprockets and grounded
road tyres. `common.py` owns that one path for construction and animation. Its
length solves the rolling radii: five track pitches per move loop, five twelve-stud
road-wheel periods and four twelve-tooth sprocket periods. Each link has two thick
beveled pads, a hinge ridge and side pins. The entire front armour receives a smooth
full-depth registration adjustment against the two painted headlight centers.
The close upper-body orthographic framing remains; a conventional perspective fit
could not simultaneously explain the painting's upper and lower proportions.
Do not describe this as an exact solved camera.

A new original generated wheel face is a **pigment texture on solid geometry**.
`prepare.py` averages twelve angular samples to suppress baked directional light
and make the pigment periodic at the wheel's physical closure. UVs follow the axle;
physical lighting and live AO remain world-space. The exact prompt, generator ID,
licence and immutable source hashes live in the unit's provenance files. Existing
generated olive fills, real AO/Pointiness bakes, warm key/cool rim/fill and frozen
histogram grade remain. Cloth and straps are absent from this machine's painting.

Tread-only painting masks now permit frozen source pigment on individual moving
shoes, excluding source wheels, hull and stone. Unseen shoe surfaces retain the
physical/generated finish. Inspect the move seam and newly exposed surfaces:
semantic masking prevents copied wheel hubs, but arbitrary tread pigment is not
mathematically periodic when shoes advance. The decoded loop-seam check and visual
review are both required. The top/front `g` diagnostic hides the upper body to show
the actual running gear; the audit additionally bounds every sampled contact tread
inside the stone's radius, not merely at the stone's height.

The no-argument executable handoff defaults to round 3:

```sh
ROUND=3 tools/art/anim3d/units/autonomous-armour/gpu.sh
```

It still makes every stage, fresh 512/256 masters, the trimmed160 atlas/JSON,
validated decoded-atlas movie and independent GPU provenance receipt. CPU previews
are never 512 masters or a GPU sign-off. Check the current unit `REVIEW.md` and
external step log for exact measurements and remaining defects; no script writes
PASS automatically.
