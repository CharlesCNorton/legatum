"""Audit full 3D sources, frozen base, finite transforms, loops and terminal hold."""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from bpy_extras.object_utils import world_to_camera_view
records={};sourcehash=hashlib.sha256((M/'peltast.blend').read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(M/'peltast.blend'))
sc=bpy.context.scene;bpy.context.view_layer.update()
rest={p.name:p.matrix.copy() for p in bpy.data.objects['RIG-Peltast'].pose.bones}
control_bones={'CTRL-Pelta':'hand_l','CTRL-Throwing javelin':'hand_r'}
rest_controls={name:bpy.data.objects[name].matrix_world.copy() for name in control_bones}
uv_error=0.;finished_count=0
for obj in sc.objects:
 if obj.type!='MESH' or not obj.get('finished_projection_surface'):continue
 uv=obj.data.uv_layers.get('Painting rest UV')
 if uv is None:continue
 finished_count+=1
 assert not obj.modifiers,'Rigid geometry changed after UV calibration'
 for loop in obj.data.loops:
  q=world_to_camera_view(sc,sc.camera,obj.matrix_world@obj.data.vertices[loop.vertex_index].co)
  uv_error=max(uv_error,256*(Vector((q.x,q.y))-uv.data[loop.index].uv).length)
assert finished_count>100 and uv_error<.01,(finished_count,uv_error)
for clip,(n,fps,loop) in CLIPS.items():
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Peltast'];base=bpy.data.objects['GEO-Stationary cream base'];refbase=base.matrix_world.copy();assert sc['source_sha256']==sourcehash
 assert len(rig.data.bones)==53;assert len(bpy.data.objects['GEO-MPFB peltast anatomy'].data.vertices)>10000
 assert bpy.data.objects['GEO-Dished wicker crescent pelta'].get('finished_projection_surface'), 'Project the finished thick shield'
 assert any('Painting rest UV' in o.data.uv_layers for o in sc.objects if o.type=='MESH')
 matrices=[];control_matrices=[];grip_error=0.
 if clip in ('idle','move','hit','death'):
  provenance=json.loads(sc['motion_provenance'])
  assert provenance['license']=='CC0-1.0'
  assert provenance['action'] in ('Idle_Loop','Walk_Loop','Hit_Chest','Death01')
 if clip=='attack':
  for frame in (1,n):
   sc.frame_set(frame);bpy.context.view_layer.update()
   error=max(abs(p.matrix[r][c]-rest[p.name][r][c]) for p in rig.pose.bones for r in range(4) for c in range(4))
   assert error<1e-5,('Attack guard endpoint pop',frame,error)
 for f in range(1,n+1):
  sc.frame_set(f);bpy.context.view_layer.update();assert base.matrix_world==refbase,'Moving base'
  for o in sc.objects:
   assert all(math.isfinite(v) for row in o.matrix_world for v in row),'Nonfinite transform'
   if o.type in ('MESH','CURVE'):assert min(abs(v) for v in o.matrix_world.to_scale())>.0001,'Near-zero geometry scale'
  if clip in ('idle','move','hit'):
   for name,bone in control_bones.items():
    expected=rig.matrix_world@rig.pose.bones[bone].matrix@rest[bone].inverted()@rest_controls[name]
    grip_error=max(grip_error,(expected.translation-bpy.data.objects[name].matrix_world.translation).length)
  control_matrices.append([v for name in ('CTRL-Pelta','CTRL-Throwing javelin') for row in bpy.data.objects[name].matrix_world for v in row])
  matrices.append([list(row) for row in rig.matrix_world]+[[v for row in p.matrix for v in row] for p in rig.pose.bones])
 if loop:
  sc.frame_set(n+1);bpy.context.view_layer.update();wrap=[list(row) for row in rig.matrix_world]+[[v for row in p.matrix for v in row] for p in rig.pose.bones];error=max(abs(a-b) for aa,bb in zip(matrices[0],wrap) for a,b in zip(aa,bb));assert error<1e-5,(clip,'loop mismatch',error)
  end_controls=[v for name in ('CTRL-Pelta','CTRL-Throwing javelin') for row in bpy.data.objects[name].matrix_world for v in row]
  assert max(abs(a-b) for a,b in zip(control_matrices[0],end_controls))<1e-5,'Equipment loop mismatch'
 else:error=None
 if clip=='death':assert max(abs(a-b) for aa,bb in zip(matrices[-1],matrices[-2]) for a,b in zip(aa,bb))<1e-5,'Death not settled'
 assert grip_error<1e-4,('Equipment separated from hand',clip,grip_error)
 records[clip]={'hand_equipment_translation_error_m':grip_error if clip in ('idle','move','hit') else None,'frames':n,'base':'stationary','loop_max_matrix_error':error,'true_3d':True}
 if clip=='move':
  from mathutils import Quaternion
  toe_samples=[];max_rotation_error=0.;min_forward=1.
  for i in range(n+1):
   sc.frame_set(i+1);bpy.context.view_layer.update()
   sample={}
   for side in ('l','r'):
    foot=rig.pose.bones['foot_'+side];toe=rig.pose.bones['ball_'+side]
    expected=Quaternion(provenance['baked_foot_rotations'][i][side])
    angle=foot.matrix.to_quaternion().rotation_difference(expected).angle
    max_rotation_error=max(max_rotation_error,min(angle,abs(2*pi-angle)))
    direction=toe.head-foot.head;direction.z=0
    stance=(side=='l' and 1<=i<=4) or (side=='r' and 5<=i<=8)
    if stance and direction.length>.001:min_forward=min(min_forward,direction.normalized().dot(Vector((0,-1,0))))
    sample[side]=rig.matrix_world@toe.head
   toe_samples.append(sample)
  speed=provenance['contact']['virtual_ground_m_per_sample'];slip=0.
  for side,start,end in [('l',1,4),('r',5,8)]:
   anchor=toe_samples[start][side]
   for i in range(start,end+1):
    expected=anchor+Vector((0,speed*(i-start),0));actual=toe_samples[i][side]
    slip=max(slip,Vector((actual.x-expected.x,actual.y-expected.y,0)).length)
  assert max_rotation_error<.001,('Post-retarget foot rotation',max_rotation_error)
  assert min_forward>.70,('Feet not facing travel',min_forward)
  assert slip<.002,('Toe stance slide',slip)
  records[clip].update(foot_rotation_error_rad=max_rotation_error,min_forward_dot=min_forward,virtual_ground_stance_slip_m=slip)
(R/'peltast-audit.json').write_text(json.dumps({'passed':True,'source_sha256':sourcehash,'clip_sha256':{clip:hashlib.sha256((M/'clips'/f'{clip}.blend').read_bytes()).hexdigest() for clip in CLIPS},'finished_projected_meshes':finished_count,'rigid_uv_max_error_px':uv_error,'clips':records,'scope':'Finished rigid projection, attack endpoint continuity, topology, transform sanity, stationary base, loop and terminal skeletal pose. Visual intersections remain review work.'},indent=2));print('AUDIT PASS',json.dumps(records),'UV error',uv_error)
