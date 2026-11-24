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
b: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
c-details: review emitted from CYCLES frames; no art-pass claim.
d: review emitted from CYCLES frames; no art-pass claim.
e-idle: review emitted from CYCLES frames; no art-pass claim.
e-move: review emitted from CYCLES frames; no art-pass claim.
e-attack: review emitted from CYCLES frames; no art-pass claim.
e-hit: review emitted from CYCLES frames; no art-pass claim.
e-death: review emitted from CYCLES frames; no art-pass claim.
Round 1: GPU stages, 512/256 masters, trimmed atlas, validation and MP4 complete; visual approval still required.

Driver round 2 opening: opened GPU c/f and all five e strips, plus eight extracted round1 MP4 frames before editing; preserved receipts/images/masters under masters/cavalry/driver-r1-gpu. Supplied gpu-logs-cavalry-r1.log is empty because gpu.sh redirects to cavalry-gpu-round1.log; canonical status confirms completed GPU pass. Cavalry-FEEDBACK.md absent. Read complete standing FEEDBACK including motion/feet requirement and all playbook chapters.
Honest GPU critique at 256px: rider pigment/detail is close, but horse has an invented pale blaze and socks, boxy extended muzzle/bridle, upright narrow hind legs instead of the flexed painted stance, a smooth straight tail instead of flowing hair, oversized angular stirrups, and an overly thin straight-looking sabre. The base lacks painted stone grain. At 64px navy cavalry identity survives but horse silhouette, stance and tail remain visibly different. Five clips are framed, but gait support, transition pops and rigid tack need review; NO PASS.
Using blender-modeling/materials/cameras/lighting/animation/rendering: retain full-depth weighted geometry and rest-camera UVs, correct horse/tack silhouettes, reuse documented generated fills, retain physical bevels/folds and product lights, recalibrate one fixed histogram LUT, add source-motion top/front feet evidence.
c: review emitted from CYCLES frames; no art-pass claim.
First CPU rest follow-up: bridle/stirrups and tail direction improved, but dark lower legs/head lost painted detail. Correction to opening critique: the full painting DOES have a narrow blaze and pale hind fetlocks; the defect was broad invented ivory regions plus a chroma mask excluding the source details. Replace that with semantic horse pigment projection, retain opacity/geometry, and lower the actual horse head toward the source landmarks.
c: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
b: review emitted from CYCLES frames; no art-pass claim.
c-details: review emitted from CYCLES frames; no art-pass claim.
d: review emitted from CYCLES frames; no art-pass claim.
e-idle: review emitted from CYCLES frames; no art-pass claim.
e-move: review emitted from CYCLES frames; no art-pass claim.
e-attack: review emitted from CYCLES frames; no art-pass claim.
e-hit: review emitted from CYCLES frames; no art-pass claim.
e-death: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
Full-cycle inspection exposed pinched fetlocks and an upright whip tail. Added continuous weighted leg section profiles, vertical contact correctives over native Quaternius lift, source-timed restrained tail amplitude, and rest transitions for attack/hit/death. Retained native horizontal gait and foot rotations. New feet sheet has actual cutaway geometry, support line and sole heights. Rebuilding before final checks; no PASS.
Handoff negative test caught denied /dev/fd process substitution in the sandbox. Replaced logging with a normal subshell pipe plus pipefail; missing-checkpoint test now exits 1 with failed preflight receipt and visible driver output.
c: review emitted from CYCLES frames; no art-pass claim.
b: review emitted from CYCLES frames; no art-pass claim.
c-details: review emitted from CYCLES frames; no art-pass claim.
d: review emitted from CYCLES frames; no art-pass claim.
e-idle: review emitted from CYCLES frames; no art-pass claim.
e-move: review emitted from CYCLES frames; no art-pass claim.
e-attack: review emitted from CYCLES frames; no art-pass claim.
e-hit: review emitted from CYCLES frames; no art-pass claim.
Rejected continuous lower-leg profile trial after full move strip showed stretched hind legs. Final fitting excludes native leg/shoulder weights from image-plane deformation and retains source leg volumes; head/croup/tack/tail improvements stay. This accepts a remaining rest stance mismatch rather than misreporting a static-only improvement as clean animation. Rebuilding the final candidate; no PASS.
e-death: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
b: review emitted from CYCLES frames; no art-pass claim.
c-details: review emitted from CYCLES frames; no art-pass claim.
d: review emitted from CYCLES frames; no art-pass claim.
e-idle: review emitted from CYCLES frames; no art-pass claim.
e-move: review emitted from CYCLES frames; no art-pass claim.
e-attack: review emitted from CYCLES frames; no art-pass claim.
e-hit: review emitted from CYCLES frames; no art-pass claim.
e-death: review emitted from CYCLES frames; no art-pass claim.
Final-cycle visual check caught detached added tail locks in death despite valid 187976-byte Q80 atlas. Root cause: copied skin weights/armature but missing native horse object parent hierarchy. Fixed parent/matrix inheritance in finish.py and added audit assertion; full rerender follows. Size/alpha/rig passes alone are explicitly insufficient for PASS.
c: review emitted from CYCLES frames; no art-pass claim.
b: review emitted from CYCLES frames; no art-pass claim.
c-details: review emitted from CYCLES frames; no art-pass claim.
d: review emitted from CYCLES frames; no art-pass claim.
e-idle: review emitted from CYCLES frames; no art-pass claim.
e-move: review emitted from CYCLES frames; no art-pass claim.
e-attack: review emitted from CYCLES frames; no art-pass claim.
e-hit: review emitted from CYCLES frames; no art-pass claim.
e-death: review emitted from CYCLES frames; no art-pass claim.
Round 2 final CPU cycle: all 40 clip frames rendered at 256px/8 samples, detail crop at 512px, feet sheet at 192px/4 samples. Editing the wrapper during its running refresh caused a shell read-offset error after all renders finished; shell syntax passed and feet/audit/pack/validation/video were rerun successfully. No GPU provenance claimed.
Round 2 visual readback: opened fresh c, f split/crossfade, all five e strips, g feet sheet, and extracted round2 MP4 frames. Added tail now remains attached through death. At 256px uniform/face/coat/tack are closer, but thin angular legs, different hind stance, blocky exposed croup, sparse rope-like tail, weaker blade/metal highlights and abrupt hit recoil remain below the painting. At 64px the unit reads as cavalry but the stance/leg silhouette still differs clearly. Five clips are present and structurally valid, not certified clean. No PASS.
Round 2 exact CPU result: trimmed 160px atlas 184704 bytes at Q80; 40 frames 8/8/10/4/10; transparent alpha/offsets/bounds/hashes/motion/identical decoded death hold passed. Structural audit passed including shared tail parent and rein-bit attachment; zero sampled sole-below-.09m warnings is not slip/collision certification. Video 1600x352 H264 yuv420p, 192 frames, 8s.
Round 2 checks: all 24 Python files parsed, shell entrypoints bash -n passed, 11 pinned external inputs matched, grade rerun preserved all 17 idle/grade files byte-for-byte, REQUIRE_MASTERS rejected CPU previews before writes, missing-checkpoint GPU handoff negative test returned exit1 with failed-stage receipt and visible transcript. Source rest silhouette IoU 0.6962 at256 / 0.7055 at64; these diagnostics are not art approval.
GPU handoff: ROUND=2 tools/art/anim3d/units/cavalry/gpu.sh from this checkout. It rebuilds sequential GPU512 stages, gallery256, feet diagnostics, rig audit, trimmed atlas validation and MP4. Eevee feet diagnostics now receive --gpu-backend metal like the stage renders. Old GPU round1 evidence remains archived under masters/cavalry/driver-r1-gpu; new GPU512 pass is pending.
Final repository checks: git diff --check passed; working-file hygiene over all 18 changed/new files passed after spacing three matrix @ operators that the email detector misread. HEAD gate hygiene and public-claims passed, but that gate cannot include uncommitted work. Both HEAD art gate and direct working-tree distinctness render failed at Chromium launch: bootstrap_check_in MachPortRendezvousServer Permission denied (1100), SIGTRAP; no art distinctness result.
Runner handoff: git add/commit denied creating worktree index.lock; merge of newly advanced origin/master denied ORIG_HEAD.lock. Current master advance is f12ab82e (Hard Rome opening march), unrelated to art. All 18 files remain uncommitted; runner must merge latest master, run required determinism/pin checks after merge, commit with the supplied gpt-6-astra coauthor footer, and rerun repository gates including browser art on an unrestricted host. Commit message is staged externally at anim-pilot/tmp/cavalry-round2-commit.txt. No push, no PR, no PASS.
b: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
c-details: review emitted from CYCLES frames; no art-pass claim.
d: review emitted from CYCLES frames; no art-pass claim.
e-idle: review emitted from CYCLES frames; no art-pass claim.
e-move: review emitted from CYCLES frames; no art-pass claim.
e-attack: review emitted from CYCLES frames; no art-pass claim.
e-hit: review emitted from CYCLES frames; no art-pass claim.
e-death: review emitted from CYCLES frames; no art-pass claim.
Round 2: GPU stages, 512/256 masters, trimmed atlas, validation and MP4 complete; visual approval still required.

