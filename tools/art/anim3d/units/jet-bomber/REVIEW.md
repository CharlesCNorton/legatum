# Round-one review

Candidate only; **no PASS marker**. At 64px the eight-engine swept-wing identity,
camouflage and cream stand read as the painting. At 256px the near/far wing
outlines and thickness, paired pod positions, tailplane shape, stone shading
and surface richness still differ. Frozen source lighting becomes apparent
when banking; unseen sides are an approximate olive fill. Crash motion is
readable but the wing/nose deformation and terminal contact need further craft.
No runtime wiring changes are included.

Final local evidence: Cycles CPU, 12 samples, actual 512px renders (not upscaled)
and derived 256px masters. All 40 frames exist at both sizes. All b/c/details/d,
five e-strips and e-WebPs, f-restpose-compare, and g top/nose move-cycle reviews
are in `~/LegatumRuns/anim-pilot/review/3d-v2/`. First geometry/texture evidence
is preserved in `masters/jet-bomber/first-stage/`.

Checks completed:

- Closed manifold fuselage/wings/fin/intake rims; eight intakes, six real
  AO/curvature bakes; no near-zero scale; stationary base; five keyed clips;
  idle/move endpoint closure and two-frame terminal wreck: pass.
- 40-frame logical 160px trimmed atlas, quality **85**, **178,572 bytes**;
  exact alpha reconstruction, offsets, transparent padding, nonoverlap,
  clipping margins, source/grade hashes, visible motion and identical decoded
  death hold: pass.
- Five-clip 2x MP4: H.264/yuv420p, 1600x348, 240 frames, 8.000 seconds: pass.
- Eight Python files parse; both shell entry points pass `bash -n`; tracked
  diff and all unit source whitespace checks pass.
- Input/source build preflight passes. Full `gpu.sh` tested to device discovery:
  expected explicit failure because Metal is unavailable in the sandbox.
  No GPU render claim. Run `ROUND=1 tools/art/anim3d/units/jet-bomber/gpu.sh` on
  the lead host, then review the new output against the painting.
- Git staging blocked by sandbox denial creating worktree `index.lock`.
  Runner must commit. No push or PR; requested commit message is preserved in
  external `masters/jet-bomber/commit-message.txt`.

Non-obvious finding: projecting from nonplanar quad centroids can falsely reject
visible wing pigment because the centroid lies below its triangulated surface.
Sampling visibility at finished mesh vertices avoids that error. Keep bevel
and subdivision application ahead of the frozen camera UV pass.
