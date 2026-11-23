"""Trim 160px frames without losing anchors; enforce all 40 frames at quality >=75."""
import os,json,hashlib,io,sys
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/composite-archer';OUT=Path('app/src/assets/units/anim');OUT.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate_inputs():
 inputs=json.loads((M/'inputs.json').read_text())['sha256']
 assert 'face-fill-source.png' in inputs,'Missing face-fill provenance; run prepare'
 for name,digest in inputs.items():
  assert sha(R/'assets/composite-archer'/name)==digest,('changed painting/fill input',name)
def pack():
 validate_inputs()
 records={};thumbs={};rowheights=[];rowwidths=[];checks=[];provenance={}
 for clip,(count,fps,loop) in CLIPS.items():
  manifest=json.loads((M/f'renders/e-{clip}/manifest.json').read_text());meta=json.loads((M/f'clips/{clip}.json').read_text())
  assert meta['source_sha256']==sha(M/'composite-archer.blend'),f'{clip}: stale clip'
  assert manifest['blend_sha256']==sha(M/f'clips/{clip}.blend'),f'{clip}: stale render'
  assert manifest['grade_sha256']==sha(M/'grade.json'),f'{clip}: stale grade'
  assert manifest['resolution']>=512,f'{clip}: missing 512 master'
  assert len(manifest['frames'])==count
  images=[];rects=[];x=2;height=0;seen={}
  for i,rec in enumerate(manifest['frames']):
   assert sha(M/rec['path'])==rec['sha256'],f'{clip}: modified raw'
   for size in [512,256]:assert Image.open(M/f'{size}/e-{clip}/{i:02d}.png').size==(size,size)
   im=Image.open(M/f'256/e-{clip}/{i:02d}.png').convert('RGBA');bbox=im.getchannel('A').point(lambda v:255 if v>12 else 0).getbbox();assert bbox
   assert min(bbox[0],bbox[1],256-bbox[2],256-bbox[3])>=2,(clip,i,'clipped',bbox)
   im=im.convert('RGBa').resize((160,160),Image.Resampling.BICUBIC).convert('RGBA')
   # Preserve 8-bit alpha exactly; bicubic reduction avoids Lanczos perimeter ringing.
   alpha=im.getchannel('A');box=alpha.getbbox();assert box
   crop=im.crop(box);w,h=crop.size;images.append(crop)
   identity=(box,crop.tobytes())
   if identity in seen:
    rects.append(dict(seen[identity]))
   else:
    rec={'x':x,'y':0,'w':w,'h':h,'ox':box[0],'oy':box[1]};seen[identity]=rec;rects.append(rec);x+=w+4
   height=max(height,h+4)
  records[clip]=rects;thumbs[clip]=images;rowwidths.append(x);rowheights.append(height);provenance[clip]=manifest
  assert len({im.tobytes() for im in images})>1,f'{clip}: no motion'
  if clip=='death':assert images[-1].size==images[-2].size and images[-1].tobytes()==images[-2].tobytes(),'death must hold'
 width=max(rowwidths);height=sum(rowheights);atlas=Image.new('RGBA',(width,height));y=0
 clips={}
 for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
  for im,rec in zip(thumbs[clip],records[clip]):rec['y']=y+2;atlas.paste(im,(rec['x'],rec['y']))
  clips[clip]={'row':row,'frames':count,'fps':fps,'loop':loop};y+=rowheights[row]
 attempts=[];payload=None
 for quality in [90,85,80,79,78,77,76,75]:
  buffer=io.BytesIO();atlas.save(buffer,format='WEBP',quality=quality,method=6);data=buffer.getvalue();attempts.append({'quality':quality,'bytes':len(data)})
  if len(data)<=200000:payload=data;break
 if payload is None:raise RuntimeError(f'Cannot fit quality >=75 without discarding detail: {attempts}')
 metadata={'formatVersion':2,'frame':{'w':160,'h':160,'ax':79.375,'ay':138.125},'clips':clips,'frames':records,'atlas':{'w':width,'h':height},'trim':{'offsetSpace':'untrimmed-frame','padding':2},'candidate':True}
 (OUT/'composite-archer.webp').write_bytes(payload);(OUT/'composite-archer.json').write_text(json.dumps(metadata,indent=2)+'\n')
 report={'resampling':'premultiplied bicubic','alpha':'lossless 8-bit','bytes':len(payload),'quality':quality,'attempts':attempts,'atlas_sha256':sha(OUT/'composite-archer.webp'),'source':provenance,'checks':['40 frames','512/256 masters','input hashes','grade consistency','2px native margin','motion each clip','held death','quality >=75','size <=200000','160px trim offsets']}
 (M/'pack.json').write_text(json.dumps(report,indent=2));validate();decoded_review();print(json.dumps({k:report[k] for k in ['bytes','quality','attempts','checks']},indent=2))
