# Driver round 2 evidence

**Candidate; no PASS.** The lead's prior GPU run succeeded: 40 native GPU512
frames, Q80, 179,574 bytes. That complete evidence is preserved externally in
`masters/barbarian-scout/driver-r1-gpu/`.

This pass fixes trousers accidentally containing hand/finger geometry, refits the
right hand and its bind bones, restores grazing-surface paint, projects stone
grain/rim onto the beveled disc, and adds pinned generated skin/hair/leather fills.
Quaternius CC0 crouch idle/move, hit and death replace the previous authored clips;
only the axe attack remains authored. Kneeling support constrains the retarget.
Contact-driven cape/tunic folds let the fallen body settle on the stone. These
are geometric morphs, not simulated cloth. All six Sam Blender skills were used.

Current CPU evidence (native 256 px, Cycles, 8 samples):

- All 40 frames, 8/8/10/4/10; trimmed 160 px atlas **180,678 bytes, quality 80**.
- Full atlas validation passes: source/clip/grade/frame hashes, uniform settings,
  rectangles/offsets, alpha reconstruction, margins, motion and held death.
- Blender audit passes: 53 bones, anatomy, garment exclusions, open-motion
  provenance, six AO/Pointiness bakes, source freshness, positive object scales,
  stationary base, closed loops and axe grip within 2 mm during the strike.
- Both terminal death frames rendered independently. Root, skeleton, object
  transforms and cloth morphs hold. Final native PNGs are byte-identical. An earlier render differed by four
  one-LSB RGB values; a bounded noise guard now covers that case while preserving
  raw evidence.
- Three delivery regressions pass. Twelve Python scripts parse; three Bash
  scripts pass syntax; whitespace check passes.
- MP4 verified: H.264/yuv420p, 1600x348, 240 frames, 8.000 seconds, all five clips
  at 2x on cream. Its decoded contact sheet, all strips, rest/detail comparisons,
  plain geometry and actual eight-frame top/front feet sheet were opened.

At **256 px**, stone finish, garment correctness and death contact improve, but
hand/finger anatomy, raised-arm/face joins, hair/pelt silhouette and revealed
skin/cloth still differ clearly from the painting. At **64 px**, the same
horn/fur/red-scarf lookout identity reads, but the silhouette/base differ.
The feet sheet exposes excessive sole rotation; the constrained shuffle and axe
attack remain stiff. Death settles but reveals fallback texture seams. These
are not five visually approved clips. No PASS marker is warranted.

`driver-r2-cpu/` preserves current CPU evidence. Previous GPU512 files were moved
out of the live 512 folder so CPU256 cannot masquerade as fresh512. No runtime,
UI or rules code changed; engine tests do not apply. `origin/master` has no
commits ahead of this branch. No push, PR or merge into master.

The executable no-argument handoff rebuilds, audits, renders every stage and
feet on Metal Cycles, checks native GPU512/256 freshness, packs/validates and
writes the decoded-atlas eight-second MP4. This round's script invocation was
cancelled (exit 130) while waiting at the shared device gate, before its probe or
rebuild ran. The earlier sandbox check found no Metal; this round's host GPU
pass remains unverified. Commit was blocked by sandbox `index.lock` permissions;
changes remain on the requested branch for the runner. Lead command:

```sh
ROUND=2 tools/art/anim3d/units/barbarian-scout/gpu.sh
```
