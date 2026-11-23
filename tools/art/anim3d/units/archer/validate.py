"""Decode/reconstruct trims and verify budget, alpha, margins, motion, source hashes."""
import os,json,hashlib
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/archer';D=Path('app/src/assets/units/anim');meta=json.loads((D/'archer.json').read_text());report=json.loads((M/'pack.json').read_text());atlas=Image.open(D/'archer.webp').convert('RGBA');results=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert report['source_sha256']==sha(M/'archer.blend');assert report['grade_sha256']==sha(M/'grade.json');assert report['atlas_sha256']==sha(D/'archer.webp');assert report['json_sha256']==sha(D/'archer.json');assert report['quality']>=75;assert (D/'archer.webp').stat().st_size<=200000;assert meta['format']=='trimmed-v1';assert meta['frame']=={'w':160,'h':160,'ax':80,'ay':138}
for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 c=meta['clips'][clip];assert c['frames']==count;assert len(c['rects'])==count;originals=[];bounds=[];reconstruction_errors=[]
 for i,r in enumerate(c['rects']):
  x,y,w,h,ox,oy=[r[k] for k in ['x','y','w','h','ox','oy']];assert 0<=x<x+w<=atlas.width and 0<=y<y+h<=atlas.height;assert 0<=ox<ox+w<=160 and 0<=oy<oy+h<=160
  path=M/'renders'/f'e-{clip}'/f'{i:02}.png';assert sha(path)==report['clips'][clip]['frames'][i]['sha256'];raw=Image.open(path).convert('RGBA');assert raw.size==(512,512);bbox=raw.getchannel('A').getbbox();assert min(bbox[0],bbox[1],512-bbox[2],512-bbox[3])>=2,(clip,i,'clipped',bbox);bounds.append(bbox)
  original=raw.resize((160,160),Image.Resampling.LANCZOS);originals.append(original);rec=Image.new('RGBA',(160,160));rec.paste(atlas.crop((x,y,x+w,y+h)),(ox,oy));assert rec.getchannel('A').getextrema()[0]==0
  assert ImageChops.difference(rec.getchannel('A'),original.getchannel('A')).getbbox() is None,(clip,i,'alpha or offsets changed')
  a=Image.new('RGBA',(160,160),'#eee4d2');a.alpha_composite(original);b=Image.new('RGBA',(160,160),'#eee4d2');b.alpha_composite(rec);error=sum(ImageStat.Stat(ImageChops.difference(a.convert('RGB'),b.convert('RGB'))).mean)/3;assert error<8,(clip,i,error);reconstruction_errors.append(error)
 assert any(ImageChops.difference(originals[0],v).convert('RGB').getbbox() for v in originals[1:]),(clip,'no motion')
 if clip=='death':assert ImageChops.difference(originals[-1],originals[-2]).getbbox() is None,'death not held'
 results.append({'clip':clip,'frames':count,'max_composited_rgb_mae':max(reconstruction_errors),'bounds':bounds})
result={'passed':True,'frames':40,'bytes':report['bytes'],'quality':report['quality'],'checks':['source/clip/frame hashes','actual 512px masters','160px trim reconstruction','exact alpha','2px clipping margin','motion','held death'],'clips':results};(R/'review/3d-v2/archer-validation.json').write_text(json.dumps(result,indent=2));print('PASS',40,'frames;',report['bytes'],'bytes; Q',report['quality'])
