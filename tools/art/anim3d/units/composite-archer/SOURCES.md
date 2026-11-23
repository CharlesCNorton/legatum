# Composite archer sources

- MPFB 2.0.18 / MakeHuman body and game_engine rig: CC0 output; existing install
  https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18 .
- Original Legatum painting: CC BY 4.0,
  https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/composite-archer-source.png .
- Original four-part generated fills: project CC BY 4.0; generation
  01a2066f-01e7-74a3-a104-3aa0d38acf0c, prompt `painted-fills.prompt.txt`.
- Original generated face occlusion fill: project CC BY 4.0; generation
  01a20912-a0ec-7f03-9a78-d8a012419a85, prompt `face-fill.prompt.txt`.
  Both generated assets have no public URL and remain in external assets/.
- Quaternius Universal Animation Library Standard, 2025-06-10, CC0-1.0:
  https://quaternius.com/packs/universalanimationlibrary.html . Immutable mirror:
  https://raw.githubusercontent.com/J-Ponzo/gltf-universal-animation-library/e24c23cf2a1323488a3faa226ea7ea21f644b73e/glTF/AnimationLibrary_Godot_Standard.gltf
  and adjacent `.bin`. Local `assets/quaternius-ual/LICENSE` retained.
  Crouch_Idle_Loop, Crouch_Fwd_Loop, Hit_Chest, Death01; Idle_Loop carrying-arm layer.
  SHA256 glTF `0ff075c7ad6855c5c2c37a171592ee8f0d6ab2f58259e2be77a9b63dd8027765`;
  bin `6e65377d81558333c4093dbb144a48fd19019343d82b1a3a7992a98ec0e0543c`;
  licence `a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499`.
  Verified before import. Retarget adapted from inspected barbarian-archer helper;
  source-reference world rotations cancel source rest/roll before applying target
  kneeling reference. No manual foot-rotation patches. Translation-only floor
  support remains. This is adapted open motion, not unmodified motion capture.
- Original full-depth costume/bow and attack keys: MIT scripts, CC BY 4.0 renders.
  No new external download, account, paid service or deployment.
