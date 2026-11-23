# Round 2 — CPU candidate; no visual PASS

The rest pose is closer to the painting after full-depth hat/crown registration, cambered feather
vanes, finished-surface UVs and camera-only painted pigment. The physical cream disc no longer
retains painted feet/shadows when the model moves. Generated hidden-surface fills, solid straps,
folded clothing, MPFB anatomy/weights and actual AO/curvature maps remain intact.

At 256 px the feather is too thin, the face and hat contours still differ, and the cream stone lacks
the painting's fine texture. At 64 px it reads as the same kneeling musketman, but silhouette and
base differences remain visible. Smoke is now volumetric but smaller than the painted firing cloud.
The source-motion death exposes stretched paint, rigid coat panels and imperfect terminal contact;
this is not five visually clean final clips. **No PASS marker was written.**

Shared feedback 23 arrived mid-round. Four non-attack clips now use the pinned CC0 Quaternius
Universal Animation Library Standard; attack keeps authored musket recoil. Reference-pose world
rotations cancel source rolls before a fixed axis conversion. Kneeling support and grip constraints
adapt the crouch cycle. The move is deliberately a low tactical shuffle, not an upright walk.
Front/top foot checks and a decoded-atlas sheet are included. The source death's leg directions
progressively replace kneeling offsets; mixing local and world coordinates under a rotated root
initially stretched those legs, and the new length audit caught/prevents that failure class.

Verified CPU delivery: Cycles **512 px / 6 samples**, 62 genuine 512 PNGs and 62 matching 256 PNGs
(including both eight-frame foot-check views). All 40 clip frames remain 8/8/10/4/10. The trimmed
160 px atlas is **182,976 bytes at WebP quality 80**. The decoded five-clip MP4 is H.264/yuv420p,
1600 × 348, 240 frames, exactly 8 seconds. Prior round-one evidence remains in `round1-cpu`.

Checks passed: six isolated delivery regressions (valid candidate, altered atlas, stale frame,
stale rest, independent trim-offset/alpha rejection and CPU-as-GPU rejection); master/clip/frame/
metadata/grade hashes, alpha, dimensions, timing, motion and identical held death; 53-bone rig,
stationary base, safe scales, leg lengths, planted support and left-hand grip; 172 finished meshes
with zero measured sampled rest-UV error. Maximum support-hand error is 0.00000024 m. Python
compilation, Bash syntax and whitespace checks pass. These checks do not prove collision-free cloth
or artistic equivalence. No Rust, gameplay or runtime UI code changed.

The executable no-argument GPU handoff was exercised: it records its transcript/status and fails
at preflight because this sandbox has no Metal device, before rebuilding. No successful GPU pass
is claimed. On the host, from the musketman checkout, run:

```sh
ROUND=2 tools/art/anim3d/units/barbarian-musketman/gpu.sh
```

It rebuilds/bakes, authors clips, renders all stages at GPU512/48 samples or higher, exports masters,
packs/validates, runs regressions and writes the round MP4 plus a GPU receipt. Visual review remains
required; the script never creates PASS.

The runner switched lane-22 to reislaufer during this round and preserved the scripts in WIP
`3c7b309a`. Continuation uses `legatum/.worktrees/barbarian-musketman-round2` on the original
`astra/unit-anim-3d-barbarian-musketman` branch. The final atlas was moved into that checkout;
no source files from the newly assigned lane were changed. Use this isolated checkout for follow-up.
