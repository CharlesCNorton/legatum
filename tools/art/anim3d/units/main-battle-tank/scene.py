"""Original articulated main battle tank. Run through the unit render.sh.
All modelling is geometry; paint.py adds UV brushwork later. No billboard subject/effects.
"""
import sys
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parent))
import bpy, math, os, random, json
from pathlib import Path
from mathutils import Vector
from math import pi, sin, cos
ROOT = Path(os.environ['ANIM_ROOT'])
MASTER = ROOT/'masters/main-battle-tank'
MASTER.mkdir(parents=True, exist_ok=True)
random.seed(47)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def material(name, dark, light, metal=0.0, rough=.72, scale=22, bump=.02):
    m=bpy.data.materials.new(name); m.use_nodes=True
    n=m.node_tree.nodes; l=m.node_tree.links; s=n.get('Principled BSDF')
    s.inputs['Metallic'].default_value=metal; s.inputs['Roughness'].default_value=rough
    noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=scale; noise.inputs['Detail'].default_value=3
    ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.18; ramp.color_ramp.elements[0].color=(*dark,1)
    ramp.color_ramp.elements[1].position=.82; ramp.color_ramp.elements[1].color=(*light,1)
    l.new(noise.outputs['Fac'],ramp.inputs[0]); l.new(ramp.outputs[0],s.inputs['Base Color'])
    grain=n.new('ShaderNodeTexNoise'); grain.inputs['Scale'].default_value=175; grain.inputs['Detail'].default_value=2
    b=n.new('ShaderNodeBump'); b.inputs['Strength'].default_value=.26; b.inputs['Distance'].default_value=bump
    l.new(grain.outputs['Fac'],b.inputs['Height']); l.new(b.outputs[0],s.inputs['Normal'])
    return m
paint=material('Olive drab • mottled cast and rolled steel',(.046,.054,.017),(.128,.142,.046),0,.78,32,.004)
edge=material('Dusty rubbed edges',(.15,.105,.035),(.43,.30,.11),1,.57,37,.005)
steel=material('Track steel • worn and earth packed',(.065,.057,.035),(.23,.20,.12),1,.66,19,.013)
rubber=material('Dust embedded in rubber',(.028,.025,.018),(.095,.077,.046),0,.92,22,.014)
mud=material('Dry mud and road dust',(.13,.095,.039),(.31,.23,.115),0,.95,25,.025)
rust=material('Exposed dark rust chips',(.065,.025,.009),(.19,.09,.026),0,.83,30,.004)
black=material('Recessed apertures',(.022,.019,.008),(.060,.049,.022),0,.85)
stone=material('Warm cream limestone',(.88,.65,.40),(1.0,.84,.60),0,.86,110,.006)
# Small warm bounce is material-bound so the cream base survives host lighting changes.
stone_shader=stone.node_tree.nodes.get('Principled BSDF')
stone_shader.inputs['Emission Color'].default_value=(.9,.64,.40,1)
stone_shader.inputs['Emission Strength'].default_value=.20
# Original generated painted fill, reused from the artillery lane (CC BY 4.0).
n=paint.node_tree.nodes; l=paint.node_tree.links; s=n.get('Principled BSDF')
t=n.new('ShaderNodeTexImage'); t.image=bpy.data.images.load(str(ROOT/'assets/tank/painted-olive.png')); t.projection='BOX'; t.projection_blend=.3
coord=n.new('ShaderNodeTexCoord'); l.new(coord.outputs['Generated'],t.inputs['Vector'])
l.new(t.outputs['Color'],s.inputs['Base Color'])
# Reuse the actual scanned steel microstructure; colour is our painted olive pigment.
n=paint.node_tree.nodes;l=paint.node_tree.links;s= n.get('Principled BSDF')
t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ROOT/'assets/Metal034/Metal034_1K-JPG_Displacement.jpg'));t.image.colorspace_settings.name='Non-Color';t.projection='BOX';t.projection_blend=.35
uv=n.new('ShaderNodeTexCoord');l.new(uv.outputs['Generated'],t.inputs['Vector'])
b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.27;b.inputs['Distance'].default_value=.008
old=s.inputs['Normal'].links[0].from_socket;l.new(old,b.inputs['Normal']);l.new(t.outputs[0],b.inputs['Height']);l.new(b.outputs[0],s.inputs['Normal'])
# Reuse the inherited CC0 material scan for stone micrograin.
scan=ROOT/'assets/Travertine001/Travertine001_1K-JPG_Displacement.jpg'
if scan.exists():
    n=stone.node_tree.nodes; l=stone.node_tree.links; t=n.new('ShaderNodeTexImage'); t.image=bpy.data.images.load(str(scan)); t.image.colorspace_settings.name='Non-Color'; t.projection='BOX'; t.projection_blend=.3
    uv=n.new('ShaderNodeTexCoord'); l.new(uv.outputs['Generated'],t.inputs['Vector'])
    b=next(x for x in n if x.type=='BUMP'); l.new(t.outputs[0],b.inputs['Height'])

