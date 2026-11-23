# Tagmatic soldier — round 1
- Read project art instructions, infantry playbook and standing feedback 1–22; read family projection/grade implementations with git show. No rules or UI changes.
- Loaded blender-modeling/materials/lighting/cameras/animation/rendering: fitted MPFB anatomy, bevels and thickness, material-specific roughness, warm key/cool rim, orthographic landmark calibration, authored skeletal clips, low-sample CPU previews before GPU handoff.
- Retrieved archived CC BY 4.0 source; aligned to the committed 256 token. Generated four painted unseen-surface fills with built-in ImageGen (cloth/steel/leather/gold), saved externally.
- Saved b-plain immediately, then c-textured-lit/c-details/f-restpose-compare. First comparison exposed floating unfinished toes and a low base; added full leather footwear and raised the disc to match the painting.
- Cycles baked six real 256 px AO/Pointiness maps for shield, helmet and lamellae. One rest-calibrated colour LUT is shared by all clips, avoiding frame-to-frame histogram pumping.
- Five authored MPFB clips saved, with true skeletal transforms and continuous released-equipment transforms. Cloth has modeled folds with bone attachment in round 1; it is not cloth simulation.
