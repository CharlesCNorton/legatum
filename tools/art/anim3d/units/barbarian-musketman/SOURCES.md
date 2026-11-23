# Barbarian musketman sources

- Original painting: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/barbarian-musketman-source.png — project CC BY 4.0; external assets/barbarian-musketman, input hashes in inputs.json there.
- MPFB 2.0.18: https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18 — GPL software, CC0 generated anatomy/rig/weights. Installed external MakeHuman system eyes are CC0.
- Generated hidden-surface linen/coat/hair fills: original project CC BY 4.0 artwork, reused from mounted family; source prompt tools/art/anim3d/mounted/painted-fills.prompt.txt on the mounted branch. Existing provenance in assets/SOURCES.md.
- Quaternius Universal Animation Library, Standard glTF: https://quaternius.com/packs/universalanimationlibrary.html — CC0 1.0, also confirmed by its included LICENSE. Reused external assets/quaternius-ual/AnimationLibrary_Godot_Standard.gltf and .bin; exact bytes and licence pinned in motion.lock.json. Crouch_Idle_Loop, Crouch_Fwd_Loop, Hit_Chest and Death01 drive this unit's four non-attack clips. Source hierarchy/world rotations cancel bone rolls before Y-up conversion and forward alignment. Motion is constrained to a kneeling firing position, not presented as a standing walk. Only musket recoil/release are authored weapon motion.

Code is MIT; rendered art is project CC BY 4.0. No new downloads, paid services, accounts or hosted uploads in round 2.

Driver round 2 GPU follow-up reuses these unchanged painting, generated fill and motion assets.
Original inverse-skinned tailoring, contact adaptation, pigment/grain changes and frame-checkpoint
render orchestration are MIT source; rendered art remains CC BY 4.0. Prior mixed GPU/CPU evidence
is retained outside git under `masters/barbarian-musketman/driver-r1-gpu/`.

## Driver round 3, 2026-11-23

- Clean stone occlusion fill: built-in ImageGen `01a20ab4-8199-7490-8eff-da4ff8a7b69a/exec-792a2c3e-eef8-4902-a5ba-44523c95b73c.png`, original project CC BY 4.0, no public URL. Input: registered original musketman painting. External `assets/barbarian-musketman/stone-fill-source.png`; exact prompt in `stone-fill.prompt.txt`, SHA256 in `assets.lock.json`. Registered generated top with original lower rim on the actual beveled disc, live AO; image alpha never clips geometry.
- Reuses Medjay generated skin, built-in ImageGen `01a20671-5037-7490-a90a-decacb274446/exec-401b9b3e-9eef-48db-b965-0d53769ebddc.png`, original project CC BY 4.0, no public URL. Original prompt: painted warm skin, linen, hide and wood texture quadrants for a premium miniature, no text or insignia. Unchanged external copy `skin-fill.png`, tried during iteration and superseded by the unit-specific flesh fill below. Existing MPFB CC0 anatomy and Quaternius CC0 motion unchanged.
- Full-depth hooked feather, inverse-skinned sleeves, anatomical garment materials and view-dependent pigment fidelity: original MIT unit scripts / CC BY 4.0 renders. Incoming round2 GPU evidence retained in `masters/barbarian-musketman/driver-r2-gpu/`.

- Unit-specific buff/ivory/flesh/charcoal fill atlas: built-in ImageGen `01a20ab4-8199-7490-8eff-da4ff8a7b69a/exec-42f0fb55-dcb5-45e3-b9b2-53b7033e06cd.png`, original project CC BY 4.0, no public URL. External painted-fills-source.png, prompt painted-fills.prompt.txt, SHA256 assets.lock.json. Replaces the inappropriate horse-coat fur on buff garments and orange skin in exposed regions.
