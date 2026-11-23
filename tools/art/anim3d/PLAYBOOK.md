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

## War Elephant — original mounted-family candidate

The unit-specific pipeline is documented in
[`units/war-elephant/README.md`](units/war-elephant/README.md). It uses original
volumetric elephant geometry, a 20-bone elephant rig and two CC0 MPFB humans,
with the project painting projected onto real surfaces. Generated painted fills
cover unseen surfaces; bevelled timber, thick quilted cloth and sculpted anatomy
provide form. The camera and stationary cream base target the painting, including
its warm #E9CFA0 stone. A single rest-derived grade preserves temporal colour.
Review sheets include the original, render, half split and 50 percent crossfade.
Technical validation does not establish painting parity.

This unit uses the newer 160 px **trimmed v2** atlas contract: `frame` is the
logical canvas and anchor; each clip's `rects` array stores atlas `x,y,w,h` and
logical-canvas `ox,oy` per frame. See the unit README for reconstruction. All 40
frames remain, WebP quality is at least 75 and the atlas is at most 200,000 bytes.
Keep raw 512 px masters and graded 256 px gallery frames outside git. The existing
fixed-cell runtime cannot sample this contract without a trim-aware loader;
this branch does not wire the candidate into the game.

The lead's `ROUND=1 tools/art/anim3d/units/war-elephant/gpu.sh` rerenders on the
serialized host GPU, packs, validates and creates `war-elephant-round1.mp4`.
It uses the shared Blender gate, background mode and disabled autoexec. See the
unit README for short CPU stages and the full reproduction order. No PASS marker
is warranted until the rest comparison and all five clips meet the painting bar.

### War Elephant round 2: finished surfaces and contact

`units/war-elephant/project.py` restarts from the external `sculpt-input.blend`.
It freezes the current MPFB macro mix, finishes static geometry, and fits the
complete elephant, blanket, howdah, tusks and riders in the painting's view.
Weighted anatomy is fitted through inverse skin transforms, retaining its
topology and original weights. Depth is retained; this is neither a cutout nor
a per-frame image warp. The fitted landmarks and sole corrections are recorded
in `masters/war-elephant/registration.json`. Camera registration remains an
approximation, and the riders and trunk still need visual refinement.

Finish subdivision and thickness before projection. Subdivide timber faces
linearly to sample their visible interiors: corners hidden inside neighbouring
posts cannot supply the visible panel's projection weight. A scene ray test and
normal-facing mask exclude occluded backsides. Frozen painting UVs supply 96%
camera-only painted illumination, with physical materials on non-camera rays
and the existing generated skin/textile/wood/linen fills on unseen surfaces.
Standard/None avoids applying AgX to the source pigment a second time. The
physical cream stone has restrained camera-only pigment and live AO, no copied
feet or painted shadows. One rest histogram grade is reused across all clips.

Sole contact is corrected separately for each lower limb before projection.
Death rolls farther onto the flank and tucks the near limbs instead of allowing
their feet to prop up the torso. The audit checks finished-surface UV agreement,
both native human rigs, stationary camera/base, loop closure, ground clearance
and terminal torso height. It is not a full human/howdah collision solver.

`ROUND=2 tools/art/anim3d/units/war-elephant/gpu.sh` is the complete no-argument
host handoff. It checks Metal, repeats projection/animation/audit, renders plain,
rest/details, poses and all 40 frames at GPU512, exports 512/256 copies, packs,
validates and probes the eight-second H.264/yuv420p round movie. It retains a
round log and stage-status file. Every Blender invocation is plain `blender`
on PATH. CPU previews use `deliver.py pack --preview` and are labelled; the
final master gate rejects them. Bicubic token reduction preserves full 8-bit
alpha, independently checked against each decoded trimmed frame. No technical
stage writes an art PASS marker.


### War Elephant driver round 2 follow-up: sourced motion and foot evidence

