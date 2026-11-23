"""Project the original painting onto true skinned meshes; fill unseen surfaces.

The UVs are fixed in the bind pose and move with vertices. Never a billboard.
Projection is landmark-calibrated, with an incidence mask and image alpha.
"""
import bpy,os,ast,math,json
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/horseman-3d';A=R/'assets/horseman'
bpy.ops.wm.open_mainfile(filepath=str(M/'horseman-unpainted.blend'));sc=bpy.context.scene;hrig=bpy.data.objects['AnimalArmature'];rig=bpy.data.objects['Rider MPFB game_engine']
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'curve','mesh','solid','material'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared geometry>','exec'))
# Match the painting's raised near forehoof with a real pose from the source walk.
for a in bpy.data.actions:a.use_fake_user=True
hrig.animation_data.action=bpy.data.actions['AnimalArmature|Walk'];hrig.animation_data.action_slot=hrig.animation_data.action.slots[0];sc.frame_set(19)
raised={p.name:p.matrix_basis.copy() for p in hrig.pose.bones if p.name.endswith('.R') and p.name.split('.')[0] in ['FrontShoulder','FrontUpperLeg','FrontLowerLeg','IKFrontLeg','FF','PoleTarget']}
hrig.animation_data.action=bpy.data.actions['AnimalArmature|Idle'];hrig.animation_data.action_slot=hrig.animation_data.action.slots[0];sc.frame_set(0)
rest={p.name:p.matrix_basis.copy() for p in hrig.pose.bones};rest.update(raised);obmat=hrig.matrix_basis.copy();hrig.animation_data_clear();hrig.animation_data_create();hrig.animation_data.action=bpy.data.actions.new('Horseman painted rest')
hrig.matrix_basis=obmat
for p in hrig.pose.bones:
 p.matrix_basis=rest[p.name];p.rotation_mode='QUATERNION'
 for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=0)
hrig['raised_idle_foreleg']=json.dumps({n:[list(row) for row in v] for n,v in raised.items()});sc.frame_set(0);bpy.context.view_layer.update()
horse=bpy.data.objects['Horse']
for v in horse.data.vertices:
 neck=sum(g.weight for g in v.groups if horse.vertex_groups[g.group].name.startswith('Neck'))
 v.co.x*=1+.22*neck
 shoulder=math.exp(-((v.co.y+.026)/.006)**2-((v.co.z+.013)/.006)**2)
 if abs(v.co.x)>.001:v.co.x+=math.copysign(.00065*shoulder,v.co.x)
horse.data.update()
# Work in native 256 px camera coordinates, mapping a handful of anatomical landmarks.
# The source file is aligned to the committed token, not independently reframed.
horse_pairs=[((82,118),(94,138)),((128,137),(133,152)),((149,112),(157,115)),((174,107),(182,100)),((186,137),(189,120)),((161,184),(163,184)),((168,229),(169,220)),((87,220),(96,222)),((112,190),(121,192))]
rider_pairs=[((119,52),(126,49)),((116,81),(121,79)),((116,110),(125,101)),((113,147),(119,139)),((113,170),(124,174)),((104,91),(101,92)),((139,97),(145,108))]
def warped(x,y,pairs):
 weights=[1/(36+(x-a[0])**2+(y-a[1])**2)**1.8 for a,b in pairs];total=sum(weights)
 return (x+sum(w*(b[0]-a[0]) for w,(a,b) in zip(weights,pairs))/total,y+sum(w*(b[1]-a[1]) for w,(a,b) in zip(weights,pairs))/total)
