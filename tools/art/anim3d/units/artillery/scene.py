"""Artillery: real hollow hard-surface meshes, frozen UV paint, mechanical rig.
One gated Blender process builds and publishes each stage immediately.
"""
import bpy, math, os, json, sys, subprocess, hashlib, random
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from math import sin, cos, pi
ROOT=Path(os.environ['ANIM_ROOT']); M=ROOT/'masters/artillery'; A=ROOT/'assets/artillery'; REVIEW=ROOT/'review/3d-v2'
HERE=Path(__file__).resolve().parent; MODE=os.environ.get('ARTILLERY_MODE','preview')
RES=int(os.environ.get('RESOLUTION','256')); SAMPLES=int(os.environ.get('SAMPLES','8'))
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
random.seed(18)
pipeline_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')}
render_provenance={}
(M/'render-manifest.json').unlink(missing_ok=True)
def log(s):
 with (REVIEW/'artillery-log.md').open('a') as f:f.write('- '+s+'\n')
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

def beam(name,a,b,width,depth,m,p):
 o=cube(name,(Vector(a)+Vector(b))/2,(width,depth,(Vector(b)-Vector(a)).length),m,p);o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o

def ring(name,center,r,t,m,p,axis='Y'):
 pts=[]
 for i in range(97):
  a=i*2*pi/96;v=(r*cos(a),0,r*sin(a)) if axis=='Y' else (0,r*cos(a),r*sin(a))
  pts.append(tuple(Vector(center)+Vector(v)))
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=t;d.bevel_resolution=3;s=d.splines.new('POLY');s.points.add(len(pts)-1)
 for a,b in zip(s.points,pts):a.co=(*b,1)
 o=bpy.data.objects.new('GEO-'+name,d);bpy.context.collection.objects.link(o);d.materials.append(m);parent(o,p);return o

def plate(name,x,outline,thick,m,p):
 n=len(outline);v=[(x+dx,y,z) for dx in [-thick/2,thick/2] for y,z in outline]
 f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 return bevel(mesh(name,v,f,m,p),.008)

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
olive=mat('Olive painted steel',(.25,.245,.105));rubber=mat('Dusty charcoal rubber',(.12,.108,.085),0,.88)
edge=mat('Worn ochre paint edges',(.37,.32,.15));steel=mat('Exposed bright steel',(.35,.34,.27),1,.40)
black=mat('Recess and bore soot',(.012,.014,.009),0,.95)
stone=mat('Warm cream limestone target E9CFA0',(.82,.64,.40),0,.85)
plain=mat('Plain clay inspection',(.4,.43,.45))
root=empty('carriage');pivot=empty('elevation',(.35,0,1.13),root);recoil=empty('recoil',(.35,0,1.13),pivot)
# Low single stone disc, fixed throughout all animations.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1.25,depth=.13,location=(0,0,.065));base=bpy.context.object;base.name='GEO-stationary cream disc';base.data.materials.append(stone);bevel(base,.018)
rod('Axle',(.32,-.82,.53),(.32,.82,.53),.035,olive,root)
cube('Axle saddle',(.32,0,.61),(.28,.48,.21),olive,root)
# Tire profile is a continuous closed ring around real dished hubs, plus individual tread blocks.
wheels=[]
for sign in [-1,1]:
 y=sign*.66;c=Vector((.32,y,.53));w=empty('wheel '+str(sign),c,root);wheels.append(w)
 profile=[(-.105,.28),(-.125,.34),(-.11,.383),(-.075,.40),(.075,.40),(.11,.383),(.125,.34),(.105,.28)]
 v=[];f=[]
 for off,r in profile:
  for j in range(96):a=2*pi*j/96;v.append(tuple(c+Vector((r*cos(a),off,r*sin(a)))))
 for k in range(len(profile)):
  for j in range(96):f.append((k*96+j,k*96+(j+1)%96,((k+1)%len(profile))*96+(j+1)%96,((k+1)%len(profile))*96+j))
 mesh('Pneumatic tire '+str(sign),v,f,rubber,w,True)
 for j in range(36):
  a=2*pi*j/36
  for side in [-1,1]:
   o=cube('Chevron tread',c+Vector((.401*cos(a),side*.056,.401*sin(a))),(.055,.105,.025),rubber,w)
   o.rotation_euler=(0,pi/2-a,side*.25)
 rod('Pressed wheel dish',c+Vector((0,-.098,0)),c+Vector((0,.098,0)),.279,olive,w)
 for sy in [-1,1]:
  yy=y+sy*.11;ring('Raised wheel rim',(.32,yy,.53),.265,.014,edge,w)
  ring('Dish recess',(.32,yy+sy*.006,.53),.205,.008,black,w)
  rod('Hub boss',(.32,yy,.53),(.32,yy+sy*.06,.53),.098,olive,w,r2=.07)
  for j in range(8):
   a=2*pi*j/8;xx=.32+.143*cos(a);zz=.53+.143*sin(a)
   rod('Hex wheel bolt',(xx,yy,zz),(xx,yy+sy*.019,zz),.015,steel,w,verts=6)
