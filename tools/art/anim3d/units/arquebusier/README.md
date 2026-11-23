# Arquebusier round 1

Editable MPFB human, original three-dimensional Renaissance kit and five authored
skeletal clips. The existing painting remains the in-game unit. This is a review
candidate, not an approved replacement.

The infantry / arquebusier chapter in `../../PLAYBOOK.md` documents construction,
projection, bakes, clip timings and the version-2 atlas rectangle format.

- `scene.py`: reproducible anatomy, model, materials, rig, frozen-camera projection,
  action keys and stage rendering. `touchup` reapplies the final shoe/base fix to an
  existing master; the normal `build` already includes those fixes.
- `prepare.py`: full-resolution source registration and generated-fill extraction.
- `bake.py`: six actual 256 px AO/Pointiness maps.
- `finish.py`: fixed measured colour grade, review sheets, 160 px trimmed atlas,
  decoded validation and eight-second five-clip H.264 MP4.
- `audit.py`: anatomical topology, bones, nondegenerate scales, stationary base,
  motion, loop endpoints and held terminal death. It does not prove collisions.
- `render.sh`: sequential CPU stages. All Blender invocations use the PATH gate.
- `gpu.sh`: no-argument GPU handoff, run from the repository root with `ROUND` set.

External assets: `~/LegatumRuns/anim-pilot/assets/arquebusier/` (including the
built-in-imagegen `painted-fills.png`, prompt in `fills.prompt.txt`). Licences and
original output ID are in `assets/SOURCES.md`. Masters and raw/graded renders:
`~/LegatumRuns/anim-pilot/masters/arquebusier/`. Reviews and honest iteration log:
`~/LegatumRuns/anim-pilot/review/3d-v2/arquebusier-*`.

GPU handoff:

```sh
ROUND=1 tools/art/anim3d/units/arquebusier/gpu.sh
```

The host pass creates native 512 px masters and 256 px derivatives, replaces all
stage reviews, repacks the candidate atlas, validates it and writes the round MP4.
GPU appearance must be judged again. This script never writes a PASS marker.

Round 1's main remaining visual gaps are facial likeness and morion shape,
projection registration on slashed cloth, synthetic folds, and shoulder/weapon
contact during the attack. The death reaches a held sideways pose but its contact
and body mechanics still need refinement. At 64 px the red/cream costume and upright
matchlock identify the unit; at 256 px the painting remains visibly richer.

Implementation notes: MPFB's eye import may purge unused materials, so create kit
materials after importing eyes. Set explicit Euler modes before applying authored
Euler deltas to MPFB pose bones, preserving their rest matrices. Keep low-alpha
Lanczos fringes intact and validate visible coverage separately. WebP method 5
fit this round at 199,554 bytes/q75; method 4 missed the cap by 1,954 bytes. The
packer records its encoding attempts and never lowers quality below 75.
