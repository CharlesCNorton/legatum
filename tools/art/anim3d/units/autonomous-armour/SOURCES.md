# Autonomous armour sources

- Painting: [Legatum original master](https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/autonomous-armour-source.png), project CC BY 4.0. External `assets/autonomous-armour/painting-source.png`; hash in `masters/autonomous-armour/inputs.json`. The same painting supplies frozen-camera colour on the complete articulated meshes.
- Unseen painted steel: original built-in imagegen output, 2026-11-22, `01a20674-c712-70c3-8be2-9faa56cc6ca7/exec-53462d10-62c0-477b-9c78-6032916d5343`, project CC BY 4.0, no public source URL. External `assets/autonomous-armour/painted-fill.png`; exact prompt in `fill.prompt.txt`.
- Geometry and mechanical animation: original unit scripts, MIT; rendered artwork CC BY 4.0. No downloaded vehicle, human mocap, commercial motion service, or additional round-two asset. Wheel rotation and track travel derive from a shared physical distance and repeating mechanical geometry.
- Existing Blender 5.3.0, GPL software: https://www.blender.org/. Pillow 13.0.0, MIT-CMU: https://pypi.org/project/pillow/13.0.0/. External asset inventory is `~/LegatumRuns/anim-pilot/assets/SOURCES.md`.

Driver round 2 reuses these exact assets. Source cream grain is now mapped onto the real beveled disc with a mask excluding the vehicle and dark contact shadows. No new generated or downloaded assets.

## Driver round 3, 2026-11-23

- Wheel pigment: original built-in ImageGen, project CC BY 4.0, no public URL. Generation `01a20a96-9b27-74c3-9eea-54d74014ead9/exec-f3a9c7d4-77fd-4afc-a71a-8a38739d859e.png`; external `assets/autonomous-armour/wheel-fill-source.png`. Exact prompt in `wheel-fill.prompt.txt`; SHA256 pins in `assets.lock.json`. A twelve-angle mean removes directional baked lighting and makes the derived `wheel-pigment.png` periodic with twelve studs; the map colors solid tires/dishes, never image geometry.
- Reuses the recorded original painting and generated olive fill. Raised end sprockets, a convex closed track belt, thick separated tread pads and live cavity shading are original MIT scripts / CC BY 4.0 rendered art. No third-party download or motion; this is a mechanical rig. Previous GPU evidence preserved in `masters/autonomous-armour/driver-round2-gpu/`.
