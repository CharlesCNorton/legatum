Rendered b-plain: 256px CYCLES CPU, 8 samples.
Rendered c-textured-lit: 256px CYCLES CPU, 8 samples.
Rendered b-plain: 256px CYCLES CPU, 8 samples.
Rendered c-textured-lit: 256px CYCLES CPU, 8 samples.
Loaded six Blender skills: modeling (thick kit/organic subdivision), materials (projected brushwork and generated backfill), lighting (warm key/cool rim), cameras (orthographic registration), animation (CC0 source actions), rendering (CPU previews, GPU512 handoff).
Built plain model; observed low rider and narrow horse silhouette. Shifted rider and applied inverse-skin full-depth rest sculpture; no flattened or alpha-cut anatomy.
Rendered b-plain: 512px CYCLES CPU, 8 samples.
Rendered c-textured-lit: 512px CYCLES CPU, 8 samples.
Rendered four keyed attack rig poses.
Rendered idle: 8 frames, 512px, 8 samples, CPU.
Rendered move: 8 frames, 512px, 8 samples, CPU.
Rendered attack: 10 frames, 512px, 8 samples, CPU.
Rendered hit: 4 frames, 512px, 8 samples, CPU.
Rendered death: 10 frames, 512px, 8 samples, CPU.
Rendered top/front views for all eight move samples; native -Y travel axis, no post-retarget foot rotation.
Rendered b-plain: 512px CYCLES CPU, 8 samples.
Rendered c-textured-lit: 512px CYCLES CPU, 8 samples.
Rendered four keyed attack rig poses.
Move review rejected the large horse-leg inverse-skin fit: it stretched hocks in the native gallop. Preserved comparison and strip in masters/keshig/rejected-rest-fit; removed horse deformation and selected native gallop frame 12 for rest. Rider-only small registration remains.
Full CPU512/8-sample rerender underway; these are real 512 renders, not enlarged 256 previews. GPU64 remains required for final review.
Static gate run: hygiene and public-claims passed; repository art gate failed in render-sets.mjs/Chromium subprocess before producing a distinctness result. This is not an art pass.
Rendered idle: 8 frames, 512px, 8 samples, CPU.
Rendered move: 8 frames, 512px, 8 samples, CPU.
Rendered attack: 10 frames, 512px, 8 samples, CPU.
Rendered hit: 4 frames, 512px, 8 samples, CPU.
Rendered death: 10 frames, 512px, 8 samples, CPU.
Rendered top/front views for all eight move samples; native -Y travel axis, no post-retarget foot rotation.
Rendered b-plain: 512px CYCLES CPU, 8 samples.
Rendered c-textured-lit: 512px CYCLES CPU, 8 samples.
Rendered four keyed attack rig poses.
Rendered idle: 8 frames, 512px, 8 samples, CPU.
Rendered move: 8 frames, 512px, 8 samples, CPU.
Rendered attack: 10 frames, 512px, 8 samples, CPU.
Rendered hit: 4 frames, 512px, 8 samples, CPU.
Rendered death: 10 frames, 512px, 8 samples, CPU.
Rendered top/front views for all eight move samples; native -Y travel axis, no post-retarget foot rotation.
Packed and decoded 40 trimmed frames, quality 80, 186820 bytes; wrote keshig-round1.mp4. Warnings: []
Atlas validation caught left-edge clipping from duplicate authored tail. Removed extra tail, retained native weighted tail, corrected key light to camera upper-left, and rerendered every stage. Failed packing now preserves existing delivery.
Final CPU512/8-sample round: 40 frames, quality 80, 186820 bytes, exact reconstructed alpha and held death; geometry audit and 8s/240-frame H.264 yuv420p video checks passed. Rest silhouette IoU 0.5697; not painting parity at 256 or 64. No PASS.
Final source syntax/whitespace checks and 92 master dimension checks passed. Git add failed: lane-12/index.lock Operation not permitted; left all changes uncommitted for runner. GPU pass remains unrun in sandbox; no PASS marker.
