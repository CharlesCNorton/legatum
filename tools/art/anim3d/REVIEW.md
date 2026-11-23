# Spearman MPFB review — round 2

This is an improved art candidate, **not production art approval**. The existing painting remains the standard and the app runtime still uses its existing art. Sam's direction remains: this is the right direction, but the textures need a more premium finish. All GPU c/d/e sheets and all five WebPs were opened before editing; the original 11 feedback items and the two later additions were read.

## What changed

Broader MPFB shoulders, a wider braced stance, a taller front-to-back horsehair crest above a bronze bowl, raised sunburst facets and a bright rim, a less edge-on shield, a warm cream base with darker sides, brighter bronze with stronger key/rim light, restored visible cuirass engraving, and a riveted leather belt. The original 19,158-vertex anatomical body and 53-bone rig remain intact. Iron spearhead and butt, white linen and red simulated wool are retained.

The bake correction matters more than simply increasing saturation: inward shield winding and Solidify's shared inner/outer UVs had made the metal's AO misleadingly dark. The revised bake temporarily disables Solidify, bakes the authored outer surface, then restores thickness. AO now drives stronger cavity colour, and curvature drives brighter edge colour and lower roughness. Hammer-scale normal/roughness variation supplements the CC0 scans. The shield's original painted detail is blended at 18%, letting the raised geometry and current lighting carry the form.

The ten-frame attack now raises an overhand grip beside the right shoulder, bends the front knee, lowers and shifts the torso forward, and extends above the shield. The spear slides through the grip during the raise to keep both ends inside the cell. Death now starts from the wide guard, opens the hand and releases the spear across the front edge of the base before the body collapses. The move contact height was raised by 15 mm after the audit found the soles just below tolerance. Geometry checks cover the shaft's centerline against shield, cuirass and helmet bowl, plus hand-to-shaft distance before release; they do not certify every possible cloth/skin contact.

## Visual verdict

At **256 px**, the bronze, cream disc, crest and raised shield read more clearly than round 1. The painting still wins on deliberate wear, engraving, natural cloth folds, helmet silhouette and the modelling of hands/skin. Large armour surfaces still look smoother and more synthetic. This does not meet the painting's premium finish bar.

At **64 px**, the gold shield, red cloak/crest and white linen are stronger and the stance is broader. It reads as the same unit type more convincingly, but it is not a one-for-one match to the painted token's pose and visual hierarchy. The tall crest and highlights need a fresh Eevee comparison before approval.

`c-round2-comparison.png` puts painting, round-1 GPU output and round-2 CPU output together. `c-details.png` compares helmet, cuirass and aspis close-ups; c/d/e sheets include native 256 and 64 px cells. These are evidence for iteration, not sign-off. CPU/GPU rendering differences remain material.

## Reproducibility and ownership

No new external art sources were introduced: MPFB/system assets, CC0 PBR maps, CMU motion and the project's original shield painting retain the provenance recorded in `PLAYBOOK.md`, `assets.lock.json` and the central art provenance table. No rules, Rust code or app runtime changed.

At 21:12, the runner saved the work as WIP commit `5fc931b` and switched lane-2 to `astra/unit-anim-3d-siege` during a rebuild. That mixed rebuild was rejected. The spearman branch now continues in `legatum/.worktrees/spearman-round2/`; siege edits were preserved. The complete revised master and all clips were regenerated. Clip source hashes and render hashes now prevent packing stale or mixed generations. Temporary files stay in `ANIM_ROOT/tmp`; Blender calls retain `-t 4`, fixed four-thread scene settings, the shared heavy-process lock and the runner's additional machine-wide queue.

## Lead handoff

The exact GPU render, detail, repack and audit sequence is at the end of `PLAYBOOK.md`. Run it from the spearman checkout, using the existing masters under `~/LegatumRuns/anim-pilot/masters/spearman-3d-v2/`. Compare the new GPU c/d/e output with the painting at both sizes and inspect playback, including feet, grip, equipment clearance, cloth and held death. Run the project's browser/art gate and final Claude art review before integration. No PR, push or merge was performed here.

## Final round-2 checks

- CPU previews: c at 256 px / 40 Cycles samples, close-ups at 512 px / 40 samples; d and all 40 clip frames at 384 px / 32 samples, downsampled to 256 for delivery. All final c/d/e sheets and WebPs were opened, including 64 px cells.
- Atlas: **185,868 bytes**, WebP quality **75**, **40 frames**, 2560 × 1280. Exact frame/clip JSON contract and `(127,221)` anchor retained. SHA256 `54ce14430b5d8e665de02b88abf3e749fff64dd468766273e96051a1831f6835`.
- Saved-rig audit: **40 samples, zero findings**. Original MPFB topology/rig, persistent cloth, fixed base, camera bounds, floor tolerance, held-weapon grip and spear-versus-equipment centerlines pass. Released death frames intentionally do not require hand contact.
- Decoded validation: **PASS** dimensions, metadata, all frames, alpha, transparent padding, motion, clipping margins, byte cap and identical last-two death source pixels.
- Python AST: **16 files PASS**. Source-lock JSON and both Bash files parse; diff whitespace passes. Direct repository hygiene checks: **24 text files, zero findings**.
- Stale-render rejection was exercised: packing refused an old death render after its blend changed. The final atlas uses matching clip/master/render hashes and CYCLES manifests throughout.
- No Rust, rules or app runtime changes: Cargo, WASM and app build suites were not run. Fresh Eevee/Metal review, browser art gate and final Claude art approval remain for the lead.

The final death correction moves only the released weapon sideways during the drop. It was applied to the saved clip without changing the rig or cloth simulation, and the same arc is in `animate.py` for full rebuilds. The final saved-rig audit and rerender cover the patched clip.
