"""Keep the shield face ahead of the fingers; retain baked cloth and keyed rig."""
import bpy,os,json,hashlib
from pathlib import Path
from mathutils import Vector
M=Path(os.environ['ANIM_MASTER'])
def shift():
 ctl=bpy.data.objects['Aspis control']
 for ob in ctl.children:
  if ob.type not in {'MESH','CURVE'} or ob.data.get('hoplite_grip_clearance'):continue
  points=ob.data.vertices if ob.type=='MESH' else [p for sp in ob.data.splines for p in sp.points]
  for p in points:p.co.y-=.075
  ob.data['hoplite_grip_clearance']=True
for filename in ['spearman.blend','unpainted.blend']:
 path=M/filename;bpy.ops.wm.open_mainfile(filepath=str(path));shift();bpy.ops.wm.save_as_mainfile(filepath=str(path))
new=hashlib.sha256((M/'spearman.blend').read_bytes()).hexdigest()
for clip in ['idle','move','attack','hit','death']:
 path=M/'clips'/clip/(clip+'.blend');bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;shift()
 if clip=='death':
  ctl=bpy.data.objects['Aspis control']
  for f in range(sc.frame_start,sc.frame_end+1):
   sc.frame_set(f);t=max(0,min(1,(f-25)/max(1,sc.frame_end-25)));release=max(0,min(1,(t-.30)/.42))
   if release<=.8:continue
   dg=bpy.context.evaluated_depsgraph_get();lowest=100
   for ob in ctl.children:
    ev=ob.evaluated_get(dg);me=ev.to_mesh();lowest=min(lowest,min((ob.matrix_world@v.co).z for v in me.vertices));ev.to_mesh_clear()
   mat=ctl.matrix_world.copy();mat.translation.z+=.1-lowest;ctl.matrix_world=mat;ctl.keyframe_insert('location',frame=f)
 sc['source_master_sha256']=new;sc['shield_clearance']='75mm forward, final released shield rests at z=.10'
 sc.frame_set(25);bpy.ops.wm.save_as_mainfile(filepath=str(path))
 p=path.with_name('clip.json');meta=json.loads(p.read_text());meta['source_master_sha256']=new;meta['shield_clearance']=sc['shield_clearance'];p.write_text(json.dumps(meta,indent=2))
