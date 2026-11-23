"""Closed hard-surface walker, registered in the reference camera's basis."""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import MASTER, ASSETS, log
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
E=.215; UP=Vector((0,math.sin(E),math.cos(E))); VIEW=Vector((0,-math.cos(E),math.sin(E))); TARGET=Vector((0,0,1.159))
def screen(x,y,d=0): return Vector(((x-128)/50,0,0))+UP*((128-y)/50)+VIEW*d+TARGET
def atz(x,y,z): return screen(x,y,(z-TARGET.z-UP.z*(128-y)/50)/VIEW.z)
def empty(name,pos=(0,0,0),parent=None):
 o=bpy.data.objects.new(name,None);sc.collection.objects.link(o);o.location=pos
 if parent: o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted()
 return o
def mat(name,color,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=.65;return m
olive=mat('MAT-armour painted dark olive',(.18,.165,.125));steel=mat('MAT-rubbed bright steel',(.46,.43,.37),1);dark=mat('MAT-joint cavities',(.045,.04,.032));stone=mat('MAT-cream stone E9CFA0',(.815,.624,.352));lens=mat('MAT-dark blue optical glass',(.035,.085,.10),1)
clay=mat('MAT-plain clay',(.48,.44,.37))
def finish(o,name,material,parent=None,bevel=.025):
 o.name='GEO-'+name;o.data.materials.append(material)
 bpy.context.view_layer.update()
 if parent: o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted()
 if bevel:
  b=o.modifiers.new('Machined edge roundover','BEVEL');b.width=bevel;b.segments=3
  b=o.modifiers.new('Weighted face normals','WEIGHTED_NORMAL')
 return o
def cube(name,pos,size,material=olive,parent=None,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,material,parent,bevel)
def cyl(name,a,b,r,material=steel,parent=None):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=(b-a).length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return finish(o,name,material,parent,.012)
def poly(name,points,depth,material=olive,parent=None):
 # Full-depth extruded armour, never an alpha silhouette card. Screen points
 # register only visible edges; side and rear surfaces are closed solid faces.
 front=[screen(*p) for p in points];back=[p-VIEW*depth for p in front];n=len(front)
 faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(front+back,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);sc.collection.objects.link(o)
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');o.select_set(False)
 return finish(o,name,material,parent,.018)
# Camera and one stationary cream base.
camdata=bpy.data.cameras.new('CAM-reference');cam=bpy.data.objects.new('CAM-reference',camdata);sc.collection.objects.link(cam);cam.location=TARGET+VIEW*15;cam.rotation_euler=(-VIEW).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=5.12;sc.camera=cam
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=2.32,depth=.32,location=(0,0,.16));base=finish(bpy.context.object,'Stationary cream disc',stone,bevel=.035)
# Chassis is an independent rigid transform; legs solve against its moving hips.
body=empty('RIG-chassis',(0,0,1.45));bpy.context.view_layer.update()
# Explicit six-face hull topology: each visible plane is an actual armour face.
verts=[screen(*p) for p in [(56,83,-.6),(139,80,-1.1),(197,97,.3),(125,112,1),(55,117,-.4),(121,136,1),(189,128,.4),(145,113,-1.1)]]
mesh=bpy.data.meshes.new('Hull six connected plates');mesh.from_pydata(verts,[],[(0,1,2,3),(0,3,5,4),(3,2,6,5),(1,0,4,7),(2,1,7,6),(4,5,6,7)]);mesh.update()
o=bpy.data.objects.new('Hull',mesh);sc.collection.objects.link(o);finish(o,'Main faceted hull',olive,body,.035)
bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');o.select_set(False)
# Turret ring, low tapering turret, sensors and short autocannon.
turret=empty('RIG-turret',screen(124,76,.1));turret.parent=body;turret.matrix_parent_inverse=body.matrix_world.inverted();bpy.context.view_layer.update()
# Vertical mechanical pedestal overlaps the hull deck and turret shell. The
# source's narrow screen-space gap must not become a physically floating turret.
cyl('Turret deck socket',(-.08,.12,1.72),(-.08,.12,2.11),.46,dark,body)
cyl('Turret slew ring',(-.08,.12,2.01),(-.08,.12,2.17),.50,dark,turret)
poly('Squat turret',[(83,72,.45),(89,57,.1),(107,50,-.2),(130,49,-.2),(153,59,.1),(156,76,.5),(142,81,.7),(103,80,.7)],.52,parent=turret)
poly('Turret cheek',[(88,56,.5),(105,56,.8),(101,77,.9),(82,73,.65)],.10,parent=turret)
poly('Turret crown hatch',[(108,47,.0),(128,48,-.1),(139,53,.1),(112,55,.3)],.09,parent=turret)
poly('Twin sensor housing',[(133,65,.92),(153,64,.9),(154,77,.95),(132,77,1.0)],.24,parent=turret)
for x in (138,148):
 p=screen(x,71,1.04);cyl('Sensor bezel',p,p+VIEW*.035,.071,steel,turret);cyl('Inset optical lens',p+VIEW*.036,p+VIEW*.042,.047,lens,turret)
