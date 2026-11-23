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

## Vehicles / aircraft — Jet bomber (`jet-bomber`)

Unit-local code lives in `tools/art/anim3d/units/jet-bomber/`. This chapter adds
one aircraft to the vehicles family without changing infantry or tank tooling.
The reference is the existing eight-jet camouflage painting: four paired pods,
a swept wing, a tall single fin, and a curved cream support above one stone disc.
No manufacturer or national insignia is added. The aircraft uses closed lofted
volumes, solid airfoils, tubular intake rims, recessed compressors and finished
bevels. Three plain views make depth inspectable; no silhouette card or image
opacity is used to hide missing geometry. `RIG-airframe` is a rigid mechanical
hierarchy; three released bombs have independent keys.

### Round method and skills

Load all six Sam Blender skills before working: modeling, materials, cameras,
lighting, animation and rendering. They inform finished solid geometry, paint
and roughness, registered orthographic camera, warm upper-left product key with
cool rim/soft fill, layered-action mechanical keys, and low-sample CPU previews.
Every Blender call is plain `blender -b --disable-autoexec` through the PATH
slot gate. Do not pass a thread override, bypass the gate, or start another
heavy job while one runs. Effects use keyed visibility, never zero scale.

Apply the four standing quality levers together:

1. Register full-depth geometry to the painting, finish modifiers, then freeze
   camera UVs on the actual surface. Sample source alpha only as pigment
   confidence, never as geometry opacity. Per-vertex rest-ray visibility and
   normals gate projection; generated olive fill covers unseen surfaces. This
   fill is reused licensed project imagegen artwork, pinned in `inputs.json`.
2. Bevel hard edges, retain real wall thickness and intake interiors. Six actual
   512px AO/Pointiness maps add restrained cavity grime and edge wear on the
   fuselage and wings. Never substitute procedural noise for the painting's
   large-scale camouflage and panel brushwork.
3. Use product lights and contact shadows. Camera-only painted pigment avoids
   double-lighting the source; other rays use physical materials. Standard/None
   is deliberate for this prelit painting, not a photographic lighting preset.
   The shared cream pigment is **#E9CFA0**, sRGB converted to linear roughly
   `(0.815, 0.624, 0.352)`; the rim is darker, with fine stone grain. Review actual
   lit pixels because shader values alone cannot establish the colour match.
4. Measure opaque RGB 10/50/90 percentiles against the source, freeze a bounded
   grade (at most 24 levels/channel), and apply it to every painted stage/frame.
   Keep ungraded raw renders. Histogram matching is not painting parity.

After every round inspect `jet-bomber-f-restpose-compare.png`: painting, render
and 50/50 crossfade at 256 and 64. The target is a rest pose hard to distinguish
from the painting. CPU preview success and atlas size are not art approval.

### Rebuild, preview and complete GPU pass

Run from the repository root:

```sh
tools/art/anim3d/units/jet-bomber/render.sh build
for stage in b c d e-idle e-move e-attack e-hit e-death g; do
  RESOLUTION=256 SAMPLES=8 tools/art/anim3d/units/jet-bomber/render.sh "$stage"
  RESOLUTION=256 "$HOME/LegatumRuns/anim-pilot/venv/bin/python" tools/art/anim3d/units/jet-bomber/deliver.py "$stage"
done
```

The complete no-argument lead entry point is:

```sh
ROUND=2 tools/art/anim3d/units/jet-bomber/gpu.sh
```

It verifies build/source hashes, renders **every** stage using Metal Cycles at
512px (96 denoised samples by default), exports actual 512/256 masters, writes
all interim PNG/WebP reviews, audits geometry/keys, packs and validates the
160px atlas, and encodes `jet-bomber-round${ROUND}.mp4`. The movie reconstructs
trimmed cells and shows five clips at 2x on #E9CFA0 for eight seconds; FFprobe
checks H.264, yuv420p, 1600x348, 240 frames and duration. Missing Metal fails
explicitly. GPU output must be visually reviewed. The script never writes PASS.

