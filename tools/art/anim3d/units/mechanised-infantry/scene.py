"""Artillery: real hollow hard-surface meshes, frozen UV paint, mechanical rig.
One gated Blender process builds and publishes each stage immediately.
"""
import bpy, math, os, json, sys, subprocess, hashlib, random
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from math import sin, cos, pi
ROOT=Path(os.environ['ANIM_ROOT']); M=ROOT/'masters/mechanised-infantry'; A=ROOT/'assets/mechanised-infantry'; REVIEW=ROOT/'review/3d-v2'
HERE=Path(__file__).resolve().parent; MODE=os.environ.get('MECHANISED_INFANTRY_MODE','preview')
RES=int(os.environ.get('RESOLUTION','256')); SAMPLES=int(os.environ.get('SAMPLES','8'))
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
random.seed(18)
pipeline_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')}
render_provenance={}
(M/'render-manifest.json').unlink(missing_ok=True)
def log(s):
 with (REVIEW/'mechanised-infantry-log.md').open('a') as f:f.write('- '+s+'\n')
 print(s,flush=True)
def parent(o,p):
 bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=p;o.matrix_world=w;return o

def empty(name,loc=(0,0,0),p=None):
 o=bpy.data.objects.new('RIG-'+name,None);bpy.context.collection.objects.link(o);o.location=loc
 if p:parent(o,p)
 return o

def mat(name,color,metal=0,rough=.7):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
 s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
 return m

def bevel(o,w=.008):
 b=o.modifiers.new('Worn rounded edges','BEVEL');b.width=w;b.segments=3
 return o

def mesh(name,v,f,m,p=None,smooth=False):
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new('GEO-'+name,me);bpy.context.collection.objects.link(o);me.materials.append(m)
 for face in me.polygons:face.use_smooth=smooth
 if p:parent(o,p)
 return o

def cube(name,loc,size,m,p=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name='GEO-'+name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);bevel(o)
 if p:parent(o,p)
 return o

def rod(name,a,b,r,m,p=None,r2=None,verts=48):
 d=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r if r2 is None else r2,depth=d.length,location=(Vector(a)+Vector(b))*.5);o=bpy.context.object;o.name='GEO-'+name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(m);bevel(o,.003)
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 if p:parent(o,p)
 return o

def ring(name,center,r,t,m,p,axis='Y'):
 pts=[]
 for i in range(97):
  a=i*2*pi/96;v=(r*cos(a),0,r*sin(a)) if axis=='Y' else (0,r*cos(a),r*sin(a))
  pts.append(tuple(Vector(center)+Vector(v)))
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=t;d.bevel_resolution=3;s=d.splines.new('POLY');s.points.add(len(pts)-1)
 for a,b in zip(s.points,pts):a.co=(*b,1)
 o=bpy.data.objects.new('GEO-'+name,d);bpy.context.collection.objects.link(o);d.materials.append(m);parent(o,p);return o

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
olive=mat('Olive painted steel',(.25,.245,.105));rubber=mat('Dusty charcoal rubber',(.12,.108,.085),0,.88)
edge=mat('Worn ochre paint edges',(.37,.32,.15));steel=mat('Exposed bright steel',(.35,.34,.27),1,.40)
black=mat('Recess and bore soot',(.012,.014,.009),0,.95)
stone=mat('Warm cream limestone target E9CFA0',(.815,.624,.352),0,.85)
plain=mat('Plain clay inspection',(.4,.43,.45))
sys.path.insert(0,str(HERE))
from model import build
globals().update(build(globals()))
# Product lighting, safe CPU or explicitly verified Metal GPU.
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=SAMPLES;sc.cycles.use_denoising=True;sc.cycles.max_bounces=5
if sc.cycles.device=='GPU':
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 devices=[d for d in prefs.devices if d.type=='METAL'];assert devices,'Metal GPU required; no silent CPU fallback'
 for d in prefs.devices:d.use=d.type=='METAL'
sc.render.resolution_x=sc.render.resolution_y=RES;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.52,.56,.65,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.3
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
for name,loc,power,size,color in [('key',(-3,-4,6),650,4,(1,.88,.70)),('fill',(4,-2,3),125,4,(.85,.91,1)),('rim',(1,4,4),210,3,(.75,.85,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power*.55;o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,.7))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()

def save(name):bpy.ops.wm.save_as_mainfile(filepath=str(M/name))
def render(path):
 assert sc.camera and sc.camera.type=='CAMERA'
 path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 render_provenance[str(path.relative_to(M/'renders'))]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'resolution':RES,'engine':'CYCLES','device':sc.cycles.device,'samples':SAMPLES}
 if RES==512:
  import shutil
  dest=M/'512'/path.relative_to(M/'renders');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
