"""Frozen rest grade, 512/256 masters, native-size review and projection crossfade."""
import os,sys,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/settler';V=R/'review/3d-v2';stage=sys.argv[1];out=M/'renders'/stage
source=Image.open('app/src/assets/units/settler-256.png').convert('RGBA')
raw=[Image.open(p).convert('RGBA') for p in sorted((out/'raw').glob('*.png'))]
def quantile(im):
    pixels=[v[:3] for v in im.getdata() if v[3]>230]
    return [[sorted(v[c] for v in pixels)[int((len(pixels)-1)*q)] for q in [.05,.1,.25,.5,.75,.9,.95]] for c in range(3)]
def make_lut(src,dst):
    tables=[]
    for c in range(3):
        xs=[0]+src[c]+[255];ys=[0]+dst[c]+[255];table=[]
        for x in range(256):
            k=next((i for i in range(8) if xs[i+1]>=x),7);t=(x-xs[k])/max(1,xs[k+1]-xs[k]);mapped=ys[k]*(1-t)+ys[k+1]*t
            table.append(round(max(0,min(255,x+max(-24,min(24,(mapped-x)*.5))))))
        tables+=table
    return tables
if stage=='c':
    data={'reference_quantiles':quantile(source),'render_quantiles':quantile(raw[0]),'method':'50% bounded monotonic rest transfer, max 24 channel levels; frozen for all clips'}
    data['master_sha256']=hashlib.sha256((M/'settler.blend').read_bytes()).hexdigest()
    data['source_sha256']=hashlib.sha256(Path('app/src/assets/units/settler-256.png').read_bytes()).hexdigest()
    data['lut']=make_lut(data['render_quantiles'],data['reference_quantiles'])
    # One fixed orthographic framing calibration; never resize individual poses to their bounds.
    sb=source.getchannel('A').point(lambda a:255 if a>128 else 0).getbbox()
    rb=raw[0].resize((256,256),Image.Resampling.LANCZOS).getchannel('A').point(lambda a:255 if a>128 else 0).getbbox()
    scale=(sb[3]-sb[1])/(rb[3]-rb[1]);dx=(sb[0]+sb[2])/2-scale*(rb[0]+rb[2])/2;dy=(sb[1]+sb[3])/2-scale*(rb[1]+rb[3])/2
    data['framing']={'scale':scale,'dx_256':dx,'dy_256':dy,'painting_bounds':sb,'raw_render_bounds':rb}
    (M/'grade.json').write_text(json.dumps(data,indent=2))
lut=json.loads((M/'grade.json').read_text())['lut'] if stage!='b' else None
images=[]
for i,im in enumerate(raw):
    if lut:
        im=Image.merge('RGBA',(*im.convert('RGB').point(lut).split(),im.getchannel('A')))
        framing=json.loads((M/'grade.json').read_text()).get('framing')
        if framing:
            k=framing['scale'];dx=framing['dx_256']*im.width/256;dy=framing['dy_256']*im.height/256
            im=im.transform(im.size,Image.Transform.AFFINE,(1/k,0,-dx/k,0,1/k,-dy/k),Image.Resampling.BICUBIC)

    for size in [512,256]:
        if size>im.width:continue
        d=M/f'frames-{size}'/stage;d.mkdir(parents=True,exist_ok=True);im.resize((size,size),Image.Resampling.LANCZOS).save(d/f'{i:02}.png')
    images.append(im.resize((256,256),Image.Resampling.LANCZOS))
manifest=json.loads((out/'render.json').read_text());manifest['grade_sha256']=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest() if lut else None;(out/'render.json').write_text(json.dumps(manifest,indent=2))
def sheet(ims,path,labels=None):
    s=Image.new('RGB',(272*len(ims),380),(224,215,191));d=ImageDraw.Draw(s)
    for i,im in enumerate(ims):
        x=8+i*272;d.text((x,10),(labels[i] if labels else str(i))+' | 256 / 64 px',fill=(40,34,27));s.paste(im,(x,36),im);small=im.resize((64,64),Image.Resampling.LANCZOS);s.paste(small,(x+96,302),small)
    s.save(path)
name={'b':'b-plain','c':'c-textured-lit','d':'d-rig-poses','c-details':'c-details'}.get(stage,stage+'-strip')
if stage=='c-details':
    s=Image.new('RGB',(1024,570),(224,215,191));d=ImageDraw.Draw(s)
    for col,(label,box) in enumerate([('Face and hood',(100,10,159,72)),('Cloth and belt',(98,61,173,180)),('Pack and roll',(151,40,195,113)),('Staff grip',(76,69,115,111))]):
        d.text((col*256+8,5),label,fill='black')
        for row,detail in enumerate([Image.open(R/'assets/settler/projection.png').convert('RGBA'),im]):
            scale=detail.width/256;crop=detail.crop(tuple(round(v*scale) for v in box)).resize((240,240),Image.Resampling.LANCZOS);s.paste(crop,(col*256+8,row*270+25),crop)
    s.save(V/'settler-c-details.png')
else:sheet([source]+images,V/f'settler-{name}.png',['Painting']+[p.stem+' '+manifest['device'] for p in sorted((out/'raw').glob('*.png'))])
if stage=='c':
    a=source.getchannel('A').point(lambda v:255 if v>128 else 0)
    b=images[0].getchannel('A').point(lambda v:255 if v>128 else 0)
    from PIL import ImageChops
    intersection=sum(v>0 for v in ImageChops.multiply(a,b).getdata());union=sum(v>0 for v in ImageChops.lighter(a,b).getdata())
    (M/'comparison-metrics.json').write_text(json.dumps({'silhouette_iou':intersection/union,'resolution':manifest['resolution'],'device':manifest['device'],'art_approved':False},indent=2))
    half=source.copy();half.paste(images[0].crop((128,0,256,256)),(128,0));blend=Image.blend(source,images[0],.5)
    sheet([source,images[0],half,blend],V/'settler-f-restpose-compare.png',['Painting','3D '+manifest['device'],'Half split','50/50 crossfade'])
if stage.startswith('e-'):
    fps={'idle':10,'move':12,'attack':14,'hit':12,'death':10}[stage[2:]]
    images[0].save(V/f'settler-{stage}.webp',save_all=True,append_images=images[1:],duration=round(1000/fps),loop=0,quality=85,method=4)
with (V/'settler-log.md').open('a') as f:f.write(f'- Published {name}: {manifest["engine"]} {manifest["device"]}, {manifest["resolution"]} px, {manifest["samples"]} samples; not GPU approval.\n')
print('REVIEW_READY',V/f'settler-{name}.png')

# Controlled stop between stages, after publishing; never kill a running render.
if (M/'pause-after-review').exists():
    (M/'pause-after-review').unlink()
    print('STOP_REQUESTED_AFTER_REVIEW')
    sys.exit(75)
