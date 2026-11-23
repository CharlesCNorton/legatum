# Spartan hoplite — round 1

This is a true-3D review candidate, not approved replacement art. The existing
painting remains the runtime asset. At 256 px the model is visibly less refined:
the weapon hand is lower, helmet/profile and crest silhouette differ, skin and
linen need more authored shading, and the mantle needs a less regular sculpt.
At 64 px the red crest, ivory armour and lambda aspis identify the unit, but the
rest-pose crossfade still has obvious double contours. Death is held but its
settlement remains stiff. GPU frames have not been reviewed.

The unit uses MPFB CC0 anatomy and its 53-bone rig, original fitted linen armour,
bronze helmet/greaves, sandals, straps/buckles, a convex painted aspis and real
cloth simulation. Idle/walk use the shared licensed CMU captures; attack/hit/death
are authored on that rig. Projected colour is frozen on real mesh UVs. It is
view-specific, with approximate per-part registration; unseen linen uses the
mounted lane's original generated fill and other backs retain CC0 scan materials.

All artifacts are under `~/LegatumRuns/anim-pilot/`:

- Editable master, five cached clip masters, eight 512 px AO/curvature maps,
  source/grade/render/pack manifests: `masters/spartan-hoplite/round1-3d/`.
- Actual 512 px CPU frames and 256 px derivatives: `512/` and `256/` within that
  master directory. These are previews; the lead should refresh with GPU samples.
- Plain, textured, detail, rig-pose, rest comparison and five clip-strip PNGs,
  five animated WebPs, running log and checks: `review/3d-v2/spartan-hoplite-*`.
- Painting source and aligned projection masks: `assets/spartan-hoplite/`.

The candidate atlas is `app/src/assets/units/anim/spartan-hoplite.webp`, with a
matching JSON: 160 px logical cells, trim rectangles/offsets, all 40 frames, quality
at least 75 and at most 200,000 bytes. The new rectangle format is documented in
the unit's PLAYBOOK chapter; it requires a compatible loader before runtime use.
Exact pack quality, size and input hashes are in external `pack.json`.

Technical checks cover decoded dimensions, 8/8/10/4/10 frames, transparency,
trim bounds, movement, held death, source lineage, camera margins, stationary
base, anatomical topology, cloth caches, grip and spear/equipment crossings.
The targeted shield probe checks the previously exposed fingertips. This is not
a general skin/cloth collision solver or an art acceptance test. Final reports
are `spartan-hoplite-validation.json` and `spartan-hoplite-rig-audit.json`.

The repository hygiene and public-claims gates passed on the pre-existing HEAD.
The sandbox refused Git index.lock creation, so the runner must commit this
working tree and repeat the repository gates on that commit. The browser-based art-set
gate failed when its Node renderer exited nonzero in the sandbox; it still needs
a successful host run. Python syntax, shell syntax and whitespace checks are
also required before committing. No engine or UI source changed.

From this checkout, the lead's final GPU refresh is:

```sh
UNIT=spartan-hoplite RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=64 tools/art/anim3d/render.sh all-renders
UNIT=spartan-hoplite tools/art/anim3d/render.sh pack
UNIT=spartan-hoplite tools/art/anim3d/render.sh validate
UNIT=spartan-hoplite tools/art/anim3d/render.sh audit
```

Reinspect rest/64 px identity and all clips after GPU rendering. Metal selection
is explicit; unavailable GPU rendering fails instead of silently falling back.
Clean reconstruction is documented in the PLAYBOOK; `finalize`, `sync-finish`,
`clearance`, and `mantle-finish` retain the narrow round-one repair steps used to
preserve existing cloth caches while correcting rigid equipment and surfaces.

Final CPU check results: 40 actual RGBA masters at 512 px and 40 derivatives at
256 px; atlas **172,788 bytes, WebP quality 85**. Atlas validation passed all five
clips, trim reconstruction (alpha and RGB), motion, margins, lineage and held
death. The full 40-sample rig audit reported **0 findings**; the shield contact
probe hit only the shield. All 27 anim3d Python files parsed; both shell entry
points passed `bash -n`; `git diff --check` passed. CPU samples: 8 with denoising.
