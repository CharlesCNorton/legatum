"""Apply clothing coverage to existing masters without disturbing bakes or keys."""
import sys,hashlib,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from coverage import covered_indices,apply_coverage
bpy.ops.wm.open_mainfile(filepath=str(M/'medjay.blend'));visible=covered_indices(bpy.data.objects['Medjay MPFB anatomical body'])
for file in ['medjay.blend','medjay-plain.blend']+[f'medjay-{c}.blend' for c in CLIPS]:
 bpy.ops.wm.open_mainfile(filepath=str(M/file));apply_coverage(bpy.data.objects['Medjay MPFB anatomical body'],visible);bpy.ops.wm.save_as_mainfile(filepath=str(M/file))
sha=hashlib.sha256((M/'medjay.blend').read_bytes()).hexdigest()
for clip in CLIPS:
 p=M/f'{clip}.json';data=json.loads(p.read_text());data['master_sha256']=sha;p.write_text(json.dumps(data,indent=2))
log('Masked only body vertices covered by opaque linen; retained MPFB topology, weights, UVs, bakes and all authored actions. Regenerate every render after this master update.')
