# MPFB spearman pipeline

This work is a spearman-only art candidate. The body is MPFB anatomy, with its face, hands, toes, topology and skin weights. No primitive body, painted relief planes or commercial character service is used. The armour and equipment are original code-built surfaces fitted around that body. Review status and measurements are recorded in `REVIEW.md`; a successful bake or small atlas does not establish art approval.

## Isolated installation

Blender 5.3.0 (build `02f0899d78e3`) was already installed. MPFB 2.0.18 is installed from the official GitHub release tag under `~/LegatumRuns/anim-pilot/blender-user/extensions/user_default/mpfb`. Its software licence is GPL-3.0-or-later; the body, morphs, weights and MakeHuman system asset pack are CC0. MPFB's standard `game_engine` rig has 53 bones. Rigify and Rokoko are unnecessary for this implementation.

All downloads go to `~/LegatumRuns/anim-pilot/assets/`; `SOURCES.md`, `materials-manifest.json` and `install-sha256.json` there record URLs, versions, licences and hashes. See also the repository's central art provenance table. Python/Pillow 13.0.0 lives in `~/LegatumRuns/anim-pilot/venv`, not the repository or system Python. Masters, bakes, texture maps and rendered frames live in `~/LegatumRuns/anim-pilot/masters/spearman-3d-v2/`. Nothing uploads them.

```sh
python3 tools/art/anim3d/setup.py
```

The system pack is about 268 MiB and its official server can be slow. Interrupted downloads resume; ZIP validation precedes extraction. `env.sh` sets Blender resource/config/script/data/cache paths. Blender's thumbnail writer nevertheless tries `~/.thumbnails`; the sandbox denies that nonessential write. `nice -n 10` is always invoked; this sandbox denies its priority adjustment. The four-thread cap remains in force. Every heavy entry point takes one shared atomic lock at `~/LegatumRuns/anim-pilot/blender-heavy.lock`; never delete a live lock.

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

`materials.py` uses ambientCG Metal034, Fabric030 and Travertine001 plus Poly Haven brown_leather and fine_grained_wood, all CC0. Pigment grading, multiscale hammering and visible edge materials supplement the scans. `bake.py` unwraps code geometry and bakes 512 px ambient occlusion and Cycles Pointiness curvature for cuirass, helmet, shield and skin. These are actual scene bakes, not fabricated maps. AO darkens cavities and curvature drives restrained metal edge wear. Maps are packed into the master and saved separately in `textures/baked/`. `paint.py` adds our original painting's shield brushwork with a calibrated UV map on the convex 3D aspis, blended with the PBR material; it is ordinary texture mapping, not a relief plane. This texture retains some painted lighting, so multi-view reuse needs review. `finish.py` adds crest fibre highlights and adjusts bronze colour. Both stages are repeatable; the `paint-clips` and `finish-clips` stages can update already baked clips after a material-only revision.

`b` emits front, three-quarter and side views beside the painting. `c` emits a three-quarter comparison at native 256 and 64 px. Review files are written immediately to `~/LegatumRuns/anim-pilot/review/3d-v2/`; inspect and critique them before more expensive renders. The first `b` sheet is deliberately retained as first-stage evidence.

## Motion and cloth

CMU 77_02 is standing and 02_01 is walking. The BVHs are Bruce Hahne's 2010 MotionBuilder conversion, retrieved from the una-dinosauria mirror. The accompanying licence permits research and commercial use and adds no restrictions on the conversion. Raw motion stays outside git. The data used in this project was obtained from mocap.cs.cmu.edu; the database was created with funding from NSF EIA-0196217.

`mocap.py` parses BVH channel order and computes forward kinematics, removes travel/yaw, and supplies real captured motion to `animate.py`. Idle uses standing torso deltas; march retargets sagittal leg motion and adds a shield-bearing guard. The weapon arm intentionally does not copy free-walking arm swing. Attack, hit and death are authored keys on the same MPFB rig. This is a reusable retargeting starting point, not a universal full-body motion solver.

```sh
for clip in idle move attack hit death; do
  tools/art/anim3d/render.sh "animate-$clip"
  RENDER_ENGINE=CYCLES SAMPLES=16 tools/art/anim3d/render.sh "e-$clip"
done
RENDER_ENGINE=CYCLES tools/art/anim3d/render.sh d
```

