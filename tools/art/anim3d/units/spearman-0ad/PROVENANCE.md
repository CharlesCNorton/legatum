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
| `animation/biped/infantry/death_a.dae` | death |

`actors/units/athenians/infantry_spearman_b.xml` informed the assembly. Round one
also imported `meshes/props/helmet/hele_pilos_a1.dae`, `animation/biped/infantry/hoplite/attack_melee_04.dae`
and `animation/biped/infantry/death_b.dae`; those meshes/clips are excluded from the delivered GLB.
The preserved source download inventory and hashes are in
`~/LegatumRuns/anim-pilot/oad/PROVENANCE.md`; its old local-only permission text
is superseded by Sam's explicit round-two approval.

Changes: removed unused helpers; retained the strongest four native deforming
weights and normalized them; converted to metres, Y-up and +Z; resampled to
30 fps; closed idle/walk poses and incoming tangents. Authored the torso/neck hit over a native idle guard (replaced by the stronger
round 5 recoil described below). The spear grip moves 0.109 m along its shaft.

Round 3 merges body, cloak, head and every prop into **one mesh, one material
and one indexed primitive**. Spear vertices have 100% weight to weapon_R;
shield/front/back/grip to shield_arm; helmet/crest/support to a new helmet socket
that follows head. Rigid bind-space conversion preserves attachment transforms.
The COLOR_0 red channel replaces the team material on crest, shield rim and cloak
trim. Green/blue are zero and alpha is one. mesh.extras.vertex_regions records
part ranges for inspection. A mask-aware runtime shader provides team tint.

Round 4 restores the native attack_melee_05 stance; a documented 30-degree
display yaw (-30 degrees about +Y) is implemented in the review cameras only. The GLB stays +Z forward.
Round 5 replaces death_b with death_a: direct backward collapse instead of a
long staged crouch. It gains a 32-degree head relaxation while landing, an eased
finish and four final held frames. The shield is laid flat, with at most 9.38 mm
of socket clearance for its thickness. The body rests on the ground rather than
being lifted by its crest or shield. The spear still releases at death frame zero
and weapon_R follows the same 0.533-second world-space drop beside the body,
then holds. Single-bone rigid weights remain unchanged. A measured hip-height
envelope handles between-key floor penetration while retaining 30 fps sampling
and a fixed skeleton root.

Round 5 opens the idle and hit guard with a fixed-length two-bone arm solve
(hand target 10 cm out, 22 cm back, 5 cm down), then rolls the forearm 35 degrees
outward. The shield, hand and grip follow the anatomical chain. Attack_melee_05
receives monotone cubic timing for takeback, drive and recovery, a 13.25 cm total
forward hip drive, planted-ankle two-bone leg solves and four degrees of shoulder
follow. The cape1/2/3 local rotation excursions are reduced by 50%. Hit is newly
authored over idle: 14-degree torso recoil at frame 5, three-degree neck follow,
and eased recovery by frame 20. Walk remains native with its existing small
clearance correction.

Round 5 thickens the crest another 1.3x and raises its height 1.2x (overall figure
1.9361 m, inside the 1.95 m contract ceiling), widens the spear cross-section 1.5x
and adds a brighter bronze spearhead swatch. Topology and triangle count stay
unchanged. Fresh small-scale renders check a 48 px-tall figure beside 160 px
sprites; these changes are all in the GLB, not camera-only paint.

Round 4 darkens bronze and crimson base pigments, separates skin and linen
values, and enlarges the bronze sunburst against an oxidised bronze shield field.
The dark neutral rim retains its team mask. Crest hair width is multiplied
by 1.65 and its support by 1.30 without adding triangles, for 160 px readability. All pigment is newly authored for Legatum: bronze armour and greave ornament,
linen seams/hem stripes, crimson cloak/crest, Corinthian eye slots and a
12-ray sunburst aspis. No upstream textures, baked illumination, AO, normal
maps or camera projection are used. Main cloak stays crimson; team trim is
neutral in the atlas for runtime tint.

The accompanying source-manifest.json records SHA-256 hashes of the preserved
input and every exact source file used. Heavy source/master/review files stay
under ~/LegatumRuns/anim-pilot/oad/. The final GLB and embedded/separate atlas
are under 2 MB and ship beside this provenance and LICENSE-ART.

