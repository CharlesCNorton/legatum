# Barbarian spearman — driver round 2

Unapproved 3D art candidate. No PASS marker. The previous driver GPU pass
completed all stages, 512/256 masters, atlas and movie: 191422 bytes at Q80.
That exact GPU evidence is archived under masters/barbarian-spearman/driver-r1-gpu/.
Development-round labels in the older external log do not match driver rounds.

This pass adds a continuous thick shoulder pelt, better shield slant, a narrower
source-spear mask that preserves the gripping anatomy, original generated pelt
and leather fills, and painting projection restricted to the stone's front lip.
Trying to project the whole stone copied the painted feet; a luminance mask
still left pale boot-shaped holes. The final lip-only mask avoids both defects.
One automatic rest histogram grade remains frozen across every frame.

The full-depth fitted MPFB skin is rebound to joints fitted by the same field,
retaining 19158 vertices, original weights and 53 bones. This corrects the old
ankle/shoe offset during articulation. Thick straps, bevels, physical cloth,
frozen rest UVs, eight real AO/curvature bakes and product lights remain editable.

Idle, move, hit and death now retarget pinned CC0 Quaternius actions with Blender
rest/roll constraints; the original spear-specific thrust remains. Carrying arms
use the library idle layer. Ground correction translates the root. A 65mm hip-lowering knee solve fits the
upright library walk to the fixed canvas while preserving captured ankles; source
foot rotations are independently checked in the saved-scene audit. The audit
also measures a common virtual-ground toe stance speed and planted shoe height.
All eight move samples have actual top/front footwear renders. Death has keyed
support-plane cloth folds; this is not a cloth simulation.

At 256px the figure preserves the painting's brushwork, and the shield/pelt fit
is closer, but it remains distinguishable: the hand/spear are thin and dark,
shoulder fur is less natural, the stone top is smooth, and hidden skin/cloth
surfaces lack the painting's finish. At 64px it clearly reads as the same unit;
rest proportions are close but not interchangeable. Source-derived locomotion
is more articulated, but shin/boot joins and the compressed death cloth remain
visible problems. Neither technical checks nor size limits establish clean clips.

Local output is CPU256/8 preview evidence. Previous GPU512 exports are retained
in driver-r1-gpu/512 and 512-driver-r1, not relabelled as current masters.
The executable, no-argument lead-side handoff is:

```sh
ROUND=2 tools/art/anim3d/units/barbarian-spearman/gpu.sh
```

It checks GPU availability, rebuilds registration/paint/bakes/clips, renders all
review stages including g-feet at Cycles GPU512/64, exports 512/256, packs the
trimmed 160px atlas at Q75 or better within 200000 bytes, validates it, audits
saved rigs, and creates the eight-second decoded-atlas H.264/yuv420p movie.
The transcript and status identify the failed stage if anything fails.
Fresh GPU visual review remains required. Nothing is uploaded or integrated.

Final CPU checks: 40 frames and trim/alpha/hold validation passed; preview atlas
185920 bytes at Q80. Scene audit passed with maximum grip gap 0.0236m, sole error
below 0.00001m, horizontal stance error below 0.000001m and unchanged source foot
rotations. Movie: H.264/yuv420p, 1600x348, 240 frames, 8.000 seconds. Seventeen
Python parses, two shell syntax checks, six input hashes, repeated-grade byte
equality and whitespace check passed. GPU provenance correctly rejects previews.

Git staging/commit was denied by the sandbox at
.git/worktrees/lane-22/index.lock. The runner should commit the present changes:

```
Refine barbarian spearman surfaces and retarget open motion

Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>
```
