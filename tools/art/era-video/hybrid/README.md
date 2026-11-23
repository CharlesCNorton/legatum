# Classical harbour: hybrid v11

The galley sails left through the water above the lighthouse mole, west of the
large painted galley's yard: source x=560→464 at y=418. All 144 frames retain the
approved camera, painting, flame tongues, gulls, banners, immersion and reflection.
The oars sweep on a 1.35-second cycle with synchronized small foam pulses.
No simulation or bake is required.

Python projection measurements at 1920×1080:

- Horizontal screen travel: **271.672 px (14.15% of frame width)**. This includes
  the approved camera move. Actual voyage relative to the painting is **96 source
  pixels**, or **97.44 px with the first camera held fixed**, versus 11 source
  pixels in v10. Do not describe all 272 pixels as independent boat motion.
- Conservative full-ship clearance: **8.720 px minimum**, at frame 1 against the
  distant eastern lateen sail. Every frame checks the sail, rigging and full oar
  envelope against all painted ships and harbour obstacles. The large galley's
  thin mast and the lighthouse tower have separate envelopes from their wider
  bases, preserving the open water beside them. Both Python and Blender enforce
  the 8-pixel full-resolution minimum.
- Depth-matched size ratio: **1.121–1.137**. The 28-pixel far square-sail hull joins
  the existing 44- and 56-pixel hull references, so this farther lane interpolates
  within measured depth instead of clamping to a nearer boat's size. Projected
  hull widths at frames 1/72/144 are **34.8 / 38.2 / 42.8 px**.
- The hull-contact strip and reflection centre remain fully inside the water mask
  in every frame; waterline projection error is below 0.01 px.

Water highlight amplitudes are 40% of v10, with sparse short soft sparkles and
gloss confined to the upper-left sun's diagonal reflection path. The painted
water colour remains the base. The ember pool drops from 60 to 28: 11–13 particles
are above alpha 0.25, with 1.2–2.2 px initial lengths at 960, soft edges, slight
rising drift, shrinking silhouettes and orange-yellow to deep-red cooling.
The beacon retains its visible 57–68 px height at 960, with a wider warm-grey
profile, overlapping soft lobes and a thinning top. Its tiny warm base is unchanged.

`scene-report.json` records all-frame measurements; `prepared.json` hashes the
recipe and assets. These are preparation checks, not rendered visibility claims.
The lead owns Blender API validation and visual review under the lock. Original
masters and v10 artifacts are untouched. This pass does not commit.

## Commands

From the repository root, preparation and compilation only (both passed):

```sh
export ERA_HYBRID=/Users/samcorcos/LegatumRuns/era-video-pilot/masters/hybrid-v11
export ERA_PYTHON=/Users/samcorcos/LegatumRuns/era-video-pilot/venv/bin/python
"$ERA_PYTHON" tools/art/era-video/hybrid/scene.py \
  --masters "$ERA_HYBRID" --out "$ERA_HYBRID/frames-960" --prepare
"$ERA_PYTHON" -m py_compile tools/art/era-video/hybrid/scene.py
```

Lead only, while holding the existing Blender lock (not run by the editing agent):

```sh
hybrid_v11() {
  /opt/homebrew/bin/blender -b --factory-startup --disable-autoexec -t 6 \
    --python-exit-code 1 -P tools/art/era-video/hybrid/scene.py -- \
    --masters "$ERA_HYBRID" "$@"
}
hybrid_v11 --out "$ERA_HYBRID/frames-960" --dry-run
hybrid_v11 --out "$ERA_HYBRID/frames-960" --frames 1-144
hybrid_v11 --full --out "$ERA_HYBRID/frames-1080" --frames 1-144
```
