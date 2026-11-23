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
Final checks: 8 Python files parse, both shell scripts pass bash -n, gpu.sh is executable, git diff --check passes, four delivery regression tests pass, geometry audit passes, and FFprobe movie verification passes. The generic gate ran against committed HEAD (not uncommitted round-2 edits) and flagged old compact matrix @ syntax as email addresses; current unit scripts use spaced operators. Browser art gate remains blocked by MachPort permission.
Commit attempted with required coauthor, but git add failed creating .git/worktrees/lane-1/index.lock: Operation not permitted. All round-2 changes are left uncommitted for the runner; no push or PR. origin/master already contained in this branch (0 missing commits).
b: 3 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
c: 1 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
d: 4 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
e-idle: 8 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
e-move: 8 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
e-attack: 10 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
e-hit: 4 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
g: 16 frames at 256/64 from 512px CYCLES/GPU, 96 samples.
GPU round 1: all stages GPU512, 256 masters, audited, trimmed atlas validated, decoded MP4 verified. Art verdict remains manual.

Driver round 2 GPU-first critique: inspected c, f, all five e strips and four decoded round1 MP4 contact frames before editing. GPU round1 succeeded (GPU512/96 receipt); no crash fix needed. At 256px the bright paint and cream base are close, but lower-drone silhouette/struts and rotor width are visibly wrong; at 64px identity/formation match but contours remain distinct. Death is the biggest motion failure: crowded intersecting-looking wrecks and orange unseen-fill seams. Not PASS. Prior GPU evidence and masters archived in masters/drone-swarm/driver-r1-gpu. Unit-specific FEEDBACK is absent; all 23 global feedback items read. All six Blender skills loaded; preserve volumetric mechanics, refine exact-view projection, grade existing generated fill, soften blade aliasing and separate terminal wrecks. Cloth/straps and living locomotion do not apply.
c: 1 frames at 256/64 from 256px CYCLES/CPU, 8 samples.
e-death: 10 frames at 256/64 from 256px CYCLES/CPU, 6 samples.
b: 3 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
c: 1 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
d: 4 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-idle: 8 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-move: 8 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-attack: 10 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-hit: 4 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
g: 16 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
b: 3 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
c: 1 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
d: 4 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-idle: 8 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-move: 8 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-attack: 10 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-hit: 4 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
g: 16 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
e-death: 10 frames at 256/64 from 512px CYCLES/CPU, 8 samples.
Driver round 2 geometry/material finish: broadened lower closed hulls, fitted thicker near struts/hidden far supports, replaced thin rotor spars with beveled tapered solids, adjusted blade spans and lower motor positions. Generated bronze brushwork retained with muted brass shader grading. Rebuilt finished frozen UVs and all six actual AO/Pointiness bakes; warm key/cool rim/soft fill and frozen automatic histogram grade retained. No new external assets.
Driver round 2 collision finding/fix: new BVH triangle audit found lower-drone surface crossings hidden by the orthographic painting view, plus a crossing during descent. Separated physical flight depths along the camera ray without changing projected placement; lower drones descend first, upper drone delayed; rotors decelerate and three separate wrecks settle on the stone. Final audit: zero inter-drone surface intersections across all 40 sampled poses. This is not a continuous or intra-drone collision proof.
Driver round 2 delivery: CPU Cycles512/8, 256 copies, all 8/8/10/4/10 frames; 160px trimmed atlas exactly 180000 bytes at Q85, lossless alpha with offsets validated, held death identical. Six delivery/provenance regression tests pass. Geometry audit passes (163 meshes, exact finished UVs, six bakes, stationary base, entries/loops/contact). FFprobe verifies H.264/yuv420p 1600x348, 240 frames, 8 seconds; inspected four decoded MP4 contact frames, all five strips, b/c/d/f/detail and front/top g images.
Driver round 2 verdict: at 256px the paint/cream base are close, lower hull/strut silhouette better and orange fill seams removed; rotor arms/blades, hull shoulders and gimbal profile remain different. At 64px same unit, still distinguishable. Death no longer crosses surfaces but still reads too much like a controlled landing; rotor sampling is visibly stepped. IoU whole .8060 -> .8301, drones .6609 -> .7048, base .9670. NOT PASS; no marker written.
Driver round 2 handoff: executable ROUND=2 tools/art/anim3d/units/drone-swarm/gpu.sh now checks sealed build inputs, renders every stage GPU512/96, retains 256 masters, audits geometry and inter-drone crossings, packs/validates, runs six regressions, verifies movie and writes full receipt. Prior round1 GPU succeeded; revised host pass is pending. Ten Python files parse; both shell scripts pass bash -n; git diff --check passes. Global feedback remains 1-23; unit-specific feedback still absent.
Final delivery boundary: git add/commit attempted with required coauthor, but sandbox denied .git/worktrees/lane-23/index.lock (Operation not permitted); runner must commit these changes. Static gate on committed HEAD: hygiene PASS, public-claims PASS, art FAIL because render-sets.mjs subprocess exited 1; this gate did not include uncommitted round-2 changes. No push, merge or PR. origin/master has zero commits missing from this branch.
