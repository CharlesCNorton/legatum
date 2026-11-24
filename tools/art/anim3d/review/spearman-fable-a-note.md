# Spearman look lane (fable-a): Eevee painted look

Branch `fable/unit-anim-3d-spearman-a`, cut from the round-9 candidate. Look only: geometry, weights, UVs, cloth caches, actions and the camera are untouched. Astra's masters were copied to `~/LegatumRuns/anim-pilot/fable-a-masters`; nothing under `lanes/` or `masters/` was written. **Not PASS**: the silhouette target needs the form lane.

## What it is

`tools/art/anim3d/units/spearman/look.py` opens a master or clip `.blend`, replaces every material at render time (nothing is saved) and renders with **Eevee, Standard view, emission only**:

- **Projected paint** where the stored rest visibility says the surface was seen: the painting itself, no second lighting pass, no grade.
- **Unseen surfaces** (backs, undersides, what motion reveals): white Diffuse → Shader to RGB → a value ramp of the part's own painted colours, lit by one camera-space upper-left sun, with a soft fill, AO and stroke noise in rest coordinates.
- **Cast shadow alone** (a diffuse whose normal is the key direction) darkens projected paint a little and the stone fully, so shadows move with the shield and legs without relighting painted form.
- **Stone** is shaded, not projected, from colours measured on the painted disc.

