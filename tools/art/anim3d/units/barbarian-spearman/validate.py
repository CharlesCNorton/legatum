"""Validate delivery, provenance, motion, trim reconstruction and terminal death."""
from pathlib import Path
import os,json,hashlib
from PIL import Image,ImageChops
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/barbarian-spearman';O=Path('app/src/assets/units/anim')
meta=json.loads((O/'barbarian-spearman.json').read_text());report=json.loads((M/'pack.json').read_text());path=O/'barbarian-spearman.webp';im=Image.open(path).convert('RGBA')
assert path.stat().st_size<=200000 and report['quality']>=75
assert hashlib.sha256(path.read_bytes()).hexdigest()==report['atlas_sha256']
assert im.size==(1600,800) and im.getchannel('A').getextrema()==(0,255)
assert meta['frame']=={'w':160,'h':160,'ax':80,'ay':137}
checks=[]
for row,(clip,count) in enumerate([('idle',8),('move',8),('attack',10),('hit',4),('death',10)]):
 info=meta['clips'][clip];assert info['row']==row and info['frames']==count and len(info['rects'])==count
 hashes=[]
 for i,rect in enumerate(info['rects']):
  assert rect['x']==i*160 and rect['y']==row*160
  assert 0<=rect['ox'] and rect['ox']+rect['w']<=160 and 0<=rect['oy'] and rect['oy']+rect['h']<=160
  for size in [512,256]:assert Image.open(M/str(size)/clip/f'{i:02}.png').size==(size,size)
  frame=Image.open(M/'512'/clip/f'{i:02}.png').convert('RGBA');box=frame.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox()
  assert box and min(box[:2])>0 and max(box[2:])<512,f'{clip}/{i} clipped: {box}'
  # WebP alpha is lossless: trim reconstruction must exactly restore quantized alpha.
  original=frame.resize((160,160),Image.Resampling.LANCZOS).getchannel('A').point(lambda a:round(a/8)*8 if a<248 else 255)
  restored=Image.new('L',(160,160));tile=im.getchannel('A').crop((rect['x'],rect['y'],rect['x']+rect['w'],rect['y']+rect['h']));restored.paste(tile,(rect['ox'],rect['oy']))
  assert ImageChops.difference(original,restored).getbbox() is None,f'{clip}/{i}: trim alpha mismatch'
  hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
 assert len(set(hashes))>1,f'{clip} has no motion'
 if clip=='death':assert hashes[-1]==hashes[-2],'Death must hold its final pose'
 checks.append(f'{clip}: {count} frames, alpha bounds, 512/256 masters, motion and trim offsets passed')
result={'passed':True,'checks':checks,'atlas_bytes':path.stat().st_size,'quality':report['quality'],'note':'Technical validation only; painting-level quality requires visual approval.'}
(M/'validation.json').write_text(json.dumps(result,indent=2)+'\n');(R/'review/3d-v2/barbarian-spearman-validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
