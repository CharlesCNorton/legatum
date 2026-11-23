# Trench infantry, driver round 2

Candidate, not art-approved. Run commands from the repo root. Input licences,
prompts and immutable hashes are in SOURCES.md and assets.lock.json. Masters
stay outside git under `~/LegatumRuns/anim-pilot/masters/trench-infantry/`.

```sh
RESOLUTION=256 SAMPLES=8 tools/art/anim3d/units/trench-infantry/render.sh build
tools/art/anim3d/units/trench-infantry/render.sh animate
RESOLUTION=256 SAMPLES=8 tools/art/anim3d/units/trench-infantry/render.sh preview
tools/art/anim3d/units/trench-infantry/render.sh feet
tools/art/anim3d/units/trench-infantry/render.sh pack
# Entire host-side GPU pass, no arguments:
ROUND=2 tools/art/anim3d/units/trench-infantry/gpu.sh
```

The GPU script rebuilds, renders every stage at 512 px, retains 512/256 masters,
renders front/top feet diagnostics, audits, packs and validates the trimmed
160 px atlas, and writes the rest comparison and an eight-second movie decoded
from the atlas. It explicitly requires Cycles Metal GPU and refuses fallback.
Its output appears in both the driver log and the unit's `gpu-round${ROUND}.log`.
The completion receipt checks current blend hashes, device and sample settings.

Round 2 fits the helmet, coat, pack, bedroll and boots in full depth, uses
continuous weighted folded sleeves, adds real buckle/blanket seam geometry,
and corrects orthographic visibility rays before freezing painting UVs.
Generated occlusion pigment supplies cloth behind the moving hands and a clean
stone top with fresh contact shadows. Hidden cloth retains generated brushwork.
All surface projection remains frozen in bind pose on articulated 3D meshes.

The four non-weapon clips still use pinned CC0 Quaternius motion. Sparse source
channels reset per sample; death limbs use anatomical reference with a blend
out of carrying stance. Hit returns to rest. The authored rifle attack aims
from shoulder height and tilts before lifting to protect the bayonet margin.
Foot direction is never patched after retargeting. The audit checks direction,
planted intervals and hit recovery; it does not prove all cloth/kit contacts.

The original painting remains active in the game. The atlas is an unapproved
candidate with no runtime changes. At 64 px it reads as the same unit; at 256 px
it remains distinguishable in the shoulders, face/hand volumes and cloth drape.
Falling cloth and equipment contact need further refinement. No PASS marker.
Review the current external log, strips and movie before continuing. Incoming
GPU evidence is preserved in `driver-r1-gpu/` and the review archive; current
CPU previews must not be mistaken for a round-two GPU result.

Round-two CPU evidence: Cycles / 8 samples, all 40 frames at 512/256; trimmed
160 px atlas **182,300 bytes at quality 90**. Bounds, lossless alpha, offsets,
source hashes, all-clip motion and held death pass. Movie: H.264/yuv420p,
1600x348, 240 frames / eight seconds. Structural audit and hit recovery pass;
feet stay within 9.94 degrees of forward. Python/Bash syntax, whitespace and
working-file hygiene checks pass. Browser art gate remains unavailable in the
sandbox. GPU round two still requires the host command above.
