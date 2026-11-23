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

## Mounted: cataphract round 1

Unit scripts are isolated in `tools/art/anim3d/units/cataphract/`. This chapter
extends the mounted family; it does not replace the infantry instructions above.
The mounted branch's CC0 Quaternius horse and MPFB anatomical rider are reused,
with unit-specific steel scale barding, articulated neck panels, fitted rider
armor, rust-red thick folded cloak, straps, stirrups and an iron-tipped lance.
The source action supplies horse motion; the rider remains parented to the saddle.
The move clip is a source walk, with authored rider breathing, attack and recoil.
Death uses the horse collapse, rider slump and a released lance, then holds its
last two output samples. These are presentation keys, not cloth/rigid-body physics.

The four standing quality levers are the standard here: (1) original painting
registered to the token and projected through the calibrated rest camera onto
actual volumetric, weighted meshes; (2) thick, bevelled kit, smooth anatomy and
folded cloth; (3) warm upper-left key, cool rim, soft fill, contact shadows and AO;
(4) one automatically sampled 17-quantile RGB grade, shared by every animation
frame to avoid pumping. Generated mounted-family surface fills cover unseen
sides and blend through a frozen normal-incidence mask. Projection changes colour,
never mesh alpha or geometry into a billboard. Rest-camera geometric registration
preserves depth but is approximate; inspect joint deformation in motion.
The helmet has actual 256px Cycles AO/Pointiness bakes feeding cavity darkening and
edge roughness. Other surfaces use geometry, procedural grain and shader AO;
they do not claim full-body baked AO coverage.

Use a single low stone disc, warm cream **sRGB #E9CFA0**, with a darker shaded rim
and fine grain. The material starts with the linear equivalent of that pigment;
judge its displayed colour under the light and shared grade, not its shader value.
The rest review contains painting/render, a half split and a 50% crossfade at
256 and 64px in `cataphract-f-restpose-compare.png`. This round remains a candidate
until the rest silhouette, surfaces and all five clips meet the painting.

All assets and masters are outside git under `~/LegatumRuns/anim-pilot/`.
`assets/cataphract/` contains the original and registered painting and copied fills;
`assets.lock.json` pins inputs. `assets/SOURCES.md` records licences and URLs.
`masters/cataphract/` holds `unpainted.blend`, `plain.blend`, `cataphract.blend`,
five independent `clips/*.blend`, textures, raw render sequences, grade and masters.
Rebuild sequentially from the repository root:

```sh
tools/art/anim3d/units/cataphract/render.sh prepare
tools/art/anim3d/units/cataphract/render.sh build
tools/art/anim3d/units/cataphract/render.sh finish
tools/art/anim3d/units/cataphract/render.sh bake
tools/art/anim3d/units/cataphract/render.sh animate
RESOLUTION=256 SAMPLES=8 tools/art/anim3d/units/cataphract/render.sh all
tools/art/anim3d/units/cataphract/render.sh audit
tools/art/anim3d/units/cataphract/render.sh pack
```

Every Blender invocation is plain `blender -b --disable-autoexec` through the
PATH gate; no direct executable and no nested heavy process. CPU previews use
Cycles. GPU rerender needs only the executable no-argument script:

```sh
ROUND=2 tools/art/anim3d/units/cataphract/gpu.sh
```

It checks Metal availability, regenerates the five clips, checks the rig, and renders every b/c/d/e stage serially with Cycles Metal GPU at
512px/64 samples, derives true 512/256 masters, makes all review PNGs and animated
WebPs, packs and validates the atlas and writes `cataphract-round${ROUND}.mp4`.
The video restores each trimmed frame to its 160px logical canvas, displays all
five clips side by side at 2x on cream for eight seconds, H.264/yuv420p.
No CPU fallback is permitted for that script. Review GPU results again; successful
packing does not grant art approval. The script does not write a PASS marker.

### Cataphract trimmed atlas extension

