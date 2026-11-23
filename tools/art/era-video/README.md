# Classical era living-painting pilot

**Superseded direction:** the owner rejected camera drift as "just a still image".
The new genuine 3D VFX test is documented in [harbour/README.md](harbour/README.md).
Shared delivery tools now accept `FRAMES=144 SIZE=960x540`; their existing defaults
and the historical living-painting workflow below remain available.

Seven seconds, 1920×1080, 24 fps, 168 PNG frames. No title or other text is rendered.
All code is in this directory; all generated masters and delivery files are outside git.
This is a render-ready pilot, **not a visually approved video**: the sandbox can build
and save Blender scenes but cannot render with Metal. The lead renders and reviews it.

Source painting: `app/src/assets/eras/classical-1920.jpg`.
Source prompt: `app/src/assets/eras/classical.prompt.txt`.
Masters: `/Users/samcorcos/LegatumRuns/era-video-pilot/masters/classical`.
Python: `/Users/samcorcos/LegatumRuns/era-video-pilot/venv/bin/python`.
Blender: `/opt/homebrew/bin/blender` (tested scene build with 5.3.0).
No downloads, installs, generated replacement art, or game integration are needed.

## Scripts and outputs

| Script | Work | Outputs under masters |
| --- | --- | --- |
| `depth.py` | Offline Depth Anything V2 Small, CPU, six Torch threads; robust percentile normalization | `depth16.png`, `depth-preview.png`, `depth.json` |
| `plates.py` | Bilateral + luminance-guided depth, then geometric smoothing; depth-aware donor preparation and OpenCV Telea inpainting; inward-feathered position/color masks | `depth-smooth16.png`, `depth-smooth-preview.png`, `painting.png`, `background.png`, `inpaint-band.png`, `mask-{water,sky,cloth}.png`, `masks-overlay.png`, `relief.npz`, `plates.json` |
| `build_scene.py` | Builds and packs an Eevee scene; optionally renders an inclusive frame range | `scene.blend`, `scene-report.json`, `preview/frame_0001.png` or `frames/frame_0001.png`, etc. |
| `encode.sh` | Checks 168 inputs and first-frame dimensions; H.264 MP4 and VP9 WebM with six encoder threads, serially | `<basename>.mp4`, `<basename>.webm` |
| `contact_sheet.py` | Six evenly spaced frames including both endpoints; labels appear on the QA sheet only | Caller-selected PNG, 1440×592 |

The depth model is `depth-anything/Depth-Anything-V2-Small-hf`. `depth.py` sets
`HF_HOME=/Users/samcorcos/LegatumRuns/era-video-pilot/hf`, `HF_HUB_OFFLINE=1`,
and `local_files_only=True`. White depth means near, black means far; these are relative
inverse-depth values, not physical distances. Plates are specific to this 1920×1080 image.

## Run in order

Run from this checkout. Preparation has already been run; repeat steps 1–2 only after
changing depth or plate settings. The scene file is overwritten on every scene build.
Use different output directories for preview and full-size frames.