`look_textures.py` builds the data from the painting plus one flat ID pass: one inpainted paint texture per kit part, low-frequency local colour, and the ramps. `look_compare.py` writes painting | render | crossfade at 256 and 160 with the critique numbers. `look_deliver.py` writes 512/256 masters, the trimmed 160 atlas (delivery.py's packer and validator), a 160 contact sheet and the five-clip movie. Rest plus all 40 frames render in about 55 s.

## Numbers (rest pose, 256 px, critique.py definitions)

| | IoU | ΔE (critique, render shifted +1 px down) | ΔE at zero offset |
| --- | --- | --- | --- |
| Round 9 (Cycles CPU, graded) | 0.9053 | 13.71 | 10.73 |
| fable-a first Eevee pass | 0.9053 | 14.45 | 11.06 |
| + painting registered to the frozen UVs | 0.9048 | 14.69* | 10.77* |
| + display-space reduction, torso layers keep all paint | 0.9048 | 13.29 | 8.45 |
| + sun calibrated (π), cast-only term, ordered ramps | 0.9048 | 12.62 | 7.10 |
| + shaded stone | 0.9048 | 12.46 | 7.34 |
| + linen/feet fixes, painted shaft width (v3, current) | 0.9091 | **12.38** | **7.20** |
| **v3 look on fable-b's form** (`fable-b-masters`, read-only) | **0.9204** | **6.80** (offset 0,0) | **6.80** |

\* measured with the old linear-light reduction; not comparable with the rows below it.

IoU is unchanged by design (no geometry edits). critique.py picks the offset that maximises silhouette overlap (+1 px down) and measures colour there; projected paint is registered at zero offset, so every painted edge then counts as colour error. Both numbers are reported. Per part at zero offset: shield 3.0, cuirass 3.2, belt 3.5, skirt 3.9, greaves 4.3–5.2, helmet 5.4, spear 5.8 (round 9: 21.3), cloak 10.9, skin 9.6, sandals 18–22, stone top 12.6. The high ones are where the 3D outline and the painting disagree (stance, feet, cloak extent, disc size): form-lane territory.

Tone error after a 2 px Gaussian (the cloud reviewer's proposed metric, target ≤ 6): **4.94** on the round-9 form, **4.41** on fable-b's form. Round 9 itself: not measured that way before this lane.

On fable-b's form the silhouette search settles at zero offset, so the critique ΔE drops to 6.80 with no change to the look: about 5.5 of the 12.4 on the round-9 form is the +1 px shift, not colour.

Atlas previews (not written under `app/`): 196,822 bytes at quality 85 on the round-9 form; 187,206 bytes at quality 80 on fable-b's form; 40 frames, validation PASS both.

## After the art director's block on v1 (03:24Z)

- Linen too dark: the thigh skin was rejecting painted linen and inpainting flesh. Skin now rejects only red. Skirt band (x 108-134, y 140-170) luminance 85 → about the painting's.
- Shaft: render-time bevel to 21 mm (painted width), ferrules 28 mm. This is a form change made in the look because it is the first tell at 160 and 64; set `shaft_radius=0` once the master's shaft is right. IoU 0.9048 → 0.9091 from this alone.
- Feet: toes inside the sandal zone take the sandal's leather paint; the dark lump was the cast shadow at 85% plus a wide AO, now a 7 cm contact shadow and a 16% cast shadow. Foot size and splay are untouched (form lane).
- Shoulder patch in hit and death: the tunic mesh lies under the painted cloak collar. Where its continued paint is red its unseen surface now uses the cloak ramp, so the shoulder turns cloak-red instead of pale, pink or brown.
- Base: shaded stone with the painted top, edge lip, side and shadow colours; no blotches from projected paint.
- Not done: pale sliver under the spear hand (a sleeve vertex, geometry), calf slab and ring on the right greave (geometry), cloak width (geometry).

## What worked

1. **Eevee emission instead of Cycles + denoise + histogram grade.** The paint arrives pixel-for-pixel; the round-9 softness was the denoiser at 16 samples and the grade.
2. **Registering the painting to the frozen UVs.** `project.py`'s calibration (349 + (x−75)·556/105, 9 + (y−12)·1236/232) is 0.9% narrower and 0.3% shorter than the true fit (5.3425 source px per 256-canvas px about (627,627)↔(127.5,128)). That alone costs about 3 ΔE. The UVs stay; `look_textures.py` resamples the texture.
3. **Reducing renders the way the painting was reduced.** The game's 256 painting is a display-space Lanczos of the 1254 master (refit: 0.7 ΔE). The same pixels reduced in linear light score 3.1. Linear-light is right for compositing, wrong for matching this reference.
4. **Per-part paint textures.** Each part keeps the painting only inside its own rest outline and inpaints the rest from its own pixels (push-pull). Hidden and misregistered surface continues its own colour. The spear shaft, which had no projection at all (a curve, plain PBR wood), now reads the painting through an object-space version of the same projection.
5. **Ramps fitted to the painting's value distribution.** Each ramp stop sits at the lighting quantile of the 3D surface and carries the colour at the same luminance quantile of that material's paint, so unseen surfaces have the painting's contrast and the key decides where lights fall.
6. **Batching variants in one Blender session.** One wait for the GPU lock, eight A/B renders in 13 s.

## What failed or was dropped

- **Colour-cost part assignment** (k-means colour distance + distance to the 3D outline): bronze, leather, skin and wood are one colour family; the result was salt-and-pepper. Replaced by the 3D outline plus a coarse family test (red / pale / warm).
- **Family test on every part**: the model's tunic sits where the painted cloak collar is, so "linen only" turned the collar dark. Torso layers now keep all paint; only rigid or free-swinging parts (shield, helmet, greaves, sandals, spear, cloak, crest, skin) reject another family's paint.
- **Retargeting painted sandals box-to-box onto the 3D feet**: smudged; the anatomical feet are too small for the painted sandal detail. Removed. The feet need the form lane.
- **Projecting a cleaned painted disc onto the stone**: the 3D disc is larger than the painted one, so the painted rim highlight landed mid-top as a visible step. Replaced by the shaded stone.
- Eevee gotchas that each cost a round: an unlinked Normal socket ignores `default_value` (link a Combine XYZ); a sun of strength 1 returns 1/π on white diffuse; ColorRamp elements re-sort when positions are assigned in place; a script named `inspect.py` next to others shadows the stdlib and breaks numpy.

## For the merge

- One command: `tools/art/anim3d/units/spearman/look.sh MASTER_DIR OUT_DIR [LOOK_DIR]`. Verified on the round-9 masters (83 s) and on `fable-b-masters` with the look data written to my own folder (`fable-a-masters/look-on-fable-b/`). Previews: `spearman-fable-a-look-on-fable-b-rest.png`, `-clips-160.png`, `.mp4`.
- A coordinator message meant for fable-b (its death/hit clips and `spearman-fable-b-note.md`) reached this lane. I did not act on it beyond checking that fable-b's clips render with this look: they do, all five.

- The look is render-time only: run `look.py` on whatever master and clips the form/motion lanes produce, after `look_textures.py` on the new master (ID pass → textures → ramp-input pass → ramps; 15 s).
- Wants from the form lane, in order of colour cost: wider stance and larger sandals, cloak extent, stone disc size, greave tops reaching the knee.
- GPU lock: `blender-slot` polls every 5 s, so a long `gpu.sh` in another lane can starve short Eevee jobs. Batch variants per call.
