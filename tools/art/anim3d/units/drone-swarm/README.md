# Drone swarm — round 2 candidate

Original true 3D miniature: three bronze drone shells, six motor pods and solid
propellers, three optical gimbals, one cream base. No runtime code changes.

The executable GPU handoff, from the repo root:

```sh
ROUND=2 tools/art/anim3d/units/drone-swarm/gpu.sh
```

It renders all stages with Metal Cycles at 512 px, retains 256 masters, writes the
review sheets and animated WebPs, packs the trimmed 160 px atlas, audits/validates,
and encodes the required 8-second five-clip review MP4. It also renders front/top
move diagnostics and retains a transcript, stage status and GPU completion receipt. `ROUND` defaults to 2 and
`SAMPLES` to 96. It refuses GPU-to-CPU fallback. Every invocation uses the PATH
`blender` gate in background mode with automatic Python execution disabled.

Sources are already prepared under `~/LegatumRuns/anim-pilot/assets/drone-swarm/`.
`assets.lock.json` pins the full painting and reused generated hidden-surface fill;
`fill.prompt.txt` preserves that fill's original prompt. Rebuild instructions,
source licences and the exact version-2 atlas contract are in SOURCES.md and the Vehicles / drone
chapter of `../../PLAYBOOK.md`. Never rebuild just to rerender: a rebuild requires
new bakes and all downstream render/grade/pack stages.

External deliverables live under `masters/drone-swarm/` and `review/3d-v2/`.
CPU previews are evidence of the current candidate, not host GPU or art approval.
See `REVIEW.md` for observed quality and check results. Only a human/lead visual
judgment of near-identical rest pose and clean motion may create the external
`drone-swarm-PASS` marker; scripts deliberately never create it.
