Build: used blender-modeling/materials/lighting/cameras/animation/rendering skills: bevels, cloth thickness, physical pigments, fixed orthographic camera, keyed rig, Cycles previews.
Built original MPFB anatomy, 53-bone rig and hoplite-specific linen/lambda kit; saved separately from old master.
Review b: 256px CYCLES/CPU, 8 samples; 3 actual frames.
Build: used blender-modeling/materials/lighting/cameras/animation/rendering skills: bevels, cloth thickness, physical pigments, fixed orthographic camera, keyed rig, Cycles previews.
Built original MPFB anatomy, 53-bone rig and hoplite-specific linen/lambda kit; saved separately from old master.
Textured: CC0 scans, 512 AO/curvature bakes, fixed painting UVs, generated unseen linen/bronze fills, cream pigment and product lighting.
Review c: 256px CYCLES/CPU, 12 samples; 1 actual frames.
Build: used blender-modeling/materials/lighting/cameras/animation/rendering skills: bevels, cloth thickness, physical pigments, fixed orthographic camera, keyed rig, Cycles previews.
Built original MPFB anatomy, 53-bone rig and hoplite-specific linen/lambda kit; saved separately from old master.
Textured: CC0 scans, 512 AO/curvature bakes, fixed painting UVs, generated unseen linen/bronze fills, cream pigment and product lighting.
Review c: 256px CYCLES/CPU, 16 samples; 1 actual frames.
Baked clip idle
Baked clip move
Baked clip attack
Baked clip hit
Baked clip death
Review c: 256px CYCLES/CPU, 16 samples; 1 actual frames.
Visual correction: inherited aspis quad rings had inward normals; repaired winding, preserved fixed projected UVs and removed duplicate lambda relief. Rest remains below painting quality, especially mantle and helmet profile.
Review c: 512px CYCLES/CPU, 12 samples; 1 actual frames.
Review d: 512px CYCLES/CPU, 12 samples; 4 actual frames.
Review e-idle: 512px CYCLES/CPU, 12 samples; 8 actual frames.
Review e-move: 512px CYCLES/CPU, 12 samples; 8 actual frames.
Review e-attack: 512px CYCLES/CPU, 12 samples; 10 actual frames.
Review e-hit: 512px CYCLES/CPU, 12 samples; 4 actual frames.
Review e-death: 512px CYCLES/CPU, 12 samples; 10 actual frames.
Review c: 512px CYCLES/CPU, 12 samples; 1 actual frames.
Review d: 512px CYCLES/CPU, 12 samples; 4 actual frames.
Checks before final shield clearance: atlas 175738 bytes, quality 85, 40/40 frames and held death passed; full rig audit 0 findings after .43 attack grip slide. Final atlas will be refreshed after clearance renders.
Shield contact probe confirmed finger penetration; moved all shield surfaces 75mm forward and grounded the released shield. Follow-up probe hit only shield across all former fingertip pixels.
Review e-idle: 512px CYCLES/CPU, 12 samples; 8 actual frames.
Review e-move: 512px CYCLES/CPU, 12 samples; 8 actual frames.
Review e-attack: 512px CYCLES/CPU, 12 samples; 10 actual frames.
Review c: 512px CYCLES/CPU, 8 samples; 1 actual frames.
Review d: 512px CYCLES/CPU, 8 samples; 4 actual frames.
Final surface revision: outward mantle normals enable the frozen painting UV colour; projected helmet metals use Metallic=1. Final CPU master refresh running at 512px / 8 samples, deriving 256px frames as each stage completes; GPU approval remains outstanding.
Review e-idle: 512px CYCLES/CPU, 8 samples; 8 actual frames.
Review e-move: 512px CYCLES/CPU, 8 samples; 8 actual frames.
Review e-attack: 512px CYCLES/CPU, 8 samples; 10 actual frames.
Review e-hit: 512px CYCLES/CPU, 8 samples; 4 actual frames.
Review e-death: 512px CYCLES/CPU, 8 samples; 10 actual frames.
FINAL round 1: 40 actual 512px RGBA frames + 40 256px derivatives verified; 172788-byte atlas at quality 85. Atlas/trim/motion/held-death validation PASS; full rig audit 0 findings; shield probe only shield. Art verdict: still below painting at 256px, recognizable at 64px; GPU review and broader art gate outstanding.
Commit attempt blocked: Git could not create .git/worktrees/lane-5/index.lock (Operation not permitted); changes left for the runner to commit with the requested co-author line.

