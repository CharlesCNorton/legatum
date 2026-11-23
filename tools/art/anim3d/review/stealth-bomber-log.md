Round 1 started: read project art instructions, six Blender skills, standing feedback 1–23, sources and vehicles/bomber family implementation.
Skills applied: modeling closed cambered hull and bevels; materials frozen projection/grey brushwork/AO wear; camera matched token registration; warm key/cool rim lighting; rigid flight and crash animation; gated Cycles previews and explicit GPU handoff.
Source helper returned 403; direct curl retrieved the original alpha master. No external model or human/animal motion needed for this aircraft.
b: 3 frames at 256/64 from 256px CYCLES/CPU, 6 samples.
c: 1 frames at 256/64 from 256px CYCLES/CPU, 12 samples.
b: 3 frames at 256/64 from 256px CYCLES/CPU, 12 samples.
c: 1 frames at 256/64 from 256px CYCLES/CPU, 12 samples.
d: 4 frames at 256/64 from 256px CYCLES/CPU, 12 samples.
e-idle: 8 frames at 256/64 from 256px CYCLES/CPU, 12 samples.
e-move: 8 frames at 256/64 from 256px CYCLES/CPU, 12 samples.
e-attack: 10 frames at 256/64 from 256px CYCLES/CPU, 12 samples.
e-hit: 4 frames at 256/64 from 256px CYCLES/CPU, 12 samples.
e-death: 10 frames at 256/64 from 256px CYCLES/CPU, 12 samples.
Initial b/c sheets published immediately, preserved in stealth-bomber-round1-initial/. Plain view exposed shallow intakes; boolean-cut actual wells and raised the convex canopy before clips.
Five clips rendered CPU256/12. Geometry audit passed closed airframe, fixed base, loop closure and final wreck contact. Packing correctly rejected death frame 3 touching the left edge; reducing bank and adding translation-only camera margin constraints.
Sampled base against painting: rendered top about (225,192,155) versus painting (241,210,183). Raised physical limestone palette before frozen histogram grading; no alpha or geometry silhouette masking.
b: 3 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
c: 1 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
d: 4 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-idle: 8 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-move: 8 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-attack: 10 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-hit: 4 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
Round 1 final CPU checkpoint: all 64 stage frames rendered at actual 512 px / 12 samples, with verified 512/256 derivatives. Trimmed atlas 194,946 bytes Q95, all 40 clip frames; alpha reconstruction, gutters, clipping, hashes and terminal death hold pass.
Independent Blender geometry/rig audit passes all five clips: closed principal volumes, stationary base, loop closure, real motion and terminal wreck/base contact. Five delivery regression tests pass; H.264/yuv420p MP4 verified 1600x348, 240 frames, 8 seconds. Decoded video sample and full clip sheets inspected.
Visual verdict: same unit at 64 px; close rest silhouette/detail at 256 px but softer canopy/intakes, slightly pink support, too-uniform stone and restrained crash. Rest alpha IoU .96135 / overlap RGB MAE 6.47 are measurements, not approval. No PASS. GPU96 pass remains lead-side via units/stealth-bomber/gpu.sh.
Commit attempt blocked: git could not create .git/worktrees/lane-1/index.lock (Operation not permitted). Changes left uncommitted for runner; requested commit message: Add stealth bomber round-one 3D animation candidate; trailer Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>. No push or PR.
b: 3 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
c: 1 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
d: 4 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
