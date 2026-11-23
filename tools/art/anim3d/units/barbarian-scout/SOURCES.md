# Barbarian scout sources

All raw assets and masters remain under `~/LegatumRuns/anim-pilot/`. Scripts are
MIT; original project paintings, generated fills and rendered art are CC BY 4.0.

- Original painting: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/barbarian-scout-source.png . Existing project CC BY 4.0; source and registered projection retained in `assets/barbarian-scout/`. Source prompt: `app/src/assets/units/prompts/barbarian-scout.prompt.txt`; base revision: `barbarian-scout.art-pass-3.prompt.txt`.
- MPFB 2.0.18: https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18 . GPL software; body, morphs, game_engine rig and weights CC0. MakeHuman system assets: https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip , CC0. Existing isolated install.
- Quaternius Universal Animation Library Standard, 2025-06-10, CC0-1.0: https://quaternius.com/packs/universalanimationlibrary.html . Immutable mirror: https://raw.githubusercontent.com/J-Ponzo/gltf-universal-animation-library/e24c23cf2a1323488a3faa226ea7ea21f644b73e/glTF/AnimationLibrary_Godot_Standard.gltf and adjacent `.bin`. Existing local LICENSE; all three hashes checked against `motion.lock.json`. Crouch_Idle_Loop, Crouch_Fwd_Loop, Hit_Chest and Death01 drive reference-pose world rotation deltas with full source hierarchy and bone roll cancellation. The scout retains kneeling contact constraints, a constrained lead-foot shuffle and contact-driven death cloth folds. This is an adapted retarget, not full-body mocap reproduction. No post-retarget foot yaw edits. Axe attack is authored.
- `motion.py` is an isolated MIT snapshot of the barbarian-musketman lane's sampler, adapted to the scout's -Y travel axis. It reads the glTF data; it executes no downloaded code.
- Original painted fur: built-in OpenAI imagegen, 2026-11-22, project CC BY 4.0, no public URL. `assets/barbarian-scout/painted-fur.png`; exact prompt and hash in external `sources.json`.
- Original linen fill: existing mounted-family imagegen, 2026-11-22, project CC BY 4.0; copied from `assets/horseman/fill-linen.png`. Original prompt: four-quadrant painted coat/linen/bronze/hair texture for premium historical miniatures, subtle brushwork, no objects/text/insignia. Provenance in `assets/SOURCES.md`.
- Original skin fill: existing Medjay imagegen, 2026-11-22, output `01a20671-5037-7490-a90a-decacb274446/exec-401b9b3e-9eef-48db-b965-0d53769ebddc.png`, project CC BY 4.0. Copied `assets/medjay/fill-skin.png` into unit `painted-skin.png`.
- Original hair/leather fills: existing barbarian-archer imagegen, 2026-11-22, output `01a20670-76eb-7280-89dc-f54424a9d280/exec-a51d4d39-ffaa-4427-96fb-173d9ba6fdb2.png`, project CC BY 4.0. Copied `fill-hair.png`/`fill-leather.png` into unit assets. Original four-swatch fur/linen/leather/hair prompt and provenance are in that lane and `assets/SOURCES.md`. No new image generation or asset download this round.
- Blender 5.3.0 https://www.blender.org/ , GPL software; Pillow 13.0.0 https://pypi.org/project/pillow/13.0.0/ , MIT-CMU; installed FFmpeg. Every Blender call goes through plain `blender -b` on PATH.

`assets.lock.json` pins all unit texture inputs; `prepare.py` rejects changed
inputs and writes external source metadata. Native GPU512 evidence from driver
round 1 is preserved in `masters/barbarian-scout/driver-r1-gpu/`.