def empty(name,parent=None,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None); bpy.context.collection.objects.link(o); o.parent=parent; o.location=loc; return o
root=empty('Vehicle suspension root',loc=(0,0,-.11))
turret=empty('Turret traverse',root,(.05,0,1.25))
gun=empty('Gun recoil',turret,(.64,0,.28))
turret.rotation_euler[2]=math.radians(0)
gun.rotation_euler[1]=math.radians(-10)

def finish(o,name,mat,parent=None,bevel=0,smooth=False):
    o.name=name; o.data.materials.append(mat); o.parent=parent
    if bevel:
        mod=o.modifiers.new('Forged rounded edges','BEVEL'); mod.width=bevel; mod.segments=3
        bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=mod.name)
    if smooth:
        for p in o.data.polygons:p.use_smooth=True
    return o

def cube(name,loc,scale,mat=paint,parent=root,bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,mat,parent,bevel)

def cyl(name,loc,r,depth,mat=paint,parent=root,axis='Z',verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc)
    o=bpy.context.object
    if axis=='Y':o.rotation_euler[0]=pi/2
    if axis=='X':o.rotation_euler[1]=pi/2
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    return finish(o,name,mat,parent,.012,True)

def sphere(name,loc,scale,mat=paint,parent=root):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc)
    o=bpy.context.object; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,mat,parent,0,True)

def rod(name,a,b,r,mat=edge,parent=root):
    a=Vector(a); b=Vector(b); o=cyl(name,(a+b)/2,r,(a-b).length,mat,parent)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler(); return o

def tube(name,points,r,mat=edge,parent=root,closed=False):
    c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.bevel_depth=r; c.bevel_resolution=3
    s=c.splines.new('POLY'); s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    s.use_cyclic_u=closed
    o=bpy.data.objects.new(name,c); bpy.context.collection.objects.link(o); o.data.materials.append(mat); o.parent=parent; return o

def ringmesh(name,rings,mat=paint,parent=root,n=64):
    vs=[]
    for x,y,z,rx,ry in rings:
        vs.extend([(x+rx*cos(2*pi*i/n),y+ry*sin(2*pi*i/n),z) for i in range(n)])
    fs=[tuple(range(n-1,-1,-1))]
    for k in range(len(rings)-1):
        for i in range(n):j=(i+1)%n; fs.append((k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i))
    fs.append(tuple((len(rings)-1)*n+i for i in range(n)))
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(vs,[],fs); mesh.update()
    o=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(o)
    return finish(o,name,mat,parent,0,True)

# Low Cold-War hull and cast dome, matched to this painting rather than the WWII donor.
base=cyl('Stationary cream stone base',(0,0,.12),2.20,.22,stone,None,verts=128)
cube('Lower hull',(-.06,0,.71),(3.40,1.62,.55),paint)
vs=[(-1.82,-.90,.88),(1.88,-.90,.88),(1.88,.90,.88),(-1.82,.90,.88),
    (-1.82,-.94,1.24),(1.54,-.94,1.24),(1.54,.94,1.24),(-1.82,.94,1.24)]
