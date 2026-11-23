## 2026-11-23: Hybrid painted fire and camera-aware ship clearance

- User review of rendered v8 rejected the faint grey brazier column and soft bright fire blob; the sparks were too small, and the CG galley crossed the large painted galley. Water glints, banners, oar foam and full-resolution output were accepted.
- V9 removes the complete Mantaflow/bake path. Procedural narrow pigment cards bypass the CG blur, with separately timed visible sparks; a distant painted beacon supplies smoke at haze depth. Blender render quality is unverified: the lead holds the lock and this editing session only prepares and compiles.
- Collision checks must project the whole animated ship against all painted craft with relief parallax on every frame. A path that clears at frame 1 can fail during the push. Preparation writes conservative Python bounds; Blender dry-run checks evaluated mesh bounds and compares the analytical projection to the actual camera before rendering.
- The new short offshore path preserves ship scale, and the waterline, foam and reflection share one submerged contact. `scene-report.json` labels Python-only preparation separately from a Blender build; neither is visual approval.
