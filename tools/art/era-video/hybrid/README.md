# Classical harbour: hybrid v10

The v9 painted flame cards remain. The galley moves into the middle harbour,
source x=528→517 at y=550, between the smaller foreground sailboat and the large
painted galley. The camera, painting, gulls, water glints, banners, oar foam,
144 frames, six threads and `--full` framing are unchanged. No simulation or bake.

The relief map is artistic disparity, not metric distance. Hull size is calibrated
from two measured smaller painted boats (44 and 56 source pixels), interpolated by
sampled relief depth. The large merchant galley's 145-pixel hull is a separate
comparison, not the size target for this narrow lane.

Python projection measurements at 1920×1080:

| Frame | Moving hull | Depth-adjusted reference | Ratio | Nearby painted sailboat | Large painted galley |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 53.3 px | 47.5 px | 1.123 | 56.8 px | 147.2 px |
| 72 | 58.1 px | 51.5 px | 1.127 | 61.7 px | 159.9 px |
| 144 | 64.1 px | 56.5 px | 1.134 | 67.7 px | 175.2 px |

- All 144 frames pass the 0.9–1.2 depth/scale ratio. The ratio to the actual nearby
  sailboat is 0.938–0.947 at the sampled frames.
- Conservative full-ship clearance from 12 painted ships plus the lighthouse
  mole, quay and near shore is at least **4.168 px at 960 / 8.336 px at 1080**,
  at frame 1 against the large galley. The Blender build independently validates
  actual evaluated meshes and camera projection.
- The immersed local waterline at z=-0.22 clips a keel extending to z=-0.95.
  Its centre is ray-aligned with the sampled water surface; projection error is
  below 0.01 px. The entire contact strip and reflection centre have water-mask
  coverage 1.0 in every frame. The dark contact, directly attached reflection,
  wake and foam follow the same placement and depth-scaled size.
- The distant beacon uses a pale plume, with a projected alpha envelope about
  57–68 px tall at 960, and a small warm base point. Its visibility depth covers
  the entire plume footprint, not just the anchor.
- Six flame cards retain their textures, tongues and transparent edges, at 1.5×
  width/height and emission 1.85 (was 1.35); scholar spill is unchanged.
- The 60-spark pool has 46–47 particles above alpha 0.25 per frame. Streaks are
  2.8–4 px long and 1–1.35 px wide at 960, with brighter ivory-orange emission,
  a longer bright lifetime and origins at the flame tips. They bypass brush blur.

`scene-report.json` records all-frame measurements; `prepared.json` hashes the
recipe and assets. These are preparation checks, not rendered visibility claims.
The lead still owns Blender API validation and visual review under the lock.
Original masters and v9 artifacts are untouched. No commit is made by this pass.

## Commands

From the repository root, preparation and compilation only:

```sh
export ERA_HYBRID=/Users/samcorcos/LegatumRuns/era-video-pilot/masters/hybrid-v10
export ERA_PYTHON=/Users/samcorcos/LegatumRuns/era-video-pilot/venv/bin/python
"$ERA_PYTHON" tools/art/era-video/hybrid/scene.py \
  --masters "$ERA_HYBRID" --out "$ERA_HYBRID/frames-960" --prepare
"$ERA_PYTHON" -m py_compile tools/art/era-video/hybrid/scene.py
```

Lead only, while holding the existing Blender lock (not run by the editing agent):

```sh
hybrid_v10() {
  /opt/homebrew/bin/blender -b --factory-startup --disable-autoexec -t 6 \
    --python-exit-code 1 -P tools/art/era-video/hybrid/scene.py -- \
    --masters "$ERA_HYBRID" "$@"
}
hybrid_v10 --out "$ERA_HYBRID/frames-960" --dry-run
hybrid_v10 --out "$ERA_HYBRID/frames-960" --frames 1-144
hybrid_v10 --full --out "$ERA_HYBRID/frames-1080" --frames 1-144
```