fs=[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
me=bpy.data.meshes.new('Sloped armour');me.from_pydata(vs,[],fs);me.update()
hull=bpy.data.objects.new('Sloped upper hull',me);bpy.context.collection.objects.link(hull);finish(hull,hull.name,paint,root,.035)
cyl('Turret bearing',(.05,0,1.25),.73,.10,steel)
cast=ringmesh('Rounded cast turret',[(0,0,0,.84,.70),(0,0,.09,.86,.70),(-.05,0,.27,.79,.64),(-.13,0,.43,.65,.52),(-.15,0,.51,.45,.37),(-.15,0,.53,.30,.26)],paint,turret)
sub=cast.modifiers.new('Cast dome smoothing','SUBSURF');sub.levels=1
bpy.context.view_layer.objects.active=cast;bpy.ops.object.modifier_apply(modifier=sub.name)
cyl('Closed commander cupola',(-.27,-.12,.56),.23,.12,paint,turret)
cyl('Cupola bevel',(-.27,-.12,.63),.22,.035,edge,turret)
for j in range(6):
    a=j*2*pi/6
    o=cube('Periscope glass',(-.27+.216*cos(a),-.12+.216*sin(a),.57),(.095,.027,.043),black,turret,.004);o.rotation_euler[2]=a+pi/2
for x in [-.42,-.12]:
    cube('Cupola sight', (x,-.12,.69),(.045,.065,.10),paint,turret,.006)
cube('Gunner hatch',(.05,.33,.49),(.34,.33,.065),paint,turret,.035)
rod('Machine gun pintle',(.08,.33,.52),(.08,.33,.80),.027,steel,turret)
cube('Machine gun receiver',(.14,.33,.80),(.25,.07,.075),steel,turret,.012)
rod('Machine gun barrel',(.22,.33,.82),(.62,.33,.83),.017,steel,turret)
cube('Machine gun magazine',(.05,.39,.79),(.10,.12,.11),paint,turret,.012)
sphere('Cast mantlet',(.01,0,0),(.25,.22,.20),paint,gun)
cyl('Gun sleeve',(.23,0,0),.082,.36,paint,gun,'X')
cyl('Long smoothbore barrel',(1.21,0,0),.042,1.78,paint,gun,'X')
cyl('Muzzle lip',(2.11,0,0),.046,.045,edge,gun,'X')
cyl('Recessed muzzle bore',(2.135,0,0),.030,.008,black,gun,'X')
for side in [-1,1]:
    y=side*1.0
    cube('Raised track fender',(-.03,y,1.12),(3.65,.43,.07),paint,bevel=.018)
    for i,x in enumerate([-1.45,-.86,-.27,.32,.91,1.50]):
        o=cube('Armoured side skirt',(x,side*1.22,1.0),(.59,.045,.32),paint,bevel=.014)
        for xx in [-.25,.25]:sphere('Skirt bolt',(x+xx,side*1.252,1.085),(.015,.009,.015),edge)
    o=cube('Forward fender',(1.77,y,1.025),(.39,.44,.065),paint);o.rotation_euler[1]=.40
    for idx,x in enumerate([-1.35,-.82,-.29,.24,.77,1.30]):
        wheel=empty(f'Road wheel pivot {side} {idx}',root,(x,side*.99,.62));wheel['wheel']=True;wheel['track_side']=side;wheel['rolling_radius']=.29
        cyl('Rubber wheel rim',(0,0,0),.29,.28,rubber,wheel,'Y')
        cyl('Cast wheel dished face',(0,side*.15,0),.245,.03,paint,wheel,'Y')
        cyl('Wheel hub',(0,side*.18,0),.078,.07,edge,wheel,'Y')
        tube('Wheel outer lip',[(.23*cos(a*2*pi/40),side*.176,.23*sin(a*2*pi/40)) for a in range(40)],.009,edge,wheel,True)
        for j in range(8):
            a=j*2*pi/8;cyl('Wheel recess',(.153*cos(a),side*.172,.153*sin(a)),.032,.007,black,wheel,'Y',12)
    for x in [-1.65,1.65]:
        wheel=empty(f'Sprocket pivot {side} {x}',root,(x,side*.99,.73));wheel['wheel']=True;wheel['track_side']=side;wheel['rolling_radius']=.27
        cyl('Drive sprocket body',(0,0,0),.27,.26,steel,wheel,'Y')
        cyl('Drive wheel face',(0,side*.15,0),.21,.025,paint,wheel,'Y')
        cyl('Drive hub',(0,side*.18,0),.08,.06,edge,wheel,'Y')
    cyl('Headlamp housing',(1.20,side*.65,1.20),.065,.07,paint,axis='X')
    cyl('Headlamp lens',(1.24,side*.65,1.20),.05,.008,edge,axis='X')
    rod('Glacis handrail',(1.28,side*.68,1.18),(1.67,side*.68,1.04),.017,edge)
    for x in [-1.6,-1.0]:
        cube('Rear stowage box',(x,side*.90,1.31),(.45,.27,.20),paint)
        cube('Stowage lid',(x,side*.90,1.42),(.47,.29,.025),edge)
        cube('Box latch',(x,side*1.05,1.33),(.04,.025,.09),edge,bevel=.005)
# Closed constant-speed route, contacting the disc at z=.23 after suspension-root offset.
from runninggear import route
circles=[(-1.65,.73,.30),(1.65,.73,.30),(-1.35,.62,.31),(1.30,.62,.31)]
LENGTH,trackpoint=route(circles)
for side in [-1,1]:
    for i in range(62):
        x,z,a=trackpoint(i/62)
        link=empty(f'Track link {side} {i}',root,(x,side*.99,z));link.rotation_euler[1]=a;link['track_phase']=i/62;link['track_side']=side
        cube('Forged track shoe',(0,0,0),(.125,.43,.035),steel,link,.006)
        cube('Polished raised grouser',(0,0,.026),(.028,.405,.018),edge,link,.004)
# Rear fuel drum with circular ends, retaining bands and a tightly rolled tarpaulin.
canvas=material('Dusty rolled canvas',(.13,.105,.06),(.40,.32,.19),0,.92,65,.008)
cyl('Rear pale fuel drum',(-1.44,.16,1.49),.205,1.16,canvas,axis='Y')
for y in [-.44,-.15,.24,.72]:
    tube('Fuel drum rolled hoop',[(-1.44+.208*cos(a*2*pi/48),y,1.49+.208*sin(a*2*pi/48)) for a in range(48)],.012,edge,closed=True)
for y in [-.44,.72]:cyl('Drum end',(-1.44,y,1.49),.184,.01,canvas,axis='Y')
roll=cyl('Canvas roll',(-1.01,-.34,1.47),.15,.63,canvas,axis='Y')
# Full-volume gathered canvas: radial folds, pinched at the two retaining straps.
for vertex in roll.data.vertices:
    x,y,z=vertex.co;angle=math.atan2(z,x)
    gather=1-.035*math.exp(-((y+.23)/.035)**2)-.035*math.exp(-((y-.19)/.035)**2)
    fold=1+.045*math.sin(11*angle+3*y)+.018*math.sin(23*angle-8*y)
    vertex.co.x*=fold*gather;vertex.co.z*=fold*gather
# Thin closed flattened bands, with buckles rather than round wire ties.
for y in [-.57,-.15]:
    band=ringmesh('Canvas thick webbing',[(0,0,0,.16,.16),(0,0,.045,.16,.16)],canvas,root,48)
    band.rotation_euler[0]=pi/2;band.location=(-1.01,y,1.47)
    cube('Canvas thick buckle',(-1.01,y-.025,1.625),(.085,.06,.025),edge,root,.005)
for y in [-.57,-.15]:
    tube('Canvas thick retaining band',[(-1.01+.156*cos(a*2*pi/48),y,1.47+.156*sin(a*2*pi/48)) for a in range(48)],.018,edge,closed=True)
for i in range(10):cube('Engine louvre',(-1.65+i*.055,.0,1.257),(.028,.66,.025),steel,bevel=.004)
for side in [-1,1]:
    tube('Hull weld',[(-1.60,side*.82,1.25),(1.12,side*.82,1.25),(1.87,side*.90,.90)],.009,edge)
    tube('Turret casting seam',[(.845*cos(i*2*pi/64),.69*sin(i*2*pi/64),.06) for i in range(64)],.007,edge,turret,True)
    rod('Rear exhaust pipe',(-1.75,side*.65,1.02),(-1.90,side*.65,1.02),.04,steel)
# Translucent 3D smoke shells, authored geometry flames and sparks.
def smoke_mat():
    # Real translucent 3D shells: faster CPU previews, no OpenVDB grid conversion.
    m=bpy.data.materials.new('Smoke • noise faded 3D shell');m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    out=n.new('ShaderNodeOutputMaterial');diff=n.new('ShaderNodeBsdfDiffuse');diff.inputs['Color'].default_value=(.12,.105,.085,1);diff.inputs['Roughness'].default_value=1
    clear=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');l.new(clear.outputs[0],mix.inputs[1]);l.new(diff.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
    geom=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';l.new(geom.outputs['Normal'],dot.inputs[0]);l.new(geom.outputs['Incoming'],dot.inputs[1])
    absolute=n.new('ShaderNodeMath');absolute.operation='ABSOLUTE';l.new(dot.outputs['Value'],absolute.inputs[0])
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=7;noise.inputs['Detail'].default_value=3
    mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(noise.outputs['Fac'],mask.inputs[0]);l.new(absolute.outputs[0],mask.inputs[1])
    density=n.new('ShaderNodeMath');density.operation='MULTIPLY';density.inputs[1].default_value=.32;l.new(mask.outputs[0],density.inputs[0]);l.new(density.outputs[0],mix.inputs[0])
    return m
smoke=smoke_mat()
def emissive(name,color,strength):
    m=bpy.data.materials.new(name);m.use_nodes=True;s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Emission Color'].default_value=(*color,1);s.inputs['Emission Strength'].default_value=strength;s.inputs['Roughness'].default_value=.8;return m
flame=emissive('Flame amber mantle',(1,.09,.003),1.6)
core=emissive('Flame warm core',(1,.38,.025),2.2)
spark=emissive('Hot orange metal spark',(1,.35,.025),2)
for i in range(9):
    o=sphere(f'Exhaust wisp {i}',(0,0,0),(1,1,1),smoke,root);o['effect']='exhaust';o['index']=i
for i in range(12):
    o=sphere(f'Gun smoke {i}',(0,0,0),(1,1,1),smoke,gun);o['effect']='gun_smoke';o['index']=i
for i in range(14):
    o=sphere(f'Wreck smoke {i}',(0,0,0),(1,1,1),smoke,root);o['effect']='wreck_smoke';o['index']=i
for i in range(10):
    o=rod(f'Impact spark {i}',(0,0,0),(.06,0,.006),.004,spark,root);o['effect']='spark';o['index']=i
for i in range(6):
    o=ringmesh(f'Muzzle flame {i}',[(0,0,0,.045,.045),(0,0,.18,.10,.07),(.015,0,.42,.002,.002)],core if i<2 else flame,gun,10)
    o['effect']='flash';o['index']=i;o.rotation_euler[1]=pi/2
for o in bpy.data.objects:
    if 'effect' in o:o.scale=(1,)*3;o.hide_render=True

sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.cycles.transparent_max_bounces=24
sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.film_transparent=True
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.color=(.20,.20,.20)
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
bpy.ops.object.camera_add(location=(6,-14,3.3));cam=bpy.context.object;cam.name='Painting camera';cam.rotation_euler=(Vector((.20,0,.86))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=5.35;sc.camera=cam
for name,loc,power,size,col in [('Warm upper left',(-3,-4,7),650,4.0,(1,.83,.65)),('Soft cool fill',(5,1,5),210,4,(.88,.93,1)),('Rear rim',(-2,4,5),280,3,(.80,.89,1)),('Front bounce',(4,-6,2.5),70,4,(1,.86,.67))]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power*.55;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
for o in list(bpy.data.objects):
    if o.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
sc['asset']='main-battle-tank';sc['source']='Original geometry matched to Legatum tank painting; no national markings in reference.'
sc['track_length']=LENGTH
sc['track_circles']=__import__('json').dumps({str(side):circles for side in [-1,1]})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'main-battle-tank-built.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'main-battle-tank-plain.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'main-battle-tank.blend'))
print('TANK_BUILT',len(bpy.data.objects),'objects')
