"""Native-size reviews, stable painting-derived grade, trimmed 160px atlas and validation."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
import sys,os,json,hashlib,io
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
SLUG='barbarian-archer';M=ROOT/'masters'/SLUG;R=ROOT/'review/3d-v2';A=Path('app/src/assets/units/anim')
C={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
REF=Image.open(f'app/src/assets/units/{SLUG}-256.png').convert('RGBA');BG=(42,37,33,255)
def log(s):
    with (R/f'{SLUG}-log.md').open('a') as f:f.write(s+'\n')
    print(s)
def read(stage):
    res=int(os.environ.get('RESOLUTION','256'));p=M/'renders'/str(res)/stage
    manifest=json.loads((p/'manifest.json').read_text())
    source=M/('refined-plain.blend' if stage=='b' else 'attack.blend' if stage=='d' else stage[2:]+'.blend' if stage.startswith('e-') else 'master.blend')
    if stage=='g-feet':source=M/'move.blend'
    assert manifest['blend_sha256']==hashlib.sha256(source.read_bytes()).hexdigest(), 'Stale render '+stage
    assert manifest['resolution']==res
    return [Image.open(f).convert('RGBA') for f in sorted(p.glob('*.png'))],manifest

def quantiles(im):
    pixels=[p for p in im.get_flattened_data() if p[3]>220]
    return [[sorted(p[c] for p in pixels)[int((len(pixels)-1)*q)] for q in (.05,.25,.5,.75,.95)] for c in range(3)]
def make_grade(im):
    src=quantiles(im);ref=quantiles(REF);luts=[]
    for s,t in zip(src,ref):
        pairs=[(0,0)]+[(x,max(0,min(255,x+max(-24,min(24,(y-x)*.45))))) for x,y in zip(s,t)]+[(255,255)]
        pairs=sorted(dict(pairs).items());lut=[]
        for x in range(256):
            for (a,b),(c,d) in zip(pairs,pairs[1:]):
                if a<=x<=c:lut.append(round(b+(d-b)*(x-a)/max(1,c-a)));break
        luts.append(lut)
    (M/'grade.json').write_text(json.dumps({'method':'Fixed rest-derived 5-quantile RGB transfer, 45%, bounded 24 levels','source':src,'reference':ref,'luts':luts,'rest_sha256':hashlib.sha256(im.tobytes()).hexdigest(),'master_sha256':hashlib.sha256((M/'master.blend').read_bytes()).hexdigest()},indent=2))
def grade(im):
    record=json.loads((M/'grade.json').read_text())
    assert record['master_sha256']==hashlib.sha256((M/'master.blend').read_bytes()).hexdigest(), 'Stale grade'
    g=record['luts'];bands=im.split()
    return Image.merge('RGBA',tuple(bands[c].point(g[c]) for c in range(3))+(bands[3],))
def tile(im,n=256):return im.resize((n,n),Image.Resampling.LANCZOS)
def sheet(images,labels,path,small=True):
    w=256*len(images);out=Image.new('RGBA',(w,352 if small else 286),BG);d=ImageDraw.Draw(out)
    for i,(im,label) in enumerate(zip(images,labels)):
        d.text((i*256+8,7),label,fill='white');out.alpha_composite(tile(im),(i*256,26))
        if small:out.alpha_composite(tile(im,64),(i*256+96,286))
    out.convert('RGB').save(path)
def reviews(stage):
    ims,manifest=read(stage)
    if stage=='c':make_grade(ims[0])
    if stage not in ('b','g-feet'):ims=[grade(im) for im in ims]
    for i,im in enumerate(ims):
        for size in (256,512):
            if size>im.width:continue
            folder=M/str(size)/stage;folder.mkdir(parents=True,exist_ok=True)
            tile(im,size).save(folder/f'{i:02d}.png')
    if stage=='g-feet':
        canvas=Image.new('RGBA',(1024,300),BG);draw=ImageDraw.Draw(canvas)
        for i,im in enumerate(ims):
            x=(i%8)*128;y=(i//8)*150
            draw.text((x+5,y+4),('Front ' if i<8 else 'Top ')+str(i%8+1),fill='white')
            canvas.alpha_composite(tile(im,128),(x,y+20))
        canvas.convert('RGB').save(R/f'{SLUG}-g-feet-check.png')
    elif stage in ('b','c'):
        suffix='b-plain' if stage=='b' else 'c-textured-lit'
        sheet([REF]+ims,['Painting']+[f'3D {manifest["device"]} {i}' for i in range(len(ims))],R/f'{SLUG}-{suffix}.png')
        if stage=='c':
            r=tile(ims[0]);blend=Image.blend(REF,r,.5);split=REF.copy();split.paste(r.crop((128,0,256,256)),(128,0))
            sheet([REF,r,split,blend],['Painting','3D rest','Half split','50/50 crossfade'],R/f'{SLUG}-f-restpose-compare.png')
            boxes=[(65,52,140,115),(70,102,150,171),(142,25,198,141)]
            crops=[];labels=[]
            source=Image.open(ROOT/'assets'/SLUG/'painting-registered.png').convert('RGBA')
            for name,box in zip(['Head/pelt','Straps/cloth','Bow/hand'],boxes):
                sb=tuple(v*4 for v in box);rb=tuple(round(v*ims[0].width/256) for v in box)
                crops.extend([source.crop(sb).resize((256,256)),ims[0].crop(rb).resize((256,256))]);labels.extend([name+' painting',name+' 3D'])
            sheet(crops,labels,R/f'{SLUG}-c-details.png',False)
    elif stage=='d':sheet(ims,['Draw','Anticipation','Release','Recover'],R/f'{SLUG}-d-rig-poses.png')
    elif stage.startswith('e-'):
        clip=stage[2:];sheet(ims,[f'{clip} {i+1}' for i in range(len(ims))],R/f'{SLUG}-e-{clip}-strip.png')
        frames=[tile(im) for im in ims];frames[0].save(R/f'{SLUG}-e-{clip}.webp',save_all=True,append_images=frames[1:],duration=round(1000/C[clip][1]),loop=0,quality=85,method=6)
    log(f'Published {stage} review immediately; {manifest["device"]} preview, not art approval.')

def cell160(im):
    return im.convert('RGBa').resize((160,160),Image.Resampling.BICUBIC).convert('RGBA')

def pack():
    rest,rest_manifest=read('c')
    calibration=json.loads((M/'grade.json').read_text())
    assert calibration['rest_sha256']==hashlib.sha256(rest[0].tobytes()).hexdigest(), 'Stale rest calibration'
    A.mkdir(parents=True,exist_ok=True);meta={'version':2,'frame':{'w':160,'h':160,'ax':75,'ay':143},'clips':{}};report={};can=Image.new('RGBA',(1600,800))
    for row,(name,(n,fps,loop)) in enumerate(C.items()):
        raw,manifest=read('e-'+name)
        assert len(raw)==n,(name,len(raw));expected=hashlib.sha256((M/(name+'.blend')).read_bytes()).hexdigest()
        assert manifest['blend_sha256']==expected,'Stale '+name
        rest_manifest=read('c')[1]
        assert all(manifest[k]==rest_manifest[k] for k in ('engine','device','samples','resolution')), 'Mixed render settings'
        assert json.loads((M/(name+'-audit.json')).read_text())['source_master_sha256']==hashlib.sha256((M/'master.blend').read_bytes()).hexdigest(), 'Stale clip master'
        rects=[];hashes=[]
        for i,im in enumerate(raw):
            # Keep both master sizes without discarding the render source.
            g=grade(im)
            for size in (512,256):
                if size>im.width:continue
                folder=M/str(size)/name;folder.mkdir(parents=True,exist_ok=True);tile(g,size).save(folder/f'{i:02d}.png')
            cell=cell160(g);alpha=cell.getchannel('A');box=alpha.getbbox();assert box
            x,y,r,b=box;assert x>0 and y>0 and r<160 and b<160,(name,i,'clipped',box)
            crop=cell.crop(box);can.paste(crop,(i*160,row*160))
            rects.append({'x':i*160,'y':row*160,'w':r-x,'h':b-y,'ox':x,'oy':y})
            hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
        meta['clips'][name]={'row':row,'frames':n,'fps':fps,'loop':loop,'rects':rects}
        report[name]={'render':manifest,'frame_hashes':hashes}
    for quality in (90,85,80,75):
        stream=io.BytesIO();can.save(stream,format='WEBP',quality=quality,method=6)
        if len(stream.getvalue())<=200000:break
    else:raise RuntimeError('Atlas exceeds 200 KB at quality 75')
    (A/f'{SLUG}.webp').write_bytes(stream.getvalue());(A/f'{SLUG}.json').write_text(json.dumps(meta,indent=2)+'\n')
    (M/'pack.json').write_text(json.dumps({'quality':quality,'bytes':len(stream.getvalue()),'grade_sha256':hashlib.sha256((M/'grade.json').read_bytes()).hexdigest(),'clips':report},indent=2))
    decoded_review();validate();log(f'Packed 40 frames at 160px, trimmed offsets, quality {quality}, {len(stream.getvalue())} bytes.')
def decoded_review():
    meta=json.loads((A/f'{SLUG}.json').read_text());atlas=Image.open(A/f'{SLUG}.webp').convert('RGBA')
    ims=[REF];labels=['Painting']
    for clip,index in [('idle',0),('move',2),('attack',4),('hit',1),('death',9)]:
        r=meta['clips'][clip]['rects'][index];cell=Image.new('RGBA',(160,160))
        crop=atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h']))
        cell.paste(crop,(r['ox'],r['oy']));ims.append(cell);labels.append(clip+' decoded 160px')
    sheet(ims,labels,R/f'{SLUG}-g-decoded-atlas.png')

def validate():
    meta=json.loads((A/f'{SLUG}.json').read_text());im=Image.open(A/f'{SLUG}.webp').convert('RGBA');report=json.loads((M/'pack.json').read_text())
    assert im.size==(1600,800);assert (A/f'{SLUG}.webp').stat().st_size<=200000;assert report['quality']>=75
    assert im.getchannel('A').getextrema()==(0,255)
    assert report['grade_sha256']==hashlib.sha256((M/'grade.json').read_bytes()).hexdigest(), 'Changed grade'
    rest,rest_manifest=read('c')
    calibration=json.loads((M/'grade.json').read_text())
    assert calibration['rest_sha256']==hashlib.sha256(rest[0].tobytes()).hexdigest(), 'Stale rest calibration'
    assert meta['frame']=={'w':160,'h':160,'ax':75,'ay':143}
    for name,(n,fps,loop) in C.items():
        c=meta['clips'][name];assert (c['frames'],c['fps'],c['loop'])==(n,fps,loop);assert len(c['rects'])==n
        hashes=report['clips'][name]['frame_hashes'];assert len(set(hashes))>=2,(name,'static')
        raw,manifest=read('e-'+name)
        assert manifest==report['clips'][name]['render']
        assert all(manifest[k]==rest_manifest[k] for k in ('engine','device','samples','resolution'))
        assert [hashlib.sha256(f.tobytes()).hexdigest() for f in raw]==hashes, 'Changed source pixels'
        for index,r in enumerate(c['rects']):
            assert 0<=r['x'] and 0<=r['y'] and r['x']+r['w']<=im.width and r['y']+r['h']<=im.height
            assert 0<=r['ox'] and 0<=r['oy'] and r['w']+r['ox']<=160 and r['h']+r['oy']<=160
            decoded=Image.new('RGBA',(160,160))
            decoded.paste(im.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']))
            assert decoded.getchannel('A').tobytes()==cell160(grade(raw[index])).getchannel('A').tobytes(),(name,index,'decoded alpha mismatch')
    raw,_=read('e-death');assert ImageChops.difference(raw[-1],raw[-2]).getbbox(alpha_only=False) is None,'Death not held'
    print('PASS: dimensions, size, quality, alpha, 40 frames, offsets, all clips move, held death')
if __name__=='__main__':
    stage=sys.argv[1]
    if stage=='pack':pack()
    elif stage=='validate':validate()
    else:reviews(stage)
