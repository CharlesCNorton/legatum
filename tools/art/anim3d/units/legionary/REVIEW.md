# Legionary round 1

Review candidate; the existing painting remains the runtime asset. The source and
GPU commands are in the **Infantry: legionary** chapter of `../../PLAYBOOK.md`.

At **256 px**, the curved red scutum carries the painting's wing/lightning detail,
and the kit reads as Roman segmented iron, bronze helmet and pilum. The render
still falls short of the painting: face registration is soft, shoulder lames are
less natural, the armour lacks the source's individually authored wear, and skin
projection becomes noticeable around bending knees. The cream base was measured
and warmed after the first review. At **64 px**, the same unit is recognizable,
but the painting has a more confident silhouette and clearer human pose.

Idle/move are authored on the MPFB rig; attack is a shield bash, hit a recoil,
and death releases equipment and holds the terminal pose. The tunic hem uses
shape-key follow-through, not a physical cloth simulation. The audit checks
pilum centreline collisions with rigid kit and ground bounds; it cannot establish
full body/clothing nonintersection or natural motion. Final GPU art review remains
required, including projection seams, grip, loops and terminal contact.

External evidence under `~/LegatumRuns/anim-pilot/`:

- `masters/legionary/`: editable rest/clip blends, packed materials, eight actual
  AO/curvature bakes, pinned input hashes, raw and graded 512 px PNGs, 256 px copies.
- `review/3d-v2/legionary-*`: plain, textured, details, rig poses, rest crossfade,
  all five strips/animated WebPs, chronological log and machine-readable audits.
- `assets/legionary/`: original source painting and generated painted fills.

Early plain/textured revisions and the first death strip are preserved as interim evidence.
The current filenames are updated immediately after each successful stage.

Verified CPU delivery: **191,830 bytes**, WebP **quality 75**, 1193 × 757 packed
atlas, all **40** canonical 160 px frames. Trim reconstruction, source hashes,
transparent padding, margins, clip motion and identical terminal death source
pixels passed. The geometry audit passed all 40 samples with one warning:
terminal skin minimum is 0.256 m, while worn geometry reaches 0.090 m and the stone
top is 0.085 m; the body sits over the dropped shield and the stiff fold/contact
still needs art review. No pilum intersections with audited rigid kit remain.

Python syntax (10 scripts), shell syntax and `git diff --check` passed. The
repository art gate could not complete its Chromium `render-sets.mjs` step in this
sandbox. This is not a passing browser/art gate. No Rust or app runtime changed.
