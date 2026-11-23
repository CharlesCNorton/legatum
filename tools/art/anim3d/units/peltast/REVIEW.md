# Peltast — round 2 candidate

True 3D MPFB anatomy and a 53-bone rig remain the source, with thick clothing,
solid equipment and original painting UVs. No billboard, alpha-shaped figure or
per-frame reprojection is used. The game still displays the original painting;
this atlas is an unwired candidate. Masters remain outside Git under
`~/LegatumRuns/anim-pilot/masters/peltast/`; round-one evidence is preserved in
`round1-cpu/`. Current review files use `review/3d-v2/peltast-*`.

This round broadens the tunic shoulders, reshapes the flared cloak, reduces the
fox ears/muzzle, tapers the nape hide, adds curls behind the ear and shortens the
beard. The round cream stone has a smaller diameter, deeper rim, subtle grain
and live contact shading. Static kit is finished before camera UV calibration;
the rigid-surface audit measures zero projected UV error at rest. The original
MPFB skin and animated cloak retain their deformation modifiers, so this is not
an assertion of exact final-surface UV correspondence on every deforming vertex.

Camera-only painted pigment, existing generated unseen fills, actual rebuilt
AO/curvature, warm key/soft fill/cool rim and one frozen automatic histogram grade
retain the painting's surface detail. The shader uses Standard/None specifically
for already illuminated source paint, not as a general photographic preset.

At **256 px**, the tunic, woven pelta and cloak are closer to the painting, but
the cap profile, face, boots and stone finish remain visibly different. At
**64 px**, it reads as the same red/blue peltast with a crescent shield and raised
javelin; silhouette and stone shading still distinguish it. Whole-token alpha
IoU improved from **0.77181 to 0.82345** (threshold 32/255), and figure-only IoU
from **0.77943 to 0.80778**. These are geometry measurements, not art approval.
**No PASS marker.**

Attack now begins and ends in the saved guard pose, independently audited.
The throw still needs a convincing spare-to-hand rearm; movement remains an
authored stepping guard, and death remains stiff. Cloth follow-through is a
weighted mesh with an authored shape key, not a simulated cloth bake. Technical
checks do not establish that all skin, cloth and equipment intersections are clean.

## GPU handoff

From the repository root:

```sh
tools/art/anim3d/units/peltast/gpu.sh
```

The executable no-argument script defaults to round 2; the driver can set ROUND.
It rebuilds the five clips, audits geometry, renders b/c/d/e using Cycles Metal
GPU at 512 px / 64 samples, writes 256 px derivatives and all review images,
checks GPU provenance, packs/validates the trimmed 160 px atlas and creates the
eight-second five-clip `peltast-round${ROUND}.mp4`. It retains a transcript,
failing-stage status and completion receipt with `art_approved: false`.
Actual Metal execution remains for the lead; no GPU success is claimed here.

The atlas retains 8/8/10/4/10 playback samples and all timing. Premultiplied
bicubic reduction avoids Lanczos alpha ringing. Identical frames share a trimmed
rectangle, preserving an exact decoded death hold. The packer tries full alpha
before bounded quantization and never goes below RGB quality 75 or over 200,000
bytes. Full-alpha 512/256 masters remain available.

## Findings for the next round

Every original shell sample sat under a raised wicker ring, so naive vertex
visibility removed almost all shield projection. Fit the rings onto their actual
support and exempt own reed/rim occluders; retain other-object occlusion checks.
The larger cap/body silhouette and moving reveals still need refinement.

Blender smart-project can invalidate an earlier UV-layer RNA reference when
leaving edit mode. Retain its name and reacquire the layer afterward. The first
rebuild failed with UnicodeDecodeError; the corrected six-map bake completed.

## Final local checks

- All 40 transparent clip masters are actual **512 px / Cycles CPU / 12 samples**
  with 256 px gallery derivatives, all required b/c/d/e reviews and animated WebPs.
- Atlas: **195,990 bytes at quality 80**, **1384 x 742**, 160 px logical cells,
  **lossless 8-bit alpha** and zero alpha error. All 40 samples remain in 39 unique
  rectangles. Q85 was 220,268 bytes and Q90 was 257,172; neither fits the cap.
- `validate.py`: PASS on source/grade hashes, frame counts, trim/alpha reconstruction,
  margins, visible motion, exact decoded death hold, master dimensions and rectangles.
- `audit.py`: PASS on full anatomy, 53 bones, finished rigid UV registration
  (**0.0 px error**), saved attack guard endpoints, stationary base, safe transforms,
  held death and both loop closures (**0.0 matrix error**).
- Video probe: **H.264 / yuv420p / 1600 x 348 / 240 frames / 8.000 seconds**.
  Inspected every clip strip, decoded 160/64 comparison and six decoded video frames.
- 15 Python syntax checks, two shell syntax checks, executable GPU entry, missing-
  input failure/transcript check, CPU-master rejection and `git diff --check`: PASS.
- Metal GPU rendering and the lead's post-GPU visual approval remain outstanding.
  No Rust, rules, UI or runtime changes; no Rust/WASM/app test suite was run.

This round remains below the painting bar: source-view cloth/wicker improved,
but the face/cap/boots, smooth stone, abrupt rearm and stiff step/fall need another
round. Successful technical delivery is not five visually accepted clips.

Git could not create this worktree's `index.lock`; staging/commit remains for the
runner. The available `origin/master` is already an ancestor, so no merge was
needed. No push or PR was made.
