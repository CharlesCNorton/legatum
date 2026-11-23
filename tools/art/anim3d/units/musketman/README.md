# Musketman round 2

True 3D MPFB anatomy, 53-bone rig, folded buff coat, red breeches and sash,
cream stockings, boots, felt hat/feather, charge bandolier, carved musket and
socket bayonet. The original painting supplies frozen camera-projected colour
on finished geometry, with generated painted fills on unseen surfaces. Real
AO/Pointiness bakes drive hidden-surface grime/roughness. The cream stone base
is physical and never receives painted feet.

Run from the repository root:

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/musketman/prepare.py
SAMPLES=8 RESOLUTION=512 tools/art/anim3d/units/musketman/render.sh build
SAMPLES=8 RESOLUTION=512 tools/art/anim3d/units/musketman/render.sh animate
SAMPLES=8 RESOLUTION=512 tools/art/anim3d/units/musketman/render.sh render
tools/art/anim3d/units/musketman/render.sh audit
ROUND=2 "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/musketman/finish.py pack
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/musketman/test_delivery.py
```

The required no-argument host entry point is:

```sh
ROUND=2 tools/art/anim3d/units/musketman/gpu.sh
```

It rebuilds, bakes, retargets, renders all stages with Cycles Metal GPU at 512 px,
one frame per fresh gated Blender process,
keeps genuine 512/256 masters, packs/validates the trimmed 160 px delivery,
regenerates all review images and the eight-second H.264 movie, runs delivery
regressions and writes a hash-bound GPU receipt. GPU absence is an error. Logs,
status, stages and external masters are unit-specific. No PASS is issued by the
script: visual approval is separate from technical validation.

Motion comes from pinned CC0 Quaternius idle/walk/hit/death, evaluated in source
hierarchy order and retargeted with full reference-pose rotations including
bone rolls. Forward is +X. The carrying arm layer uses captured idle; the left
hand is constrained to the solid gun. Only the firing recoil is authored.
Locomotion thighs/calves calibrate to A_TPose; feet calibrate to the flat boot
rest, avoiding the mistake of matching an ankle-to-ball bone axis while tipping
the boot. There are no per-frame foot orientation corrections. Floor contact
is vertical root translation. The hit samples the captured motion outward and back to guard; the final two
death samples are held.

See `REVIEW.md` for observed limitations. Runtime activation, GPU sign-off and
Claude art review remain with the lead.

Round-one GPU rendering trapped during attack; later strips/movie from that
round were older CPU output. The revised handoff disables persistent render
caches and checkpoints each frame against blend/renderer/settings/PNG hashes.
An incomplete stage has no render manifest. The observed SIGTRAP is retried
once; other errors remain failures. The root cause and Metal recovery are not
claimed verified by CPU checks. To resume rendering unchanged masters/settings:

```sh
CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=48 tools/art/anim3d/units/musketman/render.sh render
```

That resume command only renders; `gpu.sh` performs the entire rebuild, render,
pack, validation and video handoff. No script writes a PASS marker.
