"""Apply the documented winding-only shield revision to existing clip caches.

Only the rigid shield surface and its temporary duplicate marking change. Cloth topology/geometry and animation
remain identical. Update lineage after verifying the old master hash uniformly.
"""
import bpy,os,json,hashlib
from pathlib import Path
M=Path(os.environ['ANIM_MASTER']);master=M/'spearman.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
new=sha(master)
known={json.loads((M/'clips'/c/'clip.json').read_text())['source_master_sha256'] for c in ['idle','move','attack','hit','death']}
previous=known-{new};assert len(previous)<=1,'Mixed unrelated master revisions'
old=next(iter(previous),new)
# The master was corrected by the paint stage; sync is restartable after any clip.
names=('Convex bronze aspis',)
for clip in ['idle','move','attack','hit','death']:
 path=M/'clips'/clip/(clip+'.blend');bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
 assert sc['source_master_sha256'] in {old,new}
 legacy=bpy.data.objects.get('Aspis red lambda painted relief')
 if legacy:bpy.data.objects.remove(legacy,do_unlink=True)
 targets={name:bpy.data.objects[name] for name in names}
 with bpy.data.libraries.load(str(master),link=False) as (src,dst):dst.objects=list(names)
 for name,source in zip(names,dst.objects):
  assert len(targets[name].data.vertices)==len(source.data.vertices)
  targets[name].data=source.data;bpy.data.objects.remove(source,do_unlink=True)
 assert bpy.data.objects['Cloak • simulated wool'].modifiers['Cloth per clip'].point_cache.is_baked
 sc['source_master_sha256']=new;sc['finish_revision']='Shield winding and painting UV; removed duplicate lambda relief; no cloth or motion change'
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path))
 p=path.with_name('clip.json');meta=json.loads(p.read_text());meta['source_master_sha256']=new;meta['finish_revision']=sc['finish_revision'];p.write_text(json.dumps(meta,indent=2))
(M/'finish-revision.json').write_text(json.dumps({'before':old,'after':new,'changed':names,'retained':'All animation, rig, cloth geometry and baked caches'},indent=2))
