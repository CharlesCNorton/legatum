# Animated miniature pilot

**Status: scaffold only; pass 1 is blocked before rendering. No atlas is delivered.**
See [the blocking evidence](review/pass-1.md). Do not wire this into the game until
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

Run a complete render and browser capture pass:

```sh
tools/art/anim/pass.sh 1
```

`require('playwright')` and a downloaded Chromium must be available to Node. If the
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

After each pass, open **all** captures and the per-unit sheets. Write the critique,
changes and measured results to `~/LegatumRuns/anim-pilot/review/pass-N.md`, copy the
note and a few small PNGs into `tools/art/anim/review/`, then commit. Three successful
render/review passes are the minimum; blocked setup is not a completed pass.
The runner handles pushing this branch under the final task instruction.

## Outputs and format

- Git: `app/src/assets/units/anim/<slug>.webp` and `.json`.
- Outside git: `~/LegatumRuns/anim-pilot/masters/<slug>/` holds packed-texture `.blend`,
  projection layers and `frames/<clip>/NN.png`.
- Outside git: `~/LegatumRuns/anim-pilot/review/<slug>.png` shows the source at left
  and every frame on grey and parchment; `<slug>-<clip>.webp` is an animated preview.
- Outside git: `review/pass-N/` holds browser screenshots and `metrics.json`.

Atlases are 2560 × 1280: rows idle/move/attack/hit/death, respectively 8/8/10/4/10
frames. The remaining columns are transparent. Base-centre anchors are explicit
per unit in `units.py`. Packing starts at WebP quality 80, method 6; it lowers quality
only to meet the strict 200,000-byte ceiling and refuses to go below 30.
`validate.py` checks dimensions, metadata, alpha, clipping, transparent padding,
held death pose and byte size. It does not replace visual review.

## Modelling and limitations

The shipped 256 painting is the texture and proportion reference. The higher
resolution panel is inspected for identity, not substituted for the map painting.
Hand-traced regions in `units.py` define anatomical/kit pivots and segmentation.
`prepare.py` separates them and reconstructs the cream base from its painted stone.
`render.py` builds subdivided shallow relief meshes, UV-projects the painting,
skins each part to a Blender armature, and animates the named regions.

This is **single-facing articulated relief**, not a volumetric character model.
It preserves the painting's three-quarter camera and baked soft upper-left light;
emission materials avoid relighting those highlights. The base has no animated
transform. It has baked contact shading only and no outside ground plane.
Seams, uncovered regions, wheel motion, death foreshortening and smoke are still
unreviewed. Do not describe the current result as excellent or production-ready.
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
checks the render configuration and projected opaque samples at all 40 poses, and
writes `masters/spearman/rig-audit.json`. It does not certify the rendered alpha or
quality. `venv/bin/python tools/art/anim/test_pipeline.py` exercises the packer with
temporary synthetic images; none of those images becomes a delivered atlas.
