"""Frozen grade, stage reviews, trimmed atlas, reconstruction checks and MP4.
Schema v2: logical frame=160; clip.rects stores atlas x/y/w/h and cell ox/oy.
Place a sprite at world anchor - (ax,ay) + (ox,oy), with no per-frame rescaling.
"""
import os,json,hashlib,sys,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/jet-fighter';V=R/'review/3d-v2';V.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
REF=Image.open('app/src/assets/units/jet-fighter-256.png').convert('RGBA');CREAM=(233,207,160,255)
mode=sys.argv[1] if len(sys.argv)>1 else 'all'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def composite(im):
    out=Image.new('RGBA',im.size,CREAM);out.alpha_composite(im);return out

def grade_luts(im):
    def quant(img):
        ps=[p for p in img.get_flattened_data() if p[3]>240]
        return [[sorted(p[c] for p in ps)[int((len(ps)-1)*q)] for q in (.1,.5,.9)] for c in range(3)]
    src,dst=quant(im),quant(REF);tables=[]
    for a,b in zip(src,dst):
        pairs=[(0,0),*zip(a,b),(255,255)];lut=[]
        for value in range(256):
            lo,hi=next((lo,hi) for lo,hi in zip(pairs,pairs[1:]) if lo[0]<=value<=hi[0]);target=lo[1]+(hi[1]-lo[1])*(value-lo[0])/max(1,hi[0]-lo[0]);lut.append(round(max(0,min(255,max(value-24,min(value+24,target))))))
        tables.append(lut)
    (M/'grade.json').write_text(json.dumps({'source_quantiles':dst,'render_quantiles':src,'max_delta':24,'luts':tables},indent=2));return tables