Masters stay outside git under `$ANIM_ROOT/masters/jet-bomber/`; source images
under `assets/jet-bomber/`; review evidence/logs under `review/3d-v2/`.
`build.json`, per-stage render receipts and `pack.json` guard against stale
geometry, mixed grades and modified frames. Rebuilding invalidates downstream
outputs. Read the unit feedback file if present before each iteration.

### Flight and motion checks

Clips are idle 8, move 8, attack 10, hit 4 and death 10. Idle and move close on
an unexported endpoint; attack performs a shallow bombing pass; hit rocks and
recovers; death descends, deforms the near wing/nose and holds a wreck for the
last two samples. The base stays fixed. The rigid aircraft is the mechanical
exception to the open-motion standard: there are no people, animals or feet.
`jet-bomber-g-feet-check.png` explicitly records that exception and shows top
and nose views of the entire move cycle for heading and clearance review.

The standard for units that **do** have feet remains proven open motion:
humans use CMU free-use or Quaternius CC0 idle/walk/hit/death, retargeted through
Blender/Rokoko with matched rest poses and bone rolls; only weapon attack is
hand-authored. Animals use a CC0 animated quadruped. Check top and front feet
for a full move cycle every round, aligned to travel without sliding; never
hand-correct foot direction after retargeting. Record source URL, version,
licence and hash locally and in `assets/SOURCES.md`; no Mixamo or paid assets.

### Trimmed atlas version 2

The candidate atlas uses logical **160x160** cells, exact alpha at WebP quality
95/90/85/80/75 (highest fitting), and refuses delivery over **200,000 bytes**.
Every clip remains in idle/move/attack/hit/death row order. Metadata:

```json
{"version":2,"trimmed":true,"frame":{"w":160,"h":160,"ax":82,"ay":132},
 "clips":{"idle":{"row":0,"frames":8,"fps":10,"loop":true,
 "rects":[{"x":2,"y":2,"w":145,"h":110,"ox":8,"oy":24}]}}}
```

The example has one illustrative rectangle; actual JSON contains all 40.
`x/y/w/h` address the crop in the atlas; `ox/oy` restore its original logical
cell. Draw at `(anchorX-ax+ox, anchorY-ay+oy)` and scale every coordinate equally.
`row` specifies ordering, not a fixed-height grid. Identical terminal frames
reuse their rectangle so lossy RGB is identical too. Validation checks exact
alpha reconstruction, transparent gutters, clipping, motion, grade/source
hashes and held death. This lane does not wire the new format into the UI;
keep the existing static painting until art approval and runtime integration.

### Jet bomber driver round 2

Preserve the previous GPU reviews and decoded movie frames before overwriting
interims. The round-one GPU pass completed at 189,538 bytes / Q80; that passed
delivery but still showed narrow fuselage/pod silhouettes and a dark oversized
stone rim. Inspect a binary silhouette difference as well as RGB: frozen source
pigment can make missing volume surprisingly difficult to spot. Refit complete
loft rings and nacelle lengths, retaining their depth, before re-projecting.
Subdivide long airfoil spans with **Simple** subdivision before projection:
otherwise occluded root vertices can fade source pigment over an entire wing.
Use rest-ray visibility for visible thin-airfoil pigment instead of rejecting
it based on smooth grazing vertex normals. Keep unseen surfaces filled.
The stationary disc now uses source pigment on its visible curved rim too;
outward normals must not unnecessarily reject the painting at that silhouette.

Death compresses and bends the solid support continuously, never toggling it
away. Wing and attached outer pod deform in a shared world-space field; applying
the same local displacement to objects with different origins breaks their
attachment. Keep finite support thickness and test its evaluated manifold
volume. Released bombs have real fins and a release-pose transform followed by
accelerating fall. No zero-scale effects or volumes are involved.

`rest-metrics.json` records alpha silhouette intersection-over-union and opaque
RGB error at 256/64. These are diagnostic measurements, not approval gates.
CPU interims are labelled as CPU; `ROUND=2-cpu .../deliver.py pack` keeps their
movie separate from the lead's `jet-bomber-round2.mp4`. The GPU script reports
the active stage, repeats source preflight after delivery, and never writes PASS.