```sh
cd /Users/samcorcos/LegatumRuns/era-video-pilot/legatum
export ERA_MASTERS=/Users/samcorcos/LegatumRuns/era-video-pilot/masters/classical
export ERA_PYTHON=/Users/samcorcos/LegatumRuns/era-video-pilot/venv/bin/python
export OMP_NUM_THREADS=6 OPENBLAS_NUM_THREADS=6 VECLIB_MAXIMUM_THREADS=6

# 1. Depth (offline, CPU only).
nice -n 15 "$ERA_PYTHON" tools/art/era-video/depth.py --masters "$ERA_MASTERS"

# 2. Plates and mask overlay.
nice -n 15 "$ERA_PYTHON" tools/art/era-video/plates.py --masters "$ERA_MASTERS"

# 3. Optional non-rendering scene check, permitted inside the sandbox.
nice -n 15 /opt/homebrew/bin/blender -b --python-exit-code 1 \
  -P tools/art/era-video/build_scene.py -- \
  --masters "$ERA_MASTERS" --out "$ERA_MASTERS/frames" --dry-run

# 4. Lead, outside sandbox: full-duration preview at 960x540, 16 samples.
nice -n 15 /opt/homebrew/bin/blender -b --python-exit-code 1 \
  -P tools/art/era-video/build_scene.py -- \
  --masters "$ERA_MASTERS" --out "$ERA_MASTERS/preview" --preview

# Optional short iteration: use --frames 1-12, --frames 72-84, or --frames 140-168.
# Frame numbers always refer to the full seven-second timeline.

# 5. Lead, outside sandbox: full 1920x1080 sequence, 64 samples.
nice -n 15 /opt/homebrew/bin/blender -b --python-exit-code 1 \
  -P tools/art/era-video/build_scene.py -- \
  --masters "$ERA_MASTERS" --out "$ERA_MASTERS/frames"

# 6. Encode both delivery formats.
bash tools/art/era-video/encode.sh "$ERA_MASTERS/frames" "$ERA_MASTERS/classical"

# 7. Six-frame contact sheet (also accepts the preview directory).
nice -n 15 "$ERA_PYTHON" tools/art/era-video/contact_sheet.py \
  "$ERA_MASTERS/frames" "$ERA_MASTERS/contact-sheet.png"
```

The encoder expects `frame_0001.png` through `frame_0168.png` with no gaps. It refuses
preview resolution. MP4 starts at CRF 23, VP9 at 33; each retries at higher CRF if larger
than 2,000,000 bytes, stopping at 35/45 and reporting any remaining oversize. It does not
pad small files. Actual animation size and compression quality require the real render.
H.264 uses yuv420p and faststart; both outputs explicitly convert RGB to BT.709 and use
24 fps without audio. The final ffprobe readback checks codec, size, pixel format, rate
and decoded frame count. If a short frame-range preview is rendered, use its contact
sheet; the delivery encoder intentionally requires the complete full-size sequence.

## Motion and avoiding the cardboard look

There are no separately cut-out people, buildings, trees, or ships. The painting is one
641×361 vertex relief with 460,800 triangles, carrying the original painted texture.
Each vertex is projected back onto the original camera ray after depth displacement,
so the starting composition has no depth-induced bulging. V2 uses 0.20 units of relief
at a camera distance of 8, a 4.5% dolly-in (about 4.7% magnification), 0.008 units of
horizontal drift and 0.003 units of upward drift. Depth gets a six-source-pixel Gaussian
transition before mesh sampling; the painting texture is not blurred. The initial
1.5% crop protects the image perimeter. Camera progression uses quintic easing.

The geometric guard measures both principal stretches of each projected triangle,
including compression and shear, after removing ordinary zoom. Camera-only geometry
outside the 0.90–1.10 stretch bounds fails the build; seven evaluated cloth/camera
samples must also have no folds and stay within 0.75–1.25. The existing repair plane
at z=-0.045 and opacity fallback remain, but the default v2 has no faded vertices:
its camera-only principal stretches are 0.9643–1.0368. The repair image is not a
visible scene layer. It uses a 25-pixel dilated apron and farther-depth donors before
inpainting, and should remain hidden rather than compensate for excessive parallax.

Water uses up to 1.15 horizontal / 0.30 vertical source pixels of shader UV distortion
and at most ±2.5% linear brightness modulation of the existing painted strokes. Sails
and pennants use two local shape-key deformations, with about 1.5 pixels of maximum
combined horizontal displacement. Inward-feathered masks pin their boundaries and keep
motion away from hulls, masts and masonry. Seven evaluated samples measured combined
cloth/camera principal stretches of 0.8629–1.1382, with no folded triangles.

Slow broad noise adds a distance-limited atmospheric glaze and weak oblique sunlight
bands. The haze is reduced and vanishes at relative depth 0.25; sky glaze is halved.
Three tapered blue-gray birds span roughly 7 pixels each at 1080p, travel about 48
pixels independently of the camera over the motion clock, and flex their wings with
staggered phases. Emission materials and the Standard view transform preserve the
source pigments and brushwork without new CG highlights, sharpening, or depth of field.