def review(stage):
    candidates=[r for r in (512,256,128) if (M/'raw'/str(r)/stage/'render.json').exists()]
    if not candidates:raise RuntimeError('Missing complete render '+stage)
    res=int(os.environ.get('RESOLUTION',candidates[0]));folder=M/'raw'/str(res)/stage;manifest=json.loads((folder/'render.json').read_text())
    assert manifest['master_sha256']==sha(M/'jet-fighter.blend'),'stale render master'
    raw=[]
    for name,h in manifest['frames'].items():
        assert sha(folder/name)==h,'frame hash mismatch';raw.append(Image.open(folder/name).convert('RGBA'))
    if stage=='c':tables=grade_luts(raw[0])
    elif stage!='b':tables=json.loads((M/'grade.json').read_text())['luts']
    else:tables=None
    out=[]
    for i,im in enumerate(raw):
        if tables:
            cs=im.split();im=Image.merge('RGBA',tuple(cs[c].point(tables[c]) for c in range(3))+(cs[3],))
        for size in (512,256):
            if size>res:continue
            dest=M/'frames'/str(size)/stage;dest.mkdir(parents=True,exist_ok=True);im.resize((size,size),Image.Resampling.LANCZOS).save(dest/f'{i:03}.png')
        out.append(im.resize((256,256),Image.Resampling.LANCZOS))
    for size in (512,256):
        dest=M/'frames'/str(size)/stage
        if size<=res:
            (dest/'render.json').write_text(json.dumps({'master_sha256':manifest['master_sha256'],'grade_sha256':sha(M/'grade.json') if tables else None,'source_render':manifest,'frames':{p.name:sha(p) for p in sorted(dest.glob('*.png'))}},indent=2))
    labels={'b':'b-plain','c':'c-textured-lit','d':'d-rig-poses','g':'g-feet-check'};name=labels.get(stage,stage+'-strip');panels=[REF,*out]
    sheet=Image.new('RGBA',(256*len(panels),350),CREAM);d=ImageDraw.Draw(sheet)
    for i,im in enumerate(panels):
        sheet.alpha_composite(im,(i*256,24));sheet.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,282));d.text((i*256+6,6),'painting' if i==0 else f'{stage} {i-1} | {manifest["device"]}',fill='black')
    sheet.save(V/f'jet-fighter-{name}.png')
    if stage=='g':
        sheet=Image.new('RGBA',(8*256,2*280+30),CREAM);d=ImageDraw.Draw(sheet)
        d.text((8,5),'Aircraft: no feet / gait. Move-cycle top and nose views; rigid airframe heading and clearance.',fill='black')
        for i,im in enumerate(out):
            sheet.alpha_composite(im,((i%8)*256,30+(i//8)*280));d.text(((i%8)*256+5,30+(i//8)*280),'top' if i<8 else 'nose',fill='black')
        sheet.save(V/'jet-fighter-g-feet-check.png')
    if stage=='c':
        compare=Image.new('RGBA',(768,350),CREAM);d=ImageDraw.Draw(compare)
        for i,(label,im) in enumerate([('painting',REF),('true 3D',out[0]),('50/50 crossfade',Image.blend(REF,out[0],.5))]):
            compare.alpha_composite(im,(i*256,24));compare.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,282));d.text((i*256+8,5),label,fill='black')
        compare.save(V/'jet-fighter-f-restpose-compare.png')
        details=Image.new('RGBA',(1024,560),CREAM);d=ImageDraw.Draw(details)
        for row,(label,box) in enumerate([('canopy, rivets and intake',(147,38,246,92)),('swept aluminium wing',(30,82,177,154))]):
            detailref=Image.open(R/'assets/jet-fighter/projection.png').convert('RGBA').resize((512,512),Image.Resampling.LANCZOS)
            detailrender=Image.open(M/'frames/512/c/000.png').convert('RGBA') if res>=512 else out[0].resize((512,512))
            for col,im in enumerate((detailref,detailrender)):
                details.alpha_composite(im.crop(tuple(v*2 for v in box)).resize((492,240),Image.Resampling.LANCZOS),(col*512+10,row*280+25));d.text((col*512+10,row*280+6),label+(' painting' if col==0 else ' render'),fill='black')
        details.save(V/'jet-fighter-c-details.png')
    if stage.startswith('e-'):
        name=stage[2:];ims=[composite(im) for im in out];ims[0].save(V/f'jet-fighter-e-{name}.webp',save_all=True,append_images=ims[1:],duration=round(1000/CLIPS[name][1]),loop=0,quality=85)
    with (V/'jet-fighter-log.md').open('a') as f:f.write(f'{stage}: {len(out)} frames at 256/64 from {res}px {manifest["engine"]}/{manifest["device"]}, {manifest["samples"]} samples.\n')

def pack():
    rows=[];metadata={'version':2,'unit':'jet-fighter','trimmed':True,'frame':{'w':160,'h':160,'ax':72.8,'ay':130.0},'clips':{}};height=0;hashes={}
    for row,(name,(n,fps,loop)) in enumerate(CLIPS.items()):
        images=[];rects=[];x=2;maxh=0;seen={};folder=M/'frames/256'/('e-'+name)
        proof=json.loads((folder/'render.json').read_text());assert proof['master_sha256']==sha(M/'jet-fighter.blend'),'stale derived frames';assert proof['grade_sha256']==sha(M/'grade.json'),'mixed grades';assert len(proof['frames'])==n
        assert proof['source_render']['render_script_sha256']==sha(Path(__file__).with_name('render.py')),'animation script changed; rerender'
        assert all(sha(folder/file)==digest for file,digest in proof['frames'].items()),'changed derived frames'
        for i in range(n):
            path=folder/f'{i:03}.png';hashes[str(path.relative_to(M))]=sha(path);im=Image.open(path).convert('RGBA').resize((160,160),Image.Resampling.LANCZOS)
            a=im.getchannel('A').point(lambda a:0 if a<3 else a);im.putalpha(a);box=a.getbbox();assert box and min(box[:2])>=1 and max(box[2:])<=159,(name,i,'clipping',box)
            crop=im.crop(box);key=hashlib.sha256(im.tobytes()).hexdigest()
            if key in seen:images.append(None);rects.append(dict(seen[key]))
            else:
                rect={'x':x,'y':height+2,'w':crop.width,'h':crop.height,'ox':box[0],'oy':box[1]}
                images.append(crop);rects.append(rect);seen[key]=rect;x+=crop.width+4
            maxh=max(maxh,crop.height)
        metadata['clips'][name]={'row':row,'frames':n,'fps':fps,'loop':loop,'rects':rects};rows.append(images);height+=maxh+4
    width=max(r['x']+r['w']+2 for c in metadata['clips'].values() for r in c['rects']);atlas=Image.new('RGBA',(width,height))
    for clip,row in zip(metadata['clips'].values(),rows):
        for im,s in zip(row,clip['rects']):
            if im is not None:atlas.paste(im,(s['x'],s['y']))
    dest=Path('app/src/assets/units/anim');dest.mkdir(parents=True,exist_ok=True);tmp=M/'candidate.webp'
    for quality in (95,90,85,80,75):
        atlas.save(tmp,'WEBP',quality=quality,alpha_quality=100,method=6,exact=True)
        if tmp.stat().st_size<=200000:break
    assert tmp.stat().st_size<=200000,'atlas too big at quality 75'
    metadata['atlas']={'w':width,'h':height,'quality':quality};(dest/'jet-fighter.webp').write_bytes(tmp.read_bytes());(dest/'jet-fighter.json').write_text(json.dumps(metadata,indent=2)+'\n')
    (M/'pack.json').write_text(json.dumps({'quality':quality,'bytes':tmp.stat().st_size,'master':sha(M/'jet-fighter.blend'),'frames':hashes,'atlas':sha(dest/'jet-fighter.webp')},indent=2))

def validate():
    path=Path('app/src/assets/units/anim/jet-fighter.webp');meta=json.loads(path.with_suffix('.json').read_text());atlas=Image.open(path).convert('RGBA');assert path.stat().st_size<=200000 and meta['atlas']['quality']>=75
    receipt=json.loads((M/'pack.json').read_text())
    assert receipt['master']==sha(M/'jet-fighter.blend') and receipt['atlas']==sha(path)
    assert all(sha(M/file)==digest for file,digest in receipt['frames'].items())
    assert meta['trimmed'] and meta['version']==2 and meta['frame']=={'w':160,'h':160,'ax':72.8,'ay':130.0}
    assert atlas.size==(meta['atlas']['w'],meta['atlas']['h']);frames={};occupied=Image.new('L',atlas.size);seen=set()
    for name,(n,fps,loop) in CLIPS.items():
        c=meta['clips'][name];assert (c['frames'],c['fps'],c['loop'])==(n,fps,loop);assert len(c['rects'])==n;fr=[]
        proof=json.loads((M/'frames/256'/('e-'+name)/'render.json').read_text())
        assert proof['master_sha256']==sha(M/'jet-fighter.blend') and proof['grade_sha256']==sha(M/'grade.json')
        assert proof['source_render']['render_script_sha256']==sha(Path(__file__).with_name('render.py'))
        if os.environ.get('REQUIRE_GPU')=='1':
            assert proof['source_render']['device']=='GPU' and proof['source_render']['resolution']==512
        for index,s in enumerate(c['rects']):
            x,y,w,h,ox,oy=[s[k] for k in ('x','y','w','h','ox','oy')];assert 0<=x<x+w<=atlas.width and 0<=y<y+h<=atlas.height;assert 0<=ox<ox+w<=160 and 0<=oy<oy+h<=160
            im=Image.new('RGBA',(160,160));im.alpha_composite(atlas.crop((x,y,x+w,y+h)),(ox,oy));assert im.getchannel('A').getextrema()==(0,255);fr.append(im)
            expected=Image.open(M/'frames/256'/('e-'+name)/f'{index:03}.png').convert('RGBA').resize((160,160),Image.Resampling.LANCZOS).getchannel('A').point(lambda a:0 if a<3 else a)
            assert expected.tobytes()==im.getchannel('A').tobytes(),'trimmed alpha reconstruction mismatch'
            rect=(x,y,w,h)
            if rect not in seen:
                assert not occupied.crop((x-1,y-1,x+w+1,y+h+1)).getbbox(),'overlapping crops'
                occupied.paste(255,(x,y,x+w,y+h));seen.add(rect)
        assert len({hashlib.sha256(im.tobytes()).hexdigest() for im in fr})>1,name+' no motion';frames[name]=fr
    assert not ImageChops.multiply(atlas.getchannel('A'),ImageChops.invert(occupied)).getbbox(),'opaque padding'
    assert frames['death'][-1].tobytes()==frames['death'][-2].tobytes(),'decoded death hold changed'
    a=Image.open(M/'frames/256/e-death/008.png').convert('RGBA');b=Image.open(M/'frames/256/e-death/009.png').convert('RGBA')
    assert ImageChops.difference(a.getchannel('A'),b.getchannel('A')).getbbox() is None,'death alpha not held'
    assert ImageChops.difference(composite(a),composite(b)).getbbox() is None,'visible death not held'
    report={'status':'pass','frames':40,'bytes':path.stat().st_size,'quality':meta['atlas']['quality'],'logical_cell':160,'trim_offsets':True,'held_death':True,'art_approval':False}
    (M/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));return meta,frames

