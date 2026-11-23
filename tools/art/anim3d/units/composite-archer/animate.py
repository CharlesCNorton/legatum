"""Five editable MPFB clips, hand-following string and keyed arrow release."""
import bpy,os,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
sys.path.insert(0,str(Path(__file__).parent));import geometry as g
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/composite-archer';CLIPS={'idle':(8,10),'move':(8,12),'attack':(10,14),'hit':(4,12),'death':(10,10)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def turn(rig,name,axis,angle):
 p=rig.pose.bones[name];mat=p.matrix.copy();pos=mat.translation.copy();mat=Matrix.Rotation(angle,4,axis) @ mat;mat.translation=pos;p.matrix=mat;bpy.context.view_layer.update()
def animate(clip):
 bpy.ops.wm.open_mainfile(filepath=str(M/'composite-archer.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-composite-archer'];g.rig=rig
 neutral=json.loads(rig['neutral_pose']);base=Vector(rig['neutral_location']);bow=bpy.data.objects['CTRL-bow'];bowrest=bow.matrix_basis.copy();arrow=bpy.data.objects['CTRL-arrow'];arrowrest=arrow.matrix_world.copy();string=bpy.data.objects['GEO-bowstring'];original=[v.co.copy() for v in string.data.vertices]
 original_points=[Vector(v) for v in json.loads(string['rest_points'])];griprest=bow.matrix_world.translation.copy();localtips=[bow.matrix_world.inverted() @ original_points[i] for i in [0,2]]
 # String topology interpolation weights follow both bow tips and the nock.
 weights=[]
 for v in original:
  options=[]
  for j in [0,1]:
   a,b=original_points[j:j+2];axis=b-a;t=max(0,min(1,(v-a).dot(axis)/axis.length_squared));p=a+axis*t;options.append(((v-p).length,j,t,v-p))
  _,j,t,offset=min(options,key=lambda a:a[0]);weights.append((j,t,offset))
 string.shape_key_add(name='Basis');count,fps=CLIPS[clip];sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps
 for p in rig.pose.bones:p.rotation_mode='QUATERNION'
 # Bow detaches only in death; no object ever receives zero scale.
 if clip=='death':
  world=bow.matrix_world.copy();bow.parent=None;bow.matrix_world=world;bowrestworld=world.copy()
 out=M/'clips';out.mkdir(exist_ok=True);(out/f'{clip}.json').unlink(missing_ok=True)
 handhomes={side:rig.matrix_world @ rig.pose.bones['hand_'+side].head for side in ['l','r']}
 foothomes={side:rig.matrix_world @ rig.pose.bones['foot_'+side].head for side in ['l','r']}
 kneehomes={side:rig.matrix_world @ rig.pose.bones['calf_'+side].head for side in ['l','r']}
 elbowhomes={side:rig.matrix_world @ rig.pose.bones['lowerarm_'+side].head for side in ['l','r']}
 snapshots=[]
 for i in range(count+(1 if clip in ['idle','move'] else 0)):
  frame=i+1;t=i/count if clip in ['idle','move'] else min(i,count-1)/(count-1);sc.frame_set(frame)
  rig.location=base;rig.rotation_euler=(0,0,0)
  for p in rig.pose.bones:p.matrix_basis=Matrix(neutral[p.name])
  if clip!='death':bow.matrix_basis=bowrest
  else:bow.matrix_world=bowrestworld
  arrow.matrix_world=arrowrest;arrow.hide_render=False
  for child in arrow.children:child.hide_render=False
  bpy.context.view_layer.update()
  release=0;death=0
  if clip=='idle':
   breath=math.sin(t*2*math.pi);turn(rig,'spine_03','Y',.012*breath);turn(rig,'head','Z',.014*breath)
  elif clip=='move':
   # A low, guarded in-place advance; a kneeling unit does not pop upright off-frame.
   phase=2*math.pi*t;rig.location.z=base.z+.035+.018*math.cos(phase*2)
   for side,sg in [('l',1),('r',-1)]:
    step=math.sin(phase+(0 if sg==1 else math.pi));lift=.09*max(0,math.cos(phase+(0 if sg==1 else math.pi)))
    ankle=Vector((sg*.23+.14*step,-.05+sg*.08,.125+lift))-rig.location
    pole=Vector((sg*.32,-.35,.46))-rig.location
    g.limb('thigh_'+side,'calf_'+side,ankle,pole);g.aim_bone('foot_'+side,(.17,-.05,-.03))
   g.limb('upperarm_l','lowerarm_l',(.59,-.18,1.40),(.40,-.28,1.35));g.limb('upperarm_r','lowerarm_r',(.10,-.30,1.40),(-.40,-.24,1.37));turn(rig,'spine_03','Z',.035*math.sin(phase))
  elif clip=='attack':
   # Archery follow-through: drawing hand recoils BACK from the cheek.
   # It never travels forward with the string. Recovery reaches toward the quiver.
   hx=[-.035,-.055,-.07,-.07,-.14,-.13,-.26,-.22,-.06,-.035][i]
   hz=[1.60,1.60,1.60,1.60,1.59,1.50,1.18,1.30,1.50,1.60][i]
   g.limb('upperarm_r','lowerarm_r',(hx,-.30,hz),(-.55,-.26,1.55));g.aim_bone('hand_r',(.10,0,0));turn(rig,'spine_03','Y',-.025*math.sin(t*math.pi))
   if 4<=i<=7:
    for child in arrow.children:child.hide_render=True
  elif clip=='hit':
   strength=[0,1,.45,0][i];turn(rig,'spine_03','Y',-.09*strength);turn(rig,'head','Y',-.06*strength)
  elif clip=='death':
   a=min(1,t/.78);death=a*a*(3-2*a);rig.location=base+Vector((.10*death,.03*death,-.26*death));turn(rig,'pelvis','Y',-1.35*death);turn(rig,'spine_03','Y',-.20*death)
   # Fold legs toward the torso instead of a straight rigid body fall.
   for side,sg in [('l',1),('r',-1)]:
    footend=Vector((.34,-.06,.16) if side=='l' else (.12,.17,.15))
    ankle=foothomes[side].lerp(footend,death)-rig.location
    pole=kneehomes[side].lerp(Vector((.28,-.35,.24) if side=='l' else (.10,.33,.22)),death)-rig.location
    if death>0:g.limb('thigh_'+side,'calf_'+side,ankle,pole)
   # Let both arms come to rest across the fallen torso, never hold a fist aloft.
   for side in ['l','r']:
    handend=Vector((.05,-.25,.20) if side=='l' else (-.42,-.20,.20))
    wrist=handhomes[side].lerp(handend,death)-rig.location
    pole=elbowhomes[side].lerp(Vector((-.15,-.33,.20) if side=='l' else (-.50,-.10,.19)),death)-rig.location
    if death>0:g.limb('upperarm_'+side,'lowerarm_'+side,wrist,pole)
   # Released bow settles flat on the front of the disc; visibility remains real.
   q=bowrestworld.to_quaternion().slerp(Quaternion((0,1,0),math.pi/2),death)
   pos=bowrestworld.translation.lerp(Vector((.01,-.22,.12)),death);bow.matrix_world=Matrix.Translation(pos) @ q.to_matrix().to_4x4()
   for child in arrow.children:child.hide_render=i>=2
   # Ground the actual evaluated anatomy and costume, excluding the released bow.
   bpy.context.view_layer.update();zs=[]
   for o in sc.objects:
    if o.type!='MESH' or o.name.startswith(('GEO-stationary','GEO-bowstring','GEO-arrow','GEO-nocked')):continue
    if o.parent==arrow:continue
    if o.name.startswith(('GEO-MPFB anatomical','GEO-patterned trousers','GEO-soft leather boots','GEO-tunic')):
     ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();zs.extend((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
   rig.location.z+=max(0,.094-min(zs))*death
  bpy.context.view_layer.update()
  # String middle follows the draw hand until release, then goes to bow center.
  tip0,tip1=[bow.matrix_world @ p for p in localtips];nock=rig.matrix_world @ rig.pose.bones['hand_r'].head+Vector((.04,-.015,.026))
  if clip=='death':nock=nock.lerp((tip0+tip1)*.5,death)
  if clip=='attack' and 4<=i<=8:
   nock=nock.lerp((tip0+tip1)*.5,1 if i<=7 else .3)
  points=[tip0,nock,tip1];key=string.shape_key_add(name=f'{clip}-{frame:02d}')
  for v,(j,u,offset) in zip(key.data,weights):v.co=points[j].lerp(points[j+1],u)+offset
  for f,value in [(frame-1,0),(frame,1),(frame+1,0)]:key.value=value;key.keyframe_insert('value',frame=f)
  key.value=1
  # Rotate complete arrow geometry along the actual nock-to-grip axis.
  currentgrip=bow.matrix_world.translation+Vector((.15,0,.026));original_axis=griprest+Vector((.15,0,.026))-arrowrest.translation
  axis=currentgrip-nock;q=original_axis.rotation_difference(axis);arrow.matrix_world=Matrix.Translation(nock) @ q.to_matrix().to_4x4()
  for child in arrow.children:child.keyframe_insert('hide_render',frame=frame)
  arrow.rotation_mode='QUATERNION';bow.rotation_mode='QUATERNION'
  for o in [rig,bow,arrow]:
   for prop in ['location','rotation_quaternion' if o!=rig else 'rotation_euler','scale']:o.keyframe_insert(prop,frame=frame)
  for p in rig.pose.bones:
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=frame)
  snapshots.append({'frame':frame,'bow_tips':[list(tip0),list(tip1)],'nock':list(nock),'root':list(rig.location)})
 # Same geometry state in both terminal frames. Shape keys preserve it independently.
 for action in bpy.data.actions:
  for layer in action.layers:
   for strip in layer.strips:
    for bag in getattr(strip,'channelbags',[]):
     for fc in bag.fcurves:
      for kp in fc.keyframe_points:
       kp.interpolation='LINEAR' if 'key_blocks' in fc.data_path else 'BEZIER';kp.handle_left_type=kp.handle_right_type='AUTO_CLAMPED'
 sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{clip}.blend'))
 (out/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':clip in ['idle','move'],'source_sha256':sha(M/'composite-archer.blend'),'samples':snapshots},indent=2));print('CLIP_READY',clip,flush=True)
if __name__=='__main__':
 for clip in ([os.environ['CLIP']] if os.environ.get('CLIP') else CLIPS):animate(clip)
