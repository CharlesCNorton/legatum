# Barbarian spearman — round 1 review

This is a true 3D, editable art candidate. It is not approved for replacing the
painting. All review images and animation WebPs are outside git in
`~/LegatumRuns/anim-pilot/review/3d-v2/barbarian-spearman-*`.

The round includes an MPFB body and 53-bone skeleton, original linen/fur/leather
kit, a convex rawhide shield with red painting projection, low ash spear and iron
head, eight actual AO/curvature bake maps, and five authored clips. Geometry is
fully volumetric; plain front/three-quarter/side views document it. No flat image
plane or runtime image deformation substitutes for the model.

The original 256 px painting is noticeably richer. The 3D head and fur mantle
remain narrower and more upright; hair/face landmarks are approximate, the fur
locks are too pointed, and the tunic lacks the painting's natural drape. The
camera projection transfers brushwork but also reveals registration errors.
At 64 px the oval red-striped shield, low spear and brown/cream kit identify the
same unit, but its body silhouette remains too narrow and less forceful.

Motion is authored on the skeleton. The weapon and shield follow hand/forearm
controls, then release independently in death. The base is stationary. The final
death sample is repeated. The mantle is thick folded geometry attached to the
spine, not simulated cloth; there is no full collision solver. Walk contact,
weapon clearance and released equipment need the lead's motion review, especially
after the GPU pass. Technical validation is not an art verdict.

The no-argument `gpu.sh` rerenders every stage using Cycles Metal GPU at 512 px,
creates the 512/256 masters, common grade, all review sheets, animated WebPs,
rest-pose split/crossfade, trimmed 160 px atlas, validation and saved-scene audit.
CPU images are preview evidence only. No GPU execution is claimed by this lane.

The final detail crop makes two remaining projection defects explicit: the mask
for the source spear leaves a visible lighter strip, and the source shield-boss
highlight is not perfectly registered with the modeled boss. The rest crossfade
also shows the base/feet alignment difference. These are round-two priorities,
along with a broader, more braced pose and a sculpted fur/face pass. The round-one
candidate deliberately remains unapproved rather than hiding these defects.

Final CPU technical results: 40 frames passed at 512 px, with all 256 px masters
retained. Trimmed 160 px atlas is **185,064 bytes at WebP quality 75**. Validation
passed all counts, alpha bounds, exact alpha reconstruction from trim offsets,
pixel motion and repeated terminal death. Scene audit passed source hashes,
19,158-vertex MPFB anatomy, 53 bones, stationary base, safe scales, evaluated death
ground clearance and hand-to-shaft distance (maximum 0.0252 m before release).
Thirteen Python scripts parse, both shell entry points pass `bash -n`, and all
four external PNG hashes match. CPU renders use Cycles, 8 samples, denoising;
the required GPU script uses Cycles Metal, 64 samples. GPU and browser art review
remain lead-side checks.

The death is technically clear of the ground and canvas, but its final body pose
still reads too stiff and high on the supporting arm. Refine the roll and contact
pose next round. Do not interpret the geometry audit as a physical-motion pass.

Implementation findings: reacquire UV-layer identifiers after Blender Edit Mode
(the prior RNA handle can become invalid); enable Cycles persistent render data
to avoid recompiling the same detailed scene for every frame; frozen painting
UVs need explicit masks for foreground equipment that will move independently.

Git handoff: the sandbox denied both `index.lock` (add/commit) and `ORIG_HEAD.lock`
(merge). All requested files are left uncommitted for the runner. `origin/master`
advanced by two CI/browser-test commits; their actual incoming paths do not
overlap this unit's edits. Commit with:

```text
Add round-one 3D barbarian spearman animation candidate

Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>
```

Then merge the current local `origin/master` and run the landing gates. The
HEAD-only hygiene/public-claims check passed, but did not include uncommitted
files and is not a check of this candidate. No push or PR was attempted.
