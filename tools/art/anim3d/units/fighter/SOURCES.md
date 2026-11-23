# Fighter sources and motion

- Original fighter painting: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/fighter-source.png — project CC BY 4.0. External `assets/fighter/painting-source.png`; registered `projection.png`; exact hashes in `assets.lock.json`.
- Generated unseen-surface olive brushwork: original OpenAI imagegen output `01a20674-cc7c-7391-9ed5-eaf3529562ff/exec-71c71165-4b96-4204-bead-5802066e70f1.png`, CC BY 4.0, reused from the bomber lane. No public URL. External `assets/fighter/painted-fill.png`; original prompt in the bomber lane's `fill.prompt.txt`. No new image service call this round.
- Blender 5.3.0 (`02f0899d78e3`), https://www.blender.org/ — GPL software. Pillow 13.0.0, https://pypi.org/project/pillow/13.0.0/ — MIT-CMU. Existing isolated installations.
- Full-depth aircraft, rigid propeller shaft, support and original mechanical flight keys: MIT project scripts; rendered artwork CC BY 4.0. No third-party model or motion asset.

The human/animal mocap standard does not apply to an unmanned miniature aircraft:
there are no human feet or quadruped limbs. Motion uses a rigid airframe, an
orthonormal propeller basis with shaft-local rotation, and a stationary display
base. The required `fighter-g-feet-check.png` contains actual top/front renders
of the eight-frame move cycle, explicitly labelled as a mechanical/no-feet check.

Driver round 2 adds original built-in ImageGen occlusion paint,
`01a20947-16e3-7b33-9a3c-7ef7536ee369/exec-48979cef-d5dc-4687-b975-2b4c4dc6267a.png`,
2026-11-23, project CC BY 4.0, no public URL. The edit target is the original
painting above; prompt in `occlusion-fill.prompt.txt`, external asset
`assets/fighter/occlusion-fill-source.png`, hash in `assets.lock.json`.
Only feathered patches behind the moving blades are used, on solid wing meshes.
