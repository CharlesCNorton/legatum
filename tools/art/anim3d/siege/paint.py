"""Calibrated rest-camera projection onto real meshes; preserves unseen PBR surfaces."""
import bpy,os,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/field-cannon';bpy.ops.wm.open_mainfile(filepath=str(M/'field-cannon.blend'))
sc=bpy.context.scene;cam=sc.camera;source=R/'assets/field-cannon/painting-source.png';image=bpy.data.images.load(str(source),check_existing=True)
# Source rectangles measured against the original 1254 px painting, not a new generated figure.
regions=[('Tailored blue coat body',(295,265,524,524),.72),('Folded blue sleeve upperarm r',(215,272,357,412),.70),('Folded blue sleeve lowerarm r',(179,345,282,461),.65),('Folded blue sleeve upperarm l',(518,307,615,469),.70),('Folded blue sleeve lowerarm l',(558,435,672,567),.65),('White wool breeches',(205,516,501,814),.62),('Hollow bronze barrel',(654,607,1115,749),.72),('Black felt shako',(372,55,552,190),.70),('MPFB artillery gunner anatomy',(367,172,517,277),.74)]
navy=bpy.data.images.load(str(R/'assets/field-cannon/projection-navy.png'),check_existing=True)
ivory=bpy.data.images.load(str(R/'assets/field-cannon/projection-ivory.png'),check_existing=True)
records=[]
for name,rect,strength in regions:
 obj=bpy.data.objects.get(name)
 if not obj or obj.type!='MESH':continue
 # Evaluate pose and morphs without topology-changing modifiers, so UV loops retain their indices.
 disabled=[]
 for mod in obj.modifiers:
  if mod.type not in ['ARMATURE'] and mod.show_viewport:disabled.append(mod);mod.show_viewport=False
 bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 assert len(me.vertices)==len(obj.data.vertices),(name,'projection topology')
 coords=[world_to_camera_view(sc,cam,ev.matrix_world@v.co) for v in me.vertices]
 face_only=name.startswith('MPFB');selected=[i for i,v in enumerate(me.vertices) if not face_only or v.co.z>1.49]
 xmin=min(coords[i].x for i in selected);xmax=max(coords[i].x for i in selected);ymin=min(coords[i].y for i in selected);ymax=max(coords[i].y for i in selected)
 facing=[]
 for v in me.vertices:
  normal=(ev.matrix_world.to_3x3()@v.normal).normalized();toward=(cam.location-ev.matrix_world@v.co).normalized();facing.append(max(0,min(1,(normal.dot(toward)-.05)/.55)))
 ev.to_mesh_clear()
 for mod in disabled:mod.show_viewport=True
 uv=obj.data.uv_layers.get('Painting projection') or obj.data.uv_layers.new(name='Painting projection')
 mask=obj.data.color_attributes.get('Painting visibility') or obj.data.color_attributes.new(name='Painting visibility',type='FLOAT_COLOR',domain='CORNER')
 selected=set(selected)
 l,t,r,b=rect
 for loop in obj.data.loops:
  i=loop.vertex_index;c=coords[i];u=(c.x-xmin)/max(.001,xmax-xmin);v=(c.y-ymin)/max(.001,ymax-ymin)
  uv.data[loop.index].uv=((l+u*(r-l))/image.size[0],1-(b-v*(b-t))/image.size[1])
  f=facing[i] if i in selected else 0;mask.data[loop.index].color=(f,f,f,1)
 # Keep original UVs active for skin maps and AO. Projection is explicitly named in its shader.
 obj.data.uv_layers.active_index=0;obj.data.uv_layers[0].active_render=True
 for slot in obj.material_slots:
  if not slot.material or 'bore soot' in slot.material.name or (face_only and 'skin' not in slot.material.name):continue
  mat=slot.material.copy();slot.material=mat;n=mat.node_tree.nodes;links=mat.node_tree.links;p=n.get('Principled BSDF')
  if not p:continue
  old=p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].is_linked else None
  if not old:
   rgb=n.new('ShaderNodeRGB');rgb.outputs[0].default_value=p.inputs['Base Color'].default_value;old=rgb.outputs[0]
  tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name;tex=n.new('ShaderNodeTexImage');tex.image=navy if ('coat body' in name or 'blue sleeve' in name) else ivory if 'breeches' in name else image;tex.extension='CLIP';links.new(tc.outputs[0],tex.inputs[0])
  attr=n.new('ShaderNodeVertexColor');attr.layer_name=mask.name;mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';links.new(attr.outputs['Color'],mult.inputs[0]);links.new(tex.outputs['Alpha'],mult.inputs[1]);weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=strength;links.new(mult.outputs[0],weight.inputs[0])
  mix=n.new('ShaderNodeMixRGB');links.new(weight.outputs[0],mix.inputs[0]);links.new(old,mix.inputs[1]);links.new(tex.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],p.inputs['Base Color'])
 records.append({'object':name,'source_rect':rect,'strength':strength})
sc['painted_projection']='Own CC BY 4.0 field cannon painting, region-calibrated rest camera UVs with facing/alpha blend; unseen surfaces retain scanned or generated material.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'field-cannon.blend'));(M/'projection.json').write_text(json.dumps(records,indent=2))
