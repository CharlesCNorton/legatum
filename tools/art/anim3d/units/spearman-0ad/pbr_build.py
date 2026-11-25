"""Premium PBR look, authored in Blender; motion copied from approved round 6.

source tools/art/anim3d/env.sh
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman-0ad/pbr_build.py
Use -- --preview for 512 bake iteration; final defaults to 2048 masters.
"""
import bpy, bmesh, sys, os, math, json, hashlib, subprocess
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin,cos,pi
UNIT=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB
from pbr_export import extract,write_glb
import pbr_forms
import pbr_human
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
WORK=ROOT/'oad/pbr-r2';WORK.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'oad/pbr-r1/approved-r6.glb'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='84bf794f543fd4a1af2d1b9c2b48c89a6c52533a00d7803e553b49a22513f92c', 'Expected approved round-6 motion source'
g=GLB(SOURCE);d=g.doc;prim=d['meshes'][0]['primitives'][0]
old={k:g.accessor(v) for k,v in prim['attributes'].items()};ix=[v[0] for v in g.accessor(prim['indices'])]
bones={d['nodes'][n]['name']:i for i,n in enumerate(d['skins'][0]['joints'])}
SIZE=512 if '--preview' in sys.argv else 2048
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
parts=[];catalog={}
# All procedural colour uses bind-space position and pigment variation only.
PALETTES={'bronze':('#b88a46',.43,1),'edge':('#e2b96a',.23,1),'darkbronze':('#604528',.59,1),'linen':('#e5d8b8',.91,0),'leather':('#442c20',.56,0),'wool':('#921921',.94,0),'wooldark':('#4b1019',.96,0),'skin':('#bb865e',.62,0),'wood':('#705036',.55,0),'team':('#b2a596',.88,0)}
def linear(c):
    v=int(c,16)/255;return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4

def material(kind,part,bone=None,team=None):
    name='MAT-'+str(len(catalog))+'-'+kind+'-'+part
    m=bpy.data.materials.new(name);m.use_nodes=True;nodes=m.node_tree.nodes;links=m.node_tree.links
    bs=nodes.get('Principled BSDF');hexcol,rough,metal=PALETTES[kind];rgb=[linear(hexcol[i:i+2]) for i in (1,3,5)]
    bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    pos=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(pos.outputs['Position'],sep.inputs[0])
    ramp=nodes.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1.95;ramp.inputs['To Min'].default_value=.76;ramp.inputs['To Max'].default_value=1.05;links.new(sep.outputs['Y'],ramp.inputs['Value'])
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=55 if metal else 90;noise.inputs['Detail'].default_value=3;links.new(pos.outputs['Position'],noise.inputs['Vector'])
    vary=nodes.new('ShaderNodeMapRange');vary.inputs['To Min'].default_value=.58 if metal else .84;vary.inputs['To Max'].default_value=1.20 if metal else 1.05;links.new(noise.outputs['Fac'],vary.inputs['Value'])
    mult=nodes.new('ShaderNodeMath');mult.operation='MULTIPLY';links.new(ramp.outputs[0],mult.inputs[0]);links.new(vary.outputs[0],mult.inputs[1])
    color=nodes.new('ShaderNodeMixRGB');color.blend_type='MULTIPLY';color.inputs[0].default_value=1;color.inputs[1].default_value=(*rgb,1);links.new(mult.outputs[0],color.inputs[2]);links.new(color.outputs[0],bs.inputs['Base Color'])
    rmap=nodes.new('ShaderNodeMapRange');rmap.inputs['To Min'].default_value=max(.15,rough-(.16 if metal else .09));rmap.inputs['To Max'].default_value=min(1,rough+(.16 if metal else .08));links.new(noise.outputs['Fac'],rmap.inputs['Value']);links.new(rmap.outputs[0],bs.inputs['Roughness'])
    fine=nodes.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=430 if kind in ('wool','linen','team') else 180;fine.inputs['Detail'].default_value=2;links.new(pos.outputs['Position'],fine.inputs['Vector'])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.25;bump.inputs['Distance'].default_value=.0012 if metal else .0007;links.new(fine.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],bs.inputs['Normal'])
    if kind in ('linen','wool','team'):
        weave=nodes.new('ShaderNodeTexWave');weave.bands_direction='X';weave.inputs['Scale'].default_value=350
        links.new(pos.outputs['Position'],weave.inputs['Vector'])
        thread=nodes.new('ShaderNodeMixRGB');thread.blend_type='MULTIPLY';thread.inputs[0].default_value=.65
        links.new(fine.outputs['Fac'],thread.inputs[1]);links.new(weave.outputs['Color'],thread.inputs[2]);links.new(thread.outputs[0],bump.inputs['Height'])
    catalog[m.name]={'part':part,'bone':bone,'team':team};m['kind']=kind
    return m

