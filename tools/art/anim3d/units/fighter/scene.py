"""Original full-volume propeller fighter, frozen painting UVs and mechanical rig.
Run only through the plain `blender` gate. No billboard or alpha-shaped geometry.
"""
import bpy, bmesh, math, os, json, sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']); M=R/'masters/fighter'; A=R/'assets/fighter'
M.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.use_denoising=True
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
sc.view_settings.view_transform='AgX'
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.50,.55,.65,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.35
look=Vector((0,0,1.7)); direction=Vector((4.5,-8.9,3.2)).normalized()
bpy.ops.object.camera_add(location=look+direction*18);cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=5.5;sc.camera=cam
right=cam.rotation_euler.to_matrix()@Vector((1,0,0));up=cam.rotation_euler.to_matrix()@Vector((0,1,0));PP=256/5.5

def at(sx,sy,y=0):
    x=((sx-128)/PP-right.y*y)/right.x
    z=( (128-sy)/PP-up.x*x-up.y*y)/up.z+1.7
    return Vector((x,y,z))

def plane(sx,sy,z):
    a=(sx-128)/PP;b=(128-sy)/PP-up.z*(z-1.7)
    det=right.x*up.y-right.y*up.x
    return Vector(((a*up.y-right.y*b)/det,(right.x*b-a*up.x)/det,z))

def mat(name,color,metal=0,rough=.65):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=140;noise.inputs['Detail'].default_value=3
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.008;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=tuple(v*.65 for v in color)+(1,);ramp.color_ramp.elements[1].color=tuple(min(1,v*1.2) for v in color)+(1,);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],s.inputs['Base Color'])
    return m
olive=mat('Paint • worn olive',(.24,.25,.12));silver=mat('Aluminium • brushed worn',(.58,.56,.48),1,.43)
stone=mat('Cream stone • E9CFA0',(.815,.624,.352),0,.83);black=mat('Propeller • charcoal',(.038,.034,.026),0,.52);glass=mat('Canopy • smoked glass',(.09,.12,.13),0,.20);brass=mat('Exhaust • burnished bronze',(.25,.14,.065),1,.46)
plain=mat('Plain clay',(.46,.45,.41));yellow=mat('Blade tip • ochre',(.60,.40,.035))

def empty(name,loc,parent=None):
    o=bpy.data.objects.new(name,None);sc.collection.objects.link(o);o.location=loc;o.parent=parent;return o
root=empty('RIG-flight',(0,0,2.15)); parts=[]

def mesh(name,verts,faces,material,parent=root,bevel=.015):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o);o.data.materials.append(material)
    for p in me.polygons:p.use_smooth=True
    if bevel:
        mod=o.modifiers.new('Rounded manufactured edges','BEVEL');mod.width=bevel;mod.segments=3
    if parent:
        o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted()
    parts.append(o);return o

def finish(o,name,material,parent=root):
    o.name=name;o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    if parent:
        world=o.matrix_world.copy();o.parent=parent;o.matrix_world=world
    parts.append(o);return o

def ellipsoid(name,loc,scale,material,parent=root):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=loc);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,material,parent)

def rod(name,a,b,radius,material,parent=root):
    a,b=Vector(a),Vector(b);d=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=radius,depth=d.length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return finish(o,name,material,parent)

bpy.context.view_layer.update()
# Lathed, smoothly lofted elliptical fuselage. Each station has physical breadth.
stations=[(42,85,2,.055),(52,88,5,.10),(70,95,10,.18),(95,103,15,.27),(120,109,18,.32),(146,112,18,.34),(174,113,17,.34),(197,110,14,.28),(207,107,9,.23)]
verts=[];faces=[]
for sx,sy,r,ry in stations:
    c=at(sx,sy)
    for j in range(48):
        t=2*math.pi*j/48;verts.append(c+Vector((0,ry*math.cos(t),(r+(4 if 65<=sx<=146 and math.sin(t)>0 else 0))/PP/up.z*math.sin(t))))
for k in range(len(stations)-1):
    for j in range(48):a=k*48+j;b=k*48+(j+1)%48;faces.append((a,b,b+48,a+48))
