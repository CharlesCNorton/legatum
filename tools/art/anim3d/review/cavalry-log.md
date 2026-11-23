Round 1: read six Blender skills, Legatum art, mounted branch and standing feedback; inspected cavalry painting.
Reusing licensed Quaternius horse, MPFB rider and original generated mounted fills; authored cavalry uniform and sabre geometry.
b: review emitted from CYCLES frames; no art-pass claim.
b: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
b: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
c-details: review emitted from CYCLES frames; no art-pass claim.
d: review emitted from CYCLES frames; no art-pass claim.
e-idle: review emitted from CYCLES frames; no art-pass claim.
e-move: review emitted from CYCLES frames; no art-pass claim.
e-attack: review emitted from CYCLES frames; no art-pass claim.
Rest review: still visibly behind painting; adjusted side camera/elevation, wider weapon reach, removed rigid extra tail. No PASS.
Motion review: source horse gait renders; authored sabre sweep revised downward after attack pose inspection. Shortening blade to keep all cells inside bounds.
e-hit: review emitted from CYCLES frames; no art-pass claim.
e-death: review emitted from CYCLES frames; no art-pass claim.

Round 2 opening critique: opened latest rest comparison and rig poses before editing. At 256px horse chest/muzzle and legs differ markedly, sword hand is too far right/up, arm is bent rather than extended left, saddle blanket is oversized and surfaces are shiny/patchy. At 64px cavalry identity survives but pose and silhouette are clearly different; no PASS. Cavalry-specific FEEDBACK file absent; read all standing FEEDBACK. Loaded six Blender skills; use finished-surface frozen UVs, camera-only painted pigment, physical pose fitting, and validated sequential GPU delivery.
c: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
b: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
c-details: review emitted from CYCLES frames; no art-pass claim.
Round 2: runner switched lane-20 to peltast at 07:09; recovered WIP 84bb6e56 in legatum/.worktrees/cavalry-round2, original cavalry branch. Do not switch the shared lane back.
Round 2 fixes: frozen MPFB morph plus inverse-skin rest fitting; rejected oscillating hindquarter trial; bounded horse corrections, rigid sabre fit, jacket hand cut, camera-only painted pigment, retained generated fills/physical detail, warm stone, live rein endpoints. GPU handoff now regenerates paint and clips with preflight, transcript and failed-stage receipt. Missing-input rejection test passed.
d: review emitted from CYCLES frames; no art-pass claim.
e-idle: review emitted from CYCLES frames; no art-pass claim.
e-move: review emitted from CYCLES frames; no art-pass claim.
e-attack: review emitted from CYCLES frames; no art-pass claim.
e-hit: review emitted from CYCLES frames; no art-pass claim.
e-death: review emitted from CYCLES frames; no art-pass claim.
e-hit: review emitted from CYCLES frames; no art-pass claim.
e-death: review emitted from CYCLES frames; no art-pass claim.
Round 2 motion inspection: opened all five strips, clay views and 512px detail. True geometric reins now meet bit/hand. Found hit top clipping and death right-edge clipping; added actual wrist framing, leftward ground-plane settling and folded released arm. The fold changed early-death sword orientation, so the wrist bounds correction also covers death. Re-rendering the changed clip before final packing.
Next visual priorities: remove inherited ivory horse blaze (not in painting), fit muzzle/chest/hindquarters and hoof stance, replace the straight thick tail with swept flowing hair, fit boots/stirrups and flatten heavy tack straps, improve sabre curvature/guard projection. Source clip entry and hoof contact remain distinguishable from a clean finished animation. No art PASS.
e-death: review emitted from CYCLES frames; no art-pass claim.
Round 2 final CPU evidence: all 40 frames at Cycles CPU/256/8 samples (details genuinely 512/8); atlas 190758 bytes at Q80, [1319, 739], 39 unique rectangles, premultiplied bicubic and lossless 8-bit alpha. Full decoded alpha/offset/bounds/motion/held-death validation passed; dual-rig/anatomy/rein-bit/stationary-base/safe-scale audit passed. MP4 [1600, 352], 192 frames, 8 seconds, H.264/yuv420p.
Checks: 18 Python files parse, both shell entry points parse, executable GPU handoff and whitespace pass; grade reapplication preserves raw/render/LUT hashes; missing-input GPU receipt and CPU-master rejection passed. Repository art gate blocked by Chromium bootstrap_check_in permission denied (1100), not by a visual comparison result.
Final visual verdict: at 256px uniform/face brushwork and cream base improve; horse shape, pale blaze patches, thick tack, tail and sabre remain visibly unlike the painting. At 64px cavalry identity is clear but the silhouette/stance are not the same. Motion framing now passes, but contact, transitions and anatomy still need polish. No PASS. GPU512/64 masters and fresh visual review remain pending. Lead runs ROUND=2 tools/art/anim3d/units/cavalry/gpu.sh from legatum/.worktrees/cavalry-round2 (or another checkout of the cavalry branch).
Committed a553ab6d on astra/unit-anim-3d-cavalry; clean isolated worktree. Final committed hygiene check: 0 findings. Inspected decoded MP4 contact frame; no art PASS.
