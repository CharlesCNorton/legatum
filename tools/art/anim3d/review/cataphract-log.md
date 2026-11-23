Round 1: read project art skill, mounted playbook, all six Blender skills and standing feedback 1–22; no unit-specific feedback file yet.
Registered original cataphract master to committed 256px token; pinned source hashes; reused licensed Quaternius CC0 horse and MPFB CC0 rider.
Created unit-local GPU handoff entry point; geometry build started through plain blender gate, CPU only.
Rendered b-plain: 256px CYCLES CPU, 8 samples.
Rendered c-textured-lit: 256px CYCLES CPU, 8 samples.
Rendered b-plain: 256px CYCLES CPU, 8 samples.
Rendered c-textured-lit: 256px CYCLES CPU, 8 samples.
Rendered four keyed attack rig poses.
Rendered idle: 8 frames, 256px, 8 samples, CPU.
Rendered move: 8 frames, 256px, 8 samples, CPU.
Rendered attack: 10 frames, 256px, 8 samples, CPU.
Rendered hit: 4 frames, 256px, 8 samples, CPU.
Rendered death: 10 frames, 256px, 8 samples, CPU.
First plain render exposed low horse head/rider, upright lance and broad base; corrected actual mesh registration, raised rider, angled/shortened lance and reduced base footprint before frozen projection.
Applied projected original painting with normal-incidence blend into generated hidden-surface fills; retained full volumetric mesh depth and alpha-independent geometry.
Baked actual 256px helmet AO and Pointiness in Cycles, wired cavity darkening and edge roughness; other surfaces retain shader AO and procedural grain (not full-body baked coverage).
Built 8/8/10/4/10 idle/walk/attack/hit/death clip masters with source horse actions, authored rider motion, released lance and terminal death hold.
Render wrapper was edited while an earlier invocation was running, causing a shell read-position syntax failure after animation; current wrapper passed bash -n and the serial render batch was restarted.
Rest comparison: rider height improved but chest/forearms remain patchy, horse neck too narrow, rein hand high, base still darker than painting; candidate requires another round, no PASS marker.
Packed and decoded 40 trimmed frames, quality 80, 187204 bytes; wrote cataphract-round1.mp4. Warnings: []
Round 2 opening critique: supplied rest comparison and move strip are CPU256 evidence, not a verified GPU pass. At 256px rider chest/arms are patchy and pale, rein hand is high and detached-looking, neck/head silhouette narrow and too high, white pasterns unlike painting, base grey with rounded thin rim. At64 identity reads as armored cavalry but posture and bright horse markings differ; no PASS. Preserved supplied review/master checkpoints in masters/cataphract/round1-supplied.
Loaded all six Blender skills: modeling (finished solids), materials (camera-only painted illumination), cameras (landmark registration), lighting (product softboxes/cream calibration), animation (guard continuity), rendering (CPU previews and GPU provenance). Read all standing feedback and latest spearman/field-cannon playbooks through round8.
Rendered c-textured-lit: 256px CYCLES CPU, 8 samples.
Rendered c-textured-lit: 256px CYCLES CPU, 8 samples.
Rendered b-plain: 256px CYCLES CPU, 8 samples.
Rendered c-textured-lit: 256px CYCLES CPU, 8 samples.
Rendered four keyed attack rig poses.
Rendered idle: 8 frames, 256px, 8 samples, CPU.
Rendered move: 8 frames, 256px, 8 samples, CPU.
Rendered attack: 10 frames, 256px, 8 samples, CPU.
Rendered hit: 4 frames, 256px, 8 samples, CPU.
Rendered death: 10 frames, 256px, 8 samples, CPU.
Round2 changes: froze active MPFB macro mix and finished solidify/bevel/subdivision before inverse-skinned fitting and projection; added ray visibility and base-pigment exclusion, lowered rein palm, broadened shoulder/neck, removed inherited ivory markings, camera-only painted illumination and calibrated cream stone under product lights. Reused recorded generated unseen fills, thick straps/folded cloak and volumetric mane/tail. Rebuilt actual helmet AO/Pointiness.
Packed and decoded 40 trimmed frames, quality 85, 188488 bytes; wrote cataphract-round2.mp4. Warnings: []
