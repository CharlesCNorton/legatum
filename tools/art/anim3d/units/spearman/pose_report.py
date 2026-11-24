"""Print world joint positions, shield centre/normal and base size at chosen frames of a clip .blend.

    blender -b --factory-startup --python units/spearman/pose_report.py -- <blend> <frame,frame|samples>
"""
import bpy,sys,json
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=args[0]);sc=bpy.context.scene
rig=bpy.data.objects['Spearman • MPFB game_engine']
frames=json.loads(sc['sample_frames']) if args[1]=='samples' else [int(v) for v in args[1].split(',')]
base=bpy.data.objects['Stationary cream stone']
pts=[base.matrix_world @ v.co for v in base.data.vertices]
print('BASE floor',round(max(p.z for p in pts),3),'radius',round(max((p.x*p.x+p.y*p.y)**.5 for p in pts),3))
shield=bpy.data.objects['Aspis control']
print('SHIELD parent',shield.parent and shield.parent.name,shield.parent_type,shield.parent_bone)
r=lambda v:tuple(round(c,2) for c in v)
for f in frames:
 sc.frame_set(f);dg=bpy.context.evaluated_depsgraph_get()
 print('FRAME',f)
 for n in ['pelvis','spine_03','neck_01','head','upperarm_l','lowerarm_l','hand_l','upperarm_r','lowerarm_r','hand_r','thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r']:
  p=rig.pose.bones[n];print(' ',n,r(rig.matrix_world @ p.head),'tail',r(rig.matrix_world @ p.tail))
 m=shield.matrix_world;P=[]
 for ob in shield.children:
  ev=ob.evaluated_get(dg);me=ev.to_mesh();P+=[ob.matrix_world @ v.co for v in me.vertices];ev.to_mesh_clear()
 c=sum(P,Vector())/len(P)
 print('  shield origin',r(m.translation),'normal',r(m.to_quaternion() @ Vector((0,-1,0))),'centroid',r(c),'radius',round(max((p-c).length for p in P),3),'min z',round(min(p.z for p in P),3))
 cam=sc.camera.matrix_world;print('  camera view dir',r(cam.to_quaternion() @ Vector((0,0,-1))))