def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o

def mod(o,kind,**kwargs):
    active(o);m=o.modifiers.new(kind,kind)
    for k,v in kwargs.items():setattr(m,k,v)
    bpy.ops.object.modifier_apply(modifier=m.name)

def mesh(name,verts,faces,mat,bone=None,weights=None,smooth=True):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('GEO-'+name,me);bpy.context.collection.objects.link(o);me.materials.append(mat)
    if bone:
        vg=o.vertex_groups.new(name='j'+str(bones[bone]));vg.add(list(range(len(verts))),1,'REPLACE')
    elif weights:
        for j in range(len(bones)):
            vg=o.vertex_groups.new(name='j'+str(j))
            for vi,ws in enumerate(weights):
                if j in ws:vg.add([vi],ws[j],'REPLACE')
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    for p in me.polygons:p.use_smooth=smooth
    parts.append(o);return o

def tube(name,points,radii,mat,bone,sides=10):
    verts=[];faces=[]
    for i,p in enumerate(points):
        p=Vector(p);axis=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])).normalized()
        u=axis.cross(Vector((0,1,0)))
        if u.length<.1:u=axis.cross(Vector((1,0,0)))
        u.normalize();v=axis.cross(u).normalized()
        for j in range(sides):verts.append(p+radii[i]*(u*cos(j*2*pi/sides)+v*sin(j*2*pi/sides)))
    for i in range(len(points)-1):
        for j in range(sides):faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    faces.extend([tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))])
    return mesh(name,verts,faces,mat,bone)

def ring(name,c,u,v,r,minor,mat,bone,n=64,k=6):
    c,u,v=map(Vector,(c,u,v));normal=u.cross(v).normalized();verts=[];faces=[]
    for i in range(n):
        radial=u*cos(i*2*pi/n)+v*sin(i*2*pi/n)
        for j in range(k):verts.append(c+radial*(r+minor*cos(j*2*pi/k))+normal*minor*sin(j*2*pi/k))
    for i in range(n):
        for j in range(k):faces.append((i*k+j,((i+1)%n)*k+j,((i+1)%n)*k+(j+1)%k,i*k+(j+1)%k))
    return mesh(name,verts,faces,mat,bone)

