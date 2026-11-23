"""Original true-3D biplane. X tailward, Y span, Z up; no subject cards."""
import bpy, math, os, json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']); M=R/'masters/biplane'; A=R/'assets/biplane'
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene

def mat(name,color,rough=.6,metal=0,fill=None):
 m=bpy.data.materials.new('MAT-'+name);m.diffuse_color=(*color,1);m.use_nodes=True
 n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Roughness'].default_value=rough;s.inputs['Metallic'].default_value=metal
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.008;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
 if fill:
  tx=n.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(A/(fill+'.png')),check_existing=True);tx.projection='BOX';tx.projection_blend=.25
  co=n.new('ShaderNodeTexCoord');l.new(co.outputs['Generated'],tx.inputs[0]);l.new(tx.outputs['Color'],s.inputs['Base Color'])
 return m
linen=mat('doped-linen',(.72,.53,.30),.78,fill='linen');olive=mat('olive-pigment',(.24,.24,.09),.65,fill='olive');wood=mat('varnished-ash',(.5,.19,.025),.4,fill='wood');steel=mat('rubbed-steel',(.32,.30,.25),.35,1);brass=mat('brass-edges',(.55,.37,.12),.32,1);rubber=mat('rubber',(.07,.06,.05),.86,fill='rubber');leather=mat('cockpit-leather',(.20,.055,.015),.58)
# #E9CFA0 converted from sRGB to linear, not mistaken for linear shader RGB.
def lin(c):return ((c/255+.055)/1.055)**2.4
stone=mat('cream-stone-E9CFA0',tuple(lin(c) for c in (233,207,160)),.86)

def mesh(name,vs,fs,ma,parent=None,bevel=0,smooth=True):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('GEO-'+name,me);sc.collection.objects.link(o);o.data.materials.append(ma)
 if parent:o.parent=parent
 if bevel:
  md=o.modifiers.new('Rounded physical edges','BEVEL');md.width=bevel;md.segments=3
 for p in me.polygons:p.use_smooth=smooth
 return o

def empty(name,loc,parent=None):
 o=bpy.data.objects.new(name,None);sc.collection.objects.link(o);o.location=loc;o.parent=parent;return o
flight=empty('RIG-flight',(0,0,1.90));flight.rotation_euler.x=-.075;flight.scale.x=.90;prop=empty('RIG-propeller',(-1.40,0,0),flight)

def uvball(name,loc,scale,ma,parent=flight):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=loc);o=bpy.context.object;o.name='GEO-'+name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma);o.parent=parent
 for p in o.data.polygons:p.use_smooth=True
 return o

def rod(name,a,b,r,ma,parent=flight):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=(b-a).length,location=(a+b)*.5);o=bpy.context.object;o.name='GEO-'+name;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();o.data.materials.append(ma);o.parent=parent
 md=o.modifiers.new('Edge glints','BEVEL');md.width=r*.22;md.segments=2
 for p in o.data.polygons:p.use_smooth=True
 return o

def tube(name,pts,r,ma,parent=flight):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=2;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,1)
 o=bpy.data.objects.new('GEO-'+name,cu);sc.collection.objects.link(o);o.data.materials.append(ma);o.parent=parent;return o

def lathe(name,sections,ma):
 vs=[];N=64
 for x,r,rz in sections:
  vs.extend((x,r*math.cos(2*math.pi*j/N),rz*math.sin(2*math.pi*j/N)) for j in range(N))
 fs=[]
 for i in range(len(sections)-1):
  for j in range(N):fs.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
 return mesh(name,vs,fs,ma,flight)
