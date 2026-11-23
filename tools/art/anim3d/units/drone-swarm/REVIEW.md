# Drone swarm round 2

Not art-approved; no PASS marker. Current evidence is Cycles CPU at 512 px,
12 samples, with 256 px copies. A host GPU pass is still required.

The stone now closely matches the warm painting and its deeper rim. Finished
bevelled surfaces preserve more projected brushwork; the lower formation and
rotor-pod positions are closer. At 256 px hull undersides, landing struts and
blade outlines remain visibly simpler. At 64 px this reads as the same three-drone
unit, but the contours remain distinguishable. Oblique/death views expose warm
fill seams and crowded overlapping wrecks. No near-identical-rest claim is made.

Silhouette intersection-over-union at alpha >128 improved from .7322 to .8060
for the full token; drones alone .6022 to .6609, base .8766 to .9675. These are
measurements of overlap, not artistic acceptance.

## Verified outputs

- Five clips, 8/8/10/4/10 frames; all 40 transparent masters at 512 and 256 px.
- Trimmed 160 px logical cells, **176,538 bytes at WebP quality 85**, lossless alpha.
  Every decoded alpha matches its source at the recorded offset. Held death
  reuses the same rectangle and is identical in decoded RGBA.
- Native 256/64 rest comparison, plain views, close-ups, rig poses, five strips,
  five animated WebPs, decoded atlas sheet and front/top move-cycle diagnostic.
- `drone-swarm-round2.mp4`: decoded clips, H.264/yuv420p, 1600 x 348,
  240 frames, eight seconds. Contact frames from the encoded movie inspected.
- Geometry audit passes: 163 solid meshes, finished projection UVs, camera-only
  pigment, six AO/Pointiness bakes, stationary base, clip-entry transforms, loop
  roots/gimbals and settled death contact. This is not a complete collision solver.
- Four delivery regression tests pass, including corrupted offsets/atlas and
  rejection of CPU evidence as GPU completion. GPU missing-input preflight
  returns exit 1 and records its failed stage, without launching Blender.

The browser art gate cannot run in this sandbox: using the installed main
checkout Playwright reaches Chromium but its macOS MachPort bootstrap fails
with Permission denied (1100). The initial direct invocation also lacked this
worktree's Playwright dependency. No browser/art gate pass is claimed.

## Host handoff

```sh
ROUND=2 tools/art/anim3d/units/drone-swarm/gpu.sh
```

The executable takes no arguments. It renders all stages at GPU512, exports
256 masters, audits, checks GPU provenance, packs/validates and verifies the
round movie. Defaults: Cycles Metal, 96 samples. It writes
`drone-swarm-gpu-round2.log` under ANIM_ROOT plus stage status and a success
receipt in review/3d-v2. Actual GPU execution remains unverified in the sandbox.

Prior evidence is preserved under `masters/drone-swarm/round1-cpu/`.
All masters/review media stay outside git. The runtime still uses the painting.
