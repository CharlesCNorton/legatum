# Spearman: round 13 combined candidate

2026-11-24. CPU reviewed; GPU pass and final art approval pending. No PASS.
Exact source branches, lane timings and history: `../LOG.md` and external
`lanes/spearman-r13-merge/source-branches.json`. Current review:
`~/LegatumRuns/anim-pilot/review/3d-v2/spearman-round13-note.md`.

## Selected result

Fable C guard and painted look (on retained A/B work), Astra c lower swing and
calmer collapse, R12 KayKit hit. Idle/attack rebuilt on the new guard and
reviewed at 256/160/64 before deliberate action re-pinning. Fable D death was
rejected by the 06:40Z director verdict; its post-retarget foot rotations were
also excluded. Later unreviewed D commits are not this candidate.

- Combined CPU proxy, 256 px / 8 samples: IoU **0.9512536** at zero offset,
  blurred ΔE **3.3866**, raw **7.2743**. Regions: head 3.74, torso 2.63,
  cloak 5.03, shield 2.22, legs 2.73, feet 5.45, base 3.23. Raw is informational;
  only the agreed blurred colour target passes. R12 CPU: .9394 / 4.55,
  feet 13.35 and base 4.75.
- Fable C's earlier 1280 Eevee result was .9534 / 3.35. Do not present that
  as this merge's final GPU score.
- CPU trimmed 160 atlas: **192,866 bytes, Q80**, 40 records, validated. Movie:
  five clips, 1600×352, H.264 yuv420p, 24 fps, 192 frames, 8 s.
- 36 tests; all 40 poses audited without findings, with a repeat audit of the
  final changed attack. Attack sole entry/exit difference from idle <0.001 mm.
- 33-sample walk: slip .0042 mm, floor .0001 mm, heading 5.142° (readable 9.175°),
  seam zero. Root XY correction 48.963/50 mm, sole correction 39.954/40 mm:
  do not grow feet or alter the guard without repeating contact checks.

## Open, ranked

1. Spear-side cloak is narrower than the painting between arm and hip. Director
   measured 579 vs 632 px in x98–112/y120–175. A local flare A/B is next; do not
   disturb the now-correct ankles/knees to fix the red mass.
2. Ground shadow's far edge is slightly strong/hard. CPU omits cast shadow;
   judge final Eevee before reducing it. Base colour and lip improved markedly.
3. At 256: forearm red/pale sliver near (106,123), dark skirt linen, simplified
   diagonal cloak hem. These are subtle at 160 and largely disappear at 64.
4. Walk toe-off still exposes a lighter sole; the donor foot rotations remain
   intact. Death shaft clears the knees by frame 3 but remains diagonal across
   frame 2. The calm ending keeps the crest/shield readable at 64, at the cost
   of the shield covering much of the torso.
5. Verify the whole idle-to-walk transition on the host movie. The fixed guard
   registration offset is carried to the whole donor track; a walking pose
   naturally differs from standing idle. Do not claim identical entry poses.
6. GPU parity is a new enforced gate, not yet run in the CPU sandbox.

## Closed: regression checks

- Feet sit under their own painted sandal detail; no longer enlarge or darken
  them to fix the old registration fault. Shins, straps and sole contact match.
- Shaft thickness/wood, shield/helmet spans, calf containment, no floating ring.
- Base lip and warm stone, ground shadow anchored to moving ankles.
- Lower walk swing, separate legs, donor orientation and all eight foot limits.
- Attack feet return to the exact guard; idle/attack hashes deliberately pinned.
- Hit is retained per the 06:16Z GPU verdict, which explicitly withdrew the
  earlier suggestion to exaggerate its peak.

## Host handoff

Run from repo root: `ROUND=13 tools/art/anim3d/units/spearman/gpu.sh`.
It rebuilds all clips and calibration, checks scene/transition/frozen actions,
renders all stages and 512/256 masters, compares rest pixels from the shared
look and delivery paths, renders top/front feet, audits, packs/validates the
atlas, writes the five-clip movie, critique and note. No automated art PASS.

## Stable settings

Orthographic camera (2.5, -7, 3), target (0,0,1.2), scale 2.9. Paint registration
5.3425 source pixels per 256-canvas pixel, source (627,627) at (127.5,128).
Registration correction lives in look textures; never also change frozen UVs.
MPFB game rig; Quaternius Idle_Loop/Walk_Loop, influence .90; KayKit Hit_B;
keyed attack/collapse. Foot width 1.50, original length, height 1.18.
Eevee emission paint: sun pi at 24°, paint cast .22, fill cast .30, base cast
.16, contact .40. Clips 8/8/10/4/10 at 4/6/14/12/4 fps. CPU proxy is ungraded.
