# Barbarian archer sources

All raw assets and editable masters remain under `~/LegatumRuns/anim-pilot/`.
Scripts are MIT; rendered art is project CC BY 4.0.

- Painting: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/barbarian-archer-source.png — original project CC BY 4.0. Registered to the committed 256 px token; exact hashes in `inputs.json`.
- MPFB 2.0.18: https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18 — GPL software; CC0 anatomy, targets, weights and game-engine rig. MakeHuman CC0 eyes: https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip.
- Generated hidden-side fur/linen/leather/hair fills: original project CC BY 4.0, built-in ImageGen output `01a20670-76eb-7280-89dc-f54424a9d280/exec-a51d4d39-ffaa-4427-96fb-173d9ba6fdb2.png`; no public URL. Original prompt in `painted-fills.prompt.txt`, bytes pinned in `inputs.json`. Reused unchanged.
- Quaternius Universal Animation Library Standard, 2025-06-10: https://quaternius.com/packs/universalanimationlibrary.html — CC0-1.0, existing external `assets/quaternius-ual/LICENSE`. Immutable conversion: https://raw.githubusercontent.com/J-Ponzo/gltf-universal-animation-library/e24c23cf2a1323488a3faa226ea7ea21f644b73e/glTF/AnimationLibrary_Godot_Standard.gltf and adjacent `.bin`. SHA256 glTF `0ff075c7ad6855c5c2c37a171592ee8f0d6ab2f58259e2be77a9b63dd8027765`; bin `6e65377d81558333c4093dbb144a48fd19019343d82b1a3a7992a98ec0e0543c`. Both checked before retarget. Idle_Loop, Walk_Loop, Hit_Chest, Death01; Blender reference/rest and bone-roll compensated world-space constraints. Carrying arms layer open Idle_Loop; only bow attack remains authored. Retarget helper adapted from the project archer lane (MIT). No post-retarget foot rotation correction.
- Existing Blender 5.3.0 https://www.blender.org/ (GPL software), Pillow 13.0.0 https://pypi.org/project/pillow/13.0.0/ (MIT-CMU), FFmpeg. All Blender calls through the PATH gate.

The pelt's death contact folds are modelled shape keys, not a cloth simulation.
No new asset downloads, image generation, accounts or paid services in this pass.