faces += [tuple(range(47,-1,-1)),tuple((len(stations)-1)*48+j for j in range(48))]
fuselage=mesh('Fuselage • elliptical riveted monocoque',verts,faces,silver,bevel=0)
sub=fuselage.modifiers.new('Loft smoothing','SUBSURF');sub.levels=sub.render_levels=2
# Airfoil wings are closed solids, not planes; outline follows source planform.
def wing(name,outline,z):
    perimeter=[plane(x,y,z) for x,y in outline];center=sum(perimeter,Vector())/len(perimeter);v=[]
    # Convex top/bottom airfoil skin with thickness and edge roundover.
    for height in (.0,.075,-.035):
        if height==0:v.extend(perimeter)
        else:v.append(center+Vector((0,0,height)))
    n=len(perimeter);f=[]
    for j in range(n):f.extend([(j,(j+1)%n,n),(j,n+1,(j+1)%n)])
    o=mesh(name,v,f,olive,bevel=.022);return o
near=wing('Port wing • thick tapered airfoil',[(153,117),(130,113),(90,121),(19,148),(17,151),(31,155),(74,147),(135,131),(153,125)],2.03)
far=wing('Starboard wing • thick tapered airfoil',[(147,104),(169,88),(214,64),(237,57),(242,60),(227,83),(198,107),(162,121)],2.10)
wing('Port tailplane',[(66,79),(47,81),(14,91),(16,94),(49,91),(75,85)],2.23)
wing('Starboard tailplane',[(54,79),(79,67),(90,66),(91,68),(69,81)],2.23)
# Vertical tail is extruded with actual thickness.
outline=[(33,81),(35,43),(40,40),(46,41),(56,70),(63,78)]
v=[at(x,y,side) for side in (-.055,.055) for x,y in outline];n=len(outline)
fin=mesh('Vertical stabilizer • tapered fin',v,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)],olive)
# Canopy dome is its own thick 3D shell, with raised framing.
canopy=ellipsoid('Canopy • cockpit blister',at(128,85),(.46,.245,.23),glass)
for sx in (114,134,143):
    pts=[]
    for j in range(13):
        t=math.pi*j/12;c=at(sx,88);pts.append(c+Vector((0,.24*math.cos(t),.22*math.sin(t))))
    for a,b in zip(pts,pts[1:]):rod('Canopy frame',a,b,.012,olive)
# Spinner, shaft and four independent physical blades.
spinner=ellipsoid('Spinner • olive ogive',at(217,106),(.34,.19,.19),olive)
prop=empty('RIG-propeller',at(209,106),root);prop.matrix_world.translation=at(209,106)
for j in range(4):
    t=math.radians(32)+j*math.pi/2
    center=at(210,106);radial=Vector((0,math.cos(t),math.sin(t)));tangent=Vector((0,-math.sin(t),math.cos(t)))
    pts=[center+radial*r+tangent*w+Vector((dx,0,0)) for r,w,dx in [( .13,-.035,0),(.80,-.075,.02),(.98,-.02,.04),(.98,.025,.06),(.60,.10,.04),(.13,.035,0)]]
    v=pts+[p+Vector((.025,0,0)) for p in pts];n=len(pts)
    blade=mesh('Propeller blade',v,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)],black,parent=None,bevel=.012)
    world=blade.matrix_world.copy();blade.parent=prop;blade.matrix_world=world
# Exhaust stubs, tiny hollow mouths (no national markings).
for side in (-1,1):
    for j in range(5):
        a=at(173+j*5,108,side*.30);b=a+Vector((-.04,side*.10,0))
        rod('Exhaust pipe',a,b,.035,brass);ellipsoid('Exhaust cavity',b,(.028,.015,.026),black)
