"""Review sheets, fixed temporal grade, trimmed atlas, validation and MP4."""
import os,sys,json,hashlib,subprocess,io,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageStat
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/barbarian-scout';V=R/'review/3d-v2';SLUG='barbarian-scout'
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[4]
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
CREAM=(240,232,214,255);ref=Image.open(REPO/f'app/src/assets/units/{SLUG}-256.png').convert('RGBA')
def log(s):
    with (V/f'{SLUG}-log.md').open('a') as f:f.write(s+'\n')
def composite(im):
    bg=Image.new('RGBA',im.size,CREAM);bg.alpha_composite(im);return bg

def quantiles(im):
    mask=im.getchannel('A').point(lambda x:255 if x>200 else 0)
    # Foreground only: transparency cannot influence the transfer function.
    chans=[]
    for ch in im.convert('RGB').split():
        hist=ch.histogram(mask=mask);total=sum(hist);q=[]
        for f in [i/16 for i in range(17)]:
            cum=0
            for v,n in enumerate(hist):
                cum+=n
                if cum>=total*f:q.append(v);break
        chans.append(q)
    return chans

def grade_lut(raw):
    a,b=quantiles(raw),quantiles(ref);luts=[]
    for x,y in zip(a,b):
        vals=[]
        for v in range(256):
            k=next((i for i in range(15) if x[i]<=v<x[i+1]),15)
            mapped=y[k]+(y[k+1]-y[k])*(v-x[k])/max(1,x[k+1]-x[k])
            vals.append(round(max(0,min(255,.7*v+.3*mapped))))
        # Keep LUT monotonic to avoid contrast reversal.
        for i in range(1,256):vals[i]=max(vals[i],vals[i-1])
        luts.append(vals)
    (M/'grade.json').write_text(json.dumps({'luts':luts,'reference_quantiles':b,'rest_quantiles':a},indent=2))
    return luts

def graded(im,luts):
    return Image.merge('RGBA',tuple(ch.point(lut) for ch,lut in zip(im.split()[:3],luts))+(im.getchannel('A'),))

def sheet(images,labels,path,size=256):
    out=Image.new('RGBA',(len(images)*size,size+28),CREAM);d=ImageDraw.Draw(out)
    for i,(im,label) in enumerate(zip(images,labels)):
        out.alpha_composite(im.resize((size,size),Image.Resampling.LANCZOS),(i*size,28));d.text((i*size+6,8),label,fill=(50,40,30))
    out.save(path)

