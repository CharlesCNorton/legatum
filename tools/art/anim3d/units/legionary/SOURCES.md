# Legionary sources

All raw assets and masters are external under `~/LegatumRuns/anim-pilot/`.
`assets.lock.json` pins painting and generated fills; `retarget.py` verifies both
motion files before import. No commercial animation or character service is used.

| Asset | Source / version | Licence |
| --- | --- | --- |
| Legionary painting | [Project master](https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/legionary-source.png), existing 1254px master | Project CC BY 4.0 |
| MPFB anatomy, weights, game_engine rig, eyes | [MPFB 2.0.18](https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18), existing MakeHuman system assets | CC0 assets; GPL software |
| Painted iron, bronze, cloth, leather | Original built-in imagegen `01a2066e-ff83-7250-bec6-14c5f46f1f73/exec-d6de0de4-bc9d-4927-be04-fbc6b4bbe7e4`; `painted-fills.prompt.txt` | Project CC BY 4.0 |
| Painted hidden skin fill | Original Medjay imagegen `01a20671-5037-7490-a90a-decacb274446/exec-401b9b3e-9eef-48db-b965-0d53769ebddc`, reused unchanged from `assets/medjay/fill-skin.png` | Project CC BY 4.0 |
| Idle_Loop, Walk_Loop, Hit_Chest, Death01 | [Quaternius Universal Animation Library Standard](https://quaternius.com/packs/universalanimationlibrary.html), 2025-06-10 | CC0 1.0; retained `assets/quaternius-ual/LICENSE` |
| glTF conversion | [Immutable mirror](https://raw.githubusercontent.com/J-Ponzo/gltf-universal-animation-library/e24c23cf2a1323488a3faa226ea7ea21f644b73e/glTF/AnimationLibrary_Godot_Standard.gltf), adjacent `.bin` | Same CC0 assets |

Motion SHA256: glTF `0ff075c7ad6855c5c2c37a171592ee8f0d6ab2f58259e2be77a9b63dd8027765`;
buffer `6e65377d81558333c4093dbb144a48fd19019343d82b1a3a7992a98ec0e0543c`.

The Blender constraint retarget implementation is adapted from the project's
infantry lane (MIT), with source rest/reference and bone-roll calibration.
Walking uses the open idle's carrying-arm layer. Shield attack, equipment release,
cloth-hem follow-through and ground translations are original. Foot rotations
come from the calibrated source; there is no post-retarget orientation patch.
No source mannequin is rendered. Original scripts MIT; rendered art CC BY 4.0.
