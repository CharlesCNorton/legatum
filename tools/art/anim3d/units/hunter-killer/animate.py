"""Rigid robotic articulation with analytic two-link IK and fixed contact feet.
No animal/human locomotion is used: this is the vehicles mechanical-motion exception.
"""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import MASTER, CLIPS, log
TAU=math.tau

def solve(hip,foot,knee0,hip0,foot0,a,b):
 direction=foot-hip;distance=direction.length
 assert abs(a-b)+1e-5<distance<a+b-1e-5,('IK reach',distance,a,b)
 axis=direction.normalized();restaxis=(foot0-hip0).normalized();bend=knee0-hip0; bend-=restaxis*bend.dot(restaxis)
 bend-=axis*bend.dot(axis);bend.normalize()
 along=(a*a-b*b+distance*distance)/(2*distance)
 return hip+axis*along+bend*math.sqrt(max(0,a*a-along*along))

def curves(action):
 if hasattr(action,'fcurves'):return action.fcurves
 return [fc for layer in action.layers for strip in layer.strips if hasattr(strip,'channelbags') for bag in strip.channelbags for fc in bag.fcurves]

for clip,(count,fps,loop) in CLIPS.items():
 bpy.ops.wm.open_mainfile(filepath=str(MASTER/'finished.blend'));sc=bpy.context.scene;body=bpy.data.objects['RIG-chassis'];turret=bpy.data.objects['RIG-turret'];recoil=bpy.data.objects['RIG-recoil'];flash=bpy.data.objects['GEO-Muzzle flash'];legs=json.loads(sc['legs'])
 body0=body.location.copy();turret0=turret.rotation_euler.copy();recoil0=recoil.location.copy();bodymat=body.matrix_world.copy();samples=list(range(1,count+1))
 if clip=='death':samples[-1]=samples[-2]
 records=[]
 # One extra loop endpoint ensures saved F-curves close exactly; not an extra output frame.
 for frame in range(1,count+2 if loop else count+1):
  t=(frame-1)/(count if loop else count-1);s=math.sin(TAU*t);body.location=body0;body.rotation_euler=(0,0,0);turret.rotation_euler=turret0;recoil.location=recoil0;flash.hide_render=True
  if clip=='idle':body.location.z-=.012*(1-math.cos(TAU*t));turret.rotation_euler.z+=math.radians(2)*s
  elif clip=='move':body.location.x+=.055*math.sin(TAU*t);body.location.z-=.025*(1-math.cos(2*TAU*t));body.rotation_euler.y=.012*math.sin(TAU*t)
  elif clip=='attack':
   pulse=[0,.0,.15,1,.55,.20,.05,0,0,0][frame-1];body.location.x-=.075*pulse;body.location.z-=.09*pulse;body.rotation_euler.y=-.025*pulse;turret.rotation_euler.z+=math.radians(3)*math.sin(math.pi*t);recoil.location.x-=.24*pulse;flash.hide_render=not(.27<t<.43)
  elif clip=='hit':
   q=[0,1,-.35,0][frame-1];body.location.x+=.06*q;body.location.z-=.09*abs(q);body.rotation_euler.y+=.018*q;turret.rotation_euler.z-=.04*q
  elif clip=='death':
   u=min(1,t/.78);ease=u*u*(3-2*u);body.location.z-=.56*ease;body.rotation_euler.y+=.12*ease;body.rotation_euler.x-=.07*ease;turret.rotation_euler.z-=.12*ease
  bpy.context.view_layer.update()
  contacts=[]
  for j,leg in enumerate(legs):
   hip0,knee0,foot0=[Vector(leg[k]) for k in ('hip','knee','foot')];hip=body.matrix_world@(bodymat.inverted()@hip0);foot=foot0.copy();air=False
   if clip=='move':
    phase=(t-j/4)%1
    if phase<.375:
     u=phase/.375;lift=math.sin(math.pi*u)**2;foot.z+=.18*lift;foot.y-=.03*math.sin(TAU*u)*lift;air=lift>1e-8
   knee=solve(hip,foot,knee0,hip0,foot0,*leg['lengths'])
   upper=bpy.data.objects['RIG-upper-'+leg['name']];lower=bpy.data.objects['RIG-lower-'+leg['name']];shoe=bpy.data.objects['RIG-foot-'+leg['name']]
   upper.location=hip;lower.location=knee;shoe.location=foot
   upper.rotation_quaternion=(knee0-hip0).rotation_difference(knee-hip);lower.rotation_quaternion=(foot0-knee0).rotation_difference(foot-knee)
   for o in (upper,lower):o.keyframe_insert('location',frame=frame);o.keyframe_insert('rotation_quaternion',frame=frame)
   shoe.keyframe_insert('location',frame=frame)
   contacts.append({'leg':leg['name'],'airborne':air,'foot':list(foot),'plant_error':0 if air else (foot-foot0).length,'upper_error':abs((hip-knee).length-leg['lengths'][0]),'lower_error':abs((foot-knee).length-leg['lengths'][1])})
  for o in (body,turret,recoil):o.keyframe_insert('location',frame=frame);o.keyframe_insert('rotation_euler',frame=frame)
  flash.keyframe_insert('hide_render',frame=frame);records.append({'frame':frame,'contacts':contacts})
 for action in bpy.data.actions:
  for fc in curves(action):
   for key in fc.keyframe_points:key.interpolation='CONSTANT' if fc.data_path=='hide_render' else 'LINEAR'
 sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps;sc['sample_frames']=json.dumps(samples);sc['clip']=clip;sc.frame_set(1)
 folder=MASTER/'clips';folder.mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(folder/f'{clip}.blend'))
 (folder/f'{clip}-kinematics.json').write_text(json.dumps(records,indent=2))
 log(f'Keyed {clip}: {count} output samples; fixed planted contacts, rigid IK segments; terminal death held.' )
