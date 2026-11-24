"""Authored rigid aircraft clips; the stationary base never follows the flight rig."""
import bpy,math,os,json,hashlib
from pathlib import Path
from mathutils import Vector, Matrix
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/biplane';src=M/'biplane.blend';source_hash=hashlib.sha256(src.read_bytes()).hexdigest()
clips={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
requested=os.environ.get('CLIP')
if requested and requested not in clips:raise ValueError('Unknown CLIP: '+requested)
for clip,(count,fps,loop) in clips.items():
 if requested and clip!=requested:continue
 bpy.ops.wm.open_mainfile(filepath=str(src));sc=bpy.context.scene;root=bpy.data.objects['RIG-flight'];prop=bpy.data.objects['RIG-propeller'];rest=root.location.copy();rot=root.rotation_euler.copy();support=bpy.data.objects['GEO-curved-display-support'];flash=[]
 # Full-depth stone fractures fall separately and settle on the base. Sections
 # share their exact rest boundary, with capped faces and frozen surface pigment.
 bpy.context.view_layer.update()
 supports=sorted((o for o in sc.objects if 'stone_section' in o),key=lambda o:o['stone_section'])
 support_rests={o.name:o.matrix_world.copy() for o in supports}
 pivots={o.name:sum((o.matrix_world@v.co for v in o.data.vertices),Vector())/len(o.data.vertices) for o in supports}
 fall_axis=sc.camera.matrix_world.to_3x3()@Vector((0,0,1))
 fall_axis.z=0;fall_axis.normalize()
 right=sc.camera.matrix_world.to_3x3()@Vector((1,0,0))
 base=bpy.data.objects['GEO-cream-stone-base'];base_inverse=base.matrix_world.inverted()
 def falling_support(progress):
  for o in supports:
   index=o['stone_section'];pivot=pivots[o.name]
   target=base.matrix_world.translation+right*[-.12,.20,.07][index]+fall_axis*[-.06,-.12,.24][index]
   target.z=[.28,.24,.20][index]
   rotation=Matrix.Rotation(math.radians([-92,88,-86][index])*progress,4,fall_axis)
   centre=pivot.lerp(target,progress)
   transform=Matrix.Translation(centre)@rotation@Matrix.Translation(-pivot)@support_rests[o.name]
   lift=0
   for v in o.data.vertices:
    world=transform@v.co;local=base_inverse@world
    surface=.13 if local.x**2+local.y**2<.68**2 else 0
    lift=max(lift,surface-world.z)
   transform.translation.z+=lift
   o.matrix_world=transform
 # Brief 3D muzzle streaks, never volume meshes or zero-scale hide tricks.
 # Position bursts from the finished barrel endpoints, not the pre-registration
 # coordinates: the old flashes sat inside the cowling after silhouette fitting.
 bpy.context.view_layer.update()
 for gun in [o for o in sc.objects if o.name.startswith('GEO-synchronized-gun')]:
  end=min((gun.matrix_world@v.co for v in gun.data.vertices),key=lambda p:p.x)
  local=root.matrix_world.inverted()@end
  local.x-=.25;local.z+=.055
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=local)
  o=bpy.context.object;o.name='GEO-muzzle-flash';o.scale=(.22,.038,.038);o.parent=root
  ma=bpy.data.materials.new('MAT-muzzle');ma.use_nodes=True
  s=ma.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(1,.3,.02,1)
  s.inputs['Emission Color'].default_value=(1,.55,.06,1);s.inputs['Emission Strength'].default_value=3
  o.data.materials.append(ma);flash.append(o)
 # Upper-wing stitching follows the physical wing during the crash.
 upper=bpy.data.objects['GEO-upper-cambered-wing']
 for rib in list(sc.objects):
  if rib.name.startswith('GEO-stitched-wing-rib'):
   z=sum(v.co.z for v in rib.data.vertices)/len(rib.data.vertices)
   if z>0:
    world=rib.matrix_world.copy();rib.parent=upper;rib.matrix_world=world
 # A broken upper wing pivots at the center on impact, rather than a generic fade.
 wing=bpy.data.objects['GEO-upper-cambered-wing'];wing_rest=wing.rotation_euler.copy()
 for i in range(count+(1 if loop else 0)):
  f=i+1;t=i/count;phase=math.tau*t;root.location=rest;root.rotation_euler=rot;prop.rotation_euler.x=i*2.13;wing.rotation_euler=wing_rest
  for o in supports:o.hide_render=False;o.matrix_world=support_rests[o.name]
  if clip=='idle':root.location.z+=.025*math.sin(phase);root.rotation_euler.x+=.025*math.sin(phase)
  elif clip=='move':root.location.x+=.035*(1+math.sin(phase));root.location.z+=.04*math.sin(phase);root.rotation_euler.x+=.055*math.sin(phase);root.rotation_euler.y+=.025*math.cos(phase);prop.rotation_euler.x=i*2.8
  elif clip=='attack':
   k=math.sin(math.pi*i/(count-1));root.location.x+=.03*k;root.location.z-=.16*k;root.rotation_euler.y-=.10*k;root.rotation_euler.x+=.06*k
  elif clip=='hit':
   k=[0,1,-.35,0][i];root.location.z-=.10*k;root.rotation_euler.x+=.14*k;root.rotation_euler.z+=.04*k
  elif clip=='death':
   # Descent, nose-down impact, crumpled wing, then a held planted wreck.
   k=min(1,i/6);ease=k*k;root.location.z-=.54*ease;root.location.x+=.36*ease;root.rotation_euler.y-=.5*ease;root.rotation_euler.x+=.11*ease
   root.location -= (sc.camera.matrix_world.to_3x3()@Vector((1,0,0)))*(.14*ease)
   if i>=5:wing.rotation_euler.x+=.14*min(1,(i-4)/3)
   falling_support(min(1,max(0,(i-1)/6))**1.5);prop.rotation_euler.x=i*2.13 if i<5 else -1.0
  for o in flash:o.hide_render=not(clip=='attack' and i in [3,5]);o.keyframe_insert('hide_render',frame=f)
  for o in supports:o.keyframe_insert('hide_render',frame=f)
  for o in [root,prop,wing]+supports:
   o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_euler',frame=f)
 # Loop propeller at a multiple of pi (two visually identical blades).
 if loop:
  for i in range(count+1):prop.rotation_euler.x=math.pi*7*i/count;prop.keyframe_insert('rotation_euler',frame=i+1)
 for o in sc.objects:
  if not o.animation_data or not o.animation_data.action:continue
  action=o.animation_data.action
  curves=list(action.fcurves) if hasattr(action,'fcurves') else [fc for layer in action.layers for strip in layer.strips for bag in getattr(strip,'channelbags',[]) for fc in bag.fcurves]
  for fc in curves:
   for kp in fc.keyframe_points:kp.interpolation='CONSTANT' if 'hide_render' in fc.data_path else 'LINEAR'
 sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps;sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/(clip+'.blend')))
 (M/(clip+'.json')).write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':source_hash},indent=2))
print('ANIMATED',requested or 'five clips / 40 frames')
