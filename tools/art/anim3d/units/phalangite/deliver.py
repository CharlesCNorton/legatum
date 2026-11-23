"""Frozen histogram grade, review sheets, trimmed atlas and strict artifact checks."""
from pathlib import Path
import os,sys,json,hashlib,io,subprocess
from PIL import Image,ImageDraw,ImageStat
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/phalangite';V=R/'review/3d-v2';A=R/'assets/phalangite'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
REF=Image.open('app/src/assets/units/phalangite-256.png').convert('RGBA')
BG=(233,207,160,255)
def log(msg):
    with (V/'phalangite-log.md').open('a') as f:f.write('- '+msg+'\n')
def quantiles(im):
    mask=im.getchannel('A').point(lambda a:255 if a>220 else 0);out=[]
    for channel in im.convert('RGB').split():
        h=channel.histogram(mask);total=sum(h);v=[]
        for q in [.05,.1,.25,.5,.75,.9,.95]:
            running=0
            for i,count in enumerate(h):
                running+=count
                if running>=total*q:v.append(i);break
        out.append(v)
    return out

def make_grade(im):
    source=quantiles(im);target=quantiles(REF);luts=[]
    for s,t in zip(source,target):
        pairs=[(0,0)]+list(zip(s,t))+[(255,255)];lut=[]
        for x in range(256):
            j=next((j for j in range(len(pairs)-1) if pairs[j+1][0]>=x),len(pairs)-2);a,b=pairs[j],pairs[j+1]
            y=a[1]+(b[1]-a[1])*(x-a[0])/max(1,b[0]-a[0]);lut.append(round(max(0,min(255,x+max(-24,min(24,(y-x)*.45))))))
        luts.append(lut)
    (M/'grade.json').write_text(json.dumps({'source_quantiles':source,'painting_quantiles':target,'luts':luts},indent=2))

def grade(im):
    luts=json.loads((M/'grade.json').read_text())['luts'];rgb=im.convert('RGB').point(sum(luts,[]));rgb.putalpha(im.getchannel('A'));return rgb

def sheet(images,labels,path):
    w=256*len(images);out=Image.new('RGBA',(w,364),BG);d=ImageDraw.Draw(out)
    for i,(im,label) in enumerate(zip(images,labels)):
        im=im.resize((256,256),Image.Resampling.LANCZOS);out.alpha_composite(im,(i*256,24));out.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,292));d.text((i*256+8,5),label,fill=(43,31,19))
    out.convert('RGB').save(path)

def review(stage,res):
    directory=M/'renders'/str(res)/stage;raw=[Image.open(p).convert('RGBA') for p in sorted(directory.glob('[0-9][0-9].png'))]
    if stage=='c':make_grade(raw[0])
    frames=raw if stage=='b' else [grade(im) for im in raw]
    for size in [256]+([512] if res==512 else []):
        dest=M/str(size)/stage;dest.mkdir(parents=True,exist_ok=True)
        for i,im in enumerate(frames):im.resize((size,size),Image.Resampling.LANCZOS).save(dest/f'{i:02}.png')
    labels=[f'{stage} {i+1}' for i in range(len(frames))]
    suffix={'b':'b-plain','c':'c-textured-lit','d':'d-rig-poses'}.get(stage,stage+'-strip')
    sheet([REF]+frames,['Painting']+labels,V/f'phalangite-{suffix}.png')
    if stage=='c':
        im=frames[0].resize((256,256),Image.Resampling.LANCZOS);blend=Image.blend(REF,im,.5);split=REF.copy();split.paste(im.crop((128,0,256,256)),(128,0))
        sheet([REF,im,split,blend],['Painting','3D rest','Half split','50/50 crossfade'],V/'phalangite-f-restpose-compare.png')
        boxes=[(61,47,106,91),(48,88,128,146),(94,95,140,150)]
        highref=Image.open(A/'painting-aligned.png').convert('RGBA')
        details=[]
        for box in boxes:
            for x in [highref,frames[0]]:
                scale=x.width/256;details.append(x.crop(tuple(round(v*scale) for v in box)))
        sheet(details,['Painting head','3D head','Painting torso','3D torso','Painting shield','3D shield'],V/'phalangite-c-details.png')
    if stage.startswith('e-'):
        c=stage[2:];seq=[im.resize((256,256),Image.Resampling.LANCZOS) for im in frames]
        seq[0].save(V/f'phalangite-e-{c}.webp',save_all=True,append_images=seq[1:],duration=round(1000/CLIPS[c][1]),loop=0,quality=85,method=6)
    log(f'Published {stage} review from {res}px {json.loads((directory/"render.json").read_text())["device"]} renders.')

