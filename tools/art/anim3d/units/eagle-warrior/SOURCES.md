# Eagle warrior animation inputs

- Original project painting: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/eagle-warrior-source.png — CC BY 4.0. Original generated feather fill: built-in ImageGen output `01a2068d-febe-7ea0-b5e1-8771effc912e/exec-e9a5d7b5-583d-4010-ae69-3ec2d3297d31.png`, 2026-11-22, CC BY 4.0; prompt `fills.prompt.txt`. Both already installed; hashes in `assets.lock.json`.
- MPFB 2.0.18: https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18 — GPL software, CC0 anatomy, rig, weights and MakeHuman system eyes. Existing installation.
- Quaternius Universal Animation Library Standard (2025-06-10): https://quaternius.com/packs/universalanimationlibrary.html — CC0-1.0. Existing immutable mirror: https://raw.githubusercontent.com/J-Ponzo/gltf-universal-animation-library/e24c23cf2a1323488a3faa226ea7ea21f644b73e/glTF/AnimationLibrary_Godot_Standard.gltf and adjacent `.bin`; local `assets/quaternius-ual/LICENSE`.

Motion hashes, checked before import:

| File | SHA256 |
| --- | --- |
| AnimationLibrary_Godot_Standard.gltf | 0ff075c7ad6855c5c2c37a171592ee8f0d6ab2f58259e2be77a9b63dd8027765 |
| AnimationLibrary_Godot_Standard.bin | 6e65377d81558333c4093dbb144a48fd19019343d82b1a3a7992a98ec0e0543c |
| LICENSE | a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499 |

Idle_Loop, Walk_Loop, Hit_Chest and Death01 are retargeted with Blender world rotation constraints and source/target rest/reference offsets including roll. Walk arms carry the weapons with the library idle layered through NLA. Only the macuahuitl attack and rigid weapon release are authored. No post-retarget foot-rotation correction, cloth simulation, paid service or new download. Unit-local retarget and feet helpers adapted from inspected crossbowman lane scripts (MIT). Original geometry/material scripts MIT; rendered art CC BY 4.0.
