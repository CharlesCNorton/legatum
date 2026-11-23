# Phalangite round 1

Candidate, not approved for runtime use. The standing painting-parity bar has
not been met; no `phalangite-PASS` marker is written.

The editable scene is `~/LegatumRuns/anim-pilot/masters/phalangite/phalangite.blend`.
It contains MPFB anatomy/weights, physical layered kit, projected original
painting colour, three AO/curvature pairs and the stationary cream base. Five
separate clip scenes live under `clips/`. The `512/` and `256/` directories retain
CPU preview masters; raw frames and their engine/device/sample/source reports
live under `renders/`. GPU output replaces those preview sets only when the lead
runs `tools/art/anim3d/units/phalangite/gpu.sh` from this checkout's root.

The first plain and textured reviews are retained in the external
`review/3d-v2/phalangite-interim/` directory. Latest named sheets, animated WebPs,
rest-pose split-screen and running log are in `review/3d-v2/`.

## Visual verdict

At 256 px the unit is recognizable but distinctly less finished than the
painting. Painting projection restores red cloth and ivory armour brushwork;
the long diagonal sarissa and small forearm shield distinguish it from the
spearman. The face/helmet registration, shoulder anatomy, straight lower arm,
calf/greave volume and shield shading still need refinement. Some projected
colour crosses physical material boundaries. Fine projection does not replace
correct sculpture. The stone is warm but more uniformly shaded than the source.
At 64 px the class and palette read correctly, but the figure remains too narrow
and its surface highlights are less deliberate than the painting's.

The five clips are authored rig animation. Hand-to-weapon measurements use a
fixed palm proxy rather than finger contact surfaces. The current maximum proxy
errors are recorded per clip in `animation-audit.json`; these are diagnostic,
not a claim of perfect grips. The body fall and released shaft need motion review
on the GPU, as do sleeve/chest and shield/forearm intersections. Cloth folds are
modelled and rigged, not simulated. There is no exhaustive collision solver.

## Reproduction and checks

Use the Phalangite chapter of `../../PLAYBOOK.md`. Source images are pinned in
`assets.lock.json`; `prepare.py` verifies them. `run.sh audit` checks the saved
3D scenes, loops, held death and source hashes. `deliver.py pack` validates all
40 frames, per-frame trimming, motion, alpha margins, held death, common grade,
current scene hashes and the quality/size cap before delivery. `deliver.py
validate` rechecks the emitted atlas. `gpu.sh` adds the eight-second five-column
MP4 required by the overnight driver.

Non-obvious finding: projecting the painting's exact pole diagonal can put the
painted lower hand beyond the current MPFB arm's reach. Check arm reach in 3D
before texture registration; a good 2D line match is not a valid two-handed pose.

## Recorded round-1 verification

- 48 review/master PNGs at 512 px and 48 at 256 px, including all 40 clip frames.
- Atlas: 1600×800, 160 px reconstructed cells, 193,974 bytes, WebP quality 80.
- Pack and decoded-atlas validation passed: 8/8/10/4/10 frames, trim offsets,
  transparent padding, current scene/frame/grade hashes, motion and held death.
- Saved-scene audit passed for all five clips: 19,158-vertex MPFB body, 53 bones,
  projected UVs, six baked maps, stationary base, loop boundaries and settled pose.
- Review MP4 verified with ffprobe: H.264/yuv420p, 1600×360, 192 frames, 8 seconds.
- Python syntax, shell syntax and `git diff --check` passed.
- CPU masters use Cycles, 512 px, 8 samples. The Metal GPU pass was not run in
  this sandbox. GPU output may require a different quality in the allowed 90–75
  range; the handoff refuses an atlas over 200,000 bytes.
- Sampled base patch: painting #FACE9E, render #EED4B6. The render is warm but
  still too pale relative to this painting and the shared #E9CFA0 target.

The terminal death is sampled twice from frame 9. Copying that rendered sample
prevents tiny repeated-evaluation/noise differences from making the hold shimmer;
all ten requested output frames remain present. The corrected corpse remains
inside the cell, although the fall still needs more natural articulation.

Commit was attempted with the requested co-author trailer, but this sandbox
refused `.git/worktrees/lane-14/index.lock`; changes are left uncommitted for the
runner. `tools/gates/check.py HEAD --base origin/master --checks-only` therefore
checked only the existing HEAD: hygiene and public-claims passed; art failed when
`render-sets.mjs` exited 1. It is not a gate result for this uncommitted candidate.
The unit artifact, geometry, syntax and video checks above cover the actual work.
