# Spartan hoplite sources

- Painting: https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/spartan-hoplite-source.png — project CC BY 4.0. Full original and aligned image in assets/spartan-hoplite; frozen camera UVs on solid geometry.
- MPFB 2.0.18: https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18 — GPL software, CC0 anatomy, rig, weights and MakeHuman system eyes. Existing isolated installation.
- Quaternius Universal Animation Library Standard, 2025-06-10: https://quaternius.com/packs/universalanimationlibrary.html — CC0-1.0. Idle_Loop, Walk_Loop, Hit_Chest, Death01. Existing immutable mirror https://raw.githubusercontent.com/J-Ponzo/gltf-universal-animation-library/e24c23cf2a1323488a3faa226ea7ea21f644b73e/glTF/AnimationLibrary_Godot_Standard.gltf and adjacent .bin. LICENSE retained externally. SHA256 pins in assets.lock.json and checked in the retarget helper.
- The unit-local MIT retarget helper was read and copied from astra/unit-anim-3d-trench-infantry. Blender world-space COPY_ROTATION constraints compensate reference poses and complete bone rolls. Locomotion leg axes calibrate once to the donor rest pose; no foot yaw/pitch overrides after retargeting. The original hoplite attack and equipment release remain authored.
- Existing CMU 77_02/02_01 BVHs are historical inputs only; new clips use Quaternius. CMU terms and 2010 Bruce Hahne conversion source remain in assets/SOURCES.md.
- Existing ambientCG Metal034, Fabric030 and Travertine001 (https://ambientcg.com/), Poly Haven brown_leather and fine_grained_wood (https://polyhaven.com/): CC0, pinned existing scan files and actual baked AO/curvature.
- Unseen linen fill: original mounted-family built-in imagegen artwork, 2026-11-22, CC BY 4.0, assets/horseman/fill-linen.png from painted-fills.png. No public URL. Original prompt: four-quadrant painted coat/linen/bronze/hair texture sheet for premium historical miniatures, subtle brushwork, no objects/text/insignia. No new generation or paid service.
- Blender 5.3.0 (GPL), Pillow 13.0.0 (MIT-CMU), FFmpeg: existing installations. Original geometry/material/animation/pipeline scripts MIT, rendered art CC BY 4.0. Masters and downloads remain outside git under ~/LegatumRuns/anim-pilot/.

Driver round 3 reuses unchanged generated Medjay skin (built-in ImageGen,
2026-11-22, `01a20671-5037-7490-a90a-decacb274446/exec-401b9b3e-9eef-48db-b965-0d53769ebddc.png`)
and Tagmatic Soldier crimson wool/leather
(`01a20671-5064-7c72-a6fe-cf93cc86ea3d/exec-487c13de-dea1-48e2-adb2-76092f8dbbcd.png`).
Original project CC BY 4.0; no public generation URLs. Copies under
`assets/spartan-hoplite/fill-{skin,cloth,leather}.png`, SHA256 in assets.lock.json.
Original prompts: painted warm skin/linen/hide/wood quadrants for a premium
miniature; crimson woven wool/bright worn steel/scuffed leather/worn brass
quadrants, respectively; no objects, text or insignia. These are physical
unseen-surface fills; visible pigment remains the original hoplite painting.
No new asset downloads or image-generation service calls this round.
