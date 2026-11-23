# Jet bomber sources

- Original Legatum jet-bomber painting, source version downloaded 2026-11-23:
  https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/jet-bomber-source.png
  Project artwork, CC BY 4.0. Frozen camera projection on actual meshes; existing
  `jet-bomber-256.png` is the comparison target. No insignia added.
- Unseen olive surface fill: reused original project imagegen artwork from the
  bomber lane, generation `01a20674-cc7c-7391-9ed5-eaf3529562ff/exec-71c71165-4b96-4204-bead-5802066e70f1.png`.
  CC BY 4.0, no public URL. Original prompt at
  `astra/unit-anim-3d-bomber:tools/art/anim3d/units/bomber/fill.prompt.txt`;
  copied from `assets/bomber/painted-fill.png` into `assets/jet-bomber/`.
- Blender 5.3.0, build `02f0899d78e3`, https://www.blender.org/, GPL-3.0-or-later;
  existing open-source installation. Pillow 13.0.0, https://python-pillow.org/,
  HPND, existing external venv. FFmpeg, https://ffmpeg.org/, existing installation.
- Original code-built closed aircraft lofts, intake tunnels, vanes, support and
  mechanical motion: MIT scripts; rendered artwork CC BY 4.0. Reused and adapted
  bomber-family orchestration and vehicles-family trimmed-atlas conventions.
- No human/animal animation asset is applicable: rigid airborne aircraft has no
  gait or feet. Idle/bank, flight, bombing pass, hit and crash are authored
  mechanical keys. No Mixamo, paid model, account, or external animation service.

`inputs.json` pins both consumed source images by SHA256. Masters, packed images,
AO/curvature bakes and previews remain under `~/LegatumRuns/anim-pilot/`.
