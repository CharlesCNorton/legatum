"""Original, articulated WWII tank. Run only through vehicles/render.sh / blender-slot.
All modelling is geometry; paint.py adds UV brushwork later. No billboard subject/effects.
"""
import bpy, math, os, random, json
from pathlib import Path
from mathutils import Vector
from math import pi, sin, cos
ROOT = Path(os.environ['ANIM_ROOT'])
MASTER = ROOT/'masters/tank'
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
edge=material('Dusty rubbed edges',(.15,.105,.035),(.43,.30,.11),.4,.57,37,.005)
steel=material('Track steel • worn and earth packed',(.065,.057,.035),(.23,.20,.12),.65,.66,19,.013)
rubber=material('Dust embedded in rubber',(.028,.025,.018),(.095,.077,.046),0,.92,22,.014)
mud=material('Dry mud and road dust',(.13,.095,.039),(.31,.23,.115),0,.95,25,.025)
rust=material('Exposed dark rust chips',(.065,.025,.009),(.19,.09,.026),.35,.83,30,.004)
black=material('Recessed apertures',(.022,.019,.008),(.060,.049,.022),.2,.85)
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
turret=empty('Turret traverse',root,(.2,0,1.75))
gun=empty('Gun recoil',turret,(.55,0,.20))
turret.rotation_euler[2]=math.radians(15)
gun.rotation_euler[1]=math.radians(-22)

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

base=cyl('Stationary cream stone base',(0,0,.12),2.20,.22,stone,None,verts=128)
cube('Lower hull',(-.05,0,.94),(2.85,1.64,.58),paint)
# Sloped glacis and shoulders, with deliberate steel thickness.
vs=[(-1.57,-.87,1.13),(1.56,-.87,1.13),(1.56,.87,1.13),(-1.57,.87,1.13),
    (-1.35,-.68,1.72),(.76,-.68,1.72),(.76,.68,1.72),(-1.35,.68,1.72)]
