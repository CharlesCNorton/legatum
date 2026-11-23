"""Original, articulated WWII tank. Run only through vehicles/render.sh / blender-slot.
All modelling is geometry; paint.py adds UV brushwork later. No billboard subject/effects.
"""
import bpy, math, os, random, json
from pathlib import Path
from mathutils import Vector
from math import pi, sin, cos
ROOT = Path(os.environ['ANIM_ROOT'])
MASTER = ROOT/'masters/panzer'
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
paint=material('Olive drab • mottled cast and rolled steel',(.21,.15,.055),(.52,.37,.15),0,.78,32,.004)
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
fill=n.new('ShaderNodeMixRGB'); fill.inputs[0].default_value=.22; l.new(s.inputs['Base Color'].links[0].from_socket,fill.inputs[1]); l.new(t.outputs['Color'],fill.inputs[2]); l.new(fill.outputs[0],s.inputs['Base Color'])
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
root=empty('Vehicle suspension root',loc=(0,0,0))
turret=empty('Turret traverse',root,(-.22,0,1.66))
gun=empty('Gun recoil',turret,(.66,0,.26))
turret.scale.z=1.12
turret.rotation_euler[2]=math.radians(13)
gun.rotation_euler[1]=math.radians(-21)

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
cube('Lower hull',(-.03,0,.85),(3.22,1.55,.66),paint)
# Properly closed plate-built hull with stepped deck and inclined glacis.
vs=[(-1.68,-.85,.93),(1.65,-.85,.93),(1.65,.85,.93),(-1.68,.85,.93),
    (-1.55,-.80,1.48),(1.10,-.80,1.48),(1.10,.80,1.48),(-1.55,.80,1.48)]