Delivery is `app/src/assets/units/anim/cataphract.{webp,json}`. JSON version 2 uses
`layout: "trimmed-rows"`; `frame: {w:160,h:160,ax,ay}` is the **logical**
canvas and common anchor, measured from the stationary base top centre. `clips` keeps `row`, `frames`, `fps`, `loop` in the order
idle/move/attack/hit/death, lengths **8/8/10/4/10**. Each clip adds ordered `rects`:
`{x,y,w,h,ox,oy}`. Crop `(x,y,w,h)` from the atlas and paste at `(ox,oy)` on a
transparent 160px canvas; position that canvas relative to `(ax,ay)`. Atlas row
heights and widths are variable, with two-pixel gutters; do not multiply row/index
by 160 to find pixels. Runtime loading is unchanged by this art-only candidate.

The packer preserves all frames, downsamples with bicubic filtering and lossless
8-bit alpha, shares identical rectangles within each row, and tries WebP
quality 90/85/80/75, refusing anything over **200,000 bytes**. Decoded bounds,
transparency, reconstructed motion and held death are validated. Master and clip
hashes reject stale renders. Raw render PNGs remain untouched; only the derived
masters/reviews/atlas receive the shared rest LUT. CPU previews are never enlarged
and labelled as 512px masters: the GPU handoff produces those originals.

### Cataphract round 2: finished surfaces and rider coverage

`finish.py` starts from the preserved clean `unpainted.blend` on every run.
`refine.py` freezes the MPFB macro mix, applies the actual solidify/bevel/subdivision
surfaces with armature deformation disabled, then fits the completed weighted
anatomy through inverse skin transforms. The 53-bone rig, weights and full mesh
depth remain. This fixes projection sampled on a cage that was displaced later by
render modifiers. A local camera-plane fitting field broadens the near shoulder,
lowers the neck crest and moves the rein hand toward the painting; it preserves
depth but is still an approximate registration, not an exact camera match.
The rein palm turns down. Source walk/idle/hit/death and authored rider motion
remain; attack/hit now begin with the guard lance angle instead of snapping upright.

Projection now records finished-surface UVs, normal incidence and ray visibility.
A separate source-pigment mask rejects cream base pixels on the horse's lower legs;
otherwise registration error paints the stationary stone onto moving hooves.
This changes pigment coverage only, never mesh opacity. The original generated
coat/linen/metal/hair fills remain on unseen areas, along with real mane/tail curves,
thick straps, folded cloak and scale relief. Original projected painted illumination
is a camera-only 96% pigment branch; non-camera rays keep physical materials, baked
helmet AO/Pointiness, shadows and product lighting. Standard/None avoids compressing
already painted illumination again. This is deliberate source-color preservation,
not a general photographic preset. The round cream stone uses its own physical and
camera-only pigment, with no figure or hoof projection, and a single automatic
rest-histogram grade still applies to all clips.

`gpu.sh` defaults to round 2 and is the only required host command. It retains
`gpu-logs-cataphract-r${ROUND}.log`, reports the failed stage in
`review/3d-v2/cataphract-gpu-status.txt`, and writes a round-specific JSON receipt
only after independent verification. A missing Metal device fails before animation.
All b/c/d/e stage manifests must be current Cycles GPU512/64; actual 512/256 stage
and clip masters, lossless reconstructed alpha, unchanged frame counts, margins,
gutters, motion, exact decoded death hold and the H.264/yuv420p eight-second
1600x348 / 240-frame movie are checked by `verify.py --gpu`. A successful receipt
still sets `art_pass:false`; only visual acceptance can create a PASS marker.
For CPU delivery verification run `ROUND=2 "$ANIM_ROOT/venv/bin/python"
 tools/art/anim3d/units/cataphract/verify.py` after rendering/packing. CPU previews
cannot pass the GPU provenance gate. This remains an unwired art candidate.

Round-two CPU evidence: all forty samples at Cycles CPU256/8, **188,488 bytes at Q85**, 1156x736 atlas, lossless alpha and exact decoded death hold. Geometry/finished-surface audit, independent delivery/video checks, syntax, missing-input logging and CPU-master GPU rejection pass. The movie is H.264/yuv420p,1600x348,240frames/eight seconds. Evidence remains in `masters/cataphract/round2-cpu`. At256 the far arm, reins, horse contours and underside finish still differ from the painting; at64 identity reads but silhouette is not equivalent. **No PASS marker; host GPU512/64 and visual acceptance remain outstanding.**

