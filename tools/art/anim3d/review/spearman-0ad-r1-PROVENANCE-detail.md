# Local 0 A.D. hoplite provenance

LOCAL REVIEW ONLY. Sam has not approved these assets for the public Legatum repository. No uploads, GitHub writes, commits, or repository file changes were made.

## Attribution and licence

0 A.D. art by **Wildfire Games and the 0 A.D. art contributors**. Original project: https://wildfiregames.com/ and https://play0ad.com/. Art licence: **CC BY-SA 3.0**, https://creativecommons.org/licenses/by-sa/3.0/. Imported actor and derived renders remain CC BY-SA 3.0.

Pinned source commit: `61a3b9507d974084e6badb88a0826bd89a6d5b8b`. Sparse raw-file downloads only; no repository clone.

Author/credit records retained: `src/binaries/data/mods/public/gui/credits/texts/art.json`, root `src/LICENSE.txt`, and `src/binaries/data/mods/public/art/LICENSE.txt`. The art JSON is the project contributor roster; individual per-mesh authorship is not inferred. COLLADA contributor metadata is preserved in every downloaded DAE.

The four files under `src/source/collada/` were read to verify coordinate and prop conventions. They are GPL-2.0-or-later engine code, not CC BY-SA art. No upstream executable code was run or copied into the converter.

## Assembly and modifications

Selected `actors/units/athenians/infantry_spearman_b.xml`. Native tunic body and skin weights; Greek head; Pilos helmet; aspis front, bronze back and handgrip; hoplite spear. No textures downloaded; materials replaced with plain linen, skin, bronze and wood colours. UVs preserved.

Attachments: body rig -> `head` -> `prop-head` -> head; `helmet` -> `prop-helmet` -> helmet; `forearm_L` -> `shield_arm` -> `prop-shield_arm` -> aspis; `hand_R` -> `weapon_R` -> `prop-weapon_R` -> spear. Source prop transforms and mesh-node transforms preserved. Blender bone-tail origin is compensated. Nested aspis handgrip uses its native `prop-handgrip` transform. Props are rigid; no per-clip socket changes.

Source clips imported: `attack_melee_04`, `attack_melee_05`, `idle_relax_01`, `walk_relax`, `death_a`, `death_b`. Source timestamps normalized; exact sampled local matrices reconstructed, no retargeting. `procedural_hit` is a new 0.8-second additive torso/neck recoil over the native idle pose.

Fixed actor scale 0.40 and translation (0,0,0.10) for all final reviews. Camera unchanged from `astra/unit-anim-3d-v2:tools/art/anim3d/kit/presets/spearman.json`: location (2.5,-7,3), target (0,0,1.2), orthographic scale 2.9. Source reference stored as `camera-reference.json`.

Blender 5.3 through the PATH gate, background/factory startup/autoexec disabled, 3 threads, requested via nice. Sandbox reports that nice cannot change priority; renders were short CPU previews. COLLADA operator absent. Official portable Blender 4.5.9 downloaded and hash verified, but disk-image mounting was refused. Therefore `import_hoplite.py` is a small local source-available matrix/skin COLLADA converter using Blender and Python XML; triangles and polylists supported. All file parsing is data-only.

`hoplite.blend` contains the studio, holdout ground, actor and all seven actions. `hoplite.gltf` + `hoplite.bin` contain only the actor and all seven actions, with all skin influences preserved. The camera-only review ground occludes below-ground portions; there is no prop release or collision correction.

Final MP4s: H.264, yuv420p, 160x160, cream #f8f4e8, three repeats. Game rates: attack 14, walk 6, death 4, hit 12, idle 4 fps. Uniform source sampling with duration rounded to whole game frames; loops omit duplicated endpoints. Full-rate PNG contact strips retain every native source sample (attack 36 at 30Hz; walk 41 at 30Hz; death B 47 at 24Hz). Actor XML runtime speed multipliers are not applied; these are source-time motion reviews, not a claim of matching 0 A.D. gameplay playback.

Death B selected; death A retained in editable exports but rejected for the main review because the fall extends beyond the fixed camera. Attack 04 selected; attack 05 also retained.

## Download inventory

Every retained upstream source file is listed below with its exact URL and SHA-256.

