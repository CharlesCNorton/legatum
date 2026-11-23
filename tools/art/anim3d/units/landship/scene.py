"""Full-depth WWI rhomboid landship. Camera registration edits geometry, not alpha.
No cards, billboard meshes, image-space deformation, or degenerate smoke.
"""
import bpy,bmesh,math,os,json,random,sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/landship';random.seed(20)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
right=Vector((.8660254,.5,0));up=Vector((-.08,.138564065,.987117014));view=right.cross(up)
k=256/5.7;target=right*(4/k)+up*(45/k)+Vector((0,0,.20))
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=target+view*12);cam=bpy.context.object;cam.name='CAM-painting';cam.data.type='ORTHO';cam.data.ortho_scale=5.7;aim(cam,target);sc.camera=cam
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
# Solve world X/Z at a known depth Y from painting landmarks.
def point(px,py,y):
    x=((px-128)/k+right.dot(target)-right.y*y)/right.x
    z=((128-py)/k+up.dot(target)-up.x*x-up.y*y)/up.z
    return (x,y,z)
def material(name,color,metal=0,rough=.75):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF')
    s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=85;noise.inputs['Detail'].default_value=3
    b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.25;b.inputs['Distance'].default_value=.008;l.new(noise.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],s.inputs['Normal'])
    return m
paint=material('MAT-ochre_painted_armour',(.23,.16,.075));track=material('MAT-dusty_worn_track',(.065,.040,.022),0,.85)
edge=material('MAT-rubbed_steel_edges',(.12,.075,.035),1,.78);dark=material('MAT-recess_black',(.022,.016,.009));mud=material('MAT-dried_mud',(.19,.11,.05))
stone=material('MAT-cream_E9CFA0',tuple(((v/255+.055)/1.055)**2.4 for v in (233,207,160)),0,.88)
# A generated painted-metal fill, blended to ochre; source pinned with prepare.py.
n=paint.node_tree.nodes;l=paint.node_tree.links;s=n.get('Principled BSDF');t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(R/'assets/landship/painted-olive.png'));t.projection='BOX';t.projection_blend=.3
co=n.new('ShaderNodeTexCoord');l.new(co.outputs['Generated'],t.inputs['Vector']);mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.65;mix.inputs[2].default_value=(.9,.63,.31,1);l.new(t.outputs['Color'],mix.inputs[1]);l.new(mix.outputs[0],s.inputs['Base Color'])
def empty(name,parent=None):
    o=bpy.data.objects.new(name,None);sc.collection.objects.link(o);o.parent=parent;return o
root=empty('RIG-chassis');gun=empty('RIG-sponson_recoil',root);hatch=empty('RIG-roof_hatch',root)
def finish(o,name,mat,parent=root,bevel=.012):
    o.name='GEO-'+name;o.data.materials.append(mat);o.parent=parent
    if bevel:
        mod=o.modifiers.new('Rounded machined edge','BEVEL');mod.width=bevel;mod.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    return o
def mesh(name,verts,faces,mat,parent=root,bevel=.012):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o)
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();return finish(o,name,mat,parent,bevel)
def prism(name,poly,y0,y1,mat=paint):
    a=[point(x,z,y0) for x,z in poly];v=a+[(x,y1,z) for x,y,z in a];n=len(a)
    return mesh(name,v,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat)
def cube(name,loc,scale,mat=paint,parent=root,bevel=.012):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,mat,parent,bevel)
def sphere(name,loc,r,mat=paint,parent=root):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=r,location=loc);o=bpy.context.object
    for p in o.data.polygons:p.use_smooth=True
    return finish(o,name,mat,parent,0)
def cylinder(name,a,b,r,mat=paint,parent=root):
    a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=(b-a).length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    return finish(o,name,mat,parent,.008)
