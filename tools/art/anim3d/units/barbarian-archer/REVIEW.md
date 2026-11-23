# Barbarian archer, resumed round 2

**Review candidate, not art-approved. No PASS marker.** At 256 px the frozen
painted detail, cloth/belts, face position, arm pose and smooth bow curve improve
substantially over round one. The face/fingers, fur outline and pale left boot tip
remain visibly different. At 64 px it reads as the same wolf-pelt archer, but the
upper-body proportions and silhouette still differ. Alpha silhouette overlap at
256 px improves from 0.6873 to 0.7588 (threshold 32); this is not an art-quality score.

The unit remains true 3D MPFB anatomy with its original skin weights and 53-bone
rig, solid kit, generated hidden-surface fills and eight actual AO/curvature maps.
Round two freezes macro shape keys, fits full-depth geometry through inverse skin
transforms, applies surface modifiers before UV calibration, and uses camera-only
painted pigment with physical non-camera shading. The warm product lights remain;
Standard/None avoids compressing the source's painted illumination a second time.
One automatically sampled rest grade is reused across every frame.

All five clips retain 8/8/10/4/10 samples. Saved-scene evaluation verifies all forty
bow/string endpoints, nock tracking, stationary base and nonzero scales. The final
two death PNGs are identical. These checks are not a complete collision solver:
the walk is still stiff, the fall is mechanical and the folded pelt sticks upward
in death. Motion and hidden fills require another artistic pass.

## Artifacts and checks

- New raw and graded CPU256 previews use Cycles, eight samples and denoising.
  All stage sheets, details, rest split/crossfade, five strips/WebPs and decoded
  atlas review are under `~/LegatumRuns/anim-pilot/review/3d-v2/barbarian-archer-*`.
- The shipped candidate atlas is **191,798 bytes, WebP quality 90**, 160 px logical
  cells with trim rectangles/offsets. Forty frames, clip timing, master/render/
  grade/pixel hashes, decoded alpha byte equality, offsets and held death pass.
- Four delivery tests pass: valid delivery accepted; displaced trim offset,
  wrong atlas rectangle and changed clip timing rejected.
- `barbarian-archer-round2.mp4` is decoded from that atlas, verified H.264/yuv420p,
  1600x348, 240 frames/eight seconds, five clips at 2x on cream. Sampled decoded
  movie frames were inspected in `barbarian-archer-round2-video-contact.png`.
- Python syntax, Bash syntax, executable handoff, missing-input failure logging
  and whitespace checks pass. No Rust/app code changed; no Rust/WASM/app build ran.
- Prior genuine CPU512/256 masters and raw frames remain in
  `masters/barbarian-archer/round1-cpu/`. Current previews are not upscaled into
  final 512 masters. GPU512/64 rendering remains unverified in this sandbox.

## Complete GPU handoff

From the repository root, run the executable with no arguments:

```sh
ROUND=2 tools/art/anim3d/units/barbarian-archer/gpu.sh
```

It requires Metal, rebuilds clips from the saved finished master, audits actual
poses, renders every stage and all forty frames at 512/64 samples, exports current
512/256 masters, packs/validates the atlas and encodes the driver's round MP4.
The script retains `gpu-logs-barbarian-archer-r${ROUND}.log` and a stage/status file.
It refuses CPU fallback and does not create an art PASS marker. The sandbox probe
queued behind the shared GPU gate and was cancelled without launching Blender;
this is not evidence of either a GPU success or a GPU failure.

No new asset downloads or image service calls: source URLs, licences and original
generated-fill identity remain in `assets/SOURCES.md` and unit `inputs.json`.
No runtime animation integration, deployment, push or PR is included.

Non-obvious findings: finish bevel/subdivision before freezing camera UVs; freeze
MPFB macro shapes before inverse-skin edits; allow its named `Hide helpers` mask
in the surface audit because it removes helper faces without displacing surfaces;
remove zero-level subdivision rather than trying to apply it. Never edit a shell
entry point while that same script is running: the current shell can resume at an
invalid byte offset. One such iteration stopped after d; all remaining stages
were rerun successfully from the completed script.
