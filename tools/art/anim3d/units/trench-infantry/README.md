# Trench infantry round 1

Candidate, not art-approved. Run all commands from the repo root. External inputs,
licences and immutable hashes are in SOURCES.md and assets.lock.json.

```sh
RESOLUTION=256 SAMPLES=4 tools/art/anim3d/units/trench-infantry/render.sh build
tools/art/anim3d/units/trench-infantry/render.sh animate
RESOLUTION=256 SAMPLES=4 tools/art/anim3d/units/trench-infantry/render.sh preview
tools/art/anim3d/units/trench-infantry/render.sh feet
tools/art/anim3d/units/trench-infantry/render.sh pack
ROUND=1 tools/art/anim3d/units/trench-infantry/gpu.sh
```

The last command is the no-argument GPU handoff: rebuild, all stage renders,
512/256 masters, feet, structural audit, 160px trimmed WebP/JSON, validation,
rest comparison and eight-second decoded-atlas movie. It requires Metal Cycles;
there is no silent CPU fallback. CPU renders are preview evidence only.

The original painting remains active in the game. The atlas is an unapproved
candidate with no runtime changes. Review the external log and rest/clip/feet
sheets before continuing; do not infer art approval from validation.json.

Known round-one gaps: overly squared shoulder/pack contours, narrow and stiff
coat drape, visible projection/fill transitions as the figure turns or falls,
and a fall that needs better coat and equipment contact. No PASS marker.

Round-one technical evidence: 40 frames at 512 and 256; 160px atlas 182,822 bytes
at quality 90; lossless alpha reconstruction and held-death checks pass. Movie is
H.264/yuv420p, 1600x348, 240 frames / 8 seconds. All preview renders use Cycles CPU
at four samples. Feet stay within 9.94 degrees of forward; the audit checks
planted intervals against virtual ground speed with a 15mm limit. These checks
do not establish that the coat or released rifle has no collisions.

Python/Bash syntax and whitespace checks pass. Repository hygiene and public
claims pass; the Chromium art gate is blocked by sandbox MachPortRendezvous
permission denial. No Rust, gameplay or UI code changed.
