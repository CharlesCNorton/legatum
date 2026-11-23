"""Original closed-volume bomber, fitted in rest-camera coordinates.
Longitudinal loft, solid airfoil lofts, twin fins, radial engines and framed glazing.
All colour projection is frozen UV on geometry, never a facing image card.
"""
import bpy,bmesh,math,json,os,sys
import numpy as np
from mathutils import Matrix
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']); M=R/'masters/bomber'; A=R/'assets/bomber'
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
for name,loc,power,color,size in [('key',(-3,-5,7),470,(1,.97,.91),4),('fill',(4,-4,3),125,(.92,.95,1),5),('rim',(0,5,5),300,(.85,.91,1),3)]:
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
body=loft('fuselage',[(286,440,-.28,12,.08),(335,450,-.20,46,.21),(450,460,-.1,65,.33),(620,476,.04,92,.39),(820,500,.19,119,.45),(990,510,.33,97,.46),(1080,522,.42,78,.36),(1130,525,.45,53,.23),(1164,523,.46,8,.035)],olive)

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
    o=mesh(name,vs,fs,mat);b=o.modifiers.new('Rounded edges','BEVEL');b.width=.014;b.segments=3;return o
near=airfoil('near wing',[((785,534),(665,477),.35,.065),((634,575),(521,522),.70,.065),((420,681),(316,632),1.07,.045),((125,789),(64,764),1.55,.025),((80,793),(60,781),1.56,.012)],olive)
far=airfoil('far wing',[((948,394),(811,360),-.2,.06),((1050,310),(941,294),-.9,.055),((1187,214),(1121,201),-1.7,.03),((1232,198),(1201,174),-1.95,.018),((1240,188),(1236,183),-1.98,.01)],olive)
# Tailplane on both sides, with twin tall rudders.
airfoil('tailplane near',[((379,438),(294,424),-.1,.035),((111,532),(74,505),.58,.025)],olive)
airfoil('tailplane far',[((370,417),(301,408),-.3,.035),((530,346),(498,342),-.9,.025)],olive)
for name,coords,depth in [('near',[(68,577),(29,557),(9,401),(17,372),(47,360),(73,372),(126,538),(122,560),(101,573)],.65),('far',[(533,386),(464,365),(432,237),(434,217),(459,208),(480,217),(554,350),(562,369)],-.85)]:
    vs=[p(x,y,depth+z) for z in (-.035,.035) for x,y in coords];n=len(coords);fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    o=mesh(name+' fin',vs,fs,olive);b=o.modifiers.new('Rounded fin lip','BEVEL');b.width=.024;b.segments=3

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
# Convex glazed nose and cockpit, complete 3D cages, no decal plane.
for name,cx,cy,dep,rx,rz in [('nose glazing',1096,515,.77,88,77),('cockpit',903,416,.43,87,45),('dorsal turret',760,356,.10,49,36)]:
    q=ellipsoid(name,p(cx,cy,dep),(rx*.0047,.20,rz*.0047),glass)
    for lon in (-.65,0,.65):
        pts=[]
        for k in range(25):
            a=-math.pi/2+math.pi*k/24;pts.append(p(cx+rx*lon,cy+rz*math.sin(a)*math.sqrt(1-lon*lon),dep)+FRONT*(.204*math.cos(a)*math.sqrt(1-lon*lon)))
        tube(name+' longitudinal frame',pts,.004,silver)
    for lat in (-.52,.05,.58):
        pts=[]
        for k in range(29):
            a=-math.pi/2+math.pi*k/28;pts.append(p(cx+rx*math.sin(a)*math.sqrt(1-lat*lat),cy+rz*lat,dep)+FRONT*(.205*math.cos(a)*math.sqrt(1-lat*lat)))
        tube(name+' transverse frame',pts,.004,silver)
