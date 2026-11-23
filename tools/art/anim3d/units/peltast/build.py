"""Build peltast true-3D anatomy, tailored kit, painted stance and editable rig."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import random
random.seed(19)
bpy.ops.wm.open_mainfile(filepath=str(M/'anatomy.blend'))
sc=bpy.context.scene;rig=bpy.data.objects['RIG-Peltast'];body=bpy.data.objects['GEO-MPFB peltast anatomy']
skin=material('Skin painted ochre',(.52,.255,.095),rough=.73);red=material('Vermilion linen',(.48,.035,.018),fill='red');blue=material('Indigo wool',(.022,.045,.115),fill='blue');leather=material('Worn chestnut leather',(.085,.028,.011),fill='leather');wicker=material('Woven chestnut reed',(.23,.095,.029),fill='wicker');gold=material('Bright bronze clasp',(.72,.40,.095),metal=1,rough=.33);iron=material('Forged iron',(.35,.38,.40),metal=1,rough=.35);wood=material('Oiled ash',(.18,.065,.015),rough=.66);cream=material('Rawhide pale binding',(.65,.46,.23),rough=.8);fur=material('Russet fox fur',(.20,.072,.021),rough=.9);dark=material('Beard and hair',(.035,.026,.018),rough=.87);stone=material('Cream limestone E9CFA0',tuple(linear(c/255) for c in (233,207,160)),rough=.88)
body.data.materials.clear();body.data.materials.append(skin)
# Pose anatomy using fixed landmarks in the original painting. Depth is real,
# preserving the full MPFB mesh and its original skinning weights.
lines={'pelvis':((112,124,0),(112,114,0)),'spine_01':((112,114,0),(112,106,0)),'spine_02':((112,106,0),(112,98,0)),'spine_03':((112,98,0),(112,82,0)),
'clavicle_r':((109,65,0),(88,68,-.015)),'upperarm_r':((88,68,-.015),(63,75,-.035)),'lowerarm_r':((63,75,-.035),(66,47,-.075)),'hand_r':((66,47,-.075),(67,43,-.075)),
'clavicle_l':((113,65,0),(136,69,.015)),'upperarm_l':((136,69,.015),(153,84,-.02)),'lowerarm_l':((153,84,-.02),(174,87,-.075)),'hand_l':((174,87,-.075),(177,87,-.075)),
'neck_01':((111,62,0),(111,52,0)),'head':((111,52,0),(111,33,0)),
 'thigh_r':((101,129,0),(78,162,-.01)),'calf_r':((78,162,-.01),(52,202,-.04)),'foot_r':((52,202,-.04),(50,210,-.105)),
 'thigh_l':((125,129,0),(151,160,.02)),'calf_l':((151,160,.02),(160,199,.03)),'foot_l':((160,199,.03),(172,207,-.015))}
for name,(a,b) in lines.items():bone_line(rig,name,P(*a),P(*b))
p=rig.pose.bones['head'];p.matrix=Matrix.Translation(p.head)@Matrix.Rotation(1.05,4,'Z')@Matrix.Translation(-p.head)@p.matrix;bpy.context.view_layer.update()
for side in ['l','r']:
 for digit in ['index','middle','ring','pinky']:
  for j in [1,2,3]:
   p=rig.pose.bones[f'{digit}_0{j}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.82 if j==1 else 1.15
 for j in [1,2,3]:
  p=rig.pose.bones[f'thumb_0{j}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.y=.30
bpy.context.view_layer.update()
# Shell from the actual deformed anatomy, retaining nearest native skin weights.
def body_shell(name,predicate,mat,inflate):
 states=[(m,m.show_viewport) for m in body.modifiers if m.type!='ARMATURE']
 for m,_ in states:m.show_viewport=False
 # predicates use original anatomical space, independent of the new pose
 oldmods=[(m,m.show_viewport) for m in body.modifiers if m.type=='ARMATURE']
 for m,_ in oldmods:m.show_viewport=False
 bpy.context.view_layer.update();rest=body.evaluated_get(bpy.context.evaluated_depsgraph_get());re=rest.to_mesh();skin_group=body.vertex_groups['body'].index;keep={v.index for v in re.vertices if predicate(v.co) and any(g.group==skin_group and g.weight>.5 for g in body.data.vertices[v.index].groups)};rest.to_mesh_clear()
 for m,v in oldmods:m.show_viewport=v
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 ids=sorted({i for poly in me.polygons if all(i in keep for i in poly.vertices) for i in poly.vertices});mapping={i:j for j,i in enumerate(ids)}
 vs=[tuple(ev.matrix_world@(me.vertices[i].co+me.vertices[i].normal*inflate)) for i in ids];faces=[[mapping[i] for i in poly.vertices] for poly in me.polygons if all(i in mapping for i in poly.vertices)]
 ob=mesh(name,vs,faces,mat);ww=[]
 for i in ids:
  weights={body.vertex_groups[g.group].name:g.weight for g in body.data.vertices[i].groups if body.vertex_groups[g.group].name in rig.data.bones};total=sum(weights.values());ww.append({n:w/total for n,w in weights.items()})
 ev.to_mesh_clear()
 for m,v in states:m.show_viewport=v
 bind_posed(ob,rig,ww);solid(ob,.007);bevel(ob,.003);return ob
for side,sign in [('l',1),('r',-1)]:body_shell('Laced ankle boot '+side,lambda v,s=sign:v.z<.28 and v.x*s>.04,leather,.009)
body_shell('Short sculpted beard',lambda v:1.69<v.z<1.77 and v.y<-.065,dark,.004)
# Real laces and cuffs follow their anatomical foot, not the stationary base.
for side,px,py in [('r',52,202),('l',160,199)]:
 pts=[P(px+dx,py+dy,-.115) for dx,dy in [(-4,-10),(3,-8),(-4,-5),(3,-2),(-4,1),(3,4)]]
 attach(curve('Boot cross laces '+side,pts,.0045,cream),rig,'foot_'+side)
# Gathered linen: a closed 3D tube with sculpted fold channels, shoulder-to-waist.
verts=[];faces=[];weights=[];N=64;K=24
for j in range(K+1):
 t=j/K;py=65+47*t;cx=112-2*sin(t*pi);rx=17+6*sin(t*pi*.8);ry=.21+.025*sin(t*pi)
 for i in range(N):
  a=2*pi*i/N;fold=(.012*sin(a*12+t*2)+.005*sin(a*23-t*5))*sin(pi*t*.8)
  x=cx+(rx+fold*108)*sin(a);depth=-(ry+fold)*cos(a);y=py+3*sin(a)**2*(1-t)**3
  verts.append(P(x,y,depth));w=min(1,max(0,(t-.6)/.4));weights.append({'spine_03':1-w,'spine_01':w})
for j in range(K):
 for i in range(N):a=j*N+i;b=j*N+(i+1)%N;faces.append((a,a+N,b+N,b))
tunic=mesh('Folded red chiton',verts,faces,red);bind_posed(tunic,rig,weights);solid(tunic,.005);su=tunic.modifiers.new('Linen soft folds','SUBSURF');su.levels=1
# Skirt has actual pleats and weight blending into each hip.
verts=[];faces=[];weights=[];K=22
for j in range(K+1):
 t=j/K;py=108+32*t;rx=17+18*t;ry=.135+.085*t
 for i in range(N):
  a=2*pi*i/N;fold=.010*sin(14*a+2*t)+.006*sin(25*a-t);x=112+(rx+fold*109)*sin(a);depth=-(ry+fold)*cos(a);y=py+2.1*t*sin(14*a)+2*t*cos(a)
  verts.append(P(x,y,depth));w=.25*t;weights.append({'pelvis':1-w,'thigh_l' if sin(a)>0 else 'thigh_r':w})
for j in range(K):
 for i in range(N):a=j*N+i;b=j*N+(i+1)%N;faces.append((a,a+N,b+N,b))
skirt=mesh('Pleated linen skirt',verts,faces,red);bind_posed(skirt,rig,weights);solid(skirt,.005);s=skirt.modifiers.new('Hem smoothness','SUBSURF');s.levels=1
# Leather waist tie and metal buckle, both physically raised.
attach(curve('Waist tie',[P(112+18*sin(a),109,.145*-cos(a)) for a in [i*2*pi/96 for i in range(97)]],.008,leather),rig,'spine_01')
attach(curve('Belt buckle',[P(x,y,-.154) for x,y in [(108,107),(113,107),(113,110),(108,110),(108,107)]],.0035,gold),rig,'spine_01')
# Broad cloak behind the throwing side, with cloth volume and delayed flutter keys.
verts=[];faces=[];nx=30;ny=36
for j in range(ny+1):
 t=j/ny;left=96-65*t;right=130-49*t;width=right-left
 for i in range(nx+1):
  u=i/nx;px=left+width*u;py=67+91*t+5*t*sin(u*pi*5);depth=.13+.055*sin(u*pi*5+1.8*t)+.025*sin(u*pi*11-3*t)+.06*t
  verts.append(P(px,py,depth))
for j in range(ny):
 for i in range(nx):a=j*(nx+1)+i;faces.append((a,a+nx+1,a+nx+2,a+1))
cloak=mesh('Blue wind folded cloak',verts,faces,blue);bind_posed(cloak,rig,[{'spine_03':1} for v in verts]);solid(cloak,.006);su=cloak.modifiers.new('Wool smoothness','SUBSURF');su.levels=1
cloak.shape_key_add(name='Basis');key=cloak.shape_key_add(name='Trailing breeze')
for j in range(ny+1):
 t=j/ny
 for i in range(nx+1):
  v=key.data[j*(nx+1)+i];v.co.y+=.08*t*t*sin(i/nx*2*pi+2*t);v.co.x-=.045*t*t
for k in range(4):
 pts=[P(90+51*u,62+9*sin(pi*u)+k*2,-.15-.018*k) for u in [i/40 for i in range(41)]]
 attach(curve('Wool collar fold',pts,.018,blue),rig,'spine_03')
attach(sphere('Bronze shoulder brooch',P(99,65,-.20),(.027,.009,.027),gold),rig,'spine_03')
# Fox-skin cap: sculpted ellipsoid shell with muzzle, ears and textured fur strands.
verts=[];faces=[]
for j in range(15):
 t=j/14*pi/2
 for i in range(64):
  a=i*2*pi/64;px=107+13*cos(t)*sin(a)+5*sin(t);py=30-9*sin(t);depth=.008-.12*cos(t)*cos(a)
  verts.append(P(px,py,depth))
for j in range(14):
 for i in range(64):a=j*64+i;b=j*64+(i+1)%64;faces.append((a,b,b+64,a+64))
cap=solid(mesh('Fox skin cap crown',verts,faces,fur),.008);attach(cap,rig,'head')
# The fox muzzle lies forward across the wearer's brow; this is hide, not a helmet.
attach(sphere('Fox cap muzzle',P(119,29,-.065),(.105,.08,.038),fur),rig,'head')
attach(sphere('Fox dark nose',P(128,29,-.065),(.025,.030,.018),dark),rig,'head')
for coords in [[(98,25),(97,14),(106,22)],[(108,23),(112,17),(115,26)]]:
 ob=solid(mesh('Fox pointed ear',[P(x,y,-.08) for x,y in coords],[(0,1,2)],fur),.016);bevel(ob,.002);attach(ob,rig,'head')
for j in range(75):
 x=random.uniform(95,120);y=random.uniform(23,32);d=-.1+random.uniform(-.025,.02)
 attach(curve('Fox fur strand',[P(x,y,d),P(x-1,y+2,d-.008),P(x-3,y+4,d+.002)],.0022,cream if j%5==0 else fur),rig,'head')
pts=[P(97,29,.10),P(91,45,.13),P(89,60,.17),P(86,70,.20)]
attach(curve('Fox hide nape flap',pts,.045,fur),rig,'head')
# Crescent pelta: dished wicker mesh with a true missing upper crescent.
# Boundary uses a lower ellipse and a concave upper arc between its two horns.
points=[(187,39),(199,55),(205,77),(205,99),(196,120),(180,128),(163,117),(153,96),(151,64),(159,71),(170,70),(180,60)]
outline=[]
for j in range(len(points)):
 p0=Vector(points[(j-1)%len(points)]);p1=Vector(points[j]);p2=Vector(points[(j+1)%len(points)]);p3=Vector(points[(j+2)%len(points)])
 for k in range(8):
  t=k/8;v=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t);outline.append(tuple(v))
center=(177,91);verts=[];faces=[];ns=len(outline);nr=14
for j in range(nr+1):
 r=j/nr
 for x,y in outline:
  px=center[0]+(x-center[0])*r;py=center[1]+(y-center[1])*r;depth=.045-.045*(1-r*r)
  verts.append(P(px,py,depth))
for j in range(nr):
 for i in range(ns):a=j*ns+i;b=j*ns+(i+1)%ns;faces.append((a,b,b+ns,a+ns))
shield=solid(mesh('Dished wicker crescent pelta',verts,faces,wicker),.019);bevel(shield,.002)
control=bpy.data.objects.new('CTRL-Pelta',None);bpy.context.collection.objects.link(control);control.location=P(176,90,0);attach(control,rig,'hand_l')
def parent_shield(o):
 bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=control;o.matrix_parent_inverse=control.matrix_world.inverted();o.matrix_basis=world;return o
parent_shield(shield)
for i in range(ns):
 a=outline[i];b=outline[(i+1)%ns];parent_shield(curve('Pelta rawhide rim',[P(*a,.024),P(*b,.024)],.014,cream if i//6%2==0 else leather))
# Raised wicker splints follow the curved surface; projection supplies fine weave.
for j in range(4,14):
 rr=j/14;pts=[P(center[0]+(x-center[0])*rr,center[1]+(y-center[1])*rr,-.007-.04*(1-rr*rr)) for x,y in outline]
 parent_shield(curve('Pelta reed ring',pts+[pts[0]],.0025,wood))
parent_shield(curve('Pelta hand grip',[P(176,81,-.13),P(176,99,-.13)],.016,leather))
# Three true javelins: one held above shoulder, two carried behind the shield.
def javelin(name,start,end,parent=None,bone=None):
 start,end=Vector(start),Vector(end);v=(end-start).normalized();h=end-v*.13
 objs=[curve(name+' ash shaft',[start,h],.006,wood)]
 side=Vector((-v.z,0,v.x))*.019;thick=Vector((0,.005,0));mid=h+v*.035
 vs=[h,mid+side,mid+thick,mid-side,mid-thick,end];fs=[(0,1,2),(0,2,3),(0,3,4),(0,4,1),(1,5,2),(2,5,3),(3,5,4),(4,5,1)]
 objs.append(bevel(mesh(name+' iron leaf head',vs,fs,iron),.001))
 if parent:
  for o in objs:
   bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted();o.matrix_basis=world
 elif bone:
  for o in objs:attach(o,rig,bone)
 return objs
weapon=bpy.data.objects.new('CTRL-Throwing javelin',None);bpy.context.collection.objects.link(weapon);weapon.location=P(68,42,-.11);attach(weapon,rig,'hand_r')
javelin('Throwing javelin',P(16,44,-.11),P(220,23,-.11),parent=weapon)
for dy in [0,7]:javelin('Reserve javelin',P(66,95+dy,.09),P(240,79+dy,.09),parent=control)
# Single cream stone disc, no extra tier.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.86,depth=.12,location=(-.11,0,.17));base=bpy.context.object;base.name='GEO-Stationary cream base';base.data.materials.append(stone);bevel(base,.014)
# Anatomical subdivision after skinning. All surfaces retain real side/back geometry.
sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=1;sub.render_levels=1
for p in body.data.polygons:p.use_smooth=True
bpy.ops.object.camera_add();sc.camera=bpy.context.object;sc.camera.name='CAM-Painting';sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=SCALE;sc.camera.location=TARGET+Vector((0,-8*cos(ELEV),8*sin(ELEV)));aim(sc.camera,TARGET)
for name,loc,power,size,col in [('Warm upper-left key',(-3,-4,6),650,3,(1,.91,.76)),('Soft fill',(4,-3,3),140,4,(.85,.91,1)),('Cool rim',(2,3,5),350,2.5,(.72,.83,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power;o.data.size=size;o.data.color=col;aim(o,(0,0,1))
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.36,.45,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.3
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.cycles.max_bounces=5
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.fps=24
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.2
rig['rest_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones});rig['source']='MPFB 2.0.18 CC0 body and 53-bone game_engine rig'
sc['unit']='peltast';sc['geometry']='Full MPFB anatomy, thick 3D clothing, convex wicker pelta, three javelins, no cards';sc['cream_target']='#E9CFA0'
(M/'model-info.json').write_text(json.dumps({'body_vertices':len(body.data.vertices),'bones':len(rig.data.bones),'objects':len(sc.objects),'landmarks':lines},indent=2))
save('peltast-unpainted.blend');log('- Built MPFB anatomy, painted rest stance, red chiton, blue cloak, fox-skin cap, woven crescent pelta and three iron-tipped javelins; plain review pending.')
