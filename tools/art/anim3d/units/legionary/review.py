"""Publish each stage immediately. Fixed rest-derived grade avoids colour pumping."""
import os,sys,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageEnhance
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/legionary';V=R/'review/3d-v2';V.mkdir(parents=True,exist_ok=True)
stage=sys.argv[1];folder=M/'renders'/stage;meta=json.loads((folder/'render.json').read_text())
ref=Image.open('app/src/assets/units/legionary-256.png').convert('RGBA')
def quantiles(im):
    mask=im.getchannel('A').point(lambda a:255 if a>220 else 0)
    result=[]
    for ch in im.convert('RGB').split():
        hist=ch.histogram(mask);total=sum(hist);q=[]
        for k in range(17):
            target=total*k/16;s=0
            for i,n in enumerate(hist):
                s+=n
                if s>=target:q.append(i);break
        result.append(q)
    return result
if stage=='c':
    source=quantiles(Image.open(folder/'raw/rest.png').convert('RGBA'));target=quantiles(ref);lut=[]
    for src,dst in zip(source,target):
        channel=[]
        for x in range(256):
            k=next((k for k in range(15) if src[k+1]>x),15);t=max(0,min(1,(x-src[k])/max(1,src[k+1]-src[k])))
            mapped=dst[k]+t*(dst[k+1]-dst[k]);channel.append(round(max(0,min(255,x+.35*max(-35,min(35,mapped-x))))))
        lut+=channel
    (M/'grade.json').write_text(json.dumps({'lut':lut,'source_quantiles':source,'target_quantiles':target,'blend':.35},indent=2))
lut=json.loads((M/'grade.json').read_text())['lut'] if (M/'grade.json').exists() and stage!='b' else None
files=sorted((folder/'raw').glob('*.png'));images=[]
for p in files:
    im=Image.open(p).convert('RGBA')
    if lut:
        rgb=im.convert('RGB').point(lut);rgb.putalpha(im.getchannel('A'));im=rgb
    for size in [512,256]:
        dest=folder/str(size);dest.mkdir(exist_ok=True)
        # Never claim an upscaled preview as a 512 master.
        if size<=im.width:im.resize((size,size),Image.Resampling.LANCZOS).save(dest/p.name)
    images.append(im.resize((256,256),Image.Resampling.LANCZOS))
meta['grade_sha256']=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest() if lut else None
meta['raw_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files};(folder/'render.json').write_text(json.dumps(meta,indent=2))
def sheet(ims,labels,path):
    canvas=Image.new('RGB',(len(ims)*256,368),(36,33,29));d=ImageDraw.Draw(canvas)
    for i,(im,label) in enumerate(zip(ims,labels)):
        d.text((i*256+8,8),label,fill=(237,220,187));canvas.paste(im,(i*256,28),im)
        small=im.resize((64,64),Image.Resampling.LANCZOS);canvas.paste(small,(i*256+96,294),small)
    canvas.save(path)
if stage=='b':
    ordered=[Image.open(folder/'256'/f'{n}.png').convert('RGBA') for n in ['rest','front','side']]
    sheet([ref]+ordered,['Painting','3D rest / CPU','3D front','3D side'],V/'legionary-b-plain.png')
elif stage in ['c','c-details']:
    im=images[0];sheet([ref,im],['Painting','3D '+meta['engine']+' '+meta['device']],V/'legionary-c-textured-lit.png')
    half=ref.copy();half.paste(im.crop((128,0,256,256)),(128,0));cross=Image.blend(ref,im,.5)
    sheet([ref,im,half,cross],['Painting','3D rest','Half split','50% crossfade'],V/'legionary-f-restpose-compare.png')
    crops=[(101,12,149,64),(91,50,145,113),(139,54,194,174)]
    ims=[];labels=[]
    for name,box in zip(['Helmet','Armour','Shield'],crops):
        for label,picture in [('Painting',ref),('3D',im)]:ims.append(picture.crop(box).resize((256,256),Image.Resampling.LANCZOS));labels.append(name+' '+label)
    sheet(ims,labels,V/'legionary-c-details.png')
elif stage=='d':sheet(images,[f'Attack pose {i}' for i in range(len(images))],V/'legionary-d-rig-poses.png')
elif stage.startswith('e-'):
    clip=stage[2:];sheet(images,[f'{clip} {i+1}' for i in range(len(images))],V/f'legionary-e-{clip}-strip.png')
    fps={'idle':10,'move':12,'attack':14,'hit':12,'death':10}[clip]
    images[0].save(V/f'legionary-e-{clip}.webp',save_all=True,append_images=images[1:],duration=round(1000/fps),loop=0,quality=85,method=4)
with (V/'legionary-log.md').open('a') as f:f.write(f'- Published {stage}: {meta["engine"]}/{meta["device"]}, {meta["resolution"]} px, {meta["samples"]} samples; visual review pending.\n')
print('REVIEW_READY',stage)