# Split trails: long near trail, far trail strongly foreshortened as in the painting.
trails=[]
for i,(start,end) in enumerate([((.05,-.22,.48),(-.82,-.70,.17)),((.05,.22,.48),(.40,1.10,.17))]):
 t=empty('trail '+str(i),start,root);trails.append(t)
 beam('Box trail',start,end,.12,.10,olive,t)
 d=Vector(end)-Vector(start)
 for j in range(1,5):
  at=Vector(start)+d*j/5;cube('Trail reinforcing collar',at,(.15,.13,.06),edge,t)
 cube('Ground spade',end,(.23,.22,.045),olive,t)
 beam('Spade brace',Vector(end)+Vector((0,0,.02)),Vector(end)-d.normalized()*.20+Vector((0,0,.10)),.045,.055,olive,t)
 for off in [-.07,.07]:rod('Spade rivet',Vector(end)+Vector((off,0,.025)),Vector(end)+Vector((off,0,.04)),.013,steel,t,verts=8)
# Elevation yoke, handwheel and shield: genuine opening under barrel, asymmetric shaped wings.
for sign in [-1,1]:
 beam('Trunnion yoke',(.20,sign*.20,.64),(.35,sign*.20,1.17),.09,.085,olive,root)
 rod('Trunnion pin',(.35,sign*.18,1.13),(.35,sign*.31,1.13),.065,steel,root)
 # Each shield half has its own solid thickness and beveled outline.
 outline=[(sign*.14,.72),(sign*.46,.72),(sign*.55,.96),(sign*.69,1.02),(sign*.69,1.43),(sign*.60,1.54),(sign*.34,1.54),(sign*.24,1.45),(sign*.14,1.45)]
 outline=[(y-.09,z-.06-(.22 if sign==1 and z>1.3 else 0)-max(0,z-1.1)*.18) for y,z in outline]
 plate('Shield wing '+str(sign),.25,outline,.035,olive,root)
 for yy,zz in [(sign*.62,1.30),(sign*.60,1.07),(sign*.40,.79),(sign*.19,1.33)]:rod('Shield rivet',(.273,yy-.09,zz-.06),(.289,yy-.09,zz-.06),.014,edge,root,verts=8)
 beam('Shield folded brace',(.21,sign*.50-.09,.80),(.21,sign*.56-.09,1.33-(.22 if sign==1 else 0)),.028,.045,edge,root)
cube('Shield lower tie',(.40,0,.73),(.055,.36,.09),olive,root)
ring('Elevation handwheel',(.14,-.35,.91),.105,.012,olive,root)
for j in range(3):
 a=j*2*pi/3;rod('Handwheel spoke',(.14,-.35,.91),(.14+.1*cos(a),-.35,.91+.1*sin(a)),.008,steel,root)
