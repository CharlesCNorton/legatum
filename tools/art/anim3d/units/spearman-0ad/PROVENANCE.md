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

## Painted premium round 2

Continued from the painted round-one branch, incorporating the lead and cloud
reviewer notes through 2026-11-25 02:36Z. `painted_human.py` replaces the native
mannequin body with the CC0 MPFB 2.0.18 body (source/hash/licence in SOURCES.md).
Male macro targets: muscle 1, weight .72, age .42, height .42, proportions .65;
additional arm/shoulder muscle targets shape the anatomy. The body is fitted to
the original rest coordinates. Blender Data Transfer uses POLYINTERP_NEAREST,
matched native bone names, normalization and a maximum of four influences.
The temporary fitting rig is deleted; only the approved 30-bone skeleton ships.
Hidden torso/thigh faces are removed; real hands/feet and sandal straps remain.

`painted_forms.py` broadens/deepens the cuirass with pectoral/abdominal volume,
adds pleated linen and rounded sleeves, shaped knee greaves, a sagittal crest
mass with 105 tapered tufts, and a wider knee-length crimson cloak with deep
folds, darker lining and a shoulder mantle. Helmet/headgear size is increased.
The 64-segment convex aspis, rolled rim, raised sunburst, Corinthian cheek/nose
guards, leaf blade, butt spike and pteruges retain rigid original attachments.
The cloak uses original cape bones and the tunic uses hip/thigh weights.
Comparing both round-one lanes informed sharper shield contrast and separated
pigments. No other-lane mesh, texture or animation buffers were copied.

Warm ochre highlights, dark recesses, stronger form shading and roughness grain
are authored as Blender pigment graphs. Main bronze roughness/metallic is
.49/.45, raised gold .35/.55 before grain. This is procedural painted shading,
not a manually brush-painted texture. The result still needs richer surfaces.

High-resolution parts are preserved before decimation: 70,332 source triangles,
1,131,232 in the combined subdivided/displaced reference. Cycles CPU normal/AO
transfer runs separately by part/pigment group to reduce ray contamination.
Base colour and ORM material channels are baked on the game mesh. Lossless
2048-square base colour, normal, AO and ORM masters and the editable Blender
file remain under `$ANIM_ROOT/lanes/spearman-0ad-painted-r2/` outside git.
Shipped base colour/normal/ORM are 1024-square WebP, embedded and beside the GLB;
quality is 84/85/84 respectively. Compression is lossy, including the data maps.
ORM is R occlusion, G roughness, B metallic, on UV0.

Final GLB: **1,985,664 bytes; LOD0 9,981 triangles, LOD1 2,634**. Two named
skinned meshes share one material and one skeleton; show one LOD at a time.
Both carry red COLOR_0 team masks. Props remain rigid single-bone attachments.
NORMAL/TANGENT use normalized signed shorts, UV/weights normalized unsigned
shorts, joint/mask data unsigned bytes and indices unsigned shorts. Positions
remain floats. Zero quantized weights have zero joint indices; weights sum to
65535. Required extensions: KHR_mesh_quantization and EXT_texture_webp.
Repeated identical animation buffer views/accessors are shared without changing
sample bytes. There is no MSFT_lod. Geometry remains +Z forward with no baked yaw.

SHA-256: `9f860b78aa85c0a292fa3a02e5ebd1c6bef0a61b1bc1214360ad2655259651b1`.
Exact animation/skeleton fingerprint remains
`639ad201654bf2a08b90c9b7b35c8f047ac1f5cf3531e7b7224f80e0e1d58f79`.
Ground fitting changes bind vertices only (maximum initial adjustment 47.21 mm).
The 120 Hz audit passes both LODs with minimum ground clearance -0.50015 mm.
It does not certify general mesh intersections or deformation quality.

Contract validation passes; Khronos reports 0 errors/warnings/infos/hints;
25 validator regression tests pass. Three.js 170 CPU loader/mixer, sharing,
team material and framing checks pass. The CPU image shim validates dimensions,
not browser WebP decoding or GPU appearance. Blender imports/renders the final
WebP GLB. CPU review images and five three-loop game-rate movies are fresh from
that exact asset, using Cycles/AgX.

The existing Poly Haven CC0 studio HDRI, warm key, cool rim, AO, soft shadows and
ACES remain in the browser viewer. The recorder accepts the r2 prefix and now
adds an actual three.js vs-panel PNG alongside the five movies and 12-second
360-degree idle turntable. Host browser capture is reserved for the lead and
has not run here. Renderer tuning and playing-speed approval remain pending.

Honest gate verdict: technical contract passes, **premium art gate is not met**.
Shield-rim faceting, a comb-like crest, angular neckline and insufficient bronze,
skin and cloth richness remain visible. MPFB anatomy improves the source body,
but the final silhouette still lacks the reference painting's heroic mass.

