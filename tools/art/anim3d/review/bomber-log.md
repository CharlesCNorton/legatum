Round 1: read art skill, playbook, standing feedback 12–22 and all six Blender skills; using lofted airframe, bevels, frozen projection, product lighting, keyed mechanical rig and CPU preview review.
b: 1 frames at 256/64 from 256px CYCLES/CPU, 8 samples.
c: 1 frames at 256/64 from 256px CYCLES/CPU, 8 samples.
b: 1 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
c: 1 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
d: 4 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-idle: 8 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-move: 8 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
First 512 CPU comparison: source-projected brushwork and corrected wing read as bomber at 64; 256 still has proud glazing, rough prop hub transitions and peach-biased stone after global grade. No PASS.
Added actual 512 AO/Pointiness bake workflow for fuselage and both wings; final CPU round will use those maps and corrected periodic propeller keys.
e-attack: 10 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-hit: 4 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
b: 3 frames at 256/64 from 512px CYCLES/CPU, 4 samples.
c: 1 frames at 256/64 from 512px CYCLES/CPU, 4 samples.
d: 4 frames at 256/64 from 512px CYCLES/CPU, 4 samples.
e-idle: 8 frames at 256/64 from 512px CYCLES/CPU, 4 samples.
c: 1 frames at 256/64 from 512px CYCLES/CPU, 4 samples.
e-move: 8 frames at 256/64 from 512px CYCLES/CPU, 4 samples.
e-attack: 10 frames at 256/64 from 512px CYCLES/CPU, 4 samples.
e-hit: 4 frames at 256/64 from 512px CYCLES/CPU, 4 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/CPU, 4 samples.
b: 3 frames at 256/64 from 512px CYCLES/CPU, 4 samples.
d: 4 frames at 256/64 from 512px CYCLES/CPU, 4 samples.
e-attack: 10 frames at 256/64 from 512px CYCLES/CPU, 4 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/CPU, 4 samples.
Round 1 complete: 512/256 CPU masters, six actual AO/curvature bakes, five editable clips and all review stages retained. Final geometry audit passed all five clips, periodic props, fixed base and measured wreck contact.
Final atlas validated: 40 frames, trimmed 160 logical cells with per-frame offsets, WebP quality 80, 193478 bytes. Eight-second five-clip MP4 written. No frames dropped.
Honest visual verdict: same bomber identity at 64 px; at 256 px the canopy/turret volumes and propeller hubs still look too simplified, the stone grade is peach-biased and moving projected highlights reveal the fixed-view technique. GPU 96-sample pass and lead art review remain outstanding; no PASS marker.
Non-obvious findings: keep propeller orientation periodic modulo three blades; check attack extremities independently from idle; validate held visible pixels rather than RGB beneath zero alpha; use actual base-footprint mesh height to place the wreck.
Final verification: H.264/yuv420p MP4 1600x348, 240 frames, 8.000 s; 48 masters each at 512 and 256; all 16 review files present. Git commit blocked by sandbox index.lock permission; runner must commit. No push or PR.
