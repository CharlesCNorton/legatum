# Knight round 2

Run from the repository root. The complete lead-side command is:

```sh
ROUND=2 tools/art/anim3d/units/knight/gpu.sh
```

No arguments. Requires the already-installed isolated MPFB resources and pinned
external sources. It fails before rebuilding if Metal or a source is unavailable.
All Blender calls use the machine's plain `blender` PATH gate, serially.

The pipeline builds real geometry and rigs, freezes projection UVs from the
original painting, samples licensed horse and rider motion, and renders all
review stages at GPU 512 px/64+ samples. It creates 512/256 masters, trimmed
160 px WebP/JSON, byte/quality/alpha/hash validation and a verified eight-second
five-clip H.264 movie. See the knight chapter in `../../PLAYBOOK.md` for the
format and CPU stage commands, and `SOURCES.md` for licences.

External artifacts:

- `~/LegatumRuns/anim-pilot/masters/knight/`: editable base/plain/sculpted/painted blends,
  five clip blends, raw renders, 512/256 masters, source-motion samples and
  render/pack/validation/audit/movie receipts.
- `~/LegatumRuns/anim-pilot/review/3d-v2/knight-*`: every interim stage, clip
  strips/WebPs, rest comparison, feet check, round MP4 and running log.

This is a candidate. No runtime activation or PASS is implied. The current CPU
images have 8 samples; the complete Metal pass must be run on the lead's host.
The fitted helmet, glove, shorter caparison, projected tail and stone rim improve
the rest pose. Thin lower legs, rear-drape coverage and the rigid collapsed cloth
still fall short of the painting. Cloth is
bone-driven, not simulated. Gait targets and feet views are recorded; the audit
does not claim to prove foot-slide freedom or full collision freedom.
