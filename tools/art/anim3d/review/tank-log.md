# Tank / Vehicles work log
- Read shared pipeline, project art direction, source manifest and feedback. Tank WWII selected; main-battle-tank is later; landship is turretless and does not match the requested clips.
- Inspected painting at 256 and panel size. No insignia in painting. Original 3D modelling: rounded cast turret, short barrel, sloped hull, six road wheels / three VVSS bogies per side, individual track links, deck stowage.
- Retrieved tank source into external masters/tank. All Blender runs use shared blender-slot, three threads, one lane job at a time.
- Emitted tank-b-plain.png from actual b renders; visual review pending.
- First plain sheet emitted immediately. Self-review: too-high camera, downward barrel, blotchy paint, missing rounded transmission cover. Matching pass lowers camera, yaws turret toward the painted gun angle, adds transmission casting, reduces pigment noise contrast and adds warm front bounce.
- Fixed Blender/OpenVDB crash from almost-zero smoke object scales: inactive effects now use keyed render visibility and normal scale. Initial render was launched before build finished and failed cleanly; all later heavy steps wait for previous completion.
- First actual 512px AO/curvature bake succeeded on hull, turret and lower hull; rebuilding geometry invalidates it, so all six maps will be rebaked.
- Read incoming tank-FEEDBACK: machine-wide single Blender gate now applies; crash dialogs reached desktop. Removed even temporary near-zero effect scale assignments. Inactive smoke uses normal-size geometry and keyed hide_render only; every call is background via blender-slot.