## Painted premium round 3

Continues the painted round-two commit, using the same approved round-six input
and CC0 MPFB 2.0.18 assets. No paid service, new asset download or animation donor.
The feedback was reread through the cloud review at 2026-11-25 03:18Z. The later
suggestion to offset the stance was not applied: the task's exact motion lock
remains authoritative. Bone transforms, hierarchy, inverse binds, all channels,
key times and sample values remain byte-equivalent under `check_painted.py`.

`painted_human.py` retains the MPFB macro anatomy and nearest-face interpolated
native weight transfer (normalize, at most four influences). Limb radial fitting
is fuller. Shoulders, thighs and knees remain continuous through the overhead
attack and fall; cutting surfaces merely because idle armour hides them was
rejected after the joint render exposed an open shoulder. Concealed facial
geometry is removed beneath the closed helmet; a dark rigid liner sits behind
its actual eye and mouth apertures. The torso remains continuous; covered central torso vertices are fitted inside
the cuirass and use its spine/chest blend to prevent skin emerging through the
armour during the locked attack. The temporary MPFB fitting rig never ships.

`painted_premium.py` rebuilds the helmet as a continuous closed Corinthian shell,
with temple/nape coverage, paired eye slots, central nose bridge, jaw guards and
brow/cheek borders. A rounded fluted sagittal horsehair volume with painted radial
streaks replaces the 105 collapsing tufts. The cuirass has paired pectoral and
abdominal relief. A lower folded shoulder drape and a broad rear cloak replace
the stiff collar; the team trim is part of the same cloth surface rather than
an offset ribbon. Knee greaves, pleated chiton, leather pteruges, sandalled MPFB
feet, leaf spear and butt spike retain the original sockets/weights.

The convex aspis keeps a 64-segment boundary, protected raised sunburst rays,
a 96-segment rolled rim and a protected inner gold register. Low-value tiny
ornament no longer consumes the contour budget. Simplification operates on
outer shells before thickness; a face attribute lets LOD1 remove the inner shell,
simplify the exterior, then rebuild thickness. Both LODs are triangulated before
export; LOD0 is triangulated before UV packing and baking.

Cycles CPU selected-to-active normal and AO bakes use preserved pre-decimation
parts subdivided and displaced in Blender. Close shell pairs sometimes return
opposing normals; the baked tangent vectors are reoriented to the receiving
hemisphere and limited to a 25-degree relief cone. This intentionally bounds
surface perturbation and is not an unmodified high-poly normal transfer.
Procedural Blender pigment graphs carry painted value shading, warm ochre,
darker recesses and hair streaks. This is procedural painted-style authoring,
not manual brush painting. Bronze is deliberately rougher and less metallic
than conventional PBR (main bronze .60 roughness / .32 metallic before grain).

Lossless 2048 base colour, normal, AO and ORM masters, editable .blend, bake logs
and diagnostic experiments stay in `$ANIM_ROOT/lanes/spearman-0ad-painted-r3/`.
The three delivered 1024 WebPs use quality 84/85/84; data-map compression is lossy.
Packed ORM remains R occlusion, G roughness, B metallic on UV0. The same two LOD
names, shared material/skin, red team mask, +Z facing and credit are preserved.
The validator now additionally enforces a strict download size below 2,000,000 bytes.

The existing CC0 Poly Haven HDRI, warm key, cool rim, AO, soft shadows and ACES
viewer are retained. `record.mjs --prefix spearman-0ad-painted-r3` writes the
three.js comparison and `<prefix>-turntable.mp4` on the lead's host. Browser
access was unavailable in this lane; no new browser-pixel approval is claimed.
Cycles/AgX evidence includes five three-loop 160 px movies, actual LOD1 48 px
readability, same-size panel comparison, shield/helmet/crest close-ups, joint
samples in all five clips and a separate 12-second CPU turntable. The numerical
joint check is an LBS axis-collapse indicator, not a collision or art certificate.

Final round-three asset: **1,610,900 bytes; LOD0 9,911
triangles / LOD1 2,819; 30 joints; one material**.
SHA-256: `692320d217f41db9f65b791c7a5c71009a35451efd126d1bafda2989746aa175`. The authoring surfaces contain 39,624 triangles;
the combined subdivided reference contains 639,712. Contract and exact-motion
checks pass; Khronos reports zero errors, warnings, infos and hints. The matching
motion/skeleton fingerprint is unchanged from round six:
`639ad201654bf2a08b90c9b7b35c8f047ac1f5cf3531e7b7224f80e0e1d58f79`.
These technical checks do not establish premium art approval.
