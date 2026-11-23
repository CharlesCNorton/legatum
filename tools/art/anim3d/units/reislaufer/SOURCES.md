# Reislaufer round 1 sources

All downloaded inputs and generated masters stay under `~/LegatumRuns/anim-pilot/`.
The exact painting/fill bytes are pinned by `inputs.lock.json`; motion and its included
licence are pinned by `motion.lock.json`. No paid assets, accounts or uploads.

| Input | Version and licence | Source |
| --- | --- | --- |
| Original reislaufer painting | Existing Legatum art, CC BY 4.0 | https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/reislaufer-source.png |
| MPFB anatomy, morphs and 53-bone game_engine weights | MPFB 2.0.18, GPL software; generated anatomy/rig assets CC0 | https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18 |
| MakeHuman system eyes | CC0 system pack | https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip |
| Quaternius Universal Animation Library Standard | 2025-06-10, CC0 1.0 | https://quaternius.com/packs/universalanimationlibrary.html |
| Immutable UAL glTF/bin mirror | Commit e24c23cf2a1323488a3faa226ea7ea21f644b73e, CC0 | https://raw.githubusercontent.com/J-Ponzo/gltf-universal-animation-library/e24c23cf2a1323488a3faa226ea7ea21f644b73e/glTF/AnimationLibrary_Godot_Standard.gltf and adjacent `.bin` |
| Generated linen, coat, hair and bronze fill quadrants | Original project CC BY 4.0, mounted family, 2026-11-22 | Existing external `assets/horseman/fill-*.png`; built-in imagegen, no public URL; exact original prompt in `fills.prompt.txt` |
| Blender / Pillow / FFmpeg | Installed Blender 5.3.0 GPL; Pillow 13.0.0 MIT-CMU; FFmpeg | https://www.blender.org/ / https://pypi.org/project/pillow/13.0.0/ / https://ffmpeg.org/ |

`Idle_Loop`, `Walk_Loop`, `Hit_Chest`, and `Death01` drive the four non-attack
clips. `A_TPose` supplies the standing limb reference; world hierarchy evaluation,
Y-up to Z-up conversion and reference matrices compensate bone rolls. Travel is -Y.
Carrying arms use a two-hand constraint, and stance-contact IK plus floor constraints correct foot placement. The death relaxes the carrying offsets into the captured terminal pose.
Only the two-handed pike attack and rigid pike release are authored weapon motion.
No Mixamo or hand-authored replacement walk.

Original MPFB fitting, breastplate, slashed clothing, beret, feather, belts, sword
and pike geometry: MIT scripts, CC BY 4.0 rendered art. Pipeline helpers adapted
from the inspected infantry and barbarian-musketman family work. The painting is
frozen onto finished 3D surfaces; it is never a billboard or silhouette mesh.
