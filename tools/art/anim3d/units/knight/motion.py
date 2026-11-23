"""Sample CC0 human torso motion with reference-pose and bone-roll alignment.

Seated pelvis/legs and equipment grips remain saddle/hand constraints. The horse
supplies locomotion; no human walking feet are retargeted or post-rotated.
"""
import bpy,os,json
from pathlib import Path
from mathutils import Quaternion
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/knight'
bpy.ops.wm.open_mainfile(filepath=str(M/'knight.blend'));target=bpy.data.objects['Rider MPFB game_engine'];before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(R/'assets/quaternius-ual/AnimationLibrary_Godot_Standard.gltf'))
source=next(o for o in set(bpy.data.objects)-before if o.type=='ARMATURE')
for t in source.animation_data.nla_tracks:t.mute=True
mapping={'spine_01':'DEF-spine.001','spine_02':'DEF-spine.002','spine_03':'DEF-spine.003','neck_01':'DEF-neck','head':'DEF-head'}
mapping={t:s for t,s in mapping.items() if t in target.pose.bones and s in source.pose.bones}
clips={'idle':('Sitting_Idle_Loop',8,True),'move':('Sitting_Idle_Loop',8,True),'hit':('Hit_Chest',4,False),'death':('Death01',10,False)}
result={}
for clip,(name,count,loop) in clips.items():
 action=next(a for a in bpy.data.actions if a.name==name or a.name.endswith('|'+name));source.animation_data.action=action;source.animation_data.action_slot=action.slots[0]
 start,end=action.frame_range;frames=[]
 # Motion is relative to the clip's first pose, preserving the painted seat.
 bpy.context.scene.frame_set(int(start));reference={s:source.pose.bones[s].rotation_quaternion.copy() for s in mapping.values()}
 for i in range(count+int(loop)):
  t=i/count if loop else min(i/(count-2 if clip=='death' else count-1),1)
  frame=start+t*(end-start);bpy.context.scene.frame_set(int(frame),subframe=frame%1);row={}
  for tn,sn in mapping.items():
   alignment=target.data.bones[tn].matrix_local.to_quaternion().inverted()@source.data.bones[sn].matrix_local.to_quaternion()
   delta=reference[sn].inverted()@source.pose.bones[sn].rotation_quaternion
   row[tn]=list(alignment@delta@alignment.inverted())
  frames.append(row)
 result[clip]={'source':name,'frames':frames,'mapping':mapping,'reference_frame':start,'source_range':[start,end]}
(M/'rider-motion.json').write_text(json.dumps(result,indent=2));print('KNIGHT_HUMAN_MOTION_READY')
