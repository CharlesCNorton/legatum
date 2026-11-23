# Stealth fighter sources

- Original project painting, CC BY 4.0, archived 1280px alpha master: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/stealth-fighter-source.png . Downloaded to `assets/stealth-fighter/stealth-fighter-source.png`. Source and derived texture hashes are in `inputs.json`. Registered against the committed 256px token, then projected onto finished full-depth geometry.
- Hidden-surface painted metal: reuses the bomber lane's original generated fill, project CC BY 4.0. Built-in imagegen output `01a20674-cc7c-7391-9ed5-eaf3529562ff/exec-71c71165-4b96-4204-bead-5802066e70f1.png`, no public URL. Existing `assets/bomber/painted-fill.png` is converted from olive to charcoal grey; prompt retained in `fill.prompt.txt`. No new image-service call.
- Original aircraft, curved stone support, mechanical pivots, missile and animation keys: MIT scripts / CC BY 4.0 rendered art. This rigid aircraft has no human/animal gait; CMU/Quaternius retargeting and feet are not applicable. Actual top/front move renders document its flight axis and control movement.
- Projection, bake, review/packing and movie helpers adapted from the MIT bomber family branch using `git show astra/unit-anim-3d-bomber:<path>`. Vehicles chapter read from `astra/unit-anim-3d-vehicles`.
- Existing Blender 5.3.0 (`02f0899d78e3`, GPL software), Pillow 13.0.0 (MIT-CMU) and FFmpeg. No third-party model, paid asset, account, upload or motion download.

All assets, image derivatives, 512/256 masters and editable blends remain under `~/LegatumRuns/anim-pilot/`, outside git.

## Driver round 2, 2026-11-23

Reuses the stealth-bomber lane's original generated clean stone disc, built-in
ImageGen `01a20a1f-8c22-7cd1-a144-066c5b87d915/exec-9a0bb113-82fc-401f-b2f7-483d6cd160bd.png`,
project CC BY 4.0, no public URL. Copied unchanged to
`assets/stealth-fighter/stone-fill-source.png`; SHA256 pinned in `inputs.json`.
Original prompt retained in `stone-fill.prompt.txt`. The visible alpha footprint
is registered to this unit's disc; its own original lower rim is retained.
This is colour on the closed cylinder with live AO, not a billboard or shadow
painted permanently under the support. Existing aircraft/generated metal inputs
are unchanged. No new service, download or motion asset.