Driver round 3 opening: opened GPU c/f, all five e strips and round2 MP4 contact frames first. GPU log confirms successful pass, 184594 bytes Q80 and 40 frames; archived prior evidence under masters/cavalry/driver-r2-gpu. Cavalry-FEEDBACK.md absent. Read standing feedback and all playbook chapters; loaded six Blender skills. At 256px projected rider brushwork is close, but horse legs are thin/angular and detached-looking, hind stance wrong, tail sparse, blade weak and stone too plain. At 64px navy cavalry identity survives but stance and mass differ clearly. No PASS. Prior mesh-only support correctives and displaced joint centers are the first target; preserve proven CC0 source motion and fix geometry/rig registration together.
c: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
e-move: review emitted from CYCLES frames; no art-pass claim.
Round 3 first CPU rest review: replacing mesh-only support warps with full-depth joint registration improves silhouette substantially. Diagnosed crossed hind fetlocks: source rear IK hoof roots have opposite suffixes from upper/lower leg chains; registered anatomical pairs explicitly. Small radial native-mesh refinement retains topology and weights. No foot yaw patch. First move/death/idle checks running before accepting the fit. Generated a clean stone pigment plate using built-in ImageGen; projected on physical beveled disc with live AO, never alpha geometry. Added true diamond-section sabre fitted to painted arc and denser tapered solid tail locks for next preview.
e-death: review emitted from CYCLES frames; no art-pass claim.
e-idle: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
b: review emitted from CYCLES frames; no art-pass claim.
c: review emitted from CYCLES frames; no art-pass claim.
c-details: review emitted from CYCLES frames; no art-pass claim.
d: review emitted from CYCLES frames; no art-pass claim.
e-idle: review emitted from CYCLES frames; no art-pass claim.
e-move: review emitted from CYCLES frames; no art-pass claim.
e-attack: review emitted from CYCLES frames; no art-pass claim.
e-hit: review emitted from CYCLES frames; no art-pass claim.
Round 3 follow-up: first death sample revealed a floor-solver pop caused by rest soles below the stone. Fit planted sole depth along the orthographic viewing axis, preserving projected joint positions, and added idle sole penetration assertion. Reset sparse horse/rider action pose bases before every sample to prevent rest transforms leaking into source motion. Final full CPU cycle now renders all stages at 256/8, genuine 512/8 detail, with device/resolution/sample labels.
Round 3 interim measurement: source/rest silhouette IoU improved from GPU round2 0.6962 to CPU round3 0.7724 at256 and 0.7049 to 0.7772 at64; opaque-overlap RGB MAE 10.403/8.150. These diagnostics include the base and do not certify anatomy, animation or art parity. Opened clay, details and split: hock/knee contours remain angular, muzzle/face/hand differ, tail still needs fuller natural hair.
Repository gate: HEAD hygiene/public-claims passed; art distinctness could not launch Chromium. Direct working-tree reproduction confirmed bootstrap_check_in MachPortRendezvousServer Permission denied (1100). Working-file hygiene independently passed all 18 changed/new/deleted files; 27 Python modules parse, both shell entrypoints parse, git diff --check passes. Missing-checkpoint GPU test exits nonzero with visible failed-stage receipt. No art approval inferred from these checks.
e-death: review emitted from CYCLES frames; no art-pass claim.
