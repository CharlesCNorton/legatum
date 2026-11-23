# Pass 1 — blocked before the first render

This is a setup record, **not one of the three required completed visual passes**.
No atlas, rendered comparison sheet, gallery screenshot or performance result has
been produced. Passes 2 and 3 have not started.

## Work prepared

- Four camera-projected, articulated relief rigs using the actual `-256.png`
  paintings, with armature hierarchy and 40 keyed poses per unit: idle 8, move 8,
  attack 10, hit 4, death 10. Blender masters are outside git.
- Rebuild scripts for projection preparation, modelling, Eevee render, packing,
  metadata, grey/parchment frame sheets and animated previews.
- Standalone Canvas 2D gallery with source paintings, five clip viewers, 256 px
  inspection, 80 px tokens on the game's ground palette/tuft strokes and shipped
  terrain art, controls, mirror and 300/600-token benchmark.
- Headless Chromium capture harness at deviceScaleFactor 1; strict 200,000-byte
  atlas validation and under-4-ms mean draw assertion for 300 tokens.
- Missing atlases are explicitly labelled unavailable in the gallery. No copied
  static painting is passed off as an animated atlas.

## Evidence and blockers

`tools/art/anim/build.sh spearman 1` failed during the first Eevee render:

```
gpu.metal | WARNING Could not initialize Metal: no default Metal device available.
Abort trap: 6
```

Headless Playwright `chromium.launch()` also failed in this macOS sandbox:

```
bootstrap_check_in org.chromium.Chromium.MachPortRendezvousServer: Permission denied (1100)
```

The documented cloud fallback (`tools/cloud/remote.sh . --budget 600 ...`) failed
before running its probe: it could not update its cached instance state in the
sandbox. A direct AWS identity check returned `InvalidClientTokenId`, so no usable
cloud session was established. No bucket upload was performed.

`nice -n 10` was used as requested; the sandbox also printed `setpriority:
Operation not permitted`. All Blender scene configurations use four fixed threads.
Builds and the audit mode share an atomic lock. No long simulation or build ran.

## Source review and changes

The four map paintings and panel references were opened at original and enlarged
sizes. Their kits are distinct: bronze sunburst shield/red crest for Spearman;
white-clad rider on a brown horse; blue-coated gunner with bronze field gun; red
cloak and lambda aspis for Spartan Hoplite. The projection preserves their colour,
figure, facing and painted highlights. The models are shallow relief, not all-angle
volumetric reconstructions; this remains a material limitation against the brief.

An independent **Codex** art-scaffold reviewer inspected the sources and preparation
textures. This was not the project's required Claude art review and supplied no
final visual approval. It found:

- Missing paint under separated parts: added six pixels of adjacent-pigment overlap
  under joints and shield edges. Larger reveals still need hand painting.
- Patchy bands on the first reconstructed base: replaced thresholded source copying
  with a continuous cream low cylinder and soft contact shading. Opened the revised
  base PNG and verified the conspicuous concentric band was gone.
- Wheels rotating in screen space: changed to compressed axle space so rotating
  spoke geometry retains the projected ellipse. Still needs rendered inspection.
- Smoke close to the frame edge: reduced drift and radius.
- Death was mostly a compressed root rotation: unresolved motion-quality risk,
  especially for the horse. This is not excellent animation and is not approved.

The CPU rig audit then caught clipping in Horseman death and Hoplite attack.
Reduced the horse fall translation and Hoplite spear swing; both audits now pass.
These checks sample projected opaque texels and cannot assess seams, jitter,
alpha fringe, foot slip, contact weight or loop smoothness. Those remain unreviewed.

## Results

| Unit | Keyed poses | Rendered frames | Atlas KB | Visual fidelity |
| --- | --- | --- | --- | --- |
| Spearman | 8/8/10/4/10 | 0 | unavailable | unreviewed relief projection |
| Horseman | 8/8/10/4/10 | 0 | unavailable | unreviewed; fall and trot need work |
| Field cannon | 8/8/10/4/10 | 0 | unavailable | unreviewed; crew contact and wheel occlusion need work |
| Spartan hoplite | 8/8/10/4/10 | 0 | unavailable | unreviewed; thrust/weapon grip need work |

300-token average/p95: **not measured**. 600-token average/p95: **not measured**.
No gallery screenshot has been captured or reviewed.

Completed checks:

- `build.sh <slug> 1 --model-only`: passed for all four units.
- `build.sh <slug> 1 --audit-only`: final audits pass for all four. They verify
  40 poses, a stationary base, fixed four-thread Eevee configuration, transparent
  film and sampled projected bounds. They are not render validation.
- `venv/bin/python tools/art/anim/test_pipeline.py`: **1 test passed**, exercising
  all four unit contracts and 160 synthetic frames through PNG → WebP/JSON →
  decoded validation. These temporary fixtures are not delivered art.
- `node --check` for the inline gallery script and `capture.cjs`: passed.
- `bash -n` for `build.sh` and `pass.sh`: passed.
- Python `compileall` for the animation tools: passed.

Full repository gate result is recorded in `checks.md` after the final invocation.

## Resume

Restore an environment where headless Eevee and Chromium can run (or usable cloud
credentials), then run `tools/art/anim/pass.sh 1`. Open every screenshot and sheet,
critique and fix, and complete at least three actual render/review passes. Do not
count this blocked preparation record as a pass. Obtain Claude art review before
merge. The final task instruction leaves pushing to the runner.
