"""Painted premium geometry and Cycles bakes; never edits the approved motion.
Run with gated Blender after sourcing ../../env.sh. Heavy masters live in ANIM_ROOT.
Geometry is authored in the original glTF bind coordinates (Y up).
"""
import bpy, bmesh, math, os, sys, json, struct, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
UNIT=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
WORK=ROOT/'lanes/spearman-0ad-painted-r1';WORK.mkdir(parents=True,exist_ok=True)
SOURCE=WORK/'approved-r6.glb'
g=GLB(SOURCE);d=g.doc
attrs=d['meshes'][0]['primitives'][0]['attributes'];original={k:g.accessor(v) for k,v in attrs.items()}
indices=[v[0] for v in g.accessor(d['meshes'][0]['primitives'][0]['indices'])]
regions=d['meshes'][0]['extras']['vertex_regions']
bones=[d['nodes'][j]['name'] for j in d['skins'][0]['joints']]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
objects=[]

def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o

def apply(o,kind,**kw):
    active(o);m=o.modifiers.new(kind,kind)
    for k,v in kw.items():setattr(m,k,v)
    bpy.ops.object.modifier_apply(modifier=m.name)

def material(name,col,rough,metal,scale=75):
    m=bpy.data.materials.new(name);m.use_nodes=True;m['rough']=rough;m['metal']=metal
    n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputMaterial');emit=n.new('ShaderNodeEmission');l.new(emit.outputs[0],out.inputs['Surface'])
    geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=2
    l.new(geo.outputs['Position'],noise.inputs['Vector'])
    dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=(-.35,.8,.45);l.new(geo.outputs['Normal'],dot.inputs[0])
    ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=-1;ramp.inputs['From Max'].default_value=1;ramp.inputs['To Min'].default_value=.20;ramp.inputs['To Max'].default_value=1.55;l.new(dot.outputs['Value'],ramp.inputs[0])
    pigment=n.new('ShaderNodeMixRGB');pigment.blend_type='MULTIPLY';pigment.inputs[0].default_value=1;pigment.inputs[1].default_value=(*col,1);l.new(ramp.outputs[0],pigment.inputs[2])
    grain=n.new('ShaderNodeMixRGB');grain.blend_type='MULTIPLY';grain.inputs[0].default_value=.26;l.new(pigment.outputs[0],grain.inputs[1]);l.new(noise.outputs['Fac'],grain.inputs[2]);l.new(grain.outputs[0],emit.inputs[0]);m['paint_node']=grain.name
    return m
M={
'bronze':material('Painted ochre bronze',(.45,.215,.046),.63,.32),
'gold':material('Worn raised gold',(.82,.50,.14),.53,.38),
'shield':material('Recessed bronze shield field',(.235,.105,.025),.78,.25),
'dark':material('Engraved umber bronze',(.105,.057,.017),.82,.18),
'linen':material('Warm ivory linen',(.72,.57,.35),.95,0,160),
'red':material('Crimson wool',(.24,.008,.006),.96,0,140),
'leather':material('Oiled oxhide',(.11,.044,.017),.78,0,85),
'skin':material('Warm skin',(.49,.255,.115),.8,0,45),
'mask':material('Neutral team pigment',(.65,.56,.45),.9,0,100),
'wood':material('Ash spear shaft',(.22,.095,.025),.8,0,95)}

def mesh(name,vs,fs,mat='bronze',bone=None,team=None,weights=None):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
    ob=bpy.data.objects.new('GEO-'+name,me);bpy.context.collection.objects.link(ob);me.materials.append(M[mat])
    ob['part']=name.split(':')[0];ob['bone']=bone or '';ob['team']=team or '';ob['mat']=mat
    for p in me.polygons:p.use_smooth=True
    if bone:
        ob.vertex_groups.new(name=bone).add(list(range(len(vs))),1,'REPLACE')
    elif weights:
        for b in bones:ob.vertex_groups.new(name=b)
        for i,ww in enumerate(weights):
            for j,w in ww:
                if w>0:ob.vertex_groups[j].add([i],w,'REPLACE')
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    objects.append(ob);return ob

