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

## Siege — field cannon

The field-cannon candidate uses the painting's **one visible gunner**, navy coat, red cuffs and collar,
ivory breeches and cross-belts, black gaiters and shako, and upright sponge rammer. The person is a
fresh MPFB 2.0.18 human with native topology and the 53-bone `game_engine` rig. The gun is entirely
editable hard-surface geometry: hollow lathed bronze barrel, mouldings, cascabel and trunnions;
olive-painted oak cheeks and trail; cross-beds, axle, twelve open spokes per wheel, flat iron tyres,
hub bands, cheek straps, cap bolts, tow eyes and elevation wedge. It is not an image extrusion.

All siege scripts are in `tools/art/anim3d/siege/`. They source the shared `env.sh`, use its installed
MPFB and CC0 material packs, and write only to `masters/field-cannon/` and the shared review folder
under `ANIM_ROOT`. `assets/field-cannon/painting-source.png` is the external painting reference;
`assets/SOURCES.md` records its licence and the reused packs. No masters or downloads enter git.
The shared renderer dispatches to this family when `ANIM_FAMILY=siege`; its default stays spearman.
Every siege Blender invocation goes through `bin/blender-slot`, with no private lock or direct
Blender call. The live machine-wide gate currently allows **one Blender process**, three threads;
keep following that wrapper if the lead changes its implementation. Always use background mode.

### Building and CPU review

From the repository root:

```sh
export ANIM_FAMILY=siege
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/siege/prepare.py
tools/art/anim3d/render.sh build
RENDER_ENGINE=CYCLES SAMPLES=8 tools/art/anim3d/render.sh b
tools/art/anim3d/render.sh materials
tools/art/anim3d/render.sh bake
tools/art/anim3d/render.sh paint
tools/art/anim3d/render.sh finish
RENDER_ENGINE=CYCLES SAMPLES=16 tools/art/anim3d/render.sh c
RENDER_ENGINE=CYCLES SAMPLES=16 RESOLUTION=512 tools/art/anim3d/render.sh detail
tools/art/anim3d/render.sh animate
RENDER_ENGINE=CYCLES SAMPLES=12 tools/art/anim3d/render.sh d
for clip in idle move attack hit death; do
  RENDER_ENGINE=CYCLES SAMPLES=12 tools/art/anim3d/render.sh "e-$clip"
done
tools/art/anim3d/render.sh pack
tools/art/anim3d/render.sh validate
tools/art/anim3d/render.sh audit
```

Build invalidates materials, bakes and all clips. Material changes require re-running `animate` to
copy them into clip masters. The plain master is separate from the textured one. Review sheets
are named `field-cannon-b-plain.png`, `field-cannon-c-textured-lit.png`, `field-cannon-c-details.png`,
`field-cannon-d-rig-poses.png`, and `field-cannon-e-<clip>-strip.png`, alongside animated WebPs.
They show native 256 and 64 px beside the painting. Review sheets and `field-cannon-log.md` are
written immediately; check `field-cannon-FEEDBACK.md` before another render round.

The materials reuse ambientCG Metal034, Fabric030 and Travertine001 and Poly Haven wood/leather,
with pigment grading, restrained grain, skin texture, visible sculpted cloth folds, physical edge
trim and scratches. Real 256 px AO and curvature maps are baked for barrel, carriage cheek and
coat; AO darkens cavities and barrel curvature drives brighter wear. Bakes and textures are packed
into the master. The existing painting remains the quality reference: successful technical checks
are not art approval, and this candidate is not wired into the game.

### Siege motion and grounding

Idle shifts shoulders and head while the free hand tends the breech. Move is an in-place push cycle:
the runtime supplies map translation. Virtual ground travel advances by one of twelve spoke pitches
per loop; local body/gun sway is added to travel, and wheel angle is exactly `distance / 0.48` metres.
The repeated spoke pattern makes the rotating wheel's seam cyclic. Recoil uses the same relation,
so wheels roll backward with the carriage rather than spinning independently. The rammer is stowed
alongside the trail while moving. Combat is authored on the same MPFB skeleton, not screen warping.

Attack combines anticipation, rearward carriage recoil, recovery, a brief solid 3D muzzle flash and
seven small smoke lobes confined to the frame. Effects use keyed `hide_render`, never zero or nearly
zero scale: the lead observed Cycles/OpenVDB crashes from collapsed smoke geometry. Hit flinches the
crew and jolts the gun. Death tips the gun, cants a damaged wheel and lowers the crew; evaluated
geometry is settled on the cream disc, and the final two samples hold exactly. The base never moves.
No particle simulation or external motion download is required for these short authored clips.

### Host GPU render and delivery

The saved clip masters are ready for the lead's host Metal/Cycles pass (denoising enabled):