# Retain body anatomy and native weights, including the three cloth bones.
for reg in d['meshes'][0]['extras']['vertex_regions']:
    if reg['part'] not in ('body','Aspis handgrip'):continue
    start,end=reg['start'],reg['start']+reg['count'];faces=[ix[i:i+3] for i in range(0,len(ix),3) if start<=ix[i]<end]
    verts=old['POSITION'][start:end];weights=[{int(j):w for j,w in zip(js,ws) if w>0} for js,ws in zip(old['JOINTS_0'][start:end],old['WEIGHTS_0'][start:end])]
    ob=mesh(reg['part'],verts,[[i-start for i in f] for f in faces],material('skin' if reg['part']=='Greek head' else 'leather','Greek head' if reg['part']=='Greek head' else reg['part'],reg['bone'],reg['team']),weights=weights)
    if reg['part']=='body':
        mats={k:material(k,'body',None,reg['team']) for k in PALETTES}
        ob.data.materials.clear()
        for m in mats.values():ob.data.materials.append(m)
        keys=list(mats)
        for p in ob.data.polygons:
            c=sum((ob.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
            cape=any(any(j in (4,5,6) and w>.01 for j,w in weights[i].items()) for i in p.vertices)
            arm_weight=sum(sum(w for j,w in weights[i].items() if j in (10,11,12,13,14,17,18,19,20,21)) for i in p.vertices)/len(p.vertices)
            if cape:kind='team' if reg['team'] else 'wool'
            elif arm_weight>.45:kind='skin'
            elif c.y<.070:kind='leather'
            elif c.y<.437:kind='bronze'
            elif c.y<.61:kind='skin'
            elif c.y<.877:kind='linen'
            elif abs(c.x)<.215 and c.y<1.326:kind='bronze'
            elif abs(c.x)<.23:kind='wool'
            else:kind='skin'
            if .83<c.y<.89 and not cape:kind='leather'
            p.material_index=keys.index(kind)
        active(ob);bm=bmesh.new();bm.from_mesh(ob.data)
        deform=bm.verts.layers.deform.active
        cape_groups={i for i,vg in enumerate(ob.vertex_groups) if vg.name in ('j4','j5','j6')}
        old_cloak=[f for f in bm.faces if any(sum(w for j,w in v[deform].items() if j in cape_groups)>.2 for v in f.verts)]
        bare=[f for f in bm.faces if ob.data.materials[f.material_index].get('kind') in ('skin','wool','wooldark') or (sum(v.co.y for v in f.verts)/len(f.verts)<.61 and ob.data.materials[f.material_index].get('kind')=='bronze')]
        bmesh.ops.delete(bm,geom=list(set(old_cloak+bare)),context='FACES')
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bm.to_mesh(ob.data);bm.free()
        mod(ob,'SUBSURF',levels=1,subdivision_type='CATMULL_CLARK')
        pbr_forms.bulk_body(ob,g,bones)
        # Cloth follows the approved cape weights; folds are rest-space geometry.
        for v in ob.data.vertices:
            cape=sum(w.weight for w in v.groups if ob.vertex_groups[w.group].name in ('j4','j5','j6'))
            if v.co.y<.1:v.co.y=max(0,(v.co.y-.007)*.1/.093)
            if cape>.2:v.co.z+=.010*(1+sin(v.co.x*86+v.co.y*3))*min(1,(1.3-v.co.y)*2)*cape
        bm=bmesh.new();bm.from_mesh(ob.data)
        buried=[f for f in bm.faces if all(.92<v.co.y<1.30 and abs(v.co.x)<.22 and v.co.z>-.14 for v in f.verts) and ob.data.materials[f.material_index].get('kind')=='bronze']
        bmesh.ops.delete(bm,geom=buried,context='FACES');bm.to_mesh(ob.data);bm.free()
        mod(ob,'DECIMATE',ratio=.68)
    elif reg['part']=='Greek head':mod(ob,'SUBSURF',levels=1)

pbr_human.build(mesh,mod,material,parts,old,ix,g,bones,WORK)
pbr_forms.cloak(mesh,material)
pbr_forms.mantle(mesh,material)

# Aspis: measured socket frame, 64-segment convex dish, rolled lip, raised device.
regs=[r for r in d['meshes'][0]['extras']['vertex_regions'] if r['part']=='aspis']
rim=regs[-1];pts=np.array(old['POSITION'][rim['start']:rim['start']+rim['count']]);c=Vector(pts.mean(axis=0));val,vec=np.linalg.eigh(np.cov(pts.T));n=Vector(vec[:,0]);n*=1 if n.x>0 else -1
u=(Vector((0,1,0))-n*n.y).normalized();v=n.cross(u).normalized()
bronze=material('bronze','aspis','shield_arm');edge=material('edge','aspis','shield_arm');dark=material('darkbronze','aspis','shield_arm');team=material('team','aspis','shield_arm','shield rim')
verts=[c+n*.105];faces=[];N=64
for radius in (.09,.20,.30,.375,.389):
    for j in range(N):
        a=j*2*pi/N;verts.append(c+radius*(u*cos(a)+v*sin(a))+n*(.105*(1-(radius/.4)**2)))
for j in range(N):faces.append((0,1+j,1+(j+1)%N))
for row in range(4):
    for j in range(N):faces.append((1+row*N+j,1+(row+1)*N+j,1+(row+1)*N+(j+1)%N,1+row*N+(j+1)%N))
shield=mesh('aspis dish',verts,faces,bronze,'shield_arm');mod(shield,'SOLIDIFY',thickness=.009,offset=-1)
ring('aspis rolled lip',c+n*.008,u,v,.392,.012,edge,'shield_arm')
ring('aspis team inset',c+n*.013,u,v,.374,.005,team,'shield_arm',k=4)
ring('aspis inner bead',c+n*.045,u,v,.316,.004,edge,'shield_arm',k=4)
for j in range(12):
    a=j*2*pi/12;rad=u*cos(a)+v*sin(a);side=-u*sin(a)+v*cos(a)
    root=c+n*.110+rad*.065;tip=c+n*.046+rad*.30
    ray=mesh('sunburst ray', [root-side*.024,root+side*.024,tip,root+n*.018+rad*.065],[(0,1,3),(1,2,3),(2,0,3),(0,2,1)],edge,'shield_arm',smooth=False)
    mod(ray,'BEVEL',width=.0015,segments=2)
# Rounded central boss, and small rim rivets.
def ellipsoid(name,center,radii,mat,bone,segments=24,rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1)
    o=bpy.context.object;o.name='GEO-'+name
    for vert in o.data.vertices:vert.co=Vector(center)+Vector(tuple(vert.co[i]*radii[i] for i in range(3)))
    o.data.materials.append(mat);o.vertex_groups.new(name='j'+str(bones[bone])).add(list(range(len(o.data.vertices))),1,'REPLACE')
    for p in o.data.polygons:p.use_smooth=True
    parts.append(o);return o
boss=ellipsoid('sun boss',(0,0,0),(.06,.06,.026),edge,'shield_arm',24,8)
for vert in boss.data.vertices:vert.co=c+u*vert.co.x+v*vert.co.y+n*(.116+vert.co.z)
for j in range(12):
    a=2*pi*j/12;p=c+(u*cos(a)+v*sin(a))*.354+n*.029
    ellipsoid('rim rivet',p,(.004,)*3,edge,'shield_arm',8,4)
# Spear retains exact grip/axis/endpoints; blade gets a true lenticular leaf section.
r=next(r for r in d['meshes'][0]['extras']['vertex_regions'] if r['part']=='spear');pts=np.array(old['POSITION'][r['start']:r['start']+r['count']]);center=Vector(pts.mean(axis=0));val,vec=np.linalg.eigh(np.cov(pts.T));axis=Vector(vec[:,-1]);axis*=1 if axis.z<0 else -1
projections=[(Vector(p)-center).dot(axis) for p in pts];lo,hi=min(projections),max(projections);base=center+axis*lo;tip=center+axis*hi
wood=material('wood','spear','weapon_R');metal=material('edge','spear','weapon_R');leather=material('leather','spear','weapon_R')
tube('spear ash shaft',[base+axis*.09,tip-axis*.21],[.012,.009],wood,'weapon_R',12)
tube('spear butt spike',[base,base+axis*.09,base+axis*.14],[.001,.014,.012],metal,'weapon_R',12)
tube('spear socket',[tip-axis*.25,tip-axis*.19],[.013,.011],metal,'weapon_R',12)
broad=axis.cross(Vector((1,0,0))).normalized();thin=axis.cross(broad).normalized();verts=[];faces=[]
for dist,width in [(.21,.010),(.16,.032),(.08,.023),(.001,.0004)]:
    p=tip-axis*dist
    verts.extend([p+broad*width,p+thin*.005,p-broad*width,p-thin*.005])
for k in range(3):
    for j in range(4):faces.append((k*4+j,k*4+(j+1)%4,(k+1)*4+(j+1)%4,(k+1)*4+j))
faces.extend([(3,2,1,0),(12,13,14,15)]);blade=mesh('leaf blade',verts,faces,metal,'weapon_R',smooth=False);mod(blade,'BEVEL',width=.0005,segments=2)
# Corinthian helmet: round dome, open eye line, cheek guards and nose guard.
helm=material('bronze','helmet','helmet');hem=material('edge','helmet','helmet');lining=material('leather','helmet','helmet')
verts=[(0,1.701,.003)];faces=[];N=40
for row in range(1,9):
    theta=row*pi/16
    for j in range(N):
        a=j*2*pi/N;verts.append((.103*sin(theta)*cos(a),1.565+.136*cos(theta),.003+.137*sin(theta)*sin(a)))
for j in range(N):faces.append((0,1+j,1+(j+1)%N))
for row in range(7):
    for j in range(N):faces.append((1+row*N+j,1+(row+1)*N+j,1+(row+1)*N+(j+1)%N,1+row*N+(j+1)%N))
o=mesh('helmet dome',verts,faces,helm,'helmet');mod(o,'SOLIDIFY',thickness=.004)
for side in (-1,1):
    coords=[(.021,1.526,.135),(.085,1.548,.094),(.105,1.56,.014),(.096,1.411,.026),(.057,1.378,.111),(.025,1.438,.136)]
    o=mesh('Corinthian cheek',[(x*side,y,z) for x,y,z in coords],[(0,1,2,3,4,5)],helm,'helmet');mod(o,'SOLIDIFY',thickness=.006);mod(o,'BEVEL',width=.004,segments=3)
    tube('brow ridge',[(side*.006,1.568,.143),(side*.044,1.572,.134),(side*.086,1.568,.099)],[.007]*3,hem,'helmet',8)
    tube('cheek edging',[(side*.022,1.524,.14),(side*.026,1.441,.14),(side*.057,1.381,.113),(side*.096,1.414,.028)],[.0025]*4,hem,'helmet',6)
nose=mesh('nose guard',[(-.012,1.568,.144),(.012,1.568,.144),(.014,1.467,.153),(-.014,1.467,.153)],[(0,1,2,3)],hem,'helmet');mod(nose,'SOLIDIFY',thickness=.005);mod(nose,'BEVEL',width=.003,segments=3)
# Round-two full sagittal horsehair arc; all vertices stay on helmet.
pbr_forms.crest(mesh,mod,tube,material)
# Curved bronze greave shells: anatomical taper, actual thickness and rolled
# edges, attached to the unchanged calf sockets rather than painted on skin.
for side,bone in [(-1,'leg_R'),(1,'leg_L')]:
    greave=material('bronze','greave',bone);lip=material('edge','greave',bone)
    levels=[(.098,.034,.050,-.058),(.16,.049,.066,-.061),(.26,.068,.077,-.064),(.36,.065,.074,-.057),(.438,.057,.065,-.044),(.475,.046,.052,-.035)]
    verts=[];faces=[];N=20
    for y,rx,rz,zc in levels:
        for j in range(N+1):
            a=-1.68+3.36*j/N
            verts.append((side*.147+rx*sin(a),y+(.013*cos(a) if y>.43 else 0),zc+rz*cos(a)))
    for k in range(len(levels)-1):
        for j in range(N):faces.append((k*(N+1)+j,k*(N+1)+j+1,(k+1)*(N+1)+j+1,(k+1)*(N+1)+j))
    ob=mesh('greave shell',verts,faces,greave,bone);mod(ob,'SOLIDIFY',thickness=.004);mod(ob,'BEVEL',width=.0015,segments=2)
    for k in (0,len(levels)-1):
        row=verts[k*(N+1):(k+1)*(N+1)]
        tube('rolled greave lip',row,[.003]*len(row),lip,bone,5)
    # Raised central rib reads in the material without a painted highlight.
    tube('greave keel',[(side*.147,y,zc+rz+.003) for y,rx,rz,zc in levels],[.0025]*len(levels),lip,bone,6)
# Sandals wrap the anatomical CC0 feet; all straps follow the native foot joints.
for side,bone in [(-1,'foot_R'),(1,'foot_L')]:
    strap=material('leather','sandal',bone)
    for z,y in [(-.005,.072),(.055,.065),(.105,.044)]:
        tube('leather sandal strap',[(side*.147+dx,y+dy,z) for dx,dy in [(-.050,-.035),(-.040,0),(0,.008),(.040,0),(.050,-.035)]],[.006]*5,strap,bone,5)
# Layered leather pteruges around the waist, following the existing pelvis.
pter=material('leather','pteruges','hip');gold=material('edge','pteruges','hip')
for j in range(14):
    a=2*pi*j/14;u=Vector((cos(a),0,sin(a)));v=Vector((-sin(a),0,cos(a)));p=Vector((.232*cos(a),.912,.181*sin(a)))
    verts=[p+v*dx+Vector((0,dy,0))+u*push for dx,dy,push in [(-.025,0,0),(.025,0,0),(.025,-.22,.055),(.018,-.24,.058),(-.018,-.24,.058),(-.025,-.22,.055)]]
    o=mesh('pteruges',verts,[tuple(range(6))],pter,'hip');mod(o,'SOLIDIFY',thickness=.004);mod(o,'BEVEL',width=.003,segments=2)
    ellipsoid('pteruges rivet',p+u*.006+Vector((0,-.022,0)),(.004,)*3,gold,'hip',8,4)
# Fit sculpted armour to native body weights; all animation data stays frozen.
def torso_weights(verts):
    # Continuous torso-only skinning: nearest-surface transfer can accidentally
    # attach a broad breastplate to an upper arm and crease it on raised poses.
    anchors=[(.856,0),(.926,1),(.994,2),(1.096,3)]
    result=[]
    for v in verts:
        y=v[1]
        if y>=anchors[-1][0]:result.append({3:1.0});continue
        if y<=anchors[0][0]:result.append({0:1.0});continue
        for (lo,a),(hi,b) in zip(anchors,anchors[1:]):
            if lo<=y<=hi:
                t=(y-lo)/(hi-lo);result.append({a:1-t,b:t});break
    return result
pbr_forms.cuirass(mesh,mod,tube,material,torso_weights)
# Keep the new shield relief inside the approved death-contact depth envelope.
# Only its rest geometry changes; the shield socket and all animation are frozen.
for ob in parts:
    if catalog[ob.data.materials[0].name]['part']=='aspis':
        for vert in ob.data.vertices:
            depth=(vert.co-c).dot(n);vert.co-=n*depth*.36
# Slightly oversize the helmet and crest around the unchanged head socket.
for ob in parts:
    if catalog[ob.data.materials[0].name]['part'] in ('helmet','crest','crest_base'):
        for vert in ob.data.vertices:
            vert.co.x*=1.10;vert.co.y=1.472+(vert.co.y-1.472)*1.045;vert.co.z=-.01+(vert.co.z+.01)*1.08
# Reserve the round silhouettes before reducing the rest of LOD0. A global
# decimator otherwise turns a 64-sided lip back into a visibly polygonal one.
protected={'GEO-aspis rolled lip','GEO-helmet dome','GEO-aspis dish','GEO-CC0 muscular anatomy'}
protected_count=other_count=0
for ob in parts:
    ob.data.calc_loop_triangles();ntri=len(ob.data.loop_triangles)
    if ob.name in protected:protected_count+=ntri
    else:other_count+=ntri
ratio=min(1,(9700-protected_count-80)/other_count)
assert ratio>0
for ob in parts:
    if ob.name not in protected:mod(ob,'DECIMATE',ratio=ratio)
print('SILHOUETTE_BUDGET',protected_count,other_count,ratio,flush=True)
# Assemble the game mesh, globally unwrap, then build actual dense bake source.
active(parts[0])
for o in parts:o.select_set(True)
bpy.ops.object.join();low=bpy.context.object;low.name='GEO-spearman_LOD0'
low.data.calc_loop_triangles();count=len(low.data.loop_triangles)
if count>9700:mod(low,'DECIMATE',ratio=9700/count)
# Geometry-only contact fit against frozen round-6 animation. Project only
# vertices below the existing 2mm tolerance; never alter a joint or key.
# This resolves changed silhouette contact at the floor, not mesh intersections.
def fit_contact(ob):
    pos=np.array([tuple(v.co) for v in ob.data.vertices]);js=np.zeros((len(pos),4),dtype=int);ws=np.zeros((len(pos),4))
    for v in ob.data.vertices:
        pairs=sorted([(int(ob.vertex_groups[w.group].name[1:]),w.weight) for w in v.groups if w.weight>1e-8],key=lambda x:-x[1])[:4]
        total=sum(w for _,w in pairs)
        for k,(j,w) in enumerate(pairs):js[v.index,k]=j;ws[v.index,k]=w/total
    skin=d['skins'][0];inv=np.array(g.accessor(skin['inverseBindMatrices'])).reshape(-1,4,4).transpose(0,2,1)
    planes=[]
    for clip in d['animations']:
        duration=max(g.accessor(s['input'])[-1][0] for s in clip['samplers']);count=round(duration*120)
        for f in range(count+1):
            worlds=g.worlds(clip,duration*f/count);world=np.array([worlds[j] for j in skin['joints']]).reshape(-1,4,4).transpose(0,2,1)
            planes.append((world@inv)[:,1,:])
    original_pos=pos.copy()
    for iteration in range(3):
        for plane in planes:
            transform=sum(plane[js[:,k]]*ws[:,k,None] for k in range(4));height=np.einsum('ij,ij->i',transform[:,:3],pos)+transform[:,3]
            mask=height<-.0015
            if mask.any():
                normals=transform[mask,:3];pos[mask]+=normals*((-.001-height[mask])/np.einsum('ij,ij->i',normals,normals))[:,None]
    for vert,p in zip(ob.data.vertices,pos):vert.co=p
    print('REST_CONTACT_FIT_MAX_METRES',float(np.linalg.norm(pos-original_pos,axis=1).max()),flush=True)
fit_contact(low)
# Freeze triangulation before the high/low bake. Nonplanar cheek n-gons must
# use the same surface on both sides of the projection.
mod(low,'TRIANGULATE')
active(low);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008);bpy.ops.object.mode_set(mode='OBJECT')
# High source has 16x faces, real hammered displacement and shader weave/pores.
high=low.copy();high.data=low.data.copy();bpy.context.collection.objects.link(high);high.name='GEO-high-bake-source'
mod(high,'SUBSURF',levels=2,subdivision_type='SIMPLE')
texture=bpy.data.textures.new('Hammer and fibres',type='CLOUDS');texture.noise_scale=.006;texture.noise_depth=2
mod(high,'DISPLACE',texture=texture,strength=.00045,mid_level=.5,texture_coords='GLOBAL')
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.render.bake.margin=8 if SIZE==512 else 16;scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.0009;scene.render.bake.max_ray_distance=.002
images={}
for name in ['basecolor','normal','ao','roughness','metallic']:
    im=bpy.data.images.new('pbr-'+name,SIZE,SIZE,alpha=False,float_buffer=False);im.colorspace_settings.name='sRGB' if name=='basecolor' else 'Non-Color';images[name]=im
    for mat in low.data.materials:
        node=mat.node_tree.nodes.get('Bake Target') or mat.node_tree.nodes.new('ShaderNodeTexImage');node.name='Bake Target';node.image=im;mat.node_tree.nodes.active=node
    active(low);high.select_set(True)
    scene.render.bake.use_selected_to_active=name in ('normal','ao')
    if name=='normal':bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT')
    elif name=='ao':bpy.ops.object.bake(type='AO')
    else:
        for mat in high.data.materials:
            nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF');output=nodes.get('Material Output');em=nodes.new('ShaderNodeEmission');em.name='Bake Scalar'
            inp=bs.inputs[{'basecolor':'Base Color','roughness':'Roughness','metallic':'Metallic'}[name]]
            if inp.is_linked:links.new(inp.links[0].from_socket,em.inputs['Color'])
            else:em.inputs['Color'].default_value=(inp.default_value,)*3+(1,)
            links.new(em.outputs[0],output.inputs['Surface'])
        bpy.ops.object.bake(type='EMIT')
        for mat in high.data.materials:
            links=mat.node_tree.links;nodes=mat.node_tree.nodes;links.new(nodes.get('Principled BSDF').outputs[0],nodes.get('Material Output').inputs['Surface']);nodes.remove(nodes.get('Bake Scalar'))
    im.filepath_raw=str(WORK/f'{name}-{SIZE}.png');im.file_format='PNG';im.save();print('BAKED',name,SIZE,flush=True)
# Pack AO/roughness/metallic in linear channels; never multiply AO into pigment.
a=np.empty(SIZE*SIZE*4,dtype=np.float32);images['ao'].pixels.foreach_get(a);r=np.empty_like(a);images['roughness'].pixels.foreach_get(r);m=np.empty_like(a);images['metallic'].pixels.foreach_get(m)
orm=np.ones((SIZE*SIZE,4),dtype=np.float32);orm[:,0]=a.reshape(-1,4)[:,0];orm[:,1]=r.reshape(-1,4)[:,0];orm[:,2]=m.reshape(-1,4)[:,0]
im=bpy.data.images.new('pbr-orm',SIZE,SIZE,alpha=False);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(orm.ravel());im.filepath_raw=str(WORK/f'orm-{SIZE}.png');im.file_format='PNG';im.save();images['orm']=im
paths={}
for name in ['basecolor','normal','orm']:
    im=images[name];im.scale(1024,1024)
    ship=bpy.data.images.new('ship-'+name,1024,1024,alpha=False,float_buffer=False)
    ship.colorspace_settings.name=im.colorspace_settings.name
    px=np.empty(1024*1024*4,dtype=np.float32);im.pixels.foreach_get(px);ship.pixels.foreach_set(px)
    ship.filepath_raw=str(WORK/f'{name}-1024.png');ship.file_format='PNG';ship.save();paths[name]=str(UNIT/f'spearman-{name}.webp')
subprocess.run([str(ROOT/'venv/bin/python'),str(UNIT/'pbr_textures.py'),str(WORK),str(UNIT)],check=True)
high.hide_render=True;high.hide_set(True)
# LOD1 keeps UV islands, material boundaries and weights; the skeleton is shared.
lod=low.copy();lod.data=low.data.copy();bpy.context.collection.objects.link(lod);lod.name='GEO-spearman_LOD1'
low.data.calc_loop_triangles();mod(lod,'DECIMATE',ratio=2850/len(low.data.loop_triangles));lod.hide_render=True
fit_contact(lod)
for o in (low,lod):mod(o,'TRIANGULATE')
lods=[extract(o,catalog) for o in (low,lod)]
write_glb(g,lods,paths,UNIT/'spearman.glb',master_size=SIZE)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'spearman-pbr-master.blend'))
report={'source':str(SOURCE),'bake_master_px':SIZE,'shipped_px':1024,'lod_triangles':[len(x[1])//3 for x in lods],'high_source_triangles':sum(len(p.vertices)-2 for p in high.data.polygons),'textures':paths}
(WORK/'build-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
