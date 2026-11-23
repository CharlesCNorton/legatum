# Cavalry sources

All downloaded/generated inputs and editable masters remain under
`~/LegatumRuns/anim-pilot/`. No paid service, account or upload is used.

- Painting: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/cavalry-source.png — original project CC BY 4.0. Registered to `cavalry-256.png`; frozen camera UV pigment on full-depth geometry, never a card or alpha-cutout mesh. Hashes in `assets.lock.json`.
- Quaternius Ultimate Animated Animal Pack, July 2021: https://quaternius.com/packs/ultimateanimatedanimals.html — CC0-1.0. Horse weighted mesh, skeleton and native Idle/Gallop/Idle_HitReact_Left/Death actions. Immutable mirror https://raw.githubusercontent.com/trebeljahr/quaternius-showcase/5b491b755c6d2aaa263aaaf8671b30b559a380a4/public/glb/animals_pack/Horse.glb ; SHA256 `fbddb2c97179eca896ec69c985cd9cc74540484510776c400df64e088e9f2414`. Source animation, not motion capture. Native synchronized gallop replaces independent per-leg retiming. No post-retarget foot rotation patch.
- Quaternius Universal Animation Library Standard, 2025-06-10: https://quaternius.com/packs/universalanimationlibrary.html — CC0-1.0. Existing immutable mirror https://raw.githubusercontent.com/J-Ponzo/gltf-universal-animation-library/e24c23cf2a1323488a3faa226ea7ea21f644b73e/glTF/AnimationLibrary_Godot_Standard.gltf and adjacent `.bin`; local LICENSE retained. glTF SHA256 `0ff075c7ad6855c5c2c37a171592ee8f0d6ab2f58259e2be77a9b63dd8027765`, bin `6e65377d81558333c4093dbb144a48fd19019343d82b1a3a7992a98ec0e0543c`, LICENSE `a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499`. All three checked before import. Sitting_Idle_Loop, Hit_Chest and Death01 supply reference/roll-compensated upper-body movement; the saddle constrains pelvis and legs. Original sabre attack, weapon release, contact/framing adaptations remain authored. This is a constrained retarget, not full-body mocap reproduction.
- MPFB 2.0.18: https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18 — GPL software; CC0 anatomy, targets, game_engine rig and weights. Existing MakeHuman system assets https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip — CC0 eyes and skin.
- Generated hidden-surface coat/linen/hair/bronze fills: original mounted-family built-in image generation, 2026-11-22, project CC BY 4.0; external `assets/horseman/painted-fills.png`, copied swatches in `assets/cavalry/`. No public generation URL; original prompt retained in `inherited-fills.prompt.txt`, exact swatch hashes in `assets.lock.json`.
- ambientCG Fabric030, Metal034 and Travertine001 1K JPG: https://ambientcg.com/ — CC0. Poly Haven brown_leather and fine_grained_wood: https://polyhaven.com/ — CC0. Exact download URLs/versions in external `assets/SOURCES.md` and `materials-manifest.json`.
- Existing Blender 5.3.0 https://www.blender.org/ — GPL software; Pillow 13.0.0 https://pypi.org/project/pillow/13.0.0/ — MIT-CMU; FFmpeg installed.

Original geometry, tailoring, UV projection, shader, animation and delivery code
is MIT; rendered artwork CC BY 4.0. `rider_motion.py` and the evaluated front/top
feet review are isolated adaptations of the inspected cataphract/keshig MIT
helpers. No other lane's files are edited.