outline=[(16,127),(24,112),(49,89),(66,80),(113,80),(145,90),(171,109),(185,124),(181,140),(164,157),(139,173),(119,179),(65,174),(34,160),(18,144)]
# The hull and both track housings are closed extruded volumes, 2.3m deep overall.
plate=prism('near_rhomboid_armour',outline,-1.10,-.78)
hull=prism('central_armoured_hull',outline,-.78,1.12)
far=prism('far_track_housing',outline,-1.10,-.78)
far.location.y=2.10
# Separate shoes on closed, arc-length sampled physical rhomboid routes.
route=[Vector(point(x,z,-1.10)) for x,z in outline];lengths=[0.]
for a,b in zip(route,route[1:]+route[:1]):lengths.append(lengths[-1]+(b-a).length)
L=lengths[-1]
def route_at(t,y):
    d=t%L
    for i in range(len(route)):
        if d<=lengths[i+1]:
            a=route[i];b=route[(i+1)%len(route)];p=a.lerp(b,(d-lengths[i])/(lengths[i+1]-lengths[i]));p.y=y
            return p,-math.atan2(b.z-a.z,b.x-a.x)
shoes=[]
for side,y in [('near',-.96),('far',1.14)]:
    for i in range(64):
        p,ang=route_at(L*i/64,y);o=cube(f'track_{side}_{i:02}',p,(L/64*.90,.36,.078),track,bevel=.013);o.rotation_euler.y=ang;o['track_distance']=L*i/64;o['track_y']=y;shoes.append(o)
        # Grousers are actual raised steel, parented to their shoe.
        bar=cube(f'grouser_{side}_{i:02}',(0,0,.044),(L/64*.24,.36,.024),edge,parent=o,bevel=.008)
# Rivet seams and solid panel relief across near plate.
for j,px in enumerate([43,63,93,121,143]):
    for py in range(93 if px<130 else 105,166,8):
        sphere(f'rivet_{j}_{py}',point(px,py,-1.125),.027,edge)
for i in range(len(outline)):
    a,b=outline[i],outline[(i+1)%len(outline)]
    for q in range(max(1,int(math.dist(a,b)/7))):
        t=q/max(1,int(math.dist(a,b)/7));px=a[0]*(1-t)+b[0]*t;py=a[1]*(1-t)+b[1]*t
        # inset toward plate centroid
        sphere(f'perimeter_rivet_{i}_{q}',point(px*.94+100*.06,py*.94+130*.06,-1.13),.024,edge)
# Sponson: deep enclosed polygon, barrel with actual hollow muzzle ring.
sponson=prism('sponson',[(69,99),(89,96),(118,101),(117,131),(99,137),(70,130)],-1.52,-.93)
for px in (72,115):
    for py in range(103,130,6):sphere(f'sponson_rivet_{px}_{py}',point(px,py,-1.54),.026,edge)
a=Vector(point(103,108,-1.57));direction=Vector((.90,-.43,.02));end=a+direction*.40
cylinder('gun_mantlet',a-direction*.08,a+direction*.08,.12,paint,gun)
barrel=cylinder('barrel',a,end,.068,track,gun)
# Remove the solid front cap so the annulus really opens onto the recessed bore.
bm=bmesh.new();bm.from_mesh(barrel.data)
front=[face for face in bm.faces if face.normal.dot(direction.normalized())>.99]
bmesh.ops.delete(bm,geom=front,context='FACES');bm.to_mesh(barrel.data);bm.free()
# Bore is recessed black with a projecting metal annulus.
axis=direction.normalized();u=axis.cross(Vector((0,0,1))).normalized();v=axis.cross(u);verts=[]
for dep,r in [(0,.068),(0,.042),(-.09,.042)]:
    for i in range(24):verts.append(tuple(end+axis*dep+r*(u*math.cos(i*math.tau/24)+v*math.sin(i*math.tau/24))))
faces=[]
for ring in range(2):
    for i in range(24):faces.append((ring*24+i,ring*24+(i+1)%24,(ring+1)*24+(i+1)%24,(ring+1)*24+i))
