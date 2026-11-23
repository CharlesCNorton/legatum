# Tank candidate review

This is an animation review candidate, not a claim of painting parity or art approval. No game runtime wiring changed.

The unit is `tank`, the WWII medium tank painting. `main-battle-tank` is the later turreted asset; `landship` is the separate turretless Early Tank. The painting has no insignia, so the model has none.

The original hard-surface model has a rounded cast turret and transmission nose, articulated gun/recoil, sloped hull, closed hatches, cupola, headlights, hull MG, rear stowage, tools and jerricans. Twelve road-wheel pivots, four sprocket pivots and 124 individual track links are animated in true 3D. Real 512 px AO/curvature bakes, scanned cast grain, chipped edges and projected source brushwork give the hull depth. Frozen camera UVs cover 49 actual hull/turret/wheel/bogie meshes; back faces retain procedural materials. Smoke is translucent 3D geometry; fire and sparks are emissive meshes. Death darkens the model and settles it on the stationary cream base.

At **64 px**, it reads as the same olive WWII tank, with the short gun, rounded turret, paired-bogie running gear and cream disc. At **256 px**, it is still below the painting's craft bar. The reference has finer cast shapes, richer and less regular wheel detail, more convincing chipped steel and subtler pigment transitions. The rest-pose crossfade still exposes camera/shape registration differences, especially the barrel and rear stowage. Projected colour contains painted lighting and becomes less reliable when surfaces turn. Flames remain visibly stylized; the final smoke-shell version requires host GPU visual review. Do not call this interchangeable with the painting yet.

Immediate evidence is outside git under `~/LegatumRuns/anim-pilot/review/3d-v2/tank-*`: first plain geometry, textured comparison, detail crops, pose sheet, each clip strip and WebP, rest-pose crossfade, running log and feedback. The plain sheet is intentionally the early geometry pass; it is not the final finish. Masters and packed textures are under `~/LegatumRuns/anim-pilot/masters/tank/`.

The master is reproducible through the Vehicles chapter of `PLAYBOOK.md`. Host final rendering (explicit Metal Cycles, denoising, one shared Blender process at a time):

```sh
RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=256 tools/art/anim3d/render.sh vehicles-final
```

That command renders saved masters, recalibrates one rest-pose grade, renders every clip, repacks the exact atlas contract and runs the geometry audit. The sandbox cannot verify Metal output; the lead must inspect it and apply the art-review gate before adoption.

Validation of the CPU delivery: **PASS**. The WebP is 198,692 bytes at quality 54, 2560 × 1280, with all 40 frames at 256 × 256 and the exact existing JSON schema. Transparent padding and corners, at least two pixels of frame margin, motion in every clip and byte-identical terminal death samples all pass. Geometry audit passes: 124 track links, 16 rotating wheel/sprocket pivots, recoil, stationary base, planted samples and all six AO/curvature maps. Ten Python scripts parse, both shell entry points pass `bash -n`, and `git diff --check` passes. Metal/Eevee output remains unverified in this sandbox. No Rust or application logic changed.

The cap forces visible compression at native 256 px; inspect `tank-g-delivery.png`, which compares the painting, source CPU PNG and decoded atlas. Quality 55 was 200,758 bytes, so quality 54 is the highest tested passing setting for this CPU set. The full-resolution PNGs and masters remain intact for GPU rendering and future encoding work.

Operational learnings: near-zero volume scales can crash OpenVDB and create desktop crash dialogs; keyed visibility avoids that. Noise-faded 3D smoke shells reduced idle rendering from roughly 87 to 5 seconds while avoiding volume-grid conversion. Never edit a running shell wrapper while it waits for a render lock: Bash can resume reading at a changed file offset. Finish that invocation before changing the wrapper.

Git staging and commit were blocked by the sandbox: `.git/worktrees/lane-3/index.lock: Operation not permitted`. Changes are intentionally left uncommitted for the runner. The prepared commit message is in the external master folder and includes the requested co-author line. Ref-based merge/art gates have not been claimed for these uncommitted changes; the existing distinctness renderer only scans static `*-256.png` miniatures, not animation atlases. The candidate-specific pixel and saved-scene audits above cover this delivery; lead art approval remains pending.

The six newly installed Blender skills were read for final review. Added explicit `--disable-autoexec` and an assigned-camera guard. Their material guidance reinforces a remaining limitation: these are fixed-view painted materials, including blended metallic values, rather than calibrated raw-metal/dielectric layers. Their camera and modeling guidance also reinforces the registration and cast-detail follow-ups above. The optional reference-look-calibration helper is absent; native-size sheets, measured quantiles and the crossfade were used directly.
