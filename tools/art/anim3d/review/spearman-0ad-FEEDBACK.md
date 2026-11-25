- (3D-map contract addition, 2026-11-25 00:27Z; applies to the painted drop, this round if possible) The map thread loaded spearman.glb cleanly and has it live as three-figure squads. For the painted GLB:
  1. Merge everything into ONE skinned mesh with ONE material (one draw call). Props (spear, aspis, helmet) stay rigid by skinning each prop's vertices 100% to its single socket bone (weapon_R, shield_arm, helmet), not as separate meshes.
  2. Team areas (crest, shield rim, cloak trim) go in a vertex-colour mask (COLOR_0, red channel = team weight) instead of separate meshes or materials.
  3. Extend tools/art/anim3d/validate_glb.py to check: 1 mesh, 1 material, 1 draw call; each prop's vertices weighted to a single bone; the team mask (COLOR_0) is present.
  4. Keep the same file path and name (tools/art/anim3d/units/spearman-0ad/spearman.glb) so it drops in.
