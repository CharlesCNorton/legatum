# Main battle tank — round 2

Round-two CPU candidate, **not art-approved**; no PASS marker. The round-one GPU
pass succeeded at 512px and Q90 / 191,884 bytes. Its images and movie are preserved
in `masters/main-battle-tank/round1-gpu/`; the 512px archive is still round one until
the lead runs the updated handoff. Current 256px masters, review sheets, atlas and
`main-battle-tank-round2-cpu.mp4` are round-two CPU output.

## Changes

Individually fitted cupola sights, upright machine gun, pintle, magazine and hatch
restore more of the painting's roof silhouette. The upper deck extends farther
forward, the far front sprocket sits lower, and the barrel/sleeve are thinner.
Canvas has radial folds, pinched bands, thick webbing and beveled buckles. Actual
AO/Pointiness bakes, painting projection and the automatic histogram grade were
rebuilt using the existing generated hidden-surface fill and product lights.

Wheel meshes still rotate at belt travel/radius. Their painted illumination now
uses stationary 3D coordinates, so projected highlights and neighbouring fender
colour do not orbit with the wheel. This deliberately targets the fixed token
camera; it is not a general all-view texture solution. Exhaust stays close to its
outlet and muzzle haze is less opaque. A first smoke revision touched the atlas
boundary; the crop validator caught it and the corrected attack was rerendered.

The movie builder now validates the current atlas before encoding and records its
SHA256 in the movie receipt. A deliberate stale-atlas run failed before encoding;
a successful ffmpeg exit alone previously could certify an outdated movie.

## Checks

- All 40 CPU frames rendered at 256px / 12 samples; rest at 8 samples. All b/c,
  detail, rig, five clip strips/WebPs, top/front track views and crossfade updated.
- Three closed-route tests pass: length/closure, constant arc speed, shoe tangent.
- Blender audit passes all clips: 124 links, 16 wheel pivots, stationary support,
  safe scales, matched wheel/belt travel, recoil, held death, current source hashes,
  six actual 512px bake maps and stationary wheel-light coordinates.
- Lowest shoe-to-base plane distance: -0.00674055 scene units, within 0.02 tolerance.
- Trimmed 160px atlas: **171,950 bytes, Q90, 1364x403**, all 40 samples. Exact alpha
  reconstruction, transparent gutters, padding, frame counts, motion and identical
  terminal death frames pass. Final GPU size remains to be measured.
- Movie validates and was decoded for inspection: H.264/yuv420p, 1600x348,
  240 frames, eight seconds. The movie receipt binds it to the current atlas hash.
- Python compilation, shell syntax and whitespace checks pass.

## Visual judgment

At 64px it reads as the same unit, with a closer roof silhouette and calmer running
gear. At 256px it remains distinguishable: the front hull contour and stowage/drum
shape need closer registration, track edges are simplified, and the wreck smoke
still reads as clustered shells. The grainy low-sample smoke must be rechecked on
GPU. Top/front views expose stretched projected detail away from the hero camera.
All five clip strips and decoded movie samples were inspected; technical motion
checks do not establish premium animation quality or a perfectly invisible loop.

Current rest alpha IoU is 0.90136 (threshold >128), opaque-overlap RGB MAE 9.68764
(both alpha >240). These are diagnostics, not acceptance criteria; there is no
claim of silhouette parity or improvement based on the metric alone.

## Lead handoff

```sh
ROUND=2 tools/art/anim3d/units/main-battle-tank/gpu.sh
```

Executable, no arguments, from the repo root. Tests the belt, checks Metal, audits
masters, renders every stage and all five clips at 512px / 256 samples, archives
512/256 masters, packs and validates the atlas and writes the eight-second
`main-battle-tank-round2.mp4`. Inspect the fresh GPU rest comparison and movie before
considering PASS. No static art or runtime consumer was changed.

Repository gate limitations: the HEAD-based gate initially flagged unspaced Python
matrix multiplication as email addresses. Those expressions now have spaces, and
all currently changed text files pass the gate's hygiene line checks. Public claims
passed. The browser distinctness gate failed to execute `render-sets.mjs`; it is
not a passed art review. Git staging is blocked by the sandbox's `index.lock`
permission, so the runner must commit the work and rerun commit-based gates.
