"""True MPFB anatomy, fitted quilted kit and fixed-camera painting UVs."""
import bpy,os,math,json,sys,random
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']); M=R/'masters/barbarian-pikeman'; A=R/'assets/barbarian-pikeman'
bpy.ops.wm.open_mainfile(filepath=str(M/'anatomy.blend'))
rig=bpy.data.objects['RIG-pikeman'];body=bpy.data.objects['GEO-MPFB-anatomy'];sc=bpy.context.scene
random.seed(17)
def mat(name,color,metal=0,rough=.65):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=145;noise.inputs['Detail'].default_value=3
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.19;bump.inputs['Distance'].default_value=.007;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
 ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.08
 mult=n.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=.4;mult.inputs[1].default_value=(*color,1);l.new(ao.outputs['Color'],mult.inputs[2]);l.new(mult.outputs[0],p.inputs['Base Color'])
 return m
skin=mat('MAT-painted-skin',(.47,.235,.105));cloth=mat('MAT-quilted-buff',(.55,.35,.15));pants=mat('MAT-worn-brown-trousers',(.18,.115,.055));leather=mat('MAT-scuffed-leather',(.18,.07,.022));steel=mat('MAT-worn-bright-steel',(.48,.43,.32),1,.36);edge=mat('MAT-polished-steel-edge',(.64,.59,.46),1,.25);red=mat('MAT-cinnabar-armtie',(.40,.018,.008));wood=mat('MAT-ash-pike',(.32,.13,.035));hair=mat('MAT-beard',(.07,.032,.013));stone=mat('MAT-cream-E9CFA0',(.815,.624,.352),0,.85)
# Generated linen fills supply brushwork on unseen cloth; source and prompt recorded in SOURCES.
n=cloth.node_tree.nodes;l=cloth.node_tree.links;p=n.get('Principled BSDF');tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/'fill-linen.png'));tc=n.new('ShaderNodeTexCoord');l.new(tc.outputs['Generated'],tex.inputs['Vector']);mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.5;mix.inputs[1].default_value=(.55,.35,.15,1);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color']);p.inputs['Sheen Weight'].default_value=.25
body.data.materials.clear();body.data.materials.append(skin)
for f in body.data.polygons:f.use_smooth=True
sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=1;sub.render_levels=1

def mesh(name,vs,fs,material,smooth=True):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new('GEO-'+name,d);sc.collection.objects.link(o);d.materials.append(material)
 for p in d.polygons:p.use_smooth=smooth
 return o

def finish(o,thick=.004,bev=.002):
 if thick:s=o.modifiers.new('Physical thickness','SOLIDIFY');s.thickness=thick
 if bev:b=o.modifiers.new('Rounded edges','BEVEL');b.width=bev;b.segments=2
 return o

def curve(name,pts,r,material):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=2;s=d.splines.new('POLY');s.points.add(len(pts)-1)
 for p,v in zip(s.points,pts):p.co=(*v,1)
 o=bpy.data.objects.new('GEO-'+name,d);sc.collection.objects.link(o);d.materials.append(material);return o

def attach(o,bone):
 bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=rig;o.parent_type='BONE';o.parent_bone=bone;bpy.context.view_layer.update();o.matrix_world=w;return o

def weighted(o,fn):
 o.parent=rig
 for v in o.data.vertices:
  for bn,w in fn(v.co).items():
   g=o.vertex_groups.get(bn) or o.vertex_groups.new(name=bn);g.add([v.index],w,'REPLACE')
 mod=o.modifiers.new('Skeleton deformation','ARMATURE');mod.object=rig
 return o
kd=KDTree(len(body.data.vertices))
for v in body.data.vertices:kd.insert(v.co,v.index)
kd.balance()
def weights(v):
 _,i,_=kd.find(v);return {body.vertex_groups[g.group].name:g.weight for g in body.data.vertices[i].groups if body.vertex_groups[g.group].name in rig.data.bones}
