# Barbarian spearman — driver round 3

Unapproved art candidate. No PASS marker. The incoming round-2 GPU pass succeeded:
196162 bytes at Q80, GPU512/64 masters, all stages and valid eight-second movie.
Its evidence is preserved in masters/barbarian-spearman/driver-r2-gpu/; the old
512 exports are explicitly labelled 512-driver-r2. Current local renders are
CPU256/8 previews, never upscaled and called final GPU masters.

This round replaces the rigid calf/foot overlap with continuous MPFB-weighted
leather, retains anatomical weights and adds smooth pelvis/thigh skirt weighting.
MPFB helper polygons are excluded when extracting the shell. The hand and ash
shaft are fuller; the straight shaft is registered to the painting before UVs
are frozen. Generated clean stone pigment restores grain beneath moving feet,
with live AO and the original rim. A second generated garment/shield pigment
plate removes the faint painted spear only in the narrow occluded band. Both
source plates, derived maps, prompts and licences are pinned and recorded.

Death uses one anatomical reference calibration throughout the body. Sparse glTF
channels reset before sampling; the original CC0 Quaternius idle/walk/hit/death
remain. Equipment releases continuously from the held transform and clears the
support plane. The spear-specific attack remains authored. The scene keeps its
53 bones, 19158-vertex body, real bevels, straps, cloth thickness, generated hidden
fills, eight actual AO/curvature bakes, product lights and one automatic rest LUT.
The cloth deformation is weighted/keyed geometry, not a cloth simulation.

## Verification

- All 40 CPU256/8 samples and every b/c/details/d/e/g review rendered successfully.
- Preview atlas: 181464 bytes, WebP Q80, logical 160px trimmed cells, 8/8/10/4/10
  frames. Independent provenance, offsets, exact alpha reconstruction, bounds,
  actual motion and identical terminal death hold passed.
- Saved-scene audit passed: unchanged body/rig, evaluated sole error below
  0.00001m, horizontal virtual-ground stance error below 0.000001m, retained
  source foot rotations, maximum bone-to-shaft distance 0.0301m, loop closure
  within 0.00001, and released-equipment support clearance. No complete collision
  solver is claimed.
- Decoded-atlas movie: H.264/yuv420p, 1600x348, 240 frames, 8.000 seconds. Actual
  decoded frames, all strips, rest split/crossfade and top/front feet inspected.
- Eighteen Python parses, two Bash syntax checks, ten image-input hashes,
  repeated-grade byte equality and git diff --check passed.
- REQUIRE_GPU=1 correctly rejects this CPU preview. Round-3 GPU execution remains
  lead-side; no final GPU provenance or art approval claimed.

## Visual verdict

At 256px, the base grain, hand, shaft and ankle continuity improve on round 2;
original face/cloth brushwork and overall silhouette remain close. The shoulder
pelt, shield contour and hidden-surface finish still differ, and the death pose
retains conspicuously elevated arms and stiff cloth. At 64px it clearly reads as
the same unit with close scale; it is not interchangeable in motion. Idle/hit
and the thrust are readable; all five clips are not yet artistically clean.
Rest silhouette IoU is .871860 versus the incoming GPU .865384 (alpha >32 at
256px). Different render settings mean this is registration evidence, not an
art-equivalence score. No PASS marker is justified.

## GPU handoff

Run from the repository root:

```sh
ROUND=3 tools/art/anim3d/units/barbarian-spearman/gpu.sh
```

The executable script verifies pinned inputs, regenerates geometry/materials/
clips, performs GPU bakes and every GPU512/64 review stage, exports 512/256
masters, packs/validates the trimmed 160px Q75+ atlas within 200000 bytes, audits
saved scenes and writes barbarian-spearman-round3.mp4. It records the failed stage
on error and never writes PASS automatically. Fresh GPU visual review is required.

Non-obvious learnings are in this unit's PLAYBOOK chapter and external log:
exclude MPFB helper geometry during shell extraction, evaluate skinned soles for
contact, use one anatomical calibration for a fall, and use a generated pigment
underpainting when adjacent source samples retain a weapon ghost. No rules,
runtime integration, docs/learnings, uploads, pushes or PRs are part of this pass.

Git staging/commit was denied by the sandbox at .git/worktrees/lane-1/index.lock.
Changes remain uncommitted for the runner. Requested commit:

```
Refine barbarian spearman footwear, projection and fall

Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>
```
