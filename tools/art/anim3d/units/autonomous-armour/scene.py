"""Original autonomous tracked armour: closed, beveled meshes and a rigid mechanical rig."""
import sys, os, math, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
from common import MASTER, SLUG, log, TRACK_H, TRACK_R, TRACK_Z, TRACK_LENGTH, ROAD_RADIUS
from math import sin, cos, pi
(MASTER/'build-pending').write_text('Model rebuild started; finish and all clip builds required.\n')
random.seed(23)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def material(name, dark, light, metal=0, rough=.7, grain=.003):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF')
    s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=24;noise.inputs['Detail'].default_value=4
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*dark,1);ramp.color_ramp.elements[1].color=(*light,1)
    l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],s.inputs['Base Color'])
    micro=n.new('ShaderNodeTexNoise');micro.inputs['Scale'].default_value=170
    bump=n.new('ShaderNodeBump');bump.inputs['Distance'].default_value=grain;bump.inputs['Strength'].default_value=.2
    l.new(micro.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
    return m
paint=material('MAT-worn grey olive paint',(.105,.102,.075),(.27,.255,.19))
edge=material('MAT-exposed bright steel',(.28,.255,.20),(.56,.53,.43),1,.48)
steel=material('MAT-dark track steel',(.07,.065,.052),(.24,.215,.17),1,.72)
rubber=material('MAT-dusty wheel rubber',(.038,.035,.028),(.12,.105,.08),0,.9)
black=material('MAT-recess grime',(.009,.011,.01),(.035,.037,.03),0,.88)
glass=material('MAT-blue sensor glass',(.008,.018,.025),(.06,.15,.20),0,.18)
# Linear values corresponding to #E9CFA0, modulated by fine stone grain.
stone=material('MAT-warm cream stone #E9CFA0',(.73,.55,.32),(.89,.70,.43),0,.88,.001)
s=stone.node_tree.nodes.get('Principled BSDF');s.inputs['Emission Color'].default_value=(.815,.624,.352,1);s.inputs['Emission Strength'].default_value=.16

def empty(name, parent=None, loc=(0,0,0)):
    o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.parent=parent;o.location=loc;return o
root=empty('RIG-chassis')
turret=empty('RIG-turret',root,(-.25,-.15,1.94))
turret.rotation_euler.z=.60
turret.location.z+=.15
turret.scale.z=.85
gun=empty('RIG-gun',turret,(.85,0,.60))
sensor=empty('RIG-sensor',turret,(-.34,0,1.18))

def finish(o,name,mat,parent,bevel=.012,smooth=False):
    o.name=name;o.parent=parent;o.data.materials.append(mat)
    if bevel:
        b=o.modifiers.new('Real worn edge bevel','BEVEL');b.width=bevel;b.segments=5 if name.startswith('BASE-') else 3
        bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
    if smooth:
        for p in o.data.polygons:p.use_smooth=True
    return o

def cube(name,loc,dim,mat=paint,parent=root,bevel=.015):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,mat,parent,bevel)

def cyl(name,loc,r,depth,mat=paint,parent=root,axis='Z',verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc);o=bpy.context.object
    if axis=='X':o.rotation_euler.y=pi/2
    if axis=='Y':o.rotation_euler.x=pi/2
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    return finish(o,name,mat,parent,.055 if name.startswith('BASE-') else .007,True)

def rod(name,a,b,r,mat=edge,parent=root):
    a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,mat,parent)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def tube(name,pts,r,mat=edge,parent=root,closed=False):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2
    p=c.splines.new('POLY');p.points.add(len(pts)-1)
    for v,co in zip(p.points,pts):v.co=(*co,1)
    p.use_cyclic_u=closed;o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.parent=parent;o.data.materials.append(mat);return o

def armour(name,lo,hi,z0,z1,mat=paint,parent=root,bevel=.025):
    # Counterclockwise four-corner rectangles, sloped from lower to upper ring.
    vs=[(x,y,z0) for x,y in lo]+[(x,y,z1) for x,y in hi]
    fs=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    return finish(o,name,mat,parent,bevel)

