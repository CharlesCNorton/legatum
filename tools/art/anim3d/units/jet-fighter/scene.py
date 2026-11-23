"""Original closed-volume jet-fighter, fitted in rest-camera coordinates.
Longitudinal loft, swept solid airfoils, a recessed nose intake and bubble canopy.
All colour projection is frozen UV on geometry, never a facing image card.
"""
import bpy,bmesh,math,json,os,sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']); M=R/'masters/jet-fighter'; A=R/'assets/jet-fighter'
reg=json.loads((M/'registration.json').read_text()); S=6.4
UP=Vector((0,.28,math.sqrt(1-.28**2))); FRONT=Vector((0,-UP.z,UP.y)); RIGHT=Vector((1,0,0))
def p(x,y,d=0):
    u=(x-reg['box'][0])*reg['scale']+reg['offset'][0]
    v=(y-reg['box'][1])*reg['scale']+reg['offset'][1]
    return RIGHT*((u/1024-.5)*S)+UP*((.5-v/1024)*S)+FRONT*d
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.render.film_transparent=True
sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
sc.world.color=(.15,.15,.15);sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
cam=bpy.data.objects.new('CAM-painting',bpy.data.cameras.new('CAM-painting'));bpy.context.collection.objects.link(cam);cam.location=FRONT*15;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=S;sc.camera=cam
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
for name,loc,power,color,size in [('key',(-3,-5,7),850,(1,.89,.73),4),('fill',(4,-4,3),230,(.85,.91,1),5),('rim',(0,5,5),420,(.78,.87,1),3)]:
    o=bpy.data.objects.new('LGT-'+name,bpy.data.lights.new(name,'AREA'));bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size

def material(name,color,metal=0,rough=.65):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=140;noise.inputs['Detail'].default_value=3
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.007;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
    return m
olive=material('MAT-worn silver aluminium',(.55,.61,.65),1,.49);silver=material('MAT-exposed aluminium',(.62,.65,.65),1,.42);black=material('MAT-propeller charcoal',(.022,.026,.028),0,.5);yellow=material('MAT-safety yellow tips',(.8,.49,.03));glass=material('MAT-painted dark glazing',(.09,.13,.14),0,.25)
stone=material('MAT-cream stone E9CFA0',(.815,.624,.352),0,.86);clay=material('MAT-clay',(.46,.46,.46));smoke=material('MAT-soot',(.055,.046,.035),0,1)
objects=[]
def mesh(name,verts,faces,mat,parent=True,smooth=True):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('GEO-'+name,me);bpy.context.collection.objects.link(ob);me.materials.append(mat)
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    for f in me.polygons:f.use_smooth=smooth
    if parent:objects.append(ob)
    return ob

def loft(name,rings,mat):
    # rings: source x,y, camera-depth, vertical radius in pixels, depth radius in metres
    vs=[];N=40
    for x,y,d,r,dep in rings:
        for j in range(N):
            t=2*math.pi*j/N;vs.append(p(x,y+r*math.sin(t),d)+FRONT*(dep*math.cos(t)))
    fs=[tuple(range(N-1,-1,-1))]
    for i in range(len(rings)-1):
        for j in range(N):fs.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
    fs.append(tuple((len(rings)-1)*N+j for j in range(N)))
    o=mesh(name,vs,fs,mat);sub=o.modifiers.new('Smooth longitudinal loft','SUBSURF');sub.levels=1;return o
def airfoil(name,sections,mat):
    # Each span station defines a true closed airfoil: LE/TE screen coords + depth.
    vs=[];N=32
    for lead,trail,depth,thick in sections:
        a=p(*lead,depth);b=p(*trail,depth)
        for j in range(N):
            t=2*math.pi*j/N;u=(1-math.cos(t))/2
            vs.append(a.lerp(b,u)+FRONT*(math.sin(t)*thick*(.7+.3*(1-u))))
    fs=[]
    for k in range(len(sections)-1):
        for j in range(N):fs.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
    fs.extend([tuple(range(N-1,-1,-1)),tuple((len(sections)-1)*N+j for j in range(N))])
    o=mesh(name,vs,fs,mat);b=o.modifiers.new('Rounded edges','BEVEL');b.width=.009;b.segments=2;return o
