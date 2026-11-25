"""Pack and validate the actual 70 round-2 frames; no shipped atlas is replaced."""
import argparse,json,os,sys
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from kit.atlas import pack,validate,save_decoded
p=argparse.ArgumentParser();p.add_argument('--gpu',action='store_true');a=p.parse_args()
root=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
lane=root/'lanes/spearman-q-r2';lane=lane/'gpu' if a.gpu else lane
clips={};frames={}
for clip in ('idle','walk','attack','hit','death'):
    folder=lane/'frames'/clip;r=json.loads((folder/'receipt.json').read_text())
    key='move' if clip=='walk' else clip
    clips[key]=(r['frames'],r['fps'],clip in ('idle','walk'))
    frames[key]=[Image.open(folder/f'{i:02}.png').convert('RGBA') for i in range(r['frames'])]
webp,metadata,quality=pack(frames,tuple(r['anchor_160']),clips=clips,byte_limit=350000,space='display')
decoded=validate(webp,metadata,frames,clips=clips,byte_limit=350000,space='display')
output=lane/'atlas';output.mkdir(exist_ok=True)
(output/'spearman-q.webp').write_bytes(webp)
(output/'spearman-q.json').write_text(json.dumps(metadata,indent=2)+'\n')
save_decoded(decoded,output/'decoded')
receipt={'bytes':len(webp),'quality':quality,'frames':sum(c[0] for c in clips.values()),'decoded_validation':'pass','stage':'GPU' if a.gpu else 'CPU proxy'}
(output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