recoil=empty('RIG-recoil',screen(147,57,.3));recoil.parent=turret;recoil.matrix_parent_inverse=turret.matrix_world.inverted();bpy.context.view_layer.update()
cyl('Autocannon breech',screen(137,57,.3),screen(150,57,.3),.10,olive,recoil)
cyl('Short autocannon',screen(149,57,.3),screen(171,58,.3),.045,steel,recoil)
cyl('Muzzle collar',screen(167,58,.3),screen(172,58,.3),.064,steel,recoil)
cyl('Dark recessed bore',screen(172,58,.3),screen(172.4,58,.3),.040,dark,recoil)
# Four independent closed mechanical limbs; no animal skeleton or borrowed dog motion.
legs=[]
for name,h,k,f in [('near-left',(108,116,1.61),(91,142,.95),(81,174,.43)),('far-left',(55,104,1.53),(36,127,.91),(34,153,.43)),('near-right',(197,114,1.60),(218,136,.95),(217,166,.43)),('far-right',(146,118,1.44),(147,133,.86),(151,146,.43))]:
 hip,knee,foot=[atz(*v) for v in (h,k,f)]
 upper=empty('RIG-upper-'+name,hip);lower=empty('RIG-lower-'+name,knee);shoe=empty('RIG-foot-'+name,foot);bpy.context.view_layer.update()
 upper.rotation_mode=lower.rotation_mode='QUATERNION'
 # Put mesh endpoints in world rest space and retain those exact transforms.
 delta=knee-hip
 if name=='near-left':
  normal=(VIEW-delta.normalized()*delta.normalized().dot(VIEW)).normalized();plane=(hip+knee)/2+normal*.23
  outline=[(89,106),(110,109),(114,119),(97,146),(74,138),(80,121)]
  points=[(x,y,normal.dot(plane-screen(x,y))/normal.dot(VIEW)) for x,y in outline]
  o=poly('Upper armour '+name,points,.43,olive,upper)
 else:
  o=cube('Upper armour '+name,(hip+knee)/2,(.43,.38,delta.length+.13),olive,None,.035);o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();bpy.context.view_layer.update();o.parent=upper;o.matrix_parent_inverse=upper.matrix_world.inverted()
 delta=foot-knee;o=cube('Lower shin '+name,(knee+foot)/2,(.42 if name=='near-left' else .32,.31,delta.length+.08),olive,None,.025);o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();bpy.context.view_layer.update();o.parent=lower;o.matrix_parent_inverse=lower.matrix_world.inverted()
 for label,p,par,rad in [('Hip',hip,upper,.175),('Knee',knee,lower,.13)]:
  cyl(label+' pin '+name,p-VIEW*.20,p+VIEW*.24,rad,dark,par);cyl(label+' cap '+name,p+VIEW*.24,p+VIEW*.265,rad*.8,steel,par)
 o=cube('Broad foot '+name,(foot.x,foot.y,.415),(.98 if name=='near-left' else .9 if name=='near-right' else .78,.58,.19),olive,shoe,.065)
 o=cube('Foot centre plate '+name,(foot.x,foot.y,.52),(.40,.46,.10),olive,shoe,.035)
 # Pistons have real rods and housings, rigidly following each shin.
 cyl('Hydraulic piston '+name,knee+Vector((.13,0,0)),foot+Vector((.13,0,.12)),.045,steel,lower)
 legs.append({'name':name,'hip':list(hip),'knee':list(knee),'foot':list(foot),'lengths':[(knee-hip).length,(foot-knee).length]})
# Surface-fit detail to the armour so side views do not reveal floating plates.
def mounted_point(x,y):
 bpy.context.view_layer.update()
 hit,p,normal,*_=sc.ray_cast(bpy.context.evaluated_depsgraph_get(),screen(x,y,30),-VIEW)
 return p+VIEW*.016 if hit else screen(x,y,.5)
for i,(x,y) in enumerate([(146,94),(170,97)]):
 points=[mounted_point(x+dx,y+dy) for dx,dy in [(-7,-3),(7,-3),(8,3),(-6,3)]]
 vs=points+[p-VIEW*.045 for p in points];me=bpy.data.meshes.new('fitted hatch');me.from_pydata(vs,[],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]);me.update();o=bpy.data.objects.new('hatch',me);sc.collection.objects.link(o);finish(o,'Fitted deck hatch '+str(i),olive,body,.012)
for x,y in [(136,120),(181,119),(61,87),(122,110),(184,108),(95,61),(115,52)]:
 p=mounted_point(x,y);cyl('Surface fitted fastener',p,p+VIEW*.018,.024,steel,body if y>80 else turret)
# Safe finite-size attack flash; hidden with visibility keys later.
flash=cube('Muzzle flash',screen(177,58,.3),(.22,.07,.07),mat('MAT-flash',(.9,.48,.12)),recoil,.025);flash.hide_render=True
sc['legs']=json.dumps(legs);sc['sample_frames']='[1]';sc['reference_basis']=json.dumps({'up':list(UP),'view':list(VIEW),'target':list(TARGET)})
for name,pos,energy,color,size in [('key',(-4,-6,8),700,(1,.88,.70),5),('fill',(5,-2,5),180,(.84,.9,1),5),('rim',(1,5,7),450,(.78,.86,1),4)]:
 l=bpy.data.objects.new('LGT-'+name,bpy.data.lights.new('LGT-'+name,'AREA'));sc.collection.objects.link(l);l.location=pos;l.data.energy=energy;l.data.color=color;l.data.size=size;l.rotation_euler=(Vector((0,0,1))-l.location).to_track_quat('-Z','Y').to_euler()
sc.world=bpy.data.worlds.new('World-studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.45,.47,.5,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.3
sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.max_bounces=4;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
sc.render.fps=24
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'model.blend'))
for o in sc.objects:
 if o.type=='MESH' and o!=base:o.data.materials.clear();o.data.materials.append(clay)
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'plain.blend'))
log('Built original full-depth hull, turret, four mechanical two-link legs, broad feet, pistons, sensors, closed barrel, bevels, and stationary cream disc. All six Blender skills applied. Plain stage ready.')
