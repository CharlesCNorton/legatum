# Barbarian spearman — round 2

This remains an unapproved 3D art candidate. No PASS marker is warranted.
At 256px it is markedly closer to the painting: broader shoulders/stance,
better feet/base registration, painted linen and face, a registered iron boss,
and less double shading. It remains distinguishable: shoulder/fur silhouette,
cloth drape, hair volume and physical stone shading are still simpler. At 64px
the shield, low spear and costume identify the same unit; the silhouette is
closer but not identical. Native-256 alpha overlap improved from .761907 to
.837361, which measures registration, not painting-level craft.

The editable MPFB anatomy retains 19,158 vertices, all original skin weights and
53 bones. `refine.py` starts from the preserved plain model and writes a separate
registered copy. Macro shape keys are frozen before inverse-skin fitting; full
mesh depth remains. Rigid bevel/thickness modifiers are applied before frozen
camera UVs. Finished-scene ray tests reject hidden surfaces, so the source shield
does not paint the rear cape. Camera-only painted illumination retains the
source's brushwork; generated linen/hair fill, physical shaders, actual AO and
curvature maps remain on unseen surfaces. One automatic rest grade applies to
all frames. Its raw-input handling is idempotent.

All five clips retain 8/8/10/4/10 frames. Move now solves the finished shoe soles
for planted contact and explicit swing lift. Attack reaches visibly, hit recoils,
and death tucks the elbows after weapon release. The last death source frame is
copied and its packed rectangle reused for an identical decoded hold. Cloth is
still a thick rigid shell attached to the spine, not simulated cloth. Death is
less propped up but remains stiff; neither the audit nor atlas checks establish
clean animation or art acceptance.

The executable, no-argument host handoff is:

```sh
ROUND=2 tools/art/anim3d/units/barbarian-spearman/gpu.sh
```

It preflights GPU availability, rebuilds registration/paint/bakes/clips, renders
all stages at Cycles GPU512/64, exports native 512/256 masters, fits/applies the
rest grade, publishes all review sheets/WebPs including the rest comparison,
packs and validates the compact trimmed atlas, audits saved scenes, and encodes
the decoded atlas into `barbarian-spearman-round${ROUND}.mp4`. The movie shows
all five clips at 2x on cream and is verified with ffprobe. A retained transcript
and EXIT status record identify failures. Missing inputs fail explicitly; CPU
previews cannot pass the GPU provenance gate. It never creates a PASS marker.

Round-one CPU512 evidence is preserved in external `round1-cpu/`. This round's
local reviews are CPU256/8 previews; they are not upscaled into fake 512 masters.
Fresh GPU512 rendering and the lead's visual/browser art review remain required.
