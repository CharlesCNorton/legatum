# Round 1 — candidate, not PASS

The round is built and reviewed with Cycles CPU at 256 px / 12 samples. No host
GPU pass has been observed. The complete GPU handoff is executable and uses the
same model/material/rig/clip build. The runtime painting remains unchanged.

At 256 px the rest projection carries the painting's steel wear, red/yellow
slashes, face and belts, but the head/neck, beret feather and hip/skirt contours
still differ visibly. The base is cream now, although its rim and contact shade
are flatter than the painting. Newly exposed shoulder/arm and rear cloth surfaces
are less rich and reveal projection transitions. The pike thrust now reads,
but the shoulder/cuff deformation and the terminal fall need another visual pass;
the fallen body overhangs the small pedestal. This is not hard to distinguish
from the painting at rest, so no `reislaufer-PASS` was written.

At 64 px it reads as this unit: upright pike, feathered cap, steel chest and
contrasting slashed legs. The painting is still fuller around the hips and hat.

Evidence in `~/LegatumRuns/anim-pilot/review/3d-v2/`:
`reislaufer-b-plain.png`, `-c-textured-lit.png`, `-c-details.png`,
`-d-rig-poses.png`, all five `-e-<clip>-strip.png` and `-e-<clip>.webp`,
`-f-restpose-compare.png`, `-g-feet-check.png`, `-g-decoded-atlas.png`,
`-round1.mp4`, `-audit.json`, `-validation.json`, `-pack.json`, `-video.json`.
The honest running chronology is `reislaufer-log.md`.

Checks completed:

- Blender build, three real 512px AO/curvature bake pairs, frozen-camera projection,
  53-bone rig and all five action builds succeeded.
- Blender scene/clip audit passed: 190 finished projected meshes, zero sampled
  UV projection error, stationary base, positive scales, unchanged leg lengths
  within the stated tolerance, both motion and held death. Maximum checked
  support-hand error was 0.000000248 m.
- Top/front gait views reviewed. Contact IK removed the initially measured
  0.02865 m drift; final sampled support-ankle planar drift in the virtual
  travelling frame is 0.000000031 m, support-foot yaw 0.028 degrees. These are
  sampled contact-window checks, not continuous collision or sliding proof.
- Trimmed 160px atlas: **156902 bytes, WebP quality 90, 40 frames**, all required
  8/8/10/4/10 samples. Validation passed source/render/grade/metadata hashes,
  exact decoded alpha and offsets, bounds, motion and identical held death.
- Six delivery regression tests passed, including corrupt frame/rest/atlas,
  wrong trim offsets, and rejecting CPU output as a GPU receipt.
- FFprobe verified H.264, yuv420p, 1600x348, 240 frames, 8 seconds. All five clips
  play side by side from the decoded trimmed atlas at 2x on cream.
- Seven Python files parse; both Bash entry points pass `bash -n`; whitespace
  check passes; working-file hygiene reports zero findings. No Rust, WASM or app behavior changed.

Editable blends, raw previews, bakes and real 256px masters are external under
`masters/reislaufer/`. **512px animation masters are pending the host GPU pass**;
CPU previews were not upscaled and mislabeled as 512. The host must run:

```sh
ROUND=1 tools/art/anim3d/units/reislaufer/gpu.sh
```

That rebuilds/renders all stages on Metal Cycles, retains 512/256 masters,
recreates the atlas and reviews/movie, reruns validation/regressions, and writes
a GPU receipt only after checking dimensions/device/hashes. Visual approval
remains a separate judgment; the script never writes PASS automatically.

Git staging was attempted but the sandbox denied `.git/worktrees/lane-22/index.lock`.
Changes remain uncommitted for the runner; no push or PR was made. The advertised
branch is current with the available `origin/master` (zero missing commits).