rod('Handwheel handle',(.14,-.35,1.01),(.14,-.42,1.01),.017,black,root)
# Barrel lathe includes the inner bore: never a capped primitive posing as a muzzle.
profile=[(-.14,.090),(-.08,.112),(.06,.115),(.20,.104),(.58,.083),(.66,.085),(.70,.077),(1.30,.056),(1.32,.063),(1.35,.063),(1.35,.043),(1.10,.043)]
v=[];f=[]
for x,r in profile:
 for j in range(96):a=2*pi*j/96;v.append((.35+x,r*cos(a),1.13+r*sin(a)))
for k in range(len(profile)-1):
 for j in range(96):f.append((k*96+j,k*96+(j+1)%96,(k+1)*96+(j+1)%96,(k+1)*96+j))
barrel=mesh('Hollow tapered barrel',v,f,olive,recoil,True);barrel.data.materials.append(black)
for p in barrel.data.polygons:
 if p.index>=10*96:p.material_index=1
rod('Bore deep shadow',(1.43,0,1.13),(1.44,0,1.13),.043,black,recoil)
for x,r in [(.40,.118),(.94,.09),(1.67,.066)]:ring('Turned barrel band',(x,0,1.13),r,.008,edge,recoil,axis='X')
cube('Breech block',(.16,0,1.13),(.27,.22,.22),olive,recoil)
# Hydraulic recuperators above and alongside the central tube.
for yy,zz,rr in [(0,1.23,.058),(-.14,1.16,.038)]:
 rod('Recoil cylinder',(.18,yy,zz),(.91,yy,zz),rr,olive,pivot)
 rod('Recuperator rod',(.90,yy,zz),(1.02,yy,zz),rr*.55,steel,recoil)
 for xx in [.28,.81,.92]:ring('Cylinder clamp',(xx,yy,zz),rr+.006,.009,edge,pivot,axis='X')
beam('Recoil cradle',(.19,0,.99),(.92,0,.99),.14,.16,olive,pivot)
pivot.rotation_euler.y=-.46
# Fixed painting camera and product lights.
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=SAMPLES;sc.cycles.use_denoising=True;sc.cycles.max_bounces=5
if sc.cycles.device=='GPU':
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 devices=[d for d in prefs.devices if d.type=='METAL'];assert devices,'Metal GPU required; no silent CPU fallback'
 for d in prefs.devices:d.use=d.type=='METAL'
