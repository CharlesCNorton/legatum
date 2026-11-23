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

Horseman remains an unapproved art candidate. It uses the licensed CC0 Quaternius
Horse mesh and weighted quadruped skeleton plus MPFB 2.0.18 CC0 anatomy and the
53-bone game-engine rider rig. No cutouts, relief planes or camera-facing anatomy.
The rider is saddle-parented to Torso. Kit, cloth shells, mane and tail locks,
spear, blue meander blanket and tack are editable 3D geometry.

### Inputs and reproduction

`mounted/assets.lock.json` pins the Quaternius mirror and original project painting
and generated fills. `mounted/painted-fills.prompt.txt` records the existing
imagegen coat/linen/bronze/hair fill atlas. All inputs and licences are recorded in
`$ANIM_ROOT/assets/SOURCES.md`. No new service or download is needed this round.
`prepare.py` verifies inputs and aligns the source painting to the committed token.

Use the shared `env.sh`, MPFB installation and plain `blender` on PATH: its shared
gate limits CPU/GPU concurrency. Every invocation is background, three threads,
with autoexec disabled. Never bypass the gate, remove a live lock, invoke the
Blender application directly, or scale an object to zero to hide it.

Initial build (only when the preserved baked master is unavailable):

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/mounted/download.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/mounted/prepare.py
for stage in build materials bake paint animate audit; do
  UNIT=horseman tools/art/anim3d/render.sh "$stage"
done
```

`paint` reloads `masters/horseman-3d/horseman-unpainted.blend` each time. It does
not accumulate changes. Blender masters and packed textures remain in that
external directory; canonical image sets are in `masters/horseman/512/<stage>`
and `masters/horseman/256/<stage>`. A 256 CPU preview is never called a 512 master.
Rebuilding or repainting invalidates every clip. `animate` recreates all five.

### Round-3 method and current limitations

Load Sam's six Blender skills. Model and pose registration precede colour:
`paint.py` solves hands and the near foot against measured reference pixels at
retained depth, raises the upper torso, shortens the spear above its grip, removes
tubular fake chest folds and shapes the solid sleeveless linen shell.
`register.py` applies a smooth displacement from measured horse landmarks to real
bind-space vertices, undoing each weighted skin transform before writing them.
It retains depth, weights and volumetric geometry. Horse-attached tack and mane
receive the same rest correction; there is no per-frame image warp. This is
approximate sculpture, not proof of exact camera/shape parity. Source anatomy
and some gait proportions remain visibly stylized.

The painting now uses **direct frozen camera UVs**, replacing the old extra
landmark warp of colour. Incidence and alpha blend the original brushwork into
existing image-generated fills on unseen surfaces. Painted lighting is retained,
so inspect surfaces exposed by motion. Existing AO/curvature maps and scans are
inherited from the baked master, before the new bind-space sculpture; they are
not new bakes of the revised shape. Bronze edges, bevels, thick cloth, fringes,
straps and hair remain geometry. The source rod tail is replaced by volumetric
locks anchored to its moving tail root, with authored hanging curvature and sway. `reins.py` samples solid sagging curves
between the moving noseband and the rider's hand, keyed at every delivery frame.
It is authored leather motion, not a cloth simulation.

Use a warm upper-left key, cool rim, soft fill, contact shadows and one cream
stone disc. Common cream target: sRGB #E9CFA0; the painting's native lit top is
approximately #F4D2A8. These are display values, not linear shader inputs.
`grade.py` measures 17 foreground RGB quantiles from the rest and painting,
transfers 45 percent into a monotonic LUT, then applies the **same LUT** to every
frame. Raw images are preserved. Recalibrating rest requires rerendering all clips.
`c` emits the painting/render/split/crossfade comparison. Large double contours
mean failure regardless of successful scripts.

### Clips, contact and local previews

Clips retain 8/8/10/4/10 frames at 10/12/14/12/10 fps. Idle and move loop. Move
samples the licensed 28-frame Walk cycle; the extreme canter was rejected because
it exaggerated the revised mesh's thin legs. Attack, hit and death are authored adaptations, not captured motion.
Attack/hit blend from the registered rest; death releases the spear and holds the
last two samples. Render unique frames once and copy held samples, avoiding
sampling noise on the held death. Actual deformed geometry supplies ground
corrections. After bind-space sculpture, original foot controls are no longer
sole coordinates: `audit.py` measures weighted **hoof mesh** heights for support.

```sh
UNIT=horseman tools/art/anim3d/render.sh paint
UNIT=horseman tools/art/anim3d/render.sh animate
UNIT=horseman tools/art/anim3d/render.sh audit
UNIT=horseman RENDER_ENGINE=CYCLES CYCLES_DEVICE=CPU SAMPLES=8 tools/art/anim3d/render.sh c
```

Optional `refresh.py` audits and renders a serial batch in one gated Blender
process. `STAGES=c,d,e-idle,e-move,e-attack,e-hit,e-death` selects stages;
`CLIP=attack,hit,death` regenerates selected clips first; `GRADE_REUSE=1` retains
the common LUT for a geometry-only subset refresh. No second Blender is spawned.
Review outputs are immediately written to `review/3d-v2/horseman-*`.

### One-command GPU handoff

```sh
ROUND=2 tools/art/anim3d/units/horseman/gpu.sh
```

This executable no-argument script runs from the repository root. It prepares
inputs, rebuilds paint/animation, audits, renders every stage with Cycles Metal
GPU at 512 (default 64 samples, denoised), retains 512/256 image sets, packs,
validates, and creates `horseman-round${ROUND}.mp4`. No GPU silently falls back to
CPU. The movie reconstructs trimmed frames before placing all five clips side by
side at 2x on cream; ffprobe checks 240 frames, 8 seconds, H.264 yuv420p. The script
never writes PASS: fresh human/agent visual judgment is still required.

### Trimmed atlas format, version 2

`mounted/pack.py` packs all 40 downsampled **160 px** frames in five clip rows,
trimming only empty alpha margins with one-pixel gutters. It quantizes only alpha to 32 levels (at most 4/255 error), tries quality 90/85/80/75, and refuses to replace delivery above
200,000 bytes. No frame dropping, RGB posterization or quality below 75.

The atlas and JSON remain `app/src/assets/units/anim/horseman.{webp,json}`:

```json
{
  "version": 2,
  "layout": "trimmed-rows",
  "frame": {"w": 160, "h": 160, "ax": 79, "ay": 138},
  "atlas": {"w": 0, "h": 0},
  "clips": {
    "idle": {"row": 0, "frames": 8, "fps": 10, "loop": true,
      "rects": [{"x": 0, "y": 0, "w": 0, "h": 0, "ox": 0, "oy": 0}]}
  }
}
```

The zeroes illustrate fields, not actual bounds. `rects[i]` gives atlas source
coordinates and size; paste at `(ox,oy)` on a transparent 160x160 canvas. The
untrimmed anchor is `(ax,ay)`; direct drawing relative to a map anchor uses
`(ox-ax,oy-ay)`. `row` is the semantic clip order, **not a fixed y stride**.
Each of idle/move/attack/hit/death has its full rectangle list. No game runtime is
changed; its loader must support this format before activating the candidate.

The pack report binds current blend, grade, frame, metadata and atlas hashes.
Validation reconstructs every decoded frame, checks exact quantized alpha and a 4/255 source-alpha error limit, rectangle
bounds/non-overlap, counts, timing, motion, clipping margins, held death, quality
and bytes. Technical passes never establish painted parity or full collision
freedom. Keep `horseman-PASS` absent until the rest is hard to distinguish from
the painting at 256/64 and all five clips are visually clean.
