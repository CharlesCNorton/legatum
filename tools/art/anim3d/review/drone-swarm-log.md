Round 1 started: read project art instructions, vehicle PLAYBOOK, feedback 12–22 and all six Blender skills. Modeling: closed beveled solids; materials: projected painting and generated bronze unseen fill; cameras: alpha-bound registration; lighting: warm key/cool rim; animation: rigid roots and rotor pivots; rendering: Cycles CPU previews and fail-closed GPU handoff.
b: 3 frames at 256/64 from 256px CYCLES/CPU, 4 samples.
c: 1 frames at 256/64 from 256px CYCLES/CPU, 6 samples.
b: 3 frames at 256/64 from 256px CYCLES/CPU, 4 samples.
c: 1 frames at 256/64 from 256px CYCLES/CPU, 12 samples.
First b/c images published immediately. Visual check: narrow hulls, thin rotor bars and tall base ellipse; rebuilt fuller volumetric shells, broadened/angled solid blades, corrected formation and camera elevation. Initial evidence retained in masters/drone-swarm/first-*.png.
b: 3 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
c: 1 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
d: 4 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-idle: 8 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-move: 8 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-attack: 10 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-hit: 4 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-hit: 4 frames at 256/64 from 512px CYCLES/CPU, 12 samples.

Round 2 resumed: opened prior rest comparison, detail sheet and death strip first. At 256 px the bronze paint is recognizable but hull silhouettes and gimbal/strut positions differ, blades are pale flat paddles instead of dark plum airfoils, and the base is greenish with too little rim depth. At 64 px the three-drone formation reads correctly but its contours and stone are visibly different. Not PASS. Prior evidence is CPU512/12, not a verified GPU round; retained under masters/drone-swarm/round1-cpu. Read all global feedback (1-23); unit-specific FEEDBACK file is absent.
Using all six Blender skills: modeling for finished bevelled surfaces before UV projection; materials for camera-only painted pigment and generated unseen fill; lighting for restrained product softboxes; cameras for reference registration; animation for rigid mechanical clips; rendering for provenance, held frames and decoded video. No humans or animals: mocap/foot gait does not apply; add front/top move views of landing struts and rotors as the mechanical diagnostic.
c: 1 frames at 256/64 from 256px CYCLES/CPU, 8 samples.
b: 3 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
c: 1 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
c: 1 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
d: 4 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-idle: 8 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-move: 8 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-attack: 10 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-hit: 4 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
g: 16 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
g: 16 frames at 256/64 from 512px CYCLES/CPU, 12 samples.
Round 2 finish: applied bevels before frozen UVs, sampled complete surfaces, camera-only 96% painted pigment with Standard/None and restrained product lights; retained generated bronze fill and rebaked all six AO/Pointiness maps. Deeper cream rim, fuller hull undersides/landing struts and independently fitted lower formation/motor pods. No new external assets.
Round 2 motion: inspected all five strips, plain views, rest/details, front/top move cycle and contact samples of encoded MP4. All clip entries now match rest transforms, hover/gimbal loops close, death clearance runs after rotor transforms and the last image/atlas rectangle is reused. Oblique/death views still expose orange fill seams and crowded overlapping wrecks; not clean enough for art PASS.
Round 2 technical: CPU512/12 with 256 copies; 40 samples at 8/8/10/4/10; trimmed 160 atlas 176538 bytes Q85 with exact lossless alpha; audit and four delivery regression tests pass. MP4 verified H.264/yuv420p 1600x348, 240 frames, 8 seconds. GPU missing-input preflight correctly fails and records stage; actual Metal GPU pass remains unverified here.
Round 2 verdict: 256px color/base are substantially closer but hull underside, struts, rotor silhouettes and fill seams still differ; 64px same unit, not indistinguishable. Silhouette IoU whole .7322->.8060, drones .6022->.6609, base .8766->.9675. No PASS marker. GPU handoff executable: ROUND=2 tools/art/anim3d/units/drone-swarm/gpu.sh. Browser art gate blocked by Chromium macOS MachPort Permission denied (1100).
