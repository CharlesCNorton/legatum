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

## Infantry chapter: Gaesatae, round 1

The Gaesatae unit lives exclusively in `units/gaesatae/`; it does not replace the
spearman's master or shared scripts. Use all six Blender skills. Its CC0 MPFB
anatomy and 53-bone skeleton support the painting's bare tattooed torso, swept
hair and moustache, gold torc, folded trousers, leather boots, convex elongated
wooden shield and overhead iron-tipped spear. The shield, clothing, spear and
hair have real thickness. No image plane or alpha-cutout geometry is used.

The four quality levers are the standard method: (1) calibrate the fixed camera
and rest anatomy against the painting, register the original full-size source
to token bounds, and freeze camera UVs on deforming surfaces with ray visibility
and facing masks; unseen sides use recorded original generated painted fills;
(2) finish geometry with subdivision, folds, thick bindings and beveled metal;
(3) use warm upper-left area key, soft fill, cool rim and actual contact shadows;
(4) fit a bounded RGB histogram correction from the rest image and freeze that
same grade for all clips. Painted illumination is deliberately retained by the
projection layer. It does not establish a match when silhouettes disagree.
The shared cream stone recipe uses sRGB **#E9CFA0**, converted to linear inputs,
with roughness 0.87 and fine grain. Every unit keeps one stationary low disc.

Inspect `gaesatae-f-restpose-compare.png`: painting left, render middle, 50/50
crossfade right. Compare native 256 and 64 pixels, plus face/torc, torso and
shield details. Silhouette, equipment attachment and motion quality remain
visual gates. A technically valid atlas is not a PASS. Never write the PASS file
until rest and all five clips satisfy the art bar.

From the repository root, with existing MPFB installation and painting assets:

```sh
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/gaesatae
"$ANIM_ROOT/venv/bin/python" "$unit/prepare.py"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/build.py"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/project.py"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/animate.py"
CYCLES_DEVICE=CPU RESOLUTION=256 SAMPLES=8 blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/render.py" -- all
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" --movie
```

Every Blender invocation uses plain `blender` on PATH, the machine-wide gate.
Never bypass it or start simultaneous heavy jobs. CPU renders are previews;
`ROUND=1 tools/art/anim3d/units/gaesatae/gpu.sh` is the complete lead handoff.
It requires a real Metal Cycles GPU, renders every stage at 512 pixels, retains
512/256 sets under external `masters/gaesatae/masters/`, rebuilds review images,
packs/validates the atlas and encodes `gaesatae-round${ROUND}.mp4`. The movie
reconstructs trimmed frames, shows five clips side by side at 2x on cream, and
is 8 seconds, H.264, yuv420p. It does not silently fall back to CPU.

### Gaesatae trimmed atlas format (version 2)

The logical frame is 160x160, anchor `(ax,ay)=(80,142)`. The atlas packs one
horizontal variable-width row per clip in idle/move/attack/hit/death order.
`clips[name]` retains `row`, numeric `frames`, `fps` and `loop`, and adds `rects`,
one `{x,y,w,h,ox,oy}` per frame. `(x,y,w,h)` selects the atlas crop; `(ox,oy)`
is its top-left in the original 160px transparent cell. Reconstruct before
anchoring, or draw the crop at `screenAnchor + (ox-ax, oy-ay)`. Do not infer
atlas coordinates from `row * frame.h`. No runtime consumer is changed here.

Packing keeps 8/8/10/4/10 frames, quality 90 down to **75 minimum**, and refuses
anything over **200,000 bytes**. It checks master/render hashes, transparent
margins, rectangles, offsets, motion and identical lossless terminal death frames.
The final death PNG is copied rather than rerendered. Raw, graded and derived
masters remain outside Git. Render manifests name engine, device and samples;
CPU preview masters are never labelled GPU output or upscaled to fake 512px.

### Gaesatae resumed round 2: finished surfaces and planted feet

