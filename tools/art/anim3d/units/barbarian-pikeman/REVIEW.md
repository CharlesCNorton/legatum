# Barbarian pikeman, round 1

Status: candidate, **not an art pass**. The saved model is true articulated MPFB
anatomy with original kit; there are no image planes or relief substitutes.

At 256 px, the long diagonal pike, figure height, braced silhouette, tan quilted
coat, red arm tie and kettle helmet are recognizable beside the painting. Frozen
camera UVs retain much of the painting's cloth detail. The render is still visibly
weaker: the front elbow/hand is bulky, face/beard is soft, the coat surface loses
quilt depth and the boot silhouettes do not match. The base top is warm cream but
its side is too dark/rough. A fixed RGB foreground grade improves warmth without
per-frame color shifts. A sample of the base top is #E3C8A6; the same patch in the
painting is more golden, #F2C28D. The shared material target remains #E9CFA0.

At 64 px, the pike diagonal and tan/red costume read as the same unit class, with
an overly broad forward arm and less defined footwear. The rest pose is not hard
to distinguish from the painting, so no external PASS marker is written.

The animation uses authored skeletal keys and a common two-hand pike control.
Idle is small breathing/weight motion; move alternates steps; attack anticipates,
thrusts in depth and recovers; hit recoils; death releases the pike, falls and holds.
The torso remains stiff in move, and combat foot contact and the death landing need
closer review at GPU quality. The arm ribbons are weighted, not cloth simulated.
Unseen linen uses an existing generated painted fill; hidden skin, leather and
metal use procedural materials and need richer paint in a subsequent round.

External evidence: `~/LegatumRuns/anim-pilot/review/3d-v2/barbarian-pikeman-*`.
Editable sources, six AO/Pointiness bakes and raw/graded CPU 256 px frames are in
`~/LegatumRuns/anim-pilot/masters/barbarian-pikeman/`.

The host must run, from the repository root:

```sh
ROUND=1 tools/art/anim3d/units/barbarian-pikeman/gpu.sh
```

That performs the independent rig audit, every GPU render stage, real 512 px
masters and their 256 px derivatives, trimmed 160 px atlas, decoded validation,
review sheets/animated WebPs and an eight-second H.264/yuv420p MP4. The 512 px
render and Metal execution are pending the host pass; CPU previews are not labeled
as GPU results. A successful GPU script is still subject to the visual art bar.
