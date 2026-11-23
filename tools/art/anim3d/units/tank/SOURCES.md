# Tank animation sources

- Original Legatum tank painting, project CC BY 4.0: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/tank-source.png . Full master is external at `masters/tank/tank-source.png`; frozen rest-camera UVs on closed 3D geometry. `assets.lock.json` pins the bytes.
- Painted olive hidden-surface fill: original project image generation, 2026-11-22, CC BY 4.0, reused from the artillery lane. Generation `01a20674-c612-7411-9c8a-075f46e56d4c/exec-bdc68bad-f161-45e0-b0ec-31203ac453e8.png`; no public URL. External `assets/tank/painted-olive.png`, hash in `assets.lock.json`. No new generation this round.
- Metal034 and Travertine001, ambientCG CC0-1.0, existing 1K packs: https://ambientcg.com/get?file=Metal034_1K-JPG.zip and https://ambientcg.com/get?file=Travertine001_1K-JPG.zip . Original steel/stone pigment over scan microstructure.
- Existing Blender 5.3.0 (https://www.blender.org/, GPL software), Pillow 13.0.0 (https://pypi.org/project/pillow/13.0.0/, MIT-CMU), FFmpeg. Original geometry, mechanical rig and scripts: MIT; rendered artwork: CC BY 4.0.

This unit contains no human or animal gait. Its motion is mechanical: arc-length track travel, wheel travel/radius, turret traversal, recoil and suspension. `tank-g-feet-check.png` provides actual top/front geometry views over all eight move samples. No mocap is used or claimed. Assets, bakes and masters stay under `~/LegatumRuns/anim-pilot/`.
