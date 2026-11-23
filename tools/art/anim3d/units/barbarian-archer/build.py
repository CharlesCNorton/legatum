"""Original wolf-pelt archer kit on MPFB anatomy. Not a relief or billboard."""
import sys, math, random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from math import sin,cos,pi
random.seed(711)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.48,muscle=.9,weight=.57,height=.4,proportions=.65)
body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB-anatomy'
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
zmin=min(v.co.z for v in me.vertices);zmax=max(v.co.z for v in me.vertices);ev.to_mesh_clear()
s=1.72/(zmax-zmin);body.scale=(s*1.05,s,s)
bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-barbarian-archer'
# Real eyes use MPFB's fitted system asset.
system=ROOT/'blender-user/extensions/.user/user_default/mpfb/data'
eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-MPFB-eyes'
skin=mat('Skin painted ochre',(.43,.22,.10),rough=.7)
linen=mat('Weathered flax linen',(.42,.35,.23),rough=.92)
fur=mat('Wolf pelt grey cream',(.24,.22,.18),rough=.92)
fur_light=mat('Pelt cream tips',(.50,.44,.32),rough=.92)
leather=mat('Scuffed walnut leather',(.12,.061,.025),rough=.65)
bronze=mat('Buckle brass',(.56,.32,.10),metal=1,rough=.35)
wood=mat('Yew bow',(.20,.068,.018),rough=.5)
black=mat('Dark recess',(.025,.020,.016),rough=.85)
red=mat('Oxide red wrist binding',(.28,.025,.014),rough=.8)
iron=mat('Iron arrowhead',(.28,.30,.31),metal=1,rough=.38)
stone=mat('Cream stone #E9CFA0',(.815,.624,.352),rough=.88)
body.data.materials.clear();body.data.materials.append(skin)
for f in body.data.polygons:f.use_smooth=True
# Tight garments derived from actual anatomy, with inherited deformation weights.
def shell(name,pred,m,inflate=.008):
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    fs=[p for p in me.polygons if all(pred(me.vertices[i].co) for i in p.vertices)]
    ids=sorted({i for p in fs for i in p.vertices});mp={i:j for j,i in enumerate(ids)}
    o=mesh(name,[tuple(me.vertices[i].co+me.vertices[i].normal*inflate) for i in ids],[[mp[i] for i in p.vertices] for p in fs],m)
    for g in body.vertex_groups:
        if g.name in rig.data.bones:o.vertex_groups.new(name=g.name)
    from mathutils.kdtree import KDTree
    kd=KDTree(len(body.data.vertices))
    for v in body.data.vertices:kd.insert(v.co,v.index)
    kd.balance()
    for j,i in enumerate(ids):
        _,index,_=kd.find(me.vertices[i].co)
        for g in body.data.vertices[index].groups:
            name=body.vertex_groups[g.group].name
            if name in o.vertex_groups:o.vertex_groups[name].add([j],g.weight,'REPLACE')
    ev.to_mesh_clear();o.parent=rig;ar=o.modifiers.new('MPFB garment skinning','ARMATURE');ar.object=rig
    solid(o,.005);sub=o.modifiers.new('Soft garment surface','SUBSURF');sub.levels=1;sub.render_levels=1
    return o
shell('Trousers',lambda v:.30<v.z<.94,linen,.014)
shell('Boots',lambda v:v.z<.32,leather,.009)
shell('Tunic chest',lambda v:.88<v.z<1.41 and abs(v.x)<.23,linen,.016)
sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=1;sub.render_levels=1
# Torso wrap and ragged skirt, thick cloth with modelled folds.
vs=[];fs=[];N=72;J=18
for j in range(J+1):
    t=j/J;z=1.14-.39*t
    for i in range(N):
        a=2*pi*i/N;fold=.012*sin(a*15+.6*sin(t*pi))*(.3+.7*t)
        rx=.175+.075*t+fold;ry=.128+.045*t+fold
        zz=z+.042*t**5*(sin(a*9)+.4*sin(a*17))
        vs.append((rx*sin(a),-ry*cos(a),zz))
for j in range(J):
    for i in range(N):k=j*N+i;l=j*N+(i+1)%N;fs.append((k,l,l+N,k+N))