def sphere(name,c,r,mat,bone,team=None,seg=24,rings=12):
    vs=[];fs=[]
    for j in range(rings+1):
        t=math.pi*j/rings
        for i in range(seg):
            a=2*math.pi*i/seg;vs.append((c[0]+r[0]*math.sin(t)*math.cos(a),c[1]+r[1]*math.cos(t),c[2]+r[2]*math.sin(t)*math.sin(a)))
    for j in range(rings):
        for i in range(seg):a=j*seg+i;b=j*seg+(i+1)%seg;fs.append((a,b,b+seg,a+seg))
    ob=mesh(name,vs,fs,mat,bone,team);active(ob)
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.to_mesh(ob.data);bm.free();return ob

def tube(name,points,radii,mat,bone,team=None,seg=8):
    vs=[];fs=[];points=list(map(Vector,points))
    for j,p in enumerate(points):
        tangent=(points[min(j+1,len(points)-1)]-points[max(0,j-1)]).normalized();a=tangent.cross(Vector((0,1,0)))
        if a.length<.1:a=tangent.cross(Vector((1,0,0)))
        a.normalize();b=tangent.cross(a).normalized()
        for i in range(seg):vs.append(p+radii[j]*(a*math.cos(i*2*math.pi/seg)+b*math.sin(i*2*math.pi/seg)))
    for j in range(len(points)-1):
        for i in range(seg):a=j*seg+i;b=j*seg+(i+1)%seg;fs.append((a,b,b+seg,a+seg))
    fs.extend([tuple(range(seg-1,-1,-1)),tuple((len(points)-1)*seg+i for i in range(seg))])
    return mesh(name,vs,fs,mat,bone,team)

# Retain the native body and cloak weights. Split by pigment before adding cloth form.
for ri,r in enumerate(regions):
    if r['part'] not in {'body','Greek head','Aspis handgrip'}:continue
    selected=[indices[i:i+3] for i in range(0,len(indices),3) if r['start']<=indices[i]<r['start']+r['count']]
    buckets={}
    for face in selected:
        c=np.mean([original['POSITION'][i] for i in face],axis=0)
        cape=any(abs(original['TEXCOORD_0'][i][0]-.15625)<1e-5 and abs(original['TEXCOORD_0'][i][1]-.125)<1e-5 for i in face) or any(bones[int(j)].startswith('cape') and w>.01 for i in face for j,w in zip(original['JOINTS_0'][i],original['WEIGHTS_0'][i]))
        limb=any(bones[int(j)].startswith(('hand','finger','forearm')) and w>.5 for i in face for j,w in zip(original['JOINTS_0'][i],original['WEIGHTS_0'][i]))
        if r['team']:mat='mask'
        elif r['part']=='Greek head':mat='skin'
        elif r['part']=='Aspis handgrip':mat='leather'
        elif cape:mat='red'
        elif limb:mat='skin'
        elif c[1]<.07:mat='leather'
        elif c[1]<.44:mat='bronze'
        elif c[1]<.55:mat='skin'
        elif c[1]<.87:mat='linen'
        elif c[1]<.91:mat='leather'
        elif abs(c[0])<.23 and c[1]<1.28:mat='bronze'
        elif c[1]<1.36:mat='linen'
        else:mat='skin'
        # New cuirass replaces the covered native bronze surface, preventing z-fighting.
        if r['part']=='body' and mat=='bronze' and .89<c[1]<1.21 and abs(c[0])<.22:continue
        buckets.setdefault((mat,cape),[]).append(face)
    for (mat,cape),faces in buckets.items():
        used=sorted(set(i for f in faces for i in f));remap={v:i for i,v in enumerate(used)}
        ww=[list(zip(original['JOINTS_0'][i],original['WEIGHTS_0'][i])) for i in used]
        ob=mesh(r['part']+':'+str(ri)+mat,[original['POSITION'][i] for i in used],[[remap[i] for i in f] for f in faces],mat,r['bone'],r['team'],ww)
        # Simple subdivision retains approved attachment and anatomical boundary positions.
        apply(ob,'SUBSURF',subdivision_type='SIMPLE',levels=1)
        if cape:
            apply(ob,'SMOOTH',factor=.25,iterations=2)
            for v in ob.data.vertices:
                v.co.z-=.018*(.5+.5*math.sin(v.co.x*70+v.co.y*3))*max(0,min(1,(1.4-v.co.y)*2))
        if r['part']=='Greek head':apply(ob,'SMOOTH',factor=.15,iterations=2)
        if r['part']=='body' and not cape and not r['team']:
            if mat in {'bronze','skin'}:apply(ob,'SMOOTH',factor=.35,iterations=2)
            if mat=='linen':
                for v in ob.data.vertices:
                    v.co.z+=.006*math.sin(v.co.x*80)*max(0,1-abs(v.co.y-.69)*4)

