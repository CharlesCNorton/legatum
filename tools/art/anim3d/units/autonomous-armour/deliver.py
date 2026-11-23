"""Review, frozen histogram grade, trimmed atlas, validation and decoded-atlas MP4."""
import sys, os, json, hashlib, io, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageStat, ImageOps
from common import MASTER, REVIEW, ASSETS, HERE, SLUG, CLIPS, log
OUT=Path('app/src/assets/units/anim');OUT.mkdir(parents=True,exist_ok=True)
CREAM=(240,232,214,255)
def read(p):return Image.open(p).convert('RGBA')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def small(im,n):return im.resize((n,n),Image.Resampling.LANCZOS)
def token(im):
    # Premultiplied reduction avoids colour bleed and Lanczos perimeter ringing;
    # keep the resulting antialiased 8-bit alpha exactly in WebP.
    return im.convert('RGBa').resize((160,160),Image.Resampling.BICUBIC).convert('RGBA')
def sheet(images,labels,path,n=256):
    out=Image.new('RGBA',(n*len(images),n+28),CREAM);d=ImageDraw.Draw(out)
    for i,(im,label) in enumerate(zip(images,labels)):
        out.alpha_composite(small(im,n),(i*n,28));d.text((i*n+8,7),label,fill='#423a30')
    out.convert('RGB').save(path)
def quantiles(im):
    data=[p[:3] for p in im.get_flattened_data() if p[3]>240]
    return [[sorted(p[c] for p in data)[int((len(data)-1)*q)] for q in (.1,.5,.9)] for c in range(3)]
def make_grade(src,ref):
    before=quantiles(src);target=quantiles(ref);luts=[]
    for a,b in zip(before,target):
        pairs=[(0,0)]+list(zip(a,b))+[(255,255)];lut=[]
        for value in range(256):
            lo,hi=next((lo,hi) for lo,hi in zip(pairs,pairs[1:]) if lo[0]<=value<=hi[0])
            v=lo[1]+(hi[1]-lo[1])*(value-lo[0])/max(1,hi[0]-lo[0]);lut.append(round(max(0,min(255,max(value-24,min(value+24,v))))))
        luts.append(lut)
    report={'method':'rest-pose opaque RGB 10/50/90 percentiles, bounded to 24 levels; frozen across motion','before':before,'target':target,'luts':luts}
    (MASTER/'grade.json').write_text(json.dumps(report,indent=2));return luts

