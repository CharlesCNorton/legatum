# Artillery sources

- Original Legatum artillery painting, project CC BY 4.0:
  https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/artillery-source.png
  External `assets/artillery/painting-source.png`; registered to the committed 256px token.
  Frozen camera UVs on full-depth meshes. Input hashes in `masters/artillery/inputs.json`.
- Original generated olive paint, 2026-11-22, project CC BY 4.0. Built-in imagegen output
  `01a20674-c612-7411-9c8a-075f46e56d4c/exec-bdc68bad-f161-45e0-b0ec-31203ac453e8.png`;
  no public URL. External `assets/artillery/painted-olive.png`, prompt in `fills.prompt.txt`.
  Reused unchanged in rounds 2 and 3 for unseen surfaces; no new generation or download.
- Existing Blender 5.3.0 (https://www.blender.org/, GPL software), Pillow 13.0.0
  (https://pypi.org/project/pillow/13.0.0/, MIT-CMU), FFmpeg.
- Original hard-surface geometry, mechanical parent rig, motion keys, UVs and procedural/baked
  surface finish: unit scripts, MIT code / CC BY 4.0 rendered artwork. No third-party model.
  No crew or animals in the painting, so no mocap/retargeting asset applies. Front/top running-gear
  review is the mechanical equivalent of the feet check; no world-space travel-speed claim.

All assets, bakes and editable/512/256 masters remain under `~/LegatumRuns/anim-pilot/` outside git.

## Round 4

- Clean stone occlusion fill: built-in ImageGen 2026-11-23, original project CC BY 4.0,
  no public URL; generation `01a20a8c-fd93-7560-980e-3b541e6c9fec/exec-ae6d9595-d453-48e2-ac78-709ad38f0c0e.png`.
  Input: registered original artillery painting. External `assets/artillery/stone-fill-source.png`,
  SHA256 `733ccc70d0888268e3b07c468e7119f2183576d05721f1c7450bbdd82c7d2c87`;
  prompt in `stone-fill.prompt.txt`. Registered color on real beveled disc, with live contact AO.
- Continuous rubber pigment and non-rolling broad illumination derive from the same pinned painting;
  original MIT scripts, CC BY 4.0 renders. Existing olive fill reused; no third-party download.