# Single stationary warm cream base and curved tapered support.
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1.065,depth=.18,location=(-.02,0,.13));base=finish(bpy.context.object,'BASE • stationary cream stone',stone,None)
be=base.modifiers.new('Soft stone lip','BEVEL');be.width=.045;be.segments=4
support_outline=[(96,188),(102,174),(111,153),(119,136),(129,133),(123,153),(122,170),(128,184),(142,193),(127,195)]
v=[at(x,y,side) for side in (-.12,.12) for x,y in support_outline];n=len(support_outline)
support=mesh('DISPLAY • curved stone pedestal',v,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)],stone,None,.035)
# Restrained geometric effects, keyed visibility (never zero scale / volume grids).
flashmat=mat('Muzzle flash • amber',(.9,.32,.025));s=flashmat.node_tree.nodes.get('Principled BSDF');s.inputs['Emission Color'].default_value=(1,.35,.02,1);s.inputs['Emission Strength'].default_value=3
for j in range(2):
    o=ellipsoid('FX-flash-'+str(j),plane(99+j*12,130,2.05),(.18,.035,.035),flashmat);o.hide_render=True
for name,loc,energy,size,col in [('key',(-3,-5,8),750,5,(1,.91,.76)),('fill',(5,-2,4),180,4,(.78,.86,1)),('rim',(1,5,7),450,3,(.72,.84,1))]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,2))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
# Apply geometry modifiers before projection, so projected UVs stay calibrated.
for o in parts:
    bpy.context.view_layer.objects.active=o
    for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
# Preserve the actual plain geometry stage as an editable file.
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
image=bpy.data.images.load(str(A/'projection.png'));image.pack();toward=direction
records=[]
for o in parts:
    if o.name.startswith('FX-'):continue
    uv=o.data.uv_layers.new(name='Frozen rest-camera');attr=o.data.color_attributes.new(name='Projection confidence',type='FLOAT_COLOR',domain='CORNER')
    nm=o.matrix_world.to_3x3().inverted().transposed()
    for p in o.data.polygons:
        for li in p.loop_indices:
            vert=o.data.vertices[o.data.loops[li].vertex_index];q=world_to_camera_view(sc,cam,o.matrix_world@vert.co);uv.data[li].uv=(q.x,q.y)
            facing=max(0,min(1,((nm@vert.normal).normalized().dot(toward)-.02)/.25));attr.data[li].color=(facing,facing,facing,1)
    material=o.data.materials[0].copy();o.data.materials.clear();o.data.materials.append(material);nodes=material.node_tree.nodes;links=material.node_tree.links;s=nodes.get('Principled BSDF')
    original=s.inputs['Base Color'].links[0].from_socket
    uvnode=nodes.new('ShaderNodeUVMap');uvnode.uv_map=uv.name;tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.extension='CLIP';links.new(uvnode.outputs[0],tex.inputs['Vector'])
    confidence=nodes.new('ShaderNodeVertexColor');confidence.layer_name=attr.name;mask=nodes.new('ShaderNodeMath');mask.operation='MULTIPLY';links.new(confidence.outputs[0],mask.inputs[0]);links.new(tex.outputs['Alpha'],mask.inputs[1])
    mix=nodes.new('ShaderNodeMixRGB');links.new(mask.outputs[0],mix.inputs[0]);links.new(original,mix.inputs[1]);links.new(tex.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],s.inputs['Base Color'])
    emission=nodes.new('ShaderNodeEmission');links.new(mix.outputs[0],emission.inputs[0]);mixshader=nodes.new('ShaderNodeMixShader');factor=nodes.new('ShaderNodeMath');factor.operation='MULTIPLY';factor.inputs[1].default_value=.72;links.new(mask.outputs[0],factor.inputs[0]);links.new(factor.outputs[0],mixshader.inputs[0]);links.new(s.outputs[0],mixshader.inputs[1]);links.new(emission.outputs[0],mixshader.inputs[2]);links.new(mixshader.outputs[0],nodes.get('Material Output').inputs[0])
    records.append({'mesh':o.name,'verts':len(o.data.vertices),'projection':'frozen camera on volumetric geometry','hidden_fill':'procedural worn matching pigment / brushed metal'})
bpy.ops.wm.save_as_mainfile(filepath=str(M/'fighter.blend'))
(M/'geometry.json').write_text(json.dumps({'blender':bpy.app.version_string,'meshes':records,'camera':{'ortho_scale':5.5,'direction':list(direction)},'rig':['RIG-flight','RIG-propeller'],'base_color':'#E9CFA0'},indent=2))
print('FIGHTER BUILD COMPLETE',len(parts))
