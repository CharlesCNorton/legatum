# Barbarian crossbowman sources

- Original Legatum painting, project CC BY 4.0, 2026-11-22:
  https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/barbarian-crossbowman-source.png
  Source and generated linen hashes are pinned in `inputs.json`.
- MPFB 2.0.18, https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18 :
  GPL software; CC0 anatomy, macro targets, weights and game_engine skeleton.
  Existing MakeHuman CC0 system eyes and isolated install reused.
- Original generated mounted-family linen, 2026-11-22, project CC BY 4.0:
  `assets/horseman/fill-linen.png`; no public URL. Original prompt is retained in
  `painted-fills.prompt.txt`. Unseen cloth uses this painted fill with unit pigments.
- Quaternius Universal Animation Library Standard, 2025-06-10, CC0-1.0:
  https://quaternius.com/packs/universalanimationlibrary.html
  Immutable conversion:
  https://raw.githubusercontent.com/J-Ponzo/gltf-universal-animation-library/e24c23cf2a1323488a3faa226ea7ea21f644b73e/glTF/AnimationLibrary_Godot_Standard.gltf
  and adjacent `.bin`. Existing `assets/quaternius-ual/LICENSE` retained.
  `retarget.py` checks SHA256 of both inputs before importing. Uses Idle_Loop,
  Walk_Loop, Hit_Chest and Death01. Target/reference bone matrices compensate
  rest poses and rolls; feet are never rotated after retarget. Translation-only
  root/contact adaptation and a carrying-arm layer supplement source motion.
- Retarget/feet helpers adapted from project Tagmatic/arquebusier lanes (MIT).
  Original full-volume kit, crossbow-specific attack, projection, physical lighting,
  AO/curvature and delivery scripts: MIT code / CC BY 4.0 rendered art.
- Existing Blender 5.3.0 (GPL), Pillow 13.0.0 (MIT-CMU), FFmpeg. All assets and
  masters stay under `~/LegatumRuns/anim-pilot/`. No new download or paid service.

## Barbarian crossbowman driver round 3, 2026-11-23
- Clean stone occlusion plate: built-in ImageGen `01a20aaa-73c6-7d22-84f5-8fbedf3f9882/exec-965badca-30c0-4167-a289-6efca7f1faf1.png`, original project CC BY 4.0, no public URL. Input is the registered original painting. External assets/barbarian-crossbowman/stone-fill-source.png; exact prompt and SHA256 in unit scripts. Color textures the real beveled stone disc with live AO; alpha never controls geometry.
- Reuses generated Medjay skin (ImageGen `01a20671-5037-7490-a90a-decacb274446/exec-401b9b3e-9eef-48db-b965-0d53769ebddc.png`) and Tagmatic leather (ImageGen `01a20671-5064-7c72-a6fe-cf93cc86ea3d/exec-487c13de-dea1-48e2-adb2-76092f8dbbcd.png`), original project CC BY 4.0, no public URLs. Original prompts: painted skin/linen/hide/wood miniature swatches; crimson wool/weathered steel/scuffed leather/worn brass swatches. Local copies fill-skin.png and fill-leather.png hash-pinned in inputs.json.
- Reuses pinned MPFB CC0 anatomy and Quaternius CC0 motion. Closed weighted anatomical shoes, continuous sleeve selection, generated hidden pigments, sparse source pose reset and source-verified GPU handoff are original MIT scripts / CC BY 4.0 renders. Prior GPU evidence preserved under masters/barbarian-crossbowman/driver-r2-gpu. No third-party download.
