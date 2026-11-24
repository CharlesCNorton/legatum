# Driver round 3 evidence

**Candidate; no PASS.** The incoming round-2 GPU pass succeeded: 40 native
GPU512 frames, Q80, 187,628 bytes. Source, renders and review evidence are
preserved in external `masters/barbarian-scout/driver-r2-gpu/`.

Round 3 refits the true skull, palms/fingers and bind bones, restores the open
space beneath the salute, preserves continuous source hair brushwork, and fixes
a dependency-graph ordering bug that discarded the stone's scale/translation.
New original ImageGen cloth and stone occlusion plates are hash-pinned with
prompts and licences; they color real garment/base geometry. The generated cloth
replaces ghost hand/axe pigment on underlying shirt, tunic and trousers.

The authored axe attack uses a two-bone draw/backswing/descending cut with a
measured haft grip and a shortened arc to preserve frame margins. Quaternius
CC0 idle/move/hit/death remain; physical boot support drives contact translation
without correcting source foot rotations. All six Sam Blender skills were used.

Final CPU evidence: native 256 px, Cycles, 16 samples.

- All 40 frames, 8/8/10/4/10. Trimmed160 atlas **180,348 bytes, quality 80**.
- Atlas validation passes: source/clip/grade/frame hashes, render settings,
  rectangles/offsets, exact decoded alpha, margins, motion and held death.
- Blender audit passes: 53 bones, anatomy, garment exclusions, motion provenance,
  six AO/Pointiness bakes, positive scales, stationary base, closed loops,
  grip below 2mm, and both independently rendered held-death frames.
- All 16 boot samples clear stone: minimum sole z 0.09599975m against a 0.095m
  top. Contact height is not proof of a convincing gait.
- Three delivery regressions pass; 12 Python scripts parse; three Bash scripts
  pass syntax; executable GPU handoff and whitespace check pass.
- MP4: H.264/yuv420p, 1600x348, 240 frames, 8.000 seconds. Opened eight decoded
  frames, all five strips, decoded atlas, plain views, rest256/64 and feet sheet.

At **256 px**, the face/hair highlights, open salute gap, base dimensions and
revealed cloth improve. The actual lower palm/fingers remain small/fragmentary
and poorly aligned; wrist/cuff anatomy, cloth depth/seams and pelt outline still
miss the painting. At **64 px**, the same fur/horn/red-scarf lookout reads, but
silhouette and lower-hand/cloth mass remain distinguishable. Movement is a
constrained shuffle with pronounced foot roll; the attack needs better weight
transfer and finger grip; death exposes stretched pigment and fallback seams.
These are not five clean approved clips. No PASS marker was written.

Current CPU evidence is retained in `driver-r3-cpu/`. Incoming native GPU512
masters remain in `driver-r2-gpu/512`; CPU256 was never upscaled to512.
No runtime, UI or rules changed, so engine tests do not apply. Supplied
`origin/master` is already an ancestor; no merge was required.

The executable no-argument host handoff rebuilds/bakes/retargets, audits, renders
all stages and feet on Metal Cycles, keeps native512/gallery256, packs/validates,
and writes decoded-atlas reviews and the eight-second MP4. Round-3 GPU rendering
is pending the lead; the sandbox CPU checks are not GPU verification:

```sh
ROUND=3 tools/art/anim3d/units/barbarian-scout/gpu.sh
```
