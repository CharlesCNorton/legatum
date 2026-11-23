# Archer — round 1

Review candidate, not approved or connected to the runtime. Built with MPFB
anatomy and real fitted geometry, frozen-camera painting UVs, painted unseen-side
fills, AO/curvature bakes and five skeletal clips. Source inputs are pinned in
`assets.lock.json`; attribution is in the central art provenance table and the
external `assets/SOURCES.md`.

The external `review/3d-v2/archer-*` files contain the initial plain review,
textured rest, details, rest split/crossfade, four attack poses, five full strips
and animated WebPs. `archer-log.md` records intermediate defects and corrections.
Masters and raw frames are under `masters/archer/`, never in git.

At 256 px this does not match the painting's craft. The drawing arm is narrower,
the face projection is imperfect, the shoulder cloth and crest need better
geometry, and the crossed straps are less refined. The projected colours help
but cannot repair silhouette or anatomy. The rest alpha silhouette overlap is
about 0.744. At 64 px the bow, pale crest, ivory skirt and braced stance identify
the archer, but the source remains broader and richer. The walk's drawn-bow
upper body is stiff. The modeled skirt has no cloth simulation. The death is
an authored collapse with a mesh-derived floor correction, not a physics solve.

The attack has a cheek-side hand follow-through and independent string release;
arrow visibility is keyed, never hidden by zero scaling. Bow/nock contact is
checked before intentional release. The base remains fixed; the final death
frame is held. Neither the geometry audit nor pixel validation guarantees all
cloth/body/kit intersections are absent.

For host GPU renders, use the sequential commands in the **Infantry: early-era
archer** chapter of `../../PLAYBOOK.md`. In particular, set `UNIT=archer`,
`RENDER_ENGINE=CYCLES`, `CYCLES_DEVICE=GPU`, `RESOLUTION=512`, `SAMPLES=64` and run
`render.sh c`, `c-details`, `d`, then `e-idle/e-move/e-attack/e-hit/e-death`.
Repack and validate after all GPU frames finish, and review them anew.

The 160 px atlas uses `trimmed-v1`, with source rectangles and logical-cell
trim offsets. It needs a format-aware runtime consumer; the old uniform-grid
crop code cannot use it. No game runtime code changed in this lane.

Validation of the final CPU candidate (2026-11-22): 40 actual 512 px frames and
40 transparent 256 px derivatives; trimmed 160 px atlas **938×763**, **188,696
bytes**, WebP **quality 75**. `validate.py` passed master/clip/frame/grade hashes,
exact decoded alpha and offsets, compression error, two-pixel margins, motion,
clip lengths and held death. `audit.py` passed all five clips, MPFB topology,
53 bones, fixed base, nonzero scales, bowstring contact, pre-release nock contact,
flat settled bow and loop closure. Python compilation (12 scripts), both shell
syntax checks, input texture hashes and `git diff --check` passed. GPU rendering
and the lead's visual approval remain pending.

A useful implementation correction: compose head translation and rotation in
one matrix assignment. Reading a pose matrix again before the dependency graph
updates can restore the old rotation, turning the crest edge-on.

The whole host GPU sequence is also available as `gpu-round.sh`, using the
shared `render.sh` dispatcher and defaulting to 64 samples. Its shell syntax
was checked; GPU execution was not possible in this sandbox.

Repository handoff: Git refused both `index.lock` (commit) and `ORIG_HEAD.lock`
(merge). Changes remain uncommitted for the runner. `origin/master` advanced to
`27fa4cb` during the run; the runner must merge it and commit with the requested
co-author trailer. The browser art check was attempted: after resolving the
missing local Playwright module through the main checkout's installation,
Chromium failed with `bootstrap_check_in ... Permission denied (1100)` and
SIGTRAP. This is a blocked check, not a pass; run it on the host/build box.
