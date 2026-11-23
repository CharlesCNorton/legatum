"""Validate the candidate contract and reconstruct all trimmed frames for review."""
import os,json,hashlib
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/scout';V=R/'review/3d-v2';O=Path('app/src/assets/units/anim');(V/'scout-validation.json').unlink(missing_ok=True);meta=json.loads((O/'scout.json').read_text());atlas=Image.open(O/'scout.webp').convert('RGBA');report=json.loads((V/'scout-pack.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert report['grade_sha256']==sha(M/'grade.json')
assert meta['formatVersion']==2 and meta['frame']=={'w':160,'h':160,'ax':80,'ay':142}
assert (O/'scout.webp').stat().st_size<=200000 and report['quality']>=75
assert report['atlas_sha256']==sha(O/'scout.webp') and report['source_sha256']==sha(M/'scout.blend')
expected={'idle':8,'move':8,'attack':10,'hit':4,'death':10};rects=[];checks={};sheet=Image.new('RGBA',(1600,800),(35,31,28,255))
for row,(clip,n) in enumerate(expected.items()):
 info=meta['clips'][clip];assert info['fps']==dict(idle=10,move=12,attack=14,hit=12,death=10)[clip];assert info['loop']==(clip in ['idle','move']);assert info['frames']==n and info['row']==row;assert len(meta['trims'][clip])==n;raw=[]
 for i,t in enumerate(meta['trims'][clip]):
  x,y,w,h,ox,oy=[t[k] for k in ['x','y','w','h','ox','oy']];assert 0<=x<x+w<=atlas.width and 0<=y<y+h<=atlas.height;assert 0<=ox<ox+w<=160 and 0<=oy<oy+h<=160
  box=(x,y,x+w,y+h)
  assert all(box[2]<=b[0] or b[2]<=box[0] or box[3]<=b[1] or b[3]<=box[1] for b in rects),'Overlapping packed samples';rects.append(box)
  canvas=Image.new('RGBA',(160,160));canvas.paste(atlas.crop(box),(ox,oy));assert canvas.getchannel('A').getextrema()[0]==0;sheet.alpha_composite(canvas,(i*160,row*160))
  p=M/'renders'/('e-'+clip)/f'{i:02}.png';assert sha(p)==report['frame_sha256'][f'{clip}/{i}'];im=Image.open(p).convert('RGBA');assert im.size==(512,512);expected_alpha=im.resize((160,160),Image.Resampling.LANCZOS).getchannel('A').point(lambda v:round(round(v*31/255)*255/31));assert canvas.getchannel('A').tobytes()==expected_alpha.tobytes(),'Trim reconstruction alpha differs';assert (M/'256'/('e-'+clip)/f'{i:02}.png').exists();box=im.getchannel('A').point(lambda v:255 if v>16 else 0).getbbox();assert box[0]>0 and box[1]>0 and box[2]<512 and box[3]<512,f'Clipped {clip}/{i}: {box}';raw.append(im)
 assert len({im.tobytes() for im in raw})>1,'No motion '+clip
 if clip=='death':assert raw[-1].tobytes()==raw[-2].tobytes(),'Death must hold'
 diffs=[sum(ImageStat.Stat(ImageChops.difference(raw[i].convert('RGB'),raw[(i+1)%n].convert('RGB'))).mean) for i in range(n)]
 checks[clip]={'frames':n,'motion_delta_mean':sum(diffs)/n,'loop_seam_delta':diffs[-1] if info['loop'] else None,'margins':'pass'}
sheet.save(V/'scout-atlas-decoded.png');result={'status':'PASS','atlas_sha256':sha(O/'scout.webp'),'source_sha256':sha(M/'scout.blend'),'bytes':report['bytes'],'quality':report['quality'],'clips':checks,'trim_rectangles':len(rects),'masters':'40 actual 512px and 40 256px','limits':'Image/metadata checks do not prove art parity or full mesh collision freedom.'};(V/'scout-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