# Round 64-segment shield, in the original shield plane and socket.
rr=[r for r in regions if r['part']=='aspis' and r['team']]
points=np.array(original['POSITION'][rr[0]['start']:rr[0]['start']+rr[0]['count']])
center=Vector((points.min(0)+points.max(0))/2)
_,_,vh=np.linalg.svd(points-points.mean(0));normal=Vector(vh[-1]);normal*=1 if normal.x>0 else -1
up=(Vector((0,1,0))-normal*normal.y).normalized();right=up.cross(normal).normalized();radius=.401

def shield_point(r,a,depth=0):return center+right*(r*math.cos(a))+up*(r*math.sin(a))+normal*depth
vs=[shield_point(0,0,.093)];fs=[]
for ring in range(1,7):
    r=radius*ring/6
    for i in range(64):vs.append(shield_point(r,i*math.tau/64,.093*(1-(r/radius)**2)))
for i in range(64):fs.append((0,1+i,1+(i+1)%64))
for ring in range(5):
    for i in range(64):a=1+ring*64+i;b=1+ring*64+(i+1)%64;fs.append((a,a+64,b+64,b))
shield=mesh('aspis',vs,fs,'shield','shield_arm');apply(shield,'SOLIDIFY',thickness=.009,offset=-1)
for rad,depth,width,mat,team in [(radius,0,.015,'mask','shield rim'),(.373,.014,.006,'gold',None),(.095,.10,.008,'gold',None)]:
    pts=[shield_point(rad,i*math.tau/64,depth) for i in range(65)]
    tube('aspis:rolled rim',pts,[width]*65,mat,'shield_arm',team,8)
# Twelve physically raised, ridged bronze rays.
for i in range(12):
    a=i*math.tau/12;coords=[(.098,a-.12),(.325,a),(.098,a+.12),(.17,a)]
    vs=[shield_point(r,t,.093*(1-(r/radius)**2)+(.027 if j==3 else .007)) for j,(r,t) in enumerate(coords)]
    ray=mesh('aspis:sunray',vs,[(0,1,3),(1,2,3),(2,0,3)],'gold','shield_arm');apply(ray,'SOLIDIFY',thickness=.003)
    apply(ray,'BEVEL',width=.0018,segments=2)
sphere('aspis:boss',center+normal*.105,(.001,.001,.001),'gold','shield_arm')
# Orient ellipsoidal boss in the shield basis rather than world axes.
boss=objects[-1]
for v in boss.data.vertices:
    q=(v.co-(center+normal*.105))/.001;v.co=center+normal*(.105+q.z*.031)+right*q.x*.083+up*q.y*.083
for i in range(32):
    c=shield_point(.354,i*math.tau/32,.026)
    sphere('aspis:rivet',c,(.005,)*3,'gold','shield_arm',seg=8,rings=4)