Round 6 replaces only hit, using the delivered idle-zero pose. The new reaction
has 15 cm pelvis recoil, 6.5 cm drop, 25-degree spine/chest bend, neck follow one
frame late, a rigid shield-arm jolt, spear dip and a 15 cm rear-foot catching
step. Fixed-length limb solves retain foot/grip attachment. It eases back to the
exact idle-zero samples on key 24 (0.8 s), with the skeleton root fixed. The
GLB is patched only in its existing hit output accessors; approved clips,
geometry, textures, skin, team mask and attribution are preserved. No new
third-party inputs were used. Source: hit.py; measured review: package_hit.py.


## Premium PBR round 1

Motion source is the approved round-6 GLB, SHA-256
`84bf794f543fd4a1af2d1b9c2b48c89a6c52533a00d7803e553b49a22513f92c`.
Preserved locally as `~/LegatumRuns/anim-pilot/oad/pbr-r1/approved-r6.glb`.
`pbr_build.py` authors only rest geometry and material data in Blender;
`pbr_export.py` copies every animation input/output buffer, inverse bind and
original joint transform directly from that source. `check_pbr.py` independently
compares the payload bytes and evaluates floor clearance at 120 fps.
The round-5 attack/cloth/death fixes and round-6 hit are not resampled or edited.

New geometry: 64-segment convex aspis, rolled rim, inner bead, 12 raised bronze
rays, boss and rivets; round Corinthian dome, open eye line, cheek plates, nasal
and edge trim; full rounded horsehair crest with tapered strand ridges; ash
shaft, lenticular leaf blade, socket and butt spike. New tapered bronze greave shells have thickness, rolled lips and a raised shin
rib on the unchanged calf sockets. The native weighted body and cloak are subdivided/refined; cloak folds are authored in rest
space, with leather pteruges, cuirass piping and embossed scrollwork added.
Rigid carried props keep their original weapon_R, shield_arm and helmet sockets.
Cuirass decoration inherits nearby native garment weights. A geometry-only
floor fit checks both LODs against frozen animation; no keys are changed.

The dense source uses two levels of simple subdivision, actual small hammered
surface displacement, and procedural fibre/skin/metal bump. Cycles CPU bakes
its tangent normals and AO onto the game mesh. Pigment and material scalars are
baked independently through emission; the delivered material is lit Principled
PBR, with no emission. Bronze is metallic with varying roughness, brighter and
smoother edge pigment; linen is off-white and matte, leather semi-matte, and
cloak/scarf crimson. Pigment has small colour variation and a gentle vertical
value gradient, with darker low areas; it contains no directional illumination
or AO. AO is stored only in ORM.R, roughness in G and metallic in B, all UV0.

`oad/pbr-r1/` holds the editable `.blend`, dense mesh and **2048 square**
texture masters. The three **1024 square** shipping maps are embedded in
`spearman.glb` and provided as adjacent PNGs. One GLB contains two skinned meshes,
`spearman_LOD0` and `spearman_LOD1`, sharing one 30-joint skeleton and one material.
Select exactly one mesh at runtime (one primitive/draw per selected LOD).
No MSFT_lod extension. COLOR_0.r remains the team mask on both LODs.
The main asset path and +Z facing are unchanged; display yaw remains camera-only.

Review lighting uses Poly Haven **Studio Small 09**, Sergej Majboroda, CC0:
https://polyhaven.com/a/studio_small_09 and https://polyhaven.com/license.
Exact file: https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/studio_small_09_1k.hdr
SHA-256 `e7cfda5f4e98e623db12b8bfd0184e048488e4855d9c83e2751fb44a32e80c45`.
It is checked in beside the viewer; it is not baked into the base colour.
The viewer adds a warm key, cool rim, soft shadow filtering, SSAO and ACES.
Blender review renders use the same asset and HDRI with Cycles CPU/AgX; these
are explicitly distinct from the lead's browser/ACES captures.
No other third-party inputs, paid services or motion libraries were added.
The GLB, textures and derived renders remain CC BY-SA 3.0.

Final round-1 counts: **9,686 triangles LOD0**, **2,838 triangles LOD1**;
dense bake source **232,752 triangles**. Both LODs share the same three maps.
The source manifest records the final GLB, shipping textures and 2048 masters.