Resume from the saved `plain.blend`; `project.py` starts from that checkpoint on
every run. `refine.py` preserves the native rig, turns the feet independently of
the braced calves, fits ankle depth and corrects the evaluated leather sole to
`.103 m`. It freezes the current MPFB macro mix and applies surface modifiers
before projection so paint is registered to the actual rendered surface. A
zero-level subdivision modifier is removed instead of applied. Hair, clothes,
shield and straps remain three-dimensional; this is not a cutout. The source
pigment is camera-only, while physical shaders still receive shadows and light
on the hidden surfaces. Existing original generated fills are reused.

The base is still a round stationary disc; its radius, depth position and smaller
bevel improve the footprint. Its camera elevation/ellipse and the hair/hand
contours remain visible differences. The single automatic rest grade stays fixed
for all clips. Do not call this an exact-viewpoint or art-quality pass.

The driver-round-two continuation supersedes the authored idle/move/hit/death.
They use pinned CC0 Quaternius Idle_Loop, Walk_Loop, Hit_Chest and Death01,
retargeted through Blender constraints with full reference/rest and bone-roll
compensation. Walk arms layer the library's idle guard. Calibrate ankle/toe
orientation against anatomical rest before retargeting; never hand-rotate feet
afterward. The painting's outward toe pose belongs only to the braced guard.
Root translation grounds the support sole without changing captured rotations.
Attack remains weapon-specific, with anticipation, extension and recovery.

Every human unit should default to proven CMU or CC0 Quaternius source motion.
Each round renders the actual feet from front and top across the full move
cycle (`gaesatae-g-feet-check.png`). Inspect planted toe heading, support and
sliding. A vertical swing foot may point backward in XY without being a yaw
error; judge heading during stance and compare all rotations to source samples.
This unit audits all 53 bones/40 samples, support contact, exact retargeted foot
rotations, planted heading, virtual-ground stance slip, loop closure, held death,
stationary base and safe scales. It is not a full collision or skin/cloth solver.

Height-only clothing extraction can include the hands of an unposed MPFB body.
Inspect connected components: the accidental finger shells can have more vertices
than the real trousers. Retain the connected pelvis/leg shell by anatomy/evaluated
height; audit against hand/finger weights. Front/top feet review caught four such
islands that a valid atlas and ordinary rest view concealed.

Hair-crown refinement moves the existing full-depth locks/scalp vertices to the
painted silhouette, preserving depth and skin weights. It does not cut geometry
with alpha. Bright generated fills blend as pigment instead of dark multiply;
ash stays restrained. Fine limestone pigment variation supplements actual
product lighting and grain. The frozen automatic rest grade applies to all clips.

The packer uses bicubic 160px reduction, lossless alpha, two-pixel spacing and
reuses identical death rectangles without dropping playback samples. JSON now
includes explicit `atlas:{w,h}`. Validation reconstructs every logical frame and
compares alpha against its source; decoded death frames must also match exactly.
Three regression checks cover offsets/shared frames, grade/alpha preservation,
and WebP alpha round-tripping. `check_delivery.py --gpu` requires GPU512
provenance, both real 512/256 sets, all stage reviews and the eight-second MP4.
CPU previews cannot satisfy that gate.

`gpu.sh` remains executable and takes no arguments. It defaults to round 2,
records its own transcript/status, preflights Metal before modifying masters,
regenerates projection and all clips, audits, renders every stage at GPU512
and the front/top foot diagnostics,
packs/validates and writes the driver's ROUND-named MP4. It never writes PASS.
Missing-input failure is tested without launching Blender. CPU checks do not
prove Metal execution; the lead must run the script and inspect the fresh output.

The prior recovery patch recorded 169,328 bytes at Q85 from authored clips;
those results are historical, not evidence for the new source-motion revision.
Current results are written to `masters/gaesatae/validation.json`,
`geometry-audit.json` and the external Gaesatae log. CPU output is never a GPU
sign-off. Only visual review of the fresh rest/clip images can authorize PASS.
