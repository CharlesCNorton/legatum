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

Changes: removed unused helpers; retained the strongest four native deforming
weights and normalized them; converted to metres, Y-up and +Z; resampled to
30 fps; closed idle/walk poses and incoming tangents. Retained the authored
additive torso/neck hit. The spear grip moves 0.109 m along its shaft.

Round 3 merges body, cloak, head and every prop into **one mesh, one material
and one indexed primitive**. Spear vertices have 100% weight to weapon_R;
shield/front/back/grip to shield_arm; helmet/crest/support to a new helmet socket
that follows head. Rigid bind-space conversion preserves attachment transforms.
The COLOR_0 red channel replaces the team material on crest, shield rim and cloak
trim. Green/blue are zero and alpha is one. mesh.extras.vertex_regions records
part ranges for inspection. A mask-aware runtime shader provides team tint.

The attack_melee_05 stance turns 22 degrees for a clearer map-camera thrust.
Death_b gains a 12-degree head relaxation while landing, an eased finish and
four final held frames. Socket corrections keep spear and shield above the
floor. A measured hip-height envelope handles between-key floor penetration
while retaining 30 fps sampling and a fixed skeleton root. Walk receives only
a small clearance lift; the native gait and prop rigidity remain.

All pigment is newly authored for Legatum: bronze armour and greave ornament,
linen seams/hem stripes, crimson cloak/crest, Corinthian eye slots and a
12-ray sunburst aspis. No upstream textures, baked illumination, AO, normal
maps or camera projection are used. Main cloak stays crimson; team trim is
neutral in the atlas for runtime tint.

The accompanying source-manifest.json records SHA-256 hashes of the preserved
input and every exact source file used. Heavy source/master/review files stay
under ~/LegatumRuns/anim-pilot/oad/. The final GLB and embedded/separate atlas
are under 2 MB and ship beside this provenance and LICENSE-ART.
