"""CMU BVH global rotations with explicit rest/axis calibration; no foot rewrites."""
import bpy, math, sys, json, hashlib
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0,str(Path('tools/art/anim3d').resolve()))
from mocap import BVH

MAP={'pelvis':'Hips','spine_01':'LowerBack','spine_02':'Spine','spine_03':'Spine1','neck_01':'Neck','head':'Head',
     'thigh_l':'LeftUpLeg','calf_l':'LeftLeg','foot_l':'LeftFoot','ball_l':'LeftToeBase',
     'thigh_r':'RightUpLeg','calf_r':'RightLeg','foot_r':'RightFoot','ball_r':'RightToeBase'}
ARMS={'upperarm_l':'LeftArm','lowerarm_l':'LeftForeArm','hand_l':'LeftHand',
      'upperarm_r':'RightArm','lowerarm_r':'RightForeArm','hand_r':'RightHand'}

class Capture(BVH):
 def __init__(self,path):
  super().__init__(path);self.path=path;self.hash=hashlib.sha256(path.read_bytes()).hexdigest()
  # CMU Y-up / +Z forward -> Blender Z-up / -Y forward. Calibration is
  # fixed for the whole clip, so a fall keeps its captured root pitch/roll.
  self.axis=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
 def matrices(self,frame):
  values=self.frames[max(0,min(int(frame),len(self.frames)-1))];world=[];out={}
  for j in self.joints:
   mat=Matrix.Translation(j['offset']);rot=Matrix.Identity(4)
   for channel,index in j['channels']:
    if channel.endswith('position'):mat.translation['XYZ'.index(channel[0])]+=values[index]
    else:rot=rot@Matrix.Rotation(math.radians(values[index]),4,channel[0])
   mat=mat@rot
   if j['parent'] is not None:mat=world[j['parent']]@mat
   world.append(mat);out[j['name']]=self.axis@mat
  return out