def video(meta,frames):
    out=V/f'jet-fighter-round{os.environ.get("ROUND","1")}.mp4';w,h=1600,348
    proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{w}x{h}','-framerate','30','-i','-','-an','-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
    enlarged={name:[im.resize((320,320),Image.Resampling.LANCZOS) for im in fr] for name,fr in frames.items()}
    for t in range(240):
        canvas=Image.new('RGBA',(w,h),CREAM);d=ImageDraw.Draw(canvas)
        for k,(name,c) in enumerate(meta['clips'].items()):
            i=int(t/30*c['fps'])%c['frames'] if c['loop'] else min(int((t%60)/30*c['fps']),c['frames']-1)
            canvas.alpha_composite(enlarged[name][i],(320*k,28));d.text((k*320+8,8),name,fill='black')
        proc.stdin.write(canvas.convert('RGB').tobytes())
    proc.stdin.close();assert proc.wait()==0
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames,duration','-of','json',str(out)]))['streams'][0]
    assert probe['codec_name']=='h264' and probe['pix_fmt']=='yuv420p'
    assert int(probe['nb_frames'])==240 and float(probe['duration'])==8
    assert (probe['width'],probe['height'])==(1600,348)
    out.with_suffix('.json').write_text(json.dumps(probe,indent=2));print(out)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-ss','0.5','-i',str(out),'-frames:v','1',str(out.with_suffix('.png'))],check=True)
if mode=='validate':validate()
elif mode=='pack':pack();meta,frames=validate();video(meta,frames)
elif mode=='all':
    for s in ('b','c','d',*['e-'+c for c in CLIPS]):review(s)
    pack();meta,frames=validate();video(meta,frames)
else:review(mode)
