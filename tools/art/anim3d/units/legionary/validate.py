"""Validate the delivery contract, reconstruction, clipping, motion and held death."""
import os,json,hashlib
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/legionary';V=R/'review/3d-v2';D=Path('app/src/assets/units/anim')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((D/'legionary.json').read_text());report=json.loads((V/'legionary-pack.json').read_text());atlas=Image.open(D/'legionary.webp').convert('RGBA')
assert meta['format']=='trimmed-rows-v1';assert meta['frame']['w']==meta['frame']['h']==160
assert atlas.size==(meta['atlas']['w'],meta['atlas']['h']);assert (D/'legionary.webp').stat().st_size<=200000;assert report['quality']>=75
assert sha(D/'legionary.webp')==report['atlas_sha256'];assert sha(D/'legionary.json')==report['json_sha256'];assert sha(M/'legionary.blend')==report['source_master_sha256']
expected={'idle':8,'move':8,'attack':10,'hit':4,'death':10};assert list(meta['clips'])==list(expected)
occupied=Image.new('L',atlas.size);checks=[]
for row,(clip,count) in enumerate(expected.items()):
    c=meta['clips'][clip];assert c['row']==row and c['frames']==count and len(c['rects'])==count;assert c['loop']==(clip in ['idle','move'])
    seen=[]
    for i,r in enumerate(c['rects']):
        x,y,w,h,ox,oy=(r[k] for k in ['x','y','w','h','ox','oy']);assert min(x,y,ox,oy)>=0 and w>0 and h>0
        assert x+w<=atlas.width and y+h<=atlas.height;assert ox+w<=160 and oy+h<=160
        assert occupied.crop((x,y,x+w,y+h)).getbbox() is None,'Overlapping frames';occupied.paste(255,(x,y,x+w,y+h))
        im=Image.new('RGBA',(160,160));im.paste(atlas.crop((x,y,x+w,y+h)),(ox,oy));assert im.getchannel('A').getbbox()
        # Source framing, not transparent atlas padding, is the clipping test.
        src=Image.open(M/'renders'/f'e-{clip}'/'256'/f'{i:02}.png').convert('RGBA');box=src.getchannel('A').point(lambda a:255 if a>=20 else 0).getbbox();assert box and min(box[0],box[1],256-box[2],256-box[3])>=2,(clip,i,'clipped',box)
        assert sha(M/'renders'/f'e-{clip}'/'256'/f'{i:02}.png')==report['clips'][clip]['frames256_sha256'][f'{i:02}.png']
        assert sha(M/'renders'/f'e-{clip}'/'512'/f'{i:02}.png')==report['clips'][clip]['frames512_sha256'][f'{i:02}.png']
        seen.append(hashlib.sha256(src.tobytes()).hexdigest())
    assert len(set(seen))>1,f'{clip} no motion'
    if clip=='death':assert seen[-1]==seen[-2],'Death must hold'
    checks.append({'clip':clip,'frames':count,'unique_source_frames':len(set(seen)),'trim_reconstruction':'PASS','margins':'PASS'})
assert ImageChops.multiply(atlas.getchannel('A'),ImageChops.invert(occupied)).getbbox() is None,'Nontransparent padding'
result={'status':'PASS','size':atlas.size,'bytes':(D/'legionary.webp').stat().st_size,'quality':report['quality'],'checks':checks}
(V/'legionary-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
