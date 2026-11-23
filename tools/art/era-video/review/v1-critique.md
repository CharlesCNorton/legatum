# Classical v1 art-direction review

Reviewed 2026-11-22 against the source painting and the lead's 168 full-resolution
1920×1080 PNGs. Verdict: **a handsome painting with a competent camera move, but
not yet a premium living painting. Revise before approval.** The composition,
period atmosphere and painted surfaces carry the shot; the animation contributes
too little life relative to how much it moves the framing.

## Ranked issues

1. **The camera overwhelms the life in the scene.** A 9% dolly produces roughly
   10% enlargement and cuts into the left scholars, framing columns and right
   workshop. The frozen reading, sculpting and crowd gestures become more obvious
   as the image grows. Water is barely alive and sails read essentially still.
   This is closer to a moving illustration than an inhabited place. Reduce the
   push and drift; give the harbor and cloth a small but discernible independent
   movement. Do not puppet the people to compensate.
2. **Foreground depth boundaries spend too much distortion for too little depth.**
   Full-resolution first/middle/last crops show narrow soft/rubbery transitions at
   the left columns and some olive leaf tips. They are not catastrophic tears,
   and the smaller contact sheet conceals them. Projection analysis of the actual
   relief estimates peak local stretch about 1.70× at the columns and 1.75× in
   leaves, with compression down to 0.47×/0.39×, after removing ordinary zoom.
   These are local geometric estimates, not claims that whole columns swell by
   75%. The v1 opacity guard measures expansion of triangle edges but misses some
   compression/shear, then averages opacity and reveals the repair gradually.
   Its 0.39% faded-vertex statistic is not a quality guarantee. Reduce relief and
   smooth geometry at silhouettes; check both singular values of projected
   triangles. Avoid exchanging distortion for translucent inpaint ghosts.
3. **The secondary motion is below useful viewing size.** Harbor shimmer is
   extremely restrained, the sail folds barely change, and the three birds are
   effectively absent at normal size. Enlarging a sky crop exposes faint bird
   marks, so this is a readability failure, not proof of missing geometry. Make
   birds a few readable painted pixels with modest travel, and make water/folds
   visible without moving masts, hulls or shorelines. Broad haze and rays are also
   difficult to identify independently; that is preferable to conspicuous fog or
   light stripes. They should remain supporting atmosphere, not advertised events.
4. **The glaze slightly weakens the original pigment separation.** The source's
   blue water and warm stone remain recognizable; there is no destructive AgX
   grade, bloom or glossy relighting. However, a warm veil lifts the harbor and
   also affects relatively near surfaces. In a camera-compensated first-frame
   comparison the water averages approximately +3.4 red, +1.7 green, +0.5 blue
   levels (8-bit). Resampling contributes to this comparison, so it is not a pure
   grading measurement. Confine haze more strongly to distant depth and reduce
   its static strength; preserve painted contrast and the cooler harbor.

## Areas checked that do not justify a new effect

- **Scholars:** faces, hands, scroll and chair remain coherent in the supplied
  middle frames and full-resolution crops. No gross body melt; the problem is
  the static tableau being emphasized by the large push. Their outline strain is
  lower than the columns (estimated peak 1.38×, 99th percentile 1.10×).
- **Central statue:** the raised arm and plinth hold their shape; estimated peak
  stretch is only 1.03×. No convincing detached cardboard layer here.
- **Right awning and figures:** roof scallops, sculptor and marble bust stay
  coherent; localized edge softness deserves a render check, but not a claim of
  severe deformation. Estimated peak stretch is 1.21×. The awning is static;
  the cloth mask covers sails and two pennants, not this canopy.
- **Cardboard:** there are no conspicuous isolated cutout slabs. The shallow
  relief still has a bas-relief quality at the left framing architecture; the
  larger issue is frozen human gestures, not visibly detached people.
- **Smoothness and hold:** no measured jump or abrupt stop. Consecutive full-frame
  mean absolute RGB difference falls from 1.495 at frame 120 to 0.661 at 130,
  0.335 at 135, 0.106 at 140, 0.012 at 144 and 0.0026 at 145. Frames 145–168
  are byte-identical. Keep the quintic camera easing and decelerating motion clock.
  Frame inspection and measurements support this; real-time v2 playback remains
  a lead review gate, especially at 24 fps.

## Evidence and limits

Inspected original PNG crops at frames 1, 72 and 145, the supplied full middle
frames, masks, source painting, and 4× enlarged bird region. Computed consecutive
differences for all 168 frames and sampled camera-compensated differences using
the v1 relief projection. At frames 72–73, compensated mean absolute difference is
0.31 in water, 0.33 in sky and 0.49 in cloth, versus 0.53 in columns and 0.56 in
scholars. Residuals include resampling and geometry/cloth approximation; they do
**not** isolate effects or prove that all residual motion is animation. They do
show why an overall 3–4-level difference is insufficient evidence of visible life.

Local evidence lives under `masters/review/`: `qa-*.jpg`, `aligned-*.jpg`,
`birds-enlarged.png`, `v1-measurements.json`, `analyze-v1.py`, and a snapshot of the
v1 depth mesh/reports in `v1-preparation/`. Black areas in compensated sheets are
outside the moved camera's field of view, not render defects. No Blender render
was performed for this review. V2 changes require the lead's rendered comparison;
a dry-run can validate geometry and animation state, not visual approval.
