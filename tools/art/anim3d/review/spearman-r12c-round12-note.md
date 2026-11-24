

### Automated critique: spearman-r12c-round12 (Cycles CPU hybrid fallback 256px 16 samples fixed R11 LUT)

- Silhouette IoU: **0.9219** (target ≥ 0.95; FAIL). Best of ±3 px offsets: render x=+1, y=+0.
- Tone/colour ΔE on blurred images (sigma 2 px, CIE76): **6.42** (target ≤ 6; FAIL), at zero offset over 11640 overlapping pixels including base. Information only: raw per-pixel ΔE 10.29; at the IoU offset blurred 7.46, raw 14.55.
- Regions (blurred ΔE): head_crest 3.5, torso 2.6, cloak_spear_side 5.5, shield 2.5, legs 6.0, feet 14.8, base 6.9.
- Painting mask: alpha; frames: idle 8, move 8, attack 10, hit 4, death 10.
- Rest: `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r12c/preview/graded-rest-00.png`. Contact sheet uses `/Users/samcorcos/LegatumRuns/anim-pilot/review/3d-v2/spearman-r12c-decoded-160`.

