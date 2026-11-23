"""Reuse spearman CC0 scanned surfaces, with pigment and scale suited to artillery."""
import bpy,os
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/field-cannon';A=R/'assets'
bpy.ops.wm.open_mainfile(filepath=str(M/'field-cannon-plain.blend'))
def surface(name,folder,files,tint,scale,bump=.10):
 m=bpy.data.materials[name];n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF')
 tc=n.new('ShaderNodeTexCoord');mp=n.new('ShaderNodeVectorMath');mp.operation='SCALE';mp.inputs[3].default_value=scale;l.new(tc.outputs['Generated'],mp.inputs[0])
 def tex(file):
  t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(A/folder/file),check_existing=True);t.projection='BOX';t.projection_blend=.25;l.new(mp.outputs[0],t.inputs['Vector']);return t
 t=tex(files[0]);bw=n.new('ShaderNodeRGBToBW');l.new(t.outputs[0],bw.inputs[0]);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.08;r.color_ramp.elements[0].color=(*[c*.55 for c in tint],1);r.color_ramp.elements[1].position=.78;r.color_ramp.elements[1].color=(*tint,1);l.new(bw.outputs[0],r.inputs[0])
 ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.055;mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=.38;l.new(r.outputs[0],mul.inputs[1]);l.new(ao.outputs['Color'],mul.inputs[2]);l.new(mul.outputs[0],s.inputs['Base Color'])
 height=tex(files[1]);height.image.colorspace_settings.name='Non-Color';b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=bump;b.inputs['Distance'].default_value=.003;l.new(height.outputs[0],b.inputs['Height']);l.new(b.outputs[0],s.inputs['Normal'])
 # Micro roughness plus deliberately restrained broad variation.
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=12;noise.inputs['Detail'].default_value=3
 rm=n.new('ShaderNodeMapRange');rough=s.inputs['Roughness'].default_value;rm.inputs['To Min'].default_value=max(.25,rough-.10);rm.inputs['To Max'].default_value=min(1,rough+.14);l.new(noise.outputs['Fac'],rm.inputs[0]);l.new(rm.outputs[0],s.inputs['Roughness'])
 return m
for name,tint in [('Siege aged bronze',(.60,.39,.14)),('Siege bright worn bronze',(.84,.58,.24)),('Siege dark forged iron',(.19,.20,.18)),('Siege iron arris',(.36,.37,.34))]:surface(name,'Metal034',['Metal034_1K-JPG_Color.jpg','Metal034_1K-JPG_Displacement.jpg'],tint,3,.20)
for name,tint in [('Siege indigo wool',(.045,.085,.16)),('Siege vermilion facings',(.50,.055,.025)),('Siege ivory linen',(.88,.80,.63))]:surface(name,'Fabric030',['Fabric030_1K-JPG_Color.jpg','Fabric030_1K-JPG_Displacement.jpg'],tint,7,.14)
for name,tint in [('Siege olive painted oak',(.24,.25,.13)),('Siege exposed oak',(.38,.23,.10))]:surface(name,'fine_grained_wood',['diff.jpg','rough.jpg'],tint,2,.14)
surface('Siege black boot leather','brown_leather',['diff.jpg','rough.jpg'],(.07,.061,.043),3,.14)
surface('Siege cream limestone','Travertine001',['Travertine001_1K-JPG_Color.jpg','Travertine001_1K-JPG_Displacement.jpg'],(.91,.79,.58),4,.06)
m=bpy.data.materials['Siege cream limestone'];p=m.node_tree.nodes.get('Principled BSDF')
for l in list(p.inputs['Base Color'].links):m.node_tree.links.remove(l)
p.inputs['Base Color'].default_value=(.95,.70,.32,1)
m=bpy.data.materials['Siege painted warm skin'];n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(R/'blender-user/extensions/.user/user_default/mpfb/data/skins/young_caucasian_male2/young_lightskinned_male_diffuse2.png'),check_existing=True);l.new(t.outputs[0],p.inputs['Base Color']);p.inputs['Subsurface Weight'].default_value=.055;p.inputs['Specular IOR Level'].default_value=.22
# Broad pigment modulation survives 256 px; scan grain alone reads as smooth plastic.
for name,lo,hi,scale in [
 ('Siege aged bronze',(.085,.045,.015),(.43,.27,.085),17),
 ('Siege olive painted oak',(.095,.105,.047),(.30,.30,.14),10),
 ('Siege indigo wool',(.014,.028,.058),(.065,.115,.21),18),
 ('Siege ivory linen',(.40,.34,.23),(.87,.80,.65),22)]:
 m=bpy.data.materials[name];n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 old=p.inputs['Base Color'].links[0].from_socket;noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=3;noise.inputs['Roughness'].default_value=.75
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[0].color=(*lo,1);ramp.color_ramp.elements[1].position=.78;ramp.color_ramp.elements[1].color=(*hi,1);l.new(noise.outputs['Fac'],ramp.inputs[0])
 mix=n.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.55;l.new(old,mix.inputs[1]);l.new(ramp.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
# Warm painted skin, with low-frequency variation rather than a grey photographic hand.
m=bpy.data.materials['Siege painted warm skin'];n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=20;noise.inputs['Detail'].default_value=2
palette=n.new('ShaderNodeValToRGB');palette.color_ramp.elements[0].color=(.28,.115,.045,1);palette.color_ramp.elements[1].color=(.71,.43,.22,1);l.new(noise.outputs['Fac'],palette.inputs[0])
ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.025
mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.55;l.new(palette.outputs[0],mix.inputs[1]);l.new(ao.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
# Original image-generated painted wool supplies back and motion-revealed cloth.
cloth=R/'assets/field-cannon/painted-navy-wool.png'
if cloth.exists():
 m=bpy.data.materials['Siege indigo wool'];n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 old=p.inputs['Base Color'].links[0].from_socket;tc=n.new('ShaderNodeTexCoord');scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=2.5;l.new(tc.outputs['Generated'],scale.inputs[0]);tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(cloth),check_existing=True);tex.projection='BOX';tex.projection_blend=.35;l.new(scale.outputs[0],tex.inputs[0])
 mix=n.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.70;l.new(old,mix.inputs[1]);l.new(tex.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
p=bpy.data.materials['Siege aged bronze'].node_tree.nodes.get('Principled BSDF');p.inputs['Metallic'].default_value=.38
for link in list(p.inputs['Roughness'].links):p.id_data.links.remove(link)
p.inputs['Roughness'].default_value=.60
bpy.context.scene['material_sources']='Existing licensed CC0 Metal034, Fabric030, Travertine001, brown_leather, fine_grained_wood; MakeHuman CC0 skin'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'field-cannon.blend'))
