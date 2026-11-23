"""Check decoded delivery contract and pixel bounds; not a substitute for art review."""
from pathlib import Path
import json,os
from PIL import Image,ImageChops
p=Path('app/src/assets/units/anim');meta=json.loads((p/'spearman.json').read_text());im=Image.open(p/'spearman.webp').convert('RGBA')
assert im.size==(2560,1280);assert (p/'spearman.webp').stat().st_size<=200000
assert meta['frame']=={'w':256,'h':256,'ax':127,'ay':221}
expected={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
findings=[];boxes={}
for row,(clip,(count,fps,loop)) in enumerate(expected.items()):
 assert meta['clips'][clip]=={'row':row,'frames':count,'fps':fps,'loop':loop}
 frames=[]
 for i in range(10):
  f=im.crop((i*256,row*256,(i+1)*256,(row+1)*256));a=f.getchannel('A')
  if i>=count:assert not a.getbbox(),f'{clip} padding nontransparent';continue
  box=a.point(lambda x:255 if x>16 else 0).getbbox();assert box,f'{clip}/{i} empty';boxes[f'{clip}/{i}']=box
  if box[0]<2 or box[1]<2 or box[2]>254 or box[3]>254:findings.append(f'{clip}/{i}: clipping margin {box}')
  frames.append(f)
 assert any(ImageChops.difference(frames[0],f).getbbox(alpha_only=False) for f in frames[1:]),f'{clip} has no motion'
 if clip=='death' and ImageChops.difference(frames[-1].getchannel('A'),frames[-2].getchannel('A')).getbbox():findings.append('death terminal silhouettes are not held')
root=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
terminal=root/'masters/spearman-3d-v2/renders/e-death'
assert Image.open(terminal/'08.png').convert('RGBA').tobytes()==Image.open(terminal/'09.png').convert('RGBA').tobytes(), 'Death terminal source pixels differ'
(root/'review/3d-v2/validation.json').write_text(json.dumps({'contract':'PASS','bounds':boxes,'findings':findings},indent=2))
print('PASS: dimensions, metadata, all 40 frames, alpha, transparent padding, motion, byte cap')
for f in findings:print('FAIL:',f)
raise SystemExit(bool(findings))