mesh('open_muzzle',verts,faces,edge,gun,0);cylinder('bore_dark',end-axis*.095,end-axis*.09,.042,dark,gun)
# Cab silhouette fits the characteristic low riveted roof on the painting.
cab=mesh('driver_cab',
    [point(x,y,-.05) for x,y in [(106,79),(112,60),(151,65),(153,80)]]+
    [point(x,y,1.1) for x,y in [(142,75),(148,56),(185,60),(190,77)]],
    [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],paint)
# Raised cab rivets fitted to painted landmarks.
for i,(px,py) in enumerate([(115,63),(126,65),(138,66),(149,67)]):
    sphere(f'cab_rivet_{i}',point(px,py,-.07),.024,edge)

for px in (119,139):
    loc=point(px,66,-.065);cube(f'vision_slot_{px}',loc,(.20,.025,.065),dark)
hatch.location=point(142,58,.42)
roof=cube('roof_hatch',(0,0,0),(.55,.45,.055),paint,hatch)
prism('side_access_hatch',[(32,114),(47,112),(47,140),(32,139)],-1.14,-1.09)
# Mud chips are restrained three-dimensional surface aggregates near ground contact.
for i in range(75):
    px=random.uniform(35,153);py=random.uniform(159,171);sphere(f'mud_chip_{i}',point(px,py,-1.14),random.uniform(.016,.035),mud)
# One low cream disc; never attached to moving chassis.
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=2.14,depth=.26,location=(0,0,.07));base=finish(bpy.context.object,'cream_stone_base',stone,None,.035)
for p in base.data.polygons:p.use_smooth=len(p.vertices)==4
# Closed, finite-size smoke meshes. Visibility is keyed later; no zero scaling.
smoke=material('MAT-smoke',(.16,.145,.12),0,1);sn=smoke.node_tree.nodes;sl=smoke.node_tree.links;so=sn.get('Material Output')
for link in list(so.inputs['Surface'].links):sl.remove(link)
vn=sn.new('ShaderNodeVolumePrincipled');vn.inputs['Color'].default_value=(.32,.29,.24,1)
noise=sn.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=6;noise.inputs['Detail'].default_value=2
ramp=sn.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=.30;ramp.inputs['From Max'].default_value=.72;ramp.inputs['To Min'].default_value=0;ramp.inputs['To Max'].default_value=2.0
sl.new(noise.outputs['Fac'],ramp.inputs['Value']);sl.new(ramp.outputs[0],vn.inputs['Density']);sl.new(vn.outputs[0],so.inputs['Volume']);effects=[]
for i in range(6):
    o=sphere(f'smoke_{i}',point(148+i*1.8,60-i*4.5,.4),.10+i*.018,smoke)
    for vert in o.data.vertices:
        vert.co *= 1+random.uniform(-.18,.18)
    o['effect']=True;o.hide_render=True;effects.append(o)
flash=material('MAT-flash',(.95,.47,.08));s=flash.node_tree.nodes.get('Principled BSDF');s.inputs['Emission Color'].default_value=(1,.4,.05,1);s.inputs['Emission Strength'].default_value=2
# A short, tapered asymmetric gas jet; no luminous billiard-ball flash.
verts=[tuple(end+axis*.025)]
for i in range(8):
    phi=i*math.tau/8;rr=.055*(1+.3*math.sin(i*4))
    verts.append(tuple(end+axis*.12+rr*(u*math.cos(phi)+v*math.sin(phi))))