painting=bpy.data.images.load(str(A/'painting-aligned-1024.png'),check_existing=True)
projections={k:bpy.data.images.load(str(A/f'projection-{k}.png'),check_existing=True) for k in ['coat','linen','skin']}
fills={k:bpy.data.images.load(str(A/f'fill-{k}.png'),check_existing=True) for k in ['coat','linen','bronze','hair']}
# Generated fills only supplement areas the original painting cannot describe.
for m in list(bpy.data.materials):
 if not m.use_nodes:continue
 kind='coat' if m.name.startswith('Bay') else 'linen' if m.name.startswith('Warm ivory') else 'bronze' if m.name.startswith('Bronze') else 'hair' if m.name.startswith('Black mane') else None
 if not kind:continue
 n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');tex=n.new('ShaderNodeTexImage');tex.image=fills[kind];tex.projection='BOX';tex.projection_blend=.35
 coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],tex.inputs['Vector'])
 old=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[0].default_value=.55
 if old:l.new(old,mix.inputs[1])
 else:mix.inputs[1].default_value=s.inputs['Base Color'].default_value
 l.new(tex.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
# Project only surface meshes; props retain their own physical materials.
objects=[o for o in sc.objects if o.type=='MESH' and (o.name=='Horse' or o.name.startswith(('Rider MPFB CC0','Rider linen','Split riding tunic','Rider bronze helmet','Bronze cheekguard','Ivory woven saddle')))]
records=[]
for obj in objects:
 states=[(m,m.show_viewport) for m in obj.modifiers]
 for m,state in states:
  if m.type!='ARMATURE':m.show_viewport=False
 bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 assert len(me.vertices)==len(obj.data.vertices),(obj.name,len(me.vertices),len(obj.data.vertices))
 coords=[];weights=[];view=(sc.camera.location-Vector((0,0,1.2))).normalized()
 for v in me.vertices:
  world=ev.matrix_world@v.co;q=world_to_camera_view(sc,sc.camera,world);x,y=warped(q.x*256,(1-q.y)*256,horse_pairs if obj.name=='Horse' else rider_pairs)
  coords.append((x/256,1-y/256))
  normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized();inc=max(0,min(1,(normal.dot(view)-.05)/.55))
  weights.append(inc)
 ev.to_mesh_clear()
 for mod,state in states:mod.show_viewport=state
 uv=obj.data.uv_layers.get('Painting projection') or obj.data.uv_layers.new(name='Painting projection')
 attr=obj.data.color_attributes.get('Painting incidence') or obj.data.color_attributes.new(name='Painting incidence',type='FLOAT_COLOR',domain='CORNER')
 for i,loop in enumerate(obj.data.loops):uv.data[i].uv=coords[loop.vertex_index];attr.data[i].color=(weights[loop.vertex_index],)*3+(1,)
 if len(obj.data.uv_layers)>1:obj.data.uv_layers[0].active_render=True
 # Per-object copies keep the projection repeatable and distinguish materials in audit.
 oldmats=list(obj.data.materials)
 for idx,oldmat in enumerate(oldmats):
  # Preserve native dark hair/eye/hoof regions and white markings on the horse.
  if obj.name=='Horse' and oldmat.name not in ['Bay coat','Bay shaded muscle','Bay warm highlights']:continue
  mat=oldmat.copy();mat.name=obj.name+' projected '+oldmat.name;obj.data.materials[idx]=mat
  n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF');tc=n.new('ShaderNodeUVMap');tc.uv_map='Painting projection';tex=n.new('ShaderNodeTexImage');tex.image=projections['coat'] if obj.name=='Horse' else projections['skin'] if obj.name=='Rider MPFB CC0 anatomy' else projections['linen'] if any(w in obj.name for w in ['linen','tunic','blanket']) else painting;tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs['Vector'])
  att=n.new('ShaderNodeVertexColor');att.layer_name='Painting incidence';mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(att.outputs[0],mult.inputs[0]);l.new(tex.outputs['Alpha'],mult.inputs[1])
  factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';factor.inputs[1].default_value=.82;l.new(mult.outputs[0],factor.inputs[0])
  mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';old=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
  if old:l.new(old,mix.inputs[1])
  else:mix.inputs[1].default_value=s.inputs['Base Color'].default_value
  l.new(factor.outputs[0],mix.inputs[0]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
  # Small emissive contribution retains painted recess colour under physical lighting.
  l.new(mix.outputs[0],s.inputs['Emission Color']);s.inputs['Emission Strength'].default_value=.14
 records.append({'object':obj.name,'vertices':len(obj.data.vertices),'mapping':'static projected UV with incidence/alpha blend'})
# The painting's blue border and Greek-key textile pattern on a real blanket.
blue=material('Saddle cloth indigo paint',(.025,.09,.13),0,.85);linen=bpy.data.materials['Warm ivory linen'];gold=bpy.data.materials['Bronze • polished edges'];hair=bpy.data.materials['Black mane and tail']
def attach_horse(o,bone):
 bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=hrig;o.parent_type='BONE';o.parent_bone=bone;bpy.context.view_layer.update();o.matrix_world=world
for sg in [-1,1]:
 x=sg*.372
 for z in [1.24,1.285,1.35]:
  o=curve('Blue blanket border',[(x,-.23,z),(x,.52,z)],.009,blue);attach_horse(o,'Torso')
 for j in range(10):
  y=-.22+j*.073;pts=[(x,y,1.29),(x,y,1.335),(x,y+.055,1.335),(x,y+.055,1.305),(x,y+.025,1.305),(x,y+.025,1.32)]
  attach_horse(curve('Woven Greek key',pts,.005,blue),'Torso')
 for j in range(32):
  y=-.23+j*.024;attach_horse(curve('Blanket fringe',[(x,y,1.24),(x+sg*.006,y,1.19)],.005,linen),'Torso')
# The painting's pale fan section interrupts the dark helmet crest.
for i,o in enumerate(sorted([o for o in sc.objects if o.name.startswith('Helmet dark crest fibre')],key=lambda o:o.name)):
 if 9<=i<=27:o.data.materials.clear();o.data.materials.append(linen)
# Small bronze shield slung behind the rider, visible chiefly as a shoulder rim.
verts=[];faces=[];center=Vector((.24,.17,1.22))
for ring in range(9):
 radius=.29*ring/8
 for j in range(64):
  a=j*2*math.pi/64;verts.append(tuple(center+Vector((radius*math.sin(a),.05*(1-(radius/.29)**2),radius*math.cos(a)))))
for ring in range(8):
 for j in range(64):a=ring*64+j;b=ring*64+(j+1)%64;faces.append((a,b,b+64,a+64))
shield=solid(mesh('Slung bronze riding shield',verts,faces,bpy.data.materials['Bronze • hammered']),.007)
# Authored in rider space, then attached to the moving chest without becoming a plane.
shield.matrix_world=rig.matrix_world.copy();bpy.context.view_layer.update();world=shield.matrix_world.copy();shield.parent=rig;shield.parent_type='BONE';shield.parent_bone='spine_03';bpy.context.view_layer.update();shield.matrix_world=world
# Skin tail fibres to the actual chain, so a second rigid tail cannot appear in gallop.
for o in list(sc.objects):
 if o.name.startswith('Tail flowing fibre'):bpy.data.objects.remove(o,do_unlink=True)
names=['Tail'+str(i) for i in range(1,8)];bpy.context.view_layer.update();points=[hrig.matrix_world@hrig.pose.bones[n].head for n in names]
for j in range(24):
 a=j*2*math.pi/24;offset=Vector((.065*math.sin(a),.045*math.cos(a),0));pts=[p+offset for p in points]+[points[-1]+offset+Vector((-.025,0,-.20))]
 ob=curve('Skinned tail hair',pts,.008,hair);bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH');ob=bpy.context.object
 for name in names:ob.vertex_groups.new(name=name)
 inv=hrig.matrix_world.inverted()
 for v in ob.data.vertices:
  world=v.co.copy();near=sorted(range(len(points)),key=lambda i:(world-points[i]).length)[:2];dist=[max(.001,(world-points[i]).length) for i in near];total=sum(1/d for d in dist)
  for k,d in zip(near,dist):ob.vertex_groups[names[k]].add([v.index],(1/d)/total,'REPLACE')
  # Bind-space correction: source tail is already posed; undo that deformation.
  weights=[(1/d)/total for d in dist]
  transforms=[hrig.pose.bones[names[k]].matrix@hrig.data.bones[names[k]].matrix_local.inverted() for k in near]
  deform=Matrix([[sum(w*mat[row][col] for w,mat in zip(weights,transforms)) for col in range(4)] for row in range(4)])
  v.co=deform.inverted()@(inv@world)
 ob.parent=hrig;ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=Matrix.Identity(4);ar=ob.modifiers.new('Source tail skin weights','ARMATURE');ar.object=hrig
# Shared cream target sampled from the painting's stone top: sRGB E9CFA0.
stone=bpy.data.materials['Cream limestone'];n=stone.node_tree.nodes;l=stone.node_tree.links;s=n.get('Principled BSDF')
for link in list(s.inputs['Base Color'].links):l.remove(link)
s.inputs['Base Color'].default_value=(.68,.47,.23,1);s.inputs['Roughness'].default_value=.85
sc.view_settings.look='AgX - Very High Contrast';sc.view_settings.exposure=.30
# Warmer, less front-lit studio treatment; do not flatten painted cavities.
bpy.data.objects['Cool fill'].data.energy=160;bpy.data.objects['Warm key'].data.energy=600
sc['painting_projection']='Original CC BY 4.0 painting, fixed UV on skinned geometry, landmark calibrated; generated unseen-surface fills'
(M/'projection.json').write_text(json.dumps({'meshes':records,'horse_landmarks':horse_pairs,'rider_landmarks':rider_pairs,'cream_target_srgb':'#E9CFA0','limitation':'View-specific painted lighting; landmark alignment is approximate, not pixel parity.'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'horseman.blend'))
