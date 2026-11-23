# Animated miniature pilot

**Status: pass 3 captured; cached p95 failed and needs a host recapture after these fixes.**
See [the pass-2 critique](review/pass-2.md), [the pass-1 critique](review/pass-1.md) and [setup history](review/pass-0-setup.md). Do not wire this into the game until
rendering, visual review and the size/performance gates actually pass.

Rebuild one unit end to end, with Blender and Pillow installed:

```sh
tools/art/anim/build.sh spearman
```

The same command accepts `horseman`, `field-cannon` and `spartan-hoplite`. It prepares
projection textures, creates an articulated Blender relief model, bakes 40 poses,
renders transparent 256 px frames in Eevee, packs the atlas/metadata and writes a
source comparison sheet plus five animated previews. `BLENDER` can select the executable.
Pillow lives in `~/LegatumRuns/anim-pilot/venv`, installed there on first use.

Serve the repository root with `python3 -m http.server`, then open
`http://localhost:8000/tools/art/anim/gallery/`. The gallery is plain HTML, JavaScript
and Canvas 2D; it has no build step, CDN, browser 3D or app runtime dependency.

The lead runs a complete render and browser capture pass **outside the Codex sandbox**:

```sh
tools/art/anim/pass.sh 3
```

`require('playwright')` and a downloaded Chromium must be available to Node via
`NODE_PATH`; this worktree has no `app/node_modules` symlink. If the
host does not provide them, install them outside the repository:

```sh
npm install --prefix "$HOME/LegatumRuns/anim-pilot/browser" playwright
export NODE_PATH="$HOME/LegatumRuns/anim-pilot/browser/node_modules"
export PLAYWRIGHT_BROWSERS_PATH="$HOME/LegatumRuns/anim-pilot/browser/cache"
"$NODE_PATH/.bin/playwright" install chromium
```

The capture tool starts a temporary loopback static server, launches headless
Chromium with deviceScaleFactor 1, captures every clip at both sizes, exercises
mirror/backdrop/terrain/frame controls, and measures 180 draw calls for both 300
and 600 tokens after 15 warmup draws. The 300-token mean must be below 4 ms. Timing
covers terrain blit and token draw commands, not rAF intervals or GPU completion.
This is a focused gallery benchmark, not a claim about the complete game renderer.

Codex does not render, capture, or try cloud/sandbox workarounds. It reviews the
lead’s outputs, fixes scripts/rigs/gallery, runs CPU-only checks, writes pass notes,
commits and stops. After each pass, open **all** available captures and the per-unit sheets. Write the critique,
changes and measured results to `~/LegatumRuns/anim-pilot/review/pass-N.md`, copy the
note and a few small PNGs into `tools/art/anim/review/`, then commit. Three successful
render/review passes are the minimum; blocked setup is not a completed pass.
The runner handles pushing this branch under the final task instruction.

## Outputs and format

- Git: `app/src/assets/units/anim/<slug>.webp` and `.json`.
- Outside git: `~/LegatumRuns/anim-pilot/masters/<slug>/` holds packed-texture `.blend`,
  projection layers and `foreground/<clip>/NN.png` (figure-only, without stone).
  The packer composites each over `base.png`; old `frames/` are pass-2 evidence,
  not valid packer input. `packed-foreground.png` and `packed-evidence.json`
  bind the selected foreground alpha, base and atlas by SHA-256 for validation.
- Outside git: `~/LegatumRuns/anim-pilot/review/<slug>.png` shows the source at left
  and every frame on grey and parchment; `<slug>-<clip>.webp` is an animated preview.
- Outside git: `review/pass-N/` holds browser screenshots and `metrics.json`.

Atlases remain 2560 × 1280, with 256 px cells and rows idle/move/attack/hit/death.
JSON stays `{frame:{w,h,ax,ay}, clips:{name:{row,frames,fps,loop}}}`. Render 40
poses (8/8/10/4/10); pack the first profile that fits at quality 60 or above:
40, 34 (4/8/10/4/8), 27 (4/8/6/3/6), then 23 (4/4/6/3/6) frames. Prefer eight move
frames; four is a last-resort budget fallback to review for cadence. Timing is
adjusted to preserve the loop period or first-to-last duration. Reduced attack
keeps anticipation, the first strike, peak and recovery; death keeps two settled
frames. Padding remains transparent, and the gallery/capture use the metadata.

WebP uses method 6 and qualities 80/70/60, with a strict 200,000-byte ceiling.
Alpha is quantized to 32 coverage levels (at most 4/255 error), and invisible RGB
is cleared. The packer probes size in memory and never replaces delivery with an
oversized candidate. `review/<slug>-pack.json` records quality, bytes and source
frame selection. `pass.sh` archives sheets, previews and packing reports into
`review/pass-N/` as each unit completes, even if a later unit fails. It also preserves base and
foreground validation evidence under `pass-N/masters/<slug>/`.

`validate.py` checks dimensions, metadata/timing, alpha, clipping, padding, held
death, bytes, the exposed stationary stone rim and neutral source framing. It
requires the prepared master base and matching packed foreground evidence. The
reference rim comes from the lower third of the opaque prepared base, independent
of figure colours. It excludes pixels occupied by rendered foreground alpha
(plus a one-pixel edge), requires at least 40 pixels / 25% to remain exposed,
and retains the position/pigment and opacity checks. The spearman's pass-2 death
failure was a leg obscuring the rim, not base movement. The new pipeline cannot
validate old pass-2 atlases without their missing foreground evidence; rerender
all four units with `pass.sh 3`, do not forge masks from colour differences.

`--contract-only` explicitly skips the art invariants; never use it as the pass
gate. No validation substitutes for visual review of the new renders.

## Modelling and limitations

