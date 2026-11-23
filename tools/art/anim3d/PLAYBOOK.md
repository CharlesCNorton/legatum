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

## Shared painted-miniature method (round two)

Judge the rest pose before motion: painting on the left, render on the right, and a 50/50 crossfade,
at both 256 and 64 px, named `<slug>-f-restpose-compare.png`. Passing an atlas validator is not art
approval. The target is a nearly indistinguishable rest pose, including silhouette and equipment.

The four quality levers, in order:

1. Match the painting's viewpoint and pose, then project its brushwork onto the actual meshes through
   that camera. Use image-generated fills for unseen surfaces and blend at seams. Do not use a flat
   cutout, or describe independently stretched texture regions as an exact camera match. Record any
   local landmark corrections and remaining registration error.
2. Finish geometry: beveled hard edges, thick straps with stitched edges and buckles, highlighted
   buttons, folded and subdivided cloth, recognizable face and hands. Texture is not a substitute
   for missing relief, contact or silhouette.
3. Light as a painted miniature in a product photograph: warm upper-left key, broad soft fill,
   cooler restrained rim and contact shadows. Use AgX, Cycles and denoising for the final GPU pass.
4. Automatically sample opaque source/render pixels to fit contrast, saturation and colour balance.
   Fit once at rest and apply that same transform to the entire clip set; per-frame fitting flickers.

The shared base palette is sRGB **cream `#E9CFA0`** on top, with a darker warm rim (`#BA9968` in the
siege shader). Convert sRGB to scene-linear before assigning a shader colour; do not enter the 8-bit
triplet directly. Judge the *lit and graded pixels* too: a numeric material match does not prove a
perceptual match. The base is stationary, plain stone, without an era-metal ring.

## Siege — field cannon

One MPFB 2.0.18 gunner (53-bone `game_engine` rig) wears navy wool, red facings, ivory breeches and
crossbelts, black gaiters/shako and a moustache. The painting has a closed blue coat: the erroneous
vertical ivory waistcoat strip is removed. The torso leans toward the gun before the arms are solved;
the left arm is solved so the palm rests on the transformed barrel crown throughout idle.
The other hand holds the sponge rammer. No primitive body, billboard or commercial character asset
is substituted for the native anatomy.

The gun is editable geometry: hollow lathed barrel, mouldings, cascabel, trunnions, olive oak carriage,
axle, twelve open spokes per wheel, flat iron tyres, hub bands and iron fastenings. The wheel track and
yaw are adjusted toward the painting. Broader irregular coat/sleeve folds, real belt thickness, both
stitched edges, a raised rectangular buckle/pin and brass buttons address the chest/crossbelt critique.
The dark mottled barrel has aged roughness; mouldings use aged bronze rather than bright gold rings.
Broader tyres have neutral scuffed iron, varied roughness, polished arrises and felloe nails.

All family code is in `tools/art/anim3d/siege/`. `ANIM_FAMILY=siege` selects it through the shared
renderer. Every Blender invocation uses **`blender` on PATH**, always `-b --disable-autoexec`; the
machine-wide gate owns serialization, its three-thread cap and retry policy. Do not bypass it with
an application path or a direct private wrapper. All six installed `blender-*` skills were applied.

Masters and images live outside git under `~/LegatumRuns/anim-pilot/masters/field-cannon/`.
`assets/field-cannon/painting-source.png` is the original painting; existing CC0 Metal034, Fabric030,
Travertine001 and Poly Haven wood/leather remain in use. The original image-generated
`painted-navy-wool.png` fills unseen cloth. No new external asset licence is introduced. The central
provenance table and external `assets/SOURCES.md` identify these sources.

### Build, paint and judge

```sh
export ANIM_FAMILY=siege
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/siege/prepare.py
tools/art/anim3d/render.sh build
RENDER_ENGINE=CYCLES CYCLES_DEVICE=CPU SAMPLES=8 RESOLUTION=256 tools/art/anim3d/render.sh b
tools/art/anim3d/render.sh materials
tools/art/anim3d/render.sh bake
tools/art/anim3d/render.sh paint
tools/art/anim3d/render.sh finish
RENDER_ENGINE=CYCLES CYCLES_DEVICE=CPU SAMPLES=12 RESOLUTION=256 tools/art/anim3d/render.sh c
```

Build invalidates all materials, bakes and clips. Bakes are actual geometry AO/curvature. `paint.py`
uses a shared rest-camera projection for coat, sleeves and breeches, with material-selective alpha
masks to prevent painted crossbelts duplicating the real geometry. Face, shako and barrel still have
local landmark corrections. `projection.json` records those exceptions; the camera/pose match is
approximate, not the promised near-identical rest result. Facing masks blend to the generated/scanned
fills as surfaces turn away. Painted highlights remain in the base colour, so inspect double lighting
and motion-revealed areas rather than treating the texture as intrinsic albedo.

