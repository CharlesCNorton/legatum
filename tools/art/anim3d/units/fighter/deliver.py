"""Reviews, fixed rest-pose grade, 512/256 masters, trimmed atlas, validation and MP4."""
import hashlib,json,os,sys,subprocess,tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/fighter';V=R/'review/3d-v2';V.mkdir(parents=True,exist_ok=True)
OUT=Path('app/src/assets/units/anim');ORDER=['idle','move','attack','hit','death'];REF=Image.open('app/src/assets/units/fighter-256.png').convert('RGBA');BG=(240,232,214,255)
RES=int(os.environ.get('RESOLUTION','256'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def raw(stage):
    p=M/'renders'/str(RES)/stage;meta=json.loads((p/'render.json').read_text());assert meta['source_sha256']==sha(M/'fighter.blend'),'Stale master'
    blend=M/(stage[2:]+'.blend' if stage.startswith('e-') else 'move.blend' if stage=='g' else ('plain.blend' if stage=='b' else 'fighter.blend'))
    assert meta['blend_sha256']==sha(blend),'Stale clip blend'
    for name,h in meta['frames'].items():assert sha(p/name)==h,'Stale frame'
    return [Image.open(p/n).convert('RGBA') for n in sorted(meta['frames'])]
def quant(im):
    values=[[],[],[]]
    for px in im.get_flattened_data():
        if px[3]>240:
            for c in range(3):values[c].append(px[c])
    return [[sorted(v)[round((len(v)-1)*q)] for q in (.1,.5,.9)] for v in values]
def make_grade(im):
    before,after=quant(im),quant(REF);luts=[]
    for a,b in zip(before,after):
        pairs=[(0,0)]+list(zip(a,b))+[(255,255)];lut=[]
        for v in range(256):
            lo,hi=next((x,y) for x,y in zip(pairs,pairs[1:]) if x[0]<=v<=y[0]);target=lo[1]+(hi[1]-lo[1])*(v-lo[0])/max(1,hi[0]-lo[0]);lut.append(round(max(0,min(255,max(v-24,min(v+24,target))))))
        luts.append(lut)
    (M/'grade.json').write_text(json.dumps({'source':before,'target':after,'luts':luts,'max_delta':24,'render_resolution':RES,'source_sha256':sha(M/'fighter.blend'),'rest_manifest_sha256':sha(M/'renders'/str(RES)/'c/render.json')},indent=2))
def grade(im):
    lut=json.loads((M/'grade.json').read_text())['luts'];cs=im.split();return Image.merge('RGBA',tuple(cs[i].point(lut[i]) for i in range(3))+(cs[3],))
def tile(im,size=256):return im.resize((size,size),Image.Resampling.LANCZOS)
def sheet(images,labels,path,size=256):
    c=Image.new('RGBA',(size*len(images),size+26),BG);d=ImageDraw.Draw(c)
    for i,(im,label) in enumerate(zip(images,labels)):c.alpha_composite(tile(im,size),(i*size,26));d.text((i*size+5,7),label,fill=(50,42,32))
    c.convert('RGB').save(path)
def review(stage):
    ims=raw(stage)
    if stage=='c':make_grade(ims[0])
    if stage!='b':ims=[grade(im) for im in ims]
    # Keep genuine resolution sets; never manufacture 512 masters from previews.
    for size in (512,256):
        if RES<size:continue
        dest=M/str(size)/stage;dest.mkdir(parents=True,exist_ok=True)
        for i,im in enumerate(ims):tile(im,size).save(dest/f'{i:03d}.png')
    if stage=='b':sheet([REF,ims[0]],['Painting','Plain 3D geometry'],V/'fighter-b-plain.png')
    elif stage=='c':
        sheet([REF,ims[0]],['Painting','Textured 3D'],V/'fighter-c-textured-lit.png')
        cross=Image.blend(REF,tile(ims[0]),.5)
        sheet([REF,ims[0],cross],['Painting','3D rest pose','50/50 crossfade'],V/'fighter-f-restpose-compare.png')
        sheet([REF,ims[0],cross],['Painting 64','3D 64','50/50'],V/'fighter-f-restpose-64.png',64)
        boxes=[(95,65,155,110),(150,87,221,132),(20,110,153,157)]
        crops=[];labels=[]
        for label,box in zip(['Canopy','Cowling','Wing'],boxes):
            crops.extend([REF.crop(box),tile(ims[0]).crop(box)]);labels.extend([label+' painting',label+' 3D'])
        sheet(crops,labels,V/'fighter-c-details.png',160)
    elif stage=='g':
        # Aircraft have no feet or animal/human gait; inspect the actual mechanical
        # travel axis and propeller plane over all eight move samples instead.
        rows=[]
        for view in ('top','front'):
            paths=sorted((M/'renders'/str(RES)/'g').glob(view+'-*.png'))
            row=Image.new('RGBA',(8*128,154),BG);d=ImageDraw.Draw(row)
            for i,p in enumerate(paths):
                row.alpha_composite(tile(grade(Image.open(p).convert('RGBA')),128),(i*128,26))
                d.text((i*128+4,6),f'{view} {i+1}',fill=(50,42,32))
            rows.append(row)
        canvas=Image.new('RGBA',(1024,334),BG);d=ImageDraw.Draw(canvas)
        d.text((8,8),'Mechanical move audit: no feet / no human or animal motion. Nose is +X; base stationary.',fill=(50,42,32))
        for i,row in enumerate(rows):canvas.alpha_composite(row,(0,26+i*154))
        canvas.convert('RGB').save(V/'fighter-g-feet-check.png')
    elif stage.startswith('e-'):
        clip=stage[2:];sheet(ims,[f'{clip} {i+1}' for i in range(len(ims))],V/f'fighter-e-{clip}-strip.png')
        sheet(ims,[str(i+1) for i in range(len(ims))],V/f'fighter-e-{clip}-64.png',64)
        data=json.loads((M/'clips.json').read_text())['clips'][clip];frames=[]
        for im in ims:
            b=Image.new('RGBA',(256,256),BG);b.alpha_composite(tile(im));frames.append(b)
        frames[0].save(V/f'fighter-e-{clip}.webp',save_all=True,append_images=frames[1:],duration=round(1000/data['fps']),loop=0,quality=85)
        if clip=='attack':sheet([ims[i] for i in (0,3,5,9)],['Rest','Attack run','Firing','Recovery'],V/'fighter-d-rig-poses.png')
    with (V/'fighter-log.md').open('a') as f:f.write(f'- Rendered {stage}: {RES}px, {json.loads((M/"renders"/str(RES)/stage/"render.json").read_text())["engine"]}; review published.\n')
def frame160(im):
    # Premultiplied bicubic keeps colour clean at alpha edges without quantization.
    return im.convert('RGBa').resize((160,160),Image.Resampling.BICUBIC).convert('RGBA')
def verify_sources(gpu=False):
    g=json.loads((M/'grade.json').read_text())
    assert g['source_sha256']==sha(M/'fighter.blend'),'Stale grade'
    assert g['rest_manifest_sha256']==sha(M/'renders'/str(RES)/'c/render.json'),'Rest render changed after grade'
    rest=json.loads((M/'renders'/str(RES)/'c/render.json').read_text())
    keys=('resolution','engine','device','samples')
    for stage in ('b','c','g',*[f'e-{n}' for n in ORDER]):
        ims=raw(stage)
        record=json.loads((M/'renders'/str(RES)/stage/'render.json').read_text())
        assert all(record[k]==rest[k] for k in keys),'Mixed render settings: '+stage
        assert all(im.size==(RES,RES) for im in ims),'Wrong source resolution'
        if gpu:
            assert RES==512 and record['engine']=='CYCLES' and record['device']=='GPU','Not GPU512: '+stage
            assert record['samples']==int(os.environ.get('SAMPLES','64')),'Wrong GPU samples'
            for size in (512,256):
                copies=sorted((M/str(size)/stage).glob('*.png'))
                assert len(copies)==len(ims),'Missing gallery/master frames: '+stage
                assert all(Image.open(p).size==(size,size) for p in copies),'Wrong export size'
    return rest
def pack():
    verify_sources()
    clips=json.loads((M/'clips.json').read_text())['clips'];OUT.mkdir(parents=True,exist_ok=True)
    atlas=Image.new('RGBA',(1604,820));meta={'version':2,'layout':'trimmed-rows','frame':{'w':160,'h':160,'ax':79,'ay':124},'clips':{}};sources={};known={}
    for row,name in enumerate(ORDER):
        ims=raw('e-'+name);assert len(ims)==clips[name]['frames'];rects=[];cursor=1
        for i,rawim in enumerate(ims):
            im=frame160(grade(rawim));alpha=im.getchannel('A');box=alpha.getbbox();assert box,'Empty frame'
            x,y,x2,y2=box;assert x>=1 and y>=1 and x2<=159 and y2<=159,f'Clipping {name} {i}: {box}'
            key=hashlib.sha256(im.tobytes()).hexdigest()
            if key in known:
                rects.append(dict(known[key]));continue
            crop=im.crop(box);atlas.paste(crop,(cursor,row*164+1))
            rect={'x':cursor,'y':row*164+1,'w':crop.width,'h':crop.height,'ox':x,'oy':y}
            rects.append(rect);known[key]=rect;cursor+=crop.width+2
        meta['clips'][name]={'row':row,**clips[name],'rects':rects};sources[name]=json.loads((M/'renders'/str(RES)/('e-'+name)/'render.json').read_text())
    maxx=max(r['x']+r['w']+1 for c in meta['clips'].values() for r in c['rects']);maxy=max(r['y']+r['h']+1 for c in meta['clips'].values() for r in c['rects'])
    atlas=atlas.crop((0,0,maxx,maxy));meta['atlas']={'w':maxx,'h':maxy}
    candidate=M/'atlas-candidate.webp'
    for quality in (90,85,80,75):
        atlas.save(candidate,'WEBP',quality=quality,method=6,exact=True)
        if candidate.stat().st_size<=200000:break
    else:raise RuntimeError('Atlas exceeds 200KB at quality 75; refusing delivery')
    meta['quality']=quality
    (OUT/'fighter.webp').write_bytes(candidate.read_bytes());(OUT/'fighter.json').write_text(json.dumps(meta,indent=2)+'\n')
    (M/'pack.json').write_text(json.dumps({'atlas_sha256':sha(OUT/'fighter.webp'),'json_sha256':sha(OUT/'fighter.json'),'bytes':candidate.stat().st_size,'quality':quality,'unique_rectangles':len(known),'renders':sources,'grade_sha256':sha(M/'grade.json')},indent=2))
    validate()
def unpack():
    meta=json.loads((OUT/'fighter.json').read_text());atlas=Image.open(OUT/'fighter.webp').convert('RGBA');frames={}
    for name,clip in meta['clips'].items():
        frames[name]=[]
        for r in clip['rects']:
            im=Image.new('RGBA',(160,160));im.alpha_composite(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));frames[name].append(im)
    return meta,frames
def validate():
    provenance=verify_sources()
    meta,frames=unpack();record=json.loads((M/'pack.json').read_text())
    assert sha(OUT/'fighter.webp')==record['atlas_sha256'];assert sha(OUT/'fighter.json')==record['json_sha256']
    assert sha(M/'grade.json')==record['grade_sha256'];assert (OUT/'fighter.webp').stat().st_size==record['bytes']<=200000
    assert meta['quality']==record['quality']>=75
    assert [len(frames[n]) for n in ORDER]==[8,8,10,4,10]
    atlas=Image.open(OUT/'fighter.webp').convert('RGBA')
    assert atlas.size==(meta['atlas']['w'],meta['atlas']['h'])
    for name,ims in frames.items():
        expected_meta=json.loads((M/'clips.json').read_text())['clips'][name]
        assert all(meta['clips'][name][k]==v for k,v in expected_meta.items()),'Wrong clip timing'
        current=json.loads((M/'renders'/str(RES)/('e-'+name)/'render.json').read_text())
        assert current==record['renders'][name],'Render changed after packing'
        assert len({im.tobytes() for im in ims})>1,f'No motion {name}'
        originals=raw('e-'+name)
        for i,im in enumerate(ims):
            r=meta['clips'][name]['rects'][i]
            assert 0<=r['ox']<160 and 0<=r['oy']<160 and r['ox']+r['w']<=160 and r['oy']+r['h']<=160
            assert r['x']>=1 and r['y']>=1 and r['x']+r['w']<atlas.width and r['y']+r['h']<atlas.height
            expected=frame160(grade(originals[i]))
            assert im.getchannel('A').tobytes()==expected.getchannel('A').tobytes(),'Trim offset/alpha mismatch'
            for box in ((r['x']-1,r['y']-1,r['x']+r['w']+1,r['y']),
                        (r['x']-1,r['y']+r['h'],r['x']+r['w']+1,r['y']+r['h']+1),
                        (r['x']-1,r['y'],r['x'],r['y']+r['h']),
                        (r['x']+r['w'],r['y'],r['x']+r['w']+1,r['y']+r['h'])):
                assert atlas.crop(box).getchannel('A').getextrema()[1]==0,'Opaque gutter'
    death=raw('e-death');assert death[-1].tobytes()==death[-2].tobytes(),'Death not held'
    assert frames['death'][-1].tobytes()==frames['death'][-2].tobytes(),'Decoded death not held'
    report={'result':'PASS technical contract (not art approval)','frames':40,'size':meta['atlas'],'bytes':record['bytes'],'quality':meta['quality'],'source_resolution':RES,'device':provenance['device'],'samples':provenance['samples'],'trim_offsets':True,'lossless_alpha':True,'terminal_death_held':True}
    (M/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
    # Decode the actual atlas for review, not a stand-in assembled from source frames.
    canvas=Image.new('RGBA',(10*160,5*186),BG)
    for row,n in enumerate(ORDER):
        d=ImageDraw.Draw(canvas);d.text((5,row*186+6),n,fill=(50,42,32))
        for i,im in enumerate(frames[n]):canvas.alpha_composite(im,(160*i,row*186+26))
    canvas.convert('RGB').save(V/'fighter-g-decoded-atlas.png')
def movie():
    meta,frames=unpack();out=V/f'fighter-round{os.environ.get("ROUND","2")}.mp4';proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1600x348','-framerate','30','-i','-','-an','-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
    enlarged={n:[tile(im,320) for im in ims] for n,ims in frames.items()}
    for t in range(240):
        canvas=Image.new('RGBA',(1600,348),BG);d=ImageDraw.Draw(canvas)
        for j,n in enumerate(ORDER):
            c=meta['clips'][n];i=int(t/30*c['fps'])%c['frames'] if c['loop'] else min(int((t%60)/30*c['fps']),c['frames']-1);canvas.alpha_composite(enlarged[n][i],(j*320,28));d.text((j*320+8,7),n,fill=(60,50,40))
        proc.stdin.write(canvas.convert('RGB').tobytes())
    proc.stdin.close();assert proc.wait()==0
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(out)]));v=probe['streams'][0];assert v['codec_name']=='h264' and v['pix_fmt']=='yuv420p' and int(v['nb_frames'])==240 and (v['width'],v['height'])==(1600,348) and abs(float(v['duration'])-8)<.01;print('MP4 VERIFIED',out)
if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='review':review(sys.argv[2])
    elif mode=='pack':pack()
    elif mode=='validate':validate()
    elif mode=='movie':movie()
    elif mode=='verify-gpu':verify_sources(gpu=True);print('GPU512 provenance and 512/256 exports verified')