Every clip has a one-second cloth pre-roll, followed by actual cloth simulation baked to its separate `.blend`. The five output lengths are 8/8/10/4/10 at 10/12/14/12/10 fps; idle and move loop. The death's last two output samples use the same settled frame. `d` shows four attack poses. Each `e-*` writes a PNG strip with native 256 px cells and 64 px versions, plus animated WebP. Review animations loop for inspection even when the runtime clip is non-looping.

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

Packing preserves all 40 frames, creates a 2560 × 1280 transparent WebP grid, quantizes alpha to 32 levels, and selects quality 85–60 while enforcing **200,000 bytes**. It refuses to overwrite delivery with an oversized atlas. The JSON format is exactly `{frame:{w,h,ax,ay}, clips:{name:{row,frames,fps,loop}}}`, anchor `(127,221)`. `pack.json` binds the atlas to each raw frame by SHA256. `validate.py` checks decoded size, metadata, all clips, alpha, padding, clipping margins, actual motion and held death. `audit.py` checks saved geometry, cloth, source topology and stationary base across all samples.

The review bar is the original painting: equally rich at 256 px, same identity and scale at 64 px, convincing anatomy and equipment, no plastic, blurred or toy-like finish. Compare source and render side by side; inspect chest, helmet and shield close-ups. Check planted feet, grip, spear clipping, cloth intersections, terminal death and the loop seam in motion. No technical check substitutes for the lead's art verdict. Keep the existing painting in the game until that bar is met. No app runtime is changed by this pipeline.

For the next unit, start new external master and review directories; calibrate the painting's camera, proportions and anchor first. Adjust the MPFB macro targets, fit new kit to the same skeletal segments, select and license suitable captured motion, then author the combat keys. Repeat the plain, textured, pose and per-clip reviews before packing. Reuse the download, bake, retarget and validation approach; do not treat a copied spearman mesh, texture or motion as finished art for another unit.

## Mounted family — Horseman

The mounted candidate uses **true 3D** throughout: Quaternius' CC0 `Horse` mesh,
its original weighted quadruped skeleton and sampled animation, plus a separately
created MPFB 2.0.18 male with the native game-engine rig, skin and eyes. No painting
cutouts, relief planes or camera-facing body parts are used. The bay coat, black
mane/tail/socks, narrow white blaze, pale pastern markings, ivory riding tunic, bronze helmet
and upright iron-tipped spear follow `horseman-256.png`. The short crest, tack,
split tunic, blue Greek-key saddle blanket and spear are editable geometry. Tail
fibres are skinned to the seven-bone source chain; a rigid-tail experiment was rejected. The rider rig is
bone-parented to the horse's `Torso`; its limbs and garments remain skinned.

### Sources and external masters

`mounted/assets.lock.json` pins the exact downloaded horse and its SHA256.
Quaternius' official Ultimate Animated Animal Pack page identifies the July 2021
pack and CC0 licence. Its Drive download returned HTML in this environment, so the
file comes from the explicitly recorded `trebeljahr/quaternius-showcase` mirror
at a pinned commit. `mounted/download.py` verifies that checksum. The original
horse has 13 named clips, including `Gallop`, `Idle`, `Death` and hit reactions.
The skin and scan licences are the inherited MPFB/CC0 sources described above.
`$ANIM_ROOT/assets/SOURCES.md` records the source, mirror, licence and painting.

All raw assets, packed textures, `.blend` masters, bakes, frames and logs stay in
`~/LegatumRuns/anim-pilot/`, under `assets/horseman/` and `masters/horseman-3d/`.
The old `masters/horseman/` experiment is not used or overwritten. Only scripts,
source lock, delivery atlas/JSON and documentation belong in git.

### Build, texture and review

Use the shared installation and `env.sh`. All Blender calls go through the
current `~/LegatumRuns/anim-pilot/bin/blender-slot` gate. During this round the lead
changed it to **one machine-wide Blender process, three threads**, shared with
other animation work. Never bypass it, remove a live lock, invoke a UI Blender,
or scale an effect to zero to hide it. Keep CPU checks short. Mounted scripts
explicitly set three render threads and invoke background Blender.

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/mounted/download.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/mounted/prepare.py
UNIT=horseman tools/art/anim3d/render.sh build
UNIT=horseman RENDER_ENGINE=CYCLES SAMPLES=8 tools/art/anim3d/render.sh b
UNIT=horseman tools/art/anim3d/render.sh materials
UNIT=horseman tools/art/anim3d/render.sh bake
UNIT=horseman tools/art/anim3d/render.sh paint
UNIT=horseman RENDER_ENGINE=CYCLES SAMPLES=12 tools/art/anim3d/render.sh c
UNIT=horseman RENDER_ENGINE=CYCLES RESOLUTION=512 SAMPLES=12 tools/art/anim3d/render.sh c-details
UNIT=horseman tools/art/anim3d/render.sh animate
UNIT=horseman tools/art/anim3d/render.sh audit
UNIT=horseman RENDER_ENGINE=CYCLES SAMPLES=8 tools/art/anim3d/render.sh d
for clip in idle move attack hit death; do
  UNIT=horseman RENDER_ENGINE=CYCLES SAMPLES=8 tools/art/anim3d/render.sh "e-$clip"
