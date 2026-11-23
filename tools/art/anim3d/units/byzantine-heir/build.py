"""True MPFB anatomy, closed fitted kit, folded mantle and static camera UVs."""
import bpy, math, os, json, ast
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
from math import sin, cos, pi
R=Path(os.environ['ANIM_ROOT']); A=R/'assets/byzantine-heir'; M=R/'masters/byzantine-heir'
M.mkdir(parents=True,exist_ok=True);(M/'bake-required').touch()
# Reuse the infantry lead's reviewed geometry and anatomical IK helpers.
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'mesh','bevel','solid','curve','sphere','attach','aim_bone','limb'}:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<infantry geometry>','exec'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.27,muscle=.50,weight=.43,height=.55,proportions=.55);macro['race']={'caucasian':.9,'african':.05,'asian':.05}
body=HumanService.create_human(macro_detail_dict=macro);body.name='Heir MPFB anatomy'
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();height=max(v.co.z for v in me.vertices)-min(v.co.z for v in me.vertices);ev.to_mesh_clear()
body.scale=(1.92/height,)*3;bpy.context.view_layer.objects.active=body;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='Heir MPFB game_engine';rig.location=(-.075,0,.13)
# Coordinates reproduce the painting camera without turning the human into a plane.
S=2.5;TH=.20;TARGET=1.10
def P(u,v,y=0):return Vector(((u-128)*S/256,y,TARGET+(128-v)*S/256/cos(TH)+y*math.tan(TH)))
sc=bpy.context.scene;bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='Heir painting camera';sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=S;cam.location=(0,-8*cos(TH),TARGET+8*sin(TH));cam.rotation_euler=(Vector((0,0,TARGET))-cam.location).to_track_quat('-Z','Y').to_euler()
# Match hands and stance with anatomical IK. Targets are in rig coordinates.
def target(u,v,y):return P(u,v,y)-rig.location
limb('upperarm_r','lowerarm_r',target(82,91,-.19),target(89,103,-.03));limb('upperarm_l','lowerarm_l',target(145,125,-.23),target(151,105,0))
limb('thigh_r','calf_r',target(101,215,0),target(103,183,-.10));limb('thigh_l','calf_l',target(145,218,.02),target(135,183,-.07))
aim_bone('foot_r',(-.06,-.16,-.025));aim_bone('foot_l',(.02,-.16,-.025))
aim_bone('hand_r',(0,-.025,.09));aim_bone('hand_l',(-.015,0,-.10))
# Small natural head turn; projection preserves the painted face rather than a generic face.
p=rig.pose.bones['head'];mat=p.matrix.copy();pos=mat.translation.copy();mat=Matrix.Rotation(-.15,4,'Z')@mat;mat.translation=pos;p.matrix=mat
p=rig.pose.bones['neck_01'];mat=p.matrix.copy();mat.translation.z+=.065;p.matrix=mat;bpy.context.view_layer.update()
for digit in ['index','middle','ring','pinky']:
 for k in range(1,4):
  p=rig.pose.bones[f'{digit}_{k:02d}_r'];p.rotation_mode='XYZ';p.rotation_euler.x=.85
bpy.context.view_layer.update()
def mat(name,color,metal=0,rough=.65,fill=None):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=160 if fill!='metal' else 110;noise.inputs['Detail'].default_value=3
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.19;bump.inputs['Distance'].default_value=.0012;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],s.inputs['Normal'])
 ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.04
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.20;mix.inputs[1].default_value=(*color,1);l.new(ao.outputs['Color'],mix.inputs[2])
 if fill:
  tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/f'fill-{fill}.png'),check_existing=True);tex.projection='BOX';tex.projection_blend=.3;coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],tex.inputs['Vector']);l.new(tex.outputs['Color'],mix.inputs[1])
 l.new(mix.outputs[0],s.inputs['Base Color'])
 if fill in ['purple','linen']:s.inputs['Sheen Weight'].default_value=.22
 return m
