"""Original full-volume propeller fighter, frozen painting UVs and mechanical rig.
Run only through the plain `blender` gate. No billboard or alpha-shaped geometry.
"""
import bpy, bmesh, math, os, json, sys
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']); M=R/'masters/fighter'; A=R/'assets/fighter'
M.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.use_denoising=True
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
# The source already includes painted illumination; preserve its display colours.
sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.50,.55,.65,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.35
look=Vector((0,0,1.7)); direction=Vector((4.5,-8.9,3.2)).normalized()
bpy.ops.object.camera_add(location=look+direction*18);cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=5.5;sc.camera=cam
right=cam.rotation_euler.to_matrix() @ Vector((1,0,0));up=cam.rotation_euler.to_matrix() @ Vector((0,1,0));PP=256/5.5

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
stone=mat('Cream stone • E9CFA0',(.815,.624,.352),0,.86);black=mat('Propeller • charcoal',(.038,.034,.026),0,.52);glass=mat('Canopy • smoked glass',(.09,.12,.13),0,.20);brass=mat('Exhaust • burnished bronze',(.25,.14,.065),1,.46)
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
# Smooth full-depth glazing with raised ribs seated on the ellipsoid itself.
canopy_center=at(129,82.5)
canopy=ellipsoid('Canopy • cockpit blister',canopy_center,(.50,.245,.25),glass)
for sx in (115,133,142):
    x=at(sx,82.5).x;fraction=math.sqrt(max(0,1-((x-canopy_center.x)/.50)**2))
    pts=[Vector((x,canopy_center.y+.248*fraction*math.cos(math.pi*j/20),canopy_center.z+.253*fraction*math.sin(math.pi*j/20))) for j in range(21)]
    for a,b in zip(pts,pts[1:]):rod('Canopy frame',a,b,.008,olive)
# Fit a circular propeller plane, retaining orthogonal blades and a real shaft.
# Source-painting opposite tips are not perfectly symmetric. This is an explicit
# least-squares compromise, not a flattened screen-space propeller.
u2=Vector((20,47));v2=Vector((-24,33));dot=u2.dot(v2);delta=v2.length_squared-u2.length_squared
du=math.sqrt((delta+math.sqrt(delta*delta+4*dot*dot))/2);dv=-dot/du
u=(right*u2.x+up*u2.y+direction*du)/PP
v=(right*v2.x+up*v2.y+direction*dv)/PP
radius=u.length;u.normalize();v.normalize();axis=u.cross(v).normalized()
if axis.x<0:axis=-axis;v=-v
center=at(210,106)
prop=empty('RIG-propeller',center,root);bpy.context.view_layer.update()
prop.matrix_world=Matrix.Translation(center) @ Matrix((axis,u,v)).transposed().to_4x4()
prop.rotation_mode='QUATERNION'
spinner=ellipsoid('Spinner • olive ogive',at(217,106),(.34,.19,.19),olive)
for j in range(4):
    t=j*math.pi/2;radial=u*math.cos(t)+v*math.sin(t);tangent=-u*math.sin(t)+v*math.cos(t)
    pts=[center+radial*r+tangent*w+axis*dx for r,w,dx in [(.13,-.025,0),(.70,-.075,.01),(radius*.96,-.035,.03),(radius,.0,.04),(.80,.08,.03),(.13,.025,0)]]
    verts=pts+[p+axis*.022 for p in pts];n=len(pts)
    blade=mesh('Propeller blade',verts,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)],black,parent=None,bevel=.008)
    # Distinct ochre-painted tips are part of the manufactured blade surface.
    blade.data.materials.append(yellow)
    bm=bmesh.new();bm.from_mesh(blade.data)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,
                          plane_co=center+radial*radius*.88,plane_no=radial,clear_inner=False,clear_outer=False)
    for face in bm.faces:
        if (face.calc_center_median()-center).dot(radial)>radius*.88:face.material_index=1
    bm.to_mesh(blade.data);bm.free()
    world=blade.matrix_world.copy();blade.parent=prop;blade.matrix_world=world
# Exhaust stubs, tiny hollow mouths (no national markings).
for side in (-1,1):
    for j in range(5):
        a=at(173+j*5,108,side*.30);b=a+Vector((-.04,side*.10,0))
        rod('Exhaust pipe',a,b,.035,brass);ellipsoid('Exhaust cavity',b,(.028,.015,.026),black)
# Single stationary warm cream base and curved tapered support.
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1.065,depth=.18,location=(-.02,0,.13));base=finish(bpy.context.object,'BASE • stationary cream stone',stone,None)
be=base.modifiers.new('Soft stone lip','BEVEL');be.width=.025;be.segments=5
support_outline=[(96,188),(102,174),(111,153),(119,136),(129,133),(123,153),(122,170),(128,184),(142,193),(127,195)]
v=[at(x,y,side) for side in (-.12,.12) for x,y in support_outline];n=len(support_outline)
support=mesh('DISPLAY • curved stone pedestal',v,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)],stone,None,.035)
# Put the pedestal pivot at its foot so the solid support can topple in death.
support_origin=Vector((-.02,0,.22))
for vertex in support.data.vertices:vertex.co-=support_origin
support.location=support_origin
# Restrained geometric effects, keyed visibility (never zero scale / volume grids).
flashmat=mat('Muzzle flash • amber',(.9,.32,.025));s=flashmat.node_tree.nodes.get('Principled BSDF');s.inputs['Emission Color'].default_value=(1,.35,.02,1);s.inputs['Emission Strength'].default_value=3
for j in range(2):
    o=ellipsoid('FX-flash-'+str(j),plane(99+j*12,130,2.05),(.18,.035,.035),flashmat);o.hide_render=True
