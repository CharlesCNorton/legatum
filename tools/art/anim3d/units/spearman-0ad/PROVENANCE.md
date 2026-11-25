# Spearman: 0 A.D. adaptation

**0 A.D. art by Wildfire Games, CC BY-SA 3.0; adapted for Legatum**

Original project: https://wildfiregames.com/ and https://play0ad.com/.
Licence: https://creativecommons.org/licenses/by-sa/3.0/ (see adjacent LICENSE-ART).
The GLB, atlas and derived renders are CC BY-SA 3.0, including our modifications.
Sam approved this art source for Legatum on 2026-11-25.

Source repository: https://github.com/0ad/0ad
Exact source commit: `61a3b9507d974084e6badb88a0826bd89a6d5b8b`.
All paths below are relative to `binaries/data/mods/public/art/` at that commit.

| Exact file | Use |
| --- | --- |
| `meshes/skeletal/new/m_tunic_short.dae` | Body, native rig and weights |
| `meshes/props/new/dude_head.dae` | Rigid head |
| `meshes/props/helmet/hele_corinthian_a.dae` | Corinthian helmet and crest socket |
| `meshes/props/helmet/props/hele_crest_a.dae` | Crest support |
| `meshes/props/helmet/props/hele_crest_hair_a.dae` | Crest hair |
| `meshes/props/new/capes/cape_hd_hoplite.dae` | Native skinned cloak |
| `meshes/props/spear_hoplite.dae` | Spear |
| `meshes/props/shield/aspis_01_front.dae` | Aspis face |
| `meshes/props/shield/aspis_01_back.dae` | Aspis back |
| `meshes/props/shield/props/aspis_handgrip_01.dae` | Aspis handgrip |
| `animation/biped/infantry/hoplite/idle_relax_01.dae` | idle |
| `animation/biped/infantry/hoplite/walk_relax.dae` | walk |
| `animation/biped/infantry/hoplite/attack_melee_05.dae` | attack |
| `animation/biped/infantry/death_b.dae` | death |

`actors/units/athenians/infantry_spearman_b.xml` informed the assembly. Round one
also imported `meshes/props/helmet/hele_pilos_a1.dae`, `animation/biped/infantry/hoplite/attack_melee_04.dae`
and `animation/biped/infantry/death_a.dae`; those meshes/clips are excluded from the delivered GLB.
The preserved source download inventory and hashes are in
`~/LegatumRuns/anim-pilot/oad/PROVENANCE.md`; its old local-only permission text
is superseded by Sam's explicit round-two approval.

Changes: removed unused helpers; merged body and cloak into one skinned mesh;
retained strongest four native weights and normalized them; attached rigid props
directly to head, weapon_R and shield_arm; converted to metres, Y-up and +Z;
resampled to 30 fps; closed idle/walk poses and incoming tangents; corrected body and prop floor penetration;
retained the authored additive torso/neck hit with the shield moving rigidly.
Replaced materials with a new flat pigment atlas: bronze armour, crimson crest
and cloak, linen skirt, leather and a twelve-ray sunburst aspis. No upstream
texture files, baked illumination, AO, normal maps or camera projection are used.
The crest, shield rim and cloak trim reference a material named `team`, using neutral atlas samples and a crimson base-colour factor. The spear grip location was shifted 0.109 m along the shaft; weapon and shield sockets rotate for floor clearance during the fall. The body rises at most a few centimetres at the end to seat the helmet crest instead of intersecting the floor.

The accompanying `source-manifest.json` records SHA-256 hashes of the preserved input and every exact source file used in this round.