def rect(x0,x1,y):return [(x0,-y),(x1,-y),(x1,y),(x0,y)]
base=cyl('BASE-stationary cream stone',(0,0,.075),2.36,.33,stone,None,verts=128)
cube('GEO-lower hull',(-.08,0,.95),(3.18,1.85,.93))
armour('GEO-sloped hull',rect(-1.72,1.85,1.08),rect(-1.57,.94,.99),1.16,1.88)
# Wide planar front plates and return lip.
armour('GEO-front lower plate',rect(1.42,1.80,.90),rect(1.55,1.88,.96),.58,1.27,bevel=.018)
o=cube('GEO-front service plate',(1.827,0,1.03),(.045,1.20,.36));o.rotation_euler.y=.18
for y in [-.65,.65]:
    tube('GEO-front towing eye',[(1.86,y+.075*cos(a*2*pi/24),1.20+.09*sin(a*2*pi/24)) for a in range(24)],.025,edge,closed=True)
    cube('GEO-tow mount',(1.81,y,1.22),(.08,.16,.16),steel)
for y in [-.95,.95]:
    cube('GEO-fender',(-.05,y,1.60),(3.75,.55,.15))
    guard=cube('GEO-front fender',(1.77,y,1.44),(.44,.56,.09));guard.rotation_euler.y=.45
    cube('GEO-headlight housing',(1.65,y,1.60),(.21,.37,.16),black)
    cube('GEO-headlight rim',(1.765,y,1.60),(.026,.31,.12),edge,bevel=.008)
    cube('GEO-headlight glass',(1.783,y,1.60),(.012,.26,.065),stone,bevel=.005)
    for dy in [-.09,-.045,0,.045,.09]:cube('GEO-headlight rib',(1.791,y+dy,1.60),(.008,.008,.065),edge,bevel=.002)
# Armoured side skirts: true separated plates, thickness, hinges, fasteners.
for side in [-1,1]:
    for j,x in enumerate([-1.46,-.84,-.22,.40,1.02]):
        p=cube('GEO-side armour panel',(x,side*1.17,1.29),(.595,.10,.92),paint,bevel=.012)
        p.rotation_euler.x=side*.10
        for dx in [-.24,.24]:
            cyl('GEO-skirt bolt',(x+dx,side*1.235,.94),.027,.018,edge,axis='Y',verts=12)
            cyl('GEO-skirt bolt',(x+dx,side*1.18,1.65),.027,.018,edge,axis='Y',verts=12)
        rod('GEO-panel hinge',(x-.12,side*1.18,1.74),(x+.12,side*1.18,1.74),.027,edge)
    cube('GEO-side intake',(.57,side*1.235,1.42),(.26,.025,.24),black)
    for z in [1.34,1.39]:cube('GEO-intake lip',(.57,side*1.254,z),(.23,.03,.023),edge,bevel=.003)
