"""Bake geometry wear, then freeze the painting's UVs on the true 3D rest pose."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import MASTER, ASSETS, ROOT, log
bpy.ops.wm.open_mainfile(filepath=str(MASTER/'model.blend'));sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=4;sc.render.threads_mode='FIXED';sc.render.threads=3
bpy.context.view_layer.update()
projection=bpy.data.images.load(str(ASSETS/'projection.png'));fill=bpy.data.images.load(str(ROOT/'assets/tank/painted-olive.png'))
baked={};folder=MASTER/'textures/baked';folder.mkdir(parents=True,exist_ok=True)
for name in ['GEO-Main faceted hull','GEO-Squat turret','GEO-Upper armour near-left']:
 o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 # Applied bevel gives pointiness a real rounded edge to measure.
 for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT');o.data.uv_layers.active.name='WearBake'
 m=o.data.materials[0].copy();o.data.materials.clear();o.data.materials.append(m);n=m.node_tree.nodes;l=m.node_tree.links;out=n.get('Material Output');bs=n.get('Principled BSDF');maps={}
 for kind in ['AO','curvature']:
  im=bpy.data.images.new(name+' '+kind,256,256,alpha=False);im.colorspace_settings.name='Non-Color';t=n.new('ShaderNodeTexImage');t.image=im;n.active=t
  if kind=='curvature':
   geo=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],em.inputs['Color']);l.new(em.outputs[0],out.inputs['Surface'])
  bpy.ops.object.bake(type='AO' if kind=='AO' else 'EMIT')
  l.new(bs.outputs[0],out.inputs['Surface'])
  im.filepath_raw=str(folder/(name.replace('GEO-','').replace(' ','-')+'-'+kind+'.png'));im.file_format='PNG';im.save();maps[kind]=im
 baked[name]=maps
view=sc.camera.rotation_euler.to_matrix()@Vector((0,0,1));records=[]
for o in sc.objects:
 if o.type!='MESH' or o.name in ['GEO-Stationary cream disc','GEO-Muzzle flash']:continue
 original=o.data.materials[0];m=original.copy();m.name=original.name+' projected '+o.name;o.data.materials.clear();o.data.materials.append(m)
 n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');out=n.get('Material Output')
 tc=n.new('ShaderNodeTexCoord');f=n.new('ShaderNodeTexImage');f.image=fill;f.projection='BOX';f.projection_blend=.25;l.new(tc.outputs['Generated'],f.inputs[0])
 hidden=n.new('ShaderNodeMixRGB');hidden.blend_type='MULTIPLY';hidden.inputs[0].default_value=.55;hidden.inputs[2].default_value=original.diffuse_color;l.new(f.outputs['Color'],hidden.inputs[1]);pigment=hidden.outputs[0]
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=140;noise.inputs['Detail'].default_value=2
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.012;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
 if o.name in baked:
  uv=n.new('ShaderNodeUVMap');uv.uv_map='WearBake';maps={}
  for kind,im in baked[o.name].items():
   tex=n.new('ShaderNodeTexImage');tex.image=im;l.new(uv.outputs[0],tex.inputs[0]);maps[kind]=tex
  grime=n.new('ShaderNodeMixRGB');grime.blend_type='MULTIPLY';grime.inputs[0].default_value=.45;l.new(pigment,grime.inputs[1]);l.new(maps['AO'].outputs[0],grime.inputs[2]);pigment=grime.outputs[0]
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.50;ramp.color_ramp.elements[1].position=.56;l.new(maps['curvature'].outputs[0],ramp.inputs[0])
  wear=n.new('ShaderNodeMixRGB');l.new(ramp.outputs[0],wear.inputs[0]);l.new(pigment,wear.inputs[1]);wear.inputs[2].default_value=(.40,.37,.30,1);pigment=wear.outputs[0]
 uv=o.data.uv_layers.new(name='RestCamera');confidence=o.data.color_attributes.new(name='ProjectionConfidence',type='FLOAT_COLOR',domain='CORNER');normal=o.matrix_world.to_3x3().inverted().transposed()
 for loop in o.data.loops:
  v=o.data.vertices[loop.vertex_index];p=world_to_camera_view(sc,sc.camera,o.matrix_world@v.co);uv.data[loop.index].uv=(p.x,p.y)
  w=max(0,min(1,((normal@v.normal).normalized().dot(view)+.08)/.28));confidence.data[loop.index].color=(w,w,w,1)
 uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map='RestCamera';tex=n.new('ShaderNodeTexImage');tex.image=projection;tex.extension='CLIP';l.new(uvnode.outputs[0],tex.inputs[0]);vcol=n.new('ShaderNodeVertexColor');vcol.layer_name='ProjectionConfidence'
 mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(tex.outputs['Alpha'],mask.inputs[0]);l.new(vcol.outputs['Color'],mask.inputs[1])
 mix=n.new('ShaderNodeMixRGB');l.new(mask.outputs[0],mix.inputs[0]);l.new(pigment,mix.inputs[1]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
 # Painting-specific display transform and camera-ray pigment avoid double-lighting.
 em=n.new('ShaderNodeEmission');l.new(mix.outputs[0],em.inputs['Color']);ray=n.new('ShaderNodeLightPath');factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(mask.outputs[0],factor.inputs[0]);l.new(ray.outputs['Is Camera Ray'],factor.inputs[1]);strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.94;l.new(factor.outputs[0],strength.inputs[0]);mixs=n.new('ShaderNodeMixShader');l.new(strength.outputs[0],mixs.inputs[0]);l.new(s.outputs[0],mixs.inputs[1]);l.new(em.outputs[0],mixs.inputs[2]);l.new(mixs.outputs[0],out.inputs['Surface'])
 records.append(o.name)
# Stone is intentionally independent of the painting's feet/contact shadows.
m=bpy.data.materials['MAT-cream stone E9CFA0'];n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=150;b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.10;b.inputs['Distance'].default_value=.008;l.new(noise.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],s.inputs['Normal']);s.inputs['Roughness'].default_value=.88
# Camera-only painted stone preserves warm rim pigment; short-range AO retains
# real foot contact without baking source feet into the fixed base.
ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Color'].default_value=(.815,.624,.352,1);ao.inputs['Distance'].default_value=.20
em=n.new('ShaderNodeEmission');l.new(ao.outputs['Color'],em.inputs['Color']);ray=n.new('ShaderNodeLightPath');fac=n.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.72;l.new(ray.outputs['Is Camera Ray'],fac.inputs[0]);blend=n.new('ShaderNodeMixShader');l.new(fac.outputs[0],blend.inputs[0]);l.new(s.outputs[0],blend.inputs[1]);l.new(em.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],n.get('Material Output').inputs['Surface'])
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'finished.blend'))
(MASTER/'materials.json').write_text(json.dumps({'projected_meshes':records,'bakes':{name:{k:str(v.filepath_raw) for k,v in maps.items()} for name,maps in baked.items()},'hidden_fill':'original tank painted olive CC BY 4.0; box projected', 'base':'linear pigment from sRGB E9CFA0; independent contact shadows'},indent=2))
log('Finished frozen camera projection on solid geometry; six actual AO/curvature bakes, generated olive hidden-surface fill, grain and chipped edges. No alpha clipping or painted base feet.')
