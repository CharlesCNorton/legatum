"""Painted-fill PBR, true AO/curvature bakes, then frozen rest-camera projection."""
import bpy,os,sys,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/composite-archer';A=R/'assets/composite-archer'
bpy.ops.wm.open_mainfile(filepath=str(M/'registered.blend'));sc=bpy.context.scene
# Original fill textures on unseen surfaces, supplemented by physical surface grain.
fills={k:bpy.data.images.load(str(A/f'fill-{k}.png')) for k in ['red','trousers','leather','gold']}
for mat in list(bpy.data.materials):
 if not mat.use_nodes:continue
 n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
 if not s:continue
 kind='red' if 'wool' in mat.name else 'trousers' if 'trousers' in mat.name else 'leather' if 'leather' in mat.name else 'gold' if 'gilding' in mat.name else None
 texcoord=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=170;noise.inputs['Detail'].default_value=3;l.new(texcoord.outputs['Generated'],noise.inputs['Vector'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.0016;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
 if kind:
  tex=n.new('ShaderNodeTexImage');tex.image=fills[kind];tex.projection='BOX';tex.projection_blend=.35;l.new(texcoord.outputs['Generated'],tex.inputs['Vector']);l.new(tex.outputs['Color'],s.inputs['Base Color'])
 if kind in ('red','trousers'):s.inputs['Sheen Weight'].default_value=.25
 if 'limestone' in mat.name:
  s.inputs['Base Color'].default_value=(.82,.61,.32,1)
  # Calibrated cream pigment, with live physical contact shadows retained.
  out=n.get('Material Output');geo=n.new('ShaderNodeNewGeometry');separate=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Normal'],separate.inputs[0])
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.92,.65,.32,1);ramp.color_ramp.elements[1].color=(.93,.78,.50,1);l.new(separate.outputs['Z'],ramp.inputs[0])
  pigment=n.new('ShaderNodeEmission');l.new(ramp.outputs['Color'],pigment.inputs['Color'])
  rays=n.new('ShaderNodeLightPath');factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';factor.inputs[1].default_value=.65;l.new(rays.outputs['Is Camera Ray'],factor.inputs[0])
  shader=n.new('ShaderNodeMixShader');l.new(factor.outputs[0],shader.inputs[0]);l.new(s.outputs[0],shader.inputs[1]);l.new(pigment.outputs[0],shader.inputs[2]);l.new(shader.outputs[0],out.inputs['Surface'])
 if 'skin' in mat.name:s.inputs['Subsurface Weight'].default_value=.06
 if 'skin' in mat.name or 'beard' in mat.name:
  # Painted fill for the face revealed when the drawing hand leaves the cheek.
  # Live AO retains recesses without turning the unprojected jaw into a dark block.
  out=n.get('Material Output');ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.09
  ao.inputs['Color'].default_value=(.48,.245,.105,1) if 'skin' in mat.name else (.085,.040,.018,1)
  pigment=n.new('ShaderNodeEmission');l.new(ao.outputs['Color'],pigment.inputs['Color'])
  rays=n.new('ShaderNodeLightPath');factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';factor.inputs[1].default_value=.65;l.new(rays.outputs['Is Camera Ray'],factor.inputs[0])
  shader=n.new('ShaderNodeMixShader');l.new(factor.outputs[0],shader.inputs[0]);l.new(s.outputs[0],shader.inputs[1]);l.new(pigment.outputs[0],shader.inputs[2]);l.new(shader.outputs[0],out.inputs['Surface'])
# Actual small UV bakes, with inner Solidify faces excluded to prevent UV contamination.
textures=M/'textures';textures.mkdir(exist_ok=True)
bakes=[]
for name in ['GEO-tunic fitted chest','GEO-patterned trousers','GEO-red embroidered felt cap','GEO-ornamented leather quiver']:
 o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT');o.data.uv_layers.active.name='Surface bake'
 states=[(m,m.show_render,m.show_viewport) for m in o.modifiers if m.type=='SOLIDIFY']
 for mod,_,_ in states:mod.show_render=False;mod.show_viewport=False
 # Unique materials isolate the bake target and preserve generated fills.
 o.data.materials[0]=o.data.materials[0].copy();mat=o.data.materials[0];n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF');out=n.get('Material Output');old=out.inputs['Surface'].links[0].from_socket
 maps={}
 for kind in ['ao','curvature']:
  im=bpy.data.images.new(name+' '+kind,width=256,height=256,alpha=False);im.colorspace_settings.name='Non-Color'
  target=n.new('ShaderNodeTexImage');target.image=im;n.active=target
  if kind=='curvature':
   geo=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],em.inputs['Color']);l.new(em.outputs[0],out.inputs['Surface'])
  sc.cycles.samples=4;sc.render.bake.margin=3;bpy.ops.object.bake(type='AO' if kind=='ao' else 'EMIT')
  l.new(old,out.inputs['Surface']);im.filepath_raw=str(textures/(name.replace('GEO-','')+'-'+kind+'.png'));im.file_format='PNG';im.save();im.pack();maps[kind]=target
  if kind=='curvature':n.remove(em);n.remove(geo)
 for mod,sr,sv in states:mod.show_render=sr;mod.show_viewport=sv
 uv=n.new('ShaderNodeUVMap');uv.uv_map='Surface bake'
 for t in maps.values():l.new(uv.outputs[0],t.inputs['Vector'])
 base=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
 mult=n.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=.25
 if base:l.new(base,mult.inputs[1])
 else:mult.inputs[1].default_value=s.inputs['Base Color'].default_value
 l.new(maps['ao'].outputs['Color'],mult.inputs[2]);l.new(mult.outputs[0],s.inputs['Base Color'])
 rough=n.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=.35;rough.inputs['From Max'].default_value=.65;rough.inputs['To Min'].default_value=.9;rough.inputs['To Max'].default_value=.64;l.new(maps['curvature'].outputs['Color'],rough.inputs['Value']);l.new(rough.outputs[0],s.inputs['Roughness'])
 bakes.append(name)