skin=mat('Painted warm skin',(.52,.32,.19),rough=.63);purple=mat('Imperial embroidered silk',(.12,.025,.09),fill='purple');linen=mat('Ivory woven tunic',(.65,.55,.38),fill='linen');gold=mat('Worn gold edges',(.70,.42,.12),1,.34);silver=mat('Silver gold lamellae',(.55,.47,.32),1,.48,fill='metal');leather=mat('Scuffed boot leather',(.055,.027,.014),fill='leather');hair=mat('Chestnut curls',(.042,.021,.012));stone=mat('Warm cream E9CFA0',(.815,.624,.352),rough=.88);ruby=mat('Garnet cabochons',(.19,.009,.025),rough=.25)
body.data.materials.clear();body.data.materials.append(skin)
# Original body already has valid deformation. Add subdivision only after projection.
# Build pixel-calibrated closed rotational garments with real front/back depth.
def shell(name,rings,material,bone='spine_03',segments=64):
 vs=[];fs=[]
 for u,v,rx,ry in rings:
  for i in range(segments):
   a=i*2*pi/segments;y=-ry*cos(a);pt=P(u+rx*sin(a),v,y);pt.z+=.004*sin(i*1.9);vs.append(tuple(pt))
 for j in range(len(rings)-1):
  for i in range(segments):a=j*segments+i;b=j*segments+(i+1)%segments;fs.append((a,b,b+segments,a+segments))
 o=solid(mesh(name,vs,[tuple(reversed(f)) for f in fs],material),.006);bevel(o,.002);attach(o,bone);return o
shell('Lamellar cuirass',[(117,66,14,.14),(117,75,18,.17),(117,88,19,.17),(117,101,16,.14)],silver)
shell('Jewel belt',[(117,99,17,.15),(117,106,17,.15)],gold)
shell('Lamellar skirt',[(117,106,17,.16),(117,124,22,.20),(117,143,26,.23)],silver,'pelvis')
shell('Ivory hem',[(117,135,25,.21),(117,154,25,.22),(117,168,26,.22)],linen,'pelvis')
# Individually rounded lamella scales provide real relief under the projected painting.
for row in range(17):
 v=70+row*4.1; rx=17 if v<104 else 17+(v-104)*.19
 for k in range(11):
  u=117+(k-5)*rx/5; depth=-.17*math.sqrt(max(.10,1-((u-117)/(rx+2))**2))-.008
  points=[P(u-1.5,v,depth),P(u+1.5,v,depth),P(u+1.4,v+2.7,depth-.003),P(u,v+3.5,depth-.005),P(u-1.4,v+2.7,depth-.003)]
  ob=mesh('Rounded lamella relief',[tuple(p) for p in points],[(4,3,2,1,0)],silver);solid(ob,.004);bevel(ob,.0015);attach(ob,'spine_03' if v<104 else 'pelvis')

# Sleeves and boots built around actual posed anatomical segment endpoints.
def tube(name,points,radii,material,bone,segments=32):
 vs=[];fs=[]
 for j,p in enumerate(points):
  p=Vector(p);direction=(Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])).normalized();q=Vector((0,0,1)).rotation_difference(direction)
  for i in range(segments):
   a=2*pi*i/segments;r=radii[j]*(1+.045*sin(a*7+j));vs.append(tuple(p+q@Vector((r*cos(a),r*sin(a),0))))
 for j in range(len(points)-1):
  for i in range(segments):a=j*segments+i;b=j*segments+(i+1)%segments;fs.append((a,b,b+segments,a+segments))
 fs+=[tuple(range(segments-1,-1,-1)),tuple((len(points)-1)*segments+i for i in range(segments))]
 o=mesh(name,vs,fs,material);bevel(o,.003);attach(o,bone);return o
for side in ['r','l']:
 for bn,radius in [('upperarm',.075),('lowerarm',.066)]:
  b=rig.pose.bones[bn+'_'+side];a=rig.matrix_world@b.head;c=rig.matrix_world@b.tail
  tube('Folded ivory sleeve '+bn+side,[a.lerp(c,t) for t in [0,.15,.35,.55,.75,1]],[radius,radius*1.1,radius,radius*1.1,radius*.85,radius*.8],linen,bn+'_'+side)
 b=rig.pose.bones['calf_'+side];a=rig.matrix_world@b.head;c=rig.matrix_world@b.tail
 tube('Tall leather boot '+side,[a.lerp(c,t) for t in [0,.2,.4,.7,1]]+[Vector((c.x,c.y-.025,.155))],[.065,.077,.069,.055,.060,.060],leather,'calf_'+side)
 # Full closed sculpted shoe, not a sprite plane.
 b=rig.pose.bones['foot_'+side];a=rig.matrix_world@b.head;c=a+Vector((-.04 if side=='r' else .02,-.10,-.035));c.z=.145;o=sphere('Leather toe '+side,c,(.075,.15,.055),leather);attach(o,'foot_'+side)
