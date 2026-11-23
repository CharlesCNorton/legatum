"""One frozen painting camera on finished, articulated full-depth geometry."""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from refine import refine
from bpy_extras.object_utils import world_to_camera_view
inputs=json.loads(Path(__file__).with_name('assets.lock.json').read_text())['inputs']
for name,expected in inputs.items():
 assert hashlib.sha256((ASSETS/name).read_bytes()).hexdigest()==expected,('changed texture input',name)
bpy.ops.wm.open_mainfile(filepath=str(MASTER/'archer-unpainted.blend'))
refine()
sc=bpy.context.scene
painting=bpy.data.images.load(str(ASSETS/'painting-aligned.png'),check_existing=True)
view=sc.camera.matrix_world.to_quaternion()@Vector((0,0,1))
deps=bpy.context.evaluated_depsgraph_get()
records=[]
for obj in list(sc.objects):
 if obj.type!='MESH' or obj.name.startswith(('GEO-Stationary','GEO-MPFB eyes')):continue
 ev=obj.evaluated_get(deps);me=ev.to_mesh();assert len(me.vertices)==len(obj.data.vertices)
 uvlist=[];weights=[]
 for v in me.vertices:
  world=ev.matrix_world@v.co;q=world_to_camera_view(sc,sc.camera,world);uvlist.append((q.x,q.y))
  normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized()
  hit,loc,_,_,hitobj,_=sc.ray_cast(deps,world+view*4,-view,distance=4.01)
  tolerance=.035 if obj.name=='GEO-MPFB archer anatomy' else .012
  visible=hit and hitobj.original==obj and (loc-world).length<tolerance
  weights.append(1.0 if obj.name.startswith('GEO-Pale horsehair crest') else max(0,min(1,(normal.dot(view)+.05)/.35)) if visible else 0)
 ev.to_mesh_clear()
 uv=obj.data.uv_layers.get('Painting projection') or obj.data.uv_layers.new(name='Painting projection')
 old=obj.data.color_attributes.get('Painting incidence')
 if old:obj.data.color_attributes.remove(old)
 att=obj.data.color_attributes.new(name='Painting incidence',type='FLOAT_COLOR',domain='CORNER')
 for i,loop in enumerate(obj.data.loops):
  uv.data[i].uv=uvlist[loop.vertex_index];att.data[i].color=(weights[loop.vertex_index],)*3+(1,)
 if len(obj.data.uv_layers)>1:obj.data.uv_layers[0].active_render=True
 for i,m in enumerate(list(obj.data.materials)):
  material=m.copy();obj.data.materials[i]=material;n=material.node_tree.nodes;l=material.node_tree.links
  s=n.get('Principled BSDF');output=n.get('Material Output');physical=output.inputs['Surface'].links[0].from_socket
  tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name;tex=n.new('ShaderNodeTexImage');tex.image=painting;tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs[0])
  vc=n.new('ShaderNodeVertexColor');vc.layer_name=att.name
  alpha=n.new('ShaderNodeMath');alpha.operation='MULTIPLY';l.new(vc.outputs[0],alpha.inputs[0]);l.new(tex.outputs['Alpha'],alpha.inputs[1])
  camera=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';l.new(alpha.outputs[0],weight.inputs[0]);l.new(camera.outputs['Is Camera Ray'],weight.inputs[1])
  pigment=n.new('ShaderNodeBsdfPrincipled');pigment.name='Camera-only painted pigment';pigment.inputs['Base Color'].default_value=(0,0,0,1);pigment.inputs['Specular IOR Level'].default_value=0
  pigment.inputs['Emission Strength'].default_value=.96;l.new(tex.outputs['Color'],pigment.inputs['Emission Color'])
  mix=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],mix.inputs[0]);l.new(physical,mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],output.inputs['Surface'])
 records.append({'object':obj.name,'vertices':len(obj.data.vertices),'visible_vertices':sum(w>.1 for w in weights)})
sc['projection']='Frozen finished-surface UVs with camera-ray pigment; real physical material on occluded/back surfaces and non-camera rays.'
(MASTER/'projection.json').write_text(json.dumps({'objects':records,'strength':.96,'limitation':'Measured contour fitting preserves full depth and native weights; not exact pose or camera recovery.'},indent=2))
save(MASTER/'archer.blend')
(MASTER/'paint-inputs.json').write_text(json.dumps({'inputs':inputs,'scripts':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ['paint.py','refine.py','craft.py']},'master_sha256':hashlib.sha256((MASTER/'archer.blend').read_bytes()).hexdigest()},indent=2))
log('- Projected painting onto finished surfaces with occlusion/facing masks and camera-only pigment; original generated fills, real AO/curvature and physical lighting remain.')
