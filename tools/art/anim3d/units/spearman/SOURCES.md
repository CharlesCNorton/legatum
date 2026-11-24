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

Round 10b uses no new downloaded or generated asset. Frozen shoulder/back
pigment, broad garment folds and region masks are original MIT code in
`coverage.py`; output art is project CC BY 4.0. Reuses the original painting,
CC0 MPFB anatomy/skin, recorded wool/linen fills and unchanged CC0 motion.

Round 10c reuses the same pinned CC0 `Walk_Loop` (90% source NLA influence),
`Death01` (source phase remapping), idle and hit. No new asset or human joint
keys. Death blends its own settled local leg pose into recoil and the existing
Idle_Loop local arms (85% shield arm, 65% free arm) into the carrying pose
before retargeting. It keeps the
original arm-mounted shield, with damped crest and cape response. Original orchestration is MIT; renders are CC BY 4.0.

Round 11 merge adds no downloaded or generated asset. Fable A's registered
part paint and palette fills derive from the existing project CC BY 4.0
painting. Its Blender node builder and push/pull fill are original MIT project
code, extracted into `kit/paint_graph.py` and `kit/paint_fill.py`. Astra C's
walk/death still use the pinned Quaternius CC0 actions above; Fable B's authored
body death/hit were not adopted under the donor-only requirement.

## Spearman round 12c donor candidate

KayKit Character Animations Free 1.1, Kay Lousberg, CC0-1.0.
Official source/licence: https://kaylousberg.com/game-assets/character-animations
and https://kaylousberg.itch.io/kaykit-character-animations .
Pinned free archive mirror: https://media.githubusercontent.com/media/MightyBubble/Ludots-Assets/fab331eff1cb9c552c60399ea10186ef675cd460/animations/KayKit-Character-Animations-Free-1.1.zip
Archive SHA256: `65882f31f905ad2e953819648a59287cdeab8f623908d5ef701971d3758be20f`.
Evaluated `Death_A`, `Death_B`, `Hit_A`, `Hit_B`; candidate selects `Death_B` and `Hit_B`.
The imported rig supplies reference-calibrated rotations; no KayKit mesh is rendered.
- `Rig_Medium_General.glb` SHA256 `5f725c0f745f36078c7238968cd5c04843cbc6260689eb6e7f5e2bbd7ffdd7ad`
- `License.txt` SHA256 `373b159044d1a886ed15f57ca5a7673ba14e2623c460283452705f2056912ed9`
