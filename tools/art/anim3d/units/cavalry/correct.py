"""Idempotent round-one correction for existing masters, retained for reproducibility."""
import bpy,os,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cavalry'
for p in [M/'cavalry-plain.blend',M/'cavalry-unpainted.blend',M/'cavalry.blend']+sorted((M/'clips').glob('*.blend')):
 bpy.ops.wm.open_mainfile(filepath=str(p));sc=bpy.context.scene
 if sc.get('cavalry_sabre_length',.81)==.55:continue
 blade=bpy.data.objects['GEO-sabre-blade'];direction=Vector((0,-.70,.72)).normalized()
 for v in blade.data.vertices:v.co+=direction*((v.index//4)/24*(.55-.81))
 sc['cavalry_sabre_length']=.55
 bpy.ops.wm.save_as_mainfile(filepath=str(p))
sha=hashlib.sha256((M/'cavalry.blend').read_bytes()).hexdigest()
for p in (M/'clips').glob('*.json'):
 data=json.loads(p.read_text());data['source_master_sha256']=sha;p.write_text(json.dumps(data,indent=2)+'\n')
print('CORRECTED sabre framing in all masters; all renders now require refresh')
