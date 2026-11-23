# Biplane — round 1

True 3D candidate, **not approved / no PASS marker**. The saved model and five rigid
animation clips live outside git in `~/LegatumRuns/anim-pilot/masters/biplane/`.
All scripts in this directory are unit-specific. The static painting is retained.

## What exists

- Original tapered fuselage, open cockpit/seat, hollow cowling and rotary engine,
  volumetric cambered wings, ribs, struts, tail, landing gear, propeller, rivets,
  cream stone base and solid curved display support.
- Frozen-camera painting UVs on real meshes, visibility masks, generated painted
  hidden-surface fills, eight actual 256 px AO/curvature maps, three-point lighting,
  and one measured RGB grade reused across every frame.
- Flight/propeller rigid hierarchy and authored idle 8, move 8, attack 10, hit 4,
  crash/death 10 samples. The base stays stationary. Loops have closure keys;
  death ends with a held wreck. No volume effects or zero-scale hiding.
- Plain, textured, detail, pose and five clip review sheets, five animated WebPs,
  and painting / render / 50–50 rest comparison. Early pre-correction sheets are
  retained in external `review/3d-v2/biplane-round1-initial/`.
- `gpu.sh` is the complete no-argument host handoff. It uses saved masters,
  explicitly requires Metal Cycles, renders every stage at 512, retains 256
  derivatives, packs and validates a trimmed 160 atlas, and writes the driver's
  `biplane-round${ROUND}.mp4` (five clips, 2x on cream, 8 s H.264 yuv420p).

## Visual judgment

At 256 px the biplane identity, olive/buff palette, stacked wings, rotary engine and
cream display composition are present, but the render is visibly simpler than the
painting. The fuselage/cockpit registration and wing chord remain imperfect;
projected brushwork crosses a few material boundaries. The propeller is too long
and the support too broad/straight. Fine painted linen and metal scuffs are softer
than the original; the render does not yet have painting parity.

At 64 px it reads as the same biplane, but its proportions and broad cream support
still distinguish it from the source token. The small-angle flight clips preserve
its identity. Crash posing is authored and needs the lead's motion judgment;
projected lighting and strut/wing relationships are exposed at the larger angles.
Do not write `biplane-PASS` until the rest comparison and all five clips pass review.

## Run on the lead host

```sh
ROUND=1 tools/art/anim3d/units/biplane/gpu.sh
```

This does not rebuild/repaint the geometry. To change it, follow the chapter in
`tools/art/anim3d/PLAYBOOK.md`, then regenerate clips and frames. CPU images and the
GPU pass are explicitly distinguished by each raw render manifest.

The extended atlas JSON stores `rects` with atlas coordinates and per-frame `ox/oy`;
it requires the matching trimmed-frame reader. This lane does not wire a runtime
loader. No Rust, game rules or application UI changed.

## Checks

- Python syntax compilation, `bash -n` for both entry points, and `git diff --check`
  pass.
- The general checks-only gate on inherited HEAD passed hygiene and public claims;
  art rendering failed when the Node `render-sets.mjs` subprocess exited 1. That run
  does not establish a distinctness pass for this candidate. The lead's art review
  and GPU execution remain outstanding.
- Artifact-specific results are recorded in external `validation.json`,
  `video-validation.json`, `geometry-audit.json` and per-stage render/processed
  manifests. Packing validates source `.blend`, raw PNG, grade and processed PNG
  hashes; it does not trust the presence of old frames after a rebuild.

A sampled base top pixel is RGB `(227,201,162)` versus painting `(247,212,173)` at
`(115,216)`: it is warm cream, but still darker than the source. Preserve the
full raw/graded masters when adjusting exposure in the next round. The first
crash render was rejected by the trim validator; its settle translation was
corrected and the entire death clip regenerated before delivery.

Final CPU artifact checks: **PASS** — 40 frames with native 512 and 256 masters;
160 px logical cells; atlas **1486×724, 189,246 bytes, WebP quality 85**; decoded
32-level alpha reconstructs exactly at every trim offset; held death uses the same
packed rectangle and decodes identically. MP4: **1600×348, 240 frames, 8.000 seconds,
H.264/yuv420p**. Eight AO/curvature maps and every required review image exist.
All CPU final review frames used Cycles, 8 samples, denoising; no Metal GPU pass was
possible in this sandbox. The GPU script is shell-checked, not GPU-executed here.

Git operations are blocked by the sandbox: `git merge origin/master` could not
create `ORIG_HEAD.lock`, and `git add` could not create `index.lock` in the lane's
Git directory. The runner must merge upstream CI/browser-test commits and commit
these files with the requested co-author trailer. No push or PR was attempted.
