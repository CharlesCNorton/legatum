# Spearman-q CC0 sources

Retrieved 2026-11-24 without an account or payment. Only free Standard editions were downloaded. Each bundled licence explicitly states CC0 1.0 Universal. No upstream semantic version is supplied; itch upload IDs and archive SHA-256 identify the versions.

| Pack | Official page / free download | Version | SHA-256 |
| --- | --- | --- | --- |
| universal-base-characters | https://quaternius.com/packs/universalbasecharacters.html ; https://quaternius.itch.io/universal-base-characters | Standard, itch upload 15861669 | `fdbf1804c90dfc1ea03e992bff7da2dfd1a79318e13270a660180f9308455f40` |
| universal-animation-library | https://quaternius.com/packs/universalanimationlibrary.html ; https://quaternius.itch.io/universal-animation-library | Standard, itch upload 17958403 | `cc73fc4e495b82958207316596317a3f40b9fa38065bde1027937452da537724` |
| universal-animation-library-2 | https://quaternius.com/packs/universalanimationlibrary2.html ; https://quaternius.itch.io/universal-animation-library-2 | Standard, itch upload 17958478 | `4008ea208a604773a2b2177d965f0f5d3195498b5bf838c3f5785d68e95f2a68` |

Licence: https://creativecommons.org/publicdomain/zero/1.0/

## Inputs

- Body and original 65-bone rig: `Superhero_Male_FullBody.gltf` (free pack contains Superhero proportions only). Original mesh, topology, weights and rest bones retained. Two non-deforming prop sockets added.
- Library 1: `UAL1_Standard.glb`, no root motion. Attack `Punch_Cross`; hit `Hit_Chest`; death `Death01`.
- Library 2: `UAL2_Standard.glb`, no root motion. Idle `Idle_Shield_Loop`; walk `Walk_Carry_Loop`.
- Attack is explicitly a punch-derived thrust surrogate, not a native spear stab. Sword_Attack, Sword_Dash, Sword_Regular_A/B/C and Sword_Heavy_Combo were inspected; they swing the spear and lift/sweep the unoccupied shield arm.
- Motion uses rest-space rotation transfer between matching Quaternius rigs, preserving base bone lengths. No hand-authored body poses, IK corrections or body overlays.
- Camera and base geometry: existing project Spearman master, round-15 painting camera (orthographic 2.9, location 2.5/-7/3). Only camera and stone are imported; no old body, clothes, textures or actions.
- Props: original procedural bronze shield, ash shaft and bronze leaf head. No downloaded prop assets.

## Delivery timing

| Clip | Frames | Game fps | Notes |
| --- | ---: | ---: | --- |
| attack | 16 | 14 | Full Punch_Cross including recovery, 1.143 seconds |
| idle | 12 | 4 | Full shield idle cycle, 3 seconds |
| walk | 12 | 6 | Full carry walk, 2 seconds, original duration |
| hit | 8 | 12 | Original chest reaction then held tail, 0.667 seconds |
| death | 14 | 4 | Original 2.4-second collapse then settled hold |

All video frames are shown in order, repeated exactly three times; no interpolated video frames. The game rates come from `kit/atlas.py::CLIPS` (walk uses move). The requested larger counts replace the old counts only in these review outputs.

Heavy source archives, licence files and receipt: `~/LegatumRuns/anim-pilot/assets/spearman-q/`. Editable clips: `~/LegatumRuns/anim-pilot/lanes/spearman-q/masters/`.
