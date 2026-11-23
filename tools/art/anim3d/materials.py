"""CC0 PBR with bright worn bronze, cavity contrast and pigment-grade cloth."""
import bpy,os
from pathlib import Path
ROOT=Path(os.environ['ANIM_ROOT']);A=ROOT/'assets';M=ROOT/'masters/spearman-3d-v2'
bpy.ops.wm.open_mainfile(filepath=str(M/'spearman.blend'))
def pbr(name, folder, maps, tint, roughrange, scale, bump=.1):
 m=bpy.data.materials[name];n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF')
 tc=n.new('ShaderNodeTexCoord');mp=n.new('ShaderNodeVectorMath');mp.operation='SCALE';mp.inputs[3].default_value=scale;l.new(tc.outputs['Generated'],mp.inputs[0])
 def tex(file,noncolor):
  t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(A/folder/file),check_existing=True)
  if noncolor:t.image.colorspace_settings.name='Non-Color'
  t.projection='BOX';t.projection_blend=.25;l.new(mp.outputs[0],t.inputs['Vector']);return t
 col=tex(maps[0],False)
 # Keep measured surface variation, grade pigment independently of original asset hue.
 bw=n.new('ShaderNodeRGBToBW');l.new(col.outputs['Color'],bw.inputs[0])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.05;ramp.color_ramp.elements[0].color=(*[v*.4 for v in tint],1)
 ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=(*tint,1)
 l.new(bw.outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],s.inputs['Base Color'])
 rough=tex(maps[1],True);rm=n.new('ShaderNodeMapRange');rm.inputs['To Min'].default_value=roughrange[0];rm.inputs['To Max'].default_value=roughrange[1]
 l.new(rough.outputs[0],rm.inputs[0]);l.new(rm.outputs[0],s.inputs['Roughness'])
 # Box-projected height works on code-built meshes without unreliable tangent UVs.
 texh=tex(maps[2],True);bn=n.new('ShaderNodeBump');bn.inputs['Strength'].default_value=bump;bn.inputs['Distance'].default_value=.008
 l.new(texh.outputs[0],bn.inputs['Height']);l.new(bn.outputs[0],s.inputs['Normal'])
 return m
for name in ['Bronze • hammered','Bronze • polished edges']:
 pbr(name,'Metal034',['Metal034_1K-JPG_Color.jpg','Metal034_1K-JPG_Roughness.jpg','Metal034_1K-JPG_Displacement.jpg'],(.58,.31,.085),(.27,.42),2.5,.16)
 m=bpy.data.materials[name];n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF')
 s.inputs['Metallic'].default_value=.82
 # Broad irregular patina survives downsampling; PBR microtexture alone does not.
 pigment=n.new('ShaderNodeTexNoise');pigment.inputs['Scale'].default_value=9;pigment.inputs['Detail'].default_value=4;pigment.inputs['Roughness'].default_value=.72
 palette=n.new('ShaderNodeValToRGB');palette.color_ramp.elements[0].position=.23;palette.color_ramp.elements[0].color=(.27,.115,.027,1)
 palette.color_ramp.elements[1].position=.77;palette.color_ramp.elements[1].color=(.83,.53,.19,1)
 mid=palette.color_ramp.elements.new(.5);mid.color=(.58,.31,.075,1)
 if 'polished' in name:
  palette.color_ramp.elements[0].color=(.68,.37,.09,1);mid.color=(.88,.60,.24,1);palette.color_ramp.elements[-1].color=(1,.79,.40,1)
 l.new(pigment.outputs['Fac'],palette.inputs[0]);l.new(palette.outputs[0],s.inputs['Base Color'])
 ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.06
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.8
 l.new(palette.outputs[0],mix.inputs[1]);l.new(ao.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=42;noise.inputs['Detail'].default_value=3
 b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.13;b.inputs['Distance'].default_value=.003
 old=s.inputs['Normal'].links[0].from_socket;l.new(old,b.inputs['Normal']);l.new(noise.outputs['Fac'],b.inputs['Height']);l.new(b.outputs['Normal'],s.inputs['Normal'])
for name,tint in [('Warm ivory linen',(.98,.91,.75)),('Cinnabar wool',(.56,.022,.008))]:
 pbr(name,'Fabric030',['Fabric030_1K-JPG_Color.jpg','Fabric030_1K-JPG_Roughness.jpg','Fabric030_1K-JPG_Displacement.jpg'],tint,(.75,.96),7,.22)
pbr('Oxide leather','brown_leather',['diff.jpg','rough.jpg','nor_gl.jpg'],(.23,.078,.025),(.52,.8),3,.12)
pbr('Ash spear shaft','fine_grained_wood',['diff.jpg','rough.jpg','nor_gl.jpg'],(.33,.15,.045),(.48,.74),3,.13)
pbr('Cream limestone','Travertine001',['Travertine001_1K-JPG_Color.jpg','Travertine001_1K-JPG_Roughness.jpg','Travertine001_1K-JPG_Displacement.jpg'],(.92,.80,.60),(.7,.95),4,.08)
# Keep stone warm cream; use the scanned grain at low contrast, not its grey albedo.
m=bpy.data.materials['Cream limestone'];n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF')
for link in list(s.inputs['Base Color'].links):l.remove(link)
s.inputs['Base Color'].default_value=(.85,.60,.30,1)
# Skin mottling, fine pores and restrained subsurface, no shiny coat.
m=bpy.data.materials['Skin • warm ochre'];n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF')
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=90;noise.inputs['Detail'].default_value=2
b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.14;b.inputs['Distance'].default_value=.0015;l.new(noise.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],s.inputs['Normal'])
skinmap=ROOT/'blender-user/extensions/.user/user_default/mpfb/data/skins/young_caucasian_male2/young_lightskinned_male_diffuse2.png'
t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(skinmap),check_existing=True)
paint=n.new('ShaderNodeMixRGB');paint.blend_type='MULTIPLY';paint.inputs[0].default_value=.25;paint.inputs[2].default_value=(.65,.40,.20,1)
l.new(t.outputs[0],paint.inputs[1]);l.new(paint.outputs[0],s.inputs['Base Color'])
s.inputs['Subsurface Weight'].default_value=.06;s.inputs['Specular IOR Level'].default_value=.25
bpy.context.scene['materials']='Poly Haven brown_leather/fine_grained_wood; ambientCG Metal034/Fabric030/Travertine001; CC0, pigment graded'
bpy.ops.file.pack_all()

base=bpy.data.objects['Stationary cream stone']
rim=bpy.data.materials['Cream limestone'].copy();rim.name='Cream limestone darker rim'
rim.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.62,.43,.22,1)
base.data.materials.append(rim)
for poly in base.data.polygons:poly.material_index=1 if abs(poly.normal.z)<.5 else 0
bpy.ops.wm.save_as_mainfile(filepath=str(M/'spearman.blend'))