```sh
export ANIM_FAMILY=siege RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64
tools/art/anim3d/render.sh c
RESOLUTION=512 tools/art/anim3d/render.sh detail
tools/art/anim3d/render.sh d
for clip in idle move attack hit death; do tools/art/anim3d/render.sh "e-$clip"; done
tools/art/anim3d/render.sh pack
tools/art/anim3d/render.sh validate
tools/art/anim3d/render.sh audit
```

The packer preserves 8/8/10/4/10 frames in the existing five-row 2560 × 1280 layout, with transparent
256 px cells and anchor `(127,221)`. It quantizes only alpha to 32 levels and tries WebP quality
85–40 without exceeding 200,000 bytes. It writes `app/src/assets/units/anim/field-cannon.webp` and
`.json`; source frame hashes and engine provenance go to `field-cannon-pack.json` outside git.
Validation checks frame counts, alpha, transparent padding, margins, motion, held death and size.
The geometry audit checks MPFB topology, stationary base, nondegenerate effects, rolling ratios and
terminal contact. Judge the GPU result afresh: different render engines can alter surfaces and shadows.

### Painting projection and the craft bar

The coordinator's next-round method is source-painting projection, geometry finish, product lighting,
and a restrained measured grade. `paint.py` projects the original painting onto the actual mesh UVs
at the rest camera, with per-region calibration for face, coat, sleeves, breeches, shako and barrel.
A baked facing mask and source alpha blend it into the underlying material. It never replaces
geometry with an image plane. Source rectangles and blend weights are saved in `projection.json`.
The source's highlights remain partly baked into these textures; inspect motion-revealed surfaces
and double lighting rather than assuming this is fully intrinsic albedo. The generated original
`assets/field-cannon/painted-navy-wool.png` fills unseen cloth and blends under the projection;
other unseen surfaces use the licensed CC0 scans. The mask follows the deforming geometry.

Clothing has thick ribbons, real brass buttons, red fitted cuffs, sculpted sleeve folds and solid
coat tails. The face has a moustache and eyebrows placed against evaluated facial coordinates.
Stone is deliberately warm cream: the review target is approximately sRGB `#E9CFA0` on the lit top,
with a darker warm rim. Under this scene's AgX lighting, the shader uses linear `(0.95,0.70,0.32)`;
do not copy an sRGB triplet blindly into a linear shader or grade by material input alone.

`grade.py` samples source and render opaque-pixel statistics, caps channel gains to 0.90–1.12 and
contrast to 1.14, and adds 7% saturation. Alpha is untouched; ungraded frames remain in each render
folder. `c` also writes `field-cannon-f-restpose-compare.png`, with painting, render and 50/50
crossfade at 256 and 64 px. The target is near-indistinguishability at rest, not merely a passing
atlas validator. Current silhouette and texture-registration differences remain review work.

For Eevee host comparisons use `RENDER_ENGINE=BLENDER_EEVEE` instead. For sandbox previews keep
`CYCLES_DEVICE=CPU`; the GPU path explicitly requires a Metal Cycles device and never silently
falls back. All invocations still go through the live machine-wide Blender gate.

To avoid reacquiring a busy gate between every short stage, the same complete CPU round can run in
one Blender process after `prepare.py`:

```sh
source tools/art/anim3d/env.sh
RENDER_ENGINE=CYCLES CYCLES_DEVICE=CPU "$ANIM_ROOT/bin/blender-slot" \
  -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/siege/round.py
```

`round.py` posts each stage as soon as it renders, then audits the saved clips. Run pack and validate
separately afterward. The ordinary stage commands remain available for targeted iteration.

The richly textured 40-frame CPU atlas exceeded 200 KB at quality 60 in testing. The siege packer
therefore searches down to quality 40, keeping all dimensions and frames, and records the size at
every tried quality. It refuses anything larger than the cap. Review the decoded atlas as well as
the uncompressed strips; the GPU pass must be repacked and may select a different quality.

The final two death samples are one held geometry pose. The renderer asserts all object and bone
matrices agree within `1e-6`, then reuses the first terminal PNG for the second output sample; this
avoids insignificant CPU-render rounding differences breaking the exact-pixel hold contract.
The audit checks the same matrices, plus gunner, gun and dropped-rammer ground contact.

The six installed Blender skills were loaded during the final review. `finish.py` applies fully
metallic bronze/iron with roughness controlling wear, cloth sheen, and a cooler weaker rim/fill.
It runs after painting and before animation. Entry points disable automatic script execution,
and the renderer asserts its saved camera exists. Existing descriptive object names and the
orthographic token camera are kept as project conventions. The optional `reference-look-calibration`
skill is absent; image bounds, sampled colour statistics and visual crossfades supply that comparison.
