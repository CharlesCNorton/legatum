"""Map our original painted shield detail onto the actual convex 3D aspis."""
import bpy,os
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/spearman-3d-v2'
import sys
def paint(path):
 bpy.ops.wm.open_mainfile(filepath=str(path))
 obj=bpy.data.objects['Convex bronze aspis'];mat=obj.data.materials[0]
 # Coordinates in the original 1254px master: a calibrated unwarp of the convex shield.
 # UVs sample only the shield, not its surrounding figure or a cutout plane.
 image=bpy.data.images.load(str(M/'spearman-source.png'),check_existing=True)
 uv=obj.data.uv_layers.get('Painted shield') or obj.data.uv_layers.new(name='Painted shield')
 for loop in obj.data.loops:
  v=obj.data.vertices[loop.vertex_index].co
  u=(v.x-.30)/.395;w=(v.z-1.19)/.395
  bulge=max(0,1-u*u-w*w)
  px=785+123*u-19*w+36*bulge;py=694-186*w-u-11*bulge
  uv.data[loop.index].uv=(px/image.size[0],1-py/image.size[1])
 # Keep the existing unwrap active for the AO / curvature maps.
 obj.data.uv_layers.active_index=0
 for layer in obj.data.uv_layers:layer.active_render=(layer.name!=uv.name)
 if not bpy.context.scene.get('painted_shield'):
  n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
  coords=n.new('ShaderNodeUVMap');coords.uv_map=uv.name
  tex=n.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Linear';l.new(coords.outputs[0],tex.inputs['Vector'])
  # Moderate blend: retain physical patina/lighting, add source's engraved brushwork.
  old=s.inputs['Base Color'].links[0].from_socket
  mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[0].default_value=.18
  l.new(old,mix.inputs[1]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
 sc=bpy.context.scene;sc['painted_shield']='Own CC BY 4.0 spearman source, calibrated UV on convex mesh; PBR + source detail'
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path))
paths=sorted((M/'clips').glob('*/*.blend')) if '--clips' in sys.argv else [M/'spearman.blend']
for path in paths:paint(path)