props=[]
for label,cx,cy,depth,rad in [('near',739,623,1.12,73),('far',1142,414,-.30,57)]:
    loft(label+' nacelle',[(cx-147,cy-65,depth-.2,22,.12),(cx-100,cy-35,depth-.07,rad*.95,.27),(cx-35,cy-5,depth,rad,.31),(cx+6,cy+3,depth+.01,rad*.92,.29)],olive)
    # Annular front cowl, recessed radial engine and 12 cylinder heads.
    center=p(cx,cy,depth+.34)
    # Fit a circular propeller plane to two painted blade vectors. SVD lifts
    # the projected ellipse into an orthonormal 3D frame; no stretched blades.
    pixel=reg['scale']*S/1024
    first=np.array((45,188) if label=='near' else (16,167),dtype=float)*pixel
    second=np.array((-135,-95) if label=='near' else (-82,-80),dtype=float)*pixel
    projected=np.column_stack((first,(second+.5*first)/(math.sqrt(3)/2)))
    radius=float(np.linalg.svd(projected,compute_uv=False)[0]);projected/=radius
    values,vectors=np.linalg.eigh(np.eye(2)-projected.T @ projected)
    depths=vectors[:,-1]*math.sqrt(max(0,float(values[-1])))
    basis=[RIGHT*float(projected[0,i])+UP*float(projected[1,i])+FRONT*float(depths[i]) for i in range(2)]
    axis=basis[0].cross(basis[1]).normalized()
    if axis.dot(RIGHT)<0:
        depths=-depths
        basis=[RIGHT*float(projected[0,i])+UP*float(projected[1,i])+FRONT*float(depths[i]) for i in range(2)]
        axis=basis[0].cross(basis[1]).normalized()
    prop_rotation=Matrix((basis[0],basis[1],axis)).transposed()
    v=basis[0];u=basis[1]
    vs=[];N=64
    for off,r in [(-.12,rad*.0047),(.10,rad*.0047),(.10,rad*.00365),(-.12,rad*.00365)]:
        for j in range(N):vs.append(center+axis*off+(u*math.cos(j*2*math.pi/N)+v*math.sin(j*2*math.pi/N))*r)
    fs=[(k*N+j,k*N+(j+1)%N,((k+1)%4)*N+(j+1)%N,((k+1)%4)*N+j) for k in range(4) for j in range(N)]
    cowl=mesh(label+' silver cowl',vs,fs,silver);b=cowl.modifiers.new('Rolled cowl edge','BEVEL');b.width=.008;b.segments=2
    ellipsoid(label+' engine cavity',center-axis*.1,(rad*.0035,.10,rad*.0035),black)
    for j in range(12):
        a=j*math.tau/12;pt=center+(u*math.cos(a)+v*math.sin(a))*(rad*.0027)
        tube(label+' radial cylinder',[pt-axis*.08,pt+axis*.02],.034,silver)
    mount=bpy.data.objects.new('RIG-'+label+' shaft',None);bpy.context.collection.objects.link(mount);mount.location=p(785,640,depth+.50) if label=='near' else p(1155,422,depth+.50);mount.rotation_euler=prop_rotation.to_euler();objects.append(mount)
    pivot=bpy.data.objects.new('RIG-'+label+' propeller',None);bpy.context.collection.objects.link(pivot);pivot.parent=mount
    blade_scale=radius/.72
    props.append(pivot)
    bpy.context.view_layer.update()
    spinner=ellipsoid(label+' spinner',mount.location,(.105,.105,.18),silver)
    spinner.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
    for blade in range(3):
        angle=blade*math.tau/3
        # Curved tapered blade with actual thickness, not a plane.
        poly=[(.08,-.022),(.24,-.055),(.62,-.07),(.72,-.035),(.70,.005),(.28,.04)]
        vv=[]
        for z in (-.014,.014):
            for r,t in poly:vv.append((r*math.cos(angle)-t*math.sin(angle),r*math.sin(angle)+t*math.cos(angle),z))
        
        vv=[(x*blade_scale,y*blade_scale,z) for x,y,z in vv]
        n=len(poly);ff=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
        ob=mesh(label+' prop blade',vv,ff,black,False);ob.parent=pivot
        bevel=ob.modifiers.new('Blade bevel','BEVEL');bevel.width=.008;bevel.segments=2
        ob.data.materials.append(yellow)
        for f in ob.data.polygons:
            if sum(ob.data.vertices[k].co.xy.length for k in f.vertices)/len(f.vertices)>.59*blade_scale:f.material_index=1
# Nose barrels, upper panel seams are real small tubular relief.
for yy in (530,548):tube('nose barrel',[p(1155,yy,.82),p(1205,yy+5,.87)],.010,black)
# Stone pedestal: one disc and a curved, thick support as shown in painting.
basecenter=p(640,1005,-.55)
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1.04,depth=.15,location=basecenter);base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone);bev=base.modifiers.new('Rounded stone lip','BEVEL');bev.width=.025;bev.segments=5
supportcoords=[(521,966),(536,889),(564,804),(609,735),(660,679),(687,653),(667,731),(650,785),(659,845),(688,903),(748,966)]
vs=[p(x,y,d) for d in (-.38,-.15) for x,y in supportcoords];n=len(supportcoords);fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
support=mesh('curved stationary stone support',vs,fs,stone,False);b=support.modifiers.new('Carved stone soft edges','BEVEL');b.width=.03;b.segments=3
# Parent airframe rigid components after positioning. Keep pivots local.
root=bpy.data.objects.new('RIG-airframe',None);bpy.context.collection.objects.link(root);root.location=p(660,480,0)
bpy.context.view_layer.update()
for ob in objects:
    mat=ob.matrix_world.copy();ob.parent=root;ob.matrix_world=mat
bpy.context.view_layer.update()
# Bombs are individually animated, using real geometry and visibility keys.
for i in range(3):
    ob=ellipsoid('bomb-'+str(i),p(760+i*25,570,.5),(.055,.055,.15),black,False);ob.hide_render=True
# Save early geometry master before texturing.
sc['unit']='bomber';sc['projection_method']='frozen camera UV on closed lofted volumes';sc['base_hex']='#E9CFA0'
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
# Finish the actual rendered surfaces before freezing projection coordinates.
# Curves retain closed tubular relief; source-pigment mapping removes double cage lines.
for ob in list(bpy.data.objects):
    if ob.type not in ('MESH','CURVE'):continue
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    if ob.type=='CURVE':
        ob.data.use_fill_caps=True
        bpy.ops.object.convert(target='MESH')
    for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
    if any(part in ob.name for part in ('wing','tailplane',' fin','stone support')):
        bm=bmesh.new();bm.from_mesh(ob.data)
        bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=2,use_grid_fill=True)
        bm.to_mesh(ob.data);bm.free();ob.data.update()
    ob['surface_finished']=True
bpy.context.view_layer.update()
# Keep a finished, unprojected checkpoint for diagnosis and reproducible UV work.
bpy.ops.wm.save_as_mainfile(filepath=str(M/'surface.blend'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from project import apply_projection
apply_projection(sc,cam,A,FRONT)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'bomber.blend'))
(M/'geometry.json').write_text(json.dumps({'blender':bpy.app.version_string,'mesh_count':len([o for o in bpy.data.objects if o.type=='MESH']),'vertices':sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'),'rig':'airframe, two propeller pivots, three released bombs','volumetric_smoke':False},indent=2))
print('BOMBER BUILD COMPLETE')
