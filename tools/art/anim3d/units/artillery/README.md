# Artillery round 3 candidate

Run the complete host pass from the repository root:

```sh
ROUND=3 tools/art/anim3d/units/artillery/gpu.sh
```

This executable, no-argument handoff rebuilds the true 3D gun, bakes AO/curvature, renders plain,
textured, details, poses and all 40 frames with Cycles Metal at 512px/64 samples, retains 512/256
masters, renders the front/top move inspection, packs the trimmed 160px atlas, validates it, and
encodes the eight-second five-clip MP4. The transcript goes to both stdout and
`artillery-gpu-pass-r${ROUND}.log`. Failure status and the GPU receipt are round-specific; unavailable
Metal, stale inputs/frames, CPU masters and failed checks cannot issue a successful receipt.
The script never writes an art PASS. The sandbox cannot run the hardware GPU stage.

```sh
RESOLUTION=256 SAMPLES=16 tools/art/anim3d/units/artillery/render.sh preview
ROUND=3 ~/LegatumRuns/anim-pilot/venv/bin/python tools/art/anim3d/units/artillery/deliver.py
```

`render.sh stills` publishes plain/rest/detail comparisons only. Assets remain in
`~/LegatumRuns/anim-pilot/assets/artillery/`; editable blends, bakes and frames remain in
`masters/artillery/`. The prior successful round-2 GPU evidence is preserved in
`masters/artillery/round2-gpu/` and `review/3d-v2/artillery-round2-gpu/`. That GPU atlas was
180,322 bytes at Q80; it was technically valid and not art-approved.

Round 3 adds raised box trails, collars, bolts, upright/braced spades and actual axle hinge arms.
Full-depth U-shaped supports, a narrower muzzle and whole-wheel mounting changes improve the source
fit. Bevels/curve conversion and subdivision of long rigid faces precede frozen rest-camera UVs.
Flat cap normals and interior visibility samples improve painting coverage. Cream-source exclusion
covers running gear as well as trails, removing stone pigment that rotated around the tires.
Hidden surfaces reuse the recorded image-generated olive paint and physical materials.

Warm key, cool rim, soft fill, physical AO and Pointiness bakes remain. Fine stone pigment grain
and separate gun/stone histogram measurements supplement the finish. Bounded median/10th/90th
percentile channel curves are fixed at rest and shared across every clip; alpha is unchanged.
Full CDF matching was rejected because it amplified low-sample stone noise.

Frame counts stay 8/8/10/4/10. Move rolls in place with raised trails; attack recoils; hit uses a
smaller chassis roll; death slumps and holds its final pose. The 42 sampled poses include loop
endpoints and check both tire contacts and ground clearance. Front/top views come from the actual
saved move clip, with upper equipment hidden for inspection, and check parallel rolling axes.
These are mechanical checks, not a full collision solver or a world-space no-slip test.
Identical atlas frames share a rectangle to keep the decoded death hold pixel-identical.
The atlas is `version:2, layout:"trimmed-rows"`, with explicit rectangles/offsets and fixed anchor;
see the artillery PLAYBOOK chapter. No runtime integration or game rules changed.

**Not art-approved; no PASS marker.** At 256px the raised trails and muzzle are closer, but wheel
shading, central support registration and stone richness still differ visibly from the painting.
At 64px it reads as the same artillery, but the tonal structure remains distinguishable. Rolling
baked illumination is still visible in move, and death reads as disabled rather than destroyed.
The orthographic camera is a calibrated approximation, not an exact recovered camera. Current
round-3 512px finals require the lead's GPU pass and a fresh visual review.

Round-3 CPU validation: 40 frames at 256px/Cycles16; 160px trimmed atlas 1520×557, **182,934 bytes
at Q85**. All 40 decoded alpha masks reconstruct exactly; ground/tire contacts, held death, hashes,
16 front/top samples and video checks pass. MP4: 240 frames, eight seconds, 1600×348, H.264 yuv420p.
Ten Python syntax checks, two shell syntax checks and whitespace checks pass. Missing-input preflight
fails with a transcript/status and no receipt; `--require-gpu` correctly rejects CPU256 previews.
The repository-wide `tools/gates/art.py` check failed in its Node render-sets subprocess, so its
lookalike check is unverified. It reads committed HEAD; it is not the unit's render/atlas validator.