def stage(name):
    rawdir=M/'renders'/name
    raws=[Image.open(p).convert('RGBA') for p in sorted(rawdir.glob('[0-9][0-9].png'))]
    assert raws,name
    if name=='b':
        sheet([ref]+raws,['Painting','Plain front','Plain three-quarter','Plain side'][:len(raws)+1],V/f'{SLUG}-b-plain.png');log('Published b-plain geometry checkpoint.');return
    if name=='c':luts=grade_lut(raws[0])
    else:luts=json.loads((M/'grade.json').read_text())['luts']
    frames=[graded(im,luts) for im in raws]
    for size in (512,256):
        if size>raws[0].width:continue  # Never manufacture masters by upscaling previews.
        out=M/str(size)/name;out.mkdir(parents=True,exist_ok=True)
        for i,im in enumerate(frames):im.resize((size,size),Image.Resampling.LANCZOS).save(out/f'{i:02}.png')
    manifest=json.loads((rawdir/'render.json').read_text());manifest['grade_sha256']=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest();(M/'256'/name/'render.json').write_text(json.dumps(manifest,indent=2))
    if raws[0].width>=512:(M/'512'/name/'render.json').write_text(json.dumps(manifest,indent=2))
    if name=='c':
        im=frames[0].resize((256,256),Image.Resampling.LANCZOS)
        sheet([ref,im],['Painting 256','3D 256'],V/f'{SLUG}-c-textured-lit.png')
        split=ref.copy();split.paste(im.crop((128,0,256,256)),(128,0))
        blend=Image.blend(composite(ref),composite(im),.5)
        sheet([ref,im,split,blend],['Painting','3D rest','Half split','50/50 crossfade'],V/f'{SLUG}-f-restpose-compare.png')
        sheet([ref,im],['Painting 64','3D 64'],V/f'{SLUG}-f-restpose-64.png',64)
        crops=[(90,12,185,100),(55,55,165,165),(65,115,185,218)]
        ims=[];labels=[]
        for b,label in zip(crops,['Face/fur','Cloth/axe','Knees/boots']):ims += [ref.crop(b),im.crop(b)];labels += ['Painting '+label,'3D '+label]
        sheet(ims,labels,V/f'{SLUG}-c-details.png',192)
    elif name=='d':sheet(frames,['Rig pose '+str(i+1) for i in range(len(frames))],V/f'{SLUG}-d-rig-poses.png')
    elif name.startswith('e-'):
        clip=name[2:];n,fps,loop=CLIPS[clip];assert len(frames)==n
        path=V/f'{SLUG}-e-{clip}-strip.png'
        sheet(frames,[f'{clip} {i+1}' for i in range(n)],path)
        full=Image.open(path).convert('RGBA');strip=Image.new('RGBA',(full.width,full.height+88),CREAM)
        strip.alpha_composite(full);draw=ImageDraw.Draw(strip);draw.text((6,full.height+4),'Native 64 px',fill=(50,40,30))
        for i,im in enumerate(frames):strip.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256,full.height+23))
        strip.save(path)
        previews=[composite(im.resize((256,256),Image.Resampling.LANCZOS)).convert('RGB') for im in frames]
        previews[0].save(V/f'{SLUG}-e-{clip}.webp',save_all=True,append_images=previews[1:],duration=round(1000/fps),loop=0,quality=85)
    log(f'Published {name} review: {manifest["device"]} {manifest["resolution"]} px, {manifest["samples"]} samples; fixed rest-derived grade.')

def pack():
    records={};strips=[];maxw=0;y=0;rawhash={};cliphash={}
    sourcehash=hashlib.sha256((M/'barbarian-scout.blend').read_bytes()).hexdigest()
    gradehash=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest()
    restmanifest=json.loads((M/'256/c/render.json').read_text())
    for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
        d=M/'256'/('e-'+clip);manifest=json.loads((d/'render.json').read_text())
        assert all(manifest[k]==restmanifest[k] for k in ('engine','device','samples','resolution')),(clip,'mixed render settings')
        assert manifest['source_sha256']==sourcehash,(clip,'stale model')
        cliphash[clip]=hashlib.sha256((M/'clips'/clip/(clip+'.blend')).read_bytes()).hexdigest()
        assert manifest['blend_sha256']==cliphash[clip],(clip,'stale clip render')
        assert manifest['grade_sha256']==gradehash,(clip,'stale grade')
        fs=[];cells=[];x=0;rh=0
        for i in range(n):
            path=d/f'{i:02}.png';im=Image.open(path).convert('RGBA').resize((160,160),Image.Resampling.LANCZOS)
            # Quantize alpha only; preserve colour and all 40 frames.
            a=im.getchannel('A').point(lambda v:round(v/17)*17);im.putalpha(a)
            box=a.getbbox();assert box
            left,top,right,bottom=box
            assert left>0 and top>0 and right<160 and bottom<160,(clip,i,'edge clipping',box)
            crop=im.crop(box);fs.append(crop);cells.append({'x':x,'y':y,'w':crop.width,'h':crop.height,'ox':left,'oy':top});x+=crop.width+2;rh=max(rh,crop.height)
            rawhash[f'{clip}/{i:02}']=hashlib.sha256(path.read_bytes()).hexdigest()
        strips.append((fs,cells));records[clip]={'row':row,'frames':n,'fps':fps,'loop':loop,'rects':cells};maxw=max(maxw,x);y+=rh+2
    atlas=Image.new('RGBA',(maxw,y))
    for fs,cells in strips:
        for im,c in zip(fs,cells):atlas.alpha_composite(im,(c['x'],c['y']))
    best=None
    for q in (90,85,80,75):
        out=io.BytesIO();atlas.save(out,format='WEBP',quality=q,method=6,exact=True)
        if len(out.getvalue())<=200000:best=(q,out.getvalue());break
    assert best,'Atlas exceeds 200 KB at quality 75; report rather than reduce quality'
    dest=REPO/'app/src/assets/units/anim';dest.mkdir(parents=True,exist_ok=True)
    meta={'version':2,'unit':SLUG,'frame':{'w':160,'h':160,'ax':80,'ay':140},'atlas':{'w':atlas.width,'h':atlas.height},'clips':records}
    (dest/f'{SLUG}.webp').write_bytes(best[1]);(dest/f'{SLUG}.json').write_text(json.dumps(meta,indent=2)+'\n')
    (M/'pack.json').write_text(json.dumps({'quality':best[0],'bytes':len(best[1]),'frame_hashes':rawhash,'clip_hashes':cliphash,'source_sha256':sourcehash,'grade_sha256':gradehash},indent=2))
    validate();log(f'Packed 40 trimmed 160 px frames, WebP quality {best[0]}, {len(best[1])} bytes.')

