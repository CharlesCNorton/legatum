"""Fitted linen armour and lambda aspis; preserves the shared anatomical rig."""
import bpy, os, json, math, ast
from pathlib import Path
from mathutils import Vector, Matrix
M=Path(os.environ['ANIM_MASTER'])
bpy.ops.wm.open_mainfile(filepath=str(M/'spearman.blend'))
sc=bpy.context.scene;rig=bpy.data.objects['Spearman • MPFB game_engine']
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'mesh','curve','solid','bevel','attach','material','sphere'}:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared geometry>','exec'))
linen=bpy.data.materials['Warm ivory linen'];red=bpy.data.materials['Cinnabar wool'];gold=bpy.data.materials['Bronze • polished edges'];leather=bpy.data.materials['Oxide leather']
# Sculpted muscle armour is wrong for this painting. Retain a closed fitted shell,
# smooth the abdominal embossing, and dress it in layered linen with bound seams.
chest=bpy.data.objects['Forged bronze muscle cuirass'];chest.data.materials.clear();chest.data.materials.append(linen)
for v in chest.data.vertices:
 if v.co.y<-.04:
  v.co.y=.7*v.co.y-.3*.158
for ob in list(sc.objects):
 if ob.name.startswith(('Pectoral','Chased cuirass','Cuirass rolled','Cuirass waist','Sunburst','Aspis central','Aspis rim stud','Aspis chased','Crimson collar')):
  bpy.data.objects.remove(ob,do_unlink=True)
# Outer aspis has the painting's painted ivory face and broad bronze border.
import runpy
runpy.run_path('tools/art/anim3d/units/spartan-hoplite/shield_normals.py')['repair']()
shield=bpy.data.objects['Convex bronze aspis'];shield.data.materials.clear();shield.data.materials.append(linen)
# Remove inner boss ring; restore a plain continuous face.
for ob in list(sc.objects):
 if ob.name.startswith('Aspis turned rim'):
  pts=[Vector(p.co[:3]) for p in ob.data.splines[0].points]
  if max(p.x for p in pts)-min(p.x for p in pts)<.3:bpy.data.objects.remove(ob,do_unlink=True)
bpy.context.view_layer.update()
center=Vector((.30,-.38,1.19));rad=.395
# The lambda is painted onto the convex aspis by paint.py, as in the reference.
# Keep the convex face ahead of the curled fingers, with a real grip gap.
for ob in bpy.data.objects['Aspis control'].children:
 if ob.type not in {'MESH','CURVE'}:continue
 points=ob.data.vertices if ob.type=='MESH' else [p for sp in ob.data.splines for p in sp.points]
 for p in points:p.co.y-=.075
 ob.data['hoplite_grip_clearance']=True
# Linen armour seams, leather binding and bronze buckles are geometry.
for x in [-.16,.16]:
 attach(curve('Linen armour bound seam',[(x,-.162,1.15),(x,-.18,1.36),(x*.8,-.14,1.49)],.005,leather),'spine_03')
for z in [1.13,1.16]:attach(curve('Narrow linen belt',[(.205*math.sin(a),-.17*math.cos(a),z) for a in [i*math.tau/96 for i in range(97)]],.009,leather),'spine_01')
for x in [-.145,.145]:
 attach(curve('Bronze shoulder buckle',[(x-.016,-.183,1.42),(x+.016,-.183,1.42),(x+.016,-.183,1.46),(x-.016,-.183,1.46),(x-.016,-.183,1.42)],.004,gold),'spine_03')
for ob in list(sc.objects):
 if ob.name.startswith('Linen pteruges'):
  # The red hem on each separate ivory flap is visible at token scale.
  vs=[v.co for v in ob.data.vertices]
  attach(curve('Pteruges red hem',[(v.x,v.y-.002,v.z+.018) for v in vs[-3:]],.008,red),'pelvis')
# Red draped mantle across both shoulders, with actual layered folds and thickness.
vs=[];fs=[]
for j in range(13):
 t=j/12
 for i in range(41):
  u=i/40;x=-.22+.51*u;y=-.16-.055*math.sin(math.pi*u)-.008*math.sin((t+.27*u)*math.pi*5)
  z=1.62-.17*t-.15*u-.025*math.sin(math.pi*u)
  vs.append((x,y,z))
for j in range(12):
 for i in range(40):a=j*41+i;fs.append((a,a+41,a+42,a+1))
mantle=solid(mesh('Crimson shoulder mantle folds',vs,fs,red),.006);mantle.data['hoplite_mantle_front']=True;bevel(mantle,.002);attach(mantle,'spine_03')
# Cloth remains simulated; folds begin broad and the hem flares behind both calves.
for ob in sc.objects:
 if ob.name.startswith('Cloak clasp'):ob.location.y-=.05
# Camera and lighting follow the painted miniature, with subdued fill and cool rim.
sc.camera.location=(2.5,-7,2.8);sc.camera.rotation_euler=(Vector((0,0,1.13))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=2.52
bpy.data.objects['Warm upper-left key'].data.energy=700
bpy.data.objects['Soft cool fill'].data.energy=180
rim=bpy.data.objects['Warm back rim'];rim.data.color=(.72,.84,1);rim.data.energy=400
# Match the painting's head-to-spear proportion instead of a towering pike.
for ob in sc.objects:
 if ob.name.startswith(('Ash dory shaft','Spear bronze ferrule','Leaf spearhead')):
  points=ob.data.vertices if ob.type=='MESH' else [p for sp in ob.data.splines for p in sp.points]
  for p in points:
   if p.co.z>1.30:p.co.z=1.30+(p.co.z-1.30)*.72
 if ob.name.startswith('Linen tunic shoulder sleeves'):ob.hide_render=True
base=bpy.data.objects['Stationary cream stone'];base.scale.x=base.scale.y=.90
head=rig.pose.bones['head'];pos=head.matrix.translation.copy();mat=Matrix.Rotation(1.90,4,'Z')@head.matrix;mat.translation=pos;head.matrix=mat
bpy.context.view_layer.update()
rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})
sc['unit']='spartan-hoplite';sc['round']=1
bpy.ops.wm.save_as_mainfile(filepath=str(M/'spearman.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
