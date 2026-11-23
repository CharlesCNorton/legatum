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

## Vehicles — propeller aircraft: Fighter (`fighter`)

Unit-owned implementation: `tools/art/anim3d/units/fighter/`. This chapter extends the
vehicles family to an airborne miniature. Do not substitute an infantry body or a
flat image card. The painting has an olive/silver monocoque, two thick wings, tail
surfaces, glazed canopy, four-blade propeller, a curved display support, and one cream
stone disc. Preserve its elevated composition and keep the base stationary.

### Fighter build and review

```sh
tools/art/anim3d/units/fighter/render.sh build
tools/art/anim3d/units/fighter/render.sh finish
tools/art/anim3d/units/fighter/render.sh animate
tools/art/anim3d/units/fighter/render.sh b
tools/art/anim3d/units/fighter/render.sh c
for clip in idle move attack hit death; do
  tools/art/anim3d/units/fighter/render.sh "e-$clip"
done
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/fighter/deliver.py pack
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/fighter/deliver.py movie
```

Every invocation is plain `blender -b --disable-autoexec --python-exit-code 1`,
through the PATH gate, sequentially. No application-binary bypass, thread override,
zero-scale visibility or volumes. Local previews default to Cycles CPU, 256 px,
8 samples. The six installed Blender skills informed closed loft topology,
bevels, layered-action compatibility, material separation, aimed product lighting,
orthographic source calibration, transparent sequence rendering and playback checks.

The standard quality method is: align real geometry to the source camera; freeze
camera-projected painting UVs on that geometry; blend newly exposed surfaces into
licensed generated painted fills; preserve bevels, thickness, worn metal and baked
cavity/edge detail; light with a warm upper-left key, soft fill and cool rim; freeze
one bounded RGB quantile grade from the rest render and apply it to all frames.
`finish.py` bakes real Cycles AO and Geometry Pointiness maps at 512 px on fuselage
and wings. These drive hidden-surface grime and polish. Projection supplies the
painting's visible rivets and panel brushwork, not the silhouette. Generated bomber
paint brushwork is reused with its original CC BY 4.0 provenance and modulates the
appropriate olive, silver or charcoal pigment. No new third-party model is used.

The shared base target is **sRGB #E9CFA0**, approximately linear
`(.815, .624, .352)`, dielectric roughness `.83`, with fine stone bump and a bevelled
rim. The final pixels also depend on lighting, painting projection and grade: inspect
and sample the render, not only the material constant. A pale grey base fails.

Masters live outside git at `$ANIM_ROOT/masters/fighter/`: `plain.blend`,
`fighter.blend`, separate `.blend` files for each clip, baked maps, render manifests,
and real 512/256 image sets. Rebuild → finish → animate after geometry changes;
render manifests and clip hashes reject stale inputs. Reviews are published as each
stage finishes under `$ANIM_ROOT/review/3d-v2/fighter-*`. The rest comparison shows
painting, render, and a 50/50 crossfade, plus a native 64 px comparison. Passing the
atlas validator does not mean the painting-parity bar has been met.

Flight and propeller pivots carry authored idle hover/bank, move, attack run, hit
jolt and stall/crash clips. Exact counts are 8/8/10/4/10; fps 10/12/14/12/10. Only
idle/move loop at runtime; a closing key is excluded from the sampled loop. The
last death samples hold. The support disappears at impact; that is an explicit
round-one presentation limitation pending a broken-support treatment.

### Fighter trimmed atlas v2

The source frame remains 160 × 160; its fixed base anchor is `(79,124)`. Clips keep
`row`, `frames`, `fps`, `loop`, and add `rects`, one entry per frame:
`{x,y,w,h,ox,oy}`. Crop rectangle `(x,y,w,h)` from the atlas and composite it at
`(ox,oy)` in the original 160 px frame. For world-anchor drawing, the crop origin is
`world + (ox-ax, oy-ay) * displayScale`. Packed rows remain idle/move/attack/hit/death,
with two pixels between trimmed crops. `atlas:{w,h}` gives actual decoded dimensions.
This is an extended format, not compatible with a fixed-grid cropper; this lane does
not change the app runtime or replace its static unit painting. Quality is selected
from 90/85/80/75 and packing fails above 200,000 bytes instead of dropping frames or
quality. Validation checks hashes, counts, motion, transparent margins and held death.