def review(stage):
    folder=MASTER/'renders'/stage;meta=json.loads((folder/'render.json').read_text())
    ref=read(Path(f'app/src/assets/units/{SLUG}-256.png'))
    if stage=='b':
        for name in meta['frames']:
            im=read(folder/name)
            for n in (512,256):
                if im.width>=n:
                    dest=MASTER/str(n)/stage;dest.mkdir(parents=True,exist_ok=True);small(im,n).save(dest/name)
        sheet([ref]+[read(folder/f'{v}.png') for v in ['rest','side','front']],['Painting','Plain rest','Side geometry','Front geometry'],REVIEW/f'{SLUG}-b-plain.png');return
    luts=make_grade(read(folder/'rest.png'),ref) if stage=='c' else json.loads((MASTER/'grade.json').read_text())['luts']
    gradehash=sha(MASTER/'grade.json');images=[]
    for name,expected in meta['frames'].items():
        p=folder/name;assert sha(p)==expected,f'Raw render changed: {p}'
        im=read(p);r,g,b,a=im.split();im=Image.merge('RGBA',(r.point(luts[0]),g.point(luts[1]),b.point(luts[2]),a))
        # Never upscale a CPU preview into a 512 master.
        for n in (512,256):
            if im.width>=n:
                dest=MASTER/str(n)/stage;dest.mkdir(parents=True,exist_ok=True);small(im,n).save(dest/name)
        images.append(small(im,256))
    meta['grade_sha256']=gradehash
    meta['exports']={str(n):{name:sha(MASTER/str(n)/stage/name) for name in meta['frames']}
                     for n in (256,512) if meta['resolution']>=n}
    (folder/'graded.json').write_text(json.dumps(meta,indent=2))
    if stage=='c':
        sheet([ref,images[0]],['Painting','Cycles rest'],REVIEW/f'{SLUG}-c-textured-lit.png')
        canvas=Image.new('RGBA',(768,376),CREAM);d=ImageDraw.Draw(canvas)
        for i,(im,label) in enumerate([(ref,'Painting'),(images[0],'3D rest'),(Image.blend(ref,images[0],.5),'50/50 crossfade')]):
            canvas.alpha_composite(im,(256*i,28));token=read(Path(f'app/src/assets/units/{SLUG}-64.png')) if i==0 else small(im,64);canvas.alpha_composite(token,(256*i+96,302));d.text((256*i+8,8),label,fill='#423a30')
        canvas.convert('RGB').save(REVIEW/f'{SLUG}-f-restpose-compare.png')
    elif stage=='details':
        # Compare identical camera-space regions without changing aspect ratio.
        # The separately rendered close view remains a master, but its camera
        # cannot be used as a registration comparison against the painting.
        canvas=Image.new('RGBA',(512,3*284),CREAM);draw=ImageDraw.Draw(canvas)
        regions=[('Turret',(48,18,220,126)),('Running gear',(12,124,142,218)),('Stone',(10,180,246,239))]
        reference=read(ASSETS/'projection.png')
        for row,(label,box) in enumerate(regions):
            for col,im in enumerate((reference,read(MASTER/'256'/'details'/'rest.png'))):
                scale=im.width/256;crop=im.crop(tuple(round(v*scale) for v in box))
                crop=ImageOps.contain(crop,(256,256),Image.Resampling.LANCZOS)
                canvas.alpha_composite(crop,(col*256+(256-crop.width)//2,row*284+28+(256-crop.height)//2))
                draw.text((col*256+8,row*284+8),f'{label}: {"Painting" if col==0 else "3D"}',fill='#423a30')
        canvas.convert('RGB').save(REVIEW/f'{SLUG}-c-details.png')
    elif stage=='d':sheet(images,['Ready','Aim','Recoil','Recovery'],REVIEW/f'{SLUG}-d-rig-poses.png')
    elif stage=='g':
        canvas=Image.new('RGBA',(128*8,156*2),CREAM);draw=ImageDraw.Draw(canvas)
        for i,im in enumerate(images):
            x=i%8*128;y=i//8*156
            canvas.alpha_composite(small(im,128),(x,y+28))
            draw.text((x+5,y+7),f'{"Top +X travel" if i<8 else "Front track contact"} {i%8+1}',fill='#423a30')
        canvas.convert('RGB').save(REVIEW/f'{SLUG}-g-feet-check.png')
    else:
        clip=stage[2:];sheet(images,[f'{clip} {i+1}' for i in range(len(images))],REVIEW/f'{SLUG}-{stage}-strip.png')
        images[0].save(REVIEW/f'{SLUG}-{stage}.webp',save_all=True,append_images=images[1:],duration=round(1000/CLIPS[clip][1]),loop=0,quality=90,method=6)
    log(f'Published {stage} review immediately; frozen grade {gradehash[:12]}, 256 masters retained.')

def pack():
    records={};frames={};maxwidth=0;rowheights=[];manifest={};masterhash=sha(MASTER/'finished.blend')
    for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
        folder=MASTER/'renders'/f'e-{clip}';report=json.loads((folder/'graded.json').read_text());manifest[clip]=report
        assert report['master_sha256']==masterhash,'Stale clip render'
        assert report['grade_sha256']==sha(MASTER/'grade.json'),'Stale rest-pose grade'
        assert report['blend_sha256']==sha(MASTER/'clips'/f'{clip}.blend'),'Clip rebuilt after render'
        assert report['resolution']>=256,'No upscaled thumbnails'
        if os.environ.get('CYCLES_DEVICE')=='GPU':
            assert report['device']=='GPU' and report['resolution']==512,'GPU handoff must produce fresh 512 masters'
        x=0;rh=0;entries=[];seen={}
        for i in range(count):
            name=f'{i:02}.png';assert sha(folder/name)==report['frames'][name],'Changed raw render'
            im=token(read(MASTER/'256'/f'e-{clip}'/name))
            # Keep the full alpha, including antialiased antennas. No alpha quantization.
            box=im.getchannel('A').getbbox();assert box
            x0,y0,x1,y1=box;crop=im.crop(box);frames[(clip,i)]=crop
            key=(crop.size,hashlib.sha256(crop.tobytes()).hexdigest())
            packed_x=seen.get(key,x)
            if key not in seen:seen[key]=x;x+=crop.width+2
            entries.append({'x':packed_x,'y':0,'w':crop.width,'h':crop.height,'ox':x0,'oy':y0});rh=max(rh,crop.height)
        maxwidth=max(maxwidth,x);rowheights.append(rh+2)
        records[clip]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':entries}
    assert len({r['grade_sha256'] for r in manifest.values()})==1
    atlas=Image.new('RGBA',(maxwidth,sum(rowheights)));y=0
    for clip,height in zip(CLIPS,rowheights):
        for i,e in enumerate(records[clip]['rects']):e['y']=y;atlas.paste(frames[(clip,i)],(e['x'],e['y']))
        y+=height
    for quality in [95,90,85,80,75]:
        buf=io.BytesIO();atlas.save(buf,format='WEBP',quality=quality,method=6,exact=True,alpha_quality=100)
        print(f'WebP quality {quality}: {len(buf.getvalue())} bytes',flush=True)
        if len(buf.getvalue())<=200000:break
    else:raise RuntimeError('Cannot meet 200000 bytes at quality >=75; preserve frames and report')
    meta={'format':'trimmed-v1','frame':{'w':160,'h':160,'ax':80,'ay':139},'atlas':{'w':atlas.width,'h':atlas.height},'clips':records}
    (OUT/f'{SLUG}.webp').write_bytes(buf.getvalue());(OUT/f'{SLUG}.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
    report={'resampler':'premultiplied bicubic; exact 8-bit alpha','bytes':len(buf.getvalue()),'quality':quality,'frames':40,'master_sha256':masterhash,'atlas_sha256':sha(OUT/f'{SLUG}.webp'),'renders':manifest}
    (REVIEW/f'{SLUG}-pack.json').write_text(json.dumps(report,indent=2));log(f'Packed 40 trimmed 160 px frames: {report["bytes"]} bytes, WebP quality {quality}.')

def decoded():
    meta=json.loads((OUT/f'{SLUG}.json').read_text());atlas=read(OUT/f'{SLUG}.webp');clips={}
    for name,c in meta['clips'].items():
        clips[name]=[]
        for e in c['rects']:
            im=Image.new('RGBA',(160,160));im.paste(atlas.crop((e['x'],e['y'],e['x']+e['w'],e['y']+e['h'])),(e['ox'],e['oy']));clips[name].append(im)
    return meta,atlas,clips

def validate():
    meta,atlas,clips=decoded();packreport=json.loads((REVIEW/f'{SLUG}-pack.json').read_text())
    assert meta['frame']=={'w':160,'h':160,'ax':80,'ay':139};assert atlas.size==(meta['atlas']['w'],meta['atlas']['h'])
    assert packreport['atlas_sha256']==sha(OUT/f'{SLUG}.webp');assert 75<=packreport['quality']<=100
    assert packreport['master_sha256']==sha(MASTER/'finished.blend'),'Atlas predates master'
    assert (OUT/f'{SLUG}.webp').stat().st_size<=200000
    motion={};bounds={}
    for row,(name,(count,fps,loop)) in enumerate(CLIPS.items()):
        c=meta['clips'][name];assert (c['row'],c['frames'],c['fps'],c['loop'])==(row,count,fps,loop);assert len(c['rects'])==count
        provenance=packreport['renders'][name]
        assert provenance['blend_sha256']==sha(MASTER/'clips'/f'{name}.blend')
        assert provenance['grade_sha256']==sha(MASTER/'grade.json')
        for i,(e,im) in enumerate(zip(c['rects'],clips[name])):
            filename=f'{i:02}.png'
            assert provenance['frames'][filename]==sha(MASTER/'renders'/f'e-{name}'/filename)
            assert provenance['exports']['256'][filename]==sha(MASTER/'256'/f'e-{name}'/filename)
            assert all(isinstance(e[k],int) for k in ['x','y','w','h','ox','oy'])
            assert 0<=e['x'] and e['x']+e['w']<=atlas.width and 0<=e['y'] and e['y']+e['h']<=atlas.height
            assert 0<=e['ox'] and e['ox']+e['w']<=160 and 0<=e['oy'] and e['oy']+e['h']<=160
            box=im.getchannel('A').point(lambda a:255 if a>16 else 0).getbbox();assert box and min(box[:2])>=1 and max(box[2:])<=159,f'{name} {i} clipped {box}'
            if os.environ.get('CYCLES_DEVICE')=='GPU':
                assert read(MASTER/'512'/f'e-{name}'/f'{i:02}.png').size==(512,512)
            expected=token(read(MASTER/'256'/f'e-{name}'/f'{i:02}.png'))
            assert im.getchannel('A').tobytes()==expected.getchannel('A').tobytes(),f'{name}/{i} alpha/trim reconstruction changed'
            bounds[f'{name}/{i}']=box
        motion[name]=any(ImageChops.difference(clips[name][0],im).getbbox(alpha_only=False) for im in clips[name][1:]);assert motion[name]
    a=read(MASTER/'256/e-death/08.png');b=read(MASTER/'256/e-death/09.png');assert a.tobytes()==b.tobytes(),'Death not held'
    loop_seams={}
    for name in ['idle','move']:
        frames=clips[name]
        def difference(a,b):return sum(ImageStat.Stat(ImageChops.difference(a,b).convert('RGB')).mean)/3
        internal=[difference(a,b) for a,b in zip(frames,frames[1:])]
        loop_seams[name]=difference(frames[-1],frames[0])/max(internal)
        assert loop_seams[name]<2,f'{name} loop boundary exceeds twice the largest internal step'
    result={'loop_seam_ratio':loop_seams,'contract':'PASS','frames':40,'motion':motion,'held_death':True,'bounds':bounds,'bytes':packreport['bytes'],'quality':packreport['quality'],'art_approval':False}
    (REVIEW/f'{SLUG}-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));log('Validation PASS: counts, RGBA, rect bounds, transparent margins, five moving clips, held death, quality and size. Art approval remains separate.')

def movie():
    meta,atlas,clips=decoded();dest=REVIEW/f'{SLUG}-round{os.environ.get("ROUND","1")}.mp4';w=160*2*5;h=160*2+28
    process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{w}x{h}','-framerate','30','-i','-','-an','-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(dest)],stdin=subprocess.PIPE)
    for t in range(240):
        canvas=Image.new('RGBA',(w,h),CREAM);d=ImageDraw.Draw(canvas)
        for k,(name,frames) in enumerate(clips.items()):
            c=meta['clips'][name];i=int(t/30*c['fps'])%len(frames) if c['loop'] else min(int((t%60)/30*c['fps']),len(frames)-1)
            canvas.alpha_composite(small(frames[i],320),(k*320,28));d.text((k*320+8,8),name,fill='#423a30')
        process.stdin.write(canvas.convert('RGB').tobytes())
    process.stdin.close();assert process.wait()==0
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(dest)]));s=probe['streams'][0]
    assert s['codec_name']=='h264' and s['pix_fmt']=='yuv420p' and s['nb_frames']=='240';assert float(s['duration'])==8
    (REVIEW/f'{SLUG}-video-validation.json').write_text(json.dumps({'path':str(dest),'width':s['width'],'height':s['height'],'frames':240,'duration':8,'codec':s['codec_name'],'pixel_format':s['pix_fmt']},indent=2));log(f'Encoded and ffprobe-verified {dest.name}: 8 s, 240 frames, 1600x348 H.264 yuv420p; decoded trimmed atlas.')