# Engraved inner register and worn lip separate the dark field from raised rays.
for rad,dep,width,mat in [(.338,.032,.0028,'dark'),(.345,.030,.0025,'gold'),(.103,.099,.003,'dark')]:
    tube('aspis:engraving',[shield_point(rad,i*math.tau/64,dep) for i in range(65)],[width]*65,mat,'shield_arm',seg=6)

# Corinthian helmet: smooth dome, cut-out brow, nasal and swept cheek plates.
vs=[];fs=[];seg=48;rings=9
for j in range(rings+1):
    t=(math.pi/2)*j/rings
    for i in range(seg):
        a=i*math.tau/seg;vs.append((.104*math.sin(t)*math.cos(a),1.572+.132*math.cos(t),.012+.133*math.sin(t)*math.sin(a)))
for j in range(rings):
    for i in range(seg):a=j*seg+i;b=j*seg+(i+1)%seg;fs.append((a,b,b+seg,a+seg))
ob=mesh('helmet:dome',vs,fs,'bronze','helmet');apply(ob,'SOLIDIFY',thickness=.005,offset=-1)
for side in [-1,1]:
    # Face opening stays empty, bounded by brow/nose and both cheek guards.
    pts=[(side*.023,1.55,.138),(side*.082,1.558,.102),(side*.101,1.52,.057),(side*.085,1.388,.074),(side*.035,1.413,.128)]
    ob=mesh('helmet:cheek',pts,[(0,1,2,3,4)],'bronze','helmet');apply(ob,'SOLIDIFY',thickness=.008);apply(ob,'BEVEL',width=.006,segments=3)
    tube('helmet:brow',[(side*.005,1.58,.145),(side*.038,1.592,.139),(side*.081,1.585,.114),(side*.102,1.563,.073)],[.007]*4,'gold','helmet',seg=8)
    tube('helmet:cheek engraving',[(side*.034,1.544,.144),(side*.043,1.46,.139),(side*.075,1.414,.106)],[.0025]*3,'gold','helmet',seg=6)
# Dark recessed backing closes the small eye aperture against the smaller native head.
for side in [-1,1]:
    mesh('helmet:eye recess',[(side*.014,1.583,.135),(side*.089,1.577,.096),(side*.085,1.541,.098),(side*.018,1.54,.132)],[(0,1,2,3)],'dark','helmet')
ob=mesh('helmet:nasal',[(-.013,1.586,.15),(.013,1.586,.15),(.018,1.483,.16),(0,1.46,.164),(-.018,1.483,.16)],[(0,1,2,3,4)],'gold','helmet');apply(ob,'SOLIDIFY',thickness=.006);apply(ob,'BEVEL',width=.003,segments=2)
# Rounded crest support and a continuous full horsehair mass with sculpted fluting.
pts=[(0,1.570+.143*math.sin(t),.012+.15*math.cos(t)) for t in np.linspace(0,math.pi,24)]
tube('crest_base',pts,[.012]*24,'gold','helmet',seg=10)
vs=[];fs=[];n=64
for j in range(5):
    t=j/4
    for side in [-1,1]:
        for i in range(n+1):
            a=.03+(math.pi-.06)*i/n
            h=(.145+.20*t)*math.sin(a);z=.012+(.15+.10*t)*math.cos(a)
            width=(.018+.019*math.sin(t*math.pi/2))*(1-.14*t+.14*t*math.sin(i*math.pi/2))
            vs.append((side*width,1.572+h,z))
for j in range(4):
    for s in range(2):
        for i in range(n):a=j*2*(n+1)+s*(n+1)+i;b=a+2*(n+1);fs.append((a,a+1,b+1,b))
for i in range(n):a=4*2*(n+1)+i;fs.append((a,a+1,a+n+2,a+n+1))
ob=mesh('crest',vs,fs,'mask','helmet','crest');apply(ob,'BEVEL',width=.001,segments=2)

