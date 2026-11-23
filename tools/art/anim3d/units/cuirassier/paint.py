"""Paint fixed camera UVs on real geometry, with generated hidden-side fills and real AO/curvature bakes."""
import bpy,os,json,math
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cuirassier';A=R/'assets/cuirassier'
bpy.ops.wm.open_mainfile(filepath=str(M/'cuirassier-plain.blend'));sc=bpy.context.scene;sc.frame_set(0);bpy.context.view_layer.update()
# Generated fills from the mounted lead are original project artwork (recorded source).
fills={k:bpy.data.images.load(str(A/f'fill-{k}.png')) for k in ['hair','bronze','linen']}
for mat in list(bpy.data.materials):
 if not mat.use_nodes:continue
 n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
 if not s:continue
 color=s.inputs['Base Color'].default_value[:];kind='hair' if any(k in mat.name for k in ['Bay','Black','muzzle']) else 'bronze' if any(k in mat.name for k in ['steel','gilt','Bronze','iron']) else 'linen'
 tex=n.new('ShaderNodeTexImage');tex.image=fills[kind];tex.projection='BOX';tex.projection_blend=.3;tc=n.new('ShaderNodeTexCoord');l.new(tc.outputs['Generated'],tex.inputs['Vector'])
 bw=n.new('ShaderNodeRGBToBW');l.new(tex.outputs['Color'],bw.inputs[0]);mult=n.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=.35;mult.inputs[1].default_value=color;l.new(bw.outputs[0],mult.inputs[2]);l.new(mult.outputs[0],s.inputs['Base Color'])
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=155 if kind=='linen' else 90;noise.inputs['Detail'].default_value=3
 l.new(tc.outputs['Generated'],noise.inputs['Vector']);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.002;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
 if 'steel' in mat.name or 'gilt' in mat.name:s.inputs['Metallic'].default_value=1
 if 'cloth' in mat.name:s.inputs['Sheen Weight'].default_value=.25
# Linear pigment for target warm cream #E9CFA0, with a darker rim from physical light.
mat=bpy.data.materials['Cream limestone'];s=mat.node_tree.nodes['Principled BSDF']
for link in list(s.inputs['Base Color'].links):mat.node_tree.links.remove(link)
s.inputs['Base Color'].default_value=(.815,.624,.352,1);s.inputs['Roughness'].default_value=.84
# Bake the original armour surface, disabling solidified shared-UV inside faces.
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=4;sc.render.bake.margin=4;sc.render.threads_mode='FIXED';sc.render.threads=3
out=M/'textures/baked';out.mkdir(parents=True,exist_ok=True);records=[]
for name in ['GEO-ridged steel cuirass','GEO-perforated visor']:
 obj=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 saved=[(m,m.show_render,m.show_viewport) for m in obj.modifiers if m.type=='SOLIDIFY']
 for m,_,_ in saved:m.show_render=m.show_viewport=False
 if not obj.data.uv_layers:
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.03);bpy.ops.object.mode_set(mode='OBJECT')
 mat=obj.data.materials[0].copy();obj.data.materials[0]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n['Principled BSDF'];output=n.get('Material Output');maps={}
 for mode in ['AO','curvature']:
  im=bpy.data.images.new(name+' '+mode,256,256,alpha=False);im.colorspace_settings.name='Non-Color';node=n.new('ShaderNodeTexImage');node.image=im;n.active=node
  surface=output.inputs['Surface'].links[0].from_socket
  if mode=='curvature':
   geo=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],em.inputs['Color']);l.new(em.outputs[0],output.inputs['Surface'])
  bpy.ops.object.bake(type='AO' if mode=='AO' else 'EMIT')
  if mode=='curvature':l.new(surface,output.inputs['Surface']);n.remove(em);n.remove(geo)
  im.filepath_raw=str(out/f'{name}-{mode}.png');im.file_format='PNG';im.save();maps[mode]=node
 ao=n.new('ShaderNodeMixRGB');ao.blend_type='MULTIPLY';ao.inputs[0].default_value=.55;l.new(bs.inputs['Base Color'].links[0].from_socket,ao.inputs[1]);l.new(maps['AO'].outputs[0],ao.inputs[2]);l.new(ao.outputs[0],bs.inputs['Base Color'])
 rough=n.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=.48;rough.inputs['From Max'].default_value=.54;rough.inputs['To Min'].default_value=.42;rough.inputs['To Max'].default_value=.22;l.new(maps['curvature'].outputs[0],rough.inputs[0]);l.new(rough.outputs[0],bs.inputs['Roughness'])
 for mod,a,b in saved:mod.show_render=a;mod.show_viewport=b
 records.append({'object':name,'maps':['AO','Pointiness curvature'],'size':256})
(out/'manifest.json').write_text(json.dumps(records,indent=2))
hrig=bpy.data.objects['AnimalArmature'];hair=bpy.data.materials['Black mane and tail']
import ast
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='curve':exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared curve>','exec'))
# Skin tail fibres to the actual chain, so a second rigid tail cannot appear in gallop.
for o in list(sc.objects):
 if o.name.startswith('Tail flowing fibre'):bpy.data.objects.remove(o,do_unlink=True)