### Cataphract driver round 2 follow-up

The supplied r1 GPU transcript failed trying to open an absent lane-4 animation
script. The supplied c/f/e images were CPU evidence. The no-argument `gpu.sh` now
anchors to its own checkout, passes absolute script paths, records that checkout
and branch, checks every helper before launching Blender, and validates the
licensed input hashes before accepting Metal. Use it from this unit's current
checkout; a switched branch with missing scripts fails explicitly.

`legs.py` fits continuous lower-leg sections while preserving complete mesh depth
and native skin weights. Local per-hoof warps had pinched the fetlocks. Foot
diagnostics then revealed that visual fitting had changed support heights:
`contacts.py` calibrates the rest soles and applies smooth vertical corrective
shapes over the native source lift. Horizontal motion and foot rotations remain
from the Quaternius rig. This is a support adaptation, not a claim that projected
mesh fitting preserves physical motion automatically. The independent audit
checks evaluated soles against the support plane; it does not certify no sliding.

`reins.py` replaces the old torso-parented reins with closed leather tubes. Each
end follows actual evaluated bridle/hand vertices, with slack between them. The
absolute shape keys contain the real animated geometry; there are no handlers or
asset scripts requiring auto-execution. The audit checks both endpoint gaps for
every pose, alongside the existing stationary base/camera and loop checks.

Open motion is the default: native CC0 Quaternius horse actions, plus CC0 Universal
Animation Library Sitting_Idle_Loop, Hit_Chest and Death01 for rider torso/head
(and arms during death),
reference-pose and bone-roll compensated in `rider_motion.py`. The saddle constrains
pelvis and legs; the lance attack remains authored. Source/licence hashes are
checked before importing, with full attribution in unit `SOURCES.md`. Generated
Medjay skin and Tagmatic Soldier steel, crimson wool and leather supplement the
mounted-family fills on unseen surfaces. Prompts/hashes remain in this unit.
Source-color camera projection, real bevels/folds/straps, product lighting and one
shared rest-histogram grade still form the finish; the cream stone pigment now
includes actual AO contact shading and fine grain.

Every mounted round must inspect the whole move cycle in actual top and front
views. `render.sh feet` produces an explicitly cut-away lower-leg diagnostic,
`cataphract-g-feet-check.png`, and a manifest of evaluated sole samples. CPU
defaults are 192px/4 samples; GPU handoff uses 512px/64 and verifies all sixteen
images against the current move clip. Both views use the original foot axes;
never fix foot direction after retargeting. Review contact, travel direction and
sliding in addition to the five beauty strips/video. GPU verification includes
the foot sheet and refuses CPU evidence. The GPU command remains:

```sh
ROUND=2 tools/art/anim3d/units/cataphract/gpu.sh
```

The script produces all b/c/d/e masters and reviews, the top/front foot review,
trimmed 160px atlas, validation receipt and eight-second five-clip H.264 video.
Only visual acceptance after that GPU pass can create `cataphract-PASS`.

The lance thrust slides the rigid shaft through the grip so the point reaches
beyond the muzzle. Released death fingers open, and a nearest-surface contact
adaptation settles the source-driven arms onto the horse instead of leaving a
raised empty fist. These are mounted equipment/contact adaptations, not a full
cloth or collision simulation.

Current driver-round CPU evidence: **193,924 bytes at Q85**, all forty trimmed
160px frames, exact decoded terminal death hold and lossless alpha; all b/c/d/e
renders at CPU256/8 and sixteen actual foot views at CPU192/4. The independent
geometry audit checks all forty poses (lowest sole 0.108m above a 0.100m base top;
rein endpoint gap below 0.000001m). Atlas/source hashes, gutters, offsets, motion,
H.264/yuv420p1600x348/240frames/eight seconds, syntax and input hashes pass.
Wrong-cwd/missing-master preflight and rejection of CPU evidence by GPU verification
were exercised. Review/checkpoint: `masters/cataphract/driver-round2-cpu/`.
At256 the arm/neck proportions, saddle/boots, base perspective and death undersides
still miss the painting; at64 the identity reads but the silhouette is different.
No complete sliding/intersection certification and no GPU512/64 result yet.
**No PASS marker.**
