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
- The first round used rest-space rotation transfer alone. Round 2 retains it beneath the corrections documented below.
- Camera and base: existing project Spearman master, round-15 painting camera (orthographic 2.9, location 2.5/-7/3). Round 2 enlarges the fixed stone to contain the fall.
- Round 1 props: procedural bronze shield, ash shaft and bronze leaf head. Round 2 replaces the shield surface with the project's existing rigid aspis and sunburst. No downloaded prop assets.

## Round 2 adaptation

The Quaternius sources above remain the motion sources. Their full body,
weights and 65 rest bones are preserved. `Punch_Cross` supplies torso and leg
motion; a two-bone IK correction gives the right hand a straight 39 cm spear
thrust. Left-arm guard, transition blends, floor seating and death centring
are layered corrections. The death sockets release their rigid equipment
and follow continuous paths to separate ground positions.

The prior-art survey on `astra/unit-anim-3d-prior-art` was read. Its recommended
KayKit Free 1.1 `Melee_1H_Attack_Stab` was inspected from the existing locally
licensed CC0 archive; its low wrist path was not adopted. No new motion pack,
paid tier, account-dependent download or non-CC0 animation is used.

The project-owned painting and armour come from the existing Spearman kit.
Only costume geometry and frozen per-part painting coordinates/pigment are
ported; the MPFB body and its animations are discarded. The frozen source
master SHA-256 is
`2754033f1fbfb0679c25df9d0a2f3efa337234a171b7046a583ef781431a02f5`.
All 41 local input hashes are in `input-sources.json`.

## Round 2 timing

| Clip | Frames | Game fps | Notes |
| --- | ---: | ---: | --- |
| attack | 18 | 14 | Anticipation, fast extension, short hold, slower recovery |
| idle | 12 | 4 | Complete shield-idle cycle; shared weapon guard |
| walk | 16 | 8 | Complete 2-second carry-walk cycle; shared arm layer |
| hit | 8 | 12 | Chest recoil with a return to guard |
| death | 16 | 8 | Trimmed active collapse, three held final samples |

The exported atlas has 70 records. All video samples repeat exactly three
times with no interpolation. Source samples are listed in each frame receipt.
Heavy assets stay under `~/LegatumRuns/anim-pilot/`; nothing replaces the
shipping Spearman image or atlas.
