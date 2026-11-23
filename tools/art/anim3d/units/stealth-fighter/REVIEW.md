# Round 2 review — CPU candidate, not PASS

Round-1 GPU execution completed successfully: nine stages at native 512px,
96 samples, Q90 atlas and valid eight-second movie. Its source masters and
review sheets are preserved externally in `masters/stealth-fighter/driver-r1-gpu/`
and `review/3d-v2/stealth-fighter-round1-preserved/`.

Round 2 restores painted limestone grain and the original lower rim on the
closed stone cylinder, using the recorded generated stone fill with live contact
AO. The solid support now reaches the actual belly in the alternate camera and
topples from its foot during death instead of disappearing. The beveled missile
is wider and travels farther. Build preflight rejects changed source scripts,
texture inputs or packed blends before the GPU pass.

All nine stages were regenerated in Cycles CPU at native 512px, eight samples
with denoising, retaining 256px copies. Every interim sheet, five strips and
animated WebPs, rest split/crossfade, top/front flight check, decoded atlas sheet
and round-2 MP4 are current. Masters remain outside git.

Final CPU candidate: **168,516 bytes at Q90**, 160px logical cells, all
**8/8/10/4/10** frames with per-frame trim offsets and fixed anchor (80,132).
The last death samples reuse one rectangle for exact decoded stability.

Checks passed:

- Seven delivery regression tests, including stale-build and changed-blend rejection.
- Eight Python files parsed; both shell scripts passed `bash -n`; diff whitespace clean.
- Five clip geometry audits: 23 meshes, closed principal airframe volumes,
  finished UV surfaces, correct control pivots, stationary disc, visible solid
  support throughout death, loop closure and numerical wreck contact.
- Atlas reconstruction: every alpha/offset, transparent gutter, source/grade
  hash, clipping margin, motion and exact terminal hold passed.
- All nine native512/derived256 stage manifests, dimensions and hashes checked.
- H.264/yuv420p movie: 1600x348, 240 frames, exactly 8 seconds. Decoded sample
  and every clip strip inspected.
- Packed build and texture preflight passed. No Rust, rules or runtime changes.

At 64px the unit matches the painting's identity, scale and silhouette. At
256px the stone is substantially closer, with a visible bevel and fine grain;
the airframe retains the registered painting's panel and canopy colours.
Opaque-overlap RGB MAE improved from 5.649796 (round-1 GPU) to 5.026279
(round-2 CPU); alpha IoU is 0.970850. These cross-device correspondence numbers
are diagnostic, not approval. Fine panel/canopy edges remain softened, oblique
engine joins are coarse, and projected lighting remains attached to surfaces.
The crash is continuous but still reads as a controlled descent. No PASS.

Run from repository root on the lead's Metal-capable host:

```sh
ROUND=2 tools/art/anim3d/units/stealth-fighter/gpu.sh
```

This executable takes no arguments and renders every stage, creates 512/256
masters, trims and validates the atlas, audits geometry, writes the MP4 and
records a GPU receipt. Round-2 GPU execution is not claimed from this sandbox.

Non-obvious findings: generated transparent fills can contain alpha 1–8 specks
far outside the subject; threshold before measuring their texture footprint.
Also, a perfect rest-camera overlap can hide a disconnected stand: inspect
alternate plain views and extend the real support into the hull before freezing
its projection. The attached support is retained as real geometry through death.

Git staging was denied creating `.git/worktrees/lane-19/index.lock`. Changes
remain uncommitted for the runner. `origin/master` was already contained in
HEAD; no merge was needed. Suggested commit: `Refine stealth fighter stone,
support and release animation`, with trailer:

```text
Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>
```
