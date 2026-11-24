# Spearman motion sources — round 9

All downloads and editable masters stay under `~/LegatumRuns/anim-pilot/`.

| Use | Source and version | Licence |
| --- | --- | --- |
| Idle, walk, hit, death | [Quaternius Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html), free Standard edition distributed 2025-06-10; `Idle_Loop`, `Walk_Loop` (idle arms layered through Blender NLA), `Hit_Chest`, `Death01` | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) |
| Download mirror | [J-Ponzo/gltf-universal-animation-library](https://github.com/J-Ponzo/gltf-universal-animation-library/tree/e24c23cf2a1323488a3faa226ea7ea21f644b73e), immutable commit `e24c23cf2a1323488a3faa226ea7ea21f644b73e`, `glTF/AnimationLibrary_Godot_Standard.gltf` and adjacent `.bin` | CC0; bundled `LICENSE` retained beside assets |
| Retargeting | Blender 5.3.0 glTF importer and native Copy Rotation constraints, rest/reference matrix offsets including bone roll; `infantry/retarget.py` | Blender GPL; original orchestration MIT |
| Weapon-specific attack and equipment release | Original project keyframes, rebased on the new idle reference | MIT code; CC BY 4.0 rendered artwork |
| Superseded round-8 motion | [CMU 02_01](https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/002/02_01.bvh), [CMU 77_02](https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/077/77_02.bvh); Bruce Hahne 2010 BVH conversion | CMU free research/commercial use; retained externally for comparison, no longer used by spearman |

The [official pack page](https://quaternius.com/packs/universalanimationlibrary.html)
identifies CC0 and the free Standard subset. No paid animations, Mixamo, account
or service are used. The source mannequin supplies motion only; rendered anatomy
remains MPFB 2.0.18 CC0 with its original 53-bone game_engine rig and weights.
Existing painting, generated fills and scanned-surface provenance remains in
`assets/SOURCES.md`, `assets.lock.json` and `fills.lock.json`.

Pinned files in `assets/quaternius-ual/`:

```
0ff075c7ad6855c5c2c37a171592ee8f0d6ab2f58259e2be77a9b63dd8027765  AnimationLibrary_Godot_Standard.gltf
6e65377d81558333c4093dbb144a48fd19019343d82b1a3a7992a98ec0e0543c  AnimationLibrary_Godot_Standard.bin
a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499  LICENSE
```

Round 9c reuses these exact pinned CC0 files. `Walk_Loop` runs at 92% source
NLA influence before rest/roll retargeting; idle arms remain the existing open
layer. `Hit_Chest` and `Death01` are time-remapped with a guard recovery blend
for hit. No new human joint motion is invented for those clips. Continuous
weapon attack curves, passive crest/shield springs and cloth response are
original MIT orchestration; no new asset download.

## Fable-b motion (2026-11-24)

- **Death, hit:** original keyed motion in `collapse.py` (no donor clip). MIT code; CC BY 4.0 rendered artwork.
- **Idle, move:** unchanged Quaternius Universal Animation Library `Idle_Loop` / `Walk_Loop` (CC0), with the procedural weight-shift layer in `motion.WalkWeight`.
- **Attack:** unchanged original weapon keys.
