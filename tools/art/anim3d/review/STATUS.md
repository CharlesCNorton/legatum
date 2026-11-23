# Animated units status

Updated 2026-11-23T07:53:38Z. Round = finished rounds (driver count). Pass = the lane declared the bar met (`<slug>-PASS`); the lead and Sam still review.

| Unit | Branch | State | Rounds done | Atlas KB | Pass | Latest note |
| --- | --- | --- | --- | --- | --- | --- |
| archer | `astra/unit-anim-3d-archer` | idle | 0 | 184 | no | - GPU handoff wrapper saved at tools/art/anim3d/units/archer/gpu-round.sh. No unit-specific feedback file was present at final check. |
| arquebusier | `astra/unit-anim-3d-arquebusier` | idle | 0 | 195 | no | - Commit attempted with required Co-Authored-By trailer; sandbox denied .git/worktrees/lane-15/index.lock. Changes are uncommitted for the runner; nothing pushe |
| artillery | `astra/unit-anim-3d-artillery` | idle | 1 | 179 | no | - Published painted rest pose and 50/50 comparison; real AO shader, micrograin, edge geometry and hidden-surface fill. |
| autonomous-armour | `astra/unit-anim-3d-autonomous-armour` | idle | 0 | 192 | no | Round 1 final CPU checks PASS: 40 x 256 clip masters, 16 required review artifacts, current master hashes, geometry audit, trim/alpha reconstruction, motion/loo |
| barbarian-archer | `astra/unit-anim-3d-barbarian-archer` | idle | 0 | 185 | no | Commit attempt blocked by sandbox: cannot create .git/worktrees/lane-2/index.lock. Work left uncommitted for runner. origin/master advanced by two commits durin |
| barbarian-crossbowman | `astra/unit-anim-3d-barbarian-crossbowman` | idle | 0 | 164 | no | - Git add/commit blocked: sandbox denies .git/worktrees/lane-20/index.lock. Changes left uncommitted for runner; commit-based repository gates deferred. No push |
| barbarian-musketman | `astra/unit-anim-3d-barbarian-musketman` | idle | 0 | 190 | no | - Commit attempt blocked by sandbox index.lock permission; left focused changes for the runner. origin/master is already an ancestor of HEAD. Commit-based repos |
| barbarian-pikeman | `astra/unit-anim-3d-barbarian-pikeman` | idle | 0 | 179 | no | - Independent rig audit found attack wrist-to-shaft distance 18.1 cm: the depth thrust exceeded the rear arm's reach. Replacing it with a shorter diagonal thrus |
| barbarian-scout | `astra/unit-anim-3d-barbarian-scout` | idle | 0 | 179 | no | Git commit and origin/master merge blocked by sandbox index.lock / ORIG_HEAD.lock permission denial; changes left for runner. Post-merge determinism and pin tes |
| barbarian-spearman | `astra/unit-anim-3d-barbarian-spearman` | idle | 0 | 181 | no | - HEAD-based hygiene/public-claims gate passed, but HEAD excludes this uncommitted work; this is NOT claimed as a gate pass for the new files. Browser art gate/ |
| biplane | `astra/unit-anim-3d-biplane` | idle | 0 | 185 | no | - Git add blocked by .git/worktrees/lane-19/index.lock denial. Runner must commit and merge upstream; no push/PR performed. |
| bomber | `astra/unit-anim-3d-bomber` | idle | 0 | 189 | no | Final verification: H.264/yuv420p MP4 1600x348, 240 frames, 8.000 s; 48 masters each at 512 and 256; all 16 review files present. Git commit blocked by sandbox  |
| byzantine-heir | `astra/unit-anim-3d-byzantine-heir` | idle | 0 | - | no | - Rebuild exposed a Blender UV-layer handle invalidated by edit-mode unwrap; bake stopped before saving. Fixed by retaining the UV name as a string, added nonze |
| cataphract | `astra/unit-anim-3d-cataphract` | idle | 0 | 183 | no | Packed and decoded 40 trimmed frames, quality 80, 187204 bytes; wrote cataphract-round1.mp4. Warnings: [] |
| cavalry | `astra/unit-anim-3d-cavalry` | idle | 0 | - | no | e-death: review emitted from CYCLES frames; no art-pass claim. |
| composite-archer | `astra/unit-anim-3d-composite-archer` | idle | 0 | 176 | no | - Git add/commit blocked: cannot create .git/worktrees/lane-9/index.lock (Operation not permitted). Left all changes uncommitted for the runner; do not push or  |
| crossbowman | `astra/unit-anim-3d-crossbowman` | idle | 0 | - | no | - Started render e-attack (CPU). |
| cuirassier | `astra/unit-anim-3d-cuirassier` | idle | 0 | - | no | - Emitted c-details: 1 frames, 256 px CYCLES/CPU, 8 samples. |
| drone-swarm | `astra/unit-anim-3d-drone-swarm` | idle | 0 | 187 | no | e-hit: 4 frames at 256/64 from 512px CYCLES/CPU, 12 samples. |
| eagle-warrior | `astra/unit-anim-3d-eagle-warrior` | idle | 0 | - | no | - Authored idle, move, attack, hit and terminal death on the MPFB skeleton; no mocap or cloth simulation claimed. |
| field-cannon | `astra/unit-anim-3d-siege` | idle | 8 | 178 | no | - ROUND 8 GIT: origin/master remains an ancestor; no fetch/merge needed. git add denied at .git/worktrees/siege-round2/index.lock (Operation not permitted), so  |
| fighter | `astra/unit-anim-3d-fighter` | idle | 0 | 193 | no | - Rendered e-death: 512px, CYCLES; review published. |
| gaesatae | `astra/unit-anim-3d-gaesatae` | idle | 0 | - | no | - Adjusted head width/position, grip, ankle stance and cloth fold frequency before clip authoring. No quality PASS claimed. |
| horseman | `astra/unit-anim-3d-mounted` | idle | 1 | 195 | no | - Commit attempt failed: sandbox denied .git/worktrees/lane-6/index.lock. Changes remain uncommitted for the runner, with exact message and requested co-author  |
| howitzer | `astra/unit-anim-3d-howitzer` | not started | 0 | - | no |  |
| hunter-killer | `astra/unit-anim-3d-hunter-killer` | not started | 0 | - | no |  |
| infantry | `astra/unit-anim-3d-infantry` | not started | 0 | - | no |  |
| jet-bomber | `astra/unit-anim-3d-jet-bomber` | not started | 0 | - | no |  |
| jet-fighter | `astra/unit-anim-3d-jet-fighter` | not started | 0 | - | no |  |
| keshig | `astra/unit-anim-3d-keshig` | not started | 0 | - | no |  |
| knight | `astra/unit-anim-3d-knight` | not started | 0 | - | no |  |
| landship | `astra/unit-anim-3d-landship` | not started | 0 | - | no |  |
| legionary | `astra/unit-anim-3d-legionary` | idle | 0 | 187 | no | - Python syntax (10 scripts), shell syntax and git diff whitespace check PASS. Commit attempted with required co-author line, but sandbox denied `.git/worktrees |
| main-battle-tank | `astra/unit-anim-3d-main-battle-tank` | not started | 0 | - | no |  |
| mechanised-infantry | `astra/unit-anim-3d-mechanised-infantry` | not started | 0 | - | no |  |
| medjay | `astra/unit-anim-3d-medjay` | idle | 0 | 164 | no | Visual review: recognizable Medjay at 64px, below painting parity at 256px. Improve head/headband/feather registration, facial geometry, body proportions and at |
| musketman | `astra/unit-anim-3d-musketman` | not started | 0 | - | no |  |
| panzer | `astra/unit-anim-3d-panzer` | not started | 0 | - | no |  |
| peltast | `astra/unit-anim-3d-peltast` | idle | 0 | 166 | no | - Round1 verdict: recognizable as peltast at64px, below painting at256px (face/cap, narrow torso, regular cloth folds, boot laces and abrupt rearm). No PASS mar |
| phalangite | `astra/unit-anim-3d-phalangite` | idle | 0 | 189 | no | - Existing-HEAD repository gate: hygiene/public-claims passed; art render-sets.mjs exited 1. Because the commit was blocked, that gate does not cover this uncom |
| pikeman | `astra/unit-anim-3d-pikeman` | not started | 0 | - | no |  |
| reislaufer | `astra/unit-anim-3d-reislaufer` | not started | 0 | - | no |  |
| rifleman | `astra/unit-anim-3d-rifleman` | not started | 0 | - | no |  |
| rocket-artillery | `astra/unit-anim-3d-rocket-artillery` | not started | 0 | - | no |  |
| scout | `astra/unit-anim-3d-scout` | idle | 0 | 195 | no | Final verdict: genuine 3D and recognizable scout at 64px; below painting parity at 256px. Next pass should match raised-knee stance, larger expressive face/bear |
| settler | `astra/unit-anim-3d-settler` | idle | 0 | - | no | - Saved 3D audit passed: source hashes, 53 bones, actual motion, exact loop closing keys and held death; ground/bounds recorded; collision limits explicit. |
| spartan-hoplite | `astra/unit-anim-3d-spartan-hoplite` | idle | 0 | 169 | no | Commit attempt blocked: Git could not create .git/worktrees/lane-5/index.lock (Operation not permitted); changes left for the runner to commit with the requeste |
| spearman | `astra/unit-anim-3d-v2` | idle | 8 | 178 | no | - Final handoff: git add/commit blocked by sandbox denial creating .git/worktrees/spearman-round2/index.lock (exit 128). Changes remain scoped and uncommitted.  |
| stealth-bomber | `astra/unit-anim-3d-stealth-bomber` | not started | 0 | - | no |  |
| stealth-fighter | `astra/unit-anim-3d-stealth-fighter` | not started | 0 | - | no |  |
| tagmatic-soldier | `astra/unit-anim-3d-tagmatic-soldier` | idle | 0 | 186 | no | - GPU handoff: from repo root, tools/art/anim3d/units/tagmatic-soldier/gpu.sh (no arguments; uses ROUND from driver). This performs geometry audit, all GPU stag |
| tank | `astra/unit-anim-3d-vehicles` | idle | 1 | 194 | no | - Commit attempt blocked by filesystem denial creating .git/worktrees/lane-5/index.lock; no escalation or workaround. Changes left unstaged for runner, exact co |
| trench-infantry | `astra/unit-anim-3d-trench-infantry` | not started | 0 | - | no |  |
| war-elephant | `astra/unit-anim-3d-war-elephant` | idle | 0 | 179 | no | - Final MP4 verified with ffprobe: H.264, yuv420p, 1600x348, 30 fps, 240 frames, 8.000 seconds. Decoded frame inspected for all five trimmed-atlas reconstructio |
