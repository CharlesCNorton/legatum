"""Actual AO/curvature maps and frozen rest-camera UV paint on closed 3D meshes.
Borrowed projection/partial-emission strategy from Vehicles; occluded faces keep fills.
"""
import bpy,os,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/biplane';A=R/'assets/biplane';T=M/'textures';T.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'biplane.blend'));sc=bpy.context.scene;sc.cycles.samples=8;bpy.context.view_layer.update()
if any(o.type=='MESH' and 'PaintingProjection' in o.data.uv_layers for o in sc.objects):
 raise RuntimeError('Already projected: run build before paint; preserve the existing master')
# Keep the unprojected material master for honest plain stage GPU renders/rebuilds.
bpy.ops.wm.save_as_mainfile(filepath=str(M/'unpainted.blend'))
major=['GEO-tapered-fuselage','GEO-engine-cowling','GEO-upper-cambered-wing','GEO-lower-cambered-wing']
records=[]
for name in major:
 o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 ma=o.data.materials[0].copy();o.data.materials[0]=ma;n=ma.node_tree.nodes;l=ma.node_tree.links;s=n.get('Principled BSDF');output=n.get('Material Output')
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT');o.data.uv_layers.active.name='BakeUV'
 co=n.new('ShaderNodeUVMap');co.uv_map='BakeUV';maps={}
 for kind in ['AO','curvature']:
  im=bpy.data.images.new(name+'-'+kind,width=256,height=256,alpha=False);im.colorspace_settings.name='Non-Color';node=n.new('ShaderNodeTexImage');node.image=im;l.new(co.outputs[0],node.inputs[0]);n.active=node
  if kind=='curvature':
   geo=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],em.inputs[0]);l.new(em.outputs[0],output.inputs['Surface'])
  bpy.ops.object.bake(type='AO' if kind=='AO' else 'EMIT',margin=4)
  im.filepath_raw=str(T/(name+'-'+kind+'.png'));im.file_format='PNG';im.save();maps[kind]=node
  if kind=='curvature':l.new(s.outputs[0],output.inputs['Surface']);n.remove(em);n.remove(geo)
 source=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
 mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=.30
 if source:l.new(source,mul.inputs[1])
 else:mul.inputs[1].default_value=s.inputs['Base Color'].default_value
 l.new(maps['AO'].outputs['Color'],mul.inputs[2]);l.new(mul.outputs[0],s.inputs['Base Color'])
 # Actual baked pointiness controls subtle roughness; exposed edges have separate metal geometry.
 ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=.35;ramp.inputs['From Max'].default_value=.65;ramp.inputs['To Min'].default_value=.8;ramp.inputs['To Max'].default_value=.45;l.new(maps['curvature'].outputs[0],ramp.inputs['Value']);l.new(ramp.outputs[0],s.inputs['Roughness'])
 records.append({'mesh':name,'bakes':['AO','curvature'],'size':256})
# Freeze UV coordinates at rest. The animation carries those UVs with real surfaces.
tex=bpy.data.images.load(str(A/'projection.png'));view=sc.camera.rotation_euler.to_matrix()@Vector((0,0,1));deps=bpy.context.evaluated_depsgraph_get()
for o in list(sc.objects):
 if o.type!='MESH' or not o.name.startswith('GEO-'):continue
 if o.name.startswith(('GEO-rivet','GEO-cooling-fin','GEO-radial-cylinder','GEO-rubber-wheel','GEO-linen-wheel-disc','GEO-wheel-brass-hub','GEO-laminated-propeller','GEO-propeller-boss')):continue
 me=o.data;uv=me.uv_layers.new(name='PaintingProjection');wt=me.color_attributes.new(name='PaintConfidence',type='FLOAT_COLOR',domain='CORNER');nm=o.matrix_world.to_3x3().inverted().transposed()
 for loop in me.loops:
  v=me.vertices[loop.vertex_index];world=o.matrix_world@v.co;p=world_to_camera_view(sc,sc.camera,world);uv.data[loop.index].uv=(p.x,p.y)
  facing=max(0,min(1,((nm@v.normal).normalized().dot(view)-.05)/.4))
  hit,loc,normal,idx,hitobj,matrix=sc.ray_cast(deps,world+view*20,-view,distance=20.03)
  if hit and (loc-world).length>.065:facing=0
  wt.data[loop.index].color=(facing,facing,facing,1)
 ma=o.data.materials[0].copy();ma.name=o.name+' painted';o.data.materials[0]=ma;n=ma.node_tree.nodes;l=ma.node_tree.links;s=n.get('Principled BSDF');out=n.get('Material Output')
 old=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
 co=n.new('ShaderNodeUVMap');co.uv_map='PaintingProjection';tx=n.new('ShaderNodeTexImage');tx.image=tex;tx.extension='CLIP';l.new(co.outputs[0],tx.inputs[0]);vc=n.new('ShaderNodeVertexColor');vc.layer_name='PaintConfidence';mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(vc.outputs['Color'],mask.inputs[0]);l.new(tx.outputs['Alpha'],mask.inputs[1])
 mix=n.new('ShaderNodeMixRGB');l.new(mask.outputs[0],mix.inputs[0]);l.new(tx.outputs['Color'],mix.inputs[2])
 if old:l.new(old,mix.inputs[1])
 else:mix.inputs[1].default_value=s.inputs['Base Color'].default_value
 l.new(mix.outputs[0],s.inputs['Base Color'])
 em=n.new('ShaderNodeEmission');l.new(mix.outputs[0],em.inputs[0]);fac=n.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.65;l.new(mask.outputs[0],fac.inputs[0]);blend=n.new('ShaderNodeMixShader');l.new(fac.outputs[0],blend.inputs[0]);l.new(s.outputs[0],blend.inputs[1]);l.new(em.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs['Surface'])
 records.append({'mesh':o.name,'projection':'frozen camera UV','hidden':'painted generated box fill or original material','visibility':'normal and scene ray cast'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'biplane.blend'));(T/'paint.json').write_text(json.dumps(records,indent=2));print('PAINTED',len(records))
