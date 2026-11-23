# Horseman inputs and motion

All raw assets and masters stay under `~/LegatumRuns/anim-pilot/`. Input hashes
are pinned in `../../mounted/assets.lock.json`; `prepare.py` checks the painting
and generated fills. No new service, download or account was used in this pass.

| Input | Version / source | Licence and use |
| --- | --- | --- |
| Quaternius Horse | Ultimate Animated Animal Pack, July 2021; [official pack](https://quaternius.com/packs/ultimateanimatedanimals.html); [immutable GLB mirror](https://raw.githubusercontent.com/trebeljahr/quaternius-showcase/5b491b755c6d2aaa263aaaf8671b30b559a380a4/public/glb/animals_pack/Horse.glb) | CC0-1.0; source mesh, skin weights, Idle, Walk, Gallop, Idle_HitReact_Left and Death |
| MPFB anatomy and rig | MPFB 2.0.18 / MakeHuman system assets, installed by shared setup | CC0 output; saddle-parented human anatomy and native weights; MPFB software GPL-3.0-or-later |
| Horseman painting | [Project source](https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/horseman-source.png) | Project CC BY 4.0; frozen camera projection on actual geometry |
| Coat, linen, bronze, hair fills | Original built-in ImageGen, 2026-11-22; `../../mounted/painted-fills.prompt.txt`; external `assets/horseman/painted-fills.png` | Project CC BY 4.0; surfaces the painting does not show |
| Surface scans | ambientCG Metal034, Fabric030, Travertine001; Poly Haven brown_leather and fine_grained_wood | CC0; shared source inventory in external `assets/SOURCES.md` |

Horse GLB SHA256:
`fbddb2c97179eca896ec69c985cd9cc74540484510776c400df64e088e9f2414`.

Original MIT scripts adapt the licensed quadruped actions, register the real mesh
to the painting, and supply the mounted rider's seated response, weapon attack,
rein/tail follow-through and death release. Rider responses are authored mounted
animation, not human motion capture. Source horse actions are sampled after
resetting sparse channels to bind defaults; no post-retarget hoof orientation
patch is used. The front/top feet review shows actual deformed lower-limb meshes.
