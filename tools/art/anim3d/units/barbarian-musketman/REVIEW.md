# Round 1 — CPU candidate, not approved

The model is genuine MPFB anatomy and a 53-bone rig with solid modeled clothing and equipment.
The original painting is frozen onto its rest-pose mesh UVs; hidden surfaces use the existing
licensed generated fills. This is not a billboard, depth card or a painted relief plane.

At 256 px it remains visibly below the painting: the hat is too smooth and broad, the face is partly
hidden, the sleeve/coat forms lack the source's crisp tailoring, and projected details stretch on
faces revealed in motion. The warm grade has been reduced after visual review. At 64 px the
kneeling pose, feathered hat, red sash, bandolier and horizontal musket identify the same unit,
but the head and hat silhouette still need closer matching.

The five actions exist and have their required sample counts. Idle is restrained; move is a
supported kneeling shuffle, not an upright walk. Attack and hit retain the musket, with authored
recoil and visibility-keyed effects. Death releases the musket and holds its terminal pose. The
collapse and cloth remain stiff, and smoke is still too solid. These are round-2 art/motion issues,
not a visual pass. No PASS marker was written.

CPU previews were rendered at 512 px with two Cycles samples and denoising, then retained alongside
256 px derivatives. They establish framing and delivery, not final surface quality. The lead must
run `ROUND=1 tools/art/anim3d/units/barbarian-musketman/gpu.sh` for the complete 48-sample Metal
Cycles pass and review its outputs again. All stages, five animated WebPs, rest/crossfade comparison,
512/256 masters, trimmed atlas, validation report and eight-second MP4 are produced by that script.

The final CPU atlas is **194,550 bytes at WebP quality 80**, with all 40 frames and 32 alpha levels.

Verification: Python compilation, shell syntax, atlas/trim/hash/alpha/frame-count/motion/size checks,
and skeletal/base/held-death audit. MP4 is checked with ffprobe. Two targeted unit-art Vitest suites
could not execute: the cloud box was unavailable, and the local fallback lacks the generated
`app/src/wasm-pkg/legatum.js`. No Rust or runtime UI code changed.

Non-obvious pipeline findings: cancel the complete bone-parent matrix (including the tail offset)
in `matrix_parent_inverse` when attaching rigid kit to scaled posed bones, otherwise decomposition
can introduce visible offsets. Diagnose projected vertex-facing weights before tuning a material:
the hat brim initially had zero weights from reversed winding. Keep a generous feather margin
through the whole death action and validate the downsampled 160 px frames, not just 512 px bounds.

Git could not create `.git/worktrees/lane-22/index.lock` (Operation not permitted). Changes are
left uncommitted for the runner. Commit-based repository/art gates must run after that commit;
no result from the older HEAD is presented as validation of this candidate.
