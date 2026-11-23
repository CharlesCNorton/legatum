"""Reuse infantry CC0 scan mapping; add bay pigment, linen and worn bronze."""
import bpy,os,ast
from pathlib import Path
ROOT=Path(os.environ['ANIM_ROOT']);A=ROOT/'assets';M=ROOT/'masters/horseman-3d'
bpy.ops.wm.open_mainfile(filepath=str(M/'horseman.blend'))
for node in ast.parse(Path('tools/art/anim3d/materials.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='pbr':exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared PBR>','exec'))
for name in ['Bronze • hammered','Bronze • polished edges']:
 pbr(name,'Metal034',['Metal034_1K-JPG_Color.jpg','Metal034_1K-JPG_Roughness.jpg','Metal034_1K-JPG_Displacement.jpg'],(.72,.43,.14) if 'polished' in name else (.48,.25,.065),(.3,.58),2.5,.22)
pbr('Warm ivory linen','Fabric030',['Fabric030_1K-JPG_Color.jpg','Fabric030_1K-JPG_Roughness.jpg','Fabric030_1K-JPG_Displacement.jpg'],(.95,.88,.73),(.75,.95),6,.22)
pbr('Oxide leather','brown_leather',['diff.jpg','rough.jpg','nor_gl.jpg'],(.20,.076,.026),(.52,.8),3,.14)
pbr('Ash spear shaft','fine_grained_wood',['diff.jpg','rough.jpg','nor_gl.jpg'],(.32,.16,.055),(.45,.68),3,.1)
pbr('Cream limestone','Travertine001',['Travertine001_1K-JPG_Color.jpg','Travertine001_1K-JPG_Roughness.jpg','Travertine001_1K-JPG_Displacement.jpg'],(.94,.82,.63),(.7,.95),4,.08)
def pigment(name,low,high,scale=8,bump=.07):
 m=bpy.data.materials[name];n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF')
 tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.18;ramp.color_ramp.elements[0].color=(*low,1);ramp.color_ramp.elements[1].position=.82;ramp.color_ramp.elements[1].color=(*high,1);l.new(tex.outputs['Fac'],ramp.inputs[0])
 ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.09
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.6;l.new(ramp.outputs[0],mix.inputs[1]);l.new(ao.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
 micro=n.new('ShaderNodeTexNoise');micro.inputs['Scale'].default_value=170;micro.inputs['Detail'].default_value=2
 bn=n.new('ShaderNodeBump');bn.inputs['Strength'].default_value=bump;bn.inputs['Distance'].default_value=.002;l.new(micro.outputs['Fac'],bn.inputs['Height']);l.new(bn.outputs[0],s.inputs['Normal'])
pigment('Bay coat',(.16,.043,.012),(.39,.14,.042),7)
pigment('Bay shaded muscle',(.105,.026,.008),(.25,.071,.018),9)
pigment('Bay warm highlights',(.25,.077,.02),(.48,.20,.065),7)
pigment('Black mane and tail',(.009,.007,.006),(.042,.032,.023),20,.2)
pigment('Cream limestone',(.69,.54,.33),(.90,.77,.56),35,.1)
pigment('Bronze • hammered',(.19,.085,.022),(.65,.37,.10),13,.19)
pigment('Bronze • polished edges',(.48,.23,.05),(.93,.65,.26),26,.1)
# Painted hide is satin, not a lacquered plastic surface.
for name in ['Bay coat','Bay shaded muscle','Bay warm highlights','Black mane and tail']:
 s=bpy.data.materials[name].node_tree.nodes.get('Principled BSDF');s.inputs['Roughness'].default_value=.66;s.inputs['Specular IOR Level'].default_value=.19
# Original CC0 MakeHuman skin, on its native UVs.
m=bpy.data.materials['Skin • warm ochre'];n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF')
t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ROOT/'blender-user/extensions/.user/user_default/mpfb/data/skins/young_caucasian_male2/young_lightskinned_male_diffuse2.png'),check_existing=True);l.new(t.outputs[0],s.inputs['Base Color']);s.inputs['Subsurface Weight'].default_value=.045;s.inputs['Roughness'].default_value=.63
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'horseman.blend'))