body=lathe('tapered-fuselage',[(-1.02,.34,.36),(-.8,.36,.37),(-.5,.35,.34),(-.1,.30,.30),(.35,.24,.24),(.9,.16,.15),(1.5,.065,.07),(1.72,.015,.02)],olive)
# Cockpit is a real boolean opening, with rim, leather seat and inset floor.
cutter=uvball('cockpit-cutter',(-.14,0,.32),(.31,.22,.23),olive)
bpy.context.view_layer.update();md=body.modifiers.new('Open cockpit','BOOLEAN');md.operation='DIFFERENCE';md.object=cutter;bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier=md.name);bpy.data.objects.remove(cutter,do_unlink=True)
uvball('seat-well',(-.09,0,.19),(.235,.17,.10),leather)
for y in [-.1,-.05,0,.05,.1]:uvball('seat-padded-channel',(.06,y,.27),(.055,.024,.09),leather)
tube('cockpit-coaming',[(-.14+.30*math.cos(t),.216*math.sin(t),.285+.035*math.cos(t)) for t in [2*math.pi*i/80 for i in range(81)]],.022,brass)
# Hollow cowl with annular lip: no solid cap hiding the rotary engine.
cowl=lathe('engine-cowling',[(-.91,.35,.37),(-1.03,.39,.40),(-1.18,.39,.40),(-1.24,.35,.36),(-1.24,.30,.31),(-1.18,.30,.31)],olive)
tube('cowling-bright-lip',[(-1.246,.325*math.cos(t),.335*math.sin(t)) for t in [i*2*math.pi/80 for i in range(81)]],.014,brass)
uvball('engine-hub',(-1.25,0,0),(.10,.12,.12),steel)
for j in range(9):
 t=j*math.tau/9;y,z=math.cos(t),math.sin(t)
 rod('radial-cylinder',(-1.23,.10*y,.10*z),(-1.23,.285*y,.285*z),.05,steel)
 for rr in [.14,.17,.20,.23,.26]:
  rod('cooling-fin',(-1.23,(rr-.007)*y,(rr-.007)*z),(-1.23,(rr+.007)*y,(rr+.007)*z),.057,steel)
# Closed cambered airfoil volume; rounded taper at each wingtip.
def wing(name,xc,z,span,chord,ma):
 vs=[];ns=48;nc=24
 for i in range(ns+1):
  y=-span/2+span*i/ns;end=min(1,max(.05,(span/2-abs(y))/.22));c=chord*(.64+.36*math.sin(end*math.pi/2))
  for j in range(nc):
   t=j*math.tau/nc;x=xc-.5*c*math.cos(t);zz=z+.055*math.sin(t)+.025*math.sin(t)**2
   vs.append((x,y,zz))
 fs=[]
 for i in range(ns):
  for j in range(nc):fs.append((i*nc+j,i*nc+(j+1)%nc,(i+1)*nc+(j+1)%nc,(i+1)*nc+j))
 fs.extend([tuple(reversed(range(nc))),tuple(ns*nc+j for j in range(nc))])
 return mesh(name,vs,fs,ma,flight)
upper=wing('upper-cambered-wing',-.40,.59,4.55,.63,linen)
lower=wing('lower-cambered-wing',-.20,-.31,4.32,.66,linen)
for z,xc,span in [(.59,-.40,4.55),(-.31,-.20,4.32)]:
 for j in range(-9,10):
  y=j*.22;tube('stitched-wing-rib',[(xc-.30+.60*i/16,y,z+.058*math.sin(math.pi*i/16)) for i in range(17)],.0045,linen)
 for y in [-1.62,1.62]:
  for x in [-.61,-.08]:
   rod('varnished-interplane-strut',(x+.10,y,-.28),(x-.08,y,.55),.038,wood)
   for zz,xx in [(-.28,x+.10),(.55,x-.08)]:uvball('strut-brass-shoe',(xx,y,zz),(.055,.052,.026),brass)
for y in [-.24,.24]:
 for x in [-.7,-.2]:rod('cabane-strut',(x,y,.22),(x-.12,y*1.8,.55),.027,wood)
