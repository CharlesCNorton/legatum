"""Small repeatable finish pass; applies identically to master and baked clips."""
import bpy,os,sys,math
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
  mat=bpy.data.materials.new('Horsehair painted ridge');mat.diffuse_color=(.68,.065,.018,1);mat.use_nodes=True
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
 if not sc.get('finish_v2'):
  # A real wide leather belt closes the gap between cuirass and pteruges.
  rig=bpy.data.objects['Spearman • MPFB game_engine']
  def attach(ob):
   bpy.context.view_layer.update();world=ob.matrix_world.copy()
   ob.parent=rig;ob.parent_type='BONE';ob.parent_bone='spine_01'
   bpy.context.view_layer.update();ob.matrix_world=world
  verts=[];faces=[]
  for j in range(2):
   for i in range(96):
    a=i*2*math.pi/96;verts.append((.215*math.sin(a),-.180*math.cos(a),1.045+.108*j))
  for i in range(96):nxt=(i+1)%96;faces.append((i,nxt,nxt+96,i+96))
  me=bpy.data.meshes.new('Wide waist belt');me.from_pydata(verts,[],faces);me.materials.append(bpy.data.materials['Oxide leather'])
  ob=bpy.data.objects.new('Wide waist belt',me);sc.collection.objects.link(ob)
  for poly in me.polygons:poly.use_smooth=True
  sol=ob.modifiers.new('Leather thickness','SOLIDIFY');sol.thickness=.006
  bevel=ob.modifiers.new('Worn belt edges','BEVEL');bevel.width=.003;bevel.segments=2;attach(ob)
  for i in range(9):
   a=-1.15+i*2.3/8
   bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,location=(.218*math.sin(a),-.184*math.cos(a),1.10))
   rivet=bpy.context.object;rivet.name='Waist belt bronze rivet';rivet.scale=(.005,.004,.005)
   rivet.data.materials.append(bpy.data.materials['Bronze • polished edges']);attach(rivet)
  for mat in bpy.data.materials:
   if not mat.name.startswith('Bronze •'):continue
   n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
   # Retain the baked curvature polish, vary its roughness at visible hammer scale.
   old=s.inputs['Roughness'].links[0].from_socket
   tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=65;tex.inputs['Detail'].default_value=3
   remap=n.new('ShaderNodeMapRange');remap.inputs['To Min'].default_value=-.03;remap.inputs['To Max'].default_value=.12
   add=n.new('ShaderNodeMath');add.operation='ADD'
   l.new(tex.outputs['Fac'],remap.inputs[0]);l.new(old,add.inputs[0]);l.new(remap.outputs[0],add.inputs[1]);l.new(add.outputs[0],s.inputs['Roughness'])
   for node in n:
    if node.type=='BUMP' and abs(node.inputs['Distance'].default_value-.003)<.00001:node.inputs['Strength'].default_value=.24
  sc['finish_v2']=True
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
