"""Actual AO/curvature maps and frozen rest-camera UV paint on closed 3D meshes.
Borrowed projection/partial-emission strategy from Vehicles; occluded faces keep fills.
"""
import bpy,bmesh,os,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/biplane';A=R/'assets/biplane';T=M/'textures';T.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'biplane.blend'));sc=bpy.context.scene;sc.cycles.samples=8;bpy.context.view_layer.update()
if any(o.type=='MESH' and 'PaintingProjection' in o.data.uv_layers for o in sc.objects):
 raise RuntimeError('Already projected: run build before paint; preserve the existing master')
# Sample finished faces densely enough that long strut/wing middles receive their
# own visibility. Endpoints hidden in a joint must not mask a whole visible panel.
for o in list(sc.objects):
 if o.type!='MESH' or not o.name.startswith('GEO-'):continue
 if o.name.startswith(('GEO-rivet','GEO-cooling-fin','GEO-radial-cylinder')):continue
 bm=bmesh.new();bm.from_mesh(o.data)
 longest=max((e.calc_length() for e in bm.edges),default=0)
 cuts=min(6,max(0,math.ceil(longest/.14)-1))
 if cuts:bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=cuts,use_grid_fill=True)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 o.data.update()
bpy.context.view_layer.update()
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
verts=[];faces=[]
for obj in sc.objects:
 if obj.type!='MESH' or obj.hide_render:continue
 eo=obj.evaluated_get(deps);me=eo.to_mesh();base_index=len(verts)
 verts.extend(eo.matrix_world@v.co for v in me.vertices)
 faces.extend(tuple(base_index+i for i in poly.vertices) for poly in me.polygons)
 eo.to_mesh_clear()
visibility=BVHTree.FromPolygons(verts,faces,all_triangles=False)
for o in list(sc.objects):
 if o.type!='MESH' or not o.name.startswith('GEO-'):continue
 if o.name.startswith(('GEO-rivet','GEO-cooling-fin','GEO-radial-cylinder','GEO-wheel-brass-hub','GEO-laminated-propeller','GEO-propeller-boss','GEO-cream-stone-base')):continue
 me=o.data;uv=me.uv_layers.new(name='PaintingProjection');wt=me.color_attributes.new(name='PaintConfidence',type='FLOAT_COLOR',domain='CORNER');nm=o.matrix_world.to_3x3().inverted().transposed()
 sampled=[]
 for v in me.vertices:
  world=o.matrix_world@v.co;p=world_to_camera_view(sc,sc.camera,world)
  facing=max(0,min(1,((nm@v.normal).normalized().dot(view)-.05)/.4))
  loc,normal,idx,distance=visibility.ray_cast(world+view*20,-view,20.03)
  if loc is not None and (loc-world).length>.035:facing=0
  sampled.append(((p.x,p.y),facing))
 for loop in me.loops:
  position,facing=sampled[loop.vertex_index]
  uv.data[loop.index].uv=position;wt.data[loop.index].color=(facing,facing,facing,1)
 ma=o.data.materials[0].copy();ma.name=o.name+' painted';o.data.materials[0]=ma;n=ma.node_tree.nodes;l=ma.node_tree.links;s=n.get('Principled BSDF');out=n.get('Material Output')
 old=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
 co=n.new('ShaderNodeUVMap');co.uv_map='PaintingProjection';tx=n.new('ShaderNodeTexImage');tx.image=tex;tx.extension='CLIP';l.new(co.outputs[0],tx.inputs[0]);vc=n.new('ShaderNodeVertexColor');vc.layer_name='PaintConfidence';mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(vc.outputs['Color'],mask.inputs[0]);l.new(tx.outputs['Alpha'],mask.inputs[1])
 # Camera-only pigment preserves painted light without turning the aircraft
 # into a lamp. Non-camera rays retain the original physical generated fill.
 pigment=n.new('ShaderNodeBsdfPrincipled');pigment.name='Painted camera pigment'
 pigment.inputs['Base Color'].default_value=(0,0,0,1)
 pigment.inputs['Roughness'].default_value=1
 pigment.inputs['Specular IOR Level'].default_value=0
 pigment.inputs['Emission Strength'].default_value=1
 l.new(tx.outputs['Color'],pigment.inputs['Emission Color'])
 ray=n.new('ShaderNodeLightPath');ray.name='Camera-only paint'
 camera_mask=n.new('ShaderNodeMath');camera_mask.operation='MULTIPLY'
 l.new(mask.outputs[0],camera_mask.inputs[0]);l.new(ray.outputs['Is Camera Ray'],camera_mask.inputs[1])
 fac=n.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.96
 l.new(camera_mask.outputs[0],fac.inputs[0])
 blend=n.new('ShaderNodeMixShader');l.new(fac.outputs[0],blend.inputs[0])
 l.new(s.outputs[0],blend.inputs[1]);l.new(pigment.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs['Surface'])
 records.append({'mesh':o.name,'projection':'frozen camera UV','hidden':'painted generated box fill or original material','visibility':'normal and scene ray cast'})
# Static stone keeps physical cream shading with a restrained camera pigment
# lift; never put a static painting of the moving support on the disc.
base=bpy.data.objects['GEO-cream-stone-base'];ma=base.data.materials[0].copy();base.data.materials[0]=ma
n=ma.node_tree.nodes;l=ma.node_tree.links;s=n.get('Principled BSDF');out=n.get('Material Output')
pigment=n.new('ShaderNodeBsdfPrincipled');pigment.inputs['Base Color'].default_value=(0,0,0,1)
pigment.inputs['Emission Strength'].default_value=1
geo=n.new('ShaderNodeNewGeometry');separate=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Normal'],separate.inputs[0])
ramp=n.new('ShaderNodeValToRGB')
def linear(c):return ((c/255+.055)/1.055)**2.4
ramp.color_ramp.elements[0].position=0;ramp.color_ramp.elements[0].color=tuple(linear(c) for c in (218,177,132))+(1,)
ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=tuple(linear(c) for c in (249,218,178))+(1,)
l.new(separate.outputs['Z'],ramp.inputs[0]);l.new(ramp.outputs['Color'],pigment.inputs['Emission Color'])
pigment.inputs['Specular IOR Level'].default_value=0
ray=n.new('ShaderNodeLightPath');fac=n.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.80;l.new(ray.outputs['Is Camera Ray'],fac.inputs[0])
blend=n.new('ShaderNodeMixShader');l.new(fac.outputs[0],blend.inputs[0]);l.new(s.outputs[0],blend.inputs[1]);l.new(pigment.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs['Surface'])
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'biplane.blend'));(T/'paint.json').write_text(json.dumps(records,indent=2));print('PAINTED',len(records))

unit=Path(__file__).resolve().parent
(M/"build-inputs.json").write_text(json.dumps({"master_sha256":hashlib.sha256((M/"biplane.blend").read_bytes()).hexdigest(),"scripts":{name:hashlib.sha256((unit/name).read_bytes()).hexdigest() for name in ("prepare.py","scene.py","refine.py","paint.py")}},indent=2))
