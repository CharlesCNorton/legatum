# Premium 3D units: start from a well-made model, don't model the hero in headless Blender

2026-11-25. Sam approved the 0 A.D.-based Spearman's motion (round 6) but said the look was "a 2000s video game unit". Three premium rounds had Codex/Astra model the body, helmet, cuirass and cloak procedurally in headless Blender (MPFB body, modifiers, baked detail), in two lanes. Each round fixed one layer and exposed the next: ball-shaped knees, an egg-shaped helmet, a lumpy torso. Round 3 was further from the painting than round 6.

- Codex can fit, rig, bake, decimate, validate and render well. It can't sculpt a premium character from scratch without seeing its work as it goes.
- The route that works is the studio route: take a well-made, licence-clean source model (CC0 or CC BY, for example from Sketchfab), fit it to the existing skeleton, transfer the weights, bake its textures to our budget and keep the approved clips.
- Every Sketchfab download needs a login, so the user has to download the file. Store-bought models (Sketchfab Standard, CGTrader, TurboSquid) can ship in a game but can't sit in a public repo.
- Judge the look side by side with the painted unit art, in the game's renderer (three.js), not Cycles alone.
