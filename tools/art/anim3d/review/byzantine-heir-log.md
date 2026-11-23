# Byzantine heir round 1
- Read project art instructions, infantry PLAYBOOK, newer mounted projection approach and feedback 12–22; no mechanic or UI changes.
- Loaded all six Blender skills: MPFB anatomy and beveled kit; PBR fabrics/metal; warm product lights; calibrated orthographic camera; authored clips; CPU preview before GPU final.
- Inspected painting and source: standing crowned heir with purple embroidered mantle, lamellar armour, boots, banner and warm cream base.
- Downloaded licensed source and generated four unseen-surface texture fills with built-in imagegen; source projection remains the primary visible texture.
- First plain/textured comparisons published immediately; found inverted front garment normals, floating hair and weak boot contact. Retained originals under masters and corrected before animation.
- Completed real 256 px AO/Pointiness bakes for cuirass, skirt, shoulder mantle and MPFB anatomy; maps are retained and packed into the master.
- Saved five editable clips and rendered all 40 initial CPU frames; published strips/WebPs immediately. First pack rejected death frame 5 at the left border (no atlas shipped from that pass).
- Increased attack articulation, moved the collapse inward, connected boot ankles and added a sculpted hair cap. Rebuilding all outputs at 512 px / 8 CPU samples; these are drafts for the 48-sample Metal GPU pass.
- Rebuild exposed a Blender UV-layer handle invalidated by edit-mode unwrap; bake stopped before saving. Fixed by retaining the UV name as a string, added nonzero Python exit codes and a bake-required guard so incomplete rebuilds cannot render/pack as valid.

# Resumed round 2 — 2026-11-23
- Opened latest rest comparison and move strip before edits. At 256 px the face/circlet is distorted, cloak/train is too narrow and angular, toes are pale rounded blobs and stone looks smooth/molded; projection and geometry do not yet register. At 64 px the crowned purple banner-bearer reads, but the narrow stance/train and bright toes differ. Not PASS.
- Read all common feedback (1–22); no unit-specific feedback file currently exists. Loaded all six Blender skills; read current and advanced spearman/siege playbooks. Applying finished-surface frozen projection, camera-only pigment, boot/source separation and product lighting while retaining existing generated fills and real bakes.
- Finished-surface projection preview removes doubled facial lighting; boot anatomy fitted inside leather, crown/hair shifted to source landmarks, cloth train extended, round base moved away from camera while retaining its contact top. Camera-only pigment preserves painted illumination without acting as a lamp. Existing four generated fills and baked AO/curvature retained.
- First Standard preview made stone too dark; added camera-only cream pigment blended with physical contact shadows and fine grain. Boot source mask now rejects the cream stone below the painted sole.
- GPU entry point now retains its own transcript and failed-stage receipt, checks Metal explicitly, rebuilds from the baked checkpoint and verifies GPU512/48 + gallery256 provenance. Terminal death reuses a PNG only after evaluated geometry equality.