Camera motion ends at frame 145. A separate motion clock decelerates environmental
motion over seconds 5–6; shader clocks, cloth, and birds all stop too. The scene builder
compares Blender-evaluated state throughout 145–168, including bird wing control points.
During rendering, it copies
the settled image for the rest of the hold, ensuring all final 24 PNGs are byte-identical
and avoiding temporal alpha-dither noise. A range wholly inside the hold renders the
settled scene once, then copies it to the requested frame numbers only. To resume,
rerun with an explicit `--frames a-b`; the script overwrites files in that range.

## Review and verified limits

The rendered v1 review is [review/v1-critique.md](review/v1-critique.md). V1's large camera
move dominated its almost invisible environmental motion; left columns/leaves had
localized depth strain. Its graceful ease into the byte-identical hold passed review
and is unchanged. V2 reduces camera/relief, smooths geometric transitions, improves
motion-mask boundaries and effect readability, and reduces the glaze.

For v2, plates were regenerated and inspected, Python syntax passed, and Blender's
full-size dry build passed geometry and hold assertions at six threads / 64 samples.
`masters/classical/scene.blend`, prepared plates and `scene-report.json` now describe
v2. The existing `frames/` and `classical-v1.mp4/.webm` still contain **v1**; no v2
frames have been rendered. Render steps 4–7 above to judge v2 and encode it. The
v1 diagnostic crops, measurements and preparation snapshot are in `masters/review/`.

Completed here: actual offline CPU depth inference; plate generation; visual inspection
of depth, masks, and background; Blender preview/range and full-size dry builds; evaluated
hold-state assertion; Python/shell syntax checks; real H.264/VP9 smoke encodes and ffprobe
readback using **168 copies of the source painting**, not rendered animation; six-frame
contact-sheet generation and visual inspection on that smoke fixture. The static codec
test was 604,295 bytes MP4 / 990,373 bytes WebM; it does not predict animation size.
Smoke artifacts are in `/private/tmp/legatum-era-codec-smoke`, not in the masters delivery.

No Blender frames were rendered here. The saved `scene.blend` is the full-size 1–168
configuration with 64 samples and six render threads. Blender 5.3 calls Eevee Next
`BLENDER_EEVEE`; the builder also accepts the older `BLENDER_EEVEE_NEXT` identifier.
Its non-rendering build exited successfully despite denied thumbnail/extension-cache
writes outside the workspace. The sandbox also rejected `nice`'s priority adjustment;
the commands request it again for the lead's unrestricted run. CPU libraries and Blender
are explicitly capped at six threads.

Weakest masks: the two small blue pennants and narrow harbor gaps are hand-bounded and
conservative. The leftmost water sliver is deliberately left still to avoid the column;
tiny distant sails are omitted. Sky depth gating can miss a thin strip along ridges and
temple silhouettes. Inspect `masks-overlay.png` (cyan water, violet sky, orange cloth).
The right canopy, human gestures, fire and olive foliage have no independent animation.

In the lead's motion preview, check foreground column/leaf edges, people's outlines,
the statue, and the right awning for repair blur or halos; check pennants for motion in
adjacent masonry and water for shore crawl. Inpainting cannot recover genuinely hidden
architecture, so larger camera moves are outside this pilot's safe range. Keep the
camera subtle; tune `RELIEF`, `DOLLY`, `DRIFT`, and the projected stretch fade together.
Review the final hold and compressed clips before approving the visual result. Masters
remain local; game code, art manifests and rules are unchanged.

Blender API reference used for transparent materials:
[Material.surface_render_method](https://docs.blender.org/api/current/bpy.types.Material.html#bpy.types.Material.surface_render_method).

## Lead handoff

V1 was committed by the lead. V2 edits are left uncommitted as requested; no staging,
commit or push was attempted. Commands and flags are unchanged. Art review and rendered
visual approval remain with the lead; a successful dry build is not visual approval.
