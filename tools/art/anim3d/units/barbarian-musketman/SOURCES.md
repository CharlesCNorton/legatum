# Barbarian musketman sources

- Original painting: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/barbarian-musketman-source.png — project CC BY 4.0; external assets/barbarian-musketman, input hashes in inputs.json there.
- MPFB 2.0.18: https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18 — GPL software, CC0 generated anatomy/rig/weights. Installed external MakeHuman system eyes are CC0.
- Generated hidden-surface linen/coat/hair fills: original project CC BY 4.0 artwork, reused from mounted family; source prompt tools/art/anim3d/mounted/painted-fills.prompt.txt on the mounted branch. Existing provenance in assets/SOURCES.md.
- Quaternius Universal Animation Library, Standard glTF: https://quaternius.com/packs/universalanimationlibrary.html — CC0 1.0, also confirmed by its included LICENSE. Reused external assets/quaternius-ual/AnimationLibrary_Godot_Standard.gltf and .bin; exact bytes and licence pinned in motion.lock.json. Crouch_Idle_Loop, Crouch_Fwd_Loop, Hit_Chest and Death01 drive this unit's four non-attack clips. Source hierarchy/world rotations cancel bone rolls before Y-up conversion and forward alignment. Motion is constrained to a kneeling firing position, not presented as a standing walk. Only musket recoil/release are authored weapon motion.

Code is MIT; rendered art is project CC BY 4.0. No new downloads, paid services, accounts or hosted uploads in round 2.
