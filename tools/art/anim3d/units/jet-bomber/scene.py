"""Original closed-volume jet-bomber, fitted in rest-camera coordinates.
Longitudinal loft, swept solid airfoils, eight tubular jets and one tall fin.
All colour projection is frozen UV on geometry, never a facing image card.
"""
import bpy,bmesh,math,json,os,sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']); M=R/'masters/jet-bomber'; A=R/'assets/jet-bomber'
reg=json.loads((M/'registration.json').read_text()); S=6.4
UP=Vector((0,.25,math.sqrt(1-.25**2))); FRONT=Vector((0,-UP.z,UP.y)); RIGHT=Vector((1,0,0))
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
for name,loc,power,color,size in [('key',(-3,-5,7),850,(1,.89,.73),4),('fill',(4,-4,3),230,(.85,.91,1),5),('rim',(0,5,5),600,(.78,.87,1),3)]:
    o=bpy.data.objects.new('LGT-'+name,bpy.data.lights.new(name,'AREA'));bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size

def material(name,color,metal=0,rough=.65):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=140;noise.inputs['Detail'].default_value=3
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.007;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
    return m
olive=material('MAT-worn olive lacquer',(.18,.19,.095));silver=material('MAT-exposed aluminium',(.62,.65,.65),1,.42);black=material('MAT-propeller charcoal',(.022,.026,.028),0,.5);yellow=material('MAT-safety yellow tips',(.8,.49,.03));glass=material('MAT-painted dark glazing',(.09,.13,.14),0,.25)
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
    o=mesh(name,vs,fs,mat);b=o.modifiers.new('Rounded edges','BEVEL');b.width=.009;b.segments=2
    # Localize rest-ray occlusion at the fuselage join. Sparse span quads let
    # hidden root vertices fade the source pigment across the whole wing.
    sub=o.modifiers.new('Projection sampling lattice','SUBSURF')
    sub.subdivision_type='SIMPLE';sub.levels=2;sub.render_levels=2
    return o
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
# Aircraft registered to source landmarks, each surface retains genuine depth.
body=loft('fuselage',[(23,601,.25,2,.02),(38,598,.25,17,.10),(70,591,.23,38,.23),(125,583,.21,55,.31),(215,572,.17,61,.36),(360,543,.1,64,.36),(520,513,0,60,.32),(680,480,-.1,51,.27),(820,454,-.2,46,.21),(950,419,-.3,33,.16),(1031,404,-.38,19,.11)],olive)
near=airfoil('near wing',[((390,512),(518,493),.42,.055),((640,597),(722,554),1.0,.055),((882,678),(950,644),1.65,.045),((1190,781),(1235,778),2.3,.014),((1235,785),(1242,781),2.32,.008)],olive)
far=airfoil('far wing',[((513,455),(321,491),-.35,.075),((285,302),(209,354),-1.05,.055),((137,214),(116,261),-1.65,.04),((49,164),(69,206),-2.0,.02),((23,161),(25,165),-2.15,.008)],olive)
airfoil('near tailplane',[((902,433),(973,412),-.15,.035),((1124,464),(1129,453),.35,.015),((1154,467),(1156,469),.38,.007)],olive)
airfoil('far tailplane',[((880,377),(836,398),-.5,.032),((785,330),(805,357),-.95,.014)],olive)
# Vertical fin, with closed beveled perimeter. Camera-depth varies with root.
coords=[(853,397),(884,359),(1018,182),(1031,178),(1054,174),(1008,365),(1008,385)]
def solid_profile(name,coords,depth,thickness,mat,parent=True):
    vs=[p(x,y,depth+d) for d in (-thickness/2,thickness/2) for x,y in coords];n=len(coords)
    fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    o=mesh(name,vs,fs,mat,parent,False);b=o.modifiers.new('Finished bevel','BEVEL');b.width=.009;b.segments=3;return o