class Retarget:
 def __init__(self,root,rig,clip,solver):
  self.rig=rig;self.clip=clip;self.solver=solver
  self.restfeet={side:rig.pose.bones['foot_'+side].head.copy() for side in ['l','r']}
  path=root/'assets'/({'idle':'cmu-77_02.bvh','move':'cmu-02_01.bvh'}.get(clip,'byzantine-heir/cmu-90_18.bvh'))
  self.capture=Capture(path)
  lock=json.loads((Path(__file__).parent/'motion.lock.json').read_text())
  entry=next(row for row in lock if (root/'assets'/row['file'])==path)
  assert self.capture.hash==entry['sha256'],'Motion source changed: '+str(path)
  self.reference=self.capture.matrices(0 if clip=='move' else 80 if clip=='idle' else 50 if clip=='death' else 65)
  self.first=self.capture.matrices(1 if clip=='move' else 80 if clip=='idle' else 50 if clip=='death' else 65)
  self.mapping={**MAP,**(ARMS if clip=='death' else {})}
  self.neutral={name:rig.pose.bones[name].matrix.to_quaternion() for name in self.mapping}
  self.origin=rig.location.copy();self.travel=[]
  # Uniform anatomical scale measured from hip-to-ankle segment lengths.
  source=self.capture.matrices(0)
  length=(source['LeftUpLeg'].translation-source['LeftLeg'].translation).length+(source['LeftLeg'].translation-source['LeftFoot'].translation).length
  self.scale=(rig.data.bones['thigh_l'].length+rig.data.bones['calf_l'].length)/length
  # Fixed source yaw alignment, determined once from the initial hip line.
  across=self.first['LeftUpLeg'].translation-self.first['RightUpLeg'].translation;across.z=0
  self.yaw=Matrix.Rotation(-math.atan2(across.y,across.x),4,'Z').to_quaternion()
  self.records=[];self.locks={}
 def apply(self,t,i):
  if self.clip=='move':
   frame=1+round((t%1)*132);blend=1
   if t>=1:self.locks={}
  elif self.clip=='idle':frame=80+round(t*96);blend=math.sin(math.pi*t)**2
  elif self.clip=='hit':frame=[65,90,78,65][i];blend=1
  else:frame=[50,65,80,95,110,130,170,240,360,360][i];blend=1
  pose=self.capture.matrices(frame)
  names=list(self.mapping) if self.clip in {'move','death'} else ['spine_01','spine_02','spine_03','neck_01','head']
  # Set global orientations in hierarchy order. Bone-roll/rest offsets are
  # captured once in neutral; no constant post-retarget foot orientation.
  names.sort(key=lambda name:len(self.rig.pose.bones[name].parent_recursive))
  for name in names:
   source=self.mapping[name];delta=pose[source].to_quaternion()@self.reference[source].to_quaternion().inverted()
   delta=self.yaw@delta@self.yaw.inverted();delta=Quaternion().slerp(delta,blend)
   bone=self.rig.pose.bones[name];mat=(delta@self.neutral[name]).to_matrix().to_4x4();mat.translation=bone.head;bone.matrix=mat
   bpy.context.view_layer.update()
  if self.clip=='death' and t>.1:
   # Release the weapon-carrying rest pose into the capture's hand positions.
   # Rotation deltas alone preserve the bent carrying elbows throughout a fall.
   release=min(1,(t-.1)/.25);release=release*release*(3-2*release)
   for side,prefix in [('l','Left'),('r','Right')]:
    hand=self.rig.pose.bones['hand_'+side];orientation=hand.matrix.to_quaternion()
    hip=self.rig.pose.bones['pelvis'].head
    target=hip+self.yaw@(pose[prefix+'Hand'].translation-pose['Hips'].translation)*self.scale
    pole=hip+self.yaw@(pose[prefix+'ForeArm'].translation-pose['Hips'].translation)*self.scale
    self.solver('upperarm_'+side,'lowerarm_'+side,hand.head.lerp(target,release),pole)
    hand=self.rig.pose.bones['hand_'+side];mat=orientation.to_matrix().to_4x4();mat.translation=hand.head;hand.matrix=mat
    bpy.context.view_layer.update()
  travel=self.yaw@(pose['Hips'].translation-self.first['Hips'].translation)*self.scale
  if self.clip=='move':
   # End-effector positions come from the same capture as rotations. This
   # removes stance drift introduced by differing limb lengths/rest spread.
   # Preserve the captured orientation target through the positional IK solve;
   # there is no authored foot angle or per-frame corrective rotation.
   targets={};rotations={};poles={}
   for side,prefix in [('l','Left'),('r','Right')]:
    foot=self.rig.pose.bones['foot_'+side];captured=foot.matrix.to_quaternion()
    source=pose[prefix+'Foot'].translation-pose['Hips'].translation
    reference=self.reference[prefix+'Foot'].translation-self.reference['Hips'].translation
    ankle=self.restfeet[side]+self.yaw@(source-reference)*self.scale
    knee=pose[prefix+'Leg'].translation-pose['Hips'].translation
    pole=self.rig.pose.bones['pelvis'].head+self.yaw@knee*self.scale
    targets[side]=ankle;rotations[side]=captured;poles[side]=pole
    self.solver('thigh_'+side,'calf_'+side,ankle,pole)
    foot=self.rig.pose.bones['foot_'+side];mat=captured.to_matrix().to_4x4();mat.translation=foot.head;foot.matrix=mat
    bpy.context.view_layer.update()
   self.rig.location.z=self.origin.z+travel.z
   # Contact translation is global only; all foot rotations stay from capture.
   bpy.context.view_layer.update()
   sole=min((bpy.data.objects['Leather toe '+side].matrix_world@v.co).z for side in ['l','r'] for v in bpy.data.objects['Leather toe '+side].data.vertices)
   self.rig.location.z+=.09-sole
   bpy.context.view_layer.update()
   # Pin the actual contacting sole patch in the removed-travel coordinate
   # frame. This is translation-only stance IK, never an authored foot angle.
   for side in ['l','r']:
    toe=bpy.data.objects['Leather toe '+side]
    points=[toe.matrix_world@v.co for v in toe.data.vertices];low=min(p.z for p in points)
    if low>=.115:
     self.locks.pop(side,None);continue
    patch=[p for p in points if p.z<low+.005];centre=sum(patch,Vector())/len(patch)+travel
    if side not in self.locks:self.locks[side]=centre.copy()
    delta=self.locks[side]-centre;delta.z=0
    target=targets[side]+self.rig.matrix_world.to_3x3().inverted()@delta
    self.solver('thigh_'+side,'calf_'+side,target,poles[side])
    foot=self.rig.pose.bones['foot_'+side];mat=rotations[side].to_matrix().to_4x4();mat.translation=foot.head;foot.matrix=mat
    bpy.context.view_layer.update()
   sole=min((bpy.data.objects['Leather toe '+side].matrix_world@v.co).z for side in ['l','r'] for v in bpy.data.objects['Leather toe '+side].data.vertices)
   self.rig.location.z+=.09-sole
  elif self.clip=='death':
   self.rig.location=self.origin+Vector((travel.x,travel.y*.35,travel.z))
   bpy.context.view_layer.update()
   # Keep the captured collapse above the disc without changing its rotations.
   names=['Leather toe r','Leather toe l','Heir MPFB anatomy','Lamellar cuirass']
   lowest=10
   deps=bpy.context.evaluated_depsgraph_get()
   for name in names:
    ob=bpy.data.objects[name];ev=ob.evaluated_get(deps);me=ev.to_mesh()
    lowest=min(lowest,min((ev.matrix_world@v.co).z for v in me.vertices));ev.to_mesh_clear()
   self.rig.location.z+=.09-lowest
  self.records.append({'source_frame':frame,'root_motion_m':list(travel),'source':self.capture.path.name})
 def provenance(self):
  return {'cycle_displacement_m':list(self.yaw@(self.capture.matrices(133)['Hips'].translation-self.first['Hips'].translation)*self.scale) if self.clip=='move' else None,'source':str(self.capture.path),'sha256':self.capture.hash,'licence':'CMU free use; Bruce Hahne 2010 BVH conversion','samples':self.records,'bone_map':self.mapping,'method':'Rest-calibrated BVH rotation and captured ankle-target retarget; fixed Y-up to Z-up and forward alignment; no authored foot angles'}
