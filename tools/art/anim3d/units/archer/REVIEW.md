# Archer — driver round 3

Art candidate, not approved or connected to the runtime. No PASS marker.
The round-two GPU pass succeeded: all forty 512/256 masters, 191,376-byte
Q90 atlas and a valid eight-second movie. That evidence is preserved under
`masters/archer/driver-r2-gpu/` and `review/3d-v2/archer-driver-r2-gpu/`.

Round three replaces the short shoulder patches with thick folded cuffs,
corrects their winding and binds their seams to chest/upper-arm weights while
preserving the exact rest surface. It replaces slatted crest tufts with a
continuous curved closed fan, refits quiver shafts and places the far cheek
plate behind the face. A newly generated clean stone plate textures the real
rounded disc with live contact AO; its alpha never hides geometry. Generated
linen underpaint softens exposed-fold transitions. Frozen camera projection,
real straps/bevels/folds, AO/curvature bakes, product lights and one automatically
fitted histogram grade remain.

At 256 px the cream stone, shoulder coverage and continuous crest improve.
Elbow pigment patches, face/gaze, calf lacing and quiver feathers still miss
the painting. At 64 px it is clearly the same archer, but stance/proportions
remain distinguishable. Rest alpha silhouette overlap is .818856, versus
.807612 before this round; this is a diagnostic, not art approval.
The full-depth plain views and 512 px detail master were inspected.

All five clips retain 8/8/10/4/10 frames. CC0 Quaternius idle/walk/hit/death and
the original bow attack remain unchanged. There are no post-retarget foot
rotation patches. Top/front feet diagnostics and all five strips were reviewed.
The fall stays framed and held but still exposes simplified skin/cloth and
unconvincing quiver contact; the drawn-bow gait remains stiff. This is not a
five-clean-clips sign-off. Cloth is skinned modeled geometry, not simulation.

Final CPU checks:

- All forty transparent Cycles 256 px/24-sample frames; real 512 px/24-sample
  detail master; every interim stage, five animated WebPs and rest split/crossfade.
- Scene/projection/foot audit PASS; finished UV error below .01 token pixels;
  sampled stance residual 0.00000115 m with maximum 0.0291 m root correction.
- Trimmed 160 px atlas: **197,360 bytes, Q90, 1222×750**, all forty frames.
  Full validation PASS: source/clip/frame/grade hashes, exact decoded alpha,
  offset reconstruction, gutters, margins, motion and held death.
- Movie PASS: H.264/yuv420p, 1600×348, 240 frames/eight seconds. Decoded atlas
  and sampled movie frames inspected. CPU preview is explicitly labeled.
- Python AST18, Bash syntax3 and git whitespace PASS. Source-input check PASS;
  missing-input GPU preflight, stale-craft rejection and CPU-master rejection PASS.

From the repository root, the lead runs:

```sh
ROUND=3 tools/art/anim3d/units/archer/gpu.sh
```

The executable no-argument entry point audits and renders every stage plus feet
at Cycles Metal 512/64; retains actual 512/256 masters; validates texture/craft
inputs, source hashes and gallery frame hashes; packs/validates the atlas;
and emits the round movie. It fails explicitly without Metal. Technical success
never writes PASS. Current modified masters still require this GPU pass.

Non-obvious findings: opposite cuffs need opposite winding; inverse-bind the
finished cuff before projection so its shoulder seam can deform; overlapping
crest slats create comb artifacts even with correct pigment; a clean generated
stone plate needs live contact AO and must never supply the mesh silhouette.