solid_profile('vertical fin',coords,-.41,.075,olive)
# Four pairs of jets: real hollow cowls, intake tunnel and compressor blades.
for label,cx,cy,depth,rad in [('far outer',20,324,-1.40,16),('far inner',119,417,-.83,20),('near inner',548,665,1.12,22),('near outer',761,741,1.79,22)]:
    solid_profile(label+' pylon',[(cx+28,cy-18),(cx+54,cy-50),(cx+105,cy-76),(cx+122,cy-59),(cx+89,cy-24)],depth-.08,.055,olive)
    for pair in range(2):
        x=cx+4+pair*28;y=cy+pair*10;dep=depth+pair*.09
        loft(label+f' jet {pair}',[(x,y,dep,rad,.10),(x+15,y-4,dep-.02,rad+2,.12),(x+42,y-8,dep-.08,rad,.11),(x+78,y-15,dep-.14,rad*.85,.085),(x+(110 if label.startswith('near') else 100),y-25,dep-.22,rad*.45,.045)],olive)
        center=p(x,y,dep+.035);axis=(-RIGHT*.55+FRONT*.83).normalized();v=UP;u=axis.cross(v).normalized();radius=rad*reg['scale']*S/1024
        vs=[];N=40
        for off,r in [(-.04,radius),(.018,radius),(.024,radius*.73),(-.065,radius*.73)]:
            for j in range(N):vs.append(center+axis*off+(u*math.cos(j*math.tau/N)+v*math.sin(j*math.tau/N))*r)
        fs=[(k*N+j,k*N+(j+1)%N,((k+1)%4)*N+(j+1)%N,((k+1)%4)*N+j) for k in range(4) for j in range(N)]
        o=mesh(label+f' intake rim {pair}',vs,fs,silver);b=o.modifiers.new('Rolled intake lip','BEVEL');b.width=.003;b.segments=2
        ellipsoid(label+f' intake cavity {pair}',center-axis*.05,(radius*.66,.035,radius*.66),black)
        for j in range(9):
            a=j*math.tau/9;pt=center-axis*.035
            tube(label+' compressor blade',[pt+(u*math.cos(a)+v*math.sin(a))*.018,pt+(u*math.cos(a+.25)+v*math.sin(a+.25))*radius*.61],.003,silver)
# Tiny cockpit frames are actual relief; the original painting supplies glazing colour.
for pts in [[(61,566),(83,540),(126,529),(161,529),(173,564)],[(82,540),(106,550),(128,543),(150,541),(161,564)],[(106,550),(99,571)],[(128,543),(126,568)],[(150,541),(151,565)]]:
    tube('cockpit aluminium frame',[p(x,y,.52) for x,y in pts],.0035,silver)
# One plain round cream disc; the painting's carved support is a separate solid.
basecenter=p(650,1031,-.55)
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.93,depth=.13,location=basecenter)
base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone)
b=base.modifiers.new('Rounded stone lip','BEVEL');b.width=.025;b.segments=3
supportcoords=[(552,1004),(580,970),(603,925),(622,877),(631,834),(629,800),(615,762),(594,730),(568,699),(580,702),(613,735),(646,776),(675,824),(697,875),(718,937),(740,989)]
support=solid_profile('curved stationary stone support',supportcoords,-.48,.18,stone,False)
# The silhouette alone concealed a depth gap. Shear the solid bracket toward
# the near pod while leaving the registered camera coordinates unchanged.
bottom=min(v.co.dot(UP) for v in support.data.vertices)
height=max(v.co.dot(UP) for v in support.data.vertices)-bottom
for v in support.data.vertices:v.co+=FRONT*(1.60*(v.co.dot(UP)-bottom)/height)
root=bpy.data.objects.new('RIG-airframe',None);bpy.context.collection.objects.link(root);root.location=p(580,495,.1)
bpy.context.view_layer.update()
for ob in objects:
    mat=ob.matrix_world.copy();ob.parent=root;ob.matrix_world=mat
bpy.context.view_layer.update()
for i in range(3):
    ob=ellipsoid('bomb-'+str(i),p(470+i*55,565,.25),(.055,.055,.135),olive,False);ob.hide_render=True
    # Real stabilizing fins, joined to the released mesh so all keys agree.
    parts=[ob];center=ob.location.copy()
    for axis in (RIGHT,FRONT):
        verts=[center+UP*z+axis*x+axis.cross(UP)*d
               for d in (-.006,.006)
               for x,z in ((-.085,.115),(.085,.115),(.045,.055),(-.045,.055))]
        fin=mesh('bomb fin',verts,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],olive,False)
        parts.append(fin)
    bpy.ops.object.select_all(action='DESELECT')
    for part in parts:part.select_set(True)
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.join()
# Finish modifiers BEFORE projection so UVs register the actual rendered surface.
for ob in list(bpy.data.objects):
    if ob.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
    if ob.type=='MESH':
        bpy.context.view_layer.objects.active=ob
        for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