def shell(name,pred,material,inflation):
 # Original base topology, shape keys evaluated, no subdivision to corrupt weights.
 disabled=[]
 for md in body.modifiers:
  if md.type!='ARMATURE' and md.show_viewport:disabled.append(md);md.show_viewport=False
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 body_group=body.vertex_groups['body'].index
 real={v.index for v in body.data.vertices if any(g.group==body_group and g.weight>.5 for g in v.groups)}
 fs=[p for p in me.polygons if all(i in real and pred(me.vertices[i].co) for i in p.vertices)];ids=sorted({i for p in fs for i in p.vertices});mp={v:i for i,v in enumerate(ids)}
 vs=[me.vertices[i].co+me.vertices[i].normal*(inflation+.004*math.sin(me.vertices[i].co.z*90)) for i in ids]
 o=mesh(name,vs,[[mp[i] for i in p.vertices] for p in fs],material);ev.to_mesh_clear()
 for md in disabled:md.show_viewport=True
 weighted(o,weights);finish(o);sub=o.modifiers.new('Tailored smoothing','SUBSURF');sub.levels=1;sub.render_levels=1;return o
shell('padded-sleeves',lambda v:1.03<v.z<1.43 and abs(v.x)>.16,cloth,.026)
shell('wrinkled-trousers',lambda v:.08<v.z<.98 and abs(v.x)<.30,pants,.028)
shell('leather-boots',lambda v:v.z<.19,leather,.025)
# Fitted coat with real quilt displacement, open neckline and flared skirt.
vs=[];fs=[];N=64;J=32
for j in range(J+1):
 t=j/J;z=.70+.72*t
 rx=.29-.11*math.sin(t*math.pi*.82);ry=.155+.025*math.cos(t*math.pi*2)
 for i in range(N):
  a=2*math.pi*i/N;quilt=.004*(math.cos(a*25+z*90)+math.cos(a*25-z*90));fold=.009*math.sin(a*13+t*3)*(1-t)
  vs.append(((rx+quilt+fold)*math.sin(a),-(ry+quilt+fold)*math.cos(a),z-.05*t**10*abs(math.sin(a))))
for j in range(J):
 for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
coat=mesh('quilted-gambeson',vs,fs,cloth)
def coat_weights(v):
 if v.z<.95:return {'pelvis':1}
 if v.z>1.2:return {'spine_03':1}
 t=(v.z-.95)/.25;return {'pelvis':1-t,'spine_03':t}
weighted(coat,coat_weights);finish(coat,.009,.003)
# Waist belt, diagonal baldric, buckle and hem: real thickness, not texture silhouettes.
def ring(name,z,rx,ry,width,material,bone):
 vs=[];fs=[]
 for i in range(65):
  a=i*2*math.pi/64
  for zz in [-width/2,width/2]:vs.append((rx*math.sin(a),-ry*math.cos(a),z+zz+.10))
 for i in range(64):fs.append((2*i,2*i+1,2*i+3,2*i+2))
 return attach(finish(mesh(name,vs,fs,material),.005,.002),bone)
ring('raised-quilted-collar',1.455,.080,.085,.055,cloth,'neck_01')
ring('waist-belt',.99,.205,.19,.045,leather,'pelvis')
# Short diagonal ribbon conforms to the coat front.
vs=[]
for i in range(21):
 t=i/20;x=-.17+.34*t;z=1.01+.38*t
 for dx in [-.024,.024]:vs.append((x+dx,-.195,z+.10))
baldric=attach(finish(mesh('diagonal-leather-baldric',vs,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(20)],leather),.007,.002),'spine_03')
attach(curve('belt-buckle',[(-.04,-.205,1.065),(.04,-.205,1.065),(.04,-.205,1.12),(-.04,-.205,1.12),(-.04,-.205,1.065)],.007,edge),'pelvis')
for z in [1.08,1.18,1.28,1.37]:
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.009,location=(.0,-.195,z+.1));o=bpy.context.object;o.name='GEO-coat-button';o.data.materials.append(edge);attach(o,'spine_03')
# Kettle helmet: raised dome, wide swept brim, polished rolled edge and rivets.
hz=1.59+.10
vs=[];fs=[]
for j in range(17):
 t=j/16;angle=t*math.pi*.48
 for i in range(64):
  a=i*math.pi/32;vs.append((.122*math.sin(angle)*math.cos(a),.112*math.sin(angle)*math.sin(a)-.015,hz+.135*math.cos(angle)))
