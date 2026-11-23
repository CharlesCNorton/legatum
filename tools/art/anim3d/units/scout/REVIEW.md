# Scout round 2 candidate

Unapproved art candidate; no PASS marker. The existing painting remains the game token.

The raised-knee stance, face and cloth brushwork are substantially closer at 256px.
Silhouette intersection-over-union is 0.7665 versus round one's 0.6299 at alpha >24.
At 64px the forked staff, ochre tunic, olive cloak and raised scouting pose identify
the same unit, but the silhouette is still distinguishable. At 256px the cowl has
unpainted islands, the hat/hand contours differ, the raised sandal floats above the
rear disc, and the stone and motion remain simpler than the painting. No technical
check establishes artistic acceptance or complete cloth/equipment collision freedom.

The physical pose now fits camera rays while preserving skeletal segment lengths;
arms are lengthened 17% without compounding child scale. Tailored skirt/cape/cowl
geometry retains depth, weights and real thickness. Grounding moves along the camera
ray so it does not undo landmark registration. Registered targets initialize combat
poses. Cloth follow-through/contact remains authored shape keys, not a cloth simulation.

One frozen projection replaces the former stretched per-part source boxes. The old
projection skipped the body because MPFB helper masks changed the evaluated topology;
freezing the macro mix and applying those masks now permits skin projection. The audit
requires it. Finished rigid surfaces, existing generated fills, actual AO/curvature,
beveled straps, hair and product lighting remain. Camera-only painted illumination
avoids double shading; the original physical BSDF handles indirect rays. One measured
rest grade is frozen for all clips. Detail crops use full-resolution painting/render
pixels and disclose their actual source resolution.

All outputs are under `~/LegatumRuns/anim-pilot/masters/scout/` and
`~/LegatumRuns/anim-pilot/review/3d-v2/scout-*`; original round-one evidence is preserved
in `masters/scout/round1-preserved/`. Masters stay outside git.

The driver's single executable command, from the repo root, is:

```sh
ROUND=2 tools/art/anim3d/units/scout/gpu.sh
```

It rebuilds all five clip masters, renders every stage with Cycles Metal GPU64/512,
derives 256px gallery copies, audits the rig/projection, checks actual GPU provenance,
packs the trimmed 160px atlas, validates it and writes the eight-second five-clip MP4
from decoded atlas pixels. The output is H.264/yuv420p, 1600×348, 240 frames, 2× on cream.
Its retained transcript and success-only JSON receipt distinguish a completed GPU pass
from an absent/failed one. It never writes the art PASS marker. Missing-input rejection
and CPU-master rejection were exercised; actual Metal rendering is host-only.

The atlas retains the existing scout `formatVersion:2` contract with `trims` rectangles
and offsets, all 8/8/10/4/10 samples and the quality >=75 / 200,000-byte cap. This lane
does not activate the atlas in the game. The lead still needs to review fresh GPU art.

Final CPU validation: all 40 frames and trim rectangles pass source hashes, reconstructed
alpha, timing, motion, image margins and held-death checks. The atlas is **199,216 bytes
at quality 80**, 1165×743, with 32 alpha levels. All 40 samples have actual 512px masters
and derived 256px gallery copies. The rig/projection audit passes; body minima are
Z=0.100 throughout. Twelve Python files and three shell scripts pass syntax checks;
GPU missing-input and CPU-master rejection checks pass. The decoded MP4 is verified
H.264/yuv420p, 1600×348, 240 frames/eight seconds. All five strips were inspected.
Motion remains stiff and contact is not fully solved; no claim of five clean clips.

Git could not create this worktree's `index.lock`; changes remain uncommitted for
the runner, with the requested co-author trailer. Whitespace checks pass. No
commit-based repository gate result is claimed from stale HEAD. No push or merge.