for name,loc,energy,size,col in [('key',(-3,-5,8),430,5,(1,.97,.90)),('fill',(5,-2,4),86,4,(.90,.95,1)),('rim',(1,5,7),150,3,(.85,.92,1))]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,2))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
# Apply geometry modifiers before projection, so projected UVs stay calibrated.
for o in parts:
    bpy.context.view_layer.objects.active=o
    for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
# Physical stone only: no fixed painting shadow on the base when the aircraft moves.
base.data.materials[0]=stone.copy();bn=base.data.materials[0].node_tree.nodes;bl=base.data.materials[0].node_tree.links
bs=bn.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.815,.624,.352,1)
for link in list(bs.inputs['Base Color'].links):bl.remove(link)
for node in bn:
    if node.type=='BUMP':node.inputs['Strength'].default_value=.08;node.inputs['Distance'].default_value=.001
pig=bn.new('ShaderNodeEmission');pig.inputs[0].default_value=(.92,.73,.47,1)
path=bn.new('ShaderNodeLightPath');fac=bn.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.55;bl.new(path.outputs['Is Camera Ray'],fac.inputs[0])
mix=bn.new('ShaderNodeMixShader');bl.new(fac.outputs[0],mix.inputs[0]);bl.new(bs.outputs[0],mix.inputs[1]);bl.new(pig.outputs[0],mix.inputs[2]);bl.new(mix.outputs[0],bn.get('Material Output').inputs[0])
# Separate stone edge pigment preserves the painting's darker low rim.
rimstone=base.data.materials[0].copy();rimstone.name='Cream stone • warm darker rim'
rn=rimstone.node_tree.nodes
rn.get('Principled BSDF').inputs['Base Color'].default_value=(.62,.40,.19,1)
next(node for node in rn if node.type=='EMISSION').inputs[0].default_value=(.75,.51,.28,1)
base.data.materials.append(rimstone)
for polygon in base.data.polygons:
    if polygon.normal.z<.65:polygon.material_index=1
# Preserve the actual plain geometry stage as an editable file.
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
image=bpy.data.images.load(str(A/'projection.png'));image.pack();toward=direction
records=[]
for o in parts:
    if o.name.startswith(('FX-','BASE','Propeller blade')):continue
    uv=o.data.uv_layers.new(name='Frozen rest-camera');attr=o.data.color_attributes.new(name='Projection confidence',type='FLOAT_COLOR',domain='CORNER')
    nm=o.matrix_world.to_3x3().inverted().transposed()
    for p in o.data.polygons:
        for li in p.loop_indices:
            vert=o.data.vertices[o.data.loops[li].vertex_index];q=world_to_camera_view(sc,cam,o.matrix_world @ vert.co);uv.data[li].uv=(q.x,q.y)
            facing=max(0,min(1,((nm @ vert.normal).normalized().dot(toward)-.02)/.25));attr.data[li].color=(facing,facing,facing,1)
    material=o.data.materials[0].copy();o.data.materials.clear();o.data.materials.append(material);nodes=material.node_tree.nodes;links=material.node_tree.links;s=nodes.get('Principled BSDF')
    original=s.inputs['Base Color'].links[0].from_socket
    uvnode=nodes.new('ShaderNodeUVMap');uvnode.uv_map=uv.name;tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.extension='CLIP';links.new(uvnode.outputs[0],tex.inputs['Vector'])
    confidence=nodes.new('ShaderNodeVertexColor');confidence.layer_name=attr.name;mask=nodes.new('ShaderNodeMath');mask.operation='MULTIPLY';links.new(confidence.outputs[0],mask.inputs[0]);links.new(tex.outputs['Alpha'],mask.inputs[1])
    mix=nodes.new('ShaderNodeMixRGB');mix.name='Frozen source pigment';links.new(mask.outputs[0],mix.inputs[0]);links.new(original,mix.inputs[1]);links.new(tex.outputs['Color'],mix.inputs[2]);# The physical material retains unlit pigment, not the source illumination.
    links.new(original,s.inputs['Base Color'])
    emission=nodes.new('ShaderNodeEmission');links.new(mix.outputs[0],emission.inputs[0]);mixshader=nodes.new('ShaderNodeMixShader');factor=nodes.new('ShaderNodeMath');factor.operation='MULTIPLY';factor.inputs[1].default_value=.96;links.new(mask.outputs[0],factor.inputs[0]);factor.name='Paint coverage';path=nodes.new('ShaderNodeLightPath');camera=nodes.new('ShaderNodeMath');camera.operation='MULTIPLY';links.new(path.outputs['Is Camera Ray'],camera.inputs[0]);links.new(factor.outputs[0],camera.inputs[1]);links.new(camera.outputs[0],mixshader.inputs[0]);links.new(s.outputs[0],mixshader.inputs[1]);links.new(emission.outputs[0],mixshader.inputs[2]);links.new(mixshader.outputs[0],nodes.get('Material Output').inputs[0])
    records.append({'mesh':o.name,'verts':len(o.data.vertices),'projection':'frozen camera on volumetric geometry','hidden_fill':'procedural worn matching pigment / brushed metal'})
bpy.ops.wm.save_as_mainfile(filepath=str(M/'fighter.blend'))
(M/'geometry.json').write_text(json.dumps({'blender':bpy.app.version_string,'meshes':records,'camera':{'ortho_scale':5.5,'direction':list(direction)},'rig':['RIG-flight','RIG-propeller'],'base_color':'#E9CFA0'},indent=2))
print('FIGHTER BUILD COMPLETE',len(parts))
