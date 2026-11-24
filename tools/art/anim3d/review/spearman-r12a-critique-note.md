

### Automated critique: spearman-round12 (R12a Cycles CPU hybrid fallback; 256 rest / 160 clips, 16 samples, seed 17, fixed R11 LUT; not GPU)

- Silhouette IoU: **0.9229** (target ≥ 0.95; FAIL). Best of ±3 px offsets: render x=+1, y=+0.
- Tone/colour ΔE on blurred images (sigma 2 px, CIE76): **6.29** (target ≤ 6; FAIL), at zero offset over 11632 overlapping pixels including base. Information only: raw per-pixel ΔE 10.11; at the IoU offset blurred 7.35, raw 14.41.
- Regions (blurred ΔE): head_crest 3.5, torso 2.6, cloak_spear_side 4.7, shield 2.5, legs 6.0, feet 13.8, base 7.1.
- Painting mask: alpha; frames: idle 8, move 8, attack 10, hit 4, death 10.
- Rest: `/Users/samcorcos/LegatumRuns/anim-pilot/review/3d-v2/spearman-r12a-rest.png`. Contact sheet uses `/Users/samcorcos/LegatumRuns/anim-pilot/lanes/spearman-r12a/masters/spearman-3d-v2/r12a-motion-graded`.

