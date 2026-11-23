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