Round 2 opening critique (2026-11-23): inspected latest rest split/crossfade and attack strip first. At 256px the crest is a broad sideways fan instead of the narrow swept source plume; helmet sits low, spear grip is roughly 30px too low, cloak shoulder corners are angular, linen strips lack the painted layering, shield is too low/wide, and bronze is glossy/plastic. Stone is flat pale grey-cream rather than the warm substantial painted disc. At 64px identity survives but the short torso, enlarged plume, low grip and shield silhouette are plainly different. No PASS. Unit-specific FEEDBACK file is absent; read all common feedback. Applying all six Blender skills and round-8 spearman/cannon lessons: finished-surface frozen projection, preserved rig/cloth, camera-only painted pigment, physical fill, repeatable registration, one rest-derived grade.
Review c: 256px CYCLES/CPU, 8 samples; 1 actual frames.
Review c: 256px CYCLES/CPU, 12 samples; 1 actual frames.
Baked clip idle
Round 2 fitting: preserved round1 masters; new round2-3d checkpoint. Single frozen camera replaces per-part UV stretching, static kit modifiers finish before projection, MPFB mixed shape keys freeze while original 19158 vertices/53 bones/weights remain. Raised spear grip 24cm while preserving shaft world position, narrowed crest and shield, softened mantle corners, lifted helmet six token pixels. Camera-only painted pigment with Standard display avoids double shading; physical backs retain scans/generated linen. Rest silhouette IoU at alpha>128 improves .644822 -> .770323; this is contour evidence, not art parity.
Round 2 GPU handoff: executable no-argument gpu.sh, sequential Cycles GPU512/64 stages, scene/rig audits, source/master/grade provenance gate, pack/validation and trimmed decoded 8s movie. Missing-input preflight correctly fails before Blender and records failed stage. Actual Metal run remains host-only.
Baked clip move
Baked clip attack
Baked clip hit
Baked clip death
Round 2 verification: scene invariant/input hash check passed (172 projected meshes, 19158 anatomical vertices, 53 bones). First full rig audit found 6 attack butt/camera-bound violations after raising the grip; fixed with .29m extra slide only in raised poses, preserved baked cloth because the spear is not a collider, and encoded identical correction into full animation rebuild. Repeated full 40-sample audit: 0 findings. Targeted fingertip pixels remain shield-covered; surrounding probe region also contains legitimate body pixels.
Repository baseline gates: public-claims passed; hygiene flagged two existing matrix @ expressions as email addresses (fixed operator spacing). Browser art-set gate failed in its Node renderer in this sandbox; host art review remains required.
Review b: 256px CYCLES/CPU, 12 samples; 3 actual frames.
Review c: 256px CYCLES/CPU, 12 samples; 1 actual frames.
Review d: 256px CYCLES/CPU, 12 samples; 4 actual frames.
Review e-idle: 256px CYCLES/CPU, 12 samples; 8 actual frames.
Review e-move: 256px CYCLES/CPU, 12 samples; 8 actual frames.
Review e-attack: 256px CYCLES/CPU, 12 samples; 10 actual frames.
Review e-hit: 256px CYCLES/CPU, 12 samples; 4 actual frames.
Review e-death: 256px CYCLES/CPU, 12 samples; 10 actual frames.
Round 2 final CPU: 40/40 frames at256/Cycles CPU12; atlas 199862 bytes Q90; full trim/motion/margin/hash/held-death validation passed. Full rig audit 0 findings. MP4 verified H264/yuv420p1600x348,240 frames,8s; inspected all five strips and decoded movie frame. GPU-only master gate rejects missing512 masters. Missing-input preflight passed; separate device test cancelled while queued at sharedGPU gate, no hardware result claimed.
Round 2 visual verdict: improved contour and painted linen but NO PASS. At256 plume remains uniform, neck/mantle forms a broad shelf, linen needs crisper physical layers and stone rim is too dark. At64 identity and silhouette are closer but visibly different. Death shield changes presentation at entry and the terminal pose is stiff/perched; next round must reconcile death left-arm guard and contact, not call five clean clips from technical checks alone.
Final code checks: 16 unit Python files parse; render.sh and executable gpu.sh pass bash -n; git diff --check passed; current-file hygiene scan 21 files/0 findings. Baseline public-claims passed; browser art gate remains blocked by Node renderer failure. Git add/commit both denied creating .git/worktrees/lane-12/index.lock; runner must commit with requested co-author (message saved tmp/spartan-round2-commit.txt). No push, PR, upload or PASS.
Baked clip idle
Baked clip move
Baked clip attack
Baked clip hit
