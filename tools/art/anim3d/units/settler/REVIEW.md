# Settler round 1

This is a true 3D **review candidate**, not a claim of painting parity or runtime
adoption. The static painting remains in the game. The lead owns GPU and final
art review.

The female MPFB anatomy and 53-bone rig wear complete folded garments, an open
hood, shawl/fringe, straps, a pack/spiral blanket and sandals, and hold a real staff.
Materials combine painting projection on frozen rest-camera UVs, generated fills
for unseen cloth/leather, fine bump, and ten actual AO/curvature bakes. The base
is a single stationary cream disc. Garment folds/hem follow-through are authored;
there is no claim of simulated cloth or captured motion. Covered upper-leg faces
are masked non-destructively beneath the opaque robe to avoid stride poke-through.

At **256 px**, the painting is still richer and more convincing. Remaining gaps:
face/head direction and hood fit, rounded horizontal shawl folds, insufficiently
organic diagonal robe drape, straighter/narrower posture, small equipment detail,
and projection seams on moving/newly exposed surfaces. At **64 px**, the hood,
staff, cream/olive/rust clothing and bedroll identify the settler, but the more
upright stance is visibly different. The rest crossfade exposes that mismatch.
Do not substitute a contract/audit pass for the art verdict.

External evidence lives under `~/LegatumRuns/anim-pilot/`:

- `review/3d-v2/settler-{b-plain,c-textured-lit,c-details,d-rig-poses}.png`
- `review/3d-v2/settler-f-restpose-compare.png` (256/64, half split and crossfade)
- `review/3d-v2/settler-e-{idle,move,attack,hit,death}-strip.png` and matching WebPs
- `review/3d-v2/settler-atlas-decoded.png` and `settler-log.md`
- `masters/settler/`: editable masters, ten bakes, source/render/grade/pack/audit
  manifests, and 40 frames each at 512 and 256 px. Raw frames remain ungraded.

The attack is a restrained defensive staff check, not a warrior attack. Its zero
weight pose preserves the original elbow pole/hand orientation. Move keeps the
feet level and staff upright. Death folds sideways, releases the staff and holds
the final geometry for two samples. Ground and camera bounds are audited; there
is no exhaustive skin/cloth collision solver.

All Blender runs use the PATH gate. To rerender the saved masters on the host:

```sh
UNIT=settler RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64 tools/art/anim3d/render.sh final
UNIT=settler tools/art/anim3d/render.sh pack
UNIT=settler tools/art/anim3d/render.sh validate
```

The full method and the version-2 160 px trim-offset schema are documented in the
settler chapter of `../../PLAYBOOK.md`. `rebuild` reconstructs the complete chain;
`final` preserves the model and animations. Generated hidden-fill prompt and
provenance are checked in; source assets and masters stay outside git.
