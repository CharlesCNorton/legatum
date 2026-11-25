# Painted premium inputs (rounds 1 and 2)

- Approved round-six `spearman.glb`, from commit `5199b147` on the 0 A.D. lane.
  SHA-256: `84bf794f543fd4a1af2d1b9c2b48c89a6c52533a00d7803e553b49a22513f92c`.
  Preserved at `$ANIM_ROOT/lanes/spearman-0ad-painted-r1/approved-r6.glb`.
  The upstream Wildfire Games attribution and CC BY-SA 3.0 apply to this derived
  asset; exact upstream paths and hashes remain in PROVENANCE.md and source-manifest.json.
- Art direction only: `app/src/assets/units/spearman-panel.png` and
  `spearman-256.png`. No projected source-image pixels are in the new textures.
- Studio Small 09, Sergej Majboroda / Poly Haven, CC0:
  https://polyhaven.com/a/studio_small_09 ; https://polyhaven.com/license .
  Exact download and SHA-256 are in `../../viewer/SOURCES.md`.
- New geometry, authored pigment graphs, bevels, subdivision, noise displacement,
  Cycles normal/AO bakes and ORM packing were produced in Blender 5.3.0.
  No paid tools, Mixamo, Meshy, Higgsfield or new animation donors.

Round 2 reuses the locally installed MakeHuman/MPFB 2.0.18 body asset (CC0):
https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18 .
Archive `$ANIM_ROOT/assets/mpfb2-v2.0.18.zip` SHA-256:
`ada7c4ff11e79cf6ed9b441bccabc52c9359f2848b988f66e89c14c30b21fed7`.
`src/mpfb/data/3dobjs/base.obj` SHA-256 (also matches installed base):
`8e761e6624b8f54536409135d1636da63b32486a90d4897f84e121d144f6fb4c`.
The asset licence is copied verbatim as LICENSE-MPFB from LICENSE.ASSETS.md.
MPFB program code is not redistributed; its CC0 generated body is fitted and
skinned to the unchanged 0 A.D. skeleton. The combined derivative retains the
Wildfire Games CC BY-SA 3.0 credit and licence.

The approved GLB is also preserved in
`$ANIM_ROOT/lanes/spearman-0ad-painted-r2/approved-r6.glb`; the round-two
master, 2048 bakes and review frames are stored alongside it. Both lanes'
round-one review images informed the shield contrast and value separation;
no PBR-lane geometry, textures or motion were copied.
