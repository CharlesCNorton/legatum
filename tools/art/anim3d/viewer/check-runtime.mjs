#!/usr/bin/env node
/** CPU-only GLTFLoader / AnimationMixer smoke test. No Chromium or WebGL. */
import {readFile} from 'node:fs/promises';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const here=dirname(fileURLToPath(import.meta.url));
const modules=process.env.VIEWER_NODE_MODULES;
if(!modules)throw new Error('Set VIEWER_NODE_MODULES to a directory containing three@0.170.0');
const THREE=await import(pathToFileURL(join(modules,'three/build/three.module.js')).href);
const {GLTFLoader}=await import(pathToFileURL(join(modules,'three/examples/jsm/loaders/GLTFLoader.js')).href);
globalThis.self=globalThis;
globalThis.ProgressEvent=class {constructor(type,data){this.type=type;Object.assign(this,data);}};
// Texture dimensions only: no pixel rendering is claimed by this CPU test.
globalThis.createImageBitmap=async blob=>{const b=Buffer.from(await blob.arrayBuffer());return {width:b.readUInt32BE(16),height:b.readUInt32BE(20),close(){}};};
const path=process.argv[2]||resolve(here,'../units/spearman-0ad/spearman.glb');
const bytes=await readFile(path);
const gltf=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
assert.deepEqual(gltf.animations.map(a=>a.name).sort(),['attack','death','hit','idle','walk']);
const mixer=new THREE.AnimationMixer(gltf.scene);
const report={three:THREE.REVISION,clips:{},teamMaterials:0};
const mats=new Set();gltf.scene.traverse(o=>{for(const m of (Array.isArray(o.material)?o.material:o.material?[o.material]:[]))if(m.name==='team')mats.add(m);});
assert(mats.size>0);report.teamMaterials=mats.size;
for(const m of mats){assert.equal(m.map.image.width,1024);assert.equal(m.map.image.height,1024);m.color.set('#306bda');}
for(const clip of gltf.animations){
  mixer.stopAllAction();const action=mixer.clipAction(clip);action.setLoop(THREE.LoopOnce,1);action.clampWhenFinished=true;action.reset().play();
  const bound=new THREE.Box3();let first,last,poseDelta=0;
  for(let i=0;i<=Math.round(clip.duration*30);i++){
    action.time=i/30;mixer.update(0);gltf.scene.updateMatrixWorld(true);
    gltf.scene.traverse(o=>{if(o.isSkinnedMesh)o.computeBoundingBox();});
    bound.union(new THREE.Box3().setFromObject(gltf.scene,true));
    const bone=gltf.scene.getObjectByName(clip.name==='walk'?'foot_L':'chest');
    const pos=bone.getWorldPosition(new THREE.Vector3());
    if(!first)first=pos.clone();poseDelta=Math.max(poseDelta,first.distanceTo(pos));last=pos;
    for(const [prop,parent] of [['spear','weapon_R'],['aspis','shield_arm'],['helmet','head']]){
      assert.equal(gltf.scene.getObjectByName(prop).parent.name,parent);
    }
  }
  assert(poseDelta>.0001,`${clip.name} must actually animate`);
  if(['idle','walk'].includes(clip.name))assert(first.distanceTo(last)<.0001,`${clip.name} seam`);
  report.clips[clip.name]={duration:clip.duration,bounds:[bound.min.toArray(),bound.max.toArray()],probeMotionMetres:poseDelta};
}
console.log(JSON.stringify(report,null,2));