| Local path | Source URL | SHA-256 |
| --- | --- | --- |
| `src/LICENSE.txt` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/LICENSE.txt | `cb9eb5e8768328e8086b0d17bd1b95f07b51bc9ab74fa1b509ee09c7894b2f53` |
| `src/binaries/data/mods/public/art/LICENSE.txt` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/LICENSE.txt | `ef98babd771c206032e005f3d440a1e610df409d9a9191f03e64deaa4abefbd9` |
| `src/binaries/data/mods/public/art/actors/props/units/heads/new/head_hele_b.xml` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/actors/props/units/heads/new/head_hele_b.xml | `4956b46a80ad1ab4fcebd05ac361fad08887c25565681bca29f92a757b3e28a0` |
| `src/binaries/data/mods/public/art/actors/props/units/helmets/hele_pilos.xml` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/actors/props/units/helmets/hele_pilos.xml | `7735e8dd491bd397b5e4db075374ac412258bc52b45d62d3cb03b7b19276e372` |
| `src/binaries/data/mods/public/art/actors/props/units/shields/aspis_athen_b.xml` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/actors/props/units/shields/aspis_athen_b.xml | `383bced5ae6036d3655563ff2a5951765d8cb3c7f85ebd4b0477c4752db2fba5` |
| `src/binaries/data/mods/public/art/actors/props/units/shields/props/aspis_back_bronze_01.xml` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/actors/props/units/shields/props/aspis_back_bronze_01.xml | `32a47276717dfffefb8a12a6d84c96524bddc858900a8516a0f720a033a80503` |
| `src/binaries/data/mods/public/art/actors/props/units/shields/props/aspis_handgrip_bronze_01.xml` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/actors/props/units/shields/props/aspis_handgrip_bronze_01.xml | `97b09e194338b7819c744c5fd6670c2bf58d6a7a6e3c2978791153b4e638c97a` |
| `src/binaries/data/mods/public/art/actors/props/units/weapons/spear_hoplite.xml` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/actors/props/units/weapons/spear_hoplite.xml | `f8210a6fcdd623180b60dd94608b684cffc64af481689b7409bd6c66ed2deb0f` |
| `src/binaries/data/mods/public/art/actors/units/athenians/infantry_spearman_b.xml` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/actors/units/athenians/infantry_spearman_b.xml | `0c69b560640e603bf48a1ada8a82637306690b82fc7dcfca869240ed43e74718` |
| `src/binaries/data/mods/public/art/animation/biped/infantry/death_a.dae` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/animation/biped/infantry/death_a.dae | `78802e0531e0881c38ffa28fb6b281ea18edcd8c95f3acfa2a883e287f1f8df4` |
| `src/binaries/data/mods/public/art/animation/biped/infantry/death_b.dae` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/animation/biped/infantry/death_b.dae | `46793fd672b98bdd301b4e4fe9607634d2b05a639b6651cea50419497b1eda9d` |
| `src/binaries/data/mods/public/art/animation/biped/infantry/hoplite/attack_melee_04.dae` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/animation/biped/infantry/hoplite/attack_melee_04.dae | `b8bf6b300fbd0b60950706de9b7348a8f5d74f2125277b92700a98bf4e5ba4ca` |
| `src/binaries/data/mods/public/art/animation/biped/infantry/hoplite/attack_melee_05.dae` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/animation/biped/infantry/hoplite/attack_melee_05.dae | `daaf7edad547587c6527e0ae613af2d49af5d0d13baa6fadfa0ceb96aa0f4319` |
| `src/binaries/data/mods/public/art/animation/biped/infantry/hoplite/idle_relax_01.dae` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/animation/biped/infantry/hoplite/idle_relax_01.dae | `d3d24e10285d95c7fbce3ccffe078447e24604e3a091087bf63b5b5f7eb53f32` |
| `src/binaries/data/mods/public/art/animation/biped/infantry/hoplite/walk_relax.dae` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/animation/biped/infantry/hoplite/walk_relax.dae | `2386226422203d277cac7c35fda725e60365471d23f32962f9f277b3e43c09a7` |
| `src/binaries/data/mods/public/art/meshes/props/helmet/hele_pilos_a1.dae` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/meshes/props/helmet/hele_pilos_a1.dae | `0ba87320e84f1188be12486016f8b2fef6981e362d29d8d392669ed1876e24a7` |
| `src/binaries/data/mods/public/art/meshes/props/new/dude_head.dae` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/meshes/props/new/dude_head.dae | `cd9b853b175feb8d89ada520ca5079edfa2de8e9aa20292c1d0ad3366740795e` |
| `src/binaries/data/mods/public/art/meshes/props/shield/aspis_01_back.dae` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/meshes/props/shield/aspis_01_back.dae | `a71d5714a6683093118dc1cbc142eec7439736609b85cae23082350dfe9d97f4` |
| `src/binaries/data/mods/public/art/meshes/props/shield/aspis_01_front.dae` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/meshes/props/shield/aspis_01_front.dae | `85e7d300af2072da5f69a3ff17de83609025f2031d49256e7004b51378cf19f1` |
| `src/binaries/data/mods/public/art/meshes/props/shield/props/aspis_handgrip_01.dae` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/meshes/props/shield/props/aspis_handgrip_01.dae | `a13ce210ea3672409745cdc7f6bf2d1efb6b35447100ad656b037f08a73ef9aa` |
| `src/binaries/data/mods/public/art/meshes/props/spear_hoplite.dae` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/meshes/props/spear_hoplite.dae | `14c44f11ea2a33cd6cec8311125b3dc6013480e029f5e271ebbc0159bd8eb8fd` |
| `src/binaries/data/mods/public/art/meshes/skeletal/new/m_tunic_short.dae` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/meshes/skeletal/new/m_tunic_short.dae | `749666d1046f4a0f2b3f42fed0715ecc3bd5a00a8514acfb521a0b3dd3e93e98` |
| `src/binaries/data/mods/public/art/skeletons/biped.xml` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/skeletons/biped.xml | `5363c95083f0ce520e239be9405dde4a16f8247550de54e8bc99e262e0de6273` |
| `src/binaries/data/mods/public/art/variants/biped/base_hoplite.xml` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/variants/biped/base_hoplite.xml | `a7fc5470e9a0945220e796c9c58f7af45900a04ad92cd176135cad84263fd65c` |
| `src/binaries/data/mods/public/art/variants/biped/death_infantry.xml` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/variants/biped/death_infantry.xml | `711eb6a9a21647f2142e0ee90b291c2841c1df5461f0d49169a5632cb3167387` |
| `src/binaries/data/mods/public/art/variants/shields/aspis_base_01.xml` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/variants/shields/aspis_base_01.xml | `db9fe3c00da14ad058e87c18c8f94019da7b5517ec7503d52af744fd067b9eb8` |
| `src/binaries/data/mods/public/art/variants/shields/aspis_handgrip_bronze_01.xml` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/variants/shields/aspis_handgrip_bronze_01.xml | `8459b72a2482daca68823467b6316fe1f61b0686456cc304cd9a79e5ba8a0412` |
| `src/binaries/data/mods/public/art/variants/shields/athen_aspis_basic_01.xml` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/variants/shields/athen_aspis_basic_01.xml | `c763f09bfc30499d29c0e12c443d3dced38a6d0c883aae383b0599db563dc543` |
| `src/binaries/data/mods/public/gui/credits/texts/art.json` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/gui/credits/texts/art.json | `4b18678a37df7ca7db7ca2c31a5a89172efd846fd7170c3ea43843e362820242` |
| `src/source/collada/CommonConvert.cpp` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/source/collada/CommonConvert.cpp | `a909dcb614b421536b18ad112fc2bee1eae3ba81d197a77650f634bf0b3c2d12` |
| `src/source/collada/CommonConvert.h` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/source/collada/CommonConvert.h | `6aeeba1cdae9164517170fd6c6563ac6592868f0a6d5b5ff9d11ec8c9983e864` |
| `src/source/collada/Maths.h` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/source/collada/Maths.h | `0e12a29fd9e251ce38531052f11834d196853cea34694b8073153733b5962cc9` |
| `src/source/collada/PMDConvert.cpp` | https://raw.githubusercontent.com/0ad/0ad/61a3b9507d974084e6badb88a0826bd89a6d5b8b/source/collada/PMDConvert.cpp | `81d401da9b0061f7d6cd23c0b225a59f3b25fc9032eec026c3eadbf0cfd7c347` |
| `blender-4.5.9-macos-arm64.dmg` | https://download.blender.org/release/Blender4.5/blender-4.5.9-macos-arm64.dmg | `e3a3d7aac381fb4e4d05197f99cd8899484d7e8bc4497c134066e6733f372238` |
| `blender-4.5.9.sha256` | https://download.blender.org/release/Blender4.5/blender-4.5.9.sha256 | `fadc7ef868751ab836a3792f68f95eb954042626b206cca8d9b20723eb88756b` |
