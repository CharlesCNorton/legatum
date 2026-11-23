# Fighter — resumed round 2 candidate

The glazing and seated canopy ribs, fitted circular propeller plane with ochre
blade tips, camera-only painted pigment, physical cream top/rim and retained
falling support have been revised. Original full-volume aircraft, generated
unseen-surface fill, six actual AO/Pointiness bakes and all five clips remain.
Masters, source images and review files remain outside git.

Current evidence is **256 px / Cycles CPU / 12 samples**, not a GPU sign-off.
The previous real 512/256 masters and original review evidence are preserved in
`masters/fighter/round1-preserved`; fresh final GPU512 masters are pending.
The current external `256/` set contains every revised frame. Every stage,
256/64 rest comparisons, detail and rig sheets, all five strips/animated WebPs,
decoded-atlas sheet, top/front mechanical review and round-two MP4 are present.

Checks:

- Closed positive-volume fuselage, both wings, tail, canopy and support; finished
  modifier surfaces; camera-only pigment; physical base; stationary base over
  40 samples; safe scales; closed idle/move transforms; grounded crash geometry;
  held death; six actual baked maps: passed.
- Trimmed 160 px atlas: **172,446 bytes at quality 90**, 1310 × 770 pixels,
  all **8/8/10/4/10** samples, exact decoded alpha, transparent gutters, source
  provenance and identical decoded terminal death: passed.
- MP4 decoded from that atlas: **H.264, yuv420p, 1600 × 348, 240 frames,
  8 seconds**, five clips at 2× on cream: passed. A decoded frame was inspected.
- Python compilation, Bash syntax and whitespace checks: passed.
- GPU script executable and missing-master preflight: passed; explicit failed
  status recorded before Blender. CPU inputs correctly fail the GPU512 gate.
  Actual Metal execution is unavailable in this sandbox and remains a host check.
- Repository browser art gate failed in `render-sets.mjs` locally. It needs the
  host browser/art pass; this is not a passing distinctness result.

At **256 px**, canopy placement and paint are closer, the propeller has legible
painted tips and the base is warmer. The propeller silhouette still differs from
the painting; wing brushwork and base shading remain simpler. The source's four
propeller tips are not perfectly symmetric; the circular model is an explicit
compromise. At **64 px**, the same aircraft identity and broad composition read
clearly, but base/propeller differences remain distinguishable. Silhouette IoU
at 256 is .8471; this is a diagnostic, not evidence of painting parity.

Idle/move loops, attack flashes and hit response have been inspected. The revised
support falls behind the fuselage instead of disappearing or cutting through its
visible side. Death still looks like an intact aircraft settling nose-down, and
fixed-view paint stretches on exposed wing surfaces. No art PASS marker is justified.

Lead handoff, from this checkout:

```sh
ROUND=2 tools/art/anim3d/units/fighter/gpu.sh
```

The no-argument script refreshes all clips, audits, renders every stage and the
mechanical top/front review on Cycles GPU, keeps genuine 512/256 masters, verifies
GPU provenance, packs/validates and writes `fighter-round${ROUND}.mp4`. Round log,
status and hash-bound receipt accompany it. It never creates a PASS marker.

Commit handoff: the sandbox denied `.git/worktrees/lane-8/index.lock`, so this
round remains uncommitted for the runner. The HEAD-based hygiene gate therefore
still reads the old matrix-multiply/no-space false positives. A direct scan of
all 12 changed working-tree text files using the repository's hygiene line rules
passes with zero findings; public-claims passes on HEAD. This is not a claim that
the full committed-head gate has passed. No Rust, engine or UI code changed.