def verify_build():
    assert not (MASTER/'build-pending').exists(),'Interrupted build'
    inputs=json.loads((MASTER/'build-inputs.json').read_text())
    for section,root in [('scripts',HERE),('assets',ASSETS),('scenes',MASTER)]:
        for name,expected in inputs[section].items():
            assert sha(root/name)==expected,f'Rebuild required: {section}/{name} changed'
    print('Current generator, asset and saved-scene hashes verified.')

def verify_gpu():
    """Independently reject CPU, stale, incomplete or mismatched final evidence."""
    verify_build()
    masterhash=sha(MASTER/'finished.blend');stages={'b':3,'c':1,'details':2,'d':4,'g':16}
    stages.update({f'e-{name}':count for name,(count,_,_) in CLIPS.items()})
    for stage,count in stages.items():
        folder=MASTER/'renders'/stage
        report=json.loads((folder/'render.json').read_text())
        assert report['engine']=='CYCLES' and report['device']=='GPU',f'{stage}: not GPU'
        assert report['resolution']==512 and report['samples']==int(os.environ.get('SAMPLES','96'))
        assert len(report['frames'])==count,f'{stage}: incomplete stage'
        clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else 'move' if stage=='g' else None
        blend=MASTER/'clips'/f'{clip}.blend' if clip else MASTER/('plain.blend' if stage=='b' else 'finished.blend')
        assert report['blend_sha256']==sha(blend),f'{stage}: stale scene'
        if stage!='b':
            assert report['master_sha256']==masterhash
            graded=json.loads((folder/'graded.json').read_text())
            assert graded['grade_sha256']==sha(MASTER/'grade.json')
        for name,expected in report['frames'].items():
            assert sha(folder/name)==expected
            for n in (256,512):
                path=MASTER/str(n)/stage/name
                assert read(path).size==(n,n)
                if stage!='b':assert sha(path)==graded['exports'][str(n)][name]
    validate()
    audit=json.loads((REVIEW/f'{SLUG}-audit.json').read_text())
    assert audit['contract']=='PASS' and audit['master_sha256']==masterhash
    video=REVIEW/f'{SLUG}-round{os.environ.get("ROUND","2")}.mp4'
    stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(video)]))['streams'][0]
    assert (stream['codec_name'],stream['pix_fmt'],stream['width'],stream['height'],stream['nb_frames'])==('h264','yuv420p',1600,348,'240')
    assert float(stream['duration'])==8
    receipt={'round':os.environ.get('ROUND','2'),'master_sha256':masterhash,'stages':stages,
             'video_sha256':sha(video),'atlas_sha256':sha(OUT/f'{SLUG}.webp'),'visual_approval':False}
    (REVIEW/f'{SLUG}-gpu-round{receipt["round"]}.json').write_text(json.dumps(receipt,indent=2))
    print('GPU512 / gallery256 / atlas / MP4 provenance verified; visual approval pending.')

if __name__=='__main__':
    task=sys.argv[1]
    if task=='review':review(sys.argv[2])
    else:{'pack':pack,'validate':validate,'movie':movie,'verify-build':verify_build,'verify-gpu':verify_gpu}[task]()
