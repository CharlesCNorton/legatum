# Round 2 evidence

Candidate only; **no PASS marker**. Refit the actual MPFB bind meshes and 53-bone
skeleton, finish static surfaces before frozen camera UVs, correct the axe normals
and its clearance from the shirt, fit the saluting hand, widen the rear pelt,
add visibility/source-object masks, and retain generated fur/linen fills. Six
real AO/Pointiness bakes, modeled cloth/straps/hair, product lights and one fixed
automatic histogram grade remain. Camera-only pigment prevents painted lighting
from illuminating other surfaces. No runtime or rules code changed.

Final CPU evidence, native 256 px / Cycles / 8 samples:

- All 40 frames, counts 8/8/10/4/10. Trimmed 160 px atlas **172,840 bytes at Q80**.
- Atlas validation passes: offsets, bounds, exact decoded quantized alpha,
  source/clip/grade/frame hashes, uniform render settings, actual motion and held
  death. Quality stays at least 75; the size cap remains 200,000 bytes.
- Blender audit passes: anatomy, 53 bones, bakes, source freshness, positive scale,
  stationary base, closed idle/move endpoints, held death, and axe grip within
  2 mm of the palm during striking frames. Major-limb lengths remain between
  0.916 and 1.179 times their input lengths; local fitting residual is 0.54 px.
  These checks do not establish collision-free motion or painting parity.
- Three delivery regression tests pass. Ten Python files parse; three shell
  scripts pass Bash syntax; `git diff --check` passes.
- Decoded-atlas MP4 verified: **8.000 seconds, 240 frames, 1600x348,
  H.264/yuv420p**, five clips side by side at 2x on cream. Reviewed its contact
  sheet, all clip strips, plain views, detail sheet, and rest comparisons.

At 256 px the painting is still substantially richer. The broad crouch, face
registration and equipment placement improved, but hand/brow anatomy,
hand-to-cloth joins, exposed fill seams, knee/boot contact, and flat stone finish
remain wrong. At 64 px the fur/horn/scarf/lookout identity reads; it is still
clearly distinguishable. Move and attack remain restrained/stiff. Death reveals
paint/fill seams and needs better choreography. **Five generated clips are not
five visually approved clips.**

Important findings: per-vertex floor fitting stretched feet, and a calf-only
correction stretched the torso. Both were rejected after side-view inspection;
shared full-figure depth translations preserve proportions. Visibility masking
revealed a buried axe that source paint on the shirt had been concealing. Fix the
actual support geometry before preserving a flattering projected silhouette.

`gpu.sh` is executable and resolves its checkout. Missing-input preflight and
actual device preflight both fail with recorded stages. Running the real script
in the sandbox exits 1 at `gpu-device`: **No Metal GPU; refusing CPU fallback**.
The complete host pass is therefore still unverified here. It rebuilds, audits,
renders every stage at GPU512, verifies native 512/256 masters, tests delivery,
packs/validates and writes `barbarian-scout-round${ROUND}.mp4`. Run from this
branch's checkout:

```sh
ROUND=2 tools/art/anim3d/units/barbarian-scout/gpu.sh
```

CPU previews cannot manufacture 512 px masters. Prior native CPU512 evidence is
preserved in `masters/barbarian-scout/round1-cpu/`; current round-two CPU evidence
is in `round2-cpu/`. Fresh GPU512 masters remain pending.

The repository art gate could not run: Playwright Chromium failed its macOS
MachPortRendezvous bootstrap check in the sandbox. The lead still owes the host
browser/art gate and visual review. The fetched `origin/master` is already an
ancestor of this branch, so no merge or determinism re-run was needed.

The supplied lane-21 was on crossbowman and denied branch switching. It remains
unchanged. Scout work resumed from c9464430 in the Git-managed
`.worktrees/barbarian-scout-round2` checkout on the requested scout branch.