### One-command host GPU handoff

```sh
ROUND=1 tools/art/anim3d/units/fighter/gpu.sh
```

No positional arguments; run from repository root. Requires the saved finished
masters. It renders every stage serially with Cycles Metal GPU, 512 px, 64 samples
(override `SAMPLES` if needed), keeps 512 and 256 masters, emits all review images,
rebuilds/validates the trimmed 160 px atlas, and writes `fighter-round${ROUND}.mp4`.
The video reconstructs each trimmed frame using its offsets, shows all five clips
side by side at 2× on cream, and verifies H.264/yuv420p/240 frames at 30 fps (~8 s).
No CPU fallback is allowed on this GPU path. Only a reviewed painting-parity result
may create `fighter-PASS`; scripts never grant themselves art approval.

### Fighter resumed round 2: surface and mechanical review

Preserve the previous editable masters, raw/graded frames and review sheets before
rebuilding (`masters/fighter/round1-preserved`). The supplied round-one manifests
were CPU512/8; those images do not prove a host GPU pass.

The glazing is a full-depth smooth ellipsoid with framing seated on that surface;
free-standing frame loops cannot be repaired by projected paint. The propeller
uses an orthonormal circular plane fitted to source landmarks. The painting's four
tips are not exactly symmetric, so the fit is a documented geometric compromise.
Quaternion rotation is local to the fitted shaft, with closed, thick blades and
separately assigned ochre tips. Do not add a rotation to the parent's Euler X once
the shaft has been tilted. Subdivision/bevels are applied before freezing source
UVs. The existing generated olive fill and six actual AO/Pointiness maps remain.

Source-painted illumination is now a 96% camera-only pigment branch; non-camera
rays and unseen surfaces retain physical materials, generated brushwork and baked
cavity/wear. Standard/None avoids a second highlight compression on that source.
This is specific to the painted-reference workflow. Warm key, soft fill and cool
rim remain. Fit one bounded automatic RGB quantile grade at rest and freeze it
across all clips. Material-space blade exclusions must drive both the pigment
colour and its shader weight, or a static duplicate blade survives in the wing.

The plain circular stone disc has physical top/rim materials, restrained grain,
soft bevel and real contact shadows; it receives no projected painting. This
prevents static aircraft/support shadows from remaining when those objects move.
The complete solid support topples around its foot in death instead of vanishing.
The airframe and support each receive rigid contact correction against the actual
disc footprint and world ground. The final held pose is rendered once then copied
only after verifying every visible mesh/light/camera transform and visibility.

**Motion standard:** humans use CMU free-use or Quaternius CC0 idle/walk/hit/death
retargeted with matching rest bases and bone rolls; animals use native CC0 animated
quadruped motion. Do not hand-correct feet after retargeting. Only weapon-specific
attacks are authored. This aircraft has no human/animal rig or feet: authored rigid
flight/shaft motion is appropriate. Its required `fighter-g-feet-check.png` shows
actual top/front views of all eight move samples, labelled with that exception,
for travel-axis, propeller and stationary-base inspection. Unit-local `SOURCES.md`
and the external ledger record all inputs and licences.

Packing now uses premultiplied bicubic reduction with unchanged 8-bit alpha,
transparent gutters, and shared rectangles for identical frames. It retains all
40 samples and five logical rows. The validator checks decoded alpha byte for
byte, crop bounds/offsets/gutters, timing, motion, exact source/decoded terminal
hold, current master/clip/grade/frame hashes and consistent engine/device/sample
settings. Its decoded-atlas sheet and round MP4 come from the shipped WebP.

`ROUND=2 tools/art/anim3d/units/fighter/gpu.sh` is the complete no-argument host
entry point. It resolves this checkout, refreshes clips from the reviewed master,
audits geometry/contact, renders b/c/all clips/top-front views at real GPU512,
exports 512/256 masters, verifies GPU provenance, packs/validates and encodes the
five-clip 1600×348 eight-second H.264/yuv420p MP4. It retains a round log, status and
hash-bound receipt with `art_approved:false`. Explicit failure guards prevent a
missing input or failed stage from falling through. A CPU preview cannot satisfy
its GPU512 gate. Neither the script nor the technical validator writes art PASS.
