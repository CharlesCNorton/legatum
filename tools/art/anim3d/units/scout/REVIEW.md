# Scout round 1 candidate

This is an unapproved 3D art candidate. It does not replace the painted game token.
The rest-pose split-screen remains visibly different from the painting at 256 px.

Implemented: MPFB anatomy, editable 53-bone rig, original clothing and scout kit,
real AO/curvature bakes, rest-camera UV colour from the painting, material masks,
generated unseen-surface fills, warm product lighting and one measured colour grade.
Idle/move/attack/hit/death contain 8/8/10/4/10 samples. Cape motion is authored shape
keys. There is no cloth-simulation claim and no downloaded mocap in this unit.

The recognizable cues at 64 px are the forked staff, hand at the brow, ochre tunic,
olive cloak, satchel and cream base. The image remains narrower/straighter and the
head smaller than the reference. The raised-knee scouting stance, expressive face,
beard/hair silhouette and fine cloth/leather finish need another modeling round.
The hat is too circular and exposed; the tunic hem is too regular. Projection helps
surface detail but does not repair those forms. Review the cowl/hem registration
and hidden-side transitions during motion. Attack is a modest staff shove; death
folds into a held side collapse and needs more natural ground settling.

Every published stage and animation is under `~/LegatumRuns/anim-pilot/review/3d-v2/scout-*`.
Earlier projection review images are retained under `masters/scout/review-iterations/first-projection/`.
The log distinguishes the initial defects and the material-mask correction.
Masters, licensed inputs, raw/graded 512px frames and derived 256px gallery frames
are external. Source and render hashes travel with the pack report. The decoded
160px trimmed atlas is reviewed separately; its v2 rectangle/offset contract is
in the scout PLAYBOOK chapter and is not wired into a v1 runtime consumer here.

For the lead's GPU review, run from this branch:

```sh
UNIT=scout RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64 RESOLUTION=512 tools/art/anim3d/render.sh final
UNIT=scout tools/art/anim3d/render.sh pack
UNIT=scout tools/art/anim3d/render.sh validate
```

`final` renders saved masters, establishes the GPU grade, renders all clips and
audits geometry/rig invariants. It does not rebuild or overwrite authored motion.
A fresh visual verdict is necessary after GPU rendering. The audit validates
stationary base, nondegenerate object scales, MPFB rig/topology, staff attachment,
loop endpoints and held terminal transforms; it is not a full collision solver.

The first geometry audit found toes penetrating the disc (minimum body Z 0.0519
at rest and 0.0007 in death, versus a 0.095 base top). The final build places the
rest anatomy at Z 0.100 and each authored sample computes the same clearance from
evaluated body vertices. This corrects skin contact but does not solve all cloth,
sandal or equipment intersections. The framing was also lowered after the first
atlas validator caught the base reaching the bottom image edge.

The death cape originally continued below the stone and clipped the image. Keyed
contact corrections now lift the actual cloak/hem vertices onto Z 0.108 during the
collapse, retaining the Solidify thickness. This is authored contact deformation,
not physical cloth simulation. It prevents the obvious penetration/crop; the final
fold pattern and collapse timing still need an artist's next pass.

Final CPU checks (2026-11-22): 40/40 frames and trim rectangles pass; all clipping
margins pass; exact held death pixels and rig loop endpoints pass; all body minima
are Z=0.100; maximum hand-to-staff surface distance is 0.0426. The atlas is 1161×754,
**199,794 bytes at WebP quality 80**, with 32 alpha levels. Every sample has a real
512px master and derived 256px gallery frame. Nine Python scripts parse; both shell
entry points pass `bash -n`; `git diff --check` passes. These are CPU previews,
not a GPU or artistic approval.

Git delivery: the sandbox denied creation of the worktree's `index.lock`, so the
runner must commit these changes with the requested co-author trailer. Commit-based
repository gates were not run against stale HEAD. No push, merge, PR, bucket or
runtime activation was performed. The lead's GPU render and art verdict remain outstanding.