def pack():
    records={};atlas=Image.new('RGBA',(1600,800));frame_hashes={};manifests={}
    for row,(name,(count,fps,loop)) in enumerate(CLIPS.items()):
        paths=sorted((M/'256'/f'e-{name}').glob('[0-9][0-9].png'));assert len(paths)==count,(name,len(paths))
        metadata=[];previous=None
        for i,p in enumerate(paths):
            im=Image.open(p).convert('RGBA').resize((160,160),Image.Resampling.BICUBIC)
            box=im.getchannel('A').getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<160 and box[3]<160,(name,i,'clipped',box)
            crop=im.crop(box)
            if previous==im.tobytes():
                metadata.append(metadata[-1].copy())
            else:
                atlas.alpha_composite(crop,(i*160,row*160));metadata.append({'x':i*160,'y':row*160,'w':crop.width,'h':crop.height,'ox':box[0],'oy':box[1]})
            previous=im.tobytes();frame_hashes[str(p.relative_to(M))]=hashlib.sha256(p.read_bytes()).hexdigest()
        records[name]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':metadata}
        a=Image.open(paths[0]);b=Image.open(paths[count//2]);assert a.tobytes()!=b.tobytes(),name+' has no motion'
        if name=='death':assert Image.open(paths[-1]).tobytes()==Image.open(paths[-2]).tobytes(),'death must hold'
        manifest=M/'renders'/os.environ.get('RESOLUTION','256')/f'e-{name}'/'render.json'
        info=json.loads(manifest.read_text());assert info['blend_sha256']==hashlib.sha256((M/'clips'/f'{name}.blend').read_bytes()).hexdigest(),'stale clip'
        assert info['master_sha256']==hashlib.sha256((M/'phalangite.blend').read_bytes()).hexdigest(),'stale master'
        assert info['grade_sha256']==hashlib.sha256((M/'grade.json').read_bytes()).hexdigest(),'stale grade'
        manifests[name]=info
    # Fixed 160px slots with independently trimmed rectangles; offsets reconstruct original canvas.
    output=Path('app/src/assets/units/anim');output.mkdir(parents=True,exist_ok=True)
    for quality in [90,85,80,75]:
        b=io.BytesIO();atlas.save(b,format='WEBP',quality=quality,method=6)
        if len(b.getvalue())<=200000:break
    else:raise RuntimeError('Atlas exceeds 200KB at quality75; keep all frames and report')
    (output/'phalangite.webp').write_bytes(b.getvalue())
    meta={'version':2,'frame':{'w':160,'h':160,'ax':53,'ay':144},'clips':records}
    (output/'phalangite.json').write_text(json.dumps(meta,indent=2)+'\n')
    report={'atlas_sha256':hashlib.sha256(b.getvalue()).hexdigest(),'quality':quality,'bytes':len(b.getvalue()),'frames':40,'resampler':'bicubic','frame_hashes':frame_hashes,'renders':manifests,'grade_sha256':hashlib.sha256((M/'grade.json').read_bytes()).hexdigest()}
    (M/'pack.json').write_text(json.dumps(report,indent=2));validate();log(f'Packed all 40 frames, WebP quality {quality}, {len(b.getvalue())} bytes; validation passed.')

def validate():
    out=Path('app/src/assets/units/anim');im=Image.open(out/'phalangite.webp').convert('RGBA');meta=json.loads((out/'phalangite.json').read_text());assert im.size==(1600,800)
    report=json.loads((M/'pack.json').read_text());assert report['atlas_sha256']==hashlib.sha256((out/'phalangite.webp').read_bytes()).hexdigest()
    for path,digest in report['frame_hashes'].items():assert hashlib.sha256((M/path).read_bytes()).hexdigest()==digest,'Changed packed frame: '+path
    assert report['grade_sha256']==hashlib.sha256((M/'grade.json').read_bytes()).hexdigest()
    assert report['quality']>=75 and (out/'phalangite.webp').stat().st_size<=200000
    for name,(count,fps,loop) in CLIPS.items():
        c=meta['clips'][name];assert (c['frames'],c['fps'],c['loop'])==(count,fps,loop);assert len(c['rects'])==count
        for i,r in enumerate(c['rects']):
            assert 0<=r['x'] and 0<=r['y'] and r['x']+r['w']<=im.width and r['y']+r['h']<=im.height
            assert 0<=r['ox']<160 and 0<=r['oy']<160 and r['ox']+r['w']<=160 and r['oy']+r['h']<=160
            tile=im.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h']));assert tile.getchannel('A').getextrema()[1]>0
            reconstructed=Image.new('RGBA',(160,160));reconstructed.alpha_composite(tile,(r['ox'],r['oy']))
            source=Image.open(M/'256'/f'e-{name}'/f'{i:02}.png').convert('RGBA').resize((160,160),Image.Resampling.BICUBIC)
            assert reconstructed.getchannel('A').tobytes()==source.getchannel('A').tobytes(), (name,i,'decoded alpha differs')
            slot=im.crop((r['x'],r['y'],r['x']+160,r['y']+160));slot.paste((0,0,0,0),(0,0,r['w'],r['h']));assert slot.getchannel('A').getextrema()==(0,0),'Opaque atlas padding'
        if name=='death':assert c['rects'][-1]==c['rects'][-2], 'Decoded death must hold without lossy RGB flicker'
        info=report['renders'][name]
        assert info['master_sha256']==hashlib.sha256((M/'phalangite.blend').read_bytes()).hexdigest(),'stale packed master'
        assert info['blend_sha256']==hashlib.sha256((M/'clips'/f'{name}.blend').read_bytes()).hexdigest(),'stale packed clip'
        for i in range(count,10):assert im.crop((i*160,c['row']*160,(i+1)*160,(c['row']+1)*160)).getchannel('A').getextrema()==(0,0),'Unused slot is not transparent'
    print('PASS: 40 transparent frames, five clips, 160px trim offsets, anchor, WebP quality and size, held death, hashes')

def movie():
    meta=json.loads(Path('app/src/assets/units/anim/phalangite.json').read_text());atlas=Image.open('app/src/assets/units/anim/phalangite.webp').convert('RGBA')
    movie_dir=M/'movie';movie_dir.mkdir(exist_ok=True)
    for f in range(192):
        canvas=Image.new('RGB',(1600,360),BG[:3]);d=ImageDraw.Draw(canvas)
        for col,(name,c) in enumerate(meta['clips'].items()):
            idx=int(f*c['fps']/24)%c['frames'];r=c['rects'][idx];cell=Image.new('RGBA',(160,160));cell.alpha_composite(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));large=cell.resize((320,320),Image.Resampling.LANCZOS);canvas.paste(large,(col*320,30),large);d.text((col*320+10,8),name,fill=(45,30,20))
        canvas.save(movie_dir/f'{f:03}.png')
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','24','-i',str(movie_dir/'%03d.png'),'-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','20',str(V/f'phalangite-round{os.environ.get("ROUND","1")}.mp4')],check=True)
    video=V/f'phalangite-round{os.environ.get("ROUND","1")}.mp4'
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
    stream=probe['streams'][0];assert stream['codec_name']=='h264' and stream['pix_fmt']=='yuv420p'
    assert (stream['width'],stream['height'])==(1600,360)
    assert int(stream['nb_frames'])==192 and abs(float(probe['format']['duration'])-8)<.05
    (M/'video-report.json').write_text(json.dumps({'path':str(video),'frames':192,'duration':8,'width':stream['width'],'height':stream['height'],'codec':stream['codec_name'],'pixel_format':stream['pix_fmt']},indent=2))
    print('MP4_READY: verified H.264/yuv420p, 192 frames, 8 seconds')
def gpu_check():
    master_hash=hashlib.sha256((M/'phalangite.blend').read_bytes()).hexdigest()
    for stage,count in [('b',3),('c',1),('d',4)]+[(f'e-{n}',v[0]) for n,v in CLIPS.items()]:
        info=json.loads((M/'renders/512'/stage/'render.json').read_text())
        assert (info['engine'],info['device'],info['resolution'],info['samples'])==('CYCLES','GPU',512,int(os.environ.get('SAMPLES','64'))), 'Not current GPU512 evidence: '+stage
        assert info['master_sha256']==master_hash, 'Stale GPU master: '+stage
        blend=M/'clips'/f'{stage[2:]}.blend' if stage.startswith('e-') else M/'clips/attack.blend' if stage=='d' else M/('fitted-plain.blend' if stage=='b' else 'phalangite.blend')
        assert info['blend_sha256']==hashlib.sha256(blend.read_bytes()).hexdigest(), 'Stale GPU scene: '+stage
        for size in [512,256]:
            paths=sorted((M/str(size)/stage).glob('[0-9][0-9].png'))
            assert len(paths)==count, (stage,size,'missing masters')
            assert all(Image.open(p).size==(size,size) for p in paths)
    feet=json.loads((M/'feet.json').read_text())
    assert feet['device']=='GPU', 'Feet diagnostic must use GPU'
    assert feet['source_sha256']==hashlib.sha256((M/'clips/move.blend').read_bytes()).hexdigest(), 'Stale feet diagnostic'
    assert len(feet['files'])==16
    for item in feet['files']:
        assert hashlib.sha256((M/item['path']).read_bytes()).hexdigest()==item['sha256']
    print('PASS: all 48 current GPU512 masters, matching 256 copies and 16 GPU feet views')

def receipt():
    gpu_check()
    validate()
    report={'round':os.environ.get('ROUND','2'),'status':'complete','visual_approval':False,
            'master_sha256':hashlib.sha256((M/'phalangite.blend').read_bytes()).hexdigest(),
            'pack':json.loads((M/'pack.json').read_text()),'video':json.loads((M/'video-report.json').read_text())}
    (V/f"phalangite-gpu-round{report['round']}.json").write_text(json.dumps(report,indent=2))

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='review':review(sys.argv[2],int(sys.argv[3]))
    elif mode=='pack':pack()
    elif mode=='validate':validate()
    elif mode=='movie':movie()
    elif mode=='gpu-check':gpu_check()
    elif mode=='receipt':receipt()
