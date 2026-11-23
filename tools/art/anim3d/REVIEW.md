# Spearman MPFB review

This is a reproducible 3D candidate, **not a claim of production-ready art**. The existing painting remains the standard and no runtime art is replaced. Sam's interim feedback, delivered by the lead in the external `FEEDBACK.md`, was that this is the right direction but the textures need a more premium finish.

| Stage | Evidence and verdict |
| --- | --- |
| b: body and plain kit | First three-view sheet emitted early. Real MPFB topology, face and hands are a better foundation than primitive anatomy. Initial stance was narrow, the shield too face-on and the bronze too smooth; fail for finished art. |
| c: textures and lighting | Iterated armour into an explicit muscle cuirass; increased MPFB muscle targets; added CC0 skin/eyes, iron spear fittings, warmer cream stone, shaped crest, shield engraving and baked AO/curvature. Identity is closer, but the painting still wins on helmet construction, authored surface detail, cloth folds and tonal hierarchy. Not approved. |
| d: rig poses | Early sheet caught a spear that did not rotate. Fixed keyframing at the current scene frame and the hand matrix assignment. The final thrust is level in screen space with torso weight shift and bent front knee. Grip/stance still need visual polish. |
| e: idle | Real CMU standing torso deltas plus guard breathing. Subtle at 64 px. A richer body does not automatically make a better idle loop. |
| e: move | CMU walk leg motion retargets onto the MPFB rig. Alternating lifted/planted feet read at both sizes. In-place foot slide and loop seam need host playback review. |
| e: attack | Ten-frame anticipation, level shoulder thrust and recovery; whole body participates. The transition from vertical guard is more mechanical than a trained hoplite's motion. |
| e: hit | Four-frame torso/head recoil and shield jolt are readable. Recovery is deliberately short and needs cadence review. |
| e: death | Side collapse with folded legs and held terminal frame. First pass intersected the shield with the base; the revision releases the shield into a tilted resting pose. Geometry and decoded checks below determine remaining blockers. |

## Reproducibility and limitations

Blender 5.3.0, MPFB 2.0.18, CC0 MakeHuman system pack, Pillow 13.0.0. Material sources are CC0; CMU grants permissive research/commercial use and the BVH conversion adds no restrictions. Original kit and output follow the repository licences. Full details and SHA256 pins are in `PLAYBOOK.md`, `assets.lock.json`, the central art provenance table and the external assets `SOURCES.md`.

Masters and review sheets are outside git under `~/LegatumRuns/anim-pilot/`. Every render invoked `nice -n 10`, four Blender threads and one heavy process at a time. The sandbox denies the priority adjustment and thumbnail cache write; neither warning prevents the render. The first system-pack download timed out at 90 seconds, then resumed to completion. The repository source-fetch helper returned HTTP 403; direct curl retrieved the same source, whose SHA256 matches the repository manifest.

CPU previews use Cycles. Eevee/Metal, Chromium playback and a final Claude art review have not been run in this sandbox. Hunyuan3D mini was skipped because Metal/MPS is unavailable; no expensive CPU generation, TRELLIS, cloud job, account, upload, PR or push was used.

## Lead handoff

Use `tools/art/anim3d/render.sh c`, `d`, and each `e-idle`, `e-move`, `e-attack`, `e-hit`, `e-death` outside the sandbox for Eevee/Metal. All use the same isolated resource directory and saved clip masters. Then repack and validate with the isolated venv, compare all stages with the source, review playback at 64 px, and obtain the project's final art verdict before integrating the atlas.

## Final measured checks

- Setup rerun: pinned MPFB/system pack/mocap/PBR downloads verified, isolated paths retained.
- CPU rendering: all 40 frames at 384 px / 24 Cycles samples, downsampled to 256 for packing; native 256 px comparison and 512 px close-up review also produced.
- Atlas: **177,464 bytes**, WebP quality **80**, all **40** frames; 2560 × 1280 grid. JSON retains the exact frame/clip contract and anchor `(127,221)`. SHA256 `c18745e8938f1270aa2b59de951e5dd8b0673e1458c40e3bb56af190273d15ec`.
- Saved-rig audit: **40 samples, zero findings**; original MPFB 19,158-vertex topology and 53-bone skeleton verified, cloth caches baked, base transform unchanged, evaluated character geometry in frame and above the floor tolerance.
- Decoded validation: **PASS** size, metadata, frame counts, alpha, transparent padding, clipping margins, real motion and held death. Last two raw death images have identical RGBA pixels; PNG timestamps differ.
- Python AST parsing, Bash syntax, source-lock JSON and `git diff --check`: **PASS**. No Rust, rules or app runtime changed; Cargo/WASM/app build suites are not relevant to this art-only change.

All final strips were visually inspected beside the painting at 256 and 64 px. The final helmet uses a continuous curved faceplate with real eye/mouth openings; the earlier angular cheek-panel version is removed from the build. Close-ups in `c-details.png` still show a clear gap from the painting's finish. Technical passes do not override the failed production art bar.

Non-obvious lessons: MPFB provides credible anatomy but does not solve armour design or painting quality; matched 2D source detail on a true convex mesh needs perspective/bulge calibration; PBR microtexture alone disappears at 64 px; Blender's current frame must advance before inserting pose matrices; compare terminal image pixels rather than PNG bytes because render metadata changes.

## Repository handoff

- Commit attempt failed with exit 128: the sandbox denied creating the worktree `index.lock`. No alternate index or permission bypass was used. Changes remain uncommitted for the runner; nothing was pushed and no PR was opened.
- Direct repository hygiene rules over all 23 changed/new text files: **zero findings**. The atlas is below the repository binary-size threshold.
- `python3 tools/gates/art.py HEAD`: **exit 1**, the browser-backed `render-sets.mjs` subprocess failed. This gate was against committed HEAD because the sandbox could not commit the candidate; it does not certify the new atlas. Host browser/art review remains required.
- `HEAD...origin/master`: **0 ahead / 0 behind** before the attempted commit. No fetch or merge was needed.

Stage only `tools/art/anim3d/`, `app/src/assets/PROVENANCE.md`, and `app/src/assets/units/anim/spearman.{webp,json}`. The runner should commit with the requested co-author trailer, then run the committed-tip gates. The proposed title is “Add MPFB spearman animation pipeline and review candidate”.
