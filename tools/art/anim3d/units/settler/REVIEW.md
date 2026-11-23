# Settler resumed round 2

Not art-approved; no PASS marker. The static painting remains in use.

The actual full-depth hood, garments, hair, belt, pack and bedroll now fit recorded
painting landmarks before one frozen camera projection. Independent per-garment
UV stretching is removed. Finished rigid surfaces and frozen MPFB macro shapes
retain original anatomy/weights and all 53 bones. Camera-only painted illumination,
existing generated hidden fills, ten AO/curvature bakes, softer product lighting
and one automatic rest grade preserve more of the painting's color. Ankle-bone
posing staggers the feet; the staff leans in depth. Death retains robe coverage
with shallower knee relaxation and less cloth compression.

At **256 px**, face/hood registration and painted cloth detail improved, but the
robe silhouette, sleeve contours, sandals/contact and base shading remain visibly
different. At **64 px**, identity is clear and the silhouette is closer; it is
still distinguishable. Measured on both graded 256px images with alpha >128,
silhouette IoU rises from 0.775618 to 0.843796. This is not painting parity.
Idle/attack/hit are restrained; walking contact still needs polish, and death
remains too stiff. The separated calf visible in the first death trial is fixed.

## Evidence and checks

- Current CPU Cycles8/256: all stages and 40 animation samples rendered and reviewed.
- 160px trimmed atlas: **172,316 bytes, quality 90**, original 8/8/10/4/10 counts,
  full 8-bit alpha, fractional anchor and exact decoded death hold. Pack and
  independent validation pass, including source hashes, offsets and clipping.
- Saved geometry audit passes: native body vertex count, 53 bones, frozen macro
  keys, motion, loop closure, stationary base, held death and ten bake hashes.
  Contact and camera bounds are recorded; this is not a full collision solver.
- `settler-round2.mp4`: decoded atlas, five clips side by side, H.264/yuv420p,
  1600 x 352, 192 frames/eight seconds. FFprobe verification passes.
- Python syntax (13 files), Bash syntax (two scripts), whitespace and working-tree
  hygiene line checks (20 files) pass. Public-claims gate passes. The revision-based
  hygiene gate still reads the old WIP: Git index.lock writes are sandbox-blocked,
  so the runner must commit these changes and rerun that gate.
- Repository browser art gate is blocked by Chromium Mach-port bootstrap permission
  denial in the sandbox; its visual distinctness check did not complete.
- GPU missing-input preflight and CPU-master rejection pass. **No actual Metal
  execution was possible in the sandbox.** Fresh GPU512/64 output is still owed.

Review images/WebPs, MP4 and running log are in `review/3d-v2/settler-*` under
`~/LegatumRuns/anim-pilot/`. Current 256px PNGs, editable masters and manifests
are under `masters/settler/`. Earlier 512px CPU evidence is retained in
`round1-backup`; current CPU256 previews are not upscaled or labelled GPU masters.

## Complete GPU handoff

From the repository root, with ROUND supplied by the driver:

```sh
tools/art/anim3d/units/settler/gpu.sh
```

The executable, no-argument entry point renders plain/rest/details/poses and every
clip on Cycles GPU64 at 512px, exports 256px copies, audits, checks GPU provenance,
packs/validates the atlas and writes `settler-round${ROUND}.mp4`. It retains its
transcript and failing stage; a completion receipt requires every stage. It never
writes PASS. Review the actual GPU output before accepting the art.
