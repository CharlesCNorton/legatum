# Landship round 1

Source and all editable masters: `~/LegatumRuns/anim-pilot/masters/landship/`.
Immediate review images and honest step log: `~/LegatumRuns/anim-pilot/review/3d-v2/landship-*`.

Full-depth model and mechanical object hierarchy; no subject card, relief plane,
image-space warp or silhouette mask. Frozen camera projection, generated hidden
fill, six real AO/curvature bakes and one rest-derived grade. A successful decode
or audit is not art approval. Native-size review still decides parity.

Host handoff: `ROUND=1 tools/art/anim3d/units/landship/gpu.sh` from repo root.
It requires the saved local masters and verifies Metal availability, renders every
stage, creates 512/256 sets, trimmed 160px atlas, review sheets/animations, validated
eight-second MP4, and saved-scene audit. No PASS file is created automatically.

Round-one CPU results (512px / 8 Cycles samples, denoised): 40 frames, WebP quality
90, **168682 bytes**, trimmed 1370x520 atlas with 160px logical frames. Exact alpha
reconstruction, source/grade hashes, transparent gutters, motion and identical last
two death frames passed. Saved-scene audit passed 128 shoes, six actual bake maps,
stationary base and minimum track height >=0.205 against a 0.20 stone top. FFprobe
passed eight-second H.264/yuv420p, 1600x348, 240 frames; decoded frame inspected.
Seven Python files parse; both shell entrypoints pass `bash -n`.

Visual verdict: reads as the same unit at 64px; close to the painting at 256px,
not indistinguishable. Cab roof, track contour and base rim differ in crossfade.
Projected tread brushwork needs loop scrutiny; the smoke is still a simple mesh
plume. Hidden surfaces are an approximation. GPU lighting/render quality is
unverified in this sandbox. **No PASS**; retain the static painting in the runtime.
