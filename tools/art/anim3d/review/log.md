# Spearman 3D v2 running log
- References inspected: map, panel, full source and prior comparison; source fetch helper 403, direct curl succeeded; masters remain outside git.
- MPFB 2.0.18 installed in isolated Blender resources; Blender 5.3 creates its real human mesh and 53-bone game_engine rig successfully. System asset pack download is slow (~260 KB/s).
- b-mpfb-kit-plain.png emitted: real MPFB anatomy and kit in three views; fails finish bar (narrow stance, circular shield, plain surfaces). Revised stance, shield and crest afterward.
- c-textured-lit.png emitted with CC0 PBR: still too smooth and toy-like beside painting; closer diagnostic confirms chest is bronze shell, not bare skin. Adding stronger material contrast and armour edges.
- CMU 77_02 standing and 02_01 walk downloaded with conversion licence; first hand-keyed attack and real cloth bake saved. Retarget parser fixed its HIERARCHY header handling.
- Hunyuan3D mini skipped: sandbox has no Metal/MPS, so the requested sub-20-minute Apple GPU path cannot be tested here; CPU generation would exceed the light local-work constraint.
- nice -n 10 is invoked as requested, but macOS sandbox denies setpriority; Blender thread limit remains four. Thumbnail cache writes outside resources are denied and nonfatal.
