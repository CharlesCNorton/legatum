"""Task-owned miniature finish: aged surfaces, shared cream, directional softboxes."""
import bpy
import os
from pathlib import Path

M = Path(os.environ['ANIM_ROOT']) / 'masters/field-cannon'
bpy.ops.wm.open_mainfile(filepath=str(M / 'field-cannon.blend'))

def srgb(hex_value):
    rgb = [int(hex_value[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb) + (1,)

for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    p = nodes.get('Principled BSDF')
    if not p:
        continue
    if mat.name.startswith(('Siege aged bronze', 'Siege bright worn bronze', 'Siege dark forged iron', 'Siege iron arris')):
        p.inputs['Metallic'].default_value = 1.0
    if mat.name.startswith('Siege aged bronze'):
        old = p.inputs['Base Color'].links[0].from_socket
        noise = nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 8
        noise.inputs['Detail'].default_value = 4; noise.inputs['Roughness'].default_value = .8
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = .25
        ramp.color_ramp.elements[0].color = (.13, .16, .105, 1)
        ramp.color_ramp.elements[1].position = .8
        ramp.color_ramp.elements[1].color = (.68, .60, .39, 1)
        links.new(noise.outputs['Fac'], ramp.inputs[0])
        mix = nodes.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = .85
        links.new(old, mix.inputs[1]); links.new(ramp.outputs[0], mix.inputs[2]); links.new(mix.outputs[0], p.inputs['Base Color'])
        rough = nodes.new('ShaderNodeMapRange'); rough.inputs['To Min'].default_value = .48; rough.inputs['To Max'].default_value = .83
        links.new(noise.outputs['Fac'], rough.inputs[0]); links.new(rough.outputs[0], p.inputs['Roughness'])
    if mat.name.startswith(('Siege indigo wool', 'Siege ivory linen', 'Siege vermilion facings')):
        p.inputs['Sheen Weight'].default_value = .28; p.inputs['Sheen Roughness'].default_value = .65
        p.inputs['Specular IOR Level'].default_value = .25

# The same sRGB palette is shared across leads; convert to linear before shading.
base = bpy.data.objects['Stationary cream base']
stone = bpy.data.materials['Siege cream limestone']
p = stone.node_tree.nodes.get('Principled BSDF')
for link in list(p.inputs['Base Color'].links):
    stone.node_tree.links.remove(link)
p.inputs['Base Color'].default_value = srgb('E9CFA0')
stone['palette_srgb'] = '#E9CFA0'
rim = stone.copy(); rim.name = 'Siege cream limestone darker rim'
rim.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = srgb('BA9968')
rim['palette_srgb'] = '#BA9968'
base.data.materials.append(rim)
for face in base.data.polygons:
    face.material_index = 0 if face.normal.z > .5 else 1

# Distinct neutral iron tyres: broad scuffed steel patches, not olive reflected wood.
for obj in bpy.data.objects:
    if not obj.name.startswith('Flat wrought iron tyre'):
        continue
    tyre = obj.data.materials[0].copy(); tyre.name = 'Siege worn iron tyre ' + obj.name
    obj.data.materials[0] = tyre
    nodes, links = tyre.node_tree.nodes, tyre.node_tree.links
    p = nodes.get('Principled BSDF')
    noise = nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 19
    noise.inputs['Detail'].default_value = 3; noise.inputs['Roughness'].default_value = .75
    palette = nodes.new('ShaderNodeValToRGB')
    palette.color_ramp.elements[0].position = .32; palette.color_ramp.elements[0].color = srgb('474C53')
    palette.color_ramp.elements[1].position = .70; palette.color_ramp.elements[1].color = srgb('A6A5A1')
    links.new(noise.outputs['Fac'], palette.inputs[0]); links.new(palette.outputs[0], p.inputs['Base Color'])
    roughness = nodes.new('ShaderNodeMapRange')
    roughness.inputs['To Min'].default_value = .48; roughness.inputs['To Max'].default_value = .82
    links.new(noise.outputs['Fac'], roughness.inputs[0]); links.new(roughness.outputs[0], p.inputs['Roughness'])

# Mouldings are worn bronze, not bright gold jewellery; buttons keep their glints.
aged = bpy.data.objects['Hollow bronze barrel'].data.materials[0]
for obj in bpy.data.objects:
    if obj.name.startswith(('Bronze turned moulding', 'Bronze wear scratch')):
        obj.data.materials[0] = aged

# Real porous wool sponge, separate from the deliberately unprojected cannon bore.
sponge = bpy.data.objects['Rammer sponge']
sponge_mat = bpy.data.materials['Siege black boot leather'].copy()
sponge_mat.name = 'Siege rammer charcoal wool'
sponge.data.materials[0] = sponge_mat
nodes, links = sponge_mat.node_tree.nodes, sponge_mat.node_tree.links
p = nodes.get('Principled BSDF')
p.inputs['Roughness'].default_value = .95
noise = nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 38
noise.inputs['Detail'].default_value = 3
bump = nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .7
bump.inputs['Distance'].default_value = .008
links.new(noise.outputs['Fac'], bump.inputs['Height']); links.new(bump.outputs[0], p.inputs['Normal'])

key = bpy.data.objects['Warm left key']; key.data.energy = 560
key.data.color = (1.0, .95, .86); key.data.size = 2.2
fill = bpy.data.objects['Cool fill']; fill.data.energy = 95; fill.data.size = 4
fill.data.color = (.88, .93, 1.0)
rim_light = bpy.data.objects['Gold rim']; rim_light.data.color = (.80, .89, 1.0)
rim_light.data.energy = 150; rim_light.data.size = 2.5
sc = bpy.context.scene
sc.view_settings.exposure = .35
sc['finish_skills'] = 'All six Blender skills: thick folded cloth, bevels, metal roughness/patina, product softboxes, fixed orthographic camera, authored MPFB poses, AgX/denoised PNG masters'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(M / 'field-cannon.blend'))
print('SIEGE_FINISH_READY')