# Tail surfaces are solid elliptical volumes, with real rudder seam.
uvball('horizontal-tail',(1.42,0,.03),(.40,.70,.045),linen)
fin=uvball('vertical-tail',(1.44,0,.20),(.34,.035,.32),olive)
tube('rudder-seam',[(1.58,-.038,z) for z in [.02,.12,.24,.37,.5]],.006,brass)
# Landing gear wheels with rubber tyres, linen discs and metal hubs.
for y in [-.56,.56]:
 for x in [-.88,-.37]:rod('undercarriage-strut',(x,0,-.22),(-1.0,y,-.60),.021,brass)
 wheel=uvball('rubber-wheel',(-1.0,y,-.61),(.245,.07,.245),rubber)
 for s in [-1,1]:
  uvball('linen-wheel-disc',(-1.0,y+s*.062,-.61),(.205,.014,.205),linen)
  uvball('wheel-brass-hub',(-1.0,y+s*.084,-.61),(.055,.035,.055),brass)
rod('wheel-axle',(-1.0,-.65,-.61),(-1.0,.65,-.61),.03,brass)
# True two-bladed propeller, mounted on an X rotation spindle.
for sign in [-1,1]:
 p=uvball('laminated-propeller',(0,sign*.30,sign*.42),(.036,.095,.55),wood,prop);p.rotation_euler.x=-.62
rod('propeller-shaft',(-1.43,0,0),(-1.20,0,0),.045,steel)
uvball('propeller-boss',(-.06,0,0),(.095,.105,.105),brass,prop)
# Panel seams/rivets sit on real fuselage skin, never a flat image plane.
for x in [-.89,-.68,-.35,.2,.65,1.05]:
 r=max(.10,.35-(x+.65)*.135)
 pts=[(x,r*math.cos(t),r*math.sin(t)) for t in [math.tau*j/64 for j in range(65)]];tube('fuselage-panel-seam',pts,.004,brass)
 for j in range(16):
  t=math.tau*j/16;uvball('rivet',(x,(r+.003)*math.cos(t),(r+.003)*math.sin(t)),(.009,.009,.009),brass)
# Two unobtrusive gun barrels supply an explicit attack-run action.
for y in [-.10,.10]:rod('synchronized-gun',(-.98,y,.30),(-.56,y,.30),.018,steel)
# Stationary cream stone plinth and curved solid display support.
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.68,depth=.13,location=(-.13,0,.065));base=bpy.context.object;base.name='GEO-cream-stone-base';base.data.materials.append(stone);be=base.modifiers.new('Soft stone rim','BEVEL');be.width=.035;be.segments=3
# Swept rectangular support rises to the lower wing; substantial real thickness.
vs=[];fs=[]
for i in range(25):
 t=i/24;z=.13+1.46*t;x=-.17+.27*math.sin(t*math.pi*.82);width=.24*(1-t)+.055*t
 for xx,yy in [(-width,-.10),(width,-.10),(width,.10),(-width,.10)]:vs.append((x+xx,yy,z))
for i in range(24):
 for j in range(4):fs.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
fs += [(3,2,1,0),(96,97,98,99)]
support=mesh('curved-display-support',vs,fs,stone,bevel=.035)
# Fixed orthographic source camera. Base ellipse and the two aircraft axes calibrate elevation.
target=Vector((.04,0,1.40));bpy.ops.object.camera_add(location=target+Vector((-4.77,-8.27,3.0)));cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=3.55;sc.camera=cam
for name,loc,power,size,col in [('key',(-3,-4,7),550,4,(1,.86,.67)),('fill',(4,-3,4),130,5,(.85,.91,1)),('rim',(2,4,6),350,3,(.75,.86,1))]:
 data=bpy.data.lights.new('LGT-'+name,'AREA');o=bpy.data.objects.new('LGT-'+name,data);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1.7))-o.location).to_track_quat('-Z','Y').to_euler();data.energy=power;data.shape='DISK';data.size=size;data.color=col
sc.world=bpy.data.worlds.new('WORLD-soft-fill');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.61,.7,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.3
sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.cycles.max_bounces=4;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
bpy.context.view_layer.update();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'biplane.blend'))
print('BUILT',len(sc.objects),'objects',sum(len(o.data.vertices) for o in sc.objects if o.type=='MESH'),'vertices')
