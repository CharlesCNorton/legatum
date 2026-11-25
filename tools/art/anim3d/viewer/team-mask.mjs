/** COLOR_0 is a scalar mask, not an RGB pigment multiplier. Shared with tests. */
export function applyTeamMask(material, THREE) {
  const teamColor = {value: new THREE.Color(material.userData.team.default_srgb)};
  material.userData.teamUniform = teamColor;
  material.vertexColors = true;
  material.onBeforeCompile = shader => {
    shader.uniforms.teamColor = teamColor;
    shader.fragmentShader = 'uniform vec3 teamColor;\n' + shader.fragmentShader.replace(
      '#include <color_fragment>',
      '#if defined(USE_COLOR) || defined(USE_COLOR_ALPHA)\n' +
      'diffuseColor.rgb *= mix(vec3(1.0), teamColor, vColor.r);\n#endif',
    );
  };
  material.customProgramCacheKey = () => 'legatum-team-mask-r1';
  material.needsUpdate = true;
}