for j in range(16):
 for i in range(64):a=j*64+i;b=j*64+(i+1)%64;fs.append((a,a+64,b+64,b))
attach(finish(mesh('kettle-helmet-dome',vs,fs,steel),.008,.003),'head')
vs=[];fs=[]
for i in range(65):
 a=i*2*math.pi/64
 for r,z in [(1,hz+.008),(1.38,hz-.04)]:vs.append((.125*r*math.cos(a),.12*r*math.sin(a)-.015,z))
for i in range(64):fs.append((2*i,2*i+1,2*i+3,2*i+2))
attach(finish(mesh('kettle-helmet-brim',vs,fs,steel),.008,.003),'head')
attach(curve('helmet-rolled-rim',[(.1725*math.cos(a),.1656*math.sin(a)-.015,hz-.04) for a in [i*2*math.pi/96 for i in range(97)]],.004,edge),'head')
for i in range(18):
 a=i*2*math.pi/18;bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=6,radius=.005,location=(.122*math.cos(a),.113*math.sin(a)-.015,hz+.035));o=bpy.context.object;o.name='GEO-helmet-rivet';o.data.materials.append(edge);attach(o,'head')
# Beard strands follow anatomy, do not replace the face with a primitive.
for i in range(29):
 t=i/28;x=-.065+.13*t;y=-.10-.025*math.sin(t*math.pi);z=1.56+.10
 attach(curve('beard-strand',[(x,y,z+.03),(x*.95,y-.012,z),(x*.7,y-.006,z-.043)],.004,hair),'head')
# Red tie and hanging ends on right upper arm, built in posed space below.
# Rest pose: wide braced feet and two distinct grips on a single straight shaft.
def aim(name,direction):
 p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();q=(q@Vector((0,1,0))).rotation_difference(Vector(direction).normalized())@q;m=q.to_matrix().to_4x4();m.translation=p.head;p.matrix=m;bpy.context.view_layer.update()
def limb(up,lo,target,pole):
 a=rig.pose.bones[up].head.copy();t=Vector(target);axis=t-a;l1=rig.data.bones[up].length;l2=rig.data.bones[lo].length;d=min(axis.length,l1+l2-.0001);axis.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);h=max(0,l1*l1-along*along)**.5;side=Vector(pole)-a;side=(side-axis*side.dot(axis)).normalized();elbow=a+axis*along+side*h;aim(up,elbow-a);aim(lo,t-elbow)
rig.location=(-.17,0,.10)
p=rig.pose.bones['pelvis'];m=p.matrix.copy();m.translation.z-=.14;p.matrix=m;bpy.context.view_layer.update()
for side,x,y in [('r',-.36,-.01),('l',.35,.02)]:
 limb('thigh_'+side,'calf_'+side,(x,y,.08),((-.40 if side=='r' else .23),-.30,.48));aim('foot_'+side,((-.065 if side=='r' else .16),-.16,-.065))
