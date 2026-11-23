"""Fetch the pinned CC0 horse into the external asset root, never the repository."""
import os,json,hashlib,urllib.request
from pathlib import Path
root=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
lock=json.loads(Path(__file__).with_name('assets.lock.json').read_text());out=root/'assets/horseman/Horse.glb';out.parent.mkdir(parents=True,exist_ok=True)
if not out.exists() or hashlib.sha256(out.read_bytes()).hexdigest()!=lock['sha256']:
 data=urllib.request.urlopen(lock['download'],timeout=60).read()
 assert hashlib.sha256(data).hexdigest()==lock['sha256'],'Horse source checksum mismatch'
 out.write_bytes(data)
print(out)
