# Scout driver round 2

Unapproved art candidate; no `scout-PASS`. The painting remains the game token.

Opened the incoming GPU rest comparison, all five strips and round-one MP4 frames
before editing. That GPU pass completed: 40 frames, 199,762 bytes at quality 80.
The initial surfaces still had broken green/gold chest patches, an oversized exposed
hat and a floating raised sandal. The hand-keyed walk and collapse were stiff.
The incoming evidence is retained in `masters/scout/driver-r1-gpu/` outside git.

This round replaces colour-threshold garment masks with feathered spatial masks,
preserving the painting's warm fold highlights. The full-depth scarf, raised sleeve,
hat and raised calf are fitted more closely to the source; the calf is lengthened
16% without compounding foot scale. The stone has pigment grain. Existing generated
hidden-side fills, actual AO/curvature bakes, bevelled straps, folded thick cloth,
product lighting and a single automatic rest histogram grade remain. The image is
fixed UV pigment on real geometry, with no billboard or per-frame reprojection.

Idle, walk, hit and death now use the pinned CC0 Quaternius Standard actions through
Blender rest/reference/roll-calibrated constraints. The walk layers source idle arms
onto the staff-bearing reference, with a forward torso lean and lowered carrying arm.
Foot rotations are not patched after retargeting. Translation-only stance stabilization
uses one virtual ground speed for the in-place walk. Swing toe tuck is present in the
source. The staff attack and cloth follow-through/contact corrections remain authored.
The front/top feet sheet renders all eight samples and records numerical contact and
lateral-alignment diagnostics. See `SOURCES.md` and `motion-*.json` in the masters.

At 256px the chest paint and rest pose are closer, but the face/raised hand are still
less convincing, the cowl has a seam, and the figure remains narrower than the painting.
At 64px it reads as the same scout; the silhouette and leg/hat proportions remain
distinguishable. Rest silhouette IoU is 0.7811 at alpha >24 (incoming 0.7665), which
is only a diagnostic. The library walk/death are better; attack is still restrained,
and folding cloth reveals texture stretching. This does not meet painting parity or
establish five artistically clean clips. No PASS marker is justified.

The CPU checks caught top clipping first in the staff, then in the slung hat during
one walk sample. The carrying reference and physical hat placement were corrected;
validation thresholds were retained. Validation now invalidates old success records,
and the GPU receipt binds the current atlas, source, foot renders and video.

The lead runs this executable from the repository root:

```sh
ROUND=2 tools/art/anim3d/units/scout/gpu.sh
```

It rebuilds all five clips, renders b/c/details/d/e stages with Cycles Metal GPU64/512,
keeps real 512px masters and derived 256px frames, audits rig/projection, renders the
front/top feet check, packs 40 trimmed 160px samples at quality >=75 / <=200,000 bytes,
validates, and encodes the decoded atlas into the eight-second five-clip MP4. Video is
H.264/yuv420p, 1600x348, 240 frames, 2x scale on cream. The script keeps a transcript,
writes a success receipt only after checks pass, and never writes art PASS. The new
GPU pass still requires host execution and visual review.

All masters and review artifacts stay under `~/LegatumRuns/anim-pilot/`; no masters
are committed, no game loader is changed, and no push, PR or merge is performed.

Final CPU validation passes all 40 samples and trim rectangles: current source hashes,
reconstructed alpha, timing, motion, margins and held death. Actual 512px masters
and 256px copies are present. Atlas: **180,016 bytes at quality 75**, 1165x740.
Rig audit: 53 bones, stationary base, body minimum Z=0.100, staff grip distance <=0.0426m.
Foot stance residual is 1.94e-7m relative to virtual ground; lateral toe offset <=0.00306m.
The decoded movie and contact sheet were opened; FFprobe verifies H.264/yuv420p,
1600x348, 240 frames/eight seconds. Fifteen Python and three shell syntax checks,
missing-master/no-receipt rejection, CPU-master receipt rejection and whitespace checks
pass. These are CPU results; the new host GPU pass is outstanding.

Git could not create lane-13/index.lock; leave these changes for the runner to commit
with the requested gpt-6-astra co-author trailer. No commit-based gate is claimed
against unchanged HEAD. origin/master is already an ancestor.
