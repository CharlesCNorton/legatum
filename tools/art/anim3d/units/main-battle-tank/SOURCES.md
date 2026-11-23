# Main battle tank — round 1

- Reference and projected pigment: existing Legatum painting, CC BY 4.0, retrieved 2026-11-23 from https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/main-battle-tank-source.png . Prompt: `app/src/assets/units/prompts/main-battle-tank.prompt.txt`; later cream-base edit beside the token. Exact source SHA256 in `assets.lock.json`. Master stays in `ANIM_ROOT/masters/main-battle-tank/`.
- Hidden-surface painted olive fill: existing original project artwork generated with OpenAI imagegen, 2026-11-22, generation `01a20674-c612-7411-9c8a-075f46e56d4c/exec-bdc68bad-f161-45e0-b0ec-31203ac453e8.png`, no public URL. Project CC BY 4.0. Reused `assets/tank/painted-olive.png` (artillery family original); pinned in `assets.lock.json`.
- Metal034 1K displacement: https://ambientcg.com/get?file=Metal034_1K-JPG.zip ; CC0-1.0. Existing external asset; microstructure beneath painted pigment.
- Travertine001 1K displacement: https://ambientcg.com/get?file=Travertine001_1K-JPG.zip ; CC0-1.0. Existing external stone grain.
- Blender 5.3.0, existing open-source installation; Pillow 13.0.0 and FFmpeg, existing local tools. No paid service or new model download.
- Pipeline adapted from `astra/unit-anim-3d-vehicles` (MIT project code): frozen camera projection, actual AO/Pointiness bakes, closed track route, grade, trimmed delivery, validation and movie encoding. Unit-specific model, fitting and mechanical animation are original MIT code; rendered artwork CC BY 4.0.
- Motion: rigid tracked vehicle; no people or animals to retarget. Track arc-length travel and wheel travel/radius replace gait; turret traverse, recoil, impact and wreck are authored mechanical motion. No Mixamo or external motion asset.

Vehicles reference revision inspected for this round: `0b2616f595e964a79641689ec26d31d2ed56cd28`.

Round 2 (2026-11-23): reuses the same hash-locked painting, generated olive fill
and CC0 scans; no new download. Original roof/deck fitting, folded canvas/webbing,
stationary wheel-light coordinates and revised mechanical effects are MIT code;
new renders remain CC BY 4.0.
