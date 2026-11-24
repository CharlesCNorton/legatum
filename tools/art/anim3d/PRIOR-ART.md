# Prior art: a moving, painted hoplite

Research date: 2026-11-24. Scope: free rigs, combat motion and Blender sprite baking; no asset adoption or animation implementation. This survey stays within a one-hour research budget.

**There is strong prior art.** 0 A.D. already assembles and animates Greek spear-and-shield infantry. Quaternius and KayKit supply reusable CC0 game rigs and substantial motion libraries. We should approve motion on one of these rigs before fitting the painted character to it.

**Best CC0 starting point:** the specifically CC0-licensed Quaternius Universal Base Characters Standard archive, with Universal Animation Library 1 for idle, walking, hit and death. KayKit supplies an actual one-handed stab donor. An overhand spear thrust with a steady shield still needs adaptation and visual approval; none of the inspected CC0 sets establishes a complete, unchanged hoplite solution.

**Best historical starting point:** 0 A.D.'s native hoplite body, Biped skeleton, weapon and forearm-shield attachments, and `attack_melee_04/05`. This has much stronger evidence for the intended combat stance, at the cost of CC BY-SA obligations. Its selected hoplite actor does not supply a hit reaction.

## What was verified

- Read official asset pages and licences; downloaded the free Quaternius, KayKit and Kenney archives into memory and inspected their contents. No third-party assets or tools were added to this repository.
- Parsed animation names, time accessors and rig nodes in the actual GLB/glTF files. Inspected 0 A.D. actor XML, skeleton XML and COLLADA animation data at a pinned revision.
- Read sprite-baker source and licences. Did not execute those projects, import rigs in Blender, retarget motion, or render an approval movie. Quality assessments below distinguish shipped-game evidence from fit-for-Legatum inferences.
- Mixamo's anonymous catalog requests returned HTTP 403, and browser access was unavailable. Its inventory below is a documented historical subset, **not a verified current exhaustive catalog**. No Adobe account was used.

**Counts:** where a table says “samples,” these are measured source keyframe samples, including the endpoint, not a publisher's advertised frame count or our future atlas frame count. For the inspected Quaternius and KayKit tracks, 49 samples span 48 intervals at 30 Hz, or 1.6 seconds. Counts use the largest input accessor in each action. A one-sample pose is not an animated death. Export sampling, looping and sprite playback rate remain separate choices.

## CC0 sources

### Quaternius: compatible adult bodies and motion

