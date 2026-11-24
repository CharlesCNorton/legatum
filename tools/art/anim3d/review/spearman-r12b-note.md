# Spearman round 12b — material continuity, not PASS

Files changed relative to round-11 candidate `01a69951`:

- `tools/art/anim3d/PLAYBOOK.md`
- `tools/art/anim3d/units/spearman/continuity.py`
- `tools/art/anim3d/units/spearman/continuity_preview.py`
- `tools/art/anim3d/units/spearman/continuity_report.py`
- `tools/art/anim3d/units/spearman/look.py`
- `tools/art/anim3d/units/spearman/look_receipt.py`

The requested Git merge failed at ORIG_HEAD.lock. Starting from a clean worktree,
I transferred the exact round-11 source tree before editing. Commit also failed
at index.lock. No push. `lanes/spearman-r12b/files-changed.txt` lists the inherited
50-file transfer separately. `lane-only.patch` contains only the six files above;
`commit-message.txt` carries the requested coauthor. origin/master is an ancestor
of the round-11 candidate. The executable gpu.sh is byte-identical to that candidate.

## Scope and rendering boundary

Inspected the actual round-11 GPU rest, contact sheet and selected clips. The
sandbox GPU preflight fails with `No Cycles METAL GPU`; no new GPU pixels are
claimed. New evidence uses Cycles CPU, 256 px, 16 samples, seed 17, no denoising
or adaptive sampling, Standard view, no histogram grade. The explicitly labelled
CPU proxy substitutes an analytic sun cosine for Eevee-only Shader to RGB; real
Cycles AO remains, but cast shadows are not reproduced. The preserved GPU image
is a labelled reference, not the matched before render. Frozen part textures,
source registration, camera and palette are shared by the CPU A/B.

The render-time patch colors downward sole faces/bevels leather brown, inward
skirt faces shadowed linen, and unseen rear shoulder cloth cloak red. Trusted
front pigment is preserved. The shoulder was already mostly continuous under
Fable A v3; this is a small hidden-surface reinforcement, not a shoulder-form fix.
The first broader sole mask darkened the visible sidewall and made its slab read
worse. Rejected it; the final mask leaves vertical sidewalls alone.

## Final matched measurements

| CPU rest metric | R11 proxy | R12b proxy |
| --- | ---: | ---: |
| Silhouette IoU | 0.921945 | 0.921945 |
| Zero-offset blurred CIE76 | 4.509381 | 4.513853 |
| Raw CIE76 (information only) | 8.077225 | 8.085764 |
| Feet-region blurred CIE76 | 13.9700 | 13.9849 |

The tiny rest colour regression is disclosed; this is an exposed-surface win.
Material-ID-isolated death frame 4: skirt mean luminance 101.43 → 83.09;
skirt pixels above luminance 160: 9 → 0; sandal mean 88.15 → 70.43.
Death frame 7 skirt: 94.89 → 85.73; sandals 75.65 → 70.38.
Hit shoulder: 111.42 → 111.46, only 15 pixels change by more than 2 RGB levels.
Rest and five diagnostic poses retain exactly identical alpha.
These part masks are not the reviewer's larger rectangular foot-luminance box.

The actual R11 GPU reference remains IoU 0.9275 / blurred CIE76 4.59. Its different
sampling and reduction must not be called a regression to the CPU proxy's IoU.
At 256 the upper figure is close, but foot shape, stance, shoulder form and the
plain base band still reveal the render. At 160 the underside flashes are reduced;
at 64 it reads as the same unit but is not indistinguishable from the painting.
Current death/hit/walk silhouettes remain the round-11 performances: other lanes
own their replacement. No PASS file was written.

## Contact: shadow verified, rest clearance still open

Contact-off control versus actual Cycles AO darkens 95 stone pixels by over 2
luminance levels, in box [86, 219, 171, 225], mean loss 9.10/255.
This is a live, localized geometry-dependent contact shadow, not painted feet
left on the disc. Eevee cast-shadow strength still needs the host GPU review.
No stone material or contact settings were altered.

**Saved rest contact misses the 2 mm tolerance:** both soles bottom at z=0.108 m,
while the evaluated stone top is z=0.105 m: a pre-existing 3.0 mm gap (about
0.26 px at 256). Sandal welts are 15 mm above the stone because they sit on top
of the soles; they are not the support surface. Do not hide the sole gap with a
darker contact patch. This is a concrete form-lane/merge follow-up.

The independent 33-sample move check passes all eight limits: compensated slip
0.00227 mm, floor error relative to its 0.106 m contact target
0.00002110 mm, planted heading
2.6184 degrees, loop seam 0. The target itself is 1 mm above stone.
Root correction 48.88 mm/50 and sole translation 35.73 mm/40 remain close to limits.
Top/front actual-geometry sheet is rendered with the current CPU painted proxy.

## Checks and evidence

- 32 tests pass: 23 kit, 4 critique, 2 pipeline, 3 look/calibration.
- All six scenes construct the production Eevee node graph; geometry, weights,
  camera and actions unchanged. Matched previews also hash UVs, pose and lights.
- Idle action hash 057f5cef51f6b2199b5834af980f67b1920b0e954f12b50f63d875298dcda227;
  attack 667d83498c04185fb13b1142c58274ef864aec7ae5222f07f73360d9d5168a6e, unchanged.
- All 40 new CPU frames rendered; 160 px reductions use display-space premultiplied
  Lanczos. Held death samples are copied byte-for-byte. No new shipped atlas or
  512 masters; the GPU script regenerates those after the lane merge.
- critique.py ran on before and final rest with all five current after clip rows.
  The before critique's contact sheet is explicitly labelled as after context.
- Python AST, shell syntax, git diff --check, and lane-patch reverse-check pass.
- No Rust/UI changes, new downloads, new generated source images or licence changes.

Review files (all in review/3d-v2): `spearman-r12b-rest-256.png`, `-rest-160.png`,
`-rest-64.png`, `-motion-256.png`, `-motion-160.png`, `-base-contact.png`,
`-feet-check.png`, `-feet-detail.png`, `-round12-contact-sheet.png`,
`-round12-metrics.json`, `-continuity-metrics.json`. Frozen inputs, detailed logs,
scene checks, hashes and source patch are under `lanes/spearman-r12b/`.

## Learned and host handoff

1. Patch the selected render-time look: the older fallback's garment attributes
   do not automatically affect Fable's replacement materials.
2. Distinguish inward/downward faces in undeformed mesh space; shared projected
   UVs alone carry exterior cream onto linings. Preserve trusted front pigment.
3. Restrict sole pigment to the underside/bevel; painting the sidewall makes the
   thick sole more obvious and worsens rest metrics.
4. A passing move contact trace does not certify saved rest contact. Measure both.
5. A CPU analytic-light proxy tests pigment and AO, not Eevee cast shadows. Do not
   fit another grade or reapply registration to make the proxy resemble GPU output.

Lead: merge the six-file lane delta, resolve the rest sole clearance with the
form lane, then run from the repository root:

```sh
ROUND=12 tools/art/anim3d/units/spearman/gpu.sh
```

It remains the no-argument full pass: all stages/40 frames, 512/256 masters,
trimmed 160 atlas + validation, round12 MP4, rest comparison, feet sheet and critique.
Review the merged motion's new exposures before accepting these material masks.