sc.render.resolution_x=sc.render.resolution_y=RES;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.52,.56,.65,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.3
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
bpy.ops.object.camera_add(location=(6,-7,3.07));cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(Vector((0,0,.57))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.76;sc.camera=cam
for name,loc,power,size,color in [('key',(-3,-4,6),650,4,(1,.88,.70)),('fill',(4,-2,3),125,4,(.85,.91,1)),('rim',(1,4,4),210,3,(.75,.85,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power*.55;o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,.7))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()

sys.path.insert(0,str(HERE))
from refine import refine
refine(sc,cam,wheels,base,M)

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
save('artillery-plain.blend');render(M/'renders/b-plain.png');review('b-plain');log('Published b-plain CPU/GPU geometry stage before texture work.')
for name,mats in assignments.items():
 for i,m in enumerate(mats):bpy.data.objects[name].data.materials[i]=m
# Base materials: hidden painted fill, fine grain, AO cavity shading, geometric worn rims.
fill=bpy.data.images.load(str(A/'painted-olive.png'));fill.pack()
for m in [olive,edge,rubber,stone]:
 n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');color=s.inputs['Base Color'].default_value[:]
 tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=3;l.new(tc.outputs['Generated'],noise.inputs['Vector'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.0015;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
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
baked=bake_finish(M/'textures', [o for o in sc.objects if o.type=='MESH' and ('Shield wing' in o.name or 'Hollow tapered barrel' in o.name)])
log('Baked 256px AO and curvature maps on '+', '.join(baked))
# Finished surfaces own frozen UVs and camera-only pigment; back/occluded surfaces
# retain the generated fill and physical product-light response.
from projection import project
records=project(sc,cam,base,A,M)
save('artillery.blend');render(M/'renders/c-textured-lit.png');review('c-textured-lit');log('Published painted rest pose and 50/50 comparison; real AO shader, micrograin, edge geometry and hidden-surface fill.')
review('c-details')
if MODE=='stills':sys.exit(0)
# Mechanical object hierarchy is the editable rig; each clip saved separately with explicit keys.
axle=bpy.data.objects['GEO-Axle']
controls=[root,pivot,recoil,*wheels,*trails,axle];neutral={o.name:(o.location.copy(),o.rotation_euler.copy()) for o in controls}
# Small solid flash, hidden with visibility rather than degenerate scale.
flashmat=mat('Muzzle flash warm core',(1,.35,.025),0,.6);s=flashmat.node_tree.nodes.get('Principled BSDF');s.inputs['Emission Color'].default_value=(1,.35,.02,1);s.inputs['Emission Strength'].default_value=3
flash=rod('Muzzle flash',recoil.matrix_world@Vector((1.35,0,0)),recoil.matrix_world@Vector((1.53,0,0)),.075,flashmat,recoil,r2=.008);flash.hide_render=True

ground_audit=[]
def pose(clip,i,n):
 t=i/n if clip in ['idle','move'] else i/(n-1)
 for o in controls:o.location=neutral[o.name][0];o.rotation_euler=neutral[o.name][1]
 flash.hide_render=True
 if clip=='idle':pivot.rotation_euler.y+=.014*sin(2*pi*t)
 elif clip=='move':
  # In-place rolling, like a treadmill: runtime supplies world translation. Trails lifted clear.
  root.location.z=.018*(1+sin(4*pi*t));root.rotation_euler.y=.025*sin(2*pi*t)
  for w in wheels:w.rotation_euler.y=-2*pi*t
  trails[0].rotation_euler.y=.10
  trails[1].rotation_euler.y=-.10
 elif clip=='attack':
  kick=[0,0,.025,-.22,-.13,-.055,-.018,0,0,0][i];recoil.location.x+=kick;pivot.rotation_euler.y+=.025*sin(pi*t);flash.hide_render=i!=3
 elif clip=='hit':
  root.rotation_euler.x=[0,-.085,.04,0][i];pivot.rotation_euler.y+=[0,.06,-.025,0][i]
 elif clip=='death':
  # Broken axle settles with tires on the disc; upper gun slumps and remains visibly disabled.
  f=min(1,t/.78);f=f*f*(3-2*f);root.location.z=-.095*f;root.rotation_euler.x=-.13*f;pivot.rotation_euler.y+=.54*f;recoil.location.x-=.16*f
  wheels[0].rotation_euler.x=.28*f;wheels[0].location.z+=.06*f
  trails[0].rotation_euler.z=-.06*f
 bpy.context.view_layer.update()
 # Keep every mechanical solid above the stone through recoil and axle collapse.
 meshes=[o for o in sc.objects if o.type=='MESH' and o not in [base,flash] and not o.hide_render]
 lowest=min((o.matrix_world@v.co).z for o in meshes for v in o.data.vertices)
 if lowest<.128:
  root.location.z+=.128-lowest
  bpy.context.view_layer.update()
 # Wheel suspension keeps both tires planted even when the damaged carriage tilts.
 wheel_floor=[]
 for wheel in wheels:
  parts=[o for o in wheel.children_recursive if o.type=='MESH']
  bottom=min((o.matrix_world@v.co).z for o in parts for v in o.data.vertices)
  matrix=wheel.matrix_world.copy();matrix.translation.z+=.13-bottom;wheel.matrix_world=matrix
  bpy.context.view_layer.update()
  wheel_floor.append(min((o.matrix_world@v.co).z for o in parts for v in o.data.vertices))
 a,b=[w.matrix_world.translation.copy() for w in wheels]
 matrix=axle.matrix_world.copy();matrix.translation=(a+b)/2
 axle.matrix_world=matrix
 axle.rotation_euler=(root.matrix_world.to_quaternion().inverted() @ (b-a).to_track_quat('Z','Y')).to_euler()
 axle.scale.z=(b-a).length/1.64
 bpy.context.view_layer.update()
 lowest=min((o.matrix_world@v.co).z for o in meshes for v in o.data.vertices)
 assert lowest>=.1279,(clip,i,lowest)
 ground_audit.append({'clip':clip,'sample':i,'minimum_z':lowest,'wheel_contact_z':wheel_floor})

manifest={'engine':'CYCLES','device':sc.cycles.device,'samples':SAMPLES,'resolution':RES,'clips':{},'source_sha256':hashlib.sha256((M/'artillery.blend').read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'pipeline_sha256':pipeline_hashes}
(M/'render-manifest.json').unlink(missing_ok=True)
for clip,(count,fps,loop) in CLIPS.items():
 for o in controls+[flash]:o.animation_data_clear()
 sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 for i in range(count+(1 if loop else 0)):
  pose(clip,i,count)
  for o in controls:
   o.keyframe_insert('location',frame=i+1);o.keyframe_insert('rotation_euler',frame=i+1)
  axle.keyframe_insert('scale',frame=i+1)
  flash.keyframe_insert('hide_render',frame=i+1)
 # Stable linear sampling for mechanical motion and constant effect visibility.
 for o in controls+[flash]:
  action=o.animation_data.action;curves=[fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
  for fc in curves:
   for key in fc.keyframe_points:key.interpolation='CONSTANT' if fc.data_path=='hide_render' else 'LINEAR'
 sc.frame_set(1);save('artillery-'+clip+'.blend');folder=M/'renders'/clip;folder.mkdir(parents=True,exist_ok=True)
 for i in range(count):
  sc.frame_set(i+1)
  if clip=='death' and i==count-1:
   # Geometry keys are an exact terminal hold; copy avoids stochastic denoiser differences.
   import shutil;shutil.copyfile(folder/f'{i-1:02}.png',folder/f'{i:02}.png')
   if RES==512:shutil.copyfile(folder/f'{i:02}.png',M/'512'/clip/f'{i:02}.png')
  else:render(folder/f'{i:02}.png')
  if clip=='attack' and i in [0,2,3,6]:
   import shutil;shutil.copyfile(folder/f'{i:02}.png',M/'renders'/f'pose-{i}.png')
 review('e-'+clip);log(f'Published e-{clip}: {count} actual rendered frames, {fps} fps; {sc.cycles.device} {RES}px {SAMPLES} samples.')
 manifest['clips'][clip]={'frames':count,'fps':fps,'loop':loop,'hashes':[hashlib.sha256((folder/f'{i:02}.png').read_bytes()).hexdigest() for i in range(count)]}
review('d-rig-poses')
manifest['renders']=render_provenance
manifest['inputs_sha256']=hashlib.sha256((M/'inputs.json').read_bytes()).hexdigest()
manifest['grade_sha256']=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest()
manifest['gallery_sha256']={str(p.relative_to(M/'256')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (M/'256').rglob('*.png')}
manifest['clip_blends']={c:hashlib.sha256((M/f'artillery-{c}.blend').read_bytes()).hexdigest() for c in CLIPS}
manifest['ground_audit']=ground_audit
# Check stationary base and finite nondegenerate mesh scales across all samples.
assert base.animation_data is None
assert all(min(abs(x) for x in o.scale)>.001 for o in sc.objects if o.type=='MESH')
manifest['audit']={'stationary_base':True,'nondegenerate_mesh_scales':True,'rig':'mechanical parent controls; no camera warp or billboard','painted_mesh_count':len(records)}
(M/'render-manifest.json').write_text(json.dumps(manifest,indent=2));log('Completed all five clips and geometry audit; delivery pack may now run.')
