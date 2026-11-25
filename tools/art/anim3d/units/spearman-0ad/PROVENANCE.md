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

## Painted premium round 1

This section supersedes the earlier single-mesh / flat-atlas delivery contract.
The main file now contains `spearman_LOD0` and `spearman_LOD1`, each one indexed
skinned primitive, sharing skin 0 and material 0. A consumer must show one LOD
at a time. No `MSFT_lod` is used. Both have the red-channel COLOR_0 team mask;
crest, outer shield rim and cloak trim retain their team semantics.

`painted.py` rebuilds the aspis from 64 radial segments with a convex dish,
rolled rim, raised twelve-ray sunburst, boss, engraved registers and rivets.
It adds a rounded Corinthian dome, separate cheek/nose guards and open eye
slots; a full fluted horsehair mass and rounded support; a leaf spearhead,
ferrules and butt spike; greaves; a shaped bronze cuirass with palmette and
pectoral ornament; leather pteruges; and folds in the native skinned cloak.
Native body weights are retained and interpolated by subdivision/decimation.
Coincident exported seam vertices are welded for smooth shading. The original
bronze torso surfaces covered by the new cuirass are removed to avoid overlap.

All props remain rigid, weighted 100% to their original sockets. Geometry is
built in the original bind coordinates. A ground-envelope fit adjusts only
rest-mesh vertices against the unchanged animation's sampled ground planes;
it does not edit weights, sockets, actions, timings, transforms or baked yaw.
`check_painted.py` compares every animation channel, input/output sample, joint,
inverse bind, bone transform and ancestor relationship to the preserved
round-six GLB. The matching motion/skeleton SHA-256 is
`639ad201654bf2a08b90c9b7b35c8f047ac1f5cf3531e7b7224f80e0e1d58f79`.

The high-poly baking copy uses two extra subdivision levels and small geometric
noise displacement. Cycles CPU selected-to-active bakes provide tangent-space
normals and AO. The painted lane bakes authored pigment graphs with stronger
fixed form shading, warm highlights, darker recesses and grain, plus a partial
AO contribution to base colour. This deliberately carries more shading than
the PBR lane. Bronze is rougher and less metallic (roughness .53-.82, metallic
.18-.38 across raised and recessed bronze); linen, wool and leather remain
matte dielectrics. Separate regions carry distinct painted values.

Base colour, normal and packed ORM are authored/baked at 2048 and downsampled
to 1024 for delivery. ORM uses R occlusion, G roughness, B metallic, on UV0.
All three PNGs are embedded in the GLB and also available beside it. The Blender
master, high-poly copy, 2048 images, logs and receipts are retained under
`$ANIM_ROOT/lanes/spearman-0ad-painted-r1/`. The original round-six animations
are copied directly, without passing through a Blender animation export.

The viewer now uses the documented CC0 Poly Haven studio HDRI, warm key, cool
rim, soft shadow filtering, material AO and ACES tonemapping. The display yaw
remains in the camera. `record.mjs --prefix spearman-0ad-painted-r1` writes five
native-30-fps viewer clips and a 12-second 360-degree idle turntable. CPU sprites
and stills use Cycles/AgX and are labelled separately from that browser review.
