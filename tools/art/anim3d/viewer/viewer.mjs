import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {applyTeamMask} from './team-mask.mjs';
import {cameraBasis, measureClip, fitClip} from './framing.mjs';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

const query = new URLSearchParams(location.search);
const config = await (await fetch('../units/spearman-0ad/review.json')).json();
const basis = cameraBasis(THREE, config);
const measured = {};
let activeClip;
const recording = query.has('record');
if (recording) document.body.classList.add('record');
const renderer = new THREE.WebGLRenderer({antialias: true, preserveDrawingBuffer: recording});
renderer.setPixelRatio(recording ? 1 : Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color('#f8f4e8');
const camera = new THREE.OrthographicCamera(-2, 2, 2, -2, .01, 100);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = false;
const target = new THREE.Vector3(0, 1, 0);
let extent = 3.6;
function resize() {
  const aspect = innerWidth / innerHeight;
  if (measured[activeClip]) {
    const fit = fitClip(THREE, measured[activeClip], basis, config, aspect);
    extent = fit.extent; target.copy(fit.target);
  }
  camera.left = -extent * aspect / 2; camera.right = extent * aspect / 2;
  camera.top = extent / 2; camera.bottom = -extent / 2;
  camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight);
}
function mapCamera() {
  // Inverse camera orbit implements the documented 30-degree display yaw.
  resize();
  camera.position.copy(target).addScaledVector(basis.direction, 8);
  controls.target.copy(target); controls.update();
}
mapCamera();
scene.add(new THREE.HemisphereLight(0xfff7e6, 0x716148, 2));
const light = new THREE.DirectionalLight(0xfff5dd, 2.2);
light.position.set(-3, 7, 4); light.castShadow = true;
light.shadow.mapSize.set(1024, 1024);
Object.assign(light.shadow.camera, {left:-4,right:4,top:4,bottom:-4,near:.1,far:20});
light.shadow.bias = -.0002; scene.add(light);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(200,200), new THREE.MeshStandardMaterial({color:'#f8f4e8', roughness:1}));
floor.rotation.x = -Math.PI/2; floor.position.y=-.004; floor.receiveShadow=true; scene.add(floor);
const status = document.querySelector('#status');
let mixer, actions, current, paused=false;
const clipSelect=document.querySelector('#clip');
function select(name) {
  if (!actions?.[name]) throw new Error(`Unknown clip ${name}`);
  mixer.stopAllAction(); current=actions[name]; current.reset();
  current.setLoop(THREE.LoopRepeat, Infinity); current.play(); mixer.update(0);
  clipSelect.value=name; activeClip=name;
  if(measured[name])mapCamera();
}
try {
  const gltf=await new GLTFLoader().loadAsync(query.get('model') || '../units/spearman-0ad/spearman.glb');
  scene.add(gltf.scene); mixer=new THREE.AnimationMixer(gltf.scene);
  actions=Object.fromEntries(gltf.animations.map(c=>[c.name,mixer.clipAction(c)]));
  const teamMaterials=new Set();
  gltf.scene.traverse(o=>{
    if (!o.isMesh) return;
    o.castShadow=true; o.receiveShadow=false; o.frustumCulled=false;
    for(const m of (Array.isArray(o.material)?o.material:[o.material])) if(m.userData.team?.attribute==='COLOR_0') {applyTeamMask(m, THREE);teamMaterials.add(m);}
  });
  document.querySelector('#team').addEventListener('input', e=>teamMaterials.forEach(m=>m.userData.teamUniform.value.set(e.target.value)));
  // Project actual skinned vertices, never a world AABB or the review floor.
  for(const clip of gltf.animations) {
    measured[clip.name]=measureClip(THREE,gltf.scene,mixer,actions[clip.name],basis);
  }
  select(query.get('clip')||'idle');
  status.textContent='0 A.D. art by Wildfire Games, CC BY-SA 3.0; adapted for Legatum';
  // Deterministic screenshot API: exact frames, no wall-clock capture jitter.
  window.review={
    ready:true,
    clips:Object.fromEntries(gltf.animations.map(c=>[c.name,c.duration])),
    sample(name,time) {
      if(clipSelect.value!==name)select(name);
      current.time=time; mixer.update(0); controls.update(); renderer.render(scene,camera);
    },
    framing:()=>Object.fromEntries(Object.entries(measured).map(([name,m])=>{
      const fit=fitClip(THREE,m,basis,config,innerWidth/innerHeight);
      return [name,{...fit,target:fit.target.toArray(),displayYawDegrees:config.display_yaw_degrees}];
    })),
    stats:()=>renderer.info.render,
  };
} catch(error) {
  status.textContent=error.message;
  window.review={ready:false,error:String(error)};
  throw error;
}
clipSelect.onchange=()=>select(clipSelect.value);
document.querySelector('#pause').onclick=e=>{paused=!paused;e.target.textContent=paused?'Play':'Pause';};
document.querySelector('#orbit').onclick=()=>{controls.autoRotate=!controls.autoRotate;};
document.querySelector('#map').onclick=()=>{controls.autoRotate=false;mapCamera();};
addEventListener('resize',mapCamera);
const clock=new THREE.Clock();
function draw(){requestAnimationFrame(draw);const delta=Math.min(clock.getDelta(),.1);if(!recording){if(mixer&&!paused)mixer.update(delta);controls.update();renderer.render(scene,camera);}}
draw();
