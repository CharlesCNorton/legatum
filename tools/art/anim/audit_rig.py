"""CPU-only Blender audit. Does not render or substitute for visual review."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from units import CLIPS,UNITS
slug=sys.argv[sys.argv.index('--')+1]
dest=Path.home()/'LegatumRuns/anim-pilot/masters'/slug
bpy.ops.wm.open_mainfile(filepath=str(dest/f'{slug}.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['Miniature skeleton'];base=bpy.data.objects['base']
assert scene.render.engine=='BLENDER_EEVEE'
assert scene.render.threads==4 and scene.render.threads_mode=='FIXED'
assert scene.render.film_transparent and scene.frame_end==40
assert not base.animation_data and len(base.modifiers)==0
cam=scene.camera
assert cam.data.type=='ORTHO' and cam.data.ortho_scale==256
# Audit depth as well as x/y: the old audit passed a base beyond clip_end.
for obj in scene.objects:
 if obj.type!='MESH':continue
 for corner in obj.bound_box:
  depth=-(cam.matrix_world.inverted() @ obj.matrix_world @ Vector(corner)).z
  assert cam.data.clip_start < depth < cam.data.clip_end,(obj.name,'camera depth',depth)
assert all(obj.data.materials[0].blend_method=='HASHED' for obj in scene.objects
           if obj.type=='MESH' and obj.name in ('base','body'))
samples={}
for obj in scene.objects:
 if obj.type!='MESH' or not obj.vertex_groups:continue
 name=obj.name;bone=rig.pose.bones[obj.vertex_groups[0].name]
 tex=next(n for n in obj.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE').image
 pixels=list(tex.pixels);points=[]
 for y in range(1,256,2):
  for x in range(1,256,2):
   if pixels[(y*256+x)*4+3]<.5:continue
   xx=x
   if slug=='field-cannon' and name in ('wheel_l','wheel_r'):
    ratio=.44 if name=='wheel_l' else .50;cx=bone.bone.head_local.x;xx=cx+(x-cx)/ratio
   points.append(Vector((xx,0,y)))
 samples[name]=(bone,points)
report={'slug':slug,'engine':scene.render.engine,'threads':scene.render.threads,'poses':40,'base_stationary':True,'camera_depth_checked':True,'kit_pivots_attached':True,'rendered':False,'frames':[]}
frame=1
for clip,(count,_,_) in CLIPS.items():
 for index in range(count):
  scene.frame_set(frame);bpy.context.view_layer.update();xs=[];ys=[]
  for name in ('spear','shield'):
   if name in rig.pose.bones:
    assert rig.pose.bones[name].location.length < .0001,(clip,index,name,'detached grip')
  for bone,points in samples.values():
   matrix=bone.matrix @ bone.bone.matrix_local.inverted()
   for point in points:
    p=matrix@point;xs.append(p.x);ys.append(256-p.z)
  bounds=[round(min(xs),2),round(min(ys),2),round(max(xs),2),round(max(ys),2)]
  report['frames'].append({'clip':clip,'frame':index,'opaque_sample_bounds':bounds})
  frame+=1
report['out_of_frame']=[f for f in report['frames'] if min(f['opaque_sample_bounds'][:2])<0 or max(f['opaque_sample_bounds'][2:])>256]
(dest/'rig-audit.json').write_text(json.dumps(report,indent=2)+'\n')
assert not report['out_of_frame'],report['out_of_frame']
print(f'{slug}: 40 poses, stationary base, four-thread Eevee configuration and sampled projection bounds PASS (not rendered)')
