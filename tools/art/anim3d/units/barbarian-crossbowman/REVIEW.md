# Barbarian crossbowman — driver round 3

Review candidate; **no visual PASS**. The runtime is unchanged.

The lead's round-two GPU pass succeeded: GPU64/512, 40 frames, Q90,
173282 bytes, and an eight-second H.264 video. Its rest comparisons, all five
strips and decoded video frames were opened before edits. Previous GPU evidence
is retained under `masters/barbarian-crossbowman/driver-r2-gpu/`.

This round replaces exposed anatomical toe shells with closed leather shoes,
uses source foot bones without changing retargeted rotations, and masks covered
toes that otherwise protrude during rollover. Hulls use evaluated visible MPFB
anatomy; raw vertices include hidden helpers. Sleeves now select evaluated arm
weights instead of a clipped coordinate band. The tunic and stitched channels
use transferred spine/hip/thigh weights, preserving their rest surfaces through
inverse skin matrices. This is skinned folded cloth, not cloth simulation.

The case is shorter and has real leather bands and a suspension strap. Revealed
surfaces use recorded generated skin/leather/linen fills. A new clean stone plate
from built-in ImageGen textures the real beveled disc with live contact AO;
alpha affects pigment only. Source projection, finished geometry, product
lighting, real AO/curvature bakes and one automatic rest-derived histogram grade
remain. Sparse glTF pose channels are cleared before selecting source actions.

At 256 px the face and quilt brushwork are close, and shoes, case and stone are
closer than round two. At 64 px it reads as the same unit and scale. It is still
distinguishable: the hood/cape side geometry and collar transitions are crude,
revealed surfaces have less detail, soles are simple, and the death landing
remains stiff. No claim of five visually clean clips or painting parity.
Rest alpha IoU increased from 0.855023 (prior GPU) to 0.864922 (CPU), a
silhouette-only comparison under different render settings, not art approval.

Verified current CPU candidate:

- Cycles CPU8/256: fresh b/c/d and all five e reviews; 16 front/top feet views.
  All strips, rest/details comparisons and decoded round3 MP4 frames inspected.
- 40 samples, trimmed160 WebP **162088 bytes / Q90**. Model/clip/grade/frame/
  atlas/metadata hashes, bounds, motion, exact trim-alpha reconstruction and
  decoded terminal death hold pass.
- All five 53-bone scene audits pass, including closed manifold shoes, no loose
  shoe vertices, stationary base, nonzero scales and painted-source checks.
  Maximum wrist/stock error 0.000362 mm; idle/move closure exactly zero;
  hit recovery matrix error below 4e-18.
- Foot support yaw 2.64459 degrees; virtual-ground toe stance residual
  0.000588 mm over five intervals. This does not prove full sole contact.
- MP4: H.264/yuv420p, 1600x348, 240 frames, 8.000 seconds; reconstructed from
  the actual trimmed atlas, all five clips at 2x on cream.
- Two delivery regression tests pass; 17 Python files compile; both shell scripts
  pass syntax checking; diff whitespace passes. All five pinned texture inputs
  pass preparation. No Rust, UI or simulation code changed.
- Final GPU-master gate intentionally rejects current CPU evidence. Round-three
  GPU512/256 masters remain pending. No PASS marker was written.

Complete executable handoff, from the repo root:

```sh
ROUND=3 tools/art/anim3d/units/barbarian-crossbowman/gpu.sh
```

It checks all texture inputs and Metal, rebuilds/bakes/retargets/audits, renders
feet and every stage at GPU64/512, retains 512/256 masters, validates provenance,
packs/validates the atlas and encodes/probes the round MP4. Technical completion
never creates visual PASS. Original sources and generated fills remain external
under `~/LegatumRuns/anim-pilot/assets/barbarian-crossbowman/`; the new original
is `stone-fill-source.png`, with exact prompt in `stone-fill.prompt.txt` and hash
in `inputs.json`. Provenance is in `SOURCES.md` and the external shared register.

`origin/master` is already contained. Git staging was denied creating
`.git/worktrees/lane-15/index.lock`; the runner must commit these changes.
Current CPU evidence is preserved in `masters/barbarian-crossbowman/driver-r3-cpu/`.
No fetch, merge, push or PR was performed.