# Solid, wrapped shoulder mantle. Front is a folded surface; a separate full back drape closes the volume.
def cloth(name,left,right,material,bone,depth):
 vs=[];fs=[];nu=28;nv=40
 def interp(pts,t):
  x=t*(len(pts)-1);k=min(len(pts)-2,int(x));return Vector(pts[k]).lerp(Vector(pts[k+1]),x-k)
 for j in range(nv+1):
  t=j/nv;l=interp(left,t);r=interp(right,t)
  for i in range(nu+1):
   u=i/nu;q=l.lerp(r,u);y=depth+.035*sin(u*6*pi+t*2)*sin(pi*u)+.05*sin(t*pi);vs.append(tuple(P(q.x,q.y,y)))
 for j in range(nv):
  for i in range(nu):a=j*(nu+1)+i;fs.append((a,a+1,a+nu+2,a+nu+1))
 o=mesh(name,vs,[tuple(reversed(f)) for f in fs] if depth<0 else fs,material);solid(o,.009);su=o.modifiers.new('Tailored fold subdivision','SUBSURF');su.levels=1;attach(o,bone)
 o.shape_key_add(name='Basis');key=o.shape_key_add(name='Cloth follow through')
 for idx,v in enumerate(key.data):
  t=(idx//(nu+1))/nv;u=(idx%(nu+1))/nu;v.co.y+=.045*sin(t*pi)*sin(u*pi*3);v.co.x+=.025*t*t*sin(u*pi)
 return o
mantle=cloth('Purple shoulder mantle',[(120,54),(107,62),(118,79),(140,96),(150,112)],[(133,54),(150,63),(161,84),(167,107),(159,123)],purple,'spine_03',-.245)
back=cloth('Full mantle back',[(109,59),(90,100),(89,151),(113,188),(148,215)],[(135,58),(160,99),(165,147),(178,191),(189,218)],purple,'spine_03',.18)
train=cloth('Gathered purple train',[(146,128),(135,152),(132,174),(151,198),(164,219)],[(157,126),(168,153),(174,174),(180,196),(189,219)],purple,'pelvis',-.06)
# Shoulder clasp and belt cabochons; each bevel and rim exists in geometry.
for u,v,sz,bone in [(108,63,2.5,'spine_03')]+[(x,102,1.5,'spine_03') for x in [103,112,121,130]]:
 p=P(u,v,-.27);attach(sphere('Raised golden bezel',p,(sz*.01,.009,sz*.01),gold),bone);attach(sphere('Polished garnet',p+Vector((0,-.009,0)),(sz*.006,.006,sz*.006),ruby),bone)
# Crown follows actual head; low circlet with raised gems and tiny pearls.
head=rig.pose.bones['head'];hc=rig.matrix_world@head.head
hc=P(120,30,.015)
for j in range(64):
 a=2*pi*j/64;pt=hc+Vector((.107*sin(a),-.094*cos(a),.014*cos(a)))
 nxt=hc+Vector((.107*sin(a+2*pi/64),-.094*cos(a+2*pi/64),.014*cos(a+2*pi/64)))
 attach(curve('Gold crown circlet',[pt,nxt],.012,gold),'head')
 if j%8==0:attach(sphere('Crown cabochon',pt+Vector((0,-.005,.01)),(.014,.010,.018),ruby),'head')
attach(sphere('Sculpted hair cap',P(120,29,.05),(.118,.095,.067),hair),'head')
# Hair cap and curls follow the MPFB head; anatomical face remains exposed.
for j in range(25):
 a=2*pi*j/25;pt=P(120,35,.025)+Vector((.102*sin(a),.088*cos(a),.012+.012*sin(j*2.7)))
 attach(sphere('Sculpted chestnut curl',pt,(.025,.027,.036),hair),'head')
# Standard and cloth pennon use an independent control attached to the gripping hand.
staff=bpy.data.objects.new('Banner staff control',None);bpy.context.collection.objects.link(staff);staff.location=P(82,91,-.24);attach(staff,'hand_r')
def held(o):
 bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=staff;o.parent_type='OBJECT';bpy.context.view_layer.update();o.matrix_world=w;return o
held(curve('Purple gold staff',[P(75,23,-.24),P(88,219,-.24)],.010,leather))
for v in [28,80,105,184,216]:held(tube('Gold staff collar',[P(75+(v-23)*13/196,v-1,-.24),P(75+(v-23)*13/196,v+1,-.24)],[.014,.014],gold,'hand_r'))
held(sphere('Banner orb',P(75,23,-.24),(.027,.026,.028),gold))
held(curve('Banner cross upright',[P(75,14,-.24),P(75,21,-.24)],.007,gold));held(curve('Banner cross bar',[P(72.8,16.5,-.24),P(77.2,16.5,-.24)],.006,gold))
flag=cloth('Embroidered purple standard',[(76,32),(76,45),(77,58),(78,68)],[(79,32),(84,45),(88,58),(89,79)],purple,'hand_r',-.275);held(flag)
# Warm cream, one plain round base. Width and ellipse match painting.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.54,depth=.09,location=(-.05,0,.045));base=bpy.context.object;base.name='Stationary cream stone';base.data.materials.append(stone);bevel(base,.018,3)
# Product light: warm upper left, soft fill, cool rear separation.
sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.5,.52,.6,1);sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35
for name,loc,power,size,col in [('Warm key',(-3,-4,6),480,3,(1,.90,.75)),('Soft fill',(4,-3,3),170,4,(.89,.93,1)),('Cool rim',(1,3,4),400,3,(.75,.85,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.render.fps=24
rig['neutral_pose']=json.dumps({p.name:[list(r) for r in p.matrix_basis] for p in rig.pose.bones});rig['origin']='MPFB 2.0.18 CC0 anatomical mesh and game_engine weights'
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
# Static projected UVs, evaluated in the rest pose, with facing masks to protect unseen surfaces.
painting=bpy.data.images.load(str(A/'painting-aligned.png'),check_existing=True);records=[]
for ob in list(sc.objects):
 if ob.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
 if ob.type!='MESH' or ob==base:continue
 mods=[(m,m.show_viewport) for m in ob.modifiers]
 for m,_ in mods:
  if m.type!='ARMATURE':m.show_viewport=False
 bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(me.vertices)==len(ob.data.vertices),ob.name
 uv=ob.data.uv_layers.new(name='Rest painting');attr=ob.data.color_attributes.new(name='Projection facing',type='FLOAT_COLOR',domain='CORNER');co=[];weights=[]
 for v in me.vertices:
  pt=ev.matrix_world@v.co;q=world_to_camera_view(sc,cam,pt);co.append((q.x,q.y));normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized();weights.append(max(0,min(1,(normal.dot(Vector((0,-cos(TH),sin(TH))))+.03)/.35)))
 for loop in ob.data.loops:uv.data[loop.index].uv=co[loop.vertex_index];attr.data[loop.index].color=(weights[loop.vertex_index],)*3+(1,)
 ev.to_mesh_clear()
 for m,state in mods:m.show_viewport=state
 for i,old in enumerate(list(ob.data.materials)):
  m=old.copy();m.name=ob.name+' painted';ob.data.materials[i]=m;n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');tex=n.new('ShaderNodeTexImage');tex.image=painting;tex.extension='CLIP';tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name;l.new(tc.outputs[0],tex.inputs['Vector']);att=n.new('ShaderNodeVertexColor');att.layer_name=attr.name;mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(att.outputs[0],mul.inputs[0]);l.new(tex.outputs['Alpha'],mul.inputs[1]);mix=n.new('ShaderNodeMixRGB');oldlink=s.inputs['Base Color'].links[0].from_socket;l.new(oldlink,mix.inputs[1]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mul.outputs[0],mix.inputs[0]);l.new(mix.outputs[0],s.inputs['Base Color']);l.new(mix.outputs[0],s.inputs['Emission Color']);s.inputs['Emission Strength'].default_value=.28
 records.append({'mesh':ob.name,'vertices':len(ob.data.vertices)})
sub=body.modifiers.new('Anatomical smoothness','SUBSURF');sub.levels=1;sub.render_levels=1
(M/'projection.json').write_text(json.dumps({'method':'Rest-camera UV projection on anatomical and volumetric surfaces, incidence and alpha blend','meshes':records,'cream':'#E9CFA0'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'byzantine-heir.blend'));print('BUILD_READY',len(records))
