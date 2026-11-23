# Barbarian pikeman — driver round 3 candidate

Run from the repository root. The infantry/two-handed-pike chapter in
`tools/art/anim3d/PLAYBOOK.md` documents rebuilding, external inputs and metadata.

The one-command host render is:

```sh
ROUND=3 tools/art/anim3d/units/barbarian-pikeman/gpu.sh
```

It requires the saved unit masters under `~/LegatumRuns/anim-pilot/masters/barbarian-pikeman/`
and the installed external Blender/Pillow environment. It uses Cycles Metal,
keeps 512/256 masters, publishes every review stage, front/top feet and the split/crossfade,
packs/validates the 160 px trimmed atlas and makes the eight-second round MP4.
No network, uploads, release or runtime changes occur.

The painting is still the quality target. A CPU preview or passing atlas validator
does not establish an art pass. Check face/beard, helmet angle, quilted-coat volume,
hand contact, ankle/boot silhouette and floor contact in death. Only write the
external PASS marker after reviewing the GPU rest pose and all five clips.
