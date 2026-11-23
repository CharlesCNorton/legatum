"""Review, temporal-stable painting grade, trimmed atlas, validation and driver MP4."""
import hashlib,io,json,os,subprocess,sys,tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/barbarian-crossbowman';V=R/'review/3d-v2';SLUG='barbarian-crossbowman';CREAM=(233,207,160,255)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
P=Image.open(f'app/src/assets/units/{SLUG}-256.png').convert('RGBA')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def log(s):
    with (V/f'{SLUG}-log.md').open('a') as f:f.write('- '+s+'\n')
def backdrop(im):
    out=Image.new('RGBA',im.size,CREAM);out.alpha_composite(im);return out

def quantiles(im,c):
    h=im.getchannel(c).histogram(mask=im.getchannel('A').point(lambda x:255 if x>128 else 0));total=sum(h);out=[]
    for k in range(17):
        threshold=total*(.02+.96*k/16);acc=0
        for j,n in enumerate(h):
            acc+=n
            if acc>=threshold:out.append(j);break
    return out

def fit_grade(rest):
    luts=[];stats={}
    for c in 'RGB':
        a=quantiles(rest,c);b=quantiles(P,c);lut=[]
        for x in range(256):
            if x<=a[0]:target=x+b[0]-a[0]
            elif x>=a[-1]:target=x+b[-1]-a[-1]
            else:
                k=next(i for i in range(16) if a[i]<=x<=a[i+1]);t=(x-a[k])/max(1,a[k+1]-a[k]);target=b[k]+t*(b[k+1]-b[k])
            lut.append(round(max(0,min(255,.6*x+.4*target))))
        luts.append(lut);stats[c]={'render':a,'painting':b}
    (M/'grade.json').write_text(json.dumps({'luts':luts,'quantiles':stats,'model_sha256':digest(M/'model.blend'),'method':'One rest-derived 17-quantile RGB transfer at 40 percent for every frame'},indent=2))

def grade(im):
    luts=json.loads((M/'grade.json').read_text())['luts'];return Image.merge('RGBA',[im.getchannel(c).point(l) for c,l in zip('RGB',luts)]+[im.getchannel('A')])

def review(stage,size):
    folder=M/'renders'/str(size)/stage;manifest=json.loads((folder/'render.json').read_text());raw=[Image.open(folder/f'{i:02d}.png').convert('RGBA') for i in range(manifest['frames'])]
    if stage=='c':fit_grade(raw[0])
    ims=raw if stage=='b' else [grade(im) for im in raw]
    # Keep 512 masters and their 256 derivatives, with raw images retained separately.
    for res in ({256,512} if size==512 else {size}):
        dest=M/'frames'/str(res)/stage;dest.mkdir(parents=True,exist_ok=True)
        for i,im in enumerate(ims):im.resize((res,res),Image.Resampling.LANCZOS).save(dest/f'{i:02d}.png')
        (dest/'render.json').write_text(json.dumps({**manifest,'derived_resolution':res,'grade_sha256':digest(M/'grade.json') if stage!='b' else None},indent=2))
    ims=[im.resize((256,256),Image.Resampling.LANCZOS) for im in ims]
    if stage=='b' and len(ims)==3:
        sheet=Image.new('RGBA',(1024,354),CREAM);d=ImageDraw.Draw(sheet);d.text((10,8),'Painting / plain front / three-quarter / side - '+manifest['device'],fill='black')
        for i,im in enumerate([P]+ims):sheet.alpha_composite(im,(i*256,28));sheet.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,286))
        sheet.save(V/f'{SLUG}-b-plain.png');log('b: genuine front, three-quarter and side geometry views.');return
    if stage in ['b','c']:
        sheet=Image.new('RGBA',(768,354),CREAM);d=ImageDraw.Draw(sheet);d.text((10,8),'Painting / true 3D / 50% crossfade - '+manifest['device'],fill='black')
        for i,im in enumerate([P,ims[0],Image.blend(P,ims[0],.5)]):sheet.alpha_composite(im,(i*256,28));sheet.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,286))
        sheet.save(V/(SLUG+('-b-plain.png' if stage=='b' else '-c-textured-lit.png')))
        if stage=='c':
            sheet.save(V/f'{SLUG}-f-restpose-compare.png')
            detail=Image.new('RGBA',(768,290),CREAM);dd=ImageDraw.Draw(detail)
            for j,(label,box) in enumerate([('hood / face',(108,10,160,64)),('quilt / belt',(92,64,177,141)),('crossbow',(63,100,133,218))]):
                dd.text((j*256+8,8),label,fill='black')
                for k,im in enumerate([P,ims[0]]):detail.alpha_composite(im.crop(box).resize((128,256),Image.Resampling.LANCZOS),(j*256+k*128,28))
            detail.save(V/f'{SLUG}-c-details.png')
    else:
        sheet=Image.new('RGBA',(256*len(ims),348),CREAM);d=ImageDraw.Draw(sheet);d.text((8,8),stage+' '+manifest['device'],fill='black')
        for i,im in enumerate(ims):sheet.alpha_composite(im,(i*256,24));sheet.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,282))
        sheet.save(V/f'{SLUG}-{stage+"-strip" if stage.startswith("e-") else "d-rig-poses"}.png')
        if stage.startswith('e-'):
            frames=[backdrop(im) for im in ims];frames[0].save(V/f'{SLUG}-{stage}.webp',save_all=True,append_images=frames[1:],duration=round(1000/CLIPS[stage[2:]][1]),loop=0,quality=85)
    log(f'{stage}: {len(ims)} frames reviewed at 256/64; {manifest["engine"]} {manifest["device"]}, {manifest["samples"]} samples, source {size}px.')

