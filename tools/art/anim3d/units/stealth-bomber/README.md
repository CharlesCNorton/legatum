# Stealth bomber — round 1 candidate

Closed cambered flying wing, raised centre section, recessed intake wells, convex
framed cockpit and carved support on one cream disc. Frozen camera projection
uses the original project painting; hidden composite surfaces use licensed generated
brushwork. Actual AO/Pointiness bakes drive gentle wear. A rigid airframe hierarchy
and three independent bombs supply idle, move, attack run, hit and crash clips.

## Review result

At 64 px the flying-wing silhouette and supported miniature read as the painting's
unit. At 256 px the silhouette and painted surface detail are close, but the cockpit
and intake edges are softer; the support is slightly pink and the disc is too
uniform, with less fine stone texture. The crash is a restrained bank/descend/impact
and could use stronger impact articulation. Large viewpoint changes expose the
approximate unseen surface fill. **No PASS marker: visual parity is not established.**

CPU Cycles, 12 samples: 64 stage frames rendered at actual 512 px, with both 512 and
256 sets retained externally. All five clips total 40 frames (8/8/10/4/10).
The current trimmed 160 px candidate is **194,946 bytes at Q95**. Rest alpha IoU is
0.96135; opaque-overlap RGB MAE is 6.47/255. These are alignment measurements, not
art acceptance. GPU rendering remains pending.

External artifacts under `~/LegatumRuns/anim-pilot/`:

- `masters/stealth-bomber/`: editable plain/surface/painted and five clip blends,
  six 512 px bake maps, raw/graded 512 and 256 frames, grade, audit and pack receipts.
- `review/3d-v2/stealth-bomber-*`: plain, textured, details, rig poses, five strips
  and animated WebPs, rest/crossfade, top/front flight check, decoded atlas and
  `stealth-bomber-round1.mp4`. The initial sheets are retained in
  `stealth-bomber-round1-initial/`.
- `assets/stealth-bomber/`: archived source, registered projection and grey fill.

## Lead GPU handoff

From the repository root, with no positional arguments:

```sh
ROUND=1 tools/art/anim3d/units/stealth-bomber/gpu.sh
```

The script uses gated plain `blender` calls, Metal Cycles GPU512 at 96 samples by
default, renders every stage sequentially, exports the two master sizes, rebuilds
and validates the atlas, audits the rig/geometry, and writes the eight-second
H.264/yuv420p video. It records the checkout, a failure status or GPU receipt, and
fails explicitly if Metal is unavailable. It does not rebuild the model or write
PASS. A host GPU run must be visually reviewed; CPU results do not prove it passed.

To rebuild the model and bakes, run `render.sh build` in this directory from the
repo root. Rebuilding invalidates downstream renders. Full commands and trimmed
JSON drawing semantics are in the stealth-bomber chapter of `PLAYBOOK.md`.

## Checks run

- Five delivery regression tests passed: bounded monotone grade, CPU rejection by
  the GPU provenance gate, stale master rejection, missing-input GPU status, and
  invalid video metadata rejection.
- Blender audit passed all five clips: principal meshes closed/manifold with real
  volume; no tiny scales; finished projection surfaces; stationary base; real
  motion; closed idle/move loops; terminal death held and in contact with disc.
- Atlas validation passed 40 counts, trim placement, exact reconstructed alpha,
  source/grade hashes, gutters, no clipping, visible motion and held death.
- All 64 stage frames verified at 512 and 256 with raw/derived hashes.
- FFprobe verified H.264/yuv420p, 1600x348, 240 frames and eight seconds; one decoded
  video sample and all animation frames were visually inspected in the review sheets.
- Python compilation, shell syntax and `git diff --check` passed.

Non-obvious implementation finding: Blender 5.3's `tessellate_polygon` can return
vertex indices rather than vectors; the constructor handles both. Projection must
follow boolean recess cuts and bevel application. Checking only a rest pose missed
crash clipping; the final crash uses bounded rotation and translation-only margins,
with physical disc contact checked independently.
