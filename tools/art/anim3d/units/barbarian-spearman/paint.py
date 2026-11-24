"""Freeze rest-camera UVs on real 3D surfaces; procedural/PBR backs, painted fronts."""
import bpy, os, json, math, hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-spearman';A=R/'assets/barbarian-spearman'
for name,digest in json.loads(Path(__file__).with_name('assets.lock.json').read_text()).items():
 assert hashlib.sha256((A/name).read_bytes()).hexdigest()==digest, f'Changed painting/fill input: {name}'
bpy.ops.wm.open_mainfile(filepath=str(M/'registered.blend'));sc=bpy.context.scene
image=bpy.data.images.load(str(A/'painting-aligned.png'));image.pack()
stone_image=bpy.data.images.load(str(A/'stone-fill-aligned.png'));stone_image.pack()
# Camera coordinates are baked in the neutral pose, never evaluated per animation frame.
for ob in list(sc.objects):
 if ob.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
# Test visibility on finished rest surfaces, not merely their facing normals.
# Otherwise the source shield is permanently painted onto the hidden cape/arm.
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();vertices=[];faces=[]
for obj in sc.objects:
 if obj.type!='MESH':continue
 ev=obj.evaluated_get(dg);surface=ev.to_mesh();offset=len(vertices)
 vertices.extend(obj.matrix_world@v.co for v in surface.vertices)
 faces.extend(tuple(offset+i for i in p.vertices) for p in surface.polygons)
 ev.to_mesh_clear()
