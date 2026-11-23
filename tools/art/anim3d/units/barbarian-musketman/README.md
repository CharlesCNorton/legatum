# Barbarian musketman — round 3 candidate

Run commands from the repository root. `gpu.sh` is the no-argument overnight handoff; it requires
Metal Cycles, takes `ROUND` from the environment, and executes the complete build/render/pack pass.

- `prepare.py`: hash-verified sources, painting registration and generated hidden-surface material plates.
- `scene.py`: MPFB anatomy, kneeling rig, tailored kit, frozen projection, authored clips, render and audit.
- `refine.py`: full-depth hat fitting, continuous sleeve weights, garment underlayers, hidden-pigment shading and UV audit.
- `motion.py`: pinned CC0 Quaternius motion with kneeling contact/weapon constraints.
- `bake.py`: six actual 512 px AO/Pointiness maps on coat, hat and stock.
- `finish.py`: review sheets, a fixed rest-derived grade, genuine 512/256 masters, trimmed 160 px atlas,
  hash/alpha/clip/size checks, and eight-second MP4 with reconstructed trim offsets and extracted movie frames.
- `render.sh`: gated Blender entry point for individual CPU/GPU stages.
- `render_frames.py`: fresh-process final frames with hash-bound resumable checkpoints and bounded
  SIGTRAP retry; `test_render_frames.py` verifies interrupted and stale-frame recovery in isolation.

The painting remains in the game. This is an art candidate, not a runtime renderer change or art
approval. Masters and source assets are outside git. See the unit chapter in `../../PLAYBOOK.md`
for the atlas format and the external review folder for the honest round verdict.