`finish.py` supplies the aged surfaces, cloth sheen, shared base palette and product lights. Run it
once after paint (it is a build stage, not an additive touch-up to call repeatedly). `grade.py` writes
an alpha-masked rest calibration and reuses it for every clip. It excludes transparent black from the
contrast pivot. Raw PNGs stay in each stage's `ungraded/`; repeated review of the same render is
idempotent. Always render/review `c` first to refresh the calibration after a material or lighting edit.

The renderer defaults to **512 px** and keeps those PNG masters; `review.py` also saves
`gallery256/<stage>/` PNGs for gallery/marketing. A 256 px CPU preview is explicitly a preview, not a
512 px master. Review PNGs appear immediately under `review/3d-v2/` as
`field-cannon-b-plain.png`, `field-cannon-c-textured-lit.png`, `field-cannon-c-details.png`,
`field-cannon-d-rig-poses.png`, `field-cannon-e-<clip>-strip.png`, and
`field-cannon-f-restpose-compare.png`, plus animated WebP previews. Read the complete feedback and
append findings to `field-cannon-log.md` between rounds.

### Motion, contact and final render

Clips retain **8/8/10/4/10 frames** at **10/12/14/12/10 fps**; only idle and move loop. Idle solves the
resting palm after shoulder motion, subtracting the hand length to obtain a reachable wrist target. Move is an in-place push with the rammer stowed; runtime supplies
map travel. Wheel angle is exactly `(virtual travel + local recoil) / 0.48`; twelve-spoke symmetry
closes the move loop. Attack has recoil, brief solid muzzle flash and bounded smoke lobes. Effects
use keyed `hide_render`, never near-zero scales (the old approach crashed Cycles/OpenVDB). Death
releases the rammer, tips the gun and settles evaluated geometry on the base. Its last two poses and
source PNGs are identical; the second terminal PNG is reused after asserting all transforms match.

Lead's final host GPU pass, from this branch's checkout: run
`tools/art/anim3d/siege/gpu-final.sh`. It audits geometry, renders 512 px at 64 samples, packs and
validates the saved external master. The equivalent individual stages are:

```sh
export ANIM_FAMILY=siege RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64 RESOLUTION=512
tools/art/anim3d/render.sh animate
tools/art/anim3d/render.sh c
tools/art/anim3d/render.sh detail
tools/art/anim3d/render.sh d
for clip in idle move attack hit death; do tools/art/anim3d/render.sh "e-$clip"; done
tools/art/anim3d/render.sh pack
tools/art/anim3d/render.sh validate
tools/art/anim3d/render.sh audit
```

The Metal device is required for this GPU path; it never silently falls back. CPU reviews use explicit
`CYCLES_DEVICE=CPU` and low samples. `round.py` can run the same sequential stages in one gated
process and now respects `RESOLUTION`/`SAMPLES`; `SIEGE_REUSE_MASTER=1` starts with animation of the
existing finished master. Final GPU frames must be repacked and reviewed afresh.

### Atlas decision and measured alternatives

Use **160 px logical cells, bicubic reduction in premultiplied RGBA, per-frame trimming, lossy WebP
colour at quality >=75 and lossless 8-bit alpha**. Preserve all 40 frames and their timing. Bicubic is
chosen for token reduction: Lanczos ringing creates many low-opacity perimeter pixels which are
expensive to encode losslessly. This is a resampling choice, not alpha quantization. The encoder's
alpha is checked byte-for-byte after decode. Identical logical frames share an encoded rectangle
without removing a playback sample; this makes the final death hold identical in decoded RGB too. Retain the 512 px masters and 256 px gallery copies.

Measured on the **round-one Cycles GPU / 64-sample / 256 px** PNGs (decimal bytes; these are not
estimates for the revised geometry):

| Option | Frames | Q75 bytes | Q85 bytes |
| --- | ---: | ---: | ---: |
| 256 grid, lossless alpha | 40 | 293,052 | 383,330 |
| 256 trimmed, lossless alpha | 40 | 298,648 | 390,956 |
| 256 trimmed, idle 6 / hit 3 | 37 | 272,566 | 356,012 |
| 256 trimmed, old 32-level alpha | 40 | 284,130 | 374,500 |
| 160 grid, Lanczos / lossless alpha | 40 | 223,266 | 275,906 |
| 160 trimmed, Lanczos / lossless alpha | 40 | 228,124 | 279,744 |
| 128 trimmed, Lanczos / lossless alpha | 40 | 169,718 | 207,448 |
| **160 trimmed, bicubic / lossless alpha** | **40** | **174,566** | **220,468** |

