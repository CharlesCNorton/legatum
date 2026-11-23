"""Painted surface fills with CC0 weave/grain and physical material response."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
bpy.ops.wm.open_mainfile(filepath=str(MASTER/'archer-plain.blend'))
for m in list(bpy.data.materials):
 if not m.name.startswith('MAT-'):continue
 n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=75;noise.inputs['Detail'].default_value=3;l.new(tc.outputs['Generated'],noise.inputs['Vector'])
 b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.18;b.inputs['Distance'].default_value=.0015;l.new(noise.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],s.inputs['Normal'])
 base=s.inputs['Base Color'].default_value[:];ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*[v*.65 for v in base[:3]],1);ramp.color_ramp.elements[1].color=(*[min(1,v*1.18) for v in base[:3]],1);l.new(noise.outputs['Fac'],ramp.inputs[0]);color=ramp.outputs[0]
 kind='linen' if 'linen' in m.name else 'bronze' if 'bronze' in m.name else 'coat' if 'leather' in m.name else None
 if kind:
  tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ASSETS/f'fill-{kind}.png'),check_existing=True);tex.projection='BOX';tex.projection_blend=.35;l.new(tc.outputs['Generated'],tex.inputs['Vector']);mix=n.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.35;l.new(color,mix.inputs[1]);l.new(tex.outputs['Color'],mix.inputs[2]);color=mix.outputs[0]
 if 'linen' in m.name or 'indigo' in m.name:
  tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'assets/Fabric030/Fabric030_1K-JPG_Displacement.jpg'),check_existing=True);tex.image.colorspace_settings.name='Non-Color';tex.projection='BOX';tex.projection_blend=.2;scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=7;l.new(tc.outputs['Generated'],scale.inputs[0]);l.new(scale.outputs[0],tex.inputs['Vector']);l.new(tex.outputs['Color'],b.inputs['Height']);s.inputs['Sheen Weight'].default_value=.22
 if m.name=='MAT-skin':
  tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'blender-user/extensions/.user/user_default/mpfb/data/skins/young_caucasian_male2/young_lightskinned_male_diffuse2.png'),check_existing=True);color=tex.outputs[0];s.inputs['Subsurface Weight'].default_value=.04;s.inputs['Specular IOR Level'].default_value=.22
 if 'cream' in m.name:
  color=None;s.inputs['Base Color'].default_value=base
 if color:
  ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.045;mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.55;l.new(color,mix.inputs[1]);l.new(ao.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
save(MASTER/'archer-unpainted.blend');save(MASTER/'archer.blend');log('- Applied generated painted fills, CC0 linen weave, skin map, cavity shading and warm cream base.')
