# Jet fighter round 1 sources

- Original Legatum jet fighter painting, CC BY 4.0: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/jet-fighter-source.png . Downloaded 2026-11-23 to `$ANIM_ROOT/assets/jet-fighter/jet-fighter-source.png`. Original prompt is `app/src/assets/units/jet-fighter.art-pass-3.prompt.txt`. Frozen rest-camera projection is applied to finished closed geometry; source alpha never cuts the model silhouette.
- Hidden-surface painted silver fill: existing `assets/stealth-fighter/painted-fill.png`, neutralised from original bomber generated brushwork, project CC BY 4.0. Imagegen output `01a20674-cc7c-7391-9ed5-eaf3529562ff/exec-71c71165-4b96-4204-bead-5802066e70f1.png`; no public URL. Original prompt retained in `fill.prompt.txt`. Copied to this unit's external asset directory; no new image generation.
- Existing Blender 5.3.0: https://www.blender.org/ (GPL software); Pillow 13.0.0: https://pypi.org/project/pillow/13.0.0/ (MIT-CMU); FFmpeg: https://ffmpeg.org/ (installed encoder). No additional installation or paid service.
- Reused MIT jet-bomber pipeline helpers, read with `git show astra/unit-anim-3d-jet-bomber:tools/art/anim3d/units/jet-bomber/<file>`. Vehicles family chapter read from `astra/unit-anim-3d-vehicles`. New jet fighter model, rigid flight rig and clips are original MIT source; rendered artwork CC BY 4.0.

No humans, riders or animals appear, so CMU/Quaternius gait retargeting does not apply. Mechanical bank/flight, gun run, hit and crash curves are authored. The top/front move-cycle review replaces the feet check, with the same `jet-fighter-g-feet-check.png` filename for the driver. Input hashes are pinned in `inputs.json`. Masters and downloaded assets remain outside git.

## Driver round 2, 2026-11-23

Reuses the unchanged source painting and generated silver fill above; no new download or image service. The far wing receives a conventional span/chord unwrap of this aircraft's existing near-wing panel painting, mixed with the generated fill on unseen faces. Original registered closed intake shell, canopy/wing refinements, impact crease and delivery changes: MIT scripts / CC BY 4.0 rendered art. Source hashes remain in inputs.json; scene and bake hashes are resealed by the build. Incoming GPU evidence retained under masters/jet-fighter/driver-r1-gpu/.
