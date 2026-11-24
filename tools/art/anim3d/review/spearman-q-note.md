# Spearman-q: motion-first Quaternius rebuild

Review candidate, not accepted spear motion. All five videos are 160×160, plain Cycles shading on cream, H.264/yuv420p, with exactly three repeats. The unchanged painting camera and stone come from the existing Spearman master. No painted-look pass, old body or old animation is used.

Sources: Quaternius Universal Base Characters Standard (Superhero male, original rig and weights), Universal Animation Library 1 Standard, and Universal Animation Library 2 Standard. All three were downloaded free from the official itch pages; all bundled licences say CC0 1.0. URLs, upload IDs and archive hashes are in `tools/art/anim3d/units/spearman-q/SOURCES.md` and `~/LegatumRuns/anim-pilot/assets/SOURCES.md`.

| Clip | Library action | Frames / game fps |
| --- | --- | --- |
| Attack | UAL1 `Punch_Cross` | 16 / 14 |
| Idle | UAL2 `Idle_Shield_Loop` | 12 / 4 |
| Walk | UAL2 `Walk_Carry_Loop` | 12 / 6 |
| Hit | UAL1 `Hit_Chest` | 8 / 12 |
| Death | UAL1 `Death01` | 14 / 4 |

Attack is a **punch-derived thrust substitute, not a native spear or sword stab**. The inspected free sword clips were sweeping cuts, overhead attacks or combos; they gave much worse spear and shield motion. Body motion is transferred from the library using rest-space rotations, with no authored poses or IK corrections. Walk retains its native duration; attack and idle have modest uniform timing changes. Hit and death preserve source speed and hold their final pose to fill the requested counts.

Shield: unskinned rigid bronze mesh → `prop_shield_grip` → original `lowerarm_l`. Spear shaft and leaf head: unskinned rigid meshes → `prop_spear_grip` → original `hand_r`. Each clip has a static entry-pose socket fit. The socket never changes during playback, but its offset differs between clips; transitions are therefore not production-ready. No prop has an Armature modifier, shape keys or vertex weights. The shaft and leaf together are 2.05 m long.

Motion verdict: idle and carry walk are coherent first passes and the shield no longer warps. Attack is still not convincing: punch timing, a foreshortened extension, an awkward cross-body recovery and a compromised grip. Hit ends in its library recoil and snaps when the review repeats. Death is a readable fall, but the hand-attached props intersect the ground/base and the body extends beyond the disc. No release physics or collision correction was added. The base character is deliberately plain and uncostumed. This proves the reusable rig/clip pipeline; it does not meet final Spearman motion quality.

Checks: all 62 rendered game frames verified; original body mesh/topology/weights and all 65 rest bones unchanged; baked body rotations match sampled library motion (maximum quaternion dot error 1.79e-7); rigid props verified on every frame (distance variation below 0.00000035 m); minimum nontransparent canvas margin 7 px. ffprobe decoded 48/36/36/24/42 video frames respectively, with the requested codec, pixel format, resolution and rates. Import checker: 0 unresolved imports. Shell syntax and diff whitespace checks pass.

Repository gates are not green: the pre-existing HEAD fails hygiene on matrix `@` expressions misread as emails in `spearman/donor_motion.py` and `spearman/round12c_review.py`; the art distinctness subprocess fails in `render-sets.mjs`. Public claims pass. These failures were present before this lane's untracked changes. No Rust or UI source changed. Git staging failed because the sandbox denied `index.lock`; the runner can apply the lane patch and commit with the supplied message. `origin/master` is already an ancestor of HEAD; no fetch or push was performed.

Editable scenes: `~/LegatumRuns/anim-pilot/lanes/spearman-q/masters/{attack,idle,walk,hit,death}.blend`. Verification receipt, raw frames, contact sheets and logs are beside them. All 16 attack frames are in `spearman-q-attack-fullrate.png`.