skirt=solid(mesh('Ragged pleated skirt',vs,fs,linen),.006);attach(skirt,rig,'pelvis')
# Cloak has actual thickness, longitudinal folds and ragged tips.
vs=[];fs=[];nx=30;ny=22
for j in range(ny+1):
    t=j/ny
    for i in range(nx+1):
        u=i/nx;x=(u-.5)*(.40+.16*t);y=.10+.10*t+.028*sin(u*pi*12);z=1.40-.68*t+.045*t**4*sin(u*pi*17)
        vs.append((x,y,z))
for j in range(ny):
    for i in range(nx):k=j*(nx+1)+i;fs.append((k,k+1,k+nx+2,k+nx+1))
cloak=solid(mesh('Wolf pelt back',vs,fs,fur),.012);attach(cloak,rig,'spine_03')
# Open-faced hood: hemispherical crown and rear, no face-covering front sheet.
h=rig.pose.bones['head'];hc=(h.head+h.tail)*.5
vs=[];fs=[];na=44;nj=18
for j in range(nj+1):
    t=j/nj
    for i in range(na+1):
        a=-1.9+3.8*i/na # rear cap around positive Y, open at face
        rr=sin(.12+t*1.72)
        vs.append((hc.x+.145*rr*sin(a),hc.y+.155*rr*cos(a),hc.z+.17*cos(.12+t*1.72)))
for j in range(nj):
    for i in range(na):k=j*(na+1)+i;fs.append((k,k+1,k+na+2,k+na+1))
hood=solid(mesh('Wolf hood',vs,fs,fur),.013);attach(hood,rig,'head')
# Wolf muzzle, nose and ears sit on the hood as a recognizable trophy pelt.
attach(ellipsoid('Wolf muzzle',(hc.x+.045,hc.y-.13,hc.z+.105),(.085,.068,.043),fur_light),rig,'head')
attach(ellipsoid('Wolf nose',(hc.x+.09,hc.y-.17,hc.z+.105),(.024,.018,.018),black),rig,'head')
for sg in (-1,1):
    ear=mesh('Wolf pointed ear',[(hc.x+sg*.085,hc.y-.014,hc.z+.13),(hc.x+sg*.14,hc.y+.025,hc.z+.24),(hc.x+sg*.145,hc.y+.055,hc.z+.12),(hc.x+sg*.105,hc.y+.06,hc.z+.15)],[(0,1,2),(0,3,1),(1,3,2),(0,2,3)],fur)
    bevel(ear,.007);attach(ear,rig,'head')
# Tufts are solid tapered locks with small off-axis irregularity, never alpha cards.
def tuft(name,p,d,length,width,m,bone):
    p=Vector(p);v=Vector(d).normalized();u=v.cross(Vector((0,1,0))).normalized();w=v.cross(u)
    if u.length<.1:u=Vector((1,0,0));w=v.cross(u)
    verts=[tuple(p+u*width),tuple(p+w*width*.5),tuple(p-u*width),tuple(p-w*width*.5),tuple(p+v*length)]
    o=mesh(name,verts,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,3,2,1)],m);attach(o,rig,bone)
for side in (-1,1):
    for i in range(65):
        t=i/64;x=side*(.13+.095*t);z=hc.z+.11-.49*t;y=hc.y-.205-.035*sin(t*pi)
        tuft('Mantle fur lock',(x+random.uniform(-.022,.022),y,z),(.2*side,-.1,-1),random.uniform(.035,.075),.012,fur_light if i%3 else fur,'head' if t<.22 else 'spine_03')
    for i in range(24):
        a=i*pi/23
        tuft('Hood fur lock',(hc.x+side*.14*sin(a),hc.y-.06,hc.z+.16*cos(a)),(side*.3,-.1,-1),.05,.012,fur_light,'head')
