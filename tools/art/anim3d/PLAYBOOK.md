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

## Vehicles — main battle tank (`main-battle-tank`)

This unit uses original full-depth hard-surface geometry: a low hull and cast dome,
long elevated smoothbore, six road wheels per side, 124 separate track links, armoured
skirts, rear fuel drum, rolled canvas, hatches and a small mounted gun. It is a rigid
machine; no human or quadruped motion applies. No national markings or maker logos.
All unit code lives under `tools/art/anim3d/units/main-battle-tank/`, adapted from
`astra/unit-anim-3d-vehicles`; shared spearman scripts remain compatible.

### Required quality and review method

Apply feedback 12–23. Sam's encouragement is a direction, not final art acceptance.
The four levers are standard: (1) freeze the rest-camera painting projection onto
actual finished meshes; (2) finish geometry with bevels, real thickness and visible
relief; (3) warm upper-left product key, soft fill, cool rim and contact shadows;
(4) measure the painting's opaque RGB histogram and apply one bounded rest grade to
all frames. Hidden faces use the recorded generated painted-olive fill, CC0 steel
microstructure and procedural rubber/canvas. Bake actual AO and Pointiness maps for
the two hull pieces and cast turret; do not fabricate those maps.

`refine.py` fits component landmarks in the camera's horizontal/vertical axes while
preserving depth. Wheel pivots remain circular and track paths remain in physical
X/Z planes. The gun axis is fitted separately from the mantlet to avoid turning the
mantlet into an oversized ball. The fixed camera is orthographic; native 256px
painting coordinates guide fitting. It is an approximate registration, not a proof
of painting parity or exact real-world proportions. Inspect front and side views.

The shared base target is **sRGB #E9CFA0**, a plain warm cream stone disc with a darker
rim and fine grain. Material RGB values are linear, so final rendered pixels, not
shader swatches, decide the colour. Project the painting's actual base pigment and
use the inherited Travertine micrograin/cream fallback. Base geometry never animates.
Standard/None colour management preserves the already-lit projected pigment; it is
an intentional painted-image workflow, not a photographic lighting preset. Projection
is camera-ray-only so the painted light does not illuminate other objects.

All six Blender skills are applied: modeling (closed beveled armour), materials
(dielectric paint, real steel, grain and bakes), lighting (key/fill/rim), cameras
(landmark registration), animation (rigid hierarchy and layered action curves), and
rendering (CPU drafts, explicit GPU finals and decoded video checks). Optional
reference-look-calibration is unavailable; landmarks and histogram measurements supply
that comparison. No additional skill installation is needed.

### Build and round-one previews

Run from the repository root; each step is sequential. Rebuild invalidates bakes,
projection, clips and downstream renders. Every Blender invocation is plain
`blender -b --disable-autoexec` through the PATH gate. No application-path bypass,
extra heavy process or zero-scale hiding. All effects are full-thickness translucent
meshes with keyed `hide_render`; no volume grid conversion.

```sh
u=tools/art/anim3d/units/main-battle-tank
"$u/render.sh" build
"$u/render.sh" refine
RENDER_ENGINE=CYCLES SAMPLES=8 "$u/render.sh" b
"$u/render.sh" bake
"$u/render.sh" paint
RENDER_ENGINE=CYCLES SAMPLES=8 "$u/render.sh" c
"$u/render.sh" animate
for stage in details d e-idle e-move e-attack e-hit e-death g audit; do
  RENDER_ENGINE=CYCLES SAMPLES=8 "$u/render.sh" "$stage"
done
```

Masters, six 512px bake maps, source painting, packed textures, separate clip blends,
render receipts and untouched ungraded images remain outside git under
`$ANIM_ROOT/masters/main-battle-tank/`. Each stage immediately emits
`main-battle-tank-b-plain.png`, `-c-textured-lit.png`, `-c-details.png`,
`-d-rig-poses.png`, `-e-<clip>-strip.png` and `-e-<clip>.webp` in `review/3d-v2/`.
`-f-restpose-compare.png` shows painting/render/50-50 crossfade at 256 and 64px.
`-g-feet-check.png` shows top/front views of every move sample; for this unit these
are track/wheel checks. Read incoming unit feedback and keep the unit log honest.

### Motion standard

For human lanes use CMU free-use or Quaternius CC0 captured motion by default for
idle/walk/hit/death, retargeted with Blender or Rokoko and matched rest poses/bone
rolls. Only weapon-specific attack overlays are authored. For animals use a CC0
animated quadruped. Never correct foot direction after a broken retarget; fix the
axis/rest mapping. Every round requires top/front gait views across one move cycle,
forward-pointing feet and no sliding, with source URL/licence in both source logs.

