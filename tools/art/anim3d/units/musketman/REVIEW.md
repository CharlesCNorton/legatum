# Musketman round-one review

Candidate only. No PASS marker. The game continues to display its painting.

Completed: full-depth MPFB model and 53-bone rig; buff coat, red breeches/sash,
stockings, leather boots, feathered hat, bandolier, solid musket/bayonet;
materials and six real 512px AO/curvature maps; all five skeletal clips;
512/256 CPU masters; b/c/details/d/e/f/g review sheets and five animated WebPs;
trimmed 160px atlas and eight-second side-by-side H.264 movie. External outputs
are in `~/LegatumRuns/anim-pilot/masters/musketman/` and `review/3d-v2/musketman-*`.
The final CPU render used Blender 5.3 Cycles, 512px, 8 samples and denoising.
GPU output has not been run or approved in this sandbox.

At native 256px, much of the painting's cloth, face and bandolier brushwork is
preserved. The rest pose is recognizably close, but not hard to distinguish:
the hat/feather contours differ; the base is too smooth and less warm; the gun
has brighter, simpler steel and less convincing wood volume. There are small
silhouette differences around the sleeves and breeches. At native 64px it
reads as the same buff-and-red musketeer with the long horizontal weapon.

The open walk shows alternating capture-driven footfalls with +X boot heading.
Every sampled move frame has a sole at the stone contact height. This does not
establish perfectly matched travel speed/no sliding: contact timing and the
transition from the braced idle to walking still need visual refinement.
Attack retains a two-hand grip and modest recoil; the smoke has nonzero volume.
The captured hit bends naturally but ends in a bent pose. Death is clipped from
CC0 Death01 with a diagonal fall heading to fit the fixed camera, a rigid weapon
release and held terminal frames. Its elevated legs, exposed skin/clothing
seams and uneven hidden-surface finish still look rough. Cloth is thick folded
geometry with death contact shape keys, not a physically simulated garment.

Verification:

- Scene audit passes: 53 bones, five animated clips, source hashes, fixed base,
  positive object scales, bone-length bounds and held terminal skeletal pose.
- 163 projected meshes match the finished rest camera UVs, maximum sampled
  error 0.0px; stone has no projected feet.
- All eight move samples pass boot heading (`forward.x > .70`; observed about
  1.0) and planted-sole height within 3mm of 0.104m. Maximum support-hand grip
  error across the four carried-weapon clips is under 0.001mm.
- Delivery validation passes: 40 frames, exact decoded alpha/trim reconstruction,
  fps/loops, real transparency, distinct motion, held death, master/clip/render/
  grade hashes. Atlas **189,256 bytes, quality 85** (quality 90 exceeded cap).
- Video probe passes: H.264, yuv420p, 1600×348, 240 frames, 8 seconds, all five
  decoded trimmed clips at 2× on cream.
- Six delivery regressions pass, including stale source/atlas/rest rejection,
  corrupt trim detection independent of the metadata hash, and rejecting CPU
  output as a GPU receipt. Python syntax, Bash syntax and whitespace pass.

Lead command, run from repository root, no script arguments:

```sh
ROUND=1 tools/art/anim3d/units/musketman/gpu.sh
```

The script rebuilds and GPU-renders all stages at 512px/48 samples, retains
512/256 masters, repacks, validates, emits the movie and verifies a GPU receipt.
Review actual GPU output and obtain the project's Claude art review before
integration. No Rust, rules or runtime UI code changed; no Cargo/WASM/app build
was needed for this asset-only lane.

Non-obvious finding: an ankle-to-ball bone axis is not the boot's forward axis.
Straightening that bone during T-pose calibration tilted an already flat boot,
raised the entire figure under floor contact, and cropped the feather. Calibrate
against the flat mesh contact pose before retargeting; never patch foot yaw in
the sampled animation. A captured full-length fall can exceed a camera framed
for a braced standing figure; a single diagonal fall heading preserves the
articulation while fitting the token, without stretching the body.

Commit handoff: Git staging was blocked by the sandbox (`index.lock`: Operation
not permitted), so the runner must commit these files. The requested co-author
message is in external `review/3d-v2/musketman-commit-message.txt`. Commit-based
repository/art gates and Claude art review remain for the runner/lead; the
checks above ran directly against the actual candidate. `HEAD..origin/master`
has zero commits, so no integration merge was needed.
