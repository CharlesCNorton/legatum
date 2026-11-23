"""Minimal BVH forward kinematics; original CMU channels, no synthetic stand-in."""
import re, math
from mathutils import Matrix,Vector
class BVH:
 def __init__(self,path):
  h,m=path.read_text().split('MOTION');self.joints=[];self.channels=0
  tokens=iter(re.findall(r'[{}]|[^\s{}]+',h))
  def joint(parent,kind):
   name=next(tokens) if kind!='End' else self.joints[parent]['name']+'_end'
   if kind=='End':next(tokens)
   assert next(tokens)=='{'
   j={'name':name,'parent':parent,'offset':None,'channels':[]};idx=len(self.joints);self.joints.append(j)
   while True:
    t=next(tokens)
    if t=='}':break
    if t=='OFFSET':j['offset']=Vector([float(next(tokens)) for _ in range(3)])
    elif t=='CHANNELS':
     for _ in range(int(next(tokens))):j['channels'].append((next(tokens),self.channels));self.channels+=1
    elif t in ['JOINT','End']:joint(idx,t)
   return idx
  assert next(tokens)=='HIERARCHY';assert next(tokens)=='ROOT';joint(None,'ROOT')
  lines=m.strip().splitlines();self.dt=float(lines[1].split(':')[1]);self.frames=[[float(v) for v in l.split()] for l in lines[2:] if l.strip()]
  assert len(self.frames)==int(lines[0].split(':')[1])
 def positions(self,frame):
  values=self.frames[max(1,min(frame,len(self.frames)-1))];world=[];out={}
  for j in self.joints:
   mat=Matrix.Translation(j['offset']);r=Matrix.Identity(4)
   for c,i in j['channels']:
    if c.endswith('position'):mat.translation['XYZ'.index(c[0])]+=values[i]
    else:r=r @ Matrix.Rotation(math.radians(values[i]),4,c[0])
   mat=mat @ r
   if j['parent'] is not None:mat=world[j['parent']] @ mat
   world.append(mat);out[j['name']]=mat.translation.copy()
  # Remove actor travel and yaw, preserve local captured limb directions.
  origin=out['Hips'];x=out['LeftUpLeg']-out['RightUpLeg'];x.y=0;x.normalize()
  z=x.cross(Vector((0,1,0))).normalized()
  return {k:Vector(((v-origin).dot(x),-(v-origin).dot(z),(v-origin).y)) for k,v in out.items()}