done
```

`mounted/build.py` reuses infantry mesh/fitting/joint helpers; `materials.py`
reuses its CC0 box-projected scan helper. Rebuilding invalidates all material bakes
and clips. Bronze helmet and MPFB skin receive actual 256 px AO/Pointiness bakes;
the horse receives a shared 512 px AO/Pointiness bake across its material slots.
Bakes and manifests are external and packed in the masters. Procedural pigment,
scan detail, cavity shading, bright rolled metal edges and individual mane fibres
supplement them. This is a candidate finish, not a claim of painting parity.

Import gotchas: the glTF has split vertices for flat normals; weld coincident
vertices **before** subdivision, or the horse becomes disconnected plates. Its
armature is scaled 100 and the action supplies the coordinate rotation: evaluate
an action before fitting anything. Keep its transform hierarchy intact and scale
its root. Update the dependency graph before preserving `matrix_world` while
bone-parenting, especially for scaled saddle and rosette meshes. MPFB's asset
import removes unused materials: retain material fake users until assigned.

Review files are emitted immediately to `review/3d-v2/horseman-<stage>.png`:
`b-plain`, `c-textured-lit`, `c-details`, `d-rig-poses`, and each `e-<clip>-strip`.
The `e-<clip>.webp` files are animation previews. They loop for review even when
the runtime clip does not. `horseman-log.md` records failures as well as progress;
read `horseman-FEEDBACK.md` before each round. The base and camera are shared by
all five clips.

### Motion and contact

The 8-frame idle samples Quaternius `Idle`, with rider breathing and a raised
near foreleg taken from `Walk` frame 19 to approach the painting's stepping pose. The 8-frame move
adapts the source's actual 14-frame `Gallop` trajectories to a **three-beat canter**.
`gait.py` reads the glTF foot trajectories without Blender: source contacts occur
at approximately 6/8/12/0. Time-warping the source trajectories to stance starts at 0, .23, .23 and .46
pairs right fore with left hind, followed by left fore and suspension. Stances
occupy .34 of the cycle; merely shifting foreleg phase left excessive airtime,
so that earlier attempt was rejected. The audit limits unsupported samples to
at most two of eight. It retains
source joint paths, torso and tail motion; it is an authored timing adaptation,
not captured canter data. Check diagonal contact and foot sliding in motion. Attack uses that gait with a short surge, an authored rider lean and
spear couch/thrust. Hit samples `Idle_HitReact_Left` with rider recoil. Death
samples `Death`, adds front-leg flexion, removes the source's sideways travel,
corrects the horse's ground contact and keeps the slumped rider above the base.
The spear releases during the fall and settles across the stone; hit tips the
blade forward so the recoil stays inside the fixed camera.
Those contact corrections are authored presentation keys, not a physics sim.
Reins retain a slack saddle-attached shape and need intersection review at extreme
head poses; this is not simulated leather or cloth.

Clips are baked to independent masters at integer delivery frames. The last two
death samples point to the same settled frame. Render that unique frame once and
reuse its pixels: two Cycles invocations at the same frame can still differ
slightly after sampling/denoising.
The audit checks MPFB topology, both armature modifiers, the rider's saddle parent,
the immutable base and horse/rider height bounds at every output sample. Pixel
validation separately checks all 40 samples, transparency, padding, size, motion,
frame margins and held death. Neither audit approves the art or guarantees no
intersection between every piece of tack.

### Host GPU rerender and delivery

Once the masters exist, the lead can rerender them through the same entry point;
Eevee explicitly uses Metal and does not silently fall back:

```sh
UNIT=horseman tools/art/anim3d/render.sh c
UNIT=horseman RESOLUTION=512 tools/art/anim3d/render.sh c-details
UNIT=horseman tools/art/anim3d/render.sh d
for clip in idle move attack hit death; do
  UNIT=horseman tools/art/anim3d/render.sh "e-$clip"