# Leaf spear uses the approved shaft's principal axis and endpoint envelope.
r=next(r for r in regions if r['part']=='spear');p=np.array(original['POSITION'][r['start']:r['start']+r['count']]);c=Vector(p.mean(0));_,_,vh=np.linalg.svd(p-p.mean(0));axis=Vector(vh[0]);axis*=1 if axis.z<0 else -1
lengths=[(Vector(v)-c).dot(axis) for v in p];lo=min(lengths);hi=max(lengths)
a=axis.cross(Vector((0,1,0))).normalized();b=axis.cross(a).normalized()
start=c+axis*(lo+.10);end=c+axis*(hi-.25)
tube('spear:shaft',[start,end],[.010,.009],'wood','weapon_R',seg=12)
for f in [lo+.11,hi-.27,hi-.23]:tube('spear:ferrule',[c+axis*f,c+axis*(f+.022)],[.013,.013],'gold','weapon_R',seg=12)
for tip,base,width in [(hi,hi-.25,.035),(lo,lo+.12,.018)]:
    mid=base+(tip-base)*.42
    vs=[c+axis*base,c+axis*mid+a*width,c+axis*tip,c+axis*mid-a*width,c+axis*mid+b*.009,c+axis*mid-b*.009]
    mesh('spear:leaf blade',vs,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)],'gold','weapon_R')
# Anatomical cuirass: rounded chest and waist rings, interpolated native torso weights.
vs=[];fs=[];ww=[];ring_count=9;segments=32
for j in range(ring_count):
    t=j/(ring_count-1);y=.885+.395*t
    width=.145+.065*math.sin(t*math.pi*.80);depth=.105+.026*math.sin(t*math.pi)
    for i in range(segments):
        a=i*math.tau/segments;x=width*math.cos(a);z=depth*math.sin(a)
        if z>0:z+=.024*math.exp(-((y-1.17)/.075)**2)*(.3+.7*abs(math.sin(x*11)))
        vs.append((x,y,z));blend=max(0,min(1,t*1.5-.2));ww.append([(bones.index('spine1'),1-blend),(bones.index('chest'),blend)])
for j in range(ring_count-1):
    for i in range(segments):a=j*segments+i;b=j*segments+(i+1)%segments;fs.append((a,b,b+segments,a+segments))
ob=mesh('cuirass',vs,fs,'bronze',weights=ww);apply(ob,'SOLIDIFY',thickness=.004)
# Breastplate borders, abdominal register and embossed palmette.
for y,rad,depth,bone in [(.90,.15,.11,'spine1'),(1.025,.20,.13,'spine1'),(1.265,.186,.112,'chest')]:
    tube('cuirass:border',[(rad*math.cos(a),y,depth*math.sin(a)) for a in np.linspace(0,math.tau,49)],[.004]*49,'gold',bone,seg=6)
for side in [-1,1]:
    pts=[(side*x,y,z) for x,y,z in [(.018,1.19,.16),(.055,1.21,.164),(.11,1.213,.157),(.17,1.19,.125)]]
    tube('cuirass:pectoral engraving',pts,[.003]*4,'dark','chest',seg=6)
    tube('cuirass:pectoral edge',[(x,y+.007,z+.001) for x,y,z in pts],[.0025]*4,'gold','chest',seg=6)
for i in range(7):
    a=(i-3)*.24
    tube('cuirass:palmette',[(0,1.10,.143),(.048*math.sin(a),1.125,.15),(.078*math.sin(a),1.165-.025*abs(a),.155)],[.0035,.004,.0018],'gold','chest',seg=6)
for x in [-.12,-.06,0,.06,.12]:sphere('cuirass:rivet',(x,.949,.12),(.005,.005,.004),'gold','spine1',seg=8,rings=4)

