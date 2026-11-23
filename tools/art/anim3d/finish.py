"""Small repeatable finish pass; applies identically to master and baked clips."""
import bpy,os,sys
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/spearman-3d-v2'
paths=sorted((M/'clips').glob('*/*.blend')) if '--clips' in sys.argv else [M/'spearman.blend']
for path in paths:
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
 if not sc.get('finish_v1'):
  # Existing saved masters precede the collar height correction in scene.py.
  # The data's actual minimum height determines whether correction is necessary.
  for ob in sc.objects:
   if ob.name.startswith('Crimson collar fold'):
    for sp in ob.data.splines:
     if min(p.co.z for p in sp.points)<1.50:
      for p in sp.points:p.co.z+=.10
  mat=bpy.data.materials.new('Horsehair painted ridge');mat.diffuse_color=(.47,.065,.018,1);mat.use_nodes=True
  shader=mat.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=mat.diffuse_color;shader.inputs['Roughness'].default_value=.82
  tufts=sorted([o for o in sc.objects if o.name.startswith('Horsehair crest tuft')],key=lambda o:o.name)
  for tuft in tufts[::2]:
   curve=bpy.data.curves.new('Horsehair ridge','CURVE');curve.dimensions='3D';curve.bevel_depth=.0013;curve.bevel_resolution=1
   sp=curve.splines.new('POLY');sp.points.add(1)
   for p,v in zip(sp.points,[tuft.data.vertices[0].co,tuft.data.vertices[3].co]):p.co=(*v,1)
   ob=bpy.data.objects.new('Horsehair painted fibre',curve);bpy.context.collection.objects.link(ob);curve.materials.append(mat)
   ob.parent=tuft.parent;ob.parent_type=tuft.parent_type;ob.parent_bone=tuft.parent_bone;ob.matrix_parent_inverse=tuft.matrix_parent_inverse;ob.matrix_basis=tuft.matrix_basis
  for mat in bpy.data.materials:
   if not mat.use_nodes:continue
   for n in mat.node_tree.nodes:
    if n.type=='VALTORGB' and len(n.color_ramp.elements)==3:
     es=n.color_ramp.elements
     if abs(es[0].position-.23)<.001 and es[1].color[0]<.5:
      for e,col in zip(es,[(.22,.09,.018,1),(.43,.205,.055,1),(.66,.37,.12,1)]):e.color=col
  sc['finish_v1']=True
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