def pack():
    atlas_dir=Path('app/src/assets/units/anim');atlas_dir.mkdir(parents=True,exist_ok=True)
    meta={'version':2,'layout':'trimmed-rows','frame':{'w':160,'h':160,'ax':80,'ay':140},'clips':{}};rows=[];provenance={};grade_hash=digest(M/'grade.json')
    for row,(name,(count,fps,loop)) in enumerate(CLIPS.items()):
        folder=M/'frames/256'/('e-'+name);render=json.loads((folder/'render.json').read_text());source=M/'clips'/f'{name}.blend'
        assert render['source_sha256']==digest(source),'Stale clip render '+name
        assert render['grade_sha256']==grade_hash,'Stale grade '+name
        clipmeta=json.loads((M/'clips'/f'{name}.json').read_text());assert clipmeta['model_sha256']==digest(M/'model.blend'),'Stale clip model '+name
        frames=[];entries=[];x=1;unique={}
        for i in range(count):
            im=Image.open(folder/f'{i:02d}.png').convert('RGBA').resize((160,160),Image.Resampling.BICUBIC)
            bb=im.getbbox();assert bb,(name,i)
            assert bb[0]>0 and bb[1]>0 and bb[2]<160 and bb[3]<160,('clipping',name,i,bb)
            crop=im.crop(bb);key=im.tobytes();frames.append(crop)
            if key in unique:entry=dict(unique[key])
            else:
                entry={'x':x,'y':0,'w':crop.width,'h':crop.height,'ox':bb[0],'oy':bb[1]};unique[key]=entry;x+=crop.width+2
            entries.append(entry)
        rows.append((frames,entries,x,max(im.height for im in frames)+2));meta['clips'][name]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':entries}
        provenance[name]={'render':render,'frames':[digest(folder/f'{i:02d}.png') for i in range(count)]}
    width=max(r[2] for r in rows);height=sum(r[3] for r in rows);atlas=Image.new('RGBA',(width,height));y=0
    for frames,entries,_,h in rows:
        for im,e in zip(frames,entries):e['y']=y+1;atlas.paste(im,(e['x'],y+1))
        y+=h
    for quality in [90,85,80,75]:
        buf=io.BytesIO();atlas.save(buf,format='WEBP',quality=quality,method=6)
        if len(buf.getvalue())<=200000:break
    else:raise RuntimeError('Atlas exceeds 200 KB at quality 75; refusing degraded delivery')
    meta.update({'atlas':{'w':width,'h':height},'quality':quality})
    (atlas_dir/f'{SLUG}.webp').write_bytes(buf.getvalue());(atlas_dir/f'{SLUG}.json').write_text(json.dumps(meta,indent=2)+'\n')
    (M/'pack.json').write_text(json.dumps({'bytes':len(buf.getvalue()),'quality':quality,'clips':provenance,'atlas_sha256':digest(atlas_dir/f'{SLUG}.webp'),'metadata_sha256':digest(atlas_dir/f'{SLUG}.json')},indent=2))
    validate();log(f'Packed 40 frames, trimmed 160px cells, WebP quality {quality}, {len(buf.getvalue())} bytes.')

