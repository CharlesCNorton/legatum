/** Measure evaluated vertices in the map camera plane, excluding the floor.
 * One fixed fit per clip; the camera never follows individual animation frames.
 */
export function cameraBasis(THREE, config) {
  const direction = new THREE.Vector3(...config.camera_direction_gltf).normalize()
    .applyAxisAngle(new THREE.Vector3(0, 1, 0), -config.display_yaw_degrees * Math.PI / 180);
  const right = new THREE.Vector3(0, 1, 0).cross(direction).normalize();
  const up = direction.clone().cross(right).normalize();
  return {direction, right, up};
}

export function measureClip(THREE, scene, mixer, action, basis) {
  mixer.stopAllAction();
  action.reset().setLoop(THREE.LoopOnce, 1); action.clampWhenFinished = true; action.play();
  const bounds = [Infinity, Infinity, -Infinity, -Infinity];
  let figureHeight = 0;
  const p = new THREE.Vector3();
  const samples = Math.round(action.getClip().duration * 30);
  for (let f = 0; f <= samples; f++) {
    action.time = action.getClip().duration * f / samples;
    mixer.update(0); scene.updateMatrixWorld(true);
    let low = Infinity, high = -Infinity;
    scene.traverse(o => {
      if (!o.isMesh) return;
      const spear = (o.userData.vertex_regions || []).filter(r => r.part === 'spear');
      for (let i = 0; i < o.geometry.attributes.position.count; i++) {
        o.getVertexPosition(i, p).applyMatrix4(o.matrixWorld);
        const x = p.dot(basis.right), y = p.dot(basis.up);
        bounds[0] = Math.min(bounds[0], x); bounds[1] = Math.min(bounds[1], y);
        bounds[2] = Math.max(bounds[2], x); bounds[3] = Math.max(bounds[3], y);
        if (!spear.some(r => i >= r.start && i < r.start + r.count)) {
          low = Math.min(low, y); high = Math.max(high, y);
        }
      }
    });
    figureHeight = Math.max(figureHeight, high - low);
  }
  return {bounds, figureHeight};
}

export function fitClip(THREE, measured, basis, config, aspect = 1) {
  const {bounds: b, figureHeight} = measured;
  const extent = Math.max(figureHeight / config.figure_frame_fraction,
    (b[2] - b[0]) / (config.extent_frame_fraction * aspect),
    (b[3] - b[1]) / config.extent_frame_fraction);
  const target = basis.right.clone().multiplyScalar((b[0] + b[2]) / 2)
    .addScaledVector(basis.up, (b[1] + b[3]) / 2);
  return {extent, target, figureFraction: figureHeight / extent,
    widthFraction: (b[2] - b[0]) / (extent * aspect), heightFraction: (b[3] - b[1]) / extent};
}