# Leather pteruges anchored to the existing pelvis, with raised border stitching.
for i in range(14):
    a=i*math.tau/14;rr=.175;upper=.89;lower=.73+.025*math.cos(i*2)
    vs=[]
    for y,rad in [(upper,rr),(lower,.24)]:
        for da in [-.13,.13]:vs.append((rad*math.cos(a+da),y,rad*.85*math.sin(a+da)))
    ob=mesh('pteruges',vs,[(0,1,3,2)],'leather','hip');apply(ob,'SOLIDIFY',thickness=.006);apply(ob,'BEVEL',width=.005,segments=2)
# Greaves follow the original calf bones; wrap the actual bind leg centreline.
for side,sign in [('L',1),('R',-1)]:
    joint=bones.index('leg_'+side);pp=[Vector(v) for v,js,ws in zip(original['POSITION'],original['JOINTS_0'],original['WEIGHTS_0']) if any(int(j)==joint and w>.5 for j,w in zip(js,ws))]
    if not pp:continue
    x=sum(v.x for v in pp)/len(pp);z=sum(v.z for v in pp)/len(pp)
    vs=[];fs=[]
    for j in range(7):
        t=j/6;y=.10+.32*t;rad=.049+.018*math.sin(t*math.pi/2)
        for i in range(17):
            a=-math.pi*.58+math.pi*1.16*i/16;vs.append((x+rad*math.sin(a),y,z+rad*math.cos(a)+.014))
    for j in range(6):
        for i in range(16):a=j*17+i;fs.append((a,a+1,a+18,a+17))
    ob=mesh('greave_'+side,vs,fs,'bronze','leg_'+side);apply(ob,'SOLIDIFY',thickness=.004);apply(ob,'BEVEL',width=.002,segments=2)
    tube('greave_'+side+':ridge',[(x,.115,z+.065),(x,.26,z+.081),(x,.40,z+.077)],[.0035]*3,'gold','leg_'+side,seg=6)

# Explicitly retain separate authoring parts; both runtime LODs get one primitive.
for ob in objects:
    for p in ob.data.polygons:p.use_smooth=True
# Spend the mesh budget proportionally, preserving small bevels and round outlines.
def triangles(ob):return sum(len(p.vertices)-2 for p in ob.data.polygons)
raw=sum(map(triangles,objects));ratio=min(1,8600/raw)
for ob in objects:
    if triangles(ob)>40 and ratio<1:
        part_ratio=.75 if ob['team']=='shield rim' else .85 if ob['part']=='crest_base' else min(1,ratio*1.4) if ob['part']=='helmet' else ratio
        apply(ob,'DECIMATE',ratio=part_ratio)
from painted_contact import fit
fit(objects,g,bones)
print('GEOMETRY',raw,'->',sum(map(triangles,objects)),flush=True)
# One packed non-overlapping UV0 shared by all pigments.
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.002,area_weight=1.0);bpy.ops.object.mode_set(mode='OBJECT')
# Baking copies, leaving the per-part low meshes and weights intact.
def joined_copies(items,name):
    copies=[]
    for ob in items:
        x=ob.copy();x.data=ob.data.copy();bpy.context.collection.objects.link(x);copies.append(x)
    bpy.ops.object.select_all(action='DESELECT')
    for x in copies:x.select_set(True)
    bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();x=bpy.context.object;x.name=name;return x
