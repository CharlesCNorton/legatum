# Archer sources

All assets and masters remain under `~/LegatumRuns/anim-pilot/`. Scripts are
project MIT; original rendered art and paintings are project CC BY 4.0.

- Painting: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/archer-source.png
  (original Legatum CC BY 4.0). Full master and frozen projection in
  `assets/archer/`; hashes in `assets.lock.json`.
- MPFB 2.0.18: https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18
  (GPL software, CC0 anatomy/morphs/weights/game_engine skeleton). Existing
  MakeHuman CC0 eyes and skin; ambientCG Fabric030 CC0 cloth weave.
- Existing mounted-family generated linen/bronze/leather fills, 2026-11-22,
  original project CC BY 4.0; no public URL. `reused-fills.prompt.txt` records
  the prompt; `assets.lock.json` pins the retained copies. No new generation.
- Quaternius Universal Animation Library Standard, 2025-06-10, CC0 1.0:
  https://quaternius.com/packs/universalanimationlibrary.html . Immutable mirror:
  https://raw.githubusercontent.com/J-Ponzo/gltf-universal-animation-library/e24c23cf2a1323488a3faa226ea7ea21f644b73e/glTF/AnimationLibrary_Godot_Standard.gltf
  and adjacent `.bin`. Existing `assets/quaternius-ual/LICENSE` retained.
  `retarget.py` verifies both SHA256 hashes before import. Uses Idle_Loop,
  Walk_Loop, Hit_Chest and Death01. Rest/roll-compensated Blender constraints;
  no foot rotation edits after retargeting. Bow attack remains original.
- Retarget helper adapted from project rifleman lane, MIT, inspected at
  `astra/unit-anim-3d-rifleman`; archer-specific guard/fall sampling and contact.
- Existing Blender 5.3.0, Pillow 13.0.0, FFmpeg. No paid services, accounts,
  downloads, external hosting or Mixamo.

Previous rounds used CMU 77_02 standing and 02_01 walk (permissive CMU motion),
retained in the archived evidence. The current four open clips replace them.
