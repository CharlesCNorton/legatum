# Byzantine heir animation sources

The original painting, MPFB 2.0.18 / MakeHuman CC0 anatomy and four generated
project CC BY 4.0 fills are pinned in `assets.lock.json`. Rendered art is CC BY
4.0; original scripts are MIT. External files stay under `ANIM_ROOT/assets/`.

The motion records below are the CMU Graphics Lab database's free-use recordings
in Bruce Hahne's 2010 MotionBuilder BVH conversion; the conversion adds no
restrictions. Download URLs and SHA256 are pinned in `motion.lock.json`.

| Recording | Use | Source |
| --- | --- | --- |
| CMU 02_01 | Walk, one captured cycle, frames 1–133 | [BVH](https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/002/02_01.bvh) |
| CMU 77_02 | Standing/idle, frames 80–176 | [BVH](https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/077/77_02.bvh) |
| CMU 90_18 | Rug-pull fall, death frames 50–360; early balance-loss excerpt resampled forward/back for hit | [BVH](https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/090/90_18.bvh) |
| CMU 77_18 | Lying down/getting up, inspected but not used | [BVH](https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/077/77_18.bvh) |

[CMU database](https://mocap.cs.cmu.edu/) and
[conversion licence/readme](https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/READMEFIRST.txt).
The data used in this project was obtained from mocap.cs.cmu.edu; the database
was created with funding from NSF EIA-0196217. The downloaded index is
[cmu-mocap-index-text.txt](https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/cmu-mocap-index-text.txt).

The weapon-specific attack and banner release are authored. Idle, walk, hit and
death skeletal motion use the recordings above, with fixed axis/rest calibration,
retiming, uniform anatomical scale and global contact translation. The hit is an
adapted balance-loss excerpt, not a claim that CMU recorded a weapon strike.
Cloth follow-through/settling is authored, not physics simulation.