The chosen 160 px/bicubic option also fits at **Q80: 196,242 bytes** on those GPU frames. Fully
lossless colour+alpha at 160 px/Lanczos costs **791,132 bytes**. cwebp's picture preset with sharp YUV,
10 analysis passes and best alpha filtering reached 222,920 bytes at Q75; SNS=100 reached 214,018,
still over the cap. The table predates identical-frame rectangle reuse, which saves additional bytes.
Frame trimming reduces raster area, but not necessarily WebP bytes: transparent
blocks already compress well. Fewer idle/hit samples save too little at 256 px and are not shipped.

`pack.py` tries Q90/85/80/75 and three deterministic shelf widths, selecting the smallest layout at
the highest fitting quality. It refuses to write an over-budget atlas and never goes below 75. If a
new GPU render still fails, report the measured result instead of silently dropping frames or quality.
It writes `app/src/assets/units/anim/field-cannon.{webp,json}`. Hashes, engine/sample provenance,
resampler, quality and attempted sizes go to `field-cannon-pack.json` outside git. Reproduce the full
option matrix with `python tools/art/anim3d/siege/pack.py --measure`; `--renders` and `--report` select
an archived render folder and separate report. The original GPU evidence is retained in
`masters/field-cannon/round1-backup/renders/` and `field-cannon-atlas-options-round1-gpu.json`.

### Round-two candidate delivery

The revised **512 px / Cycles CPU / 8-sample** preview set packs to **184,654 bytes at Q80**,
640 × 1233 atlas pixels. All 40 playback samples remain, referencing 37 unique rectangles; the
three exact duplicate images are stored once. Q85 was 207,096 bytes or more, so the Q80 result is
intentional. This is a measured CPU candidate, not the pending 64-sample GPU delivery. All 40 PNG
masters are 512 px and all 40 gallery copies are 256 px. `field-cannon-g-delivery.png` compares the
source painting, render and decoded atlas at 256/64; `field-cannon-g-decoded-atlas.png` shows every
reconstructed logical frame. The 512 px detail sheet uses the full painting, not an enlarged thumbnail.

Verdict: improved leaning/palm contact, distinct scuffed iron tyres, dark aged barrel, cream base and
cloth relief. At 64 px it remains recognizably the same field cannon. At 256 px the gunner is still
slimmer than the reference; face, tailoring and belt drape remain simpler, and the camera/pose are not
an exact match (silhouette overlap about 72%). Final sampled luminance spread is 65.39 vs painting
65.54, and mean HSV saturation 85.51 vs 84.66. Matching those statistics does not establish art quality.
GPU64 rendering and the lead's art judgment remain required.

### Trimmed JSON format, version 2

```json
{
  "version": 2,
  "atlas": {"w": 800, "h": 1000},
  "frame": {"w": 160, "h": 160, "ax": 79.375, "ay": 138.125},
  "clips": {
    "idle": {
      "frames": 8, "fps": 10, "loop": true,
      "rects": [{"x": 1, "y": 1, "w": 124, "h": 140, "ox": 18, "oy": 12}]
    }
  }
}
```

Illustrative dimensions/rectangle only: each real clip has exactly `frames` rectangles in playback
order. `x/y/w/h` locate the cropped pixels in the atlas; `ox/oy` place them back into the original
160-square logical cell. `ax/ay` are the old `(127,221)` anchor scaled by 160/256; retain the fractional
values. For draw scale `s` and world anchor `(X,Y)`, draw the source rectangle at
`(X + (ox-ax)*s, Y + (oy-ay)*s)` with size `(w*s,h*s)`. Do not recenter each crop or multiply its alpha
again. Identical source frames may reference the same rectangle. There is a transparent pixel of gutter
around each unique rectangle. The five-row v1 layout cannot
read v2; the eventual loader must dispatch on `version`. **This remains an unwired art candidate**;
there is no existing runtime atlas loader to migrate on this branch.

Checks: `test_pack.py` exercises reconstruction/alpha/grade invariants; `validate.py` verifies every
rectangle, offset, source alpha byte, logical anchor, transparent gutter, frame count/timing, motion,
held death, hashes, Q75 floor and 200,000-byte cap. `audit.py` verifies MPFB anatomy, all 53 bones,
barrel palm contact during idle, stationary base, rolling ratios, safe effect sizes and terminal
contact. The decoded review is `field-cannon-g-decoded-atlas.png`. Art judgment remains separate.