from mathutils.bvhtree import BVHTree
top=max(v.co.dot(UP) for v in support.data.vertices)
tips=[v.co.copy() for v in support.data.vertices if v.co.dot(UP)>top-.04]
nearest=[]
for i in range(2):
    ob=bpy.data.objects[f'GEO-near inner jet {i}']
    tree=BVHTree.FromPolygons([ob.matrix_world @ v.co for v in ob.data.vertices],
                              [list(face.vertices) for face in ob.data.polygons])
    for tip in tips:
        point,normal,_,distance=tree.find_nearest(tip)
        nearest.append((distance,point-tip-normal*.008))
correction=min(nearest,key=lambda pair:pair[0])[1]
for v in support.data.vertices:
    weight=max(0,min(1,(v.co.dot(UP)-bottom)/height))**3
    v.co+=correction*weight
sc['unit']='jet-bomber';sc['projection_method']='frozen rest UV on finished closed volumes';sc['base_hex']='#E9CFA0'
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
texture=bpy.data.images.load(str(A/'projection.png'));fill=bpy.data.images.load(str(A/'painted-fill.png'))
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
for ob in list(bpy.data.objects):
    if ob.type!='MESH' or 'bomb-' in ob.name:continue
    uv=ob.data.uv_layers.new(name='RestPainting');weights=ob.data.color_attributes.new(name='Facing',type='FLOAT_COLOR',domain='CORNER');normal=ob.matrix_world.to_3x3().inverted().transposed()
    # Sample finished vertices, not nonplanar quad centroids (which can lie
    # below the tessellated surface and falsely reject visible wing pigment).
    for loop in ob.data.loops:
        vert=ob.data.vertices[loop.vertex_index];point=ob.matrix_world @ vert.co
        q=world_to_camera_view(sc,cam,point);uv.data[loop.index].uv=(q.x,q.y)
        hit,loc,_,_,hitob,_=sc.ray_cast(deps,point+FRONT*20,-FRONT,distance=20.02)
        visible=hit and (loc-point).length<.025
        w=max(0,min(1,((normal @ vert.normal).normalized().dot(FRONT)+.06)/.15)) if visible else 0
        if ob==base or any(s in ob.name for s in ('wing','tailplane')):
            # Smooth normals at a thin airfoil or stone rim point sideways even
            # on visible surfaces. Rest-ray visibility is the confidence test;
            # source alpha still gates pigment, never the geometry's opacity.
            if visible:w=1
        weights.data[loop.index].color=(w,w,w,1)
    old=ob.data.materials[0];mat=old.copy();mat.name=ob.name+' painted';ob.data.materials[0]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF')
    uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map='RestPainting';im=n.new('ShaderNodeTexImage');im.image=texture;im.extension='CLIP';l.new(uvnode.outputs[0],im.inputs[0])
    tx=n.new('ShaderNodeTexImage');tx.image=fill;tx.projection='BOX';tx.projection_blend=.3;coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],tx.inputs[0])
    facing=n.new('ShaderNodeVertexColor');facing.layer_name='Facing';mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(facing.outputs['Color'],mult.inputs[0]);l.new(im.outputs['Alpha'],mult.inputs[1])
    mix=n.new('ShaderNodeMixRGB');l.new(mult.outputs[0],mix.inputs[0]);mix.inputs[1].default_value=old.diffuse_color
    if old==olive:l.new(tx.outputs['Color'],mix.inputs[1])
    l.new(im.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
    # Camera-only painted pigment avoids double lighting, while non-camera rays
    # still interact with the physical material and cast real contact shadows.
    pigment=n.new('ShaderNodeEmission');l.new(mix.outputs[0],pigment.inputs['Color'])
    camera=n.new('ShaderNodeLightPath');strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.97;l.new(mult.outputs[0],strength.inputs[0])
    gate=n.new('ShaderNodeMath');gate.operation='MULTIPLY';l.new(strength.outputs[0],gate.inputs[0]);l.new(camera.outputs['Is Camera Ray'],gate.inputs[1])
    shader=n.new('ShaderNodeMixShader');l.new(gate.outputs[0],shader.inputs[0]);l.new(bs.outputs[0],shader.inputs[1]);l.new(pigment.outputs[0],shader.inputs[2]);l.new(shader.outputs[0],n.get('Material Output').inputs['Surface'])
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'jet-bomber.blend'))
(M/'geometry.json').write_text(json.dumps({'blender':bpy.app.version_string,'mesh_count':len([o for o in bpy.data.objects if o.type=='MESH']),'vertices':sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'),'rig':'rigid airframe and three released bombs','jet_engines':8,'volumetric_smoke':False},indent=2))
print('JET BOMBER BUILD COMPLETE')