# Main turret: compact angular turret, not a manned WWII cast dome.
cyl('GEO-turret bearing',(-.25,0,1.92),.82,.12,steel)
armour('GEO-angular turret',rect(-1.00,.85,.75),rect(-.86,.58,.59),.05,.85,parent=turret)
for side in [-1,1]:
    for x in [-.66,.20]:
        p=cube('GEO-turret cheek armour',(x,side*.73,.46),(.73,.09,.65),paint,turret,.018);p.rotation_euler.x=side*.25
        for dx in [-.30,.30]:
            for z in [.18,.73]:cyl('GEO-turret recessed bolt',(x+dx,side*(.78-(z-.36)*.25),z),.022,.012,black,turret,'Y',12)
    for i in range(4):
        x=-.25+(i%2)*.10;z=.40+(i//2)*.13
        o=cyl('GEO-smoke launcher',(x,side*.85,z),.05,.17,steel,turret,'Y',20);o.rotation_euler.x=side*.18
        cyl('GEO-launcher mouth',(x,side*.944,z+.012),.038,.006,black,turret,'Y',20)
# Mantlet, stepped gun, tubular muzzle brake with real central hole.
cube('GEO-mantlet',(0,0,0),(.24,.43,.37),paint,gun,.04)
cyl('GEO-gun collar',(.17,0,0),.13,.17,steel,gun,'X')
cyl('GEO-barrel',(.65,0,0),.075,.88,paint,gun,'X')
for x in [.29,.84,1.02]:cyl('GEO-barrel reinforcement',(x,0,0),.086,.047,steel,gun,'X')
# Annular closed mesh, open bore, dark inside.
verts=[]
for x,r in [(1.05,.11),(1.37,.11),(1.37,.073),(1.05,.073)]:
    verts += [(x,r*cos(i*2*pi/32),r*sin(i*2*pi/32)) for i in range(32)]
faces=[]
for ring in range(4):
    for i in range(32):faces.append((ring*32+i,ring*32+(i+1)%32,((ring+1)%4)*32+(i+1)%32,((ring+1)%4)*32+i))
me=bpy.data.meshes.new('Open muzzle mesh');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('GEO-open muzzle brake',me);bpy.context.collection.objects.link(o);finish(o,o.name,steel,gun,.005)
cyl('GEO-bore depth',(1.06,0,0),.072,.006,black,gun,'X')
for x in [1.13,1.25]:
    for side in [-1,1]:cube('GEO-muzzle brake port',(x,side*.107,0),(.055,.012,.075),black,gun,.006)
# Distinct unmanned optics, separate sensor yaw bearing and two slender whip aerials.
cyl('GEO-sensor pedestal',(-.34,0,1.02),.15,.18,paint,turret)
cube('GEO-main sensor',(0,0,0),(.40,.42,.27),paint,sensor,.025)
for y,r in [(-.10,.072),(.10,.052)]:
    cyl('GEO-optic rim',(.21,y,0),r+.017,.03,steel,sensor,'X')
    cyl('GEO-optic lens',(.23,y,0),r,.014,glass,sensor,'X')
    cyl('GEO-optic reflection',(.24,y-.018,.025),r*.22,.005,stone,sensor,'X',16)
cube('GEO-forward sensor',(.31,-.10,.93),(.29,.31,.21),paint,turret)
cyl('GEO-forward optic',(.465,-.10,.93),.074,.018,black,turret,'X')
cyl('GEO-forward lens',(.48,-.10,.93),.052,.016,glass,turret,'X')
for i,(x,y,h) in enumerate([(-.96,-.46,1.22),(-.68,.38,.85)]):
    a=empty('RIG-antenna-'+str(i),turret,(x,y,.82))
    cyl('GEO-antenna mount',(0,0,.06),.055,.12,paint,a)
    rod('GEO-antenna lower',(0,0,.10),(0,0,.43),.024,steel,a)
    rod('GEO-antenna whip',(0,0,.43),(0,0,h),.010,steel,a)
# Small surface construction details.
for x in [-1.35,-.97,-.59]:
    cube('GEO-rear service hatch',(x,.10,1.901),(.31,.66,.035))
for y in [-.48,.48]:
    o=cube('GEO-front upper periscope',(.65,y,1.91),(.26,.27,.10));o.rotation_euler.y=.18
    cube('GEO-periscope glass',(.79,y,1.915),(.015,.21,.042),black)
for x in [-1.40,-1.05,-.65,-.25,.15,.55,1.10]:
    for side in [-1,1]:cube('GEO-deck fastener',(x,side*.87,1.895),(.07,.09,.035),edge,bevel=.009)
# Six separated road wheels each side; twelve repeated studs close the roll loop.
for side in [-1,1]:
    for i,x in enumerate([-1.30,-.78,-.26,.26,.78,1.30]):
        w=empty(f'RIG-wheel-{side}-{i}',root,(x,side*1.03,.24+.041+.025/2+.065/2+ROAD_RADIUS));w['wheel']=True
        cyl('GEO-rubber wheel',(0,0,0),ROAD_RADIUS,.27,rubber,w,'Y')
        # A rolled rim and deep curved dish replace the stack of flat washers.
        # The closed profile has a real recessed well and a small central cap.
        profile=[(.249,.140),(.249,.158),(.238,.174),(.222,.176),
                 (.209,.160),(.191,.128),(.160,.112),(.096,.116),
                 (.065,.145),(.045,.164),(0,.164),(0,.128)]
        vs=[(r*cos(j*2*pi/48),side*d,r*sin(j*2*pi/48)) for r,d in profile for j in range(48)]
        fs=[]
        for k in range(len(profile)):
            for j in range(48):
                face=(k*48+j,k*48+(j+1)%48,((k+1)%len(profile))*48+(j+1)%48,((k+1)%len(profile))*48+j)
                fs.append(face if side==1 else tuple(reversed(face)))
        me=bpy.data.meshes.new('Closed wheel dish');me.from_pydata(vs,[],fs);me.update()
        o=bpy.data.objects.new('GEO-wheel dish',me);bpy.context.collection.objects.link(o)
        finish(o,o.name,paint,w,0,True)
        bpy.context.view_layer.objects.active=o
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=.0001);bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
        for j in range(12):
            a=j*2*pi/12;cyl('GEO-hub stud',(.09*cos(a),side*.128,.09*sin(a)),.010,.012,paint,w,'Y',8)
    for x in [-1.49,1.49]:
        w=empty(f'RIG-sprocket-{side}-{x}',root,(x,side*1.03,TRACK_Z));w['wheel']=True
        cyl('GEO-sprocket',(0,0,0),TRACK_R-.04,.28,steel,w,'Y')
        cyl('GEO-sprocket face',(0,side*.15,0),.24,.026,paint,w,'Y')
        cyl('GEO-sprocket hub',(0,side*.18,0),.11,.04,edge,w,'Y')
        for j in range(12):
            a=j*2*pi/12;o=cube('GEO-sprocket tooth',((TRACK_R-.025)*cos(a),0,(TRACK_R-.025)*sin(a)),(.067,.30,.06),edge,w,.006);o.rotation_euler.y=-a