# One exact frozen camera projection; pose registration lives in refine.py.
painting=bpy.data.images.load(str(A/'painting-aligned.png'));records=[]
# Project visible clothing/anatomy, never alpha-cut geometry.
for o in list(sc.objects):
 if o.type!='MESH' or any(t in o.name for t in ['base','arrow','feather','MPFB eyes','bowstring','belt mount','stitch','recurved','horn backing','sinew']):continue
 if len(o.data.vertices)<20:continue
 states=[(m,m.show_viewport) for m in o.modifiers]
 for mod,_ in states:
  if mod.type!='ARMATURE':mod.show_viewport=False
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(deps);me=ev.to_mesh()
 assert len(me.vertices)==len(o.data.vertices)
 uv=o.data.uv_layers.get('Painting projection') or o.data.uv_layers.new(name='Painting projection')
 attr=o.data.color_attributes.new(name='Painting confidence',type='FLOAT_COLOR',domain='CORNER')
 coords=[];weights=[]
 samples=[(v.index,v.co.copy(),v.normal.copy()) for v in me.vertices]
 for vi,co,vnormal in samples:
  world=ev.matrix_world @ co;q=world_to_camera_view(sc,sc.camera,world);x,y=q.x*256,(1-q.y)*256
  coords.append((x/256,1-y/256));normal=(ev.matrix_world.to_3x3().inverted().transposed() @ vnormal).normalized();direction=(sc.camera.location-world).normalized()
  # Back-facing surfaces transition to generated PBR fill; this fixed mask deforms with mesh.
  confidence=max(0,min(1,(normal.dot(direction)-.05)/.55))
  # Occluded surfaces must not retain the source hand when that hand moves away.
  direction=sc.camera.matrix_world.to_quaternion() @ Vector((0,0,1))
  hit=sc.ray_cast(deps,world+direction*.004,direction,distance=10)[0]
  if hit:confidence=0
  head_weight=sum(g.weight for g in o.data.vertices[vi].groups if o.vertex_groups[g.group].name in ('head','neck_01'))
  if (head_weight>.5 or 'beard' in o.name) and 80<x<117 and 71<y<88:confidence=0
  weights.append(confidence)
 for i,loop in enumerate(o.data.loops):uv.data[i].uv=coords[loop.vertex_index];attr.data[i].color=(weights[loop.vertex_index],)*3+(1,)
 ev.to_mesh_clear()
 for mod,state in states:mod.show_viewport=state
 for idx,oldmat in enumerate(list(o.data.materials)):
  if not oldmat.use_nodes:continue
  mat=oldmat.copy();mat.name=o.name+' projected';o.data.materials[idx]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
  if not s:continue
  tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name;t=n.new('ShaderNodeTexImage');t.image=painting;t.extension='CLIP';l.new(tc.outputs[0],t.inputs['Vector'])
  at=n.new('ShaderNodeVertexColor');at.layer_name=attr.name;factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(at.outputs[0],factor.inputs[0]);l.new(t.outputs['Alpha'],factor.inputs[1])
  amount=n.new('ShaderNodeMath');amount.operation='MULTIPLY';amount.inputs[1].default_value=.98;l.new(factor.outputs[0],amount.inputs[0])
  mix=n.new('ShaderNodeMixRGB');base=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
  if base:l.new(base,mix.inputs[1])
  else:mix.inputs[1].default_value=s.inputs['Base Color'].default_value
  l.new(amount.outputs[0],mix.inputs[0]);l.new(t.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
  # Preserve the source illumination only for camera rays; it is not a light source.
  out=n.get('Material Output');physical=out.inputs['Surface'].links[0].from_socket
  pigment=n.new('ShaderNodeEmission');l.new(t.outputs['Color'],pigment.inputs['Color'])
  rays=n.new('ShaderNodeLightPath');camera=n.new('ShaderNodeMath');camera.operation='MULTIPLY'
  l.new(rays.outputs['Is Camera Ray'],camera.inputs[0]);l.new(amount.outputs[0],camera.inputs[1])
  shader=n.new('ShaderNodeMixShader');l.new(camera.outputs[0],shader.inputs[0]);l.new(physical,shader.inputs[1]);l.new(pigment.outputs[0],shader.inputs[2]);l.new(shader.outputs[0],out.inputs['Surface'])
 records.append({'mesh':o.name,'vertices':len(o.data.vertices)})
sc['projection']='Frozen rest-camera UV after physical geometry registration; real MPFB/kit geometry, generated unseen fills'
sc['cream_target']='#E9CFA0';bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'composite-archer.blend'))
(M/'projection.json').write_text(json.dumps({'registration':'registration.json','projected_meshes':records,'bakes':bakes,'limitation':'Rest registration is approximate; lighting remains partially painted into colour.'},indent=2))
print('PAINT_READY')