def validate():
 validate_inputs()
 data=json.loads((OUT/'composite-archer.json').read_text());atlas=Image.open(OUT/'composite-archer.webp').convert('RGBA');assert atlas.size==(data['atlas']['w'],data['atlas']['h']);assert (OUT/'composite-archer.webp').stat().st_size<=200000
 assert data['frame']=={'w':160,'h':160,'ax':79.375,'ay':138.125};assert atlas.getchannel('A').getextrema()==(0,255)
 count=0
 for clip,(n,_,_) in CLIPS.items():
  assert len(data['frames'][clip])==n==data['clips'][clip]['frames']
  manifest=json.loads((M/f'renders/e-{clip}/manifest.json').read_text())
  assert manifest['blend_sha256']==sha(M/f'clips/{clip}.blend'),f'{clip}: stale render'
  assert manifest['grade_sha256']==sha(M/'grade.json'),f'{clip}: stale grade'
  assert json.loads((M/f'clips/{clip}.json').read_text())['source_sha256']==sha(M/'composite-archer.blend')
  assert (data['clips'][clip]['fps'],data['clips'][clip]['loop'])==CLIPS[clip][1:]
  decoded=[]
  for i,r in enumerate(data['frames'][clip]):
   assert all(r[k]>=0 for k in ['x','y','ox','oy']);assert r['ox']+r['w']<=160 and r['oy']+r['h']<=160
   assert r['x']+r['w']<=atlas.width and r['y']+r['h']<=atlas.height
   # Frame reconstruction has fixed anchor; trimming cannot introduce animation drift.
   cell=Image.new('RGBA',(160,160));cell.paste(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));assert cell.getchannel('A').getbbox();count+=1
   source=Image.open(M/f'256/e-{clip}/{i:02d}.png').convert('RGBa').resize((160,160),Image.Resampling.BICUBIC).convert('RGBA')
   alpha=source.getchannel('A')
   assert alpha.tobytes()==cell.getchannel('A').tobytes(),(clip,i,'decoded alpha/offset mismatch')
   assert sha(M/manifest['frames'][i]['path'])==manifest['frames'][i]['sha256']
   decoded.append(cell.tobytes())
  if clip=='death':assert decoded[-1]==decoded[-2],'decoded death must hold exactly'
 assert count==40
 report=json.loads((M/'pack.json').read_text());assert report['quality']>=75;assert report['atlas_sha256']==sha(OUT/'composite-archer.webp')
 print('PASS atlas: 40 frames, fixed anchors, transparent alpha, valid trim bounds, <=200KB')
def decoded_review():
 data=json.loads((OUT/'composite-archer.json').read_text());atlas=Image.open(OUT/'composite-archer.webp').convert('RGBA');r=data['frames']['idle'][0]
 cell=Image.new('RGBA',(160,160));cell.paste(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']))
 ref=Image.open('app/src/assets/units/composite-archer-256.png').convert('RGBA').resize((160,160),Image.Resampling.LANCZOS)
 canvas=Image.new('RGB',(360,280),(38,34,30));draw=ImageDraw.Draw(canvas)
 for i,(im,label) in enumerate([(ref,'Painting at 160'),(cell,'Decoded atlas at 160')]):
  canvas.paste(im,(10+i*180,24),im);draw.text((10+i*180,5),label,fill=(240,220,190));small=im.resize((64,64),Image.Resampling.LANCZOS);canvas.paste(small,(58+i*180,200),small)
 canvas.save(R/'review/3d-v2/composite-archer-g-atlas-check.png')
if __name__=='__main__':
 validate() if '--validate-only' in sys.argv else pack()