Primary sources: [Universal Base Characters](https://quaternius.com/packs/universalbasecharacters.html), [UBC downloads](https://quaternius.itch.io/universal-base-characters), [Universal Animation Library 1](https://quaternius.itch.io/universal-animation-library), [Universal Animation Library 2](https://quaternius.itch.io/universal-animation-library-2), and the [official animation viewer](https://quaternius.com/animviewer.html).

The free **Standard** downloads are materially smaller than the full advertised libraries. Both inspected animation GLBs contain 43 named actions, including `A_TPose`: 42 motion actions each. The full libraries and editable animation source are paid tiers. Do not equate a page's “120+” or “130+” headline with its free archive.

| Pack | Verified free contents and suitability | Prop attachment |
| --- | --- | --- |
| Universal Base Characters Standard | Male and female **Superhero** full bodies; the inspected male glTF has 65 skin joints and no animations. The advertised Regular/Teen bodies are not in this free archive. Adult proportions are a more useful starting point than a chibi character, though the superhero silhouette needs adjustment. | `hand_r`, `hand_l`, `lowerarm_r`, `lowerarm_l` exist. No dedicated spear/shield sockets were found. Add nondeforming children for spear and shield; these would be our additions. |
| UAL1 Standard | Compatible mannequin animation in GLB and FBX, plus root-motion exports. Provides the four basic motions needed before the attack. | Same named hand/forearm hierarchy; rigid spear parented to right hand, aspis attached to left forearm with grip alignment. |
| UAL2 Standard | Adds shield poses/actions, a sword block and more melee. Useful for stance references and reactions; it does not add a named spear thrust. | Same attachment approach. A shield-labelled clip does not itself supply the correct Greek shield mesh, strap or grip. |

#### UAL1: relevant free actions

Measured from `Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb`.

| Category | Exact action | Samples | Span, seconds |
| --- | --- | ---: | ---: |
| Neutral idle | `Idle_Loop` | 76 | 2.500 |
| Armed idle | `Sword_Idle` | 51 | 1.667 |
| Walk | `Walk_Loop` | 41 | 1.333 |
| Walk variant | `Walk_Formal_Loop` | 41 | 1.333 |
| Jog / sprint | `Jog_Fwd_Loop` / `Sprint_Loop` | 29 / 21 | 0.933 / 0.667 |
| Sword melee | `Sword_Attack` | 47 | 1.533 |
| Unarmed melee | `Punch_Cross` / `Punch_Jab` | 31 / 27 | 1.000 / 0.867 |
| Hit | `Hit_Chest` / `Hit_Head` | 11 / 14 | 0.333 / 0.433 |
| Death | `Death01` | 73 | 2.400 |
| Spear, thrust/stab, shield or block | No explicitly named action in this free file | — | — |

The full official preview additionally names `Death02`, `Hit_Shoulder_L`, `Hit_Shoulder_R`, `Hit_Stomach`, `Kick`, `PunchKick_Enter`, `PunchKick_Exit`, `Sword_Enter`, `Sword_Exit`, `Sword_Attack_Standing` and `Sword_Attack_RM`. These are **not promises about the free download**. Full-tier frame counts were not verified. The public preview does not establish a dedicated spear thrust either.

#### UAL2: relevant free actions

Measured from `Universal Animation Library 2[Standard]/Unreal-Godot/UAL2_Standard.glb`.

| Category | Exact action | Samples | Span, seconds |
| --- | --- | ---: | ---: |
| Shield idle | `Idle_Shield_Loop` | 76 | 2.500 |
| Shield reaction | `Idle_Shield_Break` | 33 | 1.067 |
| Shield movement | `Shield_Dash` | 34 | 1.100 |
| Shield action | `Shield_OneShot` | 26 | 0.833 |
| Block | `Sword_Block` | 38 | 1.233 |
| Sword movement | `Sword_Dash` | 48 | 1.567 |
| Sword attack / recovery | `Sword_Regular_A` / `Sword_Regular_A_Rec` | 14 / 30 | 0.433 / 0.967 |
| Sword attack / recovery | `Sword_Regular_B` / `Sword_Regular_B_Rec` | 17 / 32 | 0.533 / 1.033 |
| Sword attack | `Sword_Regular_C` | 61 | 2.000 |
| Sword combinations | `Sword_Regular_Combo` / `Sword_Heavy_Combo` | 91 / 131 | 3.000 / 4.333 |
| Unarmed melee / recovery | `Melee_Hook` / `Melee_Hook_Rec` | 15 / 19 | 0.467 / 0.600 |
| Hit | `Hit_Knockback` | 26 | 0.833 |
| Overhand **throw** | `OverhandThrow` | 41 | 1.333 |
| Get up, not death | `LayToIdle` | 47 | 1.533 |
| Other melee | `Zombie_Scratch` | 55 | 1.800 |
| Carry walk | `Walk_Carry_Loop` | 61 | 2.000 |
| Spear, thrust/stab or death | No explicitly named action in this free file | — | — |

`Shield_OneShot` needs playback inspection before assigning it a more specific gameplay meaning. `OverhandThrow` is not a spear thrust: release, recovery and hand trajectory differ.

The full preview also exposes shield `Sprint_Shield`; melee `Melee_Combo`, `Melee_Knee`, `Melee_Knee_Rec`, `Melee_Uppercut`; sword `Sword_Aerial_A`, `Sword_Aerial_A_Rec`, `Sword_Aerial_B`, `Sword_Aerial_Combo`, `Sword_Aerial_Idle`, `Sword_GroundPound_RM`, `Sword_UpperCut_RM`, `Sword_Heavy_A`, `Sword_Heavy_A_Rec`, `Sword_Heavy_B`, `Sword_Heavy_B_Rec`, `Sword_Heavy_C`, `Sword_Heavy_C_Rec`, `Sword_Heavy_D`, `Sword_Light_A`, `Sword_Light_A_Rec`, `Sword_Light_B`, `Sword_Light_B_Rec`, `Sword_Light_C`, `SwordLight_C_Rec`, `Sword_Light_D`, `Sword_Light_Combo`; and airborne reactions `LiftAir_Hit_L`, `LiftAir_Hit_R`, `LiftAir_Die_Loop`, `LiftAir_Fall_Impact`, `LiftAir_Fall_Loop`, `LiftAir_Fall_RM`. These preview identifiers and artwork span revisions; they are not a downloaded paid-tier manifest. Frame counts remain unverified.

**Quality judgement:** this is the strongest CC0 base for preserving a consistent adult rig while replacing the look. The locomotion already exists; we should not rebuild a walk cycle procedurally. However, generic arm swing will collide with carried equipment unless the armed stance is adjusted. A sword attack is not automatically a spear attack.

#### Quaternius licensing needs version-specific provenance

The three inspected Standard archives explicitly contain **CC0** notices; their named pack pages also advertise CC0. In contrast, the current [sitewide licence](https://quaternius.com/license.html) is **Quaternius Asset License v1.0, dated 2026-08-28**, which permits incorporated products but prohibits redistributing standalone original or modified assets. QAL is not CC0.

Use and preserve the exact archive-level CC0 grants below, not a blanket assumption that everything on Quaternius is public domain. [CC0's legal text](https://creativecommons.org/publicdomain/zero/1.0/legalcode) makes its dedication/waiver irrevocable. A future archive carrying only QAL would need a different public-repository decision. The discrepancy is a reason to retain the evidence with any future import.

### KayKit: the most useful CC0 combat donor found

Sources: [KayKit Character Animations](https://kaylousberg.itch.io/kaykit-character-animations), [KayKit Adventurers](https://kaylousberg.itch.io/kaykit-adventurers). The animation archive's `License.txt` is CC0. Animations are free; editable source is a paid tier. Adventurers supplies free rigged stylized characters and accessories. Both FBX and glTF are available.

The following inventory is the **Medium rig**, version 1.1. Large-rig contents are a separate subset; do not assume they match. These are exact GLB action names, not inferred descriptions.

| Action(s) in `Rig_Medium_CombatMelee.glb` | Samples, respectively |
| --- | --- |
| `Melee_1H_Attack_Chop`, `Melee_1H_Attack_Jump_Chop` | 33, 41 |
| `Melee_1H_Attack_Slice_Diagonal`, `Melee_1H_Attack_Slice_Horizontal` | 31, 42 |
| **`Melee_1H_Attack_Stab`** | **49** |
| `Melee_2H_Attack_Chop`, `Melee_2H_Attack_Slice` | 50, 34 |
| `Melee_2H_Attack_Spin`, `Melee_2H_Attack_Spinning` | 73, 21 |
| `Melee_2H_Attack_Stab`, `Melee_2H_Idle` | 49, 33 |
| `Melee_Block`, `Melee_Block_Attack`, `Melee_Block_Hit`, `Melee_Blocking` | 33 each |
| `Melee_Dualwield_Attack_Chop`, `Melee_Dualwield_Attack_Slice`, `Melee_Dualwield_Attack_Stab` | 39, 36, 49 |
| `Melee_Unarmed_Attack_Kick`, `Melee_Unarmed_Attack_Punch_A`, `Melee_Unarmed_Idle` | 29, 36, 33 |

| Other required motion | Exact action(s) | Samples | Span, seconds |
| --- | --- | ---: | ---: |
| Idle | `Idle_A`, `Idle_B` | 33, 65 | 1.067, 2.133 |
| Walk | `Walking_A`, `Walking_B`, `Walking_C` | 33, 33, 49 | 1.067, 1.067, 1.600 |
| Run | `Running_A`, `Running_B` | 25, 25 | 0.800 each |
| Hit | `Hit_A`, `Hit_B` | 21, 27 | 0.667, 0.867 |
| Death | `Death_A`, `Death_B` | 25, 80 | 0.800, 2.633 |
| Held death pose | `Death_A_Pose`, `Death_B_Pose` | 1 each | 0 |

These latter actions live in `Rig_Medium_General.glb` and `Rig_Medium_MovementBasic.glb`. The combat file also includes `T-Pose`; it is not a combat clip. All listed animated tracks use 30 Hz sampling.

**Props:** the actual rig has `handslot.r` and `handslot.l`, plus `hand.l` and `lowerarm.l`. The hand slots are useful existing attachment points. No dedicated forearm shield slot was found; add one beneath `lowerarm.l` for the aspis. A hand-held buckler and a forearm-strapped aspis need different placements.

**Quality judgement:** unusually good free combat coverage, including genuine stab-labelled actions and blocking reactions. The donor body is cartoon/chibi; the creator warns that different body proportions can change results. Retargeting to the adult Quaternius body is untested here. `Melee_1H_Attack_Stab` is the best named CC0 candidate to preview, but its name does **not** prove an overhand hoplite thrust. The two-handed stab is unsuitable unchanged because the left arm must carry the shield.

### Kenney: useful rigs, insufficient motion for this unit

Inspected the official v1.1 archives for [Animated Characters: Protagonists](https://kenney.nl/assets/animated-characters-protagonists), [Retro](https://kenney.nl/assets/animated-characters-retro), and [Survivors](https://kenney.nl/assets/animated-characters-survivors). Each archive's licence is CC0.

| Pack | Supplied standalone animation files | Requested combat coverage | Frame counts |
| --- | --- | --- | --- |
| Protagonists v1.1 | `Animations/idle.fbx`, `jump.fbx`, `run.fbx` | No separate walk, melee, spear, shield, stab, block, hit or death file | Not listed; FBX curves not decoded |
| Retro v1.1 | Same three files | Same gap | Not verified |
| Survivors v1.1 | Same three files | Same gap | Not verified |

This statement concerns the supplied animation directories, not every possible animation made for a compatible skeleton. The inspected `Model/characterMedium.fbx` names `RightHand`, `LeftHand`, `RightForeArm`, `LeftForeArm` and finger bones; no explicit weapon or shield slot was found. Proposed attachment is a right-hand child for the spear and a left-forearm child for the shield. See Kenney's [character import guidance](https://kenney.nl/knowledge-base/game-assets-3d/importing-characters-and-animations).

The blocky proportions and sparse supplied motion make these a poorer main source than Quaternius or KayKit for this particular task.

### Reproducible CC0 archive evidence

These are SHA-256 hashes of the actual downloaded ZIP bytes on the research date, not model hashes. Downloads were obtained through each creator's official page. Itch upload IDs distinguish free archives from paid tiers; download URLs are temporary, so retain the page and ID instead of a signed link.

| Official archive | Upload ID | SHA-256 |
| --- | --- | --- |
| Quaternius Universal Base Characters Standard | `15861669` | `fdbf1804c90dfc1ea03e992bff7da2dfd1a79318e13270a660180f9308455f40` |
| Quaternius UAL1 Standard | `17958403` | `cc73fc4e495b82958207316596317a3f40b9fa38065bde1027937452da537724` |
| Quaternius UAL2 Standard | `17958478` | `4008ea208a604773a2b2177d965f0f5d3195498b5bf838c3f5785d68e95f2a68` |
| KayKit Character Animations 1.1 | `15799903` | `65882f31f905ad2e953819648a59287cdeab8f623908d5ef701971d3758be20f` |
| Kenney Protagonists v1.1 | Kenney download | `ec3787de70fa2200256848d74201b10f6b6c3126594e9857bf989753312c2b84` |
| Kenney Retro v1.1 | Kenney download | `1d03f1fb001f3cf629425b69c898df58261a316616220ea25b58bd35298e6882` |
| Kenney Survivors v1.1 | Kenney download | `fdadced07a0454c9b7f0b46507be6144a072b4d03b4ffa37f225893c76c62845` |

UBC's notice is `Universal Base Characters[Standard]/License_Standard.txt`; the animation archives have `License.txt` under their pack root. The official Quaternius viewer's public `index.pck` was also inspected as data for full-preview names, not run or adopted; hash `d09e1dac9b55e223ba3f450b472b26373a55b7cb9194775cb35bc86072f5921f`. Preview and download revisions differ, so the measured free inventory above takes precedence.

## 0 A.D.: the strongest directly relevant shipped example

The authoritative project now lives at [Wildfire Games' Gitea](https://gitea.wildfiregames.com/0ad/0ad). For reproducibility, this survey inspected the [GitHub mirror at `61a3b9507d974084e6badb88a0826bd89a6d5b8b`](https://github.com/0ad/0ad/tree/61a3b9507d974084e6badb88a0826bd89a6d5b8b), not an assumed latest upstream release. Paths below are under `binaries/data/mods/public/art/`.

### Body, equipment and skeleton are already an assembly

| Source | What it establishes |
| --- | --- |
| [Athenian basic spearman actor](https://github.com/0ad/0ad/blob/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/actors/units/athenians/infantry_spearman_b.xml) | Body `skeletal/new/m_tunic_short.dae`; Greek head, helmet, aspis and hoplite spear as separate props; common hoplite and formation animation variants. |
| [Spartan champion spearman actor](https://github.com/0ad/0ad/blob/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/actors/units/spartans/infantry_spearman_c.xml) | Armoured body `skeletal/new/m_armor_tunic_short.dae`, spear, aspis, greaves, helmet variants, sheath and cape. A closer armoured-hoplite construction reference. |
| [Common hoplite variant](https://github.com/0ad/0ad/blob/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/variants/biped/base_hoplite.xml) | Actual idle/walk/run/attack selections and runtime speed/frequency settings. |
| [Biped skeleton](https://github.com/0ad/0ad/blob/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/skeletons/biped.xml) | Standard hierarchy and mapping between animation/export skeletons. |
| [Hoplite spear prop](https://github.com/0ad/0ad/blob/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/actors/props/units/weapons/spear_hoplite.xml) | Mesh `props/spear_hoplite.dae` and its material/texture dependencies. |

Mesh and animation sources are separate **COLLADA 1.4.1 `.dae` files**. XML actors select meshes, textures, materials, prop actors, animation variants and weights. Fetching only a body mesh will miss the equipment, textures and animation mapping. The aspis actor itself can have nested back/grip props.

The attachment hierarchy is particularly useful:

```text
arm_R -> forearm_R -> hand_R -> weapon_R   [spear]
arm_L -> forearm_L -> shield_arm          [aspis]
                  -> hand_L -> shield / weapon_L / weapon_bow
```

The actor uses `attachpoint="weapon_R"` and `attachpoint="shield_arm"`. The mesh carries corresponding `prop-weapon_R` and `prop-shield_arm` nodes. The shield follows the forearm independently of the hand. See the project's [prop-point guide](https://wildfiregames.com/forum/topic/19739-prop-points-guide-and-faq/): animated-mesh attachment points use prefixed bones and inherit their parent's motion; static objects can use empties. This is concrete prior art for keeping the long spear rigid and the aspis strapped to the arm.

**Blender import:** built-in COLLADA support is available in [Blender 4.5 LTS](https://docs.blender.org/manual/en/4.5/files/import_export/collada.html) and was [removed for Blender 5.0](https://projects.blender.org/blender/blender/pulls/139337). A practical future bridge is to import and validate in 4.5, then save `.blend` or export glTF for the main pipeline. This survey did not test that conversion; importing separate clips and preserving bind poses/prop nodes still needs verification.

### Exact hoplite animation inventory

All 23 files in the inspected [hoplite animation directory](https://github.com/0ad/0ad/tree/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/animation/biped/infantry/hoplite) are listed below. Names omit `.dae`. Counts and sampling rates were measured from COLLADA time arrays. Mixed rates are real; assuming every file is 30 fps changes timing.

| File name(s) | Samples per file | Sample rate | Span, seconds | Use |
| --- | ---: | ---: | ---: | --- |
| `attack_melee_01`, `attack_melee_02`, `attack_melee_03` | 36 | 24 Hz | 1.458 | Additional spear attacks in directory |
| **`attack_melee_04`, `attack_melee_05`** | **36** | **30 Hz** | **1.167** | **Attacks selected by `base_hoplite.xml`** |
| `idle_ready_01`, `idle_ready_02`, `idle_ready_back` | 61 | 24 Hz | 2.500 | Ready/formation poses |
| `idle_ready_front` | 61 | 30 Hz | 2.000 | Front-rank ready idle |
| `idle_relax_01`, `idle_relax_02`, `idle_relax_03`, `idle_relax_04`, `idle_relax_05`, `idle_relax_06` | 61 | 30 Hz | 2.000 | Six relaxed idles |
| `idle_relax_long_01` | 201 | 30 Hz | 6.667 | Longer relaxed idle |
| `walk_relax` | 41 | 30 Hz | 1.333 | Normal relaxed walk |
| `walk_ready`, `walk_ready_front` | 41 | 24 Hz | 1.667 | Ready/formation walk |
| `jog_ready` | 21 | 24 Hz | 0.833 | Ready jog |
| `jog_relax` | 25 | 24 Hz | 1.000 | Relaxed jog |
| `run_ready` | 21 | 30 Hz | 0.667 | Ready run |
| `run_relax` | 21 | 24 Hz | 0.833 | Relaxed run |

The chosen actor also uses [generic infantry death variants](https://github.com/0ad/0ad/blob/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/variants/biped/death_infantry.xml): `animation/biped/infantry/death_a.dae` has 31 samples at 24 Hz (1.250 seconds), and `death_b.dae` has 47 at 24 Hz (1.917 seconds). The champion's cape has its own death variant dependencies.

**Hit/block gap:** no dedicated hit or block clip was found in this hoplite directory or the selected actor/variant chain. Ready shield stances are not evidence of a separate block reaction. This is a scoped absence, not a claim about all 0 A.D. assets. There is also an adjacent general spearman family with small-shield and shield-arm variants, but the native hoplite chain is the more direct source.

**Overhand evidence:** in `attack_melee_04/05`, inspected bone transforms place the right hand above the head in the preparation and extend it forward around head height. That is consistent with an overhand spear thrust. It is stronger evidence than a filename, but it is still data inspection, not an approved playback of the assembled hoplite.

The normal actor chooses the relaxed idles, relaxed walk/run and attacks 04/05. Formation variants choose front/middle/back ready poses and locomotion. Preserve those pairings before borrowing individual clips. Runtime XML includes attack `speed="30"`, idle `speed="80"`, and other speed values; these are **not frame counts**. Source duration alone does not reproduce the game's playback. Some relaxed idle files have nonzero absolute start times, so normalize their ranges during import rather than treating the final timestamp as duration.

### Licence: usable in a public repository, with explicit exceptions

The project's [root licence](https://github.com/0ad/0ad/blob/61a3b9507d974084e6badb88a0826bd89a6d5b8b/LICENSE.txt) distinguishes GPL engine code from art. Its [art licence](https://github.com/0ad/0ad/blob/61a3b9507d974084e6badb88a0826bd89a6d5b8b/binaries/data/mods/public/art/LICENSE.txt) specifies **CC BY-SA 3.0**, with Wildfire Games attribution. Keep any additional per-file notices and texture-source exceptions; do not assume the licence permits separately obtaining or redistributing original third-party texture libraries.

For Legatum, the practical interpretation is:

- We may modify and redistribute the covered mesh, skeleton, animation and textures, including commercially, with attribution, the licence link and modification notices.
- Treat painted sprites rendered from those assets as adaptations and distribute those sprites under CC BY-SA, conservatively retaining 3.0. Retargeting motion, repainting a model or rasterizing it does not reliably remove the original rights.
- Independent engine code can remain MIT; a collection containing BY-SA art does not automatically put every independent component under BY-SA. See the [CC BY-SA terms](https://creativecommons.org/licenses/by-sa/3.0/) and [Creative Commons FAQ](https://creativecommons.org/faq/). CC BY-SA is not a GPL-style editable-source delivery requirement.
- Our current `LICENSE-ART` says every Legatum image/video is CC BY 4.0. **Before importing this path**, add an explicit third-party exception and provenance for the derivative sprites and any redistributed sources. We cannot label the derivative sprites solely CC BY 4.0 and discard ShareAlike. No licence files are changed by this survey.

A suitable future credit identifies the particular 0 A.D. assets, Wildfire Games, the source revision, CC BY-SA 3.0, and our repainting/retargeting/rendering changes. Credit alone is insufficient without ShareAlike on the resulting adaptation.

## Mixamo: capable, account-dependent, not the default

[Adobe's FAQ](https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html) says Mixamo is free with an Adobe ID, without a Creative Cloud subscription, and permits royalty-free use in games, films and graphic art. Its [product page](https://www.mixamo.com/) describes a motion-capture library with preview and retargeting. We did not sign in or download anything; use remains deferred to Sam's decision.

The following exact historical titles are evidenced by a [firsthand game-integration tutorial](https://forum.orkframework.com/d/5215-tutorial-ork-animations-using-mecanim-my-all-new-comprehensive-guide) using the Pro Sword and Shield pack. Repeated display names can represent different variants; a numbered imported filename is not a durable catalog ID.

| Need | Documented title(s) | Qualification |
| --- | --- | --- |
| Armed idle / locomotion | `Sword And Shield Idle`, `Sword And Shield Walk`, `Sword And Shield Run` | Tutorial selects a neutral idle variant; not proof of a spear grip |
| Melee | `Sword And Shield Slash` | Forward-slash variant; sword motion |
| Block | `Sword And Shield Block`, `Sword And Shield Block (2)`, `Sword And Shield Block Idle` | Enter, exit and held block in the demonstrated setup |
| Hit | `Sword And Shield Impact` | Tutorial selects a front-hit variant |
| Death | `Sword And Shield Death` | Tutorial selects a backwards-fall variant |
| Thrust | `Upwards Thrust` | Independently documented as used by the authors of [Muenks et al., 2023, section 2](https://cdatp.journals.qucosa.de/cdatp/article/download/114/80); does not establish a shield-compatible overhand spear animation |
| Spear-specific set | Not verified | Do not claim a complete native hoplite set |

Frame counts were not verified. Export frame rate, trimming and motion controls can change them. `Bayonet Stab` and `Thrust Slash` are useful search terms for a future authorized catalog session, but this survey did not establish their current availability from Adobe; third-party reuploads are not licence evidence. A two-handed bayonet animation would also conflict with the shield arm.

**Props:** rig the body without large equipment, consistent with Adobe's auto-rig requirements, then attach props after import. Conventional Mixamo exports commonly use `mixamorig:RightHand` and `mixamorig:LeftForeArm`; verify the actual model's names and add our own sockets. No export was inspected here, and a dedicated spear/shield socket is not guaranteed.

**Licence for sprites:** rendered character sprites incorporated into a game fit the uses Adobe's FAQ describes. This is not CC0 or a grant to publish the raw animation library. Adobe's [community licensing FAQ](https://community.adobe.com/questions-696/mixamo-faq-licensing-royalties-ownership-eula-and-tos-589400?lang=en) distinguishes permitted incorporated projects from redistribution of raw character/animation files; the governing [Mixamo additional terms](https://wwwimages2.adobe.com/content/dam/cc/en/legal/servicetou/Mixamo-Addl-Terms-en_US-20210623.pdf) and Adobe terms should govern an actual adoption decision. Keep raw Mixamo FBX and animation-containing `.blend` files out of a public repo. A generally reusable sprite asset pack or a blanket CC BY grant for all underlying rights is a separate question from permission to ship sprites in our game. No assertion of that broader permission is made here.

## Blender sprite-baking prior art

These tools supply **no combat motion**. They consume an already animated character; props must already follow the rig. Rotate the complete rig-plus-props assembly, keep a fixed floor pivot and camera scale, and preserve one direction convention. Eight views ordinarily mean 45-degree heading increments, but integration must follow Legatum's existing atlas contract.

| Project / licence | Reusable work and evidence | Limits found in source or documentation |
| --- | --- | --- |
| [FoozleCC `blender_scripts`](https://github.com/FoozleCC/blender_scripts), **MIT**; [eight-direction script](https://github.com/FoozleCC/blender_scripts/blob/0409872ba070cd6d7e9eada9eafa09193be71ded/render_8_direction_sprites) | Small action-by-action render loop, 4/8 headings, configurable frames, colour and normal output. Closest minimal reference to adapt into an existing atlas pipeline. [Author's download/demo](https://foozlecc.itch.io/render-4-or-8-direction-sprites-from-blender). | Current script filters to action `run`; normal-output compositor node is required by an early-return check, despite an “optional” comment. Active-object rotation must include props. Example Blender content includes Mixamo motions: the script's MIT licence does not grant redistribution rights to those assets. Older action APIs need testing with current Blender. |
| [Blender-Spritesheet-Renderer](https://github.com/chrishayesmu/Blender-Spritesheet-Renderer), **MIT** | Add-on batches actions, angles and material variants, frames orthographic cameras, packs sheets with metadata; uses ImageMagick. More complete UI/pipeline reference. | Documentation's tested version is Blender 2.90.1 on Windows; no NLA support. Do not assume modern action-slot compatibility. Choose consistent bounds, rather than allowing frame-to-frame fitting to change apparent scale. |
| [HardRockTech 3d-to-2d-sprite-pipeline](https://github.com/HardRockTech/3d-to-2d-sprite-pipeline), **MIT** | Eight cameras, manifests, masks, normals, heights, shadows, crop/padding; author reports using it for thousands of frames. Useful pipeline architecture. | Inspected `CameraSetup8Dir.py` and `SpriteGenerationScript3.0.py` set cameras to **`PERSP`**, despite isometric descriptions. Script has a ten-frame constant and fixed action index. Camera order differs from README order. Adapt and verify; not a drop-in orthographic baker. |
| [Blender Sprite Studio](https://croomfolk.itch.io/blender-2d-sprite-studio), **CC0** | Blender 3.6 scene with isometric and dimetric 2:1 cameras, lights, shadow catcher and compositor. Author uses it for game-jam assets. Useful camera/lighting fixture. | Not an automatic all-action eight-direction batch/atlas system. Its pixel-art anti-alias treatment is not our painted look. |
| [SpriteForge](https://github.com/arqsbo3d/spriteforge), **GPL-3.0-or-later** | Claims animated import and sheets, 26 directions including multiple elevations, Blender 4.4 testing. More recent broad tool. | Early v0.9; runtime not tested here. Pixel-art processing needs disabling/adaptation. GPL governs tool redistribution, not automatically the rendered image; source asset licences still apply. |
| [iso-render-pipeline](https://github.com/craigrmccown/iso-render-pipeline), **no licence found** | Readable orthographic isometric camera, rotation, animation sampling and PNG/JSON reference. | No licence file found in the inspected tree: public code is not automatically reusable open-source code. Do not copy until licensed. |

Read-only source snapshots: Foozle `0409872ba070cd6d7e9eada9eafa09193be71ded`; Blender-Spritesheet-Renderer `445964c610ec24a2a833a46a0b2e71cdfb788e50`; HardRockTech `e123db7f80acd96a920cf9f950f67dddca4898a6`; SpriteForge `015b0fbf49d43b1633202490eb923c783c4175f5`; iso-render-pipeline `c7ccbc5641aa9f833c1618ed36c61dd2e5642784`.

**Preferred reuse:** borrow the small, licensed Foozle action/direction loop and the camera/framing ideas, integrating them into the existing animation atlas pipeline. Do not import a whole demo scene just to get eight headings. Modern Blender action handling, alpha, ground contact, shadows and direction ordering still require a small rendered validation.

## Recommendation and next experiment

### Best CC0 path

Use **one Quaternius Universal Base Characters rig** as the working body, retaining the pinned CC0 notice. Start with its matching UAL1 locomotion and reactions. Fit armour and the painted appearance only after the motion reads as a game unit.

| Required clip | Starting source | Work still needed |
| --- | --- | --- |
| Idle | UAL1 `Idle_Loop`; compare UAL2 `Idle_Shield_Loop` | Set a credible spear grip and forearm shield placement without removing the natural body motion. |
| Walk | UAL1 `Walk_Loop` | Preserve the existing gait; adjust the arms for carried spear/shield and verify feet stay planted. |
| Overhand spear thrust | Preview KayKit `Melee_1H_Attack_Stab` as the closest CC0 donor | Retarget and adapt the right arm/weapon trajectory into an overhand thrust while maintaining the left-arm guard. If the donor is unsuitable, author this one short attack on the established rig. Do not relabel a throw or sword slash. |
| Hit | UAL1 `Hit_Chest`; compare `Hit_Head` | Maintain equipment grip and return to the chosen idle. |
| Death | UAL1 `Death01` | Check spear/shield collisions, ground contact and the final held pose. |

This buys four native motions and a proven rig immediately, but **it is not a promise of five final clips without animation work**. KayKit can alternatively supply an internally consistent all-KayKit prototype; its stylized proportions make it a less direct final body for Legatum. Retarget only after seeing the donor motion play with the actual prop lengths.

### Best CC-BY-SA path if that falls short

Use **0 A.D.'s native hoplite assembly and Biped skeleton together**, retaining its spear and `shield_arm` attachments. Start with `idle_ready_front`, `walk_ready_front`, `attack_melee_04/05`, and generic infantry `death_a` or `death_b`. Check source timing against the actor variants. Add one short hit recoil or retarget a CC0 KayKit hit; the inspected hoplite chain does not provide it. Treat resulting derivative art as CC BY-SA and add the explicit repository licence exception before adoption.

This is the best evidenced way to obtain the intended spear-and-shield behaviour with minimal invention: the character, equipment and combat motion already belong to a historical RTS. Its fit to our painted look and current Blender import remain to be demonstrated.

The next implementation milestone should be a short, untextured playback of all five actions with the spear and shield attached, viewed from the side, three-quarter angle and intended game camera. Approve weight transfer, foot contact, guard, thrust/recovery and death silhouette first. Then apply the painted look and bake directions. The sprite baker can be borrowed; it cannot rescue motion that has not passed that first review.
