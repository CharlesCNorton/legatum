# Barbarian archer, round 1

A true 3D review candidate built on MPFB's 19,158-vertex body and 53-bone rig.
It has original wolf-head pelt geometry, layered fur locks, solid folded clothing,
boots, stitched straps, buckles, quiver, a deforming bow and a hand-tracked string.
The 40-frame set is idle 8, move 8, attack 10, hit 4, death 10. Only idle/move loop.
The final two death samples hold exactly. No runtime integration or art approval.

The model, packed textures, eight real AO/curvature bakes, clip blends and genuine
512/256 pixel CPU preview masters live in `~/LegatumRuns/anim-pilot/masters/barbarian-archer/`.
Review sheets, animated WebPs, the split-screen/crossfade and the running log live
in `~/LegatumRuns/anim-pilot/review/3d-v2/barbarian-archer-*`.

At 64 px, the crouch, hood, red wrist binding and drawn bow carry the same broad
identity. The painting remains richer and clearer. At 256 px, this is below the
painting: the face and bow hand have projection artifacts, fur locks are coarse,
the torso and bow curvature do not register exactly, and some cloth/boot surfaces
look flat. Generated hidden-side fills preserve material identity during motion,
but cannot repair those geometric differences. The cloak is bone-deformed with
modelled folds, not simulated. Move is an authored in-place cycle; contact and
weight transfer need further visual refinement. Death folds across the front edge
of the base and needs a more natural fall in a later round.

The CPU images use four samples and denoising. They are provisional previews,
not a claim about the final Metal image. Run this executable from repo root:

```sh
tools/art/anim3d/units/barbarian-archer/gpu.sh
```

It requires Metal Cycles, renders all stages at 512 px/64 samples, writes 512/256
masters and all reviews, packs the trimmed 160 px atlas at quality >=75 and <=200 KB,
and validates. The pipeline fails on missing/stale source masters, missing frames,
clipped frame bounds, a detached bow grip, moving base, unsettled death or an
oversized atlas. It is not a general body/cloth collision solver.

The generated fill prompt and pinned input hashes are alongside these scripts;
URLs/licences are recorded in the external `assets/SOURCES.md` and the repository's
`app/src/assets/PROVENANCE.md`. New operational finding: MPFB eye import removes
unused materials, so create the kit's materials after fitting the eyes. Garment
weight transfer must account for evaluated topology rather than assuming identical
vertex indices after subdivision.

Round-1 checks passed: Python compilation, shell syntax, whitespace diff check,
source/master hashes, 53-bone/19,158-vertex anatomy, eight nonconstant AO/curvature
maps, grip distance <=0.0453 m, stationary base, 40-frame counts and motion,
transparent padding and trim bounds, exact terminal death hold, and all 512/256
masters and review files. The atlas is **189,756 bytes at WebP quality 80**.
`barbarian-archer-g-decoded-atlas.png` reconstructs sample frames with their trim
offsets from the actual lossy atlas. Final Metal rendering and lead art review
remain outstanding. The CPU base is also paler/less golden than the painting.
