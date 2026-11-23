"""Download only CC0 1K PBR assets; cache URLs and SHA256 provenance."""
import json, subprocess, hashlib, zipfile, os
from pathlib import Path
ROOT=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
A=ROOT/'assets';A.mkdir(parents=True,exist_ok=True)
records=[]
LOCK=json.loads(Path(__file__).with_name('assets.lock.json').read_text())
def get(url,path):
 if not path.exists():subprocess.run(['curl','-L','--fail','-sS',url,'-o',str(path)],check=True)
 key=str(path.relative_to(A))
 if key in LOCK and hashlib.sha256(path.read_bytes()).hexdigest()!=LOCK[key]:raise ValueError('Source checksum changed: '+key)
 records.append({'file':str(path.relative_to(A)),'url':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'license':'CC0-1.0'})
for ident in ['brown_leather','fine_grained_wood']:
 p=A/(ident+'.json');get('https://api.polyhaven.com/files/'+ident,p);data=json.loads(p.read_text())
 dest=A/ident;dest.mkdir(exist_ok=True)
 for key in ['diff','rough','nor_gl']:
  entry=data[{'diff':'Diffuse','rough':'Rough','nor_gl':'nor_gl'}[key]]['1k']['jpg'];get(entry['url'],dest/(key+'.jpg'))
for ident in ['Metal034','Fabric030','Travertine001']:
 p=A/(ident+'_1K-JPG.zip');get('https://ambientcg.com/get?file='+p.name,p)
 dest=A/ident;dest.mkdir(exist_ok=True)
 with zipfile.ZipFile(p) as z:z.extractall(dest)
(A/'materials-manifest.json').write_text(json.dumps(records,indent=2))
print('Downloaded',len(records),'CC0 files')