def decoded():
    dest=REPO/'app/src/assets/units/anim';meta=json.loads((dest/f'{SLUG}.json').read_text());atlas=Image.open(dest/f'{SLUG}.webp').convert('RGBA');result={}
    for name,c in meta['clips'].items():
        result[name]=[]
        for r in c['rects']:
            im=Image.new('RGBA',(160,160));im.alpha_composite(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));result[name].append(im)
    return meta,atlas,result

def validate():
    meta,atlas,clips=decoded();report=json.loads((M/'pack.json').read_text());assert report['quality']>=75 and report['bytes']<=200000
    assert report['source_sha256']==hashlib.sha256((M/'barbarian-scout.blend').read_bytes()).hexdigest()
    assert report['grade_sha256']==hashlib.sha256((M/'grade.json').read_bytes()).hexdigest()
    rects=[r for c in meta['clips'].values() for r in c['rects']]
    for i,a in enumerate(rects):
        for b in rects[i+1:]:
            assert a['x']+a['w']<=b['x'] or b['x']+b['w']<=a['x'] or a['y']+a['h']<=b['y'] or b['y']+b['h']<=a['y'],'Overlapping packed rectangles'
    dest=REPO/'app/src/assets/units/anim'
    assert (dest/f'{SLUG}.webp').stat().st_size==report['bytes']
    assert atlas.size==(meta['atlas']['w'],meta['atlas']['h'])
    assert meta['frame']=={'w':160,'h':160,'ax':80,'ay':140};assert atlas.getextrema()[3]==(0,255)
    for name,(n,fps,loop) in CLIPS.items():
        assert report['clip_hashes'][name]==hashlib.sha256((M/'clips'/name/(name+'.blend')).read_bytes()).hexdigest(),(name,'stale clip')
        for i in range(n):
            assert report['frame_hashes'][f'{name}/{i:02}']==hashlib.sha256((M/'256'/('e-'+name)/f'{i:02}.png').read_bytes()).hexdigest(),(name,i,'stale frame')
        c=meta['clips'][name];assert len(c['rects'])==c['frames']==n and c['fps']==fps and c['loop']==loop
        for i,(rect,im) in enumerate(zip(c['rects'],clips[name])):
            assert 0<=rect['ox']<160 and rect['ox']+rect['w']<=160
            assert 0<=rect['oy']<160 and rect['oy']+rect['h']<=160
            assert rect['x']+rect['w']<=atlas.width and rect['y']+rect['h']<=atlas.height
            assert im.getchannel('A').getbbox()
            expected=Image.open(M/'256'/('e-'+name)/f'{i:02}.png').convert('RGBA').resize((160,160),Image.Resampling.LANCZOS).getchannel('A').point(lambda v:round(v/17)*17)
            assert im.getchannel('A').tobytes()==expected.tobytes(),(name,i,'decoded alpha differs')
        assert len({im.tobytes() for im in clips[name]})>1,(name,'no motion')
    # Lossy packed colours can differ by location; held death is checked in masters.
    death=[Image.open(M/'256/e-death'/f'{i:02}.png').tobytes() for i in (8,9)]
    assert death[0]==death[1],'Death not held'
    result={'status':'technical checks passed','frames':sum(c['frames'] for c in meta['clips'].values()),'bytes':report['bytes'],'quality':report['quality'],'art_approved':False}
    (M/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

def gpu_check():
    sourcehash=hashlib.sha256((M/'barbarian-scout.blend').read_bytes()).hexdigest()
    for stage_name in ['b','c','d']+['e-'+n for n in CLIPS]:
        raw=M/'renders'/stage_name
        manifest=json.loads((raw/'render.json').read_text())
        assert manifest['device']=='GPU' and manifest['engine']=='CYCLES' and manifest['resolution']==512,(stage_name,'not GPU512')
        assert manifest['source_sha256']==sourcehash,(stage_name,'stale source')
        clip=stage_name[2:] if stage_name.startswith('e-') else 'attack' if stage_name=='d' else None
        blend=M/'clips'/clip/(clip+'.blend') if clip else M/('registered.blend' if stage_name=='b' else 'barbarian-scout.blend')
        assert manifest['blend_sha256']==hashlib.sha256(blend.read_bytes()).hexdigest(),(stage_name,'stale rendered blend')
        for i in range(len(manifest['frames'])):
            assert Image.open(raw/f'{i:02}.png').size==(512,512)
            if stage_name=='b':continue
            for size in (512,256):
                assert Image.open(M/str(size)/stage_name/f'{i:02}.png').size==(size,size)
                saved=json.loads((M/str(size)/stage_name/'render.json').read_text())
                assert saved['blend_sha256']==manifest['blend_sha256']
                assert saved['grade_sha256']==hashlib.sha256((M/'grade.json').read_bytes()).hexdigest()
    print('GPU512_MASTER_GATE_OK')

def video():
    meta,atlas,clips=decoded();fps=30;directory=M/'video';directory.mkdir(exist_ok=True)
    scaled={n:[im.resize((320,320),Image.Resampling.LANCZOS) for im in ims] for n,ims in clips.items()}
    for t in range(240):
        im=Image.new('RGBA',(1600,348),CREAM);draw=ImageDraw.Draw(im)
        for col,(n,c) in enumerate(meta['clips'].items()):
            idx=int(t/fps*c['fps'])%c['frames'] if c['loop'] else min(int((t%60)/fps*c['fps']),c['frames']-1)
            im.alpha_composite(scaled[n][idx],(col*320,28));draw.text((col*320+8,8),n,fill=(50,40,30))
        im.convert('RGB').save(directory/f'{t:04}.png')
    out=V/f'{SLUG}-round{os.environ.get("ROUND","1")}.mp4'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(directory/'%04d.png'),'-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames:format=duration','-of','json',str(out)]))
    stream=probe['streams'][0]
    assert stream['codec_name']=='h264' and stream['pix_fmt']=='yuv420p'
    assert (stream['width'],stream['height'])==(1600,348) and int(stream['nb_frames'])==240
    assert abs(float(probe['format']['duration'])-8)<.05
    (M/'video.json').write_text(json.dumps(probe,indent=2))
    for p in directory.glob('*.png'):p.unlink()
    log('Published five-clip, 2x, cream-background H.264 review: '+out.name)

if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='pack':pack()
    elif cmd=='validate':validate()
    elif cmd=='video':video()
    elif cmd=='gpu-check':gpu_check()
    else:stage(cmd)