fs=[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
me=bpy.data.meshes.new('sloped armour');me.from_pydata(vs,[],fs);me.update(); hull=bpy.data.objects.new('Sloped upper hull',me);bpy.context.collection.objects.link(hull);finish(hull,hull.name,paint,root,.075)
sphere('Rounded transmission nose',(1.33,0,.94),(.40,.79,.39),paint)
for side in [-1,1]:
    o=cube('Glacis driver hatch',(.86,side*.43,1.68),(.33,.30,.04),paint);o.rotation_euler[1]=.55
    rod('Driver hatch hinge',(.72,side*.43-.13,1.75),(.72,side*.43+.13,1.75),.018,edge)
for side in [-1,1]:
    tube('Transmission casting seam',[(1.33+.32*cos(a*pi/32),side*.48,.94+.31*sin(a*pi/32)) for a in range(-12,17)],.012,edge)
sphere('Hull MG ball',(1.23,-.29,1.43),(.13,.12,.11),paint)
rod('Hull MG barrel',(1.31,-.29,1.43),(1.51,-.29,1.46),.023,steel)
rod('Rear shovel wooden handle',(-1.37,-.91,1.38),(-.61,-.91,1.38),.018,edge)
o=cube('Rear shovel blade',(-.52,-.91,1.38),(.21,.026,.16),steel,bevel=.03)
for x in [-1.18,-.73]:cube('Tool retaining strap',(x,-.927,1.38),(.035,.025,.10),edge,bevel=.006)
cyl('Turret bearing',(.2,0,1.73),.70,.12,steel)
cast=ringmesh('Rounded cast turret',[(-.07,0,.02,.69,.60),(-.07,0,.10,.74,.64),(-.1,0,.46,.75,.61),(-.13,0,.67,.61,.49),(-.15,0,.73,.49,.40)],paint,turret)
# Casting seam catches a thin dusty highlight; no invented insignia (painting has none).
tube('Turret casting seam',[( -.07+.696*cos(i*2*pi/64),.607*sin(i*2*pi/64),.105) for i in range(64)],.009,edge,turret,True)
cyl('Closed commander cupola',(-.22,0,.77),.30,.12,paint,turret)
cyl('Cupola top bevel',(-.22,0,.84),.25,.045,edge,turret)
for a in range(0,360,60):
    q=math.radians(a); o=cube('Cupola periscope',(-.22+.28*cos(q),.28*sin(q),.785),(.11,.045,.052),black,turret,.005);o.rotation_euler[2]=q+pi/2
cube('Closed hatch seam',(-.22,0,.866),(.39,.015,.008),black,turret,.002)
tube('Hatch handle',[(-.32,-.10,.87),(-.32,-.10,.91),(-.18,-.10,.91),(-.18,-.10,.87)],.012,edge,turret)
sphere('Rounded mantlet',(.035,0,0),(.24,.36,.29),paint,gun)
cyl('Mantlet sleeve',(.18,0,0),.125,.28,paint,gun,'X')
cyl('Short 75 mm barrel',(.77,0,0),.057,1.10,paint,gun,'X')
cyl('Worn muzzle rim',(1.325,0,0),.061,.055,edge,gun,'X')
cyl('Dark muzzle bore',(1.355,0,0),.043,.005,black,gun,'X')
for side in [-1,1]:
    y=side*.90
    cube('Raised track fender',(-.02,y,1.26),(3.42,.48,.075),paint,bevel=.018)
    # Lower dust stripe, headlights and towing eyes.
    tube('Fender folded edge',[(-1.72,y+side*.24,1.24),(1.68,y+side*.24,1.24)],.018,edge)
    cyl('Headlamp housing',(1.00,side*.66,1.58),.09,.10,paint,axis='X')
    cyl('Headlamp dusty glass',(1.057,side*.66,1.58),.066,.008,edge,axis='X')
    for x,z in [(1.46,1.24),(-1.50,1.17)]:
        tube('Tow eye',[(x+.06*cos(a*2*pi/24),side*.60,z+.075*sin(a*2*pi/24)) for a in range(24)],.022,edge,closed=True)
    # Forward fender slopes down with the glacis.
    o=cube('Front mudguard',(1.65,y,1.16),(.36,.47,.05),paint);o.rotation_euler[1]=.45
    # 6 road wheels in three visibly paired bogies.
    for idx,x in enumerate([-1.04,-.62,-.20,.22,.64,1.06]):
        wheel=empty(f'Road wheel pivot {side} {idx}',root,(x,side*.98,.61));wheel['wheel']=True
        cyl('Rubber wheel rim',(0,0,0),.28,.26,rubber,wheel,'Y')
        cyl('Cast wheel dished face',(0,side*.145,0),.225,.025,paint,wheel,'Y')
        cyl('Wheel hub',(0,side*.18,0),.072,.09,edge,wheel,'Y')
        tube('Wheel outer worn lip',[(.222*cos(a*2*pi/40),side*.165,.222*sin(a*2*pi/40)) for a in range(40)],.009,edge,wheel,True)
    for idx,x in enumerate([-.83,.01,.85]):
        cube('VVSS bogie block',(x,side*1.17,.85),(.19,.16,.36),paint,bevel=.024)
        for xx in [-.14,.14]:rod('Bogie suspension arm',(x,side*1.19,.76),(x+xx,side*1.19,.55),.043,paint)
        for xx in [-.047,0,.047]:rod('Vertical spring rib',(x+xx,side*1.267,.75),(x+xx,side*1.267,1.01),.012,edge)
        cube('Spring cover',(x,side*1.18,1.04),(.35,.22,.07),paint)
        cyl('Return roller',(x,side*.99,1.13),.085,.22,steel,axis='Y')
    for x in [-1.39,1.39]:
        sprocket=empty(f'Sprocket pivot {side} {x}',root,(x,side*.98,.79));sprocket['wheel']=True
        cyl('Drive sprocket body',(0,0,0),.32,.25,steel,sprocket,'Y')
        cyl('Drive wheel face',(0,side*.145,0),.255,.022,paint,sprocket,'Y')
        cyl('Drive hub',(0,side*.18,0),.10,.07,edge,sprocket,'Y')
        for j in range(12):
            a=j*2*pi/12
            o=cube('Sprocket tooth',(.32*cos(a),0,.32*sin(a)),(.08,.29,.065),edge,sprocket,.009);o.rotation_euler[1]=-a
            cyl('Sprocket recess',(.185*cos(a),side*.16,.185*sin(a)),.037,.008,black,sprocket,'Y',12)
# Real separate links following a capsule. Each link and raised grouser move around it.
TRACK_R=.40; TRACK_HALF=1.39; TRACK_Z=.79
LENGTH=4*TRACK_HALF+2*pi*TRACK_R

def trackpoint(t):
    d=(t%1)*LENGTH
    if d<2*TRACK_HALF:return (-TRACK_HALF+d,TRACK_Z+TRACK_R,0)
    d-=2*TRACK_HALF
    if d<pi*TRACK_R:
        a=pi/2-d/TRACK_R;return (TRACK_HALF+TRACK_R*cos(a),TRACK_Z+TRACK_R*sin(a),pi/2-a)
    d-=pi*TRACK_R
    if d<2*TRACK_HALF:return (TRACK_HALF-d,TRACK_Z-TRACK_R,pi)
    d-=2*TRACK_HALF;a=-pi/2-d/TRACK_R
    return (-TRACK_HALF+TRACK_R*cos(a),TRACK_Z+TRACK_R*sin(a),pi/2-a)
for side in [-1,1]:
    for i in range(62):
        x,z,a=trackpoint(i/62)
        link=empty(f'Track link {side} {i}',root,(x,side*.99,z));link.rotation_euler[1]=a;link['track_phase']=i/62;link['track_side']=side
        cube('Forged track shoe',(0,0,0),(.115,.41,.055),steel,link,.008)
        cube('Polished raised grouser',(0,0,.035),(.033,.385,.026),edge,link,.005)
        for yy in [-.21,.21]:cyl('Track hinge pin',(.048,yy,0),.022,.03,edge,link,'Y',12)
# Rear deck equipment, louvres, caps, hinges, tie downs and subtle field wear.
cube('Rear engine grille',(-1.03,0,1.725),(.60,.75,.025),black)
for i in range(10):cube('Engine cooling louvre',(-1.28+i*.055,0,1.746),(.028,.72,.021),paint,bevel=.003)
for side in [-1,1]:
    cube('Rear stowage box',(-1.05,side*.67,1.67),(.66,.41,.22),paint)
    cube('Stowage box lid',(-1.05,side*.67,1.79),(.68,.43,.035),edge)
    for xx in [-1.26,-.86]:cube('Stowage latch',(xx,side*.872,1.73),(.045,.024,.11),edge,bevel=.006)
canvas=material('Olive canvas stowage',(.06,.064,.025),(.19,.18,.08),0,.93,90,.006)
vs=[]; fs=[]
for j in range(13):
    for i in range(21):
        x=-1.30+i*.030; y=-.35+j*.025
        z=1.79+.026*sin(i*.9)+.014*cos(j*1.7+i*.4)
        vs.append((x,y,z))
for j in range(12):
    for i in range(20):
        a=j*21+i;fs.append((a,a+1,a+22,a+21))
me=bpy.data.meshes.new('Folded canvas');me.from_pydata(vs,[],fs);me.update()
o=bpy.data.objects.new('Folded deck blanket',me);bpy.context.collection.objects.link(o);finish(o,o.name,canvas,root,0,True)
mod=o.modifiers.new('Real canvas thickness','SOLIDIFY');mod.thickness=.035
bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
for x in [-1.20,-.83]:
    cube('Canvas retaining strap',(x,-.20,1.825),(.035,.34,.018),edge,bevel=.005)
    tube('Strap buckle',[(x-.026,-.27,1.84),(x+.026,-.27,1.84),(x+.026,-.20,1.84),(x-.026,-.20,1.84)],.006,steel,closed=True)
for y in [-.28,0,.28]:
    cube('Rear deck jerrican',(-1.34,y,1.96),(.18,.22,.37),paint)
    tube('Jerrican handle',[(-1.39,y-.06,2.15),(-1.39,y-.06,2.20),(-1.30,y-.06,2.20),(-1.30,y-.06,2.15)],.015,edge)
    tube('Jerrican stamped rib',[(-1.438,y-.08,1.85),(-1.438,y+.08,2.07)],.009,edge)
    tube('Jerrican stamped rib',[(-1.438,y+.08,1.85),(-1.438,y-.08,2.07)],.009,edge)
for side in [-1,1]:
    # Hull weld and stowage handles; fine enough not to become white outlines.
    tube('Hull shoulder weld',[(-1.32,side*.69,1.69),(.73,side*.69,1.69),(1.53,side*.87,1.15)],.011,edge)
    for x in [-.55,.45]:tube('Turret lifting eye',[(x-.06,side*.52,.34),(x-.06,side*.59,.39),(x+.03,side*.59,.43),(x+.06,side*.52,.39)],.018,edge,turret)
    for x in [-1.2,-.6,0,.6,1.2]:
        sphere('Hull attachment bolt',(x,side*.899,1.22),(.025,.014,.025),edge)
    rod('Rear exhaust pipe',(-1.57,side*.56,1.04),(-1.72,side*.56,1.08),.06,steel)
# Original chipped paint: actual shallow irregular patches on both armour flanks.
for side in [-1,1]:
    for i in range(65):
        x=random.uniform(-1.25,.7); z=random.uniform(1.31,1.64)
        y=side*(.87-(z-1.13)*(.19/.59)+.004)
        size=random.uniform(.005,.017)
        o=sphere('Irregular oxide chip',(x,y,z),(size,.004,size*random.uniform(.25,.75)),rust)
        if i%3==0:sphere('Chip lower worn lip',(x,y+side*.002,z-.007),(size*.8,.003,.003),edge)
# Fine dried mud along the running gear, restrained and grounded.
for side in [-1,1]:
    for i in range(100):
        x=random.uniform(-1.50,1.50); z=random.uniform(.42,1.18)
        if .69<z<1.05:continue
        sphere('Packed earth fleck',(x,side*1.205,z),(random.uniform(.008,.030),.008,random.uniform(.008,.026)),mud)

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
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.25
bpy.ops.object.camera_add(location=(5.6,-10,4.2));cam=bpy.context.object;cam.name='Painting camera';cam.rotation_euler=(Vector((0,0,1.02))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.95;sc.camera=cam
for name,loc,power,size,col in [('Warm upper left',(-3,-4,7),650,4.0,(1,.83,.65)),('Soft cool fill',(5,1,5),210,4,(.88,.93,1)),('Rear rim',(-2,4,5),280,3,(.80,.89,1)),('Front bounce',(4,-6,2.5),70,4,(1,.86,.67))]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
for o in list(bpy.data.objects):
    if o.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
sc['asset']='tank';sc['source']='Original geometry matched to Legatum tank painting; no national markings in reference.'
sc['track_length']=LENGTH
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'tank-built.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'tank-plain.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'tank.blend'))
print('TANK_BUILT',len(bpy.data.objects),'objects')
