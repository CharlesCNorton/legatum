"""Frozen rest-camera UV projection onto real hull and turret meshes.
Camera-facing confidence fades to procedural paint on hidden/back surfaces.
Baked AO UVs are explicitly retained; projection UVs follow the animated geometry.
"""
import bpy,os,json
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/tank'
bpy.ops.wm.open_mainfile(filepath=str(M/'tank.blend'));sc=bpy.context.scene;bpy.context.view_layer.update()
tex=bpy.data.images.load(str(M/'textures/painting-projection.png'),check_existing=True)
view=sc.camera.rotation_euler.to_matrix() @ Vector((0,0,1))
records=[]
major=['Sloped upper hull','Rounded cast turret','Rounded transmission nose','Rounded mantlet','Lower hull']
wheel_prefixes=('Cast wheel dished face','Wheel hub','Drive wheel face','Drive hub','VVSS bogie block','Spring cover')
names=major+[o.name for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(wheel_prefixes)]
for name in names:
    o=bpy.data.objects[name];mesh=o.data;old=mesh.uv_layers.active.name if mesh.uv_layers.active else None
    if 'PaintingProjection' in mesh.uv_layers:raise RuntimeError('Projection already applied; bake again before paint')
    uv=mesh.uv_layers.new(name='PaintingProjection');weights=mesh.color_attributes.new(name='Paint confidence',type='FLOAT_COLOR',domain='CORNER')
    normalmatrix=o.matrix_world.to_3x3().inverted().transposed()
    for loop in mesh.loops:
        v=mesh.vertices[loop.vertex_index];p=world_to_camera_view(sc,sc.camera,o.matrix_world @ v.co)
        uv.data[loop.index].uv=(p.x,p.y)
        facing=max(0,min(1,((normalmatrix @ v.normal).normalized().dot(view)-.05)/.40))
        weights.data[loop.index].color=(facing,facing,facing,1)
    mat=o.data.materials[0].copy();mat.name=name+' • painted projection';o.data.materials.clear();o.data.materials.append(mat)
    n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
    if old:
        bakeuv=n.new('ShaderNodeUVMap');bakeuv.uv_map=old
        for node in list(n):
            if node.type=='TEX_IMAGE' and not node.inputs['Vector'].is_linked:l.new(bakeuv.outputs[0],node.inputs['Vector'])
    original=s.inputs['Base Color'].links[0].from_socket
    coord=n.new('ShaderNodeUVMap');coord.uv_map='PaintingProjection'
    image=n.new('ShaderNodeTexImage');image.image=tex;image.extension='CLIP';l.new(coord.outputs[0],image.inputs['Vector'])
    confidence=n.new('ShaderNodeVertexColor');confidence.layer_name='Paint confidence'
    mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(confidence.outputs['Color'],mask.inputs[0]);l.new(image.outputs['Alpha'],mask.inputs[1])
    strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.90 if name in major else .55;l.new(mask.outputs[0],strength.inputs[0])
    blend=n.new('ShaderNodeMixRGB');l.new(strength.outputs[0],blend.inputs[0]);l.new(original,blend.inputs[1]);l.new(image.outputs['Color'],blend.inputs[2]);l.new(blend.outputs[0],s.inputs['Base Color'])
    s.inputs['Roughness'].default_value=.78;s.inputs['Metallic'].default_value=.18
    # The painting already contains hand-painted light. A partial emission mix retains
    # that brushwork while the physical BSDF still supplies grain, edge glints and relief.
    output=next(node for node in n if node.type=='OUTPUT_MATERIAL')
    emission=n.new('ShaderNodeEmission');l.new(blend.outputs[0],emission.inputs['Color'])
    keep=n.new('ShaderNodeMath');keep.operation='MULTIPLY';keep.inputs[1].default_value=.45;l.new(mask.outputs[0],keep.inputs[0])
    surface=n.new('ShaderNodeMixShader');l.new(keep.outputs[0],surface.inputs[0]);l.new(s.outputs[0],surface.inputs[1]);l.new(emission.outputs[0],surface.inputs[2]);l.new(surface.outputs[0],output.inputs['Surface'])
    records.append({'mesh':name,'uv':'PaintingProjection','hidden_fill':'original procedural olive + scanned steel','strength':strength.inputs[1].default_value})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'tank.blend'))
(M/'textures/paint-manifest.json').write_text(json.dumps(records,indent=2));print('PROJECTED',len(records),'real meshes, with hidden-surface fallback')