limb('upperarm_r','lowerarm_r',(-.34,-.22,.72),(-.48,-.16,1.05))
limb('upperarm_l','lowerarm_l',(.165,-.24,1.085),(.14,-.18,.85))
for side in ['r','l']:
 aim('hand_'+side,(.06,-.01,.065))
 for finger in ['index','middle','ring','pinky']:
  for k in [1,2,3]:
   p=rig.pose.bones[f'{finger}_{k:02}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=1.25
p=rig.pose.bones['head'];m=p.matrix.copy();pos=p.head.copy();m=Matrix.Rotation(.65,4,'Z')@m;m.translation=pos;p.matrix=m;bpy.context.view_layer.update()
# Pike endpoints match painting in screen projection. It is a uniform 3D cylinder.
start=Vector((-1.17,-.26,.20));end=Vector((1.17,-.26,2.34))
grip=Vector((-.24,-.26,1.06))
pike=bpy.data.objects.new('CTRL-pike',None);sc.collection.objects.link(pike);pike.location=grip;bpy.context.view_layer.update()
shaft=curve('ash-pike-shaft',[start,end-(end-start).normalized()*.085],.0055,wood);shaft.parent=pike;shaft.matrix_parent_inverse=pike.matrix_world.inverted()
d=(end-start).normalized();a=end-d*.10;u=Vector((0,1,0))*.011;v=d.cross(Vector((0,1,0)))*.018
head=mesh('iron-pike-point',[a+u,a+v,a-u,a-v,end],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(3,2,1,0)],steel,False);finish(head,0,.001);head.parent=pike;head.matrix_parent_inverse=pike.matrix_world.inverted()
# Red arm tie at the visible upper sleeve, with substantial ribbon surfaces.
center=rig.matrix_world@rig.pose.bones['upperarm_r'].head;center+=Vector((-.055,-.045,-.13))
pts=[center+Vector((.077*math.cos(a),.065*math.sin(a),0)) for a in [i*2*math.pi/40 for i in range(41)]]
attach(curve('red-arm-band',pts,.016,red),'upperarm_r')
for off in [-.03,.02]:
 vs=[]
 for j in range(13):
  t=j/12
  for s in [-1,1]:vs.append(center+Vector((off+.013*s+.015*math.sin(t*8),-.08+.025*math.sin(t*5),-.23*t)))
 attach(finish(mesh('red-tie-tail',vs,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(12)],red),.004,.001),'upperarm_r')
# Stationary one-step warm cream base.
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.59,depth=.075,location=(-.14,.20,.052));base=bpy.context.object;base.name='GEO-cream-stone-base';base.data.materials.append(stone);finish(base,0,.018)
for p in base.data.polygons:p.use_smooth=abs(p.normal.z)<.5
base.modifiers['Rounded edges'].segments=5
stone.node_tree.nodes.get('Bump').inputs['Distance'].default_value=.001
stone.node_tree.nodes.get('Bump').inputs['Strength'].default_value=.08
# A camera-only cream pigment opens the stone without painted boot shadows.
n=stone.node_tree.nodes;l=stone.node_tree.links;p=n.get('Principled BSDF');out=n.get('Material Output')
g=n.new('ShaderNodeNewGeometry');xyz=n.new('ShaderNodeSeparateXYZ');l.new(g.outputs['Normal'],xyz.inputs[0])
palette=n.new('ShaderNodeMixRGB');palette.inputs[1].default_value=(.47,.285,.12,1);palette.inputs[2].default_value=(.815,.624,.352,1);l.new(xyz.outputs['Z'],palette.inputs[0])
ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.06
pigment=n.new('ShaderNodeMixRGB');pigment.blend_type='MULTIPLY';pigment.inputs[0].default_value=.45;l.new(palette.outputs[0],pigment.inputs[1]);l.new(ao.outputs['Color'],pigment.inputs[2])
em=n.new('ShaderNodeEmission');l.new(pigment.outputs[0],em.inputs['Color'])
path=n.new('ShaderNodeLightPath');fac=n.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.70;l.new(path.outputs['Is Camera Ray'],fac.inputs[0])
mix=n.new('ShaderNodeMixShader');l.new(fac.outputs[0],mix.inputs[0]);l.new(p.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
bpy.ops.object.camera_add(location=(0,-8,1.105+8*math.tan(.22)));cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(Vector((0,0,1.105))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.6;sc.camera=cam
for name,loc,power,color,size in [('key',(-3,-4,6),300,(1,.95,.85),4),('fill',(3,-2,3),60,(.90,.94,1),3),('rim',(1,3,4),95,(.85,.91,1),2)]:
 d=bpy.data.lights.new('LGT-'+name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size;o=bpy.data.objects.new(d.name,d);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
sc.world.color=(.16,.16,.16);sc.render.film_transparent=True;sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
bpy.context.view_layer.update()
# Convert original curve fittings into meshes before freezing UVs; all retain bone parenting.
for o in list(sc.objects):
 if o.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from surface import finish_surfaces
finish_surfaces()
rig['rest_basis']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})
sc['unit']='barbarian-pikeman';sc['source']='MPFB 2.0.18 CC0, original quilted kit, project painting projection'
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
from projection import project
project()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'barbarian-pikeman.blend'))
print('BUILD_OK',len(rig.data.bones),'bones')
