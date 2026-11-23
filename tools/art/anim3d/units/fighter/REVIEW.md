# Fighter — driver round 2 after GPU review

The round1 GPU pass completed successfully: Cycles GPU512/64, all stages,
179,432-byte Q90 atlas and verified MP4. Its masters, raw frames, grade,
receipts and reviews are preserved in `masters/fighter/driver-r1-gpu/`.
The empty outer GPU log was redirection, not a render failure.

This revision replaces triangular wing roofs with closed rounded camber rings,
uses a generated occlusion painting only behind foreground propeller blades,
fits four solid blade outlines to the source painting, and restores painted
stone grain on the lower disc while keeping the upper surface live-lit.
The blades complete cyclic shaft rotations with finite-shutter blur, then fold
forward on impact. Contact checks evaluate the actual deformed meshes.
The top/front diagnostic now fits every move sample without cutting off wings.

Current evidence is **256 px / Cycles CPU / 32 samples**. All interim b/c/d/e/f/g
sheets, five animated WebPs and the decoded round2 MP4 are updated. The new
editable masters and six AO/Pointiness bakes are external; the prior GPU512
frames remain preserved and are not represented as new final renders.

Checks:

- Geometry/contact audit passed: closed positive-volume principal solids and
  propeller blades, stationary base over 40 frames, safe scales, closed flight
  and shaft loops, evaluated crash contact and held terminal death.
- Trimmed 160 px atlas passed: **187,518 bytes, quality 85, 1470 × 770**,
  **8/8/10/4/10** frames, exact decoded alpha, transparent gutters, trim offsets,
  current source/clip/grade hashes and identical held final frames.
- Atlas-decoded MP4 passed: **H.264 / yuv420p / 1600 × 348 / 240 frames / 8 s**.
  Inspected decoded frames at 0.3, 0.7 and 1.43 seconds beside round1 frames.
- Python AST parsing, Bash syntax and `git diff --check` passed.
- Build-input seal verifies the current scripts, four licensed images, two
  editable masters and six bakes. GPU missing-master preflight fails explicitly;
  GPU verification rejects CPU evidence with `Not GPU512: b`.

At **256 px**, the silhouette, blade placement and stone rim are closer to the
painting, and hard wing-repair stripes are reduced. Wing camber/profile, base-top
shading and canopy thickness remain visibly different. The fixed-view texture
still stretches under larger crash rotations. At **64 px**, identity, composition
and palette match closely; this is not an indistinguishable-rest-pose claim.
Motion blur is cleaner at 32 than 12 samples, but final GPU512 alpha edges need
inspection. The crash remains a stylized damaged miniature, not a detailed wreck;
attack flashes are subtle. No `fighter-PASS` is justified yet.

Lead handoff from this checkout:

```sh
ROUND=2 tools/art/anim3d/units/fighter/gpu.sh
```

The executable no-argument script verifies saved build inputs, clears partial
clip-selection overrides, regenerates all five clips, audits, renders every
stage on Cycles GPU512/64, exports genuine 512/256 masters, packs/validates,
and writes the five-clip MP4 plus a hash-bound receipt. It never grants art PASS.
No Rust, engine or runtime UI code changed.

Working-tree hygiene: 17 changed text files, zero findings. `origin/master` is
already an ancestor of this branch. Git add/commit was denied at
`.git/worktrees/lane-8/index.lock`; changes remain uncommitted for the runner.
Intended message: `Refine fighter wing paint and mechanical animation`, with
`Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>` as the final trailer.