verts.append(tuple(end+axis*.31))
f=mesh('muzzle_flash',verts,[(0,1+i,1+(i+1)%8) for i in range(8)]+[(9,1+(i+1)%8,1+i) for i in range(8)],flash,gun,0)
f['effect']=True;f.hide_render=True
# Recoil and disabled droop pivot at the mantlet, not the world origin.
for child in gun.children:child.location-=a
gun.location=a
for name,loc,energy,size,color in [('key',(-3,-4,7),650,5,(1,.90,.74)),('fill',(4,-4,4),170,5,(.84,.90,1)),('rim',(0,5,6),480,3,(.73,.84,1))]:
    data=bpy.data.lights.new('LGT-'+name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=color;o=bpy.data.objects.new(data.name,data);sc.collection.objects.link(o);o.location=loc;aim(o,(0,0,1))
sc.world.color=(.30,.30,.30);sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.cycles.max_bounces=4
sc['route']=json.dumps([list(p) for p in route]);sc['unit']='landship';sc['forward_axis']='+X';sc['track_length']=L;sc['source']='full-depth procedural geometry with frozen rest-camera UVs';sc['muzzle']=list(end);sc['barrel_axis']=list(direction)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
# Project the source onto actual finished surfaces. The coordinates stay on geometry.
tex=bpy.data.images.load(str(M/'textures/painting.png'));stone_tex=bpy.data.images.load(str(M/'textures/stone.png'));gun_tex=bpy.data.images.load(str(M/'textures/sponson.png'));materials={};records=[]
for o in list(sc.objects):
    if o.type!='MESH' or o.get('effect') or o.name=='GEO-bore_dark':continue
    me=o.data;uv=me.uv_layers.new(name='PaintingProjection');conf=me.color_attributes.new(name='PaintConfidence',type='FLOAT_COLOR',domain='CORNER')
    nm=o.matrix_world.to_3x3().inverted().transposed()
    for face in me.polygons:
        facing=max(0,min(1,((nm@face.normal).normalized().dot(view)+.03)/.24))
        for idx in face.loop_indices:
            p=world_to_camera_view(sc,cam,o.matrix_world@me.vertices[me.loops[idx].vertex_index].co);uv.data[idx].uv=(p.x,p.y);conf.data[idx].color=(facing,facing,facing,1)
    original=o.data.materials[0]
    key=original.name+('_sponson' if o.name=='GEO-sponson' else '')
    if key not in materials:
        mat=original.copy();mat.name=original.name+'_projected';materials[key]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF');out=n.get('Material Output')
        uvn=n.new('ShaderNodeUVMap');uvn.uv_map='PaintingProjection';t=n.new('ShaderNodeTexImage');t.image=stone_tex if 'cream' in original.name else gun_tex if o.name=='GEO-sponson' else tex;t.extension='EXTEND';l.new(uvn.outputs[0],t.inputs['Vector']);a=n.new('ShaderNodeVertexColor');a.layer_name='PaintConfidence'
        mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(a.outputs['Color'],mask.inputs[0]);l.new(t.outputs['Alpha'],mask.inputs[1])
        # Preserve hand-painted lighting on camera rays, while real BSDF handles bounce.
        lp=n.new('ShaderNodeLightPath');w=n.new('ShaderNodeMath');w.operation='MULTIPLY';l.new(mask.outputs[0],w.inputs[0]);l.new(lp.outputs['Is Camera Ray'],w.inputs[1])
        e=n.new('ShaderNodeEmission');l.new(t.outputs['Color'],e.inputs['Color'])
        if 'cream' in original.name:
            ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.3
            shade=n.new('ShaderNodeMixRGB');shade.blend_type='MULTIPLY';shade.inputs[0].default_value=.22
            l.new(t.outputs['Color'],shade.inputs[1]);l.new(ao.outputs['AO'],shade.inputs[2]);l.new(shade.outputs[0],e.inputs['Color'])
        mix=n.new('ShaderNodeMixShader');l.new(w.outputs[0],mix.inputs[0]);l.new(s.outputs[0],mix.inputs[1]);l.new(e.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
    o.data.materials.clear();o.data.materials.append(materials[key]);records.append(o.name)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'landship.blend'))
(M/'geometry.json').write_text(json.dumps({'meshes':sum(o.type=='MESH' for o in sc.objects),'shoes':128,'track_length':L,'projected_meshes':records,'source':'painting.png','camera_scale':5.7},indent=2))
print('LANDSHIP BUILD COMPLETE',len(records),'projected real meshes')