def ellipsoid(name,center,scale,mat,parent=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=center);o=bpy.context.object;o.name='GEO-'+name
    # local x is image-right; local y is front; local z is image-up
    from mathutils import Matrix
    o.rotation_euler=__import__('mathutils').Matrix((RIGHT,FRONT,UP)).transposed().to_euler();o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
    for f in o.data.polygons:f.use_smooth=True
    if parent:objects.append(o)
    return o

def tube(name,points,r,mat,parent=True):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=2;sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for dst,pt in zip(sp.points,points):dst.co=(*pt,1)
    o=bpy.data.objects.new('GEO-'+name,cu);bpy.context.collection.objects.link(o);cu.materials.append(mat)
    if parent:objects.append(o)
    return o
def solid_profile(name,coords,depth,thickness,mat,parent=True):
    vs=[p(x,y,depth+d) for d in (-thickness/2,thickness/2) for x,y in coords];n=len(coords)
    fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    o=mesh(name,vs,fs,mat,parent,False);b=o.modifiers.new('Finished bevel','BEVEL');b.width=.009;b.segments=3;return o
# Full-depth aluminium airframe registered to this painting's source pixels.
body=loft('fuselage',[(202,482,-.35,24,.16),(210,484,-.34,41,.21),(235,487,-.31,47,.25),(315,483,-.23,49,.29),(435,448,-.12,86,.35),(580,426,0,90,.39),(730,398,.16,105,.42),(880,361,.29,98,.44),(1020,316,.42,96,.46),(1129,280,.53,84,.43),(1157,260,.56,71,.40)],olive)
near=airfoil('near wing',[((792,388),(867,425),.62,.075),((623,433),(795,479),1.0,.07),((479,488),(655,557),1.42,.06),((320,616),(449,643),1.9,.045),((146,742),(232,733),2.28,.018),((130,757),(143,755),2.30,.008)],olive)
far=airfoil('far wing',[((631,330),(806,279),-.3,.065),((638,278),(770,248),-1.35,.045),((643,233),(730,221),-2.28,.025),((647,233),(710,227),-2.32,.012)],olive)
solid_profile('vertical fin',[(231,440),(152,334),(50,170),(78,160),(107,158),(346,312),(432,359),(411,397)],-.42,.10,olive)
airfoil('near tailplane',[((278,315),(309,333),-.08,.04),((127,370),(182,374),.40,.028),((8,418),(38,414),.80,.01)],olive)
airfoil('far tailplane',[((348,309),(385,331),-.62,.03),((446,284),(453,286),-1.80,.009)],olive)
# Bubble canopy is a smooth watertight loft with a raised aluminium frame.
loft('canopy',[(773,278,.41,2,.05),(797,261,.43,21,.16),(847,237,.44,32,.23),(902,218,.45,36,.24),(944,211,.44,29,.21),(982,224,.44,22,.19),(1026,234,.42,10,.12),(1043,239,.41,2,.04)],glass)
for pts in [[(776,276),(817,242),(864,210),(917,189),(954,193),(1001,213),(1035,234)],[(954,193),(945,224),(939,252)],[(777,278),(849,277),(925,258),(989,244),(1039,234)]]:
    tube('canopy rim',[p(x,y,.68) for x,y in pts],.0035,silver)
# Registered circular-section intake shell. The front ellipse is tilted in the
# painting; the rear outer ring flares into the fuselage. Dense axial stations
# preserve the frozen pigment instead of interpolating visibility across a cup.
center=p(1213,263,.80)
axis=(RIGHT*.877+FRONT*.45+UP*.17).normalized()
v=(UP-axis*UP.dot(axis)).normalized();w=axis.cross(v).normalized()
verts=[];N=96
rings=[(-.23,.378),(-.19,.363),(-.07,.310),(0,.285),
       (.003,.257),(-.07,.253),(-.20,.245),(-.33,.240)]
for offset,radius in rings:
    for j in range(N):
        t=math.tau*j/N
        verts.append(center+axis*offset+(w*math.cos(t)+v*math.sin(t))*radius)
faces=[(k*N+j,k*N+(j+1)%N,((k+1)%len(rings))*N+(j+1)%N,((k+1)%len(rings))*N+j)
       for k in range(len(rings)) for j in range(N)]
intake=mesh('nose intake rim',verts,faces,silver)
# Rounded termination deep inside the tube; the complete shell stays coaxial
# under bank and nose-view inspection, rather than only fitting its silhouette.
well=ellipsoid('intake well',center-axis*.35,(.10,.07,.23),black)
# Actual narrow panel seams / rivet relief along key fuselage stations.
for x,y,r,dep in [(369,474,57,.31),(587,421,73,.39),(923,318,85,.44),(1053,283,84,.46)]:
    pts=[p(x,y+r*math.sin(t),dep*math.cos(t)+(.1 if x<600 else .32)) for t in [j*math.pi/24 for j in range(-9,11)]]
    tube('panel seam',pts,.0025,silver)
