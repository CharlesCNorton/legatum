"""Unit-owned invariant checks on the finished master before clip generation."""
import bpy, hashlib, json, math, os
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=Path(os.environ['ANIM_MASTER'])
bpy.ops.wm.open_mainfile(filepath=str(M/'spearman.blend'))
sc=bpy.context.scene;rig=bpy.data.objects['Spearman • MPFB game_engine'];body=bpy.data.objects['MPFB anatomical male • original topology']
assert len(body.data.vertices)==19158 and body.data.shape_keys is None
assert len(rig.data.bones)==53 and sc['unit']=='spartan-hoplite'
assert sc.camera.data.type=='ORTHO' and abs(sc.camera.data.ortho_scale-2.52)<1e-5
assert all(abs(a-b)<1e-5 for a,b in zip(sc.camera.location,(2.5,-7,2.72)))
projected=0
for ob in sc.objects:
 assert all(math.isfinite(x) and abs(x)>.001 for x in ob.scale),('unsafe scale',ob.name)
 if ob.type!='MESH':continue
 uv=ob.data.uv_layers.get('Rest painting round2')
 if not uv:continue
 projected+=1
 assert len(uv.data)==len(ob.data.loops)
 assert ob.data.color_attributes.get('Rest paint visibility')
 for mat in ob.data.materials:
  if not mat or not mat.use_nodes:continue
  n=mat.node_tree.nodes
  assert n.get('Camera painted pigment'),ob.name
  assert any(node.type=='LIGHT_PATH' for node in n),ob.name
 assert all(math.isfinite(x) for v in ob.data.vertices for x in v.co)
assert projected>80,projected
lock=json.loads(Path('tools/art/anim3d/units/spartan-hoplite/assets.lock.json').read_text())
for asset in lock['assets']:
 assert hashlib.sha256((R/asset['path']).read_bytes()).hexdigest()==asset['sha256'],asset['path']
report={'status':'passed','projected_meshes':projected,'body_vertices':len(body.data.vertices),'bones':len(rig.data.bones),'camera_only_pigment':True,'nonzero_scales':True,'input_hashes':True}
(M/'scene-validation.json').write_text(json.dumps(report,indent=2));print('SCENE',report)
