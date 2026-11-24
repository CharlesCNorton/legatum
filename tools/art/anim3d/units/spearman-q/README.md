# Spearman-q motion experiment

Run from the repository root:

```sh
bash tools/art/anim3d/units/spearman-q/run.sh
```

Downloads are pinned in `downloads.json`; provenance and clip choices are in
[SOURCES.md](SOURCES.md). All Blender calls use the PATH gate. Source assets,
editable blends and PNG sequences live outside git under
`~/LegatumRuns/anim-pilot/`; review videos and strips are in `review/3d-v2/`.
The pipeline does not modify the shipped game atlas or the existing Spearman.

`build.py` preserves the Quaternius base mesh, original weights and rest rig,
transfers matching library bone rotations, and adds two non-deforming prop
bones. Props have no skinning, deformation or per-frame correction. Their
static socket fit differs between clips, so clip transitions still need work.
`verify.py` checks the saved body against the original and all sampled source
rotations, plus prop rigidity. `package.py` composites cream backgrounds,
encodes exactly three repeats, and checks decoded video metadata with ffprobe.

Attack is a Punch_Cross surrogate, not a native spear stab. The free sword
motions inspected were wide cuts. Attack remains unconvincing; death has
prop/ground intersections. This is an honest motion review, not art approval.
See `~/LegatumRuns/anim-pilot/review/3d-v2/spearman-q-note.md` for the full verdict.
