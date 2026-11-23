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
light=bpy.data.images.load(str(M/'textures/painting-light.png'),check_existing=True)
# This frame follows hull suspension, but never wheel spin. Object coordinates
# supply the same orthographic UV field as PaintingProjection at rest.
frame=bpy.data.objects.new('Wheel illumination frame',None)
sc.collection.objects.link(frame)
frame.matrix_world=sc.camera.matrix_world.copy()
frame.parent=bpy.data.objects['Vehicle suspension root']
frame.matrix_parent_inverse=frame.parent.matrix_world.inverted()
view=sc.camera.rotation_euler.to_matrix() @ Vector((0,0,1))
records=[]
# Track shoes pass through many rest-screen positions. Their own physical steel
# texture must travel with them; camera paint would carry whole wheel/bogie
# fragments around the belt. Recesses/spokes also retain their physical finish.
rotating_fill=('Forged track shoe','Polished raised grouser','Track hinge pin',
               'Wheel recessed aperture','Wheel radial spoke','Sprocket tooth','Sprocket recess')
names=[o.name for o in bpy.data.objects if o.type=='MESH' and 'effect' not in o
       and not o.name.startswith(rotating_fill)]
materials={}
for name in names:
    o=bpy.data.objects[name];mesh=o.data;old=mesh.uv_layers.active.name if mesh.uv_layers.active else None
    if 'PaintingProjection' in mesh.uv_layers:raise RuntimeError('Projection already applied; bake again before paint')
    uv=mesh.uv_layers.new(name='PaintingProjection');weights=mesh.color_attributes.new(name='Paint confidence',type='FLOAT_COLOR',domain='CORNER')
    normalmatrix=o.matrix_world.to_3x3().inverted().transposed()
    shift=Vector((0,0))
    for loop in mesh.loops:
        v=mesh.vertices[loop.vertex_index];p=world_to_camera_view(sc,sc.camera,o.matrix_world @ v.co)
        uv.data[loop.index].uv=Vector((p.x,p.y))+shift
        facing=max(0,min(1,((normalmatrix @ v.normal).normalized().dot(view)+.08)/.08))
        weights.data[loop.index].color=(facing,facing,facing,1)
    original_material=o.data.materials[0]
    wheel=bool(o.parent and 'wheel' in o.parent)
    material_key=(original_material.name,wheel)
    if material_key in materials:
        o.data.materials.clear();o.data.materials.append(materials[material_key]);continue
    mat=original_material.copy();mat.name=original_material.name+' • painted projection'
    materials[material_key]=mat
    o.data.materials.clear();o.data.materials.append(mat)
    n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
    if old:
        bakeuv=n.new('ShaderNodeUVMap');bakeuv.uv_map=old
        for node in list(n):
            if node.type=='TEX_IMAGE' and not node.inputs['Vector'].is_linked:l.new(bakeuv.outputs[0],node.inputs['Vector'])
    original=s.inputs['Base Color'].links[0].from_socket
    coord=n.new('ShaderNodeUVMap');coord.uv_map='PaintingProjection'
    image=n.new('ShaderNodeTexImage');image.image=tex;image.extension='CLIP';l.new(coord.outputs[0],image.inputs['Vector'])
    pigment=image.outputs['Color']
    if wheel:
        moving=n.new('ShaderNodeTexImage');moving.image=light;moving.name='Wheel rotating broad light'
        l.new(coord.outputs[0],moving.inputs['Vector'])
        fixed=n.new('ShaderNodeTexCoord');fixed.object=frame
        scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=1/sc.camera.data.ortho_scale
        l.new(fixed.outputs['Object'],scale.inputs[0])
        offset=n.new('ShaderNodeVectorMath');offset.operation='ADD';offset.inputs[1].default_value=(.5,.5,0)
        l.new(scale.outputs[0],offset.inputs[0])
        stationary=n.new('ShaderNodeTexImage');stationary.image=light;stationary.name='Wheel stationary broad light'
        l.new(offset.outputs[0],stationary.inputs['Vector'])
        floor=n.new('ShaderNodeVectorMath');floor.operation='MAXIMUM';floor.inputs[1].default_value=(.018,)*3
        l.new(moving.outputs['Color'],floor.inputs[0])
        ratio=n.new('ShaderNodeVectorMath');ratio.operation='DIVIDE'
        l.new(stationary.outputs['Color'],ratio.inputs[0]);l.new(floor.outputs[0],ratio.inputs[1])
        low=n.new('ShaderNodeVectorMath');low.operation='MAXIMUM';low.inputs[1].default_value=(.6,)*3;l.new(ratio.outputs[0],low.inputs[0])
        high=n.new('ShaderNodeVectorMath');high.operation='MINIMUM';high.inputs[1].default_value=(1.65,)*3;l.new(low.outputs[0],high.inputs[0])
        corrected=n.new('ShaderNodeVectorMath');corrected.operation='MULTIPLY'
        l.new(image.outputs['Color'],corrected.inputs[0]);l.new(high.outputs[0],corrected.inputs[1]);pigment=corrected.outputs[0]
        mat['wheel_light_separated']=True
    confidence=n.new('ShaderNodeVertexColor');confidence.layer_name='Paint confidence'
    mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(confidence.outputs['Color'],mask.inputs[0]);l.new(image.outputs['Alpha'],mask.inputs[1])
    strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.98;l.new(mask.outputs[0],strength.inputs[0])
    blend=n.new('ShaderNodeMixRGB');l.new(strength.outputs[0],blend.inputs[0]);l.new(original,blend.inputs[1]);l.new(pigment,blend.inputs[2]);l.new(blend.outputs[0],s.inputs['Base Color'])
    s.inputs['Roughness'].default_value=.78;s.inputs['Metallic'].default_value=0
    # The painting already contains hand-painted light. A partial emission mix retains
    # that brushwork while the physical BSDF still supplies grain, edge glints and relief.
    output=next(node for node in n if node.type=='OUTPUT_MATERIAL')
    emission=n.new('ShaderNodeEmission');l.new(blend.outputs[0],emission.inputs['Color'])
    keep=n.new('ShaderNodeMath');keep.operation='MULTIPLY';keep.inputs[1].default_value=.96;camera=n.new('ShaderNodeLightPath')
    camera_mask=n.new('ShaderNodeMath');camera_mask.operation='MULTIPLY';l.new(mask.outputs[0],camera_mask.inputs[0]);l.new(camera.outputs['Is Camera Ray'],camera_mask.inputs[1]);l.new(camera_mask.outputs[0],keep.inputs[0])
    surface=n.new('ShaderNodeMixShader');l.new(keep.outputs[0],surface.inputs[0]);l.new(s.outputs[0],surface.inputs[1]);l.new(emission.outputs[0],surface.inputs[2]);l.new(surface.outputs[0],output.inputs['Surface'])
    records.append({'mesh':name,'uv':'PaintingProjection','hidden_fill':'generated olive brushwork + scanned steel; procedural stone and rubber','strength':strength.inputs[1].default_value})
# Moving shoes use their own dusty metal pigment, never wheel/bogie fragments.
# Camera-only pigment opens the dark steel without illuminating the hull/base.
for material_name in ('Track steel • worn and earth packed', 'Dusty rubbed edges'):
    mat=bpy.data.materials[material_name];n=mat.node_tree.nodes;l=mat.node_tree.links
    shader=n.get('Principled BSDF');output=next(node for node in n if node.type=='OUTPUT_MATERIAL')
    emission=n.new('ShaderNodeEmission');l.new(shader.inputs['Base Color'].links[0].from_socket,emission.inputs['Color'])
    lightpath=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.40
    l.new(lightpath.outputs['Is Camera Ray'],weight.inputs[0])
    mix=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],mix.inputs[0]);l.new(shader.outputs[0],mix.inputs[1]);l.new(emission.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],output.inputs['Surface'])
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'tank.blend'))
(M/'textures/paint-manifest.json').write_text(json.dumps(records,indent=2));print('PROJECTED',len(names),'real meshes, with hidden-surface fallback')
