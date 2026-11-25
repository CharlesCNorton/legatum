# Spearman-q round 2 — painted CPU review

**Stage reached: 2.** Motion was revised on the original CC0 Quaternius rig,
then the existing Spearman painted kit was fitted on top. Stage 3 is prepared
in `tools/art/anim3d/units/spearman-q/gpu.sh`, but **no GPU pass has run**.
These are CPU diagnostic renders, not an owner-approved final unit. Review
here was frame-by-frame plus geometry/timing checks; the reviewer still needs
to judge the MP4s at playing speed. No round-2 reviewer verdict was available
at handoff.

## Review files

All five are complete 160×160 H.264/yuv420p videos on cream, exactly three
repeats at the atlas frame rate. Encoding uses a temporary filename followed
by an atomic replacement, so the reviewer cannot receive a zero-byte final.

| Clip | File | Frames / fps | Decoded video frames |
| --- | --- | --- | --- |
| Idle | `spearman-q-r2-idle-160.mp4` | 12 / 4 | 36 |
| Walk | `spearman-q-r2-walk-160.mp4` | 16 / 8 | 48 |
| Attack | `spearman-q-r2-attack-160.mp4` | 18 / 14 | 54 |
| Hit | `spearman-q-r2-hit-160.mp4` | 8 / 12 | 24 |
| Death | `spearman-q-r2-death-160.mp4` | 16 / 8 | 48 |

`spearman-q-r2-attack-fullrate.png` contains all 18 attack frames, 2880×160.
The lane's `atlas/spearman-q.webp` has 70 validated 160 px records, WebP q95,
**341,262 bytes**, under the 350,000-byte limit. It is a CPU preview atlas;
nothing replaced the shipping painting or animation assets.

## What changed

The attack keeps `Punch_Cross`'s body weight shift, with a two-bone right-arm
IK layer: a short draw-back, 39 cm fast extension, a short hold and slower
recovery. The spear tip follows a straight, slightly raised line, instead of
following the punch wrist's dip and sweep. The shield stays forward. Arm
layers maintain the same readable spear direction in idle, walk and hit;
their torso and leg motion remain from the library.

One fixed shield socket is parented to `lowerarm_l`; one fixed spear socket
to `hand_r`. Their object attachment transforms are identical across all five
clips. Props are unskinned rigid meshes. During death, the nondeforming
socket bones compensate their parent motion after release, and the equipment
falls to separate positions. No object is hidden by zero scale. Hit now
returns to guard; death has exactly three final held body frames.

The prior-art survey was read, including its CC0 recommendations and forearm
shield attachment practice. KayKit's `Melee_1H_Attack_Stab` was inspected from
the existing CC0 archive, but its low wrist path was not adopted. No paid or
account-dependent source, Mixamo, Meshy or Higgsfield was used.

The existing helmet, red crest, bronze cuirass, greaves, linen skirt, collar
and sunburst aspis were fitted to the unchanged Quaternius body. Frozen
projection UVs and per-part pigment stay on the costume. The render-time
look uses the shared kit's emission, palette and cast-only lighting approach;
the CPU version substitutes the sun cosine and lacks GPU cast shadows.
Small contact shadows follow the feet. Skirt and hair receive collision-only
floor keys during the fall. The full simulated red cloak is not ported yet.
The source master and 40 look files are copied into this lane and hash-pinned.

## Motion verdict by clip

- **Idle:** calm and stable, with small library breathing. The horizontal
  ready spear reads as combat readiness; it is different from the painting's
  upright carry. No clip-specific socket refit.
- **Walk:** the native two-second carry gait is preserved at 16 samples;
  the spear remains readable instead of turning into a foreshortened nub.
  This is an in-place library gait. Support feet move backward at roughly
  0.69 m/s in rig space; game translation must match. Runtime travel and
  idle/walk transition blending were not tested or changed, so this is not
  a claim of zero sliding in the game.
- **Attack:** substantially clearer as a spear thrust. The 39 cm extension
  is about 78% of the two arm bones' combined length. A short anticipation,
  fast extension, hold and slower recovery are all present. The raised shield
  overlaps much of the torso at the peak, but the sampled geometry clears
  the head and torso. Playing-speed punch-through and weight still need review.
- **Hit:** an abbreviated chest recoil, returning to the shared guard with
  no held-tail reset. It is restrained at 160 px; review its readability.
- **Death:** retains the library's squat/fall weight, then releases the
  equipment beside the body. The last three frames are held. Body, armour,
  skirt and hair clear the stone; released props do not intersect the body
  in the sampled frames. This is a scripted, collision-corrected release,
  not a rigid-body simulation. The review movie's reset between repetitions
  is intentional; the atlas marks death non-looping.

## Checks and limits

- Original body topology/vertices/weights and all 65 original rest bones:
  unchanged. Saved poses reconstruct from donor plus documented layers with
  maximum matrix error 9.54e-7. Rigid transform metrics are constant across
  all frames; cloth/hair contact keys are excluded from rigid checks.
- Attack tip line deviation: 9.35e-7 m. Body and costume minimum height:
  at least 0.106999 m over the stone's 0.105 m top. Death hold: exactly 3.
- `audit_contacts.py`: zero sampled torso/head intersections for the aspis
  shell and spear; zero released-prop/body intersections from frame 5 onward.
  This does not establish continuous collision safety between samples or
  certify every garment's self-intersections.
- Atlas decoded validation: pass, including alpha, trim offsets, gutters,
  bounds, counts, timing and held death. No frames dropped to fit the budget.
- ffprobe: all five videos have the requested codec, pixel format, size,
  rate and three-repeat decoded frame counts. All 18 attack images are in
  the full-rate strip.
- Import checker: 0 unresolved local imports. All unit Python files parse;
  shell syntax and `git diff --check` pass. Frozen inputs: 41 hashes pass.
- Repository gates on the existing HEAD: public-claims PASS; hygiene FAIL on
  four pre-existing matrix-`@` expressions misread as email addresses in
  `spearman/donor_motion.py` and `spearman/round12c_review.py`; art FAIL in
  the existing `render-sets.mjs` subprocess. No Rust or UI code changed.
  This is not a green repository-wide CI claim.

## Handoff and next work

The fixed stone was enlarged to **2.2× its previous width/depth** to contain
the extended library corpse. This is the largest visible tradeoff: the
standing figure now has a broad platform. The camera was shifted down 18 cm
to retain canvas margin, identically for every clip. Do not treat this as
painting-match improvement. A more compact CC0 death is preferable if the
reviewer rejects the broad base; simply shrinking it restores the overhang.

The lead runs `bash tools/art/anim3d/units/spearman-q/gpu.sh` outside the
sandbox. It validates inputs/scenes/contacts first, renders the same look
path in Eevee at 512 px, then reduces and validates the GPU atlas. GPU outputs
use `lanes/spearman-q-r2/gpu/` and `spearman-q-r2-gpu-*` review names, preserving
this CPU evidence. GPU cast shadows, final contact depth and output size
remain unverified until that script completes.

No fetch, push or merge was performed. `origin/master` is already an ancestor
of HEAD. Git staging failed with `index.lock: Operation not permitted`.
The complete lane-only patch and requested co-authored commit message are in
`lanes/spearman-q-r2/lane.patch` and `commit-message.txt` for the runner.

FOCUS a: judge the broad base and compact-death alternative before shrinking it.
FOCUS b: GPU cast/contact quality, then the missing full red cloak.
FOCUS c: playing-speed thrust/impact, and runtime walk travel/transition matching.