# Broad shoulder-to-waist fur lappets sit in front of the tunic.
for sg in (-1,1):
    vs=[];fs=[]
    for j in range(23):
        t=j/22
        for i in range(7):
            u=i/6; x=sg*(.075+.10*t+u*.115)
            y=-.176-.026*sin(u*pi*3)-.018*sin(t*pi)
            z=1.43-.43*t+.017*t**5*sin(u*pi*7)
            vs.append((x,y,z))
    for j in range(22):
        for i in range(6):k=j*7+i;fs.append((k,k+1,k+8,k+7))
    attach(solid(mesh('Front wolf mantle',vs,fs,fur),.012),rig,'spine_03')
    for j in range(60):
        t=random.random();u=random.random()
        tuft('Mantle surface lock',(sg*(.075+.10*t+u*.115),-.215-.024*sin(u*pi*3),1.43-.43*t),(.25*sg,-.1,-1),random.uniform(.028,.06),.008,fur_light,'spine_03')
# Beard locks around the real MPFB chin, not replacement facial anatomy.
for i in range(28):
    x=hc.x+random.uniform(-.055,.055);z=hc.z-.07+random.uniform(-.03,.02)
    tuft('Beard',(x,hc.y-.104,z),(.12,-.07,-1),random.uniform(.04,.07),.008,fur,'head')
# Thick crossbelts follow the front torso, with rolled edges and real metal buckle.
def ribbon(name,pts,width,m,bone):
    verts=[]
    for x,y,z in pts:verts.extend([(x-width/2,y,z),(x+width/2,y,z)])
    fs=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(pts)-1)]
    o=bevel(solid(mesh(name,verts,fs,m),.008),.002);attach(o,rig,bone)
    for sign in (-1,1):attach(curve(name+' stitch',[(x+sign*width*.39,y-.005,z) for x,y,z in pts],.0013,fur_light),rig,bone)
for sg in (-1,1):
    pts=[(sg*(-.145+.285*i/20),-.157-.018*sin(i*pi/20),1.38-.26*i/20) for i in range(21)]
    ribbon('Crossbelt',pts,.038,leather,'spine_03')
for z in (1.085,1.118):attach(curve('Waist belt',[(.183*sin(a),-.144*cos(a),z) for a in [i*2*pi/80 for i in range(81)]],.015,leather),rig,'pelvis')
for x,y,z in [(-.04,-.188,1.18),(.025,-.164,1.105)]:
    attach(curve('Brass ring buckle',[(x+.023*cos(a),y,z+.024*sin(a)) for a in [i*2*pi/40 for i in range(41)]],.004,bronze),rig,'spine_02' if z>1.1 else 'pelvis')
# Boot lacing around the rest calves; attachment rotates with them.
for side,sg in [('r',-1),('l',1)]:
    c=rig.pose.bones['calf_'+side];x=c.tail.x
    for j in range(6):
        z=.10+j*.039;rad=.05+.012*j/5
        pts=[(x+rad*cos(a),-.005+rad*sin(a),z+.024*a/(2*pi)) for a in [i*2*pi/32 for i in range(33)]]
        attach(curve('Boot wrapped thong',pts,.006,linen if j%3==0 else leather),rig,'calf_'+side)
# Bracer derived from MPFB forearm so it bends with the arm.
shell('Leather bow bracer',lambda v:v.x>.37 and 1.01<v.z<1.28,leather,.012)
# Hip quiver with bound rims, shafts and ivory feathers.
q=Vector((.25,.02,.87));top=q+Vector((.08,0,.29))
attach(curve('Hip quiver',[q,top],.057,leather),rig,'pelvis')
for t in (0,.04,.23,.27):
    c=q+Vector((.08*t/.29,0,t))
    attach(curve('Quiver bound rim',[tuple(c+Vector((.06*cos(a),.06*sin(a),0))) for a in [i*2*pi/40 for i in range(41)]],.006,bronze if t==.23 else leather),rig,'pelvis')
for i in range(8):
    a=i*2*pi/8;p=top+Vector((.035*cos(a),.035*sin(a),-.07));end=p+Vector((.045,0,.24+random.random()*.04))
    attach(curve('Spare arrow',[p,end],.003,wood),rig,'pelvis')
    attach(solid(mesh('Spare arrow feather',[end+Vector((-.018,0,-.08)),end+Vector((0,0,-.11)),end+Vector((.018,0,-.02)),end],[(0,1,2,3)],linen),.002),rig,'pelvis')