fs=[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
me=bpy.data.meshes.new('Rolled armour');me.from_pydata(vs,[],fs);me.update()
o=bpy.data.objects.new('Sloped upper hull',me);bpy.context.collection.objects.link(o);finish(o,o.name,paint,root,.022)
cube('Driver superstructure',(.62,0,1.49),(.85,1.46,.22),paint,bevel=.025)
for side in [-1,1]:
    y=side*.94
    cube('Fender rail',(0,y,1.18),(3.57,.45,.065),paint,bevel=.012)
    o=cube('Front mud flap',(1.63,y,1.03),(.37,.46,.06),paint);o.rotation_euler[1]=.62
    # Five separate thin overlapping Schuerzen plates; wheel bottoms stay exposed.
    for i in range(5):
        x=-1.28+i*.58
        o=cube('Hull skirt plate',(x,side*1.19,1.055),(.60,.045,.45),paint,bevel=.009)
        o.rotation_euler[0]=side*.08
        for xx in [x-.24,x+.24]:
            rod('Skirt hanger',(xx,side*1.01,1.37),(xx,side*1.20,1.25),.019,steel)
            sphere('Skirt fastener',(xx,side*1.225,1.23),(.019,.012,.019),edge)
    rod('Skirt support rail',(-1.60,side*1.18,1.29),(1.30,side*1.18,1.29),.018,edge)
    # Eight small road wheels, paired onto four leaf-spring bogies.
    for i in range(8):
        x=-1.15+i*.326
        wh=empty(f'Road wheel pivot {side} {i}',root,(x,side*.99,.51));wh['wheel_radius']=.215
        cyl('Rubber road wheel',(0,0,0),.215,.25,rubber,wh,'Y',32)
        cyl('Dished road wheel',(0,side*.14,0),.178,.025,paint,wh,'Y',32)
        cyl('Wheel hub',(0,side*.17,0),.064,.07,edge,wh,'Y',24)
        for j in range(8):
            a=2*pi*j/8;cyl('Wheel bolt',(.12*cos(a),side*.159,.12*sin(a)),.013,.018,edge,wh,'Y',8)
    for i in range(4):
        x=-.987+i*.652
        cube('Leaf spring bogie',(x,side*.97,.78),(.36,.24,.11),steel)
        for xx in [-.16,.16]:rod('Suspension arm',(x,side*1.0,.78),(x+xx,side*1.0,.51),.038,paint)
        cyl('Upper return roller',(x,side*.99,1.06),.085,.23,rubber,axis='Y',verts=24)
    for x in [-1.50,1.50]:
        wh=empty(f'Sprocket pivot {side} {x}',root,(x,side*.99,.67));wh['wheel_radius']=.295
        cyl('Drive sprocket',(0,0,0),.295,.24,steel,wh,'Y',40)
        cyl('Sprocket face',(0,side*.14,0),.235,.03,paint,wh,'Y',40)
        cyl('Sprocket hub',(0,side*.18,0),.08,.07,edge,wh,'Y',24)
        for j in range(14):
            a=j*2*pi/14;o=cube('Sprocket tooth',(.294*cos(a),0,.294*sin(a)),(.055,.27,.055),edge,wh,.005);o.rotation_euler[1]=-a
            cyl('Sprocket recess',(.16*cos(a),side*.159,.16*sin(a)),.026,.008,black,wh,'Y',12)
# Separate real shoes on a closed physical envelope, sampled at constant arc length.
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from runninggear import route
circles=[(-1.5,.67,.33),(1.5,.67,.33),(-1.15,.51,.24),(1.132,.51,.24)]
length,point=route(circles)
for side in [-1,1]:
    for i in range(72):
        x,z,a=point(i/72);link=empty(f'Track link {side} {i}',root,(x,side*.99,z));link.rotation_euler[1]=a;link['track_phase']=i/72;link['track_side']=side
        cube('Forged track shoe',(0,0,0),(.10,.40,.045),steel,link,.006)
        cube('Polished raised grouser',(0,0,.027),(.025,.39,.022),edge,link,.003)
        for yy in [-.204,.204]:cyl('Track hinge pin',(.04,yy,0),.018,.022,edge,link,'Y',8)
root['route_circles']=json.dumps(circles);root['route_length']=length
# Angular turret and spaced turret skirts (real thickness, open front).
cyl('Turret bearing',(-.22,0,1.59),.68,.10,steel)
cast=ringmesh('Angular turret',[(0,0,.0,.70,.59),(-.06,0,.48,.61,.49)],paint,turret,8)
for p in cast.data.polygons:p.use_smooth=False
bev=cast.modifiers.new('Plate edge bevel','BEVEL');bev.width=.018;bev.segments=3
bpy.context.view_layer.objects.active=cast;bpy.ops.object.modifier_apply(modifier=bev.name)
# Polygonal skirt band wraps rear and sides, retaining the mantlet aperture.
for a,b in [(35,90),(90,145),(145,195),(195,250),(250,325)]:
    a=math.radians(a);b=math.radians(b)
    pts=[(.82*cos(a),.72*sin(a),.05),(.82*cos(b),.72*sin(b),.05),(.76*cos(b),.67*sin(b),.51),(.76*cos(a),.67*sin(a),.51)]
    me=bpy.data.meshes.new('Turret skirt');me.from_pydata(pts,[],[(0,1,2,3)]);me.update()
    o=bpy.data.objects.new('Turret spaced skirt',me);bpy.context.collection.objects.link(o);finish(o,o.name,paint,turret)
    sol=o.modifiers.new('Steel thickness','SOLIDIFY');sol.thickness=.035;bev=o.modifiers.new('Skirt edge bevel','BEVEL');bev.width=.008;bev.segments=2
    for mod in list(o.modifiers):bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    rod('Turret skirt top edge',pts[2],pts[3],.009,edge,turret)
cyl('Commander cupola',(-.27,.02,.57),.25,.16,paint,turret)
cyl('Cupola hatch',(-.27,.02,.66),.25,.035,edge,turret)
for i in range(8):
    a=i*2*pi/8;o=cube('Cupola vision block',(-.27+.247*cos(a),.02+.247*sin(a),.585),(.095,.025,.047),black,turret,.004);o.rotation_euler[2]=a+pi/2
cube('Cupola hatch panel',(-.27,.02,.684),(.32,.24,.014),paint,turret,.01)
tube('Hatch handle',[(-.36,-.04,.70),(-.36,-.04,.74),(-.22,-.04,.74),(-.22,-.04,.70)],.012,edge,turret)
cube('Box mantlet',(0,0,0),(.28,.45,.34),paint,gun,.06)
cyl('Mantlet collar',(.18,0,0),.13,.25,paint,gun,'X')
cyl('Long gun barrel',(.91,0,0),.048,1.42,paint,gun,'X')
cyl('Gun sleeve',(.36,0,0),.075,.33,paint,gun,'X')
# Hollow two-chamber muzzle brake with actual lateral ports.
brake=cube('Two chamber muzzle brake',(1.70,0,0),(.25,.145,.135),paint,gun,.025)
for x in [1.64,1.74]:
    cutter=cube('Brake port cutter',(x,0,0),(.048,.24,.076),black,gun,0)
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=brake
    mod=brake.modifiers.new('Open lateral brake chamber','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
cyl('Muzzle bore',(1.829,0,0),.037,.006,black,gun,'X',24)
# Deck grilles, seams, towing eyes, hull MG and worn hardware.
cube('Engine grille',(-1.15,0,1.50),(.67,1.05,.02),black)
for i in range(12):cube('Engine louvre',(-1.45+i*.052,0,1.523),(.025,1.04,.024),paint,bevel=.003)
for side in [-1,1]:
    cube('Deck hatch',(.35,side*.46,1.614),(.35,.33,.022),paint,bevel=.012)
    cube('Driver vision slot',(1.057,side*.40,1.52),(.016,.22,.06),black,bevel=.004)
    for x in [-1.5,1.5]:
        tube('Tow eye',[(x+.06*cos(a*2*pi/20),side*.62,.99+.065*sin(a*2*pi/20)) for a in range(20)],.017,edge,closed=True)
    for x in [-1.35,-.6,.2,.9]:sphere('Fender bolt',(x,side*1.16,1.22),(.018,.018,.014),edge)
    rod('Skirt weld',(-1.50,side*.81,1.47),(1.0,side*.81,1.47),.009,edge)
sphere('Hull MG ball',(1.082,-.45,1.51),(.07,.08,.075),paint)
rod('Hull MG',(1.10,-.45,1.51),(1.30,-.45,1.51),.017,steel)
cyl('Rear exhaust',(-1.70,0,.96),.12,1.10,steel,axis='Y')
# Safe, solid smoke meshes; no volume grids and no zero scale.
smoke=material('Soot smoke',(.05,.045,.035),(.20,.18,.15),0,1,9,.02)
for i in range(6):
    o=sphere(f'Wreck smoke {i}',(-.8,0,1.7),(.13,.15,.19),smoke,root);o['effect']='smoke';o['index']=i;o.hide_render=True
flash=material('Muzzle flash',(.85,.23,.015),(1,.74,.25),0,.6)
s=flash.node_tree.nodes.get('Principled BSDF');s.inputs['Emission Color'].default_value=(1,.45,.06,1);s.inputs['Emission Strength'].default_value=1
for i in range(3):
    o=sphere(f'Muzzle flash {i}',(1.91+i*.09,0,0),(.13,.055+i*.008,.055+i*.008),flash,gun);o['effect']='flash';o.hide_render=True
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True
sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.film_transparent=True
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.color=(.20,.20,.20);sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
bpy.ops.object.camera_add(location=(5.7,-10,4.7));cam=bpy.context.object;cam.name='Painting camera';cam.rotation_euler=(Vector((.05,0,1.02))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.90;sc.camera=cam
for name,loc,power,size,col in [('Warm upper left',(-3,-4,7),650,4,(1,.87,.70)),('Soft fill',(4,-1,4),130,5,(.85,.91,1)),('Cool rim',(0,4,5),350,3,(.73,.84,1))]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
sc['unit']='panzer';sc['forward_axis']='+X';sc['rig']='rigid parent hierarchy, traverse/recoil and individual tracks/wheels'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'panzer-plain.blend'))
print('BUILD_READY',len(bpy.data.objects),'objects')