done
source tools/art/anim3d/env.sh
RENDER_ENGINE=BLENDER_EEVEE "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/mounted/pack.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/mounted/validate.py
UNIT=horseman tools/art/anim3d/render.sh audit
```

Delivery is `app/src/assets/units/anim/horseman.{webp,json}`, the existing
2560×1280 grid with transparent 256×256 cells, clip rows idle/move/attack/hit/death,
8/8/10/4/10 frames, anchor `(127,221)`, and at most 200,000 bytes. Packing never
silently reduces frame counts. `horseman-pack.json` and `horseman-validation.json`
in the external review directory bind the delivery to its renders. GPU results
need a fresh visual review beside the painting at 256 and 64 px. No runtime
loader is changed and the existing painted unit remains the game asset.

### Mounted painting-projection and grading standard

Apply `paint` after scans/bakes and before `animate`. The bake saves an unpainted
master, and each paint pass reloads it, so projection edits do not accumulate.
`prepare.py` aligns the full original painting's alpha bounds to the committed
256 px token at 1024 px, and splits the generated fill atlas into coat, linen,
bronze and hair. Both external input hashes are pinned. The generated image is
original project artwork made with the built-in imagegen tool; the exact prompt
is `mounted/painted-fills.prompt.txt`. Rebuilding elsewhere requires those external
masters, not an unrecorded regenerated approximation. They are packed into the
saved `.blend` for the lead's renders.

`paint.py` creates fixed projected UV coordinates on the actual weighted mesh,
using the rest camera and documented anatomical landmark corrections. Separate
coat, linen and skin masks prevent cross-material projection spill. The
painting's original brushwork supplies most visible colour; vertex incidence and
image alpha blend it into generated fills on unseen sides. Projection is not a
billboard and does not change mesh alpha. It does carry painted lighting, and
landmark alignment is approximate: inspect eyes, knees, cloth borders and seams
when poses expose other surfaces. An aligned colour texture cannot repair the
wrong anatomy. Subsequent rounds should improve sculpt/pose registration before
increasing projection strength. The blue meander border, fringe, straps and
bronze discs remain geometry. Reins still need a more complete dynamic solution.

Use one warm cream stone material, a low single disc with a darker side and fine
grain. The reviewer's common target is sRGB **#E9CFA0**; sampling the horseman
painting's lit top at native pixels `(100,218)-(153,224)` gives median **#F4D2A8**.
Those are displayed colour targets, not values to paste into a linear shader
without lighting calibration. The mounted material uses warm pigment under the
key light, then the painting-derived grade below. Keep it shared across every clip.

`grade.py` derives 17 foreground quantiles per RGB channel from the rest render
and painting, blends 45 percent of that transfer into a monotonic LUT, then uses
that **same LUT** for every frame. Raw, ungraded images remain in each stage's
`raw/` folder. The grade hash is recorded with the render. Never independently
match each frame: temporal colour pumping would result. Rest review also emits
`horseman-f-restpose-compare.png`: original, 3D, half-split and 50 percent crossfade.
Judge the double contours in that crossfade honestly; file generation is not a
claim that a viewer cannot distinguish the render from the painting.

For final host Cycles renders, use the same entry point with
`RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64`. It explicitly selects Metal
and denoising and refuses a silent CPU fallback. The sandbox default remains
`RENDER_ENGINE=CYCLES` with `CYCLES_DEVICE=CPU`. Example:

```sh
UNIT=horseman RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64 tools/art/anim3d/render.sh c
for clip in idle move attack hit death; do
  UNIT=horseman RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64 tools/art/anim3d/render.sh "e-$clip"
done
```

After a new GPU rest render, rerender **all** clips before packing because the
colour grade may have changed. The pack report records each render's engine,
device, grade hash and blend hash, alongside all source-frame checksums.

For a serial review batch under one gate acquisition, the optional mounted
`refresh.py` runs the audit and requested render stages in one background Blender
process. It never starts another Blender. `CLIP=move` regenerates only move;
`STAGES=c,c-details,e-move` selects reviews. `GRADE_REUSE=1` retains the existing
rest LUT for a geometry-only refresh, so unchanged clips remain colour-consistent.
The normal per-stage entry points above remain the lead's default.

Mounted CPU delivery uses 16 alpha levels and chooses WebP quality 85–55 while
enforcing 200,000 bytes. The pack report records the actual choice. No RGB
posterization, frame dropping or spatial downscaling is used to meet the cap.

`MARKINGS=1` on a serial refresh applies the four white pastern markings to
existing master/clip files before rendering. Clean builds already include them;
this material-only updater preserves the source motion and dark horn hooves.