# Curved cream pedestal, with genuine thickness and one round low-step disc.
basecenter=p(568,995,-.45)
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1.22,depth=.21,location=basecenter)
base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone)
b=base.modifiers.new('Rounded stone lip','BEVEL');b.width=.026;b.segments=3
supportcoords=[(416,951),(434,882),(464,801),(506,724),(553,654),(578,607),(587,568),(568,541),(640,529),(718,507),(747,508),(715,540),(672,578),(633,638),(600,700),(579,751),(571,789),(578,829),(595,867),(621,902),(666,955),(651,969),(607,982),(522,967)]
support=solid_profile('curved stone support',supportcoords,-.31,.25,stone,False)
# Pivot at the foot permits the support to collapse without disappearing.
pivot=p(555,951,-.31)
for vert in support.data.vertices:vert.co-=pivot
support.location=pivot
root=bpy.data.objects.new('RIG-airframe',None);bpy.context.collection.objects.link(root);root.location=p(675,396,.10)
bpy.context.view_layer.update()
for ob in objects:
    mat=ob.matrix_world.copy();ob.parent=root;ob.matrix_world=mat
bpy.context.view_layer.update()
# Restrained muzzle streaks: solid meshes, keyed visibility, never zero scale.
flashmat=material('MAT-warm cannon flash',(.95,.61,.20),0,.5)
bs=flashmat.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(1,.45,.08,1);bs.inputs['Emission Strength'].default_value=.6
for i in range(2):
    ob=tube('flash-'+str(i),[p(1040+i*38,376-i*10,.78),p(1170+i*38,349-i*10,.90)],.022,flashmat,False)
    ob.parent=root;ob.matrix_parent_inverse=root.matrix_world.inverted();ob.hide_render=True
# Reuse this aircraft's panel pattern on the opposite wing. This is a conventional
# span/chord unwrap, separate from the exact rest-camera projection. It prevents
# the hidden surface becoming a blank rectangle as the aircraft banks.
winguv=far.data.uv_layers.new(name='WingPanels')
wingstations=[((792,394),(846,430)),((500,493),(649,548)),
              ((180,720),(245,722)),((148,744),(172,742))]
for loop in far.data.loops:
    station,j=divmod(loop.vertex_index,32);u=(1-math.cos(math.tau*j/32))/2
    a,b=wingstations[station];x=a[0]*(1-u)+b[0]*u;y=a[1]*(1-u)+b[1]*u
    q=((x-reg['box'][0])*reg['scale']+reg['offset'][0])/1024
    r=((y-reg['box'][1])*reg['scale']+reg['offset'][1])/1024
    winguv.data[loop.index].uv=(q,1-r)
# Visibility weights need interior samples on this partly occluded wing, not
# just its silhouette vertices: otherwise hidden fill bleeds across the rest view.
sub=far.modifiers.new('Projection visibility samples','SUBSURF');sub.subdivision_type='SIMPLE';sub.levels=2
# Finish modifiers BEFORE projection so UVs register the actual rendered surface.
for ob in list(bpy.data.objects):
    if ob.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
    if ob.type=='MESH':
        bpy.context.view_layer.objects.active=ob
        for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
        # Mirrored span order can leave a consistently inward shell even after
        # recalc_face_normals. Fix signed volume before the facing-mask bake.
        bm=bmesh.new();bm.from_mesh(ob.data)
        if all(e.is_manifold for e in bm.edges) and bm.calc_volume(signed=True)<0:
            bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(ob.data);ob.data.update()
        bm.free()
