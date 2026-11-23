# Cuirassier round 1
- Read the six Blender skills, mounted chapter, standing feedback and painting; initial branch clean.
- Reusing CC0 Quaternius horse and MPFB rig; original cuirassier kit and pistol required.
- Emitted b: 3 frames, 256 px CYCLES/CPU, 4 samples.
- Emitted c: 1 frames, 256 px CYCLES/CPU, 6 samples.
- Emitted c-details: 1 frames, 256 px CYCLES/CPU, 6 samples.
- Emitted d: 4 frames, 256 px CYCLES/CPU, 4 samples.
- Emitted e-idle: 8 frames, 256 px CYCLES/CPU, 4 samples.
- Emitted e-move: 8 frames, 256 px CYCLES/CPU, 4 samples.
- Emitted e-attack: 10 frames, 256 px CYCLES/CPU, 4 samples.
- Emitted e-hit: 4 frames, 256 px CYCLES/CPU, 4 samples.
- Emitted e-death: 10 frames, 256 px CYCLES/CPU, 4 samples.
- First full motion review emitted. Found source coat/base projection spill and bottom-cell clipping. Archived first reviews under masters/cuirassier/review-initial. A live edit to render.sh caused a shell footer error after rendering completed; fresh invocations include Python error exit codes.
- Corrected camera extent and pistol aim; added pigment masks, raised neck pose and source-chain skinned tail. Rebuilding all dependent masters.
- Emitted b: 3 frames, 256 px CYCLES/CPU, 4 samples.
- Emitted c: 1 frames, 256 px CYCLES/CPU, 8 samples.
- Emitted c-details: 1 frames, 256 px CYCLES/CPU, 8 samples.

# Resumed round 2 — 2026-11-23
- Opened the latest rest comparison, details and attack strip before editing. At 256 px the horse is narrow, long-legged and stiff; the hind feet float away from the disc, the rider is upright with a too-low pistol arm, silver glare replaces dark worn armour, and reins stray past the muzzle. At 64 px this reads as mounted cavalry but not the same silhouette, stance or premium miniature. No PASS.
- Read all standing feedback; cuirassier-FEEDBACK.md does not currently exist. Read local playbook plus the eight-round spearman and field-cannon chapters. Loaded all six Blender skills: cameras/modeling for registration and finished surfaces; materials/lighting for camera-only painted illumination; animation/rendering for rebuilt clips and GPU provenance. Existing supplied images are CPU-labelled; no GPU success inferred.
