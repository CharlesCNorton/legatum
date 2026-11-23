Using six Blender skills: MPFB anatomy, solid folded clothing/bevels, textured Principled materials, warm key/cool rim, painting camera, authored keys/secondary cloth, denoised RGBA sequences.
Rendered b 256 px CYCLES/CPU
Using six Blender skills: MPFB anatomy, solid folded clothing/bevels, textured Principled materials, warm key/cool rim, painting camera, authored keys/secondary cloth, denoised RGBA sequences.
Rendered b 256 px CYCLES/CPU
Using six Blender skills: MPFB anatomy, solid folded clothing/bevels, textured Principled materials, warm key/cool rim, painting camera, authored keys/secondary cloth, denoised RGBA sequences.
Rendered b 512 px CYCLES/CPU
Rendered c 512 px CYCLES/CPU
Rendered c-details 512 px CYCLES/CPU
Using six Blender skills: MPFB anatomy, solid folded clothing/bevels, textured Principled materials, warm key/cool rim, painting camera, authored keys/secondary cloth, denoised RGBA sequences.
Rendered b 256 px CYCLES/CPU
Rendered c 512 px CYCLES/CPU
Rendered c-details 512 px CYCLES/CPU
Rendered d 512 px CYCLES/CPU
Rendered e-idle 512 px CYCLES/CPU
Rendered e-move 512 px CYCLES/CPU
Rendered e-attack 512 px CYCLES/CPU
Rendered e-hit 512 px CYCLES/CPU
Rendered e-death 512 px CYCLES/CPU
Round-1 source: original scout painting downloaded; generated four painted fill swatches, prompt and CC BY 4.0 provenance recorded.
First b check: standing silhouette too upright, top tunic ring obscured neck; reduced/tapered collar, leaned torso, widened cape and moved shading hand.
First c check: UV projection visibly spills tunic/skin into cloak and repeats on cowl ropes; adding material masks and retaining procedural/generated fibre on narrow cowl folds.
256 px verdict so far: noticeably below painting, especially face, cloth tailoring and knee pose. 64 px identity: forked staff, shading hand, ochre tunic and olive cape are recognizable; pose remains weaker.
Using six Blender skills: MPFB anatomy, solid folded clothing/bevels, textured Principled materials, warm key/cool rim, painting camera, authored keys/secondary cloth, denoised RGBA sequences.
Rendered b 256 px CYCLES/CPU
Rendered c 512 px CYCLES/CPU
Rendered c-details 512 px CYCLES/CPU
Rendered d 512 px CYCLES/CPU
Rendered e-idle 512 px CYCLES/CPU
Corrected projection masks: olive cloak and cowl no longer receive the painting's bright skin/tunic patches; narrow fold ropes use their wool fill rather than repeating an entire image crop.
All first-pass clips reviewed as strips; death is a held side collapse but still stiff, move is readable with alternating foot lift, and attack remains a small staff shove.
Earlier projection sheets/animations preserved in masters/scout/review-iterations/first-projection before refreshing review files.
Metadata decision: v2 keeps frame anchor and numeric clip counts, adds per-sample packed rectangle plus ox/oy; no v1 runtime loader changes in this art lane.
Rendered e-move 512 px CYCLES/CPU
Rendered e-attack 512 px CYCLES/CPU
Rendered e-hit 512 px CYCLES/CPU
Rendered e-death 512 px CYCLES/CPU
Rendered b 256 px CYCLES/CPU
Rendered d 512 px CYCLES/CPU
Rendered e-attack 512 px CYCLES/CPU
Geometry audit PASS for 53 bones, stationary base, nondegenerate objects, grip <=0.0426m, exact loop endpoint transforms and held death transforms. Contact diagnostic exposes body min Z 0.0519 at rest and 0.0007 in death vs base top 0.095: toe/body penetration remains a known round-1 defect; not a collision-free verdict.
Attack transition corrected: hand now eases from brow to brace and back; only attack/d rerendered, other clip source hashes retained.
Using six Blender skills: MPFB anatomy, solid folded clothing/bevels, textured Principled materials, warm key/cool rim, painting camera, authored keys/secondary cloth, denoised RGBA sequences.
Rendered b 256 px CYCLES/CPU
Rendered c 512 px CYCLES/CPU
Rendered c-details 512 px CYCLES/CPU
Rendered d 512 px CYCLES/CPU
Rendered e-idle 512 px CYCLES/CPU
Initial pack: 194210 bytes at quality 75, but validator correctly failed bottom clipping (idle bounds reached y=512). Candidate withheld from final validation pending framing correction.
Final correction: lower camera aim to leave base margin; set rest and every sampled pose to evaluated body minimum Z=0.100 above base top 0.095. Full source/projection/clip/render chain regenerating; prior reviews retained in pre-framing-fix.
Rendered e-move 512 px CYCLES/CPU
Rendered e-attack 512 px CYCLES/CPU
Rendered e-hit 512 px CYCLES/CPU
Framing recheck: idle/move/attack margins restored. The hit peak still lifts the staff to y=0, so reduce only the torso recoil amplitude and refresh the four hit frames after the serial render completes; head/arm recoil remains.
Rendered e-death 512 px CYCLES/CPU
Rendered e-hit 512 px CYCLES/CPU
Rendered e-death 512 px CYCLES/CPU
Post-framing body audit: every one of 40 sampled poses has body min Z=0.100. Hit recoil amplitude reduced to keep staff 10px below top boundary.
Second atlas validation isolated cape penetration in death. Added per-sample actual-geometry contact shape keys for cloak and hem at Z=0.108, preserving real shell thickness; refreshing only death.