sc['unit']='jet-fighter';sc['projection_method']='frozen rest UV on finished closed volumes';sc['base_hex']='#E9CFA0'
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
texture=bpy.data.images.load(str(A/'projection.png'));fill=bpy.data.images.load(str(A/'painted-fill.png'))
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
for ob in list(bpy.data.objects):
    if ob.type!='MESH' or 'flash-' in ob.name:continue
    uv=ob.data.uv_layers.new(name='RestPainting');weights=ob.data.color_attributes.new(name='Facing',type='FLOAT_COLOR',domain='CORNER');normal=ob.matrix_world.to_3x3().inverted().transposed()
    # Sample finished vertices, not nonplanar quad centroids (which can lie
    # below the tessellated surface and falsely reject visible wing pigment).
    for loop in ob.data.loops:
        vert=ob.data.vertices[loop.vertex_index];point=ob.matrix_world@vert.co
        q=world_to_camera_view(sc,cam,point);uv.data[loop.index].uv=(q.x,q.y)
        hit,loc,_,_,hitob,_=sc.ray_cast(deps,point+FRONT*20,-FRONT,distance=20.02)
        visible=hit and (loc-point).length<.025
        w=max(0,min(1,((normal@vert.normal).normalized().dot(FRONT)+.12)/.12)) if visible else 0
        weights.data[loop.index].color=(w,w,w,1)
    old=ob.data.materials[0];mat=old.copy();mat.name=ob.name+' painted';ob.data.materials[0]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF')
    uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map='RestPainting';im=n.new('ShaderNodeTexImage');im.image=texture;im.extension='CLIP';l.new(uvnode.outputs[0],im.inputs[0])
    tx=n.new('ShaderNodeTexImage');tx.image=fill;tx.projection='BOX';tx.projection_blend=.3;coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],tx.inputs[0])
    facing=n.new('ShaderNodeVertexColor');facing.layer_name='Facing';mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(facing.outputs['Color'],mult.inputs[0]);l.new(im.outputs['Alpha'],mult.inputs[1])
    mix=n.new('ShaderNodeMixRGB');l.new(mult.outputs[0],mix.inputs[0]);mix.inputs[1].default_value=old.diffuse_color
    if old==olive:
        # Match hidden aluminium to the painting's cool silver mids; generated
        # brushwork remains visible, with a broad softbox response rather than
        # the white rectangle previously exposed on the far wing during death.
        tint=n.new('ShaderNodeMixRGB');tint.inputs[0].default_value=.70
        l.new(tx.outputs['Color'],tint.inputs[1]);tint.inputs[2].default_value=(.32,.39,.43,1)
        l.new(tint.outputs[0],mix.inputs[1]);bs.inputs['Roughness'].default_value=.66
        if ob==far:
            paneluv=n.new('ShaderNodeUVMap');paneluv.uv_map='WingPanels'
            panel=n.new('ShaderNodeTexImage');panel.image=texture;l.new(paneluv.outputs[0],panel.inputs[0])
            panelmix=n.new('ShaderNodeMixRGB');panelmix.inputs[0].default_value=.84
            l.new(tint.outputs[0],panelmix.inputs[1]);l.new(panel.outputs['Color'],panelmix.inputs[2])
            l.new(panelmix.outputs[0],mix.inputs[1])
    l.new(im.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
    # Camera-only painted pigment avoids double lighting, while non-camera rays
    # still interact with the physical material and cast real contact shadows.
    pigment=n.new('ShaderNodeEmission');l.new(mix.outputs[0],pigment.inputs['Color'])
    camera=n.new('ShaderNodeLightPath');strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.99;l.new(mult.outputs[0],strength.inputs[0])
    if old==olive:
        hidden=n.new('ShaderNodeMapRange');hidden.inputs['From Min'].default_value=0;hidden.inputs['From Max'].default_value=1
        hidden.inputs['To Min'].default_value=.58;hidden.inputs['To Max'].default_value=.99
        l.new(mult.outputs[0],hidden.inputs['Value']);l.new(hidden.outputs[0],strength.inputs[0]);strength.inputs[1].default_value=1
    gate=n.new('ShaderNodeMath');gate.operation='MULTIPLY';l.new(strength.outputs[0],gate.inputs[0]);l.new(camera.outputs['Is Camera Ray'],gate.inputs[1])
    shader=n.new('ShaderNodeMixShader');l.new(gate.outputs[0],shader.inputs[0]);l.new(bs.outputs[0],shader.inputs[1]);l.new(pigment.outputs[0],shader.inputs[2]);l.new(shader.outputs[0],n.get('Material Output').inputs['Surface'])
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'jet-fighter.blend'))
(M/'geometry.json').write_text(json.dumps({'blender':bpy.app.version_string,'mesh_count':len([o for o in bpy.data.objects if o.type=='MESH']),'vertices':sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'),'rig':'rigid airframe and collapsing support','jet_engines':1,'volumetric_smoke':False},indent=2))
print('JET FIGHTER BUILD COMPLETE')
