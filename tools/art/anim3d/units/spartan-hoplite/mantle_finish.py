"""Correct front mantle winding and activate its already-frozen painting UVs."""
import bpy,bmesh,os,json,hashlib
from pathlib import Path
M=Path(os.environ['ANIM_MASTER'])
def repair():
 for piece in bpy.context.scene.objects:
  if piece.type=='MESH' and piece.name.startswith('Corinthian'):
   for mat in piece.data.materials:
    if mat and mat.use_nodes:mat.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=1
 ob=bpy.data.objects['Crimson shoulder mantle folds']
 if ob.data.get('hoplite_mantle_front'):return
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()
 attr=ob.data.color_attributes.get('Painting incidence')
 if attr:
  for item in attr.data:item.color=(1,1,1,1)
 ob.data['hoplite_mantle_front']=True
for file in ['spearman.blend','unpainted.blend']:
 path=M/file;bpy.ops.wm.open_mainfile(filepath=str(path));repair();bpy.ops.wm.save_as_mainfile(filepath=str(path))
new=hashlib.sha256((M/'spearman.blend').read_bytes()).hexdigest()
for clip in ['idle','move','attack','hit','death']:
 path=M/'clips'/clip/(clip+'.blend');bpy.ops.wm.open_mainfile(filepath=str(path));repair();bpy.context.scene['source_master_sha256']=new;bpy.ops.wm.save_as_mainfile(filepath=str(path))
 p=path.with_name('clip.json');meta=json.loads(p.read_text());meta['source_master_sha256']=new;meta['mantle_finish']='Outward front normals, preserved painting UVs and fixed face mask';p.write_text(json.dumps(meta,indent=2))