def restored(atlas,c,i):
    e=c['rects'][i];im=Image.new('RGBA',(160,160));im.alpha_composite(atlas.crop((e['x'],e['y'],e['x']+e['w'],e['y']+e['h'])),(e['ox'],e['oy']));return im

def validate():
    p=Path(f'app/src/assets/units/anim/{SLUG}.webp');meta=json.loads(p.with_suffix('.json').read_text());atlas=Image.open(p).convert('RGBA');assert p.stat().st_size<=200000;assert meta['quality']>=75;assert atlas.size==(meta['atlas']['w'],meta['atlas']['h']);assert atlas.getchannel('A').getextrema()==(0,255),'Transparency missing';assert meta['frame']=={'w':160,'h':160,'ax':80,'ay':140}
    provenance=json.loads((M/'pack.json').read_text());assert provenance['atlas_sha256']==digest(p);assert provenance['metadata_sha256']==digest(p.with_suffix('.json'));assert provenance['quality']==meta['quality']
    assert json.loads((M/'grade.json').read_text())['model_sha256']==digest(M/'model.blend'),'Stale calibration'
    for name,(count,fps,loop) in CLIPS.items():
        record=provenance['clips'][name];folder=M/'frames/256'/('e-'+name)
        assert record['render']['source_sha256']==digest(M/'clips'/f'{name}.blend'),'Stale rendered clip'
        assert record['render']['grade_sha256']==digest(M/'grade.json'),'Stale frame grade'
        assert json.loads((M/'clips'/f'{name}.json').read_text())['model_sha256']==digest(M/'model.blend'),'Stale model'
        c=meta['clips'][name];assert c['frames']==count and len(c['rects'])==count and c['fps']==fps and c['loop']==loop
        for e in c['rects']:
            assert 0<=e['ox']<160 and 0<=e['oy']<160 and e['ox']+e['w']<=160 and e['oy']+e['h']<=160
            assert e['x']+e['w']<=atlas.width and e['y']+e['h']<=atlas.height
        frames=[restored(atlas,c,i) for i in range(count)];assert len({im.tobytes() for im in frames})>1,'No motion '+name
        for i,frame in enumerate(frames):
            path=folder/f'{i:02d}.png';assert record['frames'][i]==digest(path),'Stale frame bytes'
            original=Image.open(path).convert('RGBA').resize((160,160),Image.Resampling.BICUBIC)
            assert frame.getchannel('A').tobytes()==original.getchannel('A').tobytes(),('Trim alpha mismatch',name,i)
        if name=='death':
            assert frames[-1].tobytes()==frames[-2].tobytes(),'Decoded death is not held'
            # Compare raw settled frames, avoiding lossy tile encoding differences.
            a=Image.open(M/'frames/256/e-death/08.png');b=Image.open(M/'frames/256/e-death/09.png');assert a.tobytes()==b.tobytes(),'Death not held'
    report={'status':'PASS technical only','frames':40,'bytes':p.stat().st_size,'quality':meta['quality'],'trim_offsets':True,'death_held':True}
    (M/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

def video():
    p=Path(f'app/src/assets/units/anim/{SLUG}.webp');meta=json.loads(p.with_suffix('.json').read_text());atlas=Image.open(p).convert('RGBA');frames={n:[restored(atlas,c,i).resize((320,320),Image.Resampling.LANCZOS) for i in range(c['frames'])] for n,c in meta['clips'].items()};out=V/f'{SLUG}-round{os.environ.get("ROUND","2")}.mp4'
    with tempfile.TemporaryDirectory(dir=M) as temp:
        for t in range(240):
            canvas=Image.new('RGBA',(1600,348),CREAM);d=ImageDraw.Draw(canvas)
            for j,(n,c) in enumerate(meta['clips'].items()):
                i=int(t/30*c['fps'])%c['frames'] if c['loop'] else min(int((t%60)/30*c['fps']),c['frames']-1)
                canvas.alpha_composite(frames[n][i],(320*j,28));d.text((320*j+8,8),n,fill='black')
            canvas.convert('RGB').save(f'{temp}/{t:04d}.png')
        subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',f'{temp}/%04d.png','-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)],check=True)
    log('Wrote 8 second five-clip H.264 yuv420p review '+out.name);print(out)

if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='review':review(sys.argv[2],int(os.environ.get('RESOLUTION','256')))
    elif cmd=='pack':pack()
    elif cmd=='validate':validate()
    elif cmd=='video':video()
    else:raise ValueError(cmd)