visibility=BVHTree.FromPolygons(vertices,faces);view_ray=sc.camera.matrix_world.to_quaternion()@Vector((0,0,1))
del vertices,faces
# One material per object permits independent incidence and material masks.
for ob in list(sc.objects):
 if ob.type!='MESH' or not ob.data.materials:continue
 mat=ob.data.materials[0].copy();ob.data.materials[0]=mat
 n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF');base=bs.inputs['Base Color'].default_value[:]
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=90;noise.inputs['Detail'].default_value=3
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.0015
 l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
 # Real AO and curvature drive cavity grime and polished exposed edges at render time.
 ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.07
 grime=n.new('ShaderNodeMixRGB');grime.blend_type='MULTIPLY';grime.inputs[0].default_value=.35;grime.inputs[1].default_value=base;l.new(ao.outputs['Color'],grime.inputs[2])
 geom=n.new('ShaderNodeNewGeometry');ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.32;ramp.color_ramp.elements[0].color=(.55,.55,.55,1);ramp.color_ramp.elements[1].position=.62;ramp.color_ramp.elements[1].color=(.27,.27,.27,1)
 l.new(geom.outputs['Pointiness'],ramp.inputs[0])
 if bs.inputs['Metallic'].default_value==1:l.new(ramp.outputs[0],bs.inputs['Roughness'])
 # Generated linen/hair fill is used on unseen back faces, under AO and scan-scale bump.
 kind='linen' if 'linen' in mat.name.lower() or 'rawhide' in mat.name.lower() else 'fur' if 'fur' in mat.name.lower() else 'hair' if 'hair' in mat.name.lower() else 'leather' if 'leather' in mat.name.lower() else None
 fallback=grime.outputs[0]
 if kind:
  fill=n.new('ShaderNodeTexImage');fill.image=bpy.data.images.load(str(A/f'fill-{kind}.png'),check_existing=True);fill.image.pack();fill.projection='BOX';fill.projection_blend=.25
  tc=n.new('ShaderNodeTexCoord');l.new(tc.outputs['Generated'],fill.inputs['Vector'])
  fm=n.new('ShaderNodeMixRGB');fm.inputs[0].default_value=.80;l.new(fallback,fm.inputs[1]);l.new(fill.outputs['Color'],fm.inputs[2]);fallback=fm.outputs[0]
 # Topology-changing modifiers are disabled only to evaluate the weighted base mesh.
 saved=[]
 for mod in ob.modifiers:
  if mod.type!='ARMATURE':saved.append((mod,mod.show_viewport));mod.show_viewport=False
 bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 assert len(me.vertices)==len(ob.data.vertices),(ob.name,len(me.vertices),len(ob.data.vertices))
 uv=ob.data.uv_layers.new(name='Frozen painting camera')
 attr=ob.data.color_attributes.new(name='Projection weight',type='FLOAT_COLOR',domain='CORNER')
 view=(sc.camera.location-Vector((0,0,1))).normalized()
 for loop in ob.data.loops:
  v=me.vertices[loop.vertex_index];world=ob.matrix_world@v.co;p=world_to_camera_view(sc,sc.camera,world)
  uv.data[loop.index].uv=(p.x,p.y)
  normal=(ob.matrix_world.to_3x3()@v.normal).normalized();weight=max(0,min(1,(normal.dot(view)-.05)/.55))
  if ob.name=='Stationary cream base':weight=1 if p.y<.25 else 0
  if p.x<0 or p.x>1 or p.y<0 or p.y>1:weight=0
  hit=visibility.ray_cast(world+view_ray*5,-view_ray,10)[0]
  if ob.name!='Stationary cream base' and hit is not None and (hit-world).dot(view_ray)>.018:weight=0
  attr.data[loop.index].color=(weight,weight,weight,1)
 ev.to_mesh_clear()
 for mod,value in saved:mod.show_viewport=value
 coord=n.new('ShaderNodeUVMap');coord.uv_map=uv.name;tex=n.new('ShaderNodeTexImage');tex.image=image;tex.extension='CLIP';l.new(coord.outputs[0],tex.inputs['Vector'])
 weight=n.new('ShaderNodeVertexColor');weight.layer_name=attr.name
 mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(weight.outputs['Color'],mul.inputs[0]);l.new(tex.outputs['Alpha'],mul.inputs[1])
 strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.98;l.new(mul.outputs[0],strength.inputs[0])
 if ob.name=='Stationary cream base':
  # Clean generated top on the real stone; original rim below the figure.
  filltex=n.new('ShaderNodeTexImage');filltex.image=stone_image;filltex.extension='EXTEND';l.new(coord.outputs[0],filltex.inputs[0])
  sep=n.new('ShaderNodeSeparateXYZ');l.new(coord.outputs[0],sep.inputs[0])
  lip=n.new('ShaderNodeMapRange');lip.clamp=True;lip.inputs['From Min'].default_value=.125;lip.inputs['From Max'].default_value=.145;lip.inputs['To Min'].default_value=1;lip.inputs['To Max'].default_value=0;l.new(sep.outputs['Y'],lip.inputs['Value'])
  stone_mix=n.new('ShaderNodeMixRGB');l.new(lip.outputs[0],stone_mix.inputs[0]);l.new(filltex.outputs['Color'],stone_mix.inputs[1]);l.new(tex.outputs['Color'],stone_mix.inputs[2])
  contact=n.new('ShaderNodeMixRGB');contact.blend_type='MULTIPLY';contact.inputs[0].default_value=.65;l.new(stone_mix.outputs[0],contact.inputs[1]);l.new(ao.outputs['Color'],contact.inputs[2])
  for link in list(strength.inputs[0].links):l.remove(link)
  l.new(filltex.outputs['Alpha'],strength.inputs[0])
 l.new(fallback,bs.inputs['Base Color'])
 # Preserve the painting's existing illumination for camera rays only.
 pigment=n.new('ShaderNodeBsdfPrincipled');pigment.name='Camera painted pigment';pigment.inputs['Base Color'].default_value=(0,0,0,1);pigment.inputs['Specular IOR Level'].default_value=0
 l.new(tex.outputs['Color'],pigment.inputs['Emission Color']);pigment.inputs['Emission Strength'].default_value=1
 if ob.name=='Stationary cream base':l.new(contact.outputs[0],pigment.inputs['Emission Color'])
 lp=n.new('ShaderNodeLightPath');camera_weight=n.new('ShaderNodeMath');camera_weight.operation='MULTIPLY';l.new(lp.outputs['Is Camera Ray'],camera_weight.inputs[0]);l.new(strength.outputs[0],camera_weight.inputs[1])
 shader=n.new('ShaderNodeMixShader');l.new(camera_weight.outputs[0],shader.inputs[0]);l.new(bs.outputs[0],shader.inputs[1]);l.new(pigment.outputs[0],shader.inputs[2]);l.new(shader.outputs[0],n.get('Material Output').inputs['Surface'])
sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
for name in ['Warm key','Soft fill','Cool rim']:bpy.data.objects[name].data.energy*=.55
import runpy
runpy.run_path('tools/art/anim3d/units/barbarian-spearman/projection_mask.py')['apply']()
sc['stage']='textured';sc['projection']='Fixed rest camera UV; incidence/alpha blended with generated fills, on real 3D mesh'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'barbarian-spearman.blend'))
print('PAINT_READY')
