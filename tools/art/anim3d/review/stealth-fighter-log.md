Round 1: read project art skill, full standing feedback including 12–23 and vehicles/bomber family pipelines. No unit-specific feedback file present.
Skills: blender-modeling (closed bevelled panels and nozzle apertures), materials (painted dielectric, titanium, frozen source pigment), lighting (warm key/cool rim), cameras (registered source landmarks), animation (rig pivots and layered actions), rendering (gated CPU Cycles previews, explicit GPU handoff).
Build: original full-depth stealth fuselage, wings, twin fins, canopy, intake throats, twin exhausts, control pivots and cream stone stand; reusing licensed bomber projection/delivery helpers.
b: 3 frames at 256/64 from 256px CYCLES/CPU, 6 samples.
c: 1 frames at 256/64 from 256px CYCLES/CPU, 8 samples.
First b/c sheets published immediately. CPU256 rest silhouette and identity are close; panel/canopy finish is softer than source, stone lacks source fine grain. Alternate views prove thickness but expose coarse engine/body joins. Not PASS.
Six actual 512px Cycles AO/Pointiness bakes saved and packed; camera pigment restricted to camera rays, physical stone does not retain a painted support shadow.
b: 3 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
c: 1 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
d: 4 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-idle: 8 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-move: 8 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-attack: 10 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-hit: 4 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
d: 4 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-attack: 10 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
b: 3 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
c: 1 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
Delivery rejected initial crash edge clipping; trajectory now fits evaluated aircraft vertices inside a fixed camera without image rescaling. Wreck contact recomputed afterward.
Final QA found origin-centred elevon pivots; dependency update added before parenting, local pivot-distance audit added, and all masters regenerated.
Final QA found lossy duplicate death-frame RGB mismatch; identical cells now reuse one atlas rectangle with straight-alpha paste. Validator requires exact decoded final hold.
d: 4 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-idle: 8 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-move: 8 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-attack: 10 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-hit: 4 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
Final round-1 CPU candidate: 163388 bytes Q90, 40 trimmed 160px frames; exact decoded death hold, all alpha/offset/hash checks pass. Nine native512+derived256 stage sets verified.
All five clip geometry audits pass: 23 meshes, manifold principal volumes, corrected elevon pivots, stationary base, loop closure and physical wreck contact. Five regression tests, eight Python syntax checks, two shell syntax checks and diff whitespace pass.
Movie verified H.264/yuv420p 1600x348, 240 frames, 8 seconds; decoded samples inspected. Rest alpha IoU .972768, RGB MAE 5.69469. 64px identity strong; 256px stone/panel craft, off-axis joins and crash impact remain weaker than painting. No PASS.
GPU pass not run in sandbox; complete executable handoff is tools/art/anim3d/units/stealth-fighter/gpu.sh with ROUND supplied by driver. CPU receipts do not claim GPU success.
Git staging denied creating .git/worktrees/lane-19/index.lock; left requested scoped changes for runner commit. No push, PR, upload or deployment.
b: 3 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
c: 1 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
d: 4 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
e-idle: 8 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
e-move: 8 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
e-attack: 10 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
e-hit: 4 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
GPU round 1: all stages GPU512, verified 256 copies, trimmed atlas, geometry/alpha/clip checks and decoded-atlas MP4; visual acceptance remains manual.