The shipped 256 painting is the texture and proportion reference. The higher
resolution panel is inspected for identity, not substituted for the map painting.
Hand-traced regions in `units.py` define anatomical/kit pivots and segmentation.
`prepare.py` separates them, reconstructs a continuous cream stone top,
and preserves the unobstructed painted front rim.
`render.py` builds subdivided shallow relief meshes, UV-projects the painting,
skins each part to a Blender armature, and animates the named regions.

This is **single-facing articulated relief**, not a volumetric character model.
It preserves the painting's three-quarter camera and baked soft upper-left light;
emission materials avoid relighting those highlights. The base has no animated
transform. The camera preserves the 1:1 painting projection; its far plane includes
the stone behind the figure. Inspection sheets compare source/render at equal size. It has baked contact shading only and no outside ground plane.
Pass 2 exposed wheel holes, orphaned crew/kit paint, stone pixels on feet,
and a horse/rider card flip. Pass 3 narrows foot masks, reassigns stray pixels
to anatomical parts, confines paint extension to small joint patches, keeps
incomplete cannon wheels rigid, and separates the horse collapse from its rider.
These changes still need host-render review. Do not describe the current result as excellent or production-ready.
A full 3D turn would require new geometry and hidden-surface painting.

The build uses `nice -n 10`, headless factory startup, Eevee, four Blender threads,
and a shared atomic lock so only one Blender process runs at a time. It never
uploads masters. A failed render never runs the packer. For rig inspection when a
GPU is unavailable, `tools/art/anim/build.sh spearman 1 --model-only` saves the model
and poses, explicitly without rendering or packing.

No source art, Blender files, renders or browser dependency installs belong in git.
No rules or app runtime code are changed. Art approval still needs the project's
Claude art reviewer before merge; no review has been claimed here.

For CPU-only checks of an already saved model, use
`tools/art/anim/build.sh spearman 1 --audit-only`. This mode shares the build lock,
checks camera depth, attached kit pivots, render configuration and projected opaque samples at all 40 poses, and
writes `masters/spearman/rig-audit.json`. It does not certify the rendered alpha or
quality. `venv/bin/python tools/art/anim/test_pipeline.py` exercises the packer with
temporary synthetic images; none of those images becomes a delivered atlas.

## Pass-3 draw cache and profiling

Pass 2 measured **300 tokens: 5.6739 ms average / 7.3 ms p95** and **600 tokens:
15.585 ms average / 19.3 ms p95**. The bar is still 300 tokens below 4 ms average.
There are no shadows or filters in the hot path; terrain already had a cached
background. The original expensive path scaled 256 px cells from each large atlas
and saved/restored/transformed the context for every token.

`gallery/sprites.js` prepares each populated cell at 64 px (army) and 80 px (map)
once, and prepares horizontally mirrored atlases once. It then converts each
canvas to an `ImageBitmap` and draws and reads every populated frame in both
facings before timing. `metrics.json` reports this cache build, decode and warmup
as `firstUseMs`, separate from draw timings. Drawing is one `drawImage`
with equal source/destination dimensions and integer destination coordinates;
mirror anchors use `size - ax`, and mirrored source columns reverse too. It reuses
the original native atlas for 256 px inspection. No image scaling, save/restore,
context transform, shadow or filter happens per token. Unchanged inspection
frames are skipped. Ground is rebuilt only when the selected terrain changes.

The lead's capture benchmarks both original and cached drawing against the
same newly rendered atlases, with 15 warmups / 180 samples per count and separate
terrain/sprite timing. `metrics.json` keeps `stress` for the cached gate and adds
`originalStress` for the A/B comparison. The 300-token cached gate is under 4 ms
for both average and p95. Other gallery draws pause during each benchmark.
Pass 3 measured 1.10 ms average / 14.7 ms p95 before explicit decode and warmup;
the new p95 needs a host capture. Both paths measure CPU Canvas command submission, not
GPU completion. The 1000 px gallery capture now scrolls to the page top first.

For the game, share this cache by asset and physical-pixel zoom tier: load/decode
the atlas, scale cells and mirror on offscreen canvases, convert cached canvases
to `ImageBitmap`, then draw/read each frame once before starting the animation
loop. Keep the bitmap and drawing context across frames; rebuild for zoom/DPR
changes, and evict unused tiers.
The 64/80 tiers for all four atlases, both facings, cost about 16 MiB of RGBA
storage (before browser overhead); native inspection adds about 100 MiB for
original and mirrored 256 px atlases and should not be retained in the map cache.
Keep terrain/chunk caches separate. No game runtime integration is included here.

CPU-only checks (no `node_modules`, rendering or Chromium):

```sh
"$HOME/LegatumRuns/anim-pilot/venv/bin/python" tools/art/anim/test_pipeline.py
node tools/art/anim/test_sprites.cjs
# Serial, for every slug:
tools/art/anim/build.sh spearman 3 --model-only
tools/art/anim/build.sh spearman 3 --audit-only
```

## Critique checklist for every unit and clip

Inspect the native 256 px capture and every preview frame on grey and parchment,
then the map capture: shoulder/elbow/hip/horse-knee seams; wheel gaps; smeared or
stretched pigment; missing paint behind moving arms/shields/rider; solid weight
shift versus flat sliding pieces; an identical planted stone; source figure
scale; alpha fringes; readable silhouettes; jitter, popping and loop wrap.
Geometry audits and still-frame sequences cannot certify smooth playback.

The cut-out limitation is inherent to single-facing relief: joint patches cannot
supply the absent side/back surfaces or a real rotation into depth. Large turns
and falls cannot meet the solid-figure bar just by tuning these transforms.
Proceed with the planned true-3D spearman comparison after pass 3. This pass is a
bounded cleanup and a testable collapse proposal, not art approval.
