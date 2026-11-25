# Spearman-q, round 2

Run `bash tools/art/anim3d/units/spearman-q/run.sh` from the repository root.
It preserves the original Quaternius mesh, weights and rest rig, samples the
CC0 library clips, adds equipment and floor corrections, and renders the
painted CPU diagnostic. It writes no shipped game assets.

Round 2 uses one shared guard and identical rigid prop attachments in all
clips. The attack retains Punch_Cross's body motion with a 39 cm Cartesian
right-hand thrust, a forward shield guard, and blended entry/recovery. The
hit returns to guard. Death releases rigid socket children after recoil,
lands them beside the body, centres the fall and holds three final samples.
A larger stationary stone supports the extended library death; this is a
visible composition tradeoff, not a painting-match improvement.

`costume.py` fits the existing Spearman armour and sunburst shield to the
new rig, retaining frozen projection UVs and per-part pigment. Skirt and crest
receive collision-only floor corrections during death; the armour and props
remain rigid. `look.py`
ports the kit's emission/palette approach. Its CPU sun-cosine substitute
has no cast shadows and is explicitly a diagnostic. The original body is
unchanged; this pass has a short red collar, not a simulated full cloak.
The costume master and 40 look inputs are frozen outside git and checked
against `input-sources.json`; `inputs.py` refuses changed source bytes.

Outputs live under `~/LegatumRuns/anim-pilot/lanes/spearman-q-r2/`:

- `masters/`: editable scenes, before the render-time look.
- `frames/`: all 70 game frames and source/timing receipts.
- `atlas/`: validated 160 px preview atlas, at most 350,000 bytes.
- `verification.json`: unchanged source geometry/rest rig, reconstructed
  donor-plus-layer poses, rigidity, floor/trajectory and motion measurements.
- `collision-audit.json`: sampled body/prop intersections, with the hand grip
  excluded while held; this is not continuous collision detection.

Review files are `review/3d-v2/spearman-q-r2-<clip>-160.mp4` and
`spearman-q-r2-attack-fullrate.png`. Videos are atomically replaced after
encoding, H.264/yuv420p, exactly three repeats at the recorded game fps.

The lead runs `bash tools/art/anim3d/units/spearman-q/gpu.sh` outside the
sandbox. It verifies inputs and scenes first, then renders Eevee at 512 px
through the same `look.py` path, reduces in display space with premultiplied
alpha, and packs/decodes/validates the atlas. GPU outputs use `gpu/` and
`spearman-q-r2-gpu-*` review names, preserving CPU evidence. A prepared
handoff does not establish that the GPU pass or playback review passed.

Provenance is in [SOURCES.md](SOURCES.md). The shared review note records
remaining visible defects and the stage actually reached.
