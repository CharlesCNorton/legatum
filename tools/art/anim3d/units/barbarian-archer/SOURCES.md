# Barbarian archer sources

All raw assets and editable masters remain under `~/LegatumRuns/anim-pilot/`.
Scripts are MIT; rendered art is project CC BY 4.0.

- Painting: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/barbarian-archer-source.png — original project CC BY 4.0. Registered to the committed 256 px token; exact hashes in `inputs.json`.
- MPFB 2.0.18: https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18 — GPL software; CC0 anatomy, targets, weights and game-engine rig. MakeHuman CC0 eyes: https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip.
- Generated hidden-side fur/linen/leather/hair fills: original project CC BY 4.0, built-in ImageGen output `01a20670-76eb-7280-89dc-f54424a9d280/exec-a51d4d39-ffaa-4427-96fb-173d9ba6fdb2.png`; no public URL. Original prompt in `painted-fills.prompt.txt`, bytes pinned in `inputs.json`. Reused unchanged.
- Quaternius Universal Animation Library Standard, 2025-06-10: https://quaternius.com/packs/universalanimationlibrary.html — CC0-1.0, existing external `assets/quaternius-ual/LICENSE`. Immutable conversion: https://raw.githubusercontent.com/J-Ponzo/gltf-universal-animation-library/e24c23cf2a1323488a3faa226ea7ea21f644b73e/glTF/AnimationLibrary_Godot_Standard.gltf and adjacent `.bin`. SHA256 glTF `0ff075c7ad6855c5c2c37a171592ee8f0d6ab2f58259e2be77a9b63dd8027765`; bin `6e65377d81558333c4093dbb144a48fd19019343d82b1a3a7992a98ec0e0543c`. Both checked before retarget. Idle_Loop, Walk_Loop, Hit_Chest, Death01; Blender reference/rest and bone-roll compensated world-space constraints. Carrying arms layer open Idle_Loop; only bow attack remains authored. Retarget helper adapted from the project archer lane (MIT). No post-retarget foot rotation correction.
- Existing Blender 5.3.0 https://www.blender.org/ (GPL software), Pillow 13.0.0 https://pypi.org/project/pillow/13.0.0/ (MIT-CMU), FFmpeg. All Blender calls through the PATH gate.

The pelt's death contact folds are modelled shape keys, not a cloth simulation.
No new third-party downloads, accounts or paid services.

## Driver round 3

- Clean stone occlusion fill: built-in ImageGen, 2026-11-23, output `01a20a9e-e6b9-7a80-b945-89b296c24d9b/exec-4c29349d-bdc2-425f-92df-5c9ef0562cf8.png`, original project CC BY 4.0; no public URL. Input: the pinned registered painting. External `assets/barbarian-archer/stone-fill-source.png`; exact prompt `stone-fill.prompt.txt`. Derived `stone-pigment.png` registers the clean disc and retains the original lower rim. Both SHA256 values in `inputs.json`. Pigment on closed geometry with live contact AO, no image card.
- Closed weighted leather toe boxes, semantic garment filtering, stone shader and source preflight are original MIT scripts; rendered art CC BY 4.0. Existing MPFB/Quaternius and generated hidden-side fills reused. Previous GPU evidence preserved under `masters/barbarian-archer/driver-r2-gpu/`.
