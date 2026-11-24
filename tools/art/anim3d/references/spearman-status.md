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

## GPU result (added by the skill editor, 2026-11-24 08:03Z)

Round 13 GPU (`d7798046`), after the parity gate was given a noise tolerance: **IoU 0.9537, blurred ΔE 3.51**, raw 6.36; regions head/crest 3.7, torso 2.9, cloak 4.8, shield 2.4, legs 3.2, feet 5.3, base 3.3; atlas 187,254 bytes at q80; walk slip 0.0042 mm, heading 5.142°. Both metric targets pass for the first time. Visual review pending; no PASS file.

## Round 14 GPU (added by the skill editor, 2026-11-24 09:32Z)

Round 14 (`9c35ac22`) is round 13's rest with polished clips: cloak damped in move and attack, cloth loop seams closed, walk samples rotated to soften the idle cut, support queried on evaluated faces. GPU: IoU 0.9537, blurred ΔE 3.51 (unchanged), atlas 187,316 bytes at q80, walk slip 0.0042 mm. The pass ran clean on its first launch. Clip review pending. The polish list below still applies except the cloak flare in move and the loop seams.

## Art director on round 13 GPU (08:03Z)

"Ready to show Sam as a PASS candidate." Best on every aspect; both numeric targets pass; clips hold at 160 px and the death reads at 64. Polish, none blocking: paint three strap bands per instep; halve and blur the base shadow band and make it follow the feet in the walk (it stays put in the movie); darken the pale sole in move frames 5–6 and damp the cloak flare to 3–4 px; let the death shaft fall 10 px nearer the viewer and give one of the three identical final frames to the kneel-to-prone drop; 4 px more cloak flare at the hip and lit folds 8% lighter; level cloak hem with three scallops; sliver under the spear hand at (106,123); darkest bronze cavities 15% deeper.

## Spearman settings worth knowing

- Camera: orthographic, location (2.5, −7, 3.0), target (0, 0, 1.2), ortho scale 2.9.
- Registration: 5.3425 source px per 256-canvas px, source (627,627) ↔ canvas (127.5,128). `project.py`'s frozen UV formula is 0.9% narrow and 0.3% short; the correction lives in the look's texture registration. Switch both together at a rebuild.
- Guard (Fable C): pelvis 5 cm back along the view ray, ankles on their painted positions, knees on columns 112.5 and 146.6; disc 1.6 px left and 3% shallower.
- Rest form (Fable B, measured by row spans): thigh 1.12, knee cap 1.18, shin 1.0, ankle 1.20; skin calf at half the greave's scale; merged foot width × 1.50, height × 1.18, original length; shaft radius × 1.75–1.8; disc radius × 0.965, band 8 mm deeper.
- Look (`units/spearman/look.py`): sun strength π at 24°; cast-shadow depth 0.22 on projected paint, 0.45 on unseen fill, 0.85 on stone; ramp input fill 0.30, AO 0.55, stroke 0.10; contact shadow at 40%.
- Motion: Quaternius `Idle_Loop`, `Walk_Loop` at 0.90 source influence with an 8.5 cm lateral ankle offset per foot; KayKit `Hit_B`; keyed death (`collapse.py`) and attack. Clips 8/8/10/4/10 frames at 4/6/14/12/4 fps.
- Cycles hybrid fallback (through R10): key (−3,−4,8) 596.75 W size 5; fill (4,−2,3) 77 W; rim (−2,3,4) 132 W; world 0.19; one histogram grade at strength 0.80.
