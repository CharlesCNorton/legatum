# Artillery round 4 candidate

Run the complete host GPU pass from the repository root:

```sh
ROUND=4 tools/art/anim3d/units/artillery/gpu.sh
```

The executable takes no arguments. It rebuilds the true 3D gun, bakes AO/curvature, renders all
stages and 40 animation frames with Cycles Metal at 512px/128 samples, retains 512/256 masters,
renders front/top running-gear checks, packs the trimmed 160px atlas, validates it and encodes
the eight-second five-clip MP4. The transcript reaches stdout and `artillery-gpu-pass-r${ROUND}.log`.
Failure status and success receipts are round-specific. CPU previews, missing inputs, stale hashes
and unavailable Metal cannot issue a GPU receipt. The script never writes an art PASS.

```sh
RESOLUTION=256 SAMPLES=16 tools/art/anim3d/units/artillery/render.sh preview
ROUND=4 ~/LegatumRuns/anim-pilot/venv/bin/python tools/art/anim3d/units/artillery/deliver.py
```

`render.sh stills` publishes plain/rest/detail comparisons. Assets remain in
`~/LegatumRuns/anim-pilot/assets/artillery/`; editable blends, bakes and frames remain under
`masters/artillery/`. Successful round-3 GPU evidence is preserved in `masters/artillery/round3-gpu/`
and `review/3d-v2/artillery-round3-gpu/`: 176,450 bytes at Q80, technically valid and not art-approved.
Old active 512px frames are explicitly retained as `round3-512-stale`; round-4 GPU finals are pending.

Round 4 improves the solid disc with a generated clean stone plate and fresh contact AO. No image
alpha replaces geometry. The prompt, source and exact input hash are in `SOURCES.md`. The original
generated olive fill supplies desaturated rubber grain around complete tires, with live physical
lighting and cavity shading. Actual tread bevels carry lighter dust; corrected radial orientations
keep chevrons aligned, and three fine sidewall moldings add depth. Hidden tire painting projection
was rejected because it sampled unrelated shield/axle colors. Hubs retain the original painted detail,
with broad illumination separated from rotation. The warm muzzle flash is smaller.

Full-depth raised trails, braced spades, U-shaped supports, hollow bore and source-registered shield
remain. Bevels and topology finish precede painting UVs. Warm key/cool rim/soft fill, real AO/Pointiness
bakes, and one bounded source-measured histogram grade serve all clips. The orthographic camera is
a calibrated approximation, not an exactly recovered viewpoint. No crew, fabric or straps are invented.

An actual denoised/raw comparison found that denoising smoothed painted detail and tread grain.
The handoff therefore uses 128 samples without denoising; the manifest records that setting.
CPU16 previews are visibly noisier than the intended GPU512 final and cannot establish its quality.

Clip counts stay 8/8/10/4/10. Move rolls in place with lifted trails; attack recoils; hit jolts;
death slumps and holds. Forty-two sampled poses check tire contact and ground clearance. Sixteen
front/top renders check parallel rolling axes and non-rolling light frames that follow the hubs.
These checks are not a full collision solver or a world-space travel/no-slip test. Identical atlas
frames share rectangles so the decoded final death hold is pixel-identical. The atlas uses
`version:2, layout:"trimmed-rows"` with per-frame rectangles, offsets and a fixed logical anchor.
No runtime integration, game rules, or Rust/UI code changed.

**Visual approval remains separate from technical validation.** Review the current 256/64 comparison,
all five strips, decoded MP4 and front/top views before writing `artillery-PASS`.

Round-4 CPU result: 40 frames at 256px/Cycles16 without denoising. The trimmed atlas is 1520x557,
**199,372 bytes at Q85**. All alpha reconstructions, source hashes, tire contacts, held death,
16 diagnostic views and MP4 checks pass. Video: 1600x348, eight seconds, 240 frames, H.264/yuv420p.
Eleven Python files and two shell scripts parse; whitespace checks pass. Missing-input preflight
fails safely, and GPU validation rejects CPU previews. The repository art gate fails in Node
`render-sets.mjs`; lookalike coverage is unverified.

**No art PASS.** At 256px rubber is consistent through rotation and stone/detail improve, but tires
remain more regular and less weathered than the painting, hubs/supports differ and CPU16 noise is
visible. At 64px the same unit and near-matching scale read clearly; tonal differences remain.
Death is a disabled/slumped gun. The lead must inspect fresh GPU128 finals before approval.