For this machine, track motion uses a closed convex circle-envelope sampled by arc
length. Each road wheel rotates by the identical travelled distance divided by its
radius. The root stays in place for map-driven locomotion; moving tracks indicate
travel along +X. Idle is subtle engine vibration and turret scanning; attack has
recoil and a brief muzzle effect at the fitted muzzle; hit jolts the chassis; death
settles into a scorched stationary wreck with subdued smoke. Counts/fps are idle
8/10, move 8/12, attack 10/14, hit 4/12, death 10/10. Only idle/move loop; final two
death samples are identical. Numerical speed tests supplement visual contact checks;
they cannot prove smooth motion or painting parity.

### Complete GPU handoff and delivery

```sh
ROUND=1 tools/art/anim3d/units/main-battle-tank/gpu.sh
```

No arguments; defaults to Cycles Metal, 512px and 256 samples with denoising. It
checks for Metal, audits saved masters, renders **every** review stage and all five
clips, retains actual 512px and downsampled 256px masters, packs/validates delivery,
and decodes the eight-second H.264/yuv420p `main-battle-tank-round${ROUND}.mp4`.
All five clips appear side by side at 2x on cream; one-shot clips replay after a hold.
The script logs its checkout, exact failure stage and final technical status. Missing
Metal fails explicitly, with no silent CPU fallback or synthetic 512px upscaling.
CPU review images are not GPU approval.

Atlas contract: 160x160 logical cells; transparent per-frame crops in clip-row order
idle/move/attack/hit/death. JSON has `version:2`, `trimmed:true`,
`frame:{w:160,h:160,ax:73.75,ay:111.25}` and
`clips:{name:{row,frames,fps,loop,rects:[{x,y,w,h,ox,oy},...]}}`.
`x/y/w/h` address the atlas; `ox/oy` restore the crop into the logical frame. Draw at
`(anchorX-ax+ox, anchorY-ay+oy)`, scaling every coordinate equally. `row` is ordering,
not a fixed-height atlas coordinate. Duplicate death frames may share a rectangle.
No runtime consumer is changed in this art lane; keep the static painting until the
lead approves and a consumer supports the trimmed schema.

The packer preserves all 40 samples, tests WebP Q95/90/85/80/75 and fails if none fits
**200,000 bytes**. Validation checks trim bounds, exact reconstructed alpha, gutters,
frame counts, actual motion, held death, grade/scene hashes and current masters.
`test_runninggear.py` checks closure, tangent orientation and constant arc-length
speed. `audit.py` checks geometry, pivots, scales, stationary base, recoil and bakes;
its contact-distance diagnostic and the visual sheets remain review evidence.
Scripts never create `main-battle-tank-PASS`: only write it after a human-quality
judgment that rest is hard to distinguish, clips are clean and delivery passes.

### Main battle tank round 2 — roof landmarks and rotating paint

The round-one host pass completed at 512px (Q90, 191,884-byte atlas); that is
technical evidence, not art acceptance. Its review sheets/movie are preserved in
`masters/main-battle-tank/round1-gpu/`. Round two fits the cupola sights, upright
machine-gun receiver, pintle, magazine and hatch separately. Fitting their combined
bounds had retained the wrong thin-bar silhouette. The upper deck now extends
farther forward and the far front sprocket sits lower. The canvas roll has modeled
radial folds, pinched straps, closed webbing and beveled buckles; the long barrel
is thinner. All surface changes are rebaked and reprojected before animation.

Projected highlights and pieces of neighbouring armour must not rotate around road
wheels. `paint.py` gives wheel surfaces a separate material cache key and a fixed
3D projection coordinate object. The wheels, hubs and recess geometry still rotate
at belt travel/radius; the painting's illumination stays fixed. Other components
retain frozen mesh UV projection and the existing generated hidden-face fills.
This is a fixed-camera art technique, not a reusable all-view tank texture. The
geometry audit checks that the wheel coordinate object stays stationary in every
clip. Idle exhaust is smaller and remains close to its outlet; muzzle smoke spreads
away from the barrel instead of stacking into a hard dark tip.

Rebuild with `build`, `refine`, `bake`, `paint`, `c`, `animate`, then the remaining
review stages and `audit`, using Cycles CPU for previews. Preserve one rest grade
across the entire set. The next host command is
`ROUND=2 tools/art/anim3d/units/main-battle-tank/gpu.sh`; it now also runs the three
mechanical route tests before Metal preflight. Inspect fresh GPU results before
writing PASS; CPU previews cannot certify the GPU result.

Movie encoding first validates the atlas against current clip/render hashes, then
records the atlas SHA256 in its receipt. This prevents an old atlas producing a
technically valid but stale movie after a failed pack. The attack-only iteration
path is `ANIMATE_CLIP=attack .../render.sh animate`; rerender `d` and `e-attack`, then
run the full audit, archive, pack and movie checks. Smoke reaching a crop boundary
must be fixed in 3D and rerendered; do not relax the atlas padding check.