# Bind rest pose before weapon geometry is fitted to the hands.
pose(rig)
bpy.context.view_layer.update()
# Blood-red cloth accent wrapped around the actual drawing wrist.
wrist=rig.matrix_world@rig.pose.bones['hand_r'].head
axis=(rig.pose.bones['lowerarm_r'].tail-rig.pose.bones['lowerarm_r'].head).normalized()
u=axis.cross(Vector((0,0,1))).normalized();v=axis.cross(u)
for j in range(5):
    center=wrist-axis*(.015+j*.008)
    pts=[tuple(center+.036*(u*cos(a)+v*sin(a))) for a in [i*2*pi/32 for i in range(33)]]
    attach(curve('Red wrist cloth wrap',pts,.006,red),rig,'lowerarm_r')
attach(solid(mesh('Red ragged wrist tail',[wrist+Vector((-.01,-.04,0)),wrist+Vector((.02,-.04,0)),wrist+Vector((-.025,-.03,-.12)),wrist+Vector((-.04,-.025,-.10))],[(0,1,2,3)],red),.004),rig,'lowerarm_r')
grip=rig.matrix_world@rig.pose.bones['hand_l'].head+Vector((.015,-.015,.04))
# Drawn asymmetric stave, shape-key animation relaxes the ends on release.
pts=[]
for i in range(65):
    t=-1+2*i/64
    x=-.27*abs(t)**2-.12*t*abs(t)+.045*sin(t*pi)
    pts.append(tuple(grip+Vector((x,0,.57*t))))
bow=curve('Bow stave',pts,.012,wood);attach(bow,rig,'hand_l')
bow['tips_world']=json.dumps([pts[0],pts[-1]])
for j in range(11):
    c=grip+Vector((0,0,-.058+j*.011))
    attach(curve('Bow grip wrap',[tuple(c+Vector((.017*cos(a),.017*sin(a),0))) for a in [i*2*pi/24 for i in range(25)]],.003,linen),rig,'hand_l')
nock=rig.matrix_world@rig.pose.bones['hand_r'].tail+Vector((.02,-.015,.012))
string=curve('Bowstring',[pts[0],tuple(nock),pts[-1]],.0022,linen)
arrow=curve('Nocked arrow',[tuple(nock),tuple(grip+Vector((.13,0,.035)))],.0035,wood)
# Dynamic string/arrow curves are keyed by animate.py; no zero-scale hiding.
arrowhead=mesh('Arrowhead',[(0,0,0),(-.055,-.012,-.012),(-.055,.012,-.012),(-.055,0,.013)],[(0,1,2),(0,2,3),(0,3,1),(1,3,2)],iron);bevel(arrowhead,.001)
arrowhead.location=grip+Vector((.15,0,.035))
# One warm cream stationary base.
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.53,depth=.075,location=(0,0,.0375));base=bpy.context.object;base.name='GEO-Stationary cream base';base.data.materials.append(stone);bevel(base,.012)
sc=settings();bpy.ops.object.camera_add(location=(.02,-8,3.15));sc.camera=bpy.context.object;sc.camera.name='CAM-painting'
target=Vector((.06,0,.91));sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=2.22
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.30,.32,.36,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.32
for name,loc,power,size,col in [('key',(-3,-4,5),650,2,(1,.88,.71)),('fill',(3,-3,3),170,3,(.83,.90,1)),('rim',(1,2,4),380,2,(.78,.87,1))]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power;o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
# Pack all external eyes maps, keep editable model and plain review master.
rig['rest_pose']=json.dumps({p.name:[list(r) for r in p.matrix_basis] for p in rig.pose.bones})
sc['origin']='MPFB CC0 anatomy, original solid wolf-pelt kit and bow; no subject cards'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'plain.blend'))
(MASTER/'model-info.json').write_text(json.dumps({'body_vertices':len(body.data.vertices),'bones':len(rig.data.bones),'objects':len(sc.objects),'blender':bpy.app.version_string},indent=2))
log('Built MPFB anatomy, weighted trousers/boots, thick folded tunic, wolf pelt and ears, beard, crossbelts, buckles, quiver and articulated bow. Six Blender skills applied.')
