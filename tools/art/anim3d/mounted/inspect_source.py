"""Inspect the licensed horse before fitting tack or transferring motion."""
import bpy,os,json
from pathlib import Path
r=Path(os.environ['ANIM_ROOT']);bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(r/'assets/horseman/Horse.glb'))
report={'objects':[], 'actions':[]}
for o in bpy.context.scene.objects:
 d={'name':o.name,'type':o.type,'location':list(o.location),'scale':list(o.scale),'dimensions':list(o.dimensions),'rotation':list(o.rotation_euler)}
 if o.type=='ARMATURE':
  d['bones']={b.name: {'head':list(b.head_local),'tail':list(b.tail_local)} for b in o.data.bones}
 if o.type=='MESH':d['bounds']=[[min(v.co[i] for v in o.data.vertices),max(v.co[i] for v in o.data.vertices)] for i in range(3)];d['vertices']=len(o.data.vertices)
 report['objects'].append(d)
for a in bpy.data.actions:report['actions'].append({'name':a.name,'range':list(a.frame_range),'slots':[s.identifier for s in a.slots]})
(r/'masters/horseman-3d/source-inspection.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
a=bpy.data.objects['AnimalArmature'];a.animation_data.action=bpy.data.actions['AnimalArmature|Idle'];a.animation_data.action_slot=a.animation_data.action.slots[0]
for t in a.animation_data.nla_tracks:t.mute=True
bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
o=bpy.data.objects['Horse'];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=[ev.matrix_world@v.co for v in me.vertices]
print('IDLE_BOUNDS',[[min(p[i] for p in v),max(p[i] for p in v)] for i in range(3)])
print('RIG_WORLD',a.matrix_world)
for bn in ['Back','Torso','Torso2','Neck3','Head','FF.L']:print(bn,list(a.matrix_world@a.pose.bones[bn].head))