names=['Tail'+str(i) for i in range(1,8)];bpy.context.view_layer.update();points=[hrig.matrix_world @ hrig.pose.bones[n].head for n in names]
for j in range(24):
 a=j*2*math.pi/24
 right=sc.camera.matrix_world.to_quaternion() @ Vector((1,0,0));up=sc.camera.matrix_world.to_quaternion() @ Vector((0,1,0));view=sc.camera.matrix_world.to_quaternion() @ Vector((0,0,1))
 targets=[(114,107),(105,119),(102,131),(96,143),(91,153),(88,165),(94,174)]
 pts=[]
 for k,(p,xy) in enumerate(zip(points,targets)):
  q=world_to_camera_view(sc,sc.camera,p);width=[.07,.10,.13,.15,.15,.12,.04][k]
  pts.append(p+right*((xy[0]/256-q.x)*sc.camera.data.ortho_scale+width*math.sin(a))+up*((1-xy[1]/256-q.y)*sc.camera.data.ortho_scale)+view*(.06*math.cos(a)))
 ob=curve('Skinned tail hair',pts,.021,hair);bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH');ob=bpy.context.object
 for name in names:ob.vertex_groups.new(name=name)
 inv=hrig.matrix_world.inverted()
 for v in ob.data.vertices:
  world=v.co.copy();near=sorted(range(len(points)),key=lambda i:(world-pts[i]).length)[:2];dist=[max(.001,(world-pts[i]).length) for i in near];total=sum(1/d for d in dist)
  for k,d in zip(near,dist):ob.vertex_groups[names[k]].add([v.index],(1/d)/total,'REPLACE')
  # Bind-space correction: source tail is already posed; undo that deformation.
  weights=[(1/d)/total for d in dist]
  transforms=[hrig.pose.bones[names[k]].matrix @ hrig.data.bones[names[k]].matrix_local.inverted() for k in near]
  deform=Matrix([[sum(w*mat[row][col] for w,mat in zip(weights,transforms)) for col in range(4)] for row in range(4)])
  v.co=deform.inverted() @ (inv @ world)
 ob.parent=hrig;ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=Matrix.Identity(4);ar=ob.modifiers.new('Source tail skin weights','ARMATURE');ar.object=hrig


import sys
sys.path.insert(0,str(Path(__file__).parent))
from refine import refine
refine(M)
bpy.ops.wm.save_as_mainfile(filepath=str(M/'cuirassier-refined-plain.blend'))
painting=bpy.data.images.load(str(A/'painting-aligned.png'));masked={k:bpy.data.images.load(str(A/f'projection-{k}.png')) for k in ['coat','steel']};view=(sc.camera.location-Vector((0,0,1.3))).normalized();records=[]
for obj in list(sc.objects):
 if obj.type!='MESH' or obj.name=='Stationary cream stone':continue
 # Evaluate only the armature, retaining exact one-to-one correspondence to base vertices.
 mods=[(m,m.show_viewport) for m in obj.modifiers]
 for m,_ in mods:
  if m.type!='ARMATURE':m.show_viewport=False
 bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(me.vertices)==len(obj.data.vertices)
 coords=[];weights=[]
 for v in me.vertices:
  q=world_to_camera_view(sc,sc.camera,ev.matrix_world @ v.co);coords.append((q.x,q.y));normal=(ev.matrix_world.to_3x3().inverted().transposed() @ v.normal).normalized();
  facing=max(0,min(1,(normal.dot(view)-.02)/.28))
  world=ev.matrix_world @ v.co
  hit,location,_,_,_,_=sc.ray_cast(bpy.context.evaluated_depsgraph_get(),world+view*8,-view)
  visible=not hit or (location-world).length<.025
  weights.append(facing if visible else 0.)
 ev.to_mesh_clear()
 for m,enabled in mods:m.show_viewport=enabled
 uv=obj.data.uv_layers.new(name='Painting projection');attr=obj.data.color_attributes.new(name='Projection incidence',type='FLOAT_COLOR',domain='CORNER')
 for i,loop in enumerate(obj.data.loops):uv.data[i].uv=coords[loop.vertex_index];attr.data[i].color=(weights[loop.vertex_index],)*3+(1,)
 if len(obj.data.uv_layers)>1:obj.data.uv_layers[0].active_render=True
 for j,old in enumerate(list(obj.data.materials)):
  if not old or not old.use_nodes:continue
  mat=old.copy();mat.name=obj.name+' painting '+old.name;obj.data.materials[j]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF')
  if not bs:continue
  tc=n.new('ShaderNodeUVMap');tc.uv_map='Painting projection';tex=n.new('ShaderNodeTexImage');tex.image=masked['coat'] if obj.name=='Horse' else painting;tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs['Vector'])
  att=n.new('ShaderNodeVertexColor');att.layer_name='Projection incidence';factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(att.outputs[0],factor.inputs[0]);l.new(tex.outputs['Alpha'],factor.inputs[1])
  # Preserve the painting's existing illumination only for camera rays.
  # Shadow/reflection rays retain the real PBR shader and generated backfill.
  strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.96;l.new(factor.outputs[0],strength.inputs[0])
  ray=n.new('ShaderNodeLightPath');gate=n.new('ShaderNodeMath');gate.operation='MULTIPLY';l.new(ray.outputs['Is Camera Ray'],gate.inputs[0]);l.new(strength.outputs[0],gate.inputs[1])
  pigment=n.new('ShaderNodeEmission');pigment.name='Frozen painted illumination';l.new(tex.outputs['Color'],pigment.inputs['Color']);pigment.inputs['Strength'].default_value=1
  output=n.get('Material Output');physical=output.inputs['Surface'].links[0].from_socket
  mix=n.new('ShaderNodeMixShader');l.new(gate.outputs[0],mix.inputs[0]);l.new(physical,mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],output.inputs['Surface'])
 records.append({'object':obj.name,'vertices':len(obj.data.vertices)})

(M/'projection.json').write_text(json.dumps(records,indent=2));bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'cuirassier.blend'))
