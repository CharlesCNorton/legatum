# Panzer round 1 sources

- Original Legatum panzer painting, project CC BY 4.0: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/panzer-source.png . Original source retained in `masters/panzer/`; full-resolution rest-camera UV projection on closed meshes, not a billboard.
- Original olive hidden-surface fill, project CC BY 4.0, reused from the artillery/vehicle lane: imagegen output `01a20674-c612-7411-9c8a-075f46e56d4c/exec-bdc68bad-f161-45e0-b0ec-31203ac453e8.png`, external `assets/tank/painted-olive.png`. Generated brushwork is blended with sand pigment for unseen camouflage; no new image-generation service or model.
- ambientCG Metal034 and Travertine001, 1K JPG, CC0-1.0: https://ambientcg.com/get?file=Metal034_1K-JPG.zip and https://ambientcg.com/get?file=Travertine001_1K-JPG.zip . Reused displacement scans, exact local bytes pinned in `assets.lock.json`.
- Blender 5.3.0, GPL software: https://www.blender.org/ . Pillow 13.0.0, MIT-CMU: https://pypi.org/project/pillow/13.0.0/ . Existing installations; no installs or accounts.
- Original closed panzer geometry and rigid mechanical keys; MIT scripts / CC BY 4.0 rendered art. Adapted from `astra/unit-anim-3d-vehicles` pipeline (project MIT). Mechanical track motion uses constant arc length and wheel angle = distance/radius. No people or animals appear, so CMU/Quaternius retargeting is inapplicable. No commercial motion, Mixamo or external model used.

Every downloaded/reused input has a SHA256 in `assets.lock.json`. Assets, masters and reviews remain outside git. See the external `assets/SOURCES.md` for the shared asset provenance history.

## Round 2

- New painted ochre wheel-face fill, original built-in ImageGen, project CC BY 4.0, no public URL. Generation `01a209c2-b900-7271-a45d-dfab232382e9/exec-a8735ac0-0e2b-4222-bab4-e83217d33216.png`; copied to `assets/panzer/painted-ochre.png`, SHA256 in `assets.lock.json`, exact prompt in `painted-ochre.prompt.txt`. Mapped onto full-depth rotating wheels and chipped rims; no replacement silhouette or baked wheel lighting.
