## 2026-11-23: Separate galley motion from camera travel

- The v10 route moved only 11 source pixels. A dolly can produce a large screen displacement even when the boat barely moves relative to the painting. Report both measurements when judging hero motion.
- The v11 route moves 96 source pixels (97.44 px with the first camera fixed), versus 271.672 px horizontal screen travel including the camera. All 144 Python projection checks pass: 8.720 px minimum clearance at 1080, 1.121–1.137 depth-matched size ratio, full water-mask coverage at hull contact and reflection centre.
- Bounding the lighthouse tower together with its wide mole, or the large galley's thin mast together with its sail, falsely closes adjacent water. Separate conservative rectangles cover the visible silhouettes. Add a far painted hull reference when moving to farther water; do not let interpolation silently clamp to a nearer vessel's size.
- Reduced water highlights, warmer smaller embers and wider warm-grey beacon smoke are authored but not visually verified. Preparation and compilation passed; the lead still runs Blender and reviews the rendered motion under the lock.