def review(stage):
 subprocess.run([str(ROOT/'venv/bin/python'),str(HERE/'review.py'),stage],check=True)
# Post the plain stage before texturing; retain actual material assignments separately.
assignments={o.name:list(o.data.materials) for o in sc.objects if o.type=='MESH'}
for name in assignments:
 o=bpy.data.objects[name]
 if o!=base:
  for i in range(len(o.data.materials)):o.data.materials[i]=plain
save('mechanised-infantry-plain.blend');render(M/'renders/b-plain.png');review('b-plain')
neutral_camera=cam.matrix_world.copy()
for label,position in [('side',(0,-8,2.5)),('rear',(6,7,3.5))]:
 cam.location=position;cam.rotation_euler=(Vector((0,0,.95))-cam.location).to_track_quat('-Z','Y').to_euler()
 render(M/'renders'/f'b-{label}.png')
cam.matrix_world=neutral_camera
review('b-multiview');log('Published b-plain CPU/GPU geometry stage before texture work.')
for name,mats in assignments.items():
 for i,m in enumerate(mats):bpy.data.objects[name].data.materials[i]=m
# Base materials: hidden painted fill, fine grain, AO cavity shading, geometric worn rims.
fill=bpy.data.images.load(str(A/'painted-olive.png'));fill.pack()
for m in [olive,edge,rubber,stone]:
 n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');color=s.inputs['Base Color'].default_value[:]
 tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=55 if m==stone else 95;noise.inputs['Detail'].default_value=3;l.new(tc.outputs['Generated'],noise.inputs['Vector'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.005 if m==stone else .0015;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=tuple(c*.7 for c in color[:3])+(1,);ramp.color_ramp.elements[1].color=tuple(min(1,c*1.13) for c in color[:3])+(1,);l.new(noise.outputs['Fac'],ramp.inputs[0]);source=ramp.outputs[0]
 if m==olive:
  tex=n.new('ShaderNodeTexImage');tex.image=fill;tex.projection='BOX';tex.projection_blend=.25;l.new(tc.outputs['Generated'],tex.inputs['Vector']);source=tex.outputs['Color']
 ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.09
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.32;l.new(source,mix.inputs[1]);l.new(ao.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
# Warm stone pigment is camera-only, so real product lights still cast contact shadows.
n=stone.node_tree.nodes;l=stone.node_tree.links;s=n.get('Principled BSDF')
g=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(g.outputs['Normal'],sep.inputs[0])
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.15;ramp.color_ramp.elements[0].color=(.81,.55,.31,1);ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=(.98,.78,.54,1);l.new(sep.outputs['Z'],ramp.inputs[0])
pigment=n.new('ShaderNodeBsdfPrincipled');pigment.inputs['Base Color'].default_value=(0,0,0,1);pigment.inputs['Specular IOR Level'].default_value=0;ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.12
contact=n.new('ShaderNodeMixRGB');contact.blend_type='MULTIPLY';contact.inputs[0].default_value=.32;l.new(ramp.outputs['Color'],contact.inputs[1]);l.new(ao.outputs['Color'],contact.inputs[2]);l.new(contact.outputs[0],pigment.inputs['Emission Color']);pigment.inputs['Emission Strength'].default_value=1
ray=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.72;l.new(ray.outputs['Is Camera Ray'],weight.inputs[0])
mix=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],mix.inputs[0]);l.new(s.outputs[0],mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
# Genuine surface bakes supplement shader contact AO and physical worn edges.
sys.path.insert(0,str(HERE))
from bake import bake_finish
baked=bake_finish(M/'textures', [o for o in sc.objects if o.type=='MESH' and any(k in o.name for k in ['Armoured hull','Turret shell','Lowered loading ramp'])])
log('Baked 256px AO and curvature maps on '+', '.join(baked))
# Finished surfaces own frozen UVs and camera-only pigment; back/occluded surfaces
# retain the generated fill and physical product-light response.
from projection import project
records=project(sc,cam,base,A,M)
from finish import finish
finish(sc,cam,base,A)
save('mechanised-infantry.blend');render(M/'renders/c-textured-lit.png');review('c-textured-lit');log('Published painted rest pose and 50/50 comparison; real AO shader, micrograin, edge geometry and hidden-surface fill.')
review('c-details')
if MODE=='stills':sys.exit(0)
# Mechanical object hierarchy is the editable rig; separate saved keyed clip masters.
controls=[root,upper,turn,lift,*wheels,soldier['group']]
neutral={o.name:(o.location.copy(),o.rotation_euler.copy()) for o in controls}
# Brief muzzle flash uses keyed visibility and a full-depth mesh.
flashmat=mat('Muzzle flash',(1,.36,.025),0,.7)
flash=rod('Autocannon flash',muzzle,muzzle+right*.055,.027,flashmat,lift,r2=.008,verts=16)
flash.hide_render=True;effects=[flash]
for o in effects:neutral[o.name]=(o.location.copy(),o.rotation_euler.copy())
controls+=effects
rig=soldier['rig'];rigloc=rig.location.copy()
from retarget import apply_matrices
ground_audit=[]
def pose(clip,i,n):
 t=i/n if clip in ['idle','move'] else i/(n-1)
 for o in controls:o.location=neutral[o.name][0];o.rotation_euler=neutral[o.name][1]
 for o in effects:o.hide_render=True
 if clip=='idle':
  upper.location.z=.0025*sin(4*pi*t);turn.rotation_euler.z=.009*sin(2*pi*t)
 elif clip=='move':
  # Fixed token treadmill: one common travel distance, each wheel rotates distance/radius.
  travel=2*pi*wheels[0]['radius']*t
  upper.location.z=.007*sin(4*pi*t);upper.rotation_euler.y=.004*sin(2*pi*t)
  for w in wheels:w.rotation_euler.y=-travel/w['radius']
 elif clip=='attack':
  lift.rotation_euler.y+=[0,-.012,-.025,-.028,-.018,-.010,-.004,0,0,0][i]
  upper.location.x+=[0,0,0,.012,.006,0,.008,.004,0,0][i]
  turn.rotation_euler.z=.012*sin(pi*t)
  if i in [3,4,6]:
   for o in effects:o.hide_render=False
 elif clip=='hit':
  upper.rotation_euler.x=[0,-.025,.014,0][i];lift.rotation_euler.y=[0,.04,-.02,0][i]
 elif clip=='death':
  # Suspension and turret collapse into a planted wreck, last two samples hold.
  f=min(1,t/.78);f=f*f*(3-2*f)
  upper.location.z=-.07*f;upper.rotation_euler.x=-.055*f
  lift.rotation_euler.y=-.45*f;turn.rotation_euler.z=-.11*f
  wheels[1].rotation_euler.x=.09*f;wheels[2].rotation_euler.x=.06*f
  # Captured backward fall clears the ramp into the foreground. This is a
  # whole-character placement correction; donor foot rotations remain intact.
  soldier['group'].location+=(Vector((view.x,view.y,0)).normalized()*.80-right*.10)*f
 bpy.context.view_layer.update()
 # Real tire mesh minima seat all eight wheels on the base, including damaged suspension.
 floor=[]
 for wheel in wheels:
  parts=[o for o in wheel.children_recursive if o.type=='MESH']
  bottom=min((o.matrix_world@v.co).z for o in parts for v in o.data.vertices)
  wheel.location+=wheel.parent.matrix_world.to_3x3().inverted()@Vector((0,0,.15-bottom))
  bpy.context.view_layer.update();floor.append(min((o.matrix_world@v.co).z for o in parts for v in o.data.vertices))
 vehicle_min=min((o.matrix_world@v.co).z for o in root.children_recursive if o.type=='MESH' and o not in effects for v in o.data.vertices)
 # Grounded wheel contact is measured independently; hull clearance is reviewed.

 ground_audit.append({'minimum_vehicle_z':vehicle_min,'clip':clip,'sample':i,'minimum_z':min(floor),'wheel_contact_z':floor,'travel':2*pi*wheels[0]['radius']*t if clip=='move' else 0,'wheel_angle':[w.rotation_euler.y for w in wheels]})

 # Soldier animation samples come from open motion; attack retains the rifle guard.
 rig.location=rigloc.copy()
 if clip=='attack':
  apply_matrices(rig,soldier['neutral'])
  p=rig.pose.bones['spine_03'];p.rotation_mode='XYZ';p.rotation_euler.x+=.025*sin(3*pi*t)
 else:
  sample=24+round(min(t,.8889 if clip=='death' else 1)*48)
  motion=soldier['motion'][clip][sample]
  rig.location=rigloc+motion['root'];apply_matrices(rig,motion['matrices'])
 bpy.context.view_layer.update()
 # Vertical contact only: preserve donor leg/foot rotations and horizontal stride.
 deps=bpy.context.evaluated_depsgraph_get()
 feet=[o for o in soldier['objects'] if 'boot sole' in o.name]
 if clip=='death':feet=[o for o in soldier['objects'] if o.type=='MESH']
 lows=[]
 for o in feet:
  ev=o.evaluated_get(deps);me=ev.to_mesh();lows.extend((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
 if lows:rig.location.z+=(.15-min(lows))/soldier['group'].scale.z
 bpy.context.view_layer.update()

manifest={'engine':'CYCLES','device':sc.cycles.device,'samples':SAMPLES,'resolution':RES,'clips':{},'source_sha256':hashlib.sha256((M/'mechanised-infantry.blend').read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'pipeline_sha256':pipeline_hashes}
(M/'render-manifest.json').unlink(missing_ok=True)
for clip,(count,fps,loop) in CLIPS.items():
 for o in controls:o.animation_data_clear()
 rig.animation_data_clear()
 sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 for i in range(count+(1 if loop else 0)):
  pose(clip,i,count)
  for o in controls:
   o.keyframe_insert('location',frame=i+1);o.keyframe_insert('rotation_euler',frame=i+1)
  for o in effects:o.keyframe_insert('hide_render',frame=i+1)
  rig.keyframe_insert('location',frame=i+1)
  for bone in rig.pose.bones:
   bone.keyframe_insert('location',frame=i+1);bone.keyframe_insert('rotation_quaternion' if bone.rotation_mode=='QUATERNION' else 'rotation_euler',frame=i+1);bone.keyframe_insert('scale',frame=i+1)
 for o in controls+[rig]:
  action=o.animation_data.action
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:key.interpolation='CONSTANT' if fc.data_path=='hide_render' else 'LINEAR'
 sc.frame_set(1);save('mechanised-infantry-'+clip+'.blend');folder=M/'renders'/clip;folder.mkdir(parents=True,exist_ok=True)
 for i in range(count):
  sc.frame_set(i+1)
  if clip=='death' and i==count-1:
   import shutil;shutil.copyfile(folder/f'{i-1:02}.png',folder/f'{i:02}.png')
   if RES==512:shutil.copyfile(folder/f'{i:02}.png',M/'512'/clip/f'{i:02}.png')
  else:render(folder/f'{i:02}.png')
  if clip=='attack' and i in [0,2,3,6]:
   import shutil;shutil.copyfile(folder/f'{i:02}.png',M/'renders'/f'pose-{i}.png')
 review('e-'+clip);log(f'Published e-{clip}: {count} actual rendered frames, {fps} fps; {sc.cycles.device} {RES}px {SAMPLES} samples.')
 manifest['clips'][clip]={'frames':count,'fps':fps,'loop':loop,'hashes':[hashlib.sha256((folder/f'{i:02}.png').read_bytes()).hexdigest() for i in range(count)]}
 if clip=='move':
  # Required top/front contact sheet: actual rigid wheel geometry, no projected body paint.
  savedcam=cam.matrix_world.copy();savedscale=cam.data.ortho_scale
  hidden={o.name:o.hide_render for o in sc.objects if o.type in ('MESH','CURVE')}
  footcenter=soldier['group'].matrix_world.translation
  for o in sc.objects:
   if o.type in ('MESH','CURVE'):o.hide_render=not ('boot' in o.name)
  front=soldier['group'].matrix_world.to_quaternion()@Vector((0,-4,.5))
  for viewname,loc in [('top',footcenter+Vector((0,0,4))),('front',footcenter+front)]:
   cam.location=loc;cam.rotation_euler=(footcenter+Vector((0,0,.12))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.9
   for i in range(count):sc.frame_set(i+1);render(M/'renders'/'feet'/f'{viewname}-{i:02}.png')
  cam.matrix_world=savedcam;cam.data.ortho_scale=savedscale
  for name,h in hidden.items():bpy.data.objects[name].hide_render=h
  review('g-feet-check')
review('d-rig-poses')
manifest['renders']=render_provenance
manifest['inputs_sha256']=hashlib.sha256((M/'inputs.json').read_bytes()).hexdigest()
manifest['grade_sha256']=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest()
manifest['gallery_sha256']={str(p.relative_to(M/'256')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (M/'256').rglob('*.png')}
manifest['clip_blends']={c:hashlib.sha256((M/f'mechanised-infantry-{c}.blend').read_bytes()).hexdigest() for c in CLIPS}
manifest['ground_audit']=ground_audit
assert base.animation_data is None
assert all(min(abs(x) for x in o.scale)>.001 for o in sc.objects if o.type=='MESH')
manifest['audit']={'stationary_base':True,'nondegenerate_mesh_scales':True,'rig':'mechanical parent controls; closed bodywork; no billboard','painted_mesh_count':len(records),'wheel_radii':[w['radius'] for w in wheels]}
(M/'render-manifest.json').write_text(json.dumps(manifest,indent=2));log('Completed all five clips and wheel contact audit; delivery pack may now run.')
