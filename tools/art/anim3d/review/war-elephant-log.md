# War Elephant round 1
- Read mounted playbook, standing feedback 12–22, project art/design/UI guidance and all six Blender skills.
- Inspected 256/panel painting; two humans, cloth-armoured elephant and timber howdah. Mounted horse pack does not contain an elephant; built original elephant geometry.
- Built continuous remeshed anatomy, separate articulated curled trunk, 20-bone skeleton, MPFB officer and mahout, equipment and stationary cream stone.
- Generated original hidden-surface fills with built-in imagegen; preserved pinned external master and prompt.
- First rendered comparison exposed low riders, overlong trunk, broad tower and high camera. Preserved initial comparison under war-elephant-round1-initial/.
- Raised riders, shortened/raised trunk, narrowed and shifted howdah, reduced base radius and lowered camera elevation.
- Fixed macOS Bash 3 empty-array handling in unit wrapper; fixed review crossfade dimensions for 256 px CPU previews.
- b-plain: three actual 3D views emitted; c: projected painting colour with incidence blend and one rest-derived histogram grade.
- Candidate remains clearly distinguishable from painting; do not create PASS marker.
- Rig audit exposed foot sinking during hit; raised the rest stance and added ground correction to every clip. Tightened body-contact audit to z >= 0.125 above the 0.12 stone top.
- Death raw 512 views show shoulder-cloth projection spill, rigid humans and a body supported too high by folded legs; retained as next-round evidence.
- Packing now reuses identical logical frames at one atlas rectangle, keeping held death identical after lossy WebP decoding.
- Corrected attack tusk clipping with a smaller surge, downward head strike and officer spine brace; hit now recoils through the head/trunk. Final attack pose review has 3 px logical margin.
- Atlas validation exposed Lanczos alpha ringing at the edge of death frame 2 despite raw-frame clearance. Area-filtered alpha separately from Lanczos RGB; all 40 decoded frames now pass alpha/bounds/motion checks.
- Final atlas: 183608 bytes, quality 75, 160 px logical canvas, all 40 frames; duplicate held frames share one rectangle.
- Final rig audit passed all five clips: fixed base/camera, body minimum z 0.13, 20 bones, MPFB topology/weights, loop closures and held death.
- Python syntax (6 files), Bash syntax (2 entry points) and git diff --check passed. Source input SHA256 verification passed.
- cargo test -p legatum-sim --profile release-checked --test determinism: 12 passed, 0 failed.
- cargo test -p legatum-sim --profile release-checked --bin legatum-sim pinned: 2 passed, 0 failed. Both wrapped with tools/sim/build-slot.sh; automatic offloader used its low-priority local fallback because the build box was unavailable.
- origin/master advanced to 27fa4cb0747035bf4181e5abe6d8f284a3731203. Its crates tree exactly matches HEAD (ffb2dbc0d3be1c25d5492e1f2ece3921e3c72c8f). Merge was blocked creating ORIG_HEAD.lock; git add was blocked creating index.lock. Changes left uncommitted for the runner; no push or master merge.
- Art remains below painting parity at 256 px; recognizable at 64 px. No PASS marker. GPU rerender remains for the host via ROUND=1 tools/art/anim3d/units/war-elephant/gpu.sh.
- Final MP4 verified with ffprobe: H.264, yuv420p, 1600x348, 30 fps, 240 frames, 8.000 seconds. Decoded frame inspected for all five trimmed-atlas reconstructions.

# War Elephant round 2
- Opened the prior rest/split/crossfade, native 64 px comparison and death strip before editing. At 256 px the blanket is much too broad/red, timber enclosure too bright/tall, tusks and trunk overextend, riders misregister and stone is dull. At 64 px the elephant/howdah identity reads but the broad red rectangle and raised trunk clearly differ. Death hovers on folded legs and reveals source spill; not painting parity, no PASS.
- Loaded all six Sam Blender skills; read the complete shared feedback, local playbook and advanced spearman/field-cannon chapters. No war-elephant-specific feedback file was present. Round focus: volumetric registration, finished-surface frozen projection, camera-only painted illumination, physical cream base and grounded collapse.
