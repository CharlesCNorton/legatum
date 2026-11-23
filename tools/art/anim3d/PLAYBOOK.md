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

## Vehicles / aircraft — jet fighter (`jet-fighter`)

This unit's implementation lives entirely in `tools/art/anim3d/units/jet-fighter/`, an isolated snapshot of the newer jet-bomber delivery tools plus original jet fighter geometry and flight curves. It follows the vehicles family method: full-depth hard surfaces, no MPFB or character mocap for machines. The source painting shows a silver single-engine jet flying above a curved stone support; retain that composition, nose intake, swept silhouette and lack of national markings. The plain stage has three views to expose the real volume.

All six Blender skills are applied: closed loft and beveled edge construction; metal roughness and actual AO/Pointiness bakes; warm upper-left key, soft fill and cool rim; rest-camera registration; quaternion bank/flight curves; denoised CPU previews and native GPU masters. Every Blender call is plain `blender -b --disable-autoexec` through the PATH gate, serial within this lane. Never use the application binary directly, scale effects to zero, or infer GPU success from a CPU preview.

### Painting parity standard

Use all four quality levers: (1) frozen camera UV projection of the full original painting onto finished three-dimensional surfaces, with visibility/facing confidence and generated same-style fills on unseen surfaces; (2) real geometry finish including closed airfoils, recessed intake, smooth canopy, relief seams and bevels; (3) miniature product lighting with contact shadows; (4) an automatically sampled, bounded RGB quantile grade frozen from the rest render and applied consistently to all clips. Painted pigment is camera-only so inherited lighting does not illuminate adjacent objects twice. Standard/None is intentional for projected display-referred art, not a photographic preset. Actual AO and Pointiness bakes drive cavity and edge response on fuselage and both main wings.

The common base pigment is warm cream **#E9CFA0**, approximately linear RGB `(0.815,0.624,0.352)`, roughness `.86`, with fine grain and darker rim. The source projection preserves the specific painting's stone brushwork. Always inspect the resulting pixels after lighting/grade. A grey-white disc fails. Save painting / 3D / 50-50 crossfade at native 256 and 64 as `jet-fighter-f-restpose-compare.png`; render completion is not art approval.

### Motion, review and host handoff

Five clips are idle 8, move 8, attack 10, hit 4, death 10; idle/move loop. The fighter banks about its longitudinal axis, advances in the move cycle, dips into a cannon run, reacts to a hit, then crashes onto the stationary base while its support tips. Effects use keyed visibility and real thickness. Two terminal death samples are held. Motion and crash contact must still be visually reviewed; a bounded turn table is not flight realism.

For human units the standard is open CMU or CC0 Quaternius idle/walk/hit/death, retargeted with rest-pose and bone-roll alignment; only weapon attacks are authored. For animals use an openly licensed animated quadruped. Never patch foot direction after retargeting. Render top and front feet through a move cycle every round. The jet has no feet: `jet-fighter-g-feet-check.png` instead shows actual top/front airframe poses over all eight move samples, explicitly labelled as an aircraft exception. No external motion licence is claimed.

Run `ROUND=1 tools/art/anim3d/units/jet-fighter/gpu.sh` from repo root for the whole lead pass. It checks input/build hashes and Metal, then serially renders b/c/d, all five clips and the top/front review using Cycles GPU. It retains actual 512px masters plus 256 derivatives, all interim sheets, animated WebPs, rest-pose crossfade, geometry/clip audit, validated atlas and `jet-fighter-round${ROUND}.mp4`. Video uses the decoded trimmed atlas at 2x on cream, all five clips side by side for eight seconds, H.264/yuv420p; FFprobe verifies it. The lead must inspect the GPU output before writing PASS.

### Jet fighter driver round 2

Archive the incoming GPU evidence before CPU previews replace the gallery. The first GPU pass succeeded technically (185,264 bytes at quality 80); its intake cup, bright canopy trim, blank far-wing panel and rubbery wing damage still failed visual parity. Round 2 rebuilds the closed intake shell from separate rear/front/inner ellipse stations, deepens its termination, raises the canopy crown, thins trim and reduces rim lighting. A signed-volume audit caught inward normals on the mirrored far wing that the old absolute-volume test missed. Correct outward winding before calculating projection visibility; increasing texture strength cannot fix a rejected facing mask. The opposite wing now has its own span/chord UVs: existing generated brushwork blends with this aircraft's painted wing panel pattern on the real hidden surface. Its shorter physical span keeps the bank silhouette proportionate. Camera pigment remains frozen on geometry; no per-frame reprojection or alpha-cut silhouette.

The crash uses a defined crease and rotating outer wing panels instead of a smooth curl. Inspect the crease, wing/base clearance and support collapse in the final GPU strip; a manifold mesh and a held final frame do not prove clean contact. The thickened, lengthened solid muzzle streaks must also read at 64 px without looking like free-floating lines. No cloth, straps, human or animal motion is present in this machine.

`ROUND=2 tools/art/anim3d/units/jet-fighter/gpu.sh` is still the complete no-argument host handoff. Status now records each running stage and defaults to round 2. Native CPU 256 previews are labelled as such; old native 512 GPU masters are retained as history but rejected for packing by the changed master hash. Keep PASS absent until the new GPU output meets both visual and delivery criteria.

### Trimmed atlas extension used by aircraft

The old fixed 256px atlas description above is superseded for this unit. Schema version 2 stores `trimmed:true`, `frame:{w:160,h:160,ax,ay}` and clips in idle/move/attack/hit/death row order. Each clip retains `row,frames,fps,loop` and has `rects:[{x,y,w,h,ox,oy}, ...]`. Rectangle coordinates address the atlas; offsets restore the crop to its logical 160px frame. Draw at `(anchorX-ax+ox, anchorY-ay+oy)` with one uniform scale. Row is ordering metadata, not a fixed cell-height multiplier. Held identical frames may share a rectangle.

Try quality 95/90/85/80/75 and fail if none meets 200,000 bytes; never drop frames or quality below 75. Alpha must reconstruct exactly, crops must not overlap, padding must stay transparent, all 40 samples must retain their anchors and the last two death frames must decode identically. Receipts bind the current scene, animation script, grade and frame hashes. The atlas is an art candidate with no runtime integration in this lane.
