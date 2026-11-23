# Biplane sources

- Original Legatum biplane painting, CC BY 4.0:
  https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/biplane-source.png
  External copy: `assets/biplane/painting-source.png`. Frozen UV pigment on complete meshes.
- Original generated painted linen, olive, wood and rubber fills, CC BY 4.0.
  Built-in imagegen output `01a20674-ccc7-7801-b652-5ed731e79f9f/exec-aec3a6e3-9c7a-48fc-afd5-65ed8dfc9a4a.png`;
  prompt: `fills.prompt.txt`; external `assets/biplane/painted-fills.png`. No public URL.
- Original airframe, rig and mechanical flight/propeller/crash keys: these unit scripts,
  MIT source / CC BY 4.0 rendered output. No human or animal appears, so CMU/Quaternius
  locomotion and skeletal retargeting are inapplicable. Top/front landing gear review
  is `biplane-g-feet-check.png`; wheels are airborne and aligned to the flight axis.
- Existing Blender 5.3.0, GPL software: https://www.blender.org/ .
  Existing Pillow 13.0.0, MIT-CMU: https://pypi.org/project/pillow/13.0.0/ .

Round 2 adds no download, model or image-generation call. External `inputs.json`
pins every painting/fill PNG by SHA256; `build-inputs.json` pins geometry/paint scripts
and the saved master. Full asset ledger: `~/LegatumRuns/anim-pilot/assets/SOURCES.md`.