low=joined_copies(objects,'Bake low');high=joined_copies(objects,'Sculpt high');pigment=joined_copies(objects,'Paint source')
pigment.hide_render=True;pigment.hide_set(True)
apply(high,'SUBSURF',subdivision_type='SIMPLE',levels=2)
tex=bpy.data.textures.new('Hammered bronze and woven grain',type='CLOUDS');tex.noise_scale=.009;tex.noise_depth=1
apply(high,'DISPLACE',texture=tex,strength=.0012,mid_level=.5)
for ob in objects:ob.hide_render=True;ob.hide_set(True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=8
s.render.bake.use_selected_to_active=True;s.render.bake.cage_extrusion=.008;s.render.bake.max_ray_distance=.02;s.render.bake.margin=12
size=2048
normal=bpy.data.images.new('normal master',size,size,alpha=False,float_buffer=False);normal.colorspace_settings.name='Non-Color'
ao=bpy.data.images.new('AO master',size,size,alpha=False,float_buffer=False);ao.colorspace_settings.name='Non-Color'
base=bpy.data.images.new('basecolor master',size,size,alpha=False,float_buffer=False)
orm=bpy.data.images.new('ORM master',size,size,alpha=False,float_buffer=False);orm.colorspace_settings.name='Non-Color'
# Low target gets an independent material to avoid an image feedback cycle.
low.data.materials.clear();target=bpy.data.materials.new('Bake receiver');target.use_nodes=True;low.data.materials.append(target)
for p in low.data.polygons:p.material_index=0
node=target.node_tree.nodes.new('ShaderNodeTexImage');target.node_tree.nodes.active=node
for im,mode in [(normal,'NORMAL'),(ao,'AO')]:
    node.image=im;active(low);high.select_set(True)
    print('BAKE',mode,size,flush=True);bpy.ops.object.bake(type=mode)
    im.filepath_raw=str(WORK/(im.name.replace(' ','-')+'.png'));im.file_format='PNG';im.save()
# Bake authored base pigment on its own surface, avoiding ray hits on adjacent thin props.
high.hide_render=True;low.hide_render=True;pigment.hide_render=False;pigment.hide_set(False)
s.render.bake.use_selected_to_active=False
for m in pigment.data.materials:
    target_node=m.node_tree.nodes.new('ShaderNodeTexImage');target_node.image=base;m.node_tree.nodes.active=target_node
active(pigment);bpy.ops.object.bake(type='EMIT')
# Painted lane deliberately carries some ambient recess shading in the albedo.
bp=np.array(base.pixels[:],dtype=np.float32).reshape(-1,4);ap=np.array(ao.pixels[:],dtype=np.float32).reshape(-1,4)
bp[:,:3]*=(.65+.35*ap[:,:1]);base.pixels.foreach_set(bp.ravel());base.update()
base.filepath_raw=str(WORK/'basecolor-master.png');base.file_format='PNG';base.save()
pigment.hide_render=True;pigment.hide_set(True);high.hide_render=False;low.hide_render=False;s.render.bake.use_selected_to_active=True
# Bake material roughness / metallic as linear channels, then replace R with AO.
for m in M.values():
    e=next(n for n in m.node_tree.nodes if n.type=='EMISSION')
    for link in list(e.inputs[0].links):m.node_tree.links.remove(link)
    e.inputs[0].default_value=(1,m['rough'],m['metal'],1)
node.image=orm;active(low);high.select_set(True);bpy.ops.object.bake(type='EMIT')
pix=np.array(orm.pixels[:],dtype=np.float32).reshape(-1,4);ap=np.array(ao.pixels[:],dtype=np.float32).reshape(-1,4);pix[:,0]=ap[:,0];orm.pixels.foreach_set(pix.ravel());orm.update()
orm.filepath_raw=str(WORK/'ORM-master.png');orm.file_format='PNG';orm.save()
for im,name in [(base,'basecolor'),(normal,'normal'),(orm,'orm')]:
    im.scale(1024,1024);im.filepath_raw=str(UNIT/f'spearman-{name}.png');im.save()
# Restore editable pigment nodes in saved master.
for m in M.values():
    e=next(n for n in m.node_tree.nodes if n.type=='EMISSION');m.node_tree.links.new(m.node_tree.nodes[m['paint_node']].outputs[0],e.inputs[0])
low.hide_render=True;high.hide_render=True;pigment.hide_render=True;low.hide_set(True);high.hide_set(True)
for ob in objects:ob.hide_render=False;ob.hide_set(False)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'painted-master.blend'))

# Packaging can be repeated from the saved master without rebaking.
import runpy
runpy.run_path(str(UNIT/'painted_export.py'),run_name='__main__')
