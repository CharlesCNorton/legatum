# Feedback from the lead and the cloud reviewer on b-mpfb-kit-plain.png and c-textured-lit.png (read and apply)
1. Bronze muscle cuirass missing (bare chest). Add it; the painting is fully armoured.
2. Build too slim: stocky, muscular hoplite; arms too thin and bare-looking, make them muscular.
3. Stance: wide and braced, feet well apart, knees slightly bent; figure turned more toward camera.
4. Spear held lower; shield close to the body with its rim overlapping the torso.
5. Cloak hangs behind both legs down to the calves.
6. Spearhead and butt are iron, not gold.
7. Stone base is grey; must be the painting's warm cream disc.
8. Shield and helmet plain; add the painting's worn, painted detail. Lighting flat; warm key from upper left.
9. Camera: match the painting (roughly eye-level three-quarter) and give the figure the same frame height as the painting so 64 px tokens compare 1:1.
10. Sam (owner), on c-textured-lit.png, pointing at the 3D figure's torso and shield: "ok that's progress. the textures don't feel as premium as the art, but we can keep iterating. this is the right direction." Priority: richer, more premium surfaces (painted wear, edge highlights, cloth weave, worn bronze with depth), matching the painting's finish.
11. TOP PRIORITY for texture work (expands item 10). Surfaces must read like a premium hand-painted miniature, as the painting does:
   - bronze: hammered and worn, dark cavities, bright edge highlights (AO- and curvature-driven grime and edge wear), etched detail on cuirass, helmet and shield;
   - skin: painted shading, warm midtones, darker recesses, highlights on the muscles (not flat beige);
   - cloth: visible weave, folds with shaded troughs, slightly faded hem;
   - leather: scuffed;
   - stone base: warm cream with fine grain.
   Bake AO and curvature maps and drive wear/grime from them. Use your image generation for painted detail textures where CC0 libraries fall short. Check close-ups of chest, helmet and shield at 256 px against the painting before calling it done.
12. Sam on the round-1 animations: "still pretty rough, but good progress!"
13. Silhouette (from the cloud reviewer): the painting's figure is WIDER: braced legs, shield held out in front of the torso and facing the camera, cloak flaring past both legs. The 3D one is narrow and upright with the shield edge-on. Turn the shield face to camera. Push the gold up in brightness and saturation to match the painting's highlights.
14. (lead, ops) Three more animation lanes now run in parallel (horseman, field-cannon, tank). From now on run EVERY Blender invocation through ~/LegatumRuns/anim-pilot/bin/blender-slot <args> (shared gate: max 2 Blender processes across lanes, 3 threads each; do not pass -t). Update tools/art/anim3d/render.sh and PLAYBOOK.md to use it (keep the lead's GPU render path working). Your branch is the infantry lead; name new review images spearman-<stage>.png.
15. (lead, crash fix 2026-11-22) Blender crashes reached Sam's screen as macOS "Blender quit unexpectedly" dialogs. Causes: (1) Cycles turning tiny/zero-scaled hidden smoke meshes into volume grids (OpenVDB ScaleMap exception, SIGABRT); (2) earlier, a Blender launched without -b touching the macOS UI from the sandbox. Rules now: never scale an object to 0 or near 0 to hide it; hide effects with keyed hide_render/visibility, and give volume/smoke meshes a sane size. Always run Blender with -b. Every `blender` call on your PATH now goes through a machine-wide gate: ONE Blender process on the whole Mac at a time, 3 threads, auto-retry on crash. Don't call /Applications/Blender.app directly. Expect to wait for the lock; keep renders short.