The original GPU pass succeeded; its frames/master are preserved externally in
`masters/war-elephant/driver-r2-before/`. Updated fitting separates the actual ear
from the shoulder, opens the trunk tip, brings far soles into the painting's
stance, and corrects the officer's grip through native skin weights. Never move
only the texture to cover incorrect anatomy. The hand grip has closed bevelled
geometry; stone grain varies pigment as well as normals.

The common motion standard is proven open motion by default: humans use CC0
Quaternius or free-use CMU; animals use a licensed animated quadruped. This unit
reuses the pinned CC0 Quaternius Horse.glb for Idle/Walk/Hit/Death motion samples,
not its geometry. `motion.py` clears unkeyed channels between actions, handles
Blender action slots and records samples/hash. Its forward -Y maps to elephant
+X. Contact adaptation keeps planted soles stationary while shortening source
swing arcs. Idle/hit displacement and death collapse timing are source-derived;
elephant folding, trunk/ears/tail and riders remain authored. This is explicitly
a partial retarget, not an elephant capture or a full skeletal transfer.

Every move cycle needs top/front foot evidence and contact measurements, not
only the flattering three-quarter camera. Stage `g` produces
`war-elephant-g-feet-check.png` using the actual evaluated lower limbs cut away
above the knees. The audit rejects drift of fully weighted sole vertices from
the contact/swing target above 1e-5 scene units, and checks fixed camera/base,
loop closure and held death. Death ground clearance checks every visible mesh,
including the ear, fringe and straps; a body-only check missed their stone
intersections. Fold the near ear inward before settling. This is not a full
mesh collision solver.

The no-argument GPU handoff includes the new `g` stage, 512/256 masters, trimmed
160 px atlas at quality >=75 and <=200,000 bytes, validation, and the round MP4.
CPU evidence is explicitly labelled and cannot pass the final GPU512 master
gate. Painting parity is still a visual gate; no technical tool writes PASS.

### War Elephant driver round 3: ground-plane fitting and seated motion

The incoming round-two GPU pass succeeded (185,694 bytes at quality 75). Its
complete master/render/review evidence is retained externally under
`masters/war-elephant/driver-r2-gpu-preserved/`. The review still showed a wide
stance, sideways officer forearm, tight trunk hook and overly deep base ellipse.

Keep contact and camera registration coupled: after fitting a sole, a vertical
ground correction changes its screen position. This round translates the final
sole along the ground plane, retaining height and original weights. Knee/calf
contours and the officer forearm/grip are fitted on full-depth skinned geometry.
The lower camera elevation matches the stone ellipse; the base remains circular,
beveled and stationary. A pinned image-generated clean stone plate supplies its
painted grain with alpha used only to blend pigment and fresh AO for contact.
Existing thick straps, folded cloth, timber bevels, generated hidden-surface
fills, product lights and one frozen histogram grade remain in use.

Both riders now use pinned CC0 Quaternius Universal Animation Library seated,
hit and death torso/head deltas. `rider_motion.py` compensates reference/rest axes
and bone rolls, resets sparse source channels and closes loops exactly. Their
seated limbs remain constrained; the attack adds an authored brace. This is a
partial upper-body retarget, not full-body mocap. The audit includes all three
rigs in loop/held-death checks. Feet views and every clip still need visual review;
ground clearance alone cannot prove clean rider/howdah intersections.
Planted soles are also checked against the flat stone top's radius. An apparent
rear-foot gap proved to be shading, not unsupported geometry. The fitted far
rear thigh needs an inward death fold to avoid a calf hooking above the body.

`ROUND=3 tools/art/anim3d/units/war-elephant/gpu.sh` performs the complete GPU512
pass, 512/256 export, trimmed 160 px packing, validation and round movie. Its
default round is now 3 and the stage status updates throughout rendering. CPU256
previews remain explicitly labeled; they cannot pass final master validation.