# Individually linked track shoes, capsule path shared with the animation script.
R=TRACK_R;H=TRACK_H;Z=TRACK_Z;LENGTH=TRACK_LENGTH

def trackpoint(t):
    d=(t%1)*LENGTH
    if d<2*H:return (-H+d,Z+R,0)
    d-=2*H
    if d<pi*R:
        a=pi/2-d/R;return(H+R*cos(a),Z+R*sin(a),pi/2-a)
    d-=pi*R
    if d<2*H:return(H-d,Z-R,pi)
    d-=2*H;a=-pi/2-d/R;return(-H+R*cos(a),Z+R*sin(a),pi/2-a)
# Shoes are actual meshes; shared datablocks reduce scene size and render setup cost.
prototype=None
for side in [-1,1]:
    for i in range(64):
        x,z,a=trackpoint(i/64);link=empty(f'RIG-track-{side}-{i}',root,(x,side*1.04,z));link.rotation_euler.y=a;link['phase']=i/64;link['side']=side
        if prototype is None:
            parts=[cube('GEO-track shoe',(0,0,0),(.126,.43,.065),steel,link,.007),cube('GEO-track ridge',(0,0,.041),(.032,.42,.025),edge,link,.004)]
            for yy in [-.22,.22]:parts.append(cyl('GEO-track pin',(.045,yy,0),.022,.028,edge,link,'Y',12))
            prototype=parts
        else:
            for original in prototype:
                p=original.copy();p.data=original.data;bpy.context.collection.objects.link(p);p.parent=link
# Visibility-keyed solid muzzle flash. No volume grids or near-zero scales.
fire=material('MAT-hot muzzle core',(.8,.18,.01),(1,.62,.10),0,.8)
s=fire.node_tree.nodes.get('Principled BSDF');s.inputs['Emission Color'].default_value=(1,.37,.025,1);s.inputs['Emission Strength'].default_value=2
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(1.50,0,0));flash=bpy.context.object;flash.scale=(.18,.09,.09);finish(flash,'FX-flash',fire,gun,0);flash.hide_render=True
# Matte char plate becomes visible only after terminal damage.
scar=cube('FX-charred impact',(.44,-1.235,1.16),(.30,.018,.23),black,root,.025);scar.hide_render=True
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True
sc.cycles.max_bounces=5;sc.render.threads_mode='FIXED';sc.render.threads=3
sc.render.film_transparent=True;sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.color=(.15,.15,.15);sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
bpy.ops.object.camera_add(location=(10,-5.7,4.60));cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(Vector((0,0,1.60))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=5.25;sc.camera=cam
for name,loc,power,size,col in [('LGT-warm key',(-3,-4,9),620,5,(1,.96,.88)),('LGT-soft fill',(5,-3,4),110,5,(.92,.96,1)),('LGT-cool rim',(-2,4,6),230,3,(.82,.90,1))]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
# Broader track gauge and hull, with circular road wheels retained.
for o in list(root.children):
    if o.name == 'RIG-turret' or o.name.startswith('GEO-turret bearing'):
        continue
    o.location.y *= 1.22
    if o.type in {'MESH', 'CURVE'}:
        o.scale.y *= 1.22
        if o.name.startswith('GEO-') and o.location.z > 1.1:
            o.location.z += .10
        if o.name == 'GEO-sloped hull':
            for v in o.data.vertices:
                if v.co.z > 1.1: v.co.z += .10
    if o.name.startswith('RIG-antenna'):
        o.location.z += .08
sc['track_gauge']=1.04*1.22
sc['asset']=SLUG;sc['track_length']=LENGTH;sc['rig']='rigid parent hierarchy, independent turret/gun/sensors/wheels/128 track links'
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'model.blend'))
# Plain evidence uses neutral clay for all vehicle meshes; base stays cream.
clay=material('MAT-plain clay',(.25,.23,.20),(.46,.43,.37))
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith('GEO-'):o.data.materials.clear();o.data.materials.append(clay)
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'plain.blend'))
log(f'Built true 3D hard-surface geometry and rigid rig: {len(bpy.data.objects)} objects; bevels, open muzzle, sensors, six wheels per side, 128 articulated tracks.')
