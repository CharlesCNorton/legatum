# Driver round 2 — CPU candidate; GPU review pending

Reviewed 2026-11-23 on `astra/unit-anim-3d-jet-fighter`. The incoming round-1 GPU pass succeeded: 185,264 bytes at quality 80, native 512 masters and eight-second video. Its c/details/f comparisons, all five strips and decoded MP4 frames were opened before editing and archived externally under `masters/jet-fighter/driver-r1-gpu/`. Shared feedback 1–23 and all playbook chapters were read. No unit-specific feedback file existed at the start or final check.

## Changes

- Rebuilt the intake as a physically coaxial closed shell with a flared rear, rounded front transition, inner tunnel and recessed termination. The former chrome cup / visible rear wall is reduced; its nose-view alignment is much better.
- Raised the canopy crown, thinned its solid trim, reduced rim-light energy and increased the frozen painting contribution. The existing automatic bounded RGB-quantile grade is recalculated from the new rest render and frozen across every clip.
- Shortened the hidden far-wing span and gave it a conventional span/chord unwrap mixing this aircraft's painted panel pattern with the existing generated silver fill. Added interior projection samples.
- Diagnosed inward normals on the far wing: signed volume was -0.015719 although the old absolute-volume audit passed. Closed surfaces now get outward signed orientation after modifiers, before camera projection and AO/Pointiness bakes. The audit requires positive signed volume.
- Replaced the crash's smooth wing curl with a defined crease and rotating outer panels. Lengthened/thickened the solid, visibility-keyed cannon streaks for token readability.
- Updated executable gpu.sh to default to round 2 and publish running-stage status. It retains strict Metal/input checks and the complete stage/master/atlas/video workflow. Updated only this unit's playbook chapter and source documentation. No new download or image service.

## Current artifacts and checks

Blender 5.3.0, Cycles CPU, native 256px, 16 samples with denoising. The rebuilt scene has 20 meshes / 10,645 vertices. Editable masters, six native 512px AO/Pointiness maps, five keyed clip scenes, grade and hash receipts remain under `~/LegatumRuns/anim-pilot/masters/jet-fighter/`.

All b/c/details/d/e/f/g review images and the five animated WebPs are current. The top/front move-cycle sheet is the explicitly labelled aircraft equivalent of a feet check. Rest comparison and every strip were inspected at native 256/64, plus four decoded MP4 frames showing rest, firing/hit and impact/held wreck.

- Input/build preflight: PASS, source/fill and build-script/master hashes current.
- Blender geometry/clip audit: PASS, manifold positive signed-volume principal shells, nonzero scales, stationary base, moving clips, matching idle/move loop endpoints, held death root and support collapse.
- Atlas validation: PASS, **40 frames, 180,018 bytes, quality 85**, logical 160px cells, trim offsets/anchors preserved, exact decoded alpha, transparent padding, no overlapping crops or clipped frame extents, identical decoded final two death frames. All scene/script/grade/frame receipts current.
- MP4/FFprobe: PASS, H.264, yuv420p, 1600 × 348, 240 frames, 8.000 seconds, five clips side by side on cream at 2x. File: `review/3d-v2/jet-fighter-round2.mp4`.
- Python AST: PASS, eight scripts. Bash syntax: PASS, render.sh/gpu.sh. Git diff whitespace: PASS.
- No Rust, mechanics or app UI changed; Cargo and app suites were not run. Current native 512 **renders** require the lead GPU pass; historical round-1 native 512 frames are preserved and cannot pass current-master hash validation.

## Honest visual verdict

At 64px this clearly retains the painting's silver jet, swept silhouette, scale and warm cream pedestal. The darker intake reads better, the far wing no longer flashes white, and the attack is visible. At 256px the rest pose is closer but not yet hard to distinguish: canopy and near-wing-root contours remain approximate, the intake transition is slightly heavy, and the low-sample CPU close-up is softer than the source. Off-angle wing proportions still look asymmetric; the crash crease is more mechanical but support/wreck contact remains stylized. These are unresolved visual limits, not failures hidden by a technically passing atlas.

Five clips render without crop loss or zero-scale effects; idle/move endpoint checks pass and death holds. This is not a full self-collision or flight-dynamics solver. The lead must inspect the new GPU lighting, edges, attack and death sequence. **No PASS file written.**

## Lead handoff

Run from this branch's repository root, no script arguments:

```sh
ROUND=2 tools/art/anim3d/units/jet-fighter/gpu.sh
```

This renders every stage and all clips with Cycles GPU at native 512px, keeps 512/256 masters, updates the rest crossfade/details/top-front and all clip sheets, packs and validates the trimmed 160px atlas, runs the geometry audit and writes `jet-fighter-round${ROUND}.mp4`. It never turns technical success into art approval.

Commit attempt: sandbox denied `.git/worktrees/lane-6/index.lock`. Changes remain uncommitted for the runner, with no push or PR. Intended commit footer: `Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>`.
